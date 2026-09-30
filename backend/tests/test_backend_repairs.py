import socket
import sys
import base64
import tempfile
import time
import unittest
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from celery.exceptions import Retry
from flask_jwt_extended import create_access_token
from sqlalchemy import inspect, text

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.customer import Customer
from app.models.comparison import Comparison
from app.models.prompt import Prompt
from app.models.translate import Translate
from app.models.user import User
from app.models.mcp_api_key import McpApiKey
from app.models.job import FailedJob, Job
from app.models.translate_batch import TranslateBatch
from app.utils.auth_tools import is_password_hash, verify_legacy_password
from app.utils.file_security import safe_display_filename, validate_public_url
from app.translate.db import get_database_url
from app.translate import to_translate
from app.translate.pdf_paths import move_babeldoc_output
from app.resources.api.translate import (
    TranslateStartValidationError,
    _validate_translate_start,
)
from app.resources.task.translate_service import TranslateEngine
from app.celery_tasks import _refresh_lock, register_tasks
from app.task_queue import (
    DEFAULT_QUEUE,
    PDF_QUEUE,
    claim_next_job,
    enqueue_translation,
    queue_backend_name,
    retry_or_fail_job,
)
from app.translate.batch_service import extract_zip_documents, remove_batch_directory
from app.result_storage import FinalizedResult
from migrate_startup import run_migrations


class BackendRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestingConfig)
        run_migrations(cls.app, seed=True)
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            first = Customer(
                email='first@example.com',
                password='unused',
                storage=0,
                total_storage=1024 * 1024,
            )
            second = Customer(
                email='second@example.com',
                password='unused',
                storage=0,
                total_storage=1024 * 1024,
            )
            admin = User(
                name='admin',
                email='admin@example.com',
                password='legacy-password',
                deleted_flag='N',
            )
            db.session.add_all([first, second, admin])
            db.session.commit()
            cls.first_id = first.id
            cls.second_id = second.id
            cls.admin_id = admin.id
            cls.user_token = create_access_token(
                identity=str(first.id), additional_claims={'role': 'user'}
            )
            cls.second_token = create_access_token(
                identity=str(second.id), additional_claims={'role': 'user'}
            )
            cls.admin_token = create_access_token(
                identity=str(admin.id), additional_claims={'role': 'admin'}
            )
            cls.roleless_token = create_access_token(identity=str(first.id))

    def test_empty_database_reaches_current_head(self):
        with self.app.app_context():
            engine = db.engine
            self.assertIn('translate', inspect(engine).get_table_names())
            with engine.connect() as connection:
                version = connection.execute(
                    text('SELECT version_num FROM alembic_version')
                ).scalar()
            self.assertEqual(version, '20260723_result_storage')

    def test_unversioned_legacy_schema_repairs_missing_tables(self):
        legacy_app = create_app(TestingConfig)
        with legacy_app.app_context():
            engine = db.engine
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    'CREATE TABLE customer (id INTEGER PRIMARY KEY, password TEXT NOT NULL)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE user (id INTEGER PRIMARY KEY, password TEXT NOT NULL)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE prompt (id INTEGER PRIMARY KEY)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE setting (id INTEGER PRIMARY KEY)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE translate (id INTEGER PRIMARY KEY)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE jobs ('
                    'id INTEGER PRIMARY KEY, queue VARCHAR(255) NOT NULL, '
                    'available_at INTEGER NOT NULL, reserved_at INTEGER)'
                )
                connection.exec_driver_sql(
                    "INSERT INTO customer (id, password) VALUES (1, 'legacy')"
                )

        run_migrations(legacy_app, seed=False)

        with legacy_app.app_context():
            tables = set(inspect(db.engine).get_table_names())
            version = db.session.execute(
                text('SELECT version_num FROM alembic_version')
            ).scalar()
            self.assertEqual(version, '20260723_result_storage')
            self.assertIn('mcp_api_key', tables)
            self.assertIn('comparison', tables)
            self.assertIn('translate_batch', tables)
            self.assertEqual(
                db.session.execute(
                    text("SELECT password FROM customer WHERE id = 1")
                ).scalar(),
                'legacy',
            )

    def test_migrations_are_idempotent(self):
        migration_app = create_app(TestingConfig)
        run_migrations(migration_app, seed=False)
        run_migrations(migration_app, seed=False)
        with migration_app.app_context():
            self.assertEqual(
                db.session.execute(
                    text('SELECT version_num FROM alembic_version')
                ).scalar(),
                '20260723_result_storage',
            )

    def test_unknown_migration_revision_stops_startup(self):
        unknown_app = create_app(TestingConfig)
        with unknown_app.app_context():
            with db.engine.begin() as connection:
                connection.exec_driver_sql(
                    'CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)'
                )
                connection.exec_driver_sql(
                    "INSERT INTO alembic_version (version_num) VALUES ('unknown_revision')"
                )

        with self.assertRaisesRegex(RuntimeError, '未知 Alembic 版本'):
            run_migrations(unknown_app, seed=False)

    def test_versioned_database_recreates_missing_table(self):
        migration_app = create_app(TestingConfig)
        run_migrations(migration_app, seed=False)
        with migration_app.app_context():
            with db.engine.begin() as connection:
                connection.exec_driver_sql('DROP TABLE mcp_api_key')
            self.assertNotIn(
                'mcp_api_key', inspect(db.engine).get_table_names()
            )

        run_migrations(migration_app, seed=False)

        with migration_app.app_context():
            self.assertIn('mcp_api_key', inspect(db.engine).get_table_names())
            self.assertEqual(
                db.session.execute(
                    text('SELECT version_num FROM alembic_version')
                ).scalar(),
                '20260723_result_storage',
            )

    def test_admin_routes_require_admin_role(self):
        denied = self.client.get(
            '/api/admin/customers?page=1&limit=10',
            headers={'token': self.user_token},
        )
        self.assertEqual(denied.status_code, 403)

        allowed = self.client.get(
            '/api/admin/customers?page=1&limit=10',
            headers={'token': self.admin_token},
        )
        self.assertEqual(allowed.status_code, 200)

    def test_roleless_tokens_are_rejected(self):
        response = self.client.get(
            '/api/translates', headers={'token': self.roleless_token}
        )
        self.assertEqual(response.status_code, 401)

    def test_user_cannot_create_admin_mcp_key(self):
        response = self.client.post(
            '/api/mcp/key',
            headers={'token': self.user_token},
            json={
                'name': 'user key',
                'scope': 'admin',
                'config': {
                    'api_url': 'https://api.example.com',
                    'api_key': 'test-key',
                    'model': 'test-model',
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        key_id = response.get_json()['data']['id']
        with self.app.app_context():
            key = db.session.get(McpApiKey, key_id)
            self.assertEqual(key.scope, 'user')

    def test_legacy_admin_password_is_upgraded(self):
        response = self.client.post(
            '/api/admin/login',
            json={'email': 'admin@example.com', 'password': 'legacy-password'},
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            admin = db.session.get(User, self.admin_id)
            self.assertTrue(is_password_hash(admin.password))

    def test_translation_download_is_owner_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'translated.txt'
            target.write_text('translated', encoding='utf-8')
            with self.app.app_context():
                record = Translate(
                    customer_id=self.first_id,
                    origin_filename='document.txt',
                    origin_filepath=str(target),
                    target_filepath=str(target),
                    status='done',
                    deleted_flag='N',
                )
                db.session.add(record)
                db.session.commit()
                record_id = record.id

            denied = self.client.get(
                f'/api/translate/download/{record_id}',
                headers={'token': self.second_token},
            )
            self.assertEqual(denied.status_code, 404)

            allowed = self.client.get(
                f'/api/translate/download/{record_id}',
                headers={'token': self.user_token},
            )
            self.assertEqual(allowed.status_code, 200)
            allowed.get_data()
            allowed.close()

    def test_batch_download_preserves_display_filenames(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            targets = []
            with self.app.app_context():
                for index in range(2):
                    target = Path(temp_dir) / f'internal-{index}.txt'
                    target.write_text(f'translated-{index}', encoding='utf-8')
                    targets.append(target)
                    db.session.add(Translate(
                        customer_id=self.first_id,
                        origin_filename='same-name.txt',
                        origin_filepath=str(target),
                        target_filepath=str(target),
                        status='done',
                        deleted_flag='N',
                    ))
                db.session.commit()

            response = self.client.get(
                '/api/translate/download/all',
                headers={'token': self.user_token},
            )
            self.assertEqual(response.status_code, 200)
            with zipfile.ZipFile(BytesIO(response.get_data())) as archive:
                names = archive.namelist()
            self.assertIn('same-name.txt', names)
            self.assertIn('same-name (2).txt', names)
            response.close()

    def test_filename_validation_rejects_paths(self):
        self.assertEqual(safe_display_filename('中文文档.docx'), '中文文档.docx')
        for unsafe in ('../secret.docx', 'folder/file.docx', 'C:\\secret.docx'):
            with self.assertRaises(ValueError):
                safe_display_filename(unsafe)

    def test_mcp_requires_content_or_url_and_validates_base64(self):
        from app.mcp.tools import _decode_base64_file, _resolve_file_input

        with self.app.app_context():
            with tempfile.NamedTemporaryFile(suffix='.txt') as local_file:
                with self.assertRaisesRegex(ValueError, 'file_content 或 file_url'):
                    _resolve_file_input(None, None, local_file.name, self.app)

            self.assertEqual(_decode_base64_file(base64.b64encode(b'abc').decode(), 3), b'abc')
            with self.assertRaisesRegex(ValueError, '超过大小限制'):
                _decode_base64_file(base64.b64encode(b'abcd').decode(), 3)
            with self.assertRaisesRegex(ValueError, '有效的Base64'):
                _decode_base64_file('not-base64!', 100)

    def test_mcp_upload_cleanup_and_unique_disk_names(self):
        from app.mcp.tools import _save_upload_file, translate_file

        with self.app.app_context():
            first_path = _save_upload_file(b'one', 'same.txt', self.app)
            second_path = _save_upload_file(b'two', 'same.txt', self.app)
            try:
                self.assertNotEqual(Path(first_path).name, Path(second_path).name)
            finally:
                Path(first_path).unlink(missing_ok=True)
                Path(second_path).unlink(missing_ok=True)

            temporary_path = Path(tempfile.gettempdir()) / 'mcp-invalid-upload.txt'
            temporary_path.write_bytes(b'invalid')
            try:
                with patch(
                    'app.mcp.tools._save_upload_file',
                    return_value=str(temporary_path),
                ):
                    response = translate_file(
                        {}, self.first_id, self.app,
                        file_content=base64.b64encode(b'invalid').decode(),
                        file_name='invalid.exe',
                    )
                self.assertIn('不支持的文件格式', response['error'])
                self.assertFalse(temporary_path.exists())
            finally:
                temporary_path.unlink(missing_ok=True)

    def test_mcp_delete_is_idempotent_for_storage_quota(self):
        from app.mcp.tools import delete_translate

        with self.app.app_context():
            customer = db.session.get(Customer, self.first_id)
            original_storage = customer.storage
            customer.storage = 100
            record = Translate(
                customer_id=self.first_id,
                origin_filename='mcp-delete.txt',
                origin_filepath='/tmp/mcp-delete.txt',
                target_filepath='/tmp/mcp-delete.out',
                size=10,
                deleted_flag='N',
            )
            db.session.add(record)
            db.session.commit()
            record_id = record.id

            try:
                self.assertEqual(delete_translate(self.first_id, record_id), {'message': '删除成功'})
                self.assertEqual(customer.storage, 90)
                self.assertEqual(delete_translate(self.first_id, record_id), {'error': '翻译记录不存在'})
                self.assertEqual(customer.storage, 90)
            finally:
                db.session.delete(record)
                customer.storage = original_storage
                db.session.commit()

    @patch('app.utils.file_security.socket.getaddrinfo')
    def test_private_remote_addresses_are_rejected(self, getaddrinfo):
        getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 80))
        ]
        with self.assertRaises(ValueError):
            validate_public_url('http://example.test/file.docx')

    def test_plaintext_password_transition_helper(self):
        self.assertEqual(
            verify_legacy_password('plain', 'plain'),
            (True, True),
        )
        self.assertEqual(
            verify_legacy_password('plain', 'wrong'),
            (False, False),
        )

    def test_translation_database_url_follows_environment(self):
        values = {
            'FLASK_ENV': 'development',
            'DEV_DATABASE_URL': 'mysql+pymysql://dev/db',
            'PROD_DATABASE_URL': 'mysql+pymysql://prod/db',
        }
        self.assertEqual(get_database_url(values), values['DEV_DATABASE_URL'])
        values['FLASK_ENV'] = 'production'
        self.assertEqual(get_database_url(values), values['PROD_DATABASE_URL'])
        values.pop('PROD_DATABASE_URL')
        with self.assertRaises(ValueError):
            get_database_url(values)
        with self.assertRaises(ValueError):
            get_database_url({})

    @patch('app.translate.to_translate.OpenAI')
    def test_openai_clients_are_task_local(self, openai_class):
        openai_class.side_effect = [object(), object()]
        first = to_translate.create_openai_client(
            'https://first.example.com/v1', 'first-secret'
        )
        second = to_translate.create_openai_client(
            'https://second.example.com/v1', 'second-secret'
        )
        self.assertEqual(openai_class.call_count, 2)
        self.assertIsNot(first, second)
        self.assertEqual(openai_class.call_args_list[0].kwargs['api_key'], 'first-secret')
        self.assertEqual(openai_class.call_args_list[1].kwargs['api_key'], 'second-secret')

    def test_openai_translation_uses_task_client(self):
        client = MagicMock()
        choice = MagicMock()
        choice.message.content = 'translated'
        client.chat.completions.create.return_value.choices = [choice]
        result = to_translate._translate_openai(
            {
                'id': 1,
                'lang': '英语',
                'prompt': 'Translate to {target_lang}',
                'extension': '.txt',
                '_openai_client': client,
            },
            '原文',
            'model-a',
        )
        self.assertEqual(result, 'translated')
        client.chat.completions.create.assert_called_once()

    @patch('app.translate.to_translate.OpenAI')
    def test_openai_translation_reuses_fallback_client(self, openai_class):
        client = MagicMock()
        choice = MagicMock()
        choice.message.content = 'translated'
        client.chat.completions.create.return_value.choices = [choice]
        openai_class.return_value = client
        config = {
            'id': 1,
            'lang': '英语',
            'prompt': 'Translate to {target_lang}',
            'extension': '.txt',
            'api_url': 'https://api.example.com',
            'api_key': 'secret',
        }

        to_translate._translate_openai(config, '第一段', 'model-a')
        to_translate._translate_openai(config, '第二段', 'model-a')

        openai_class.assert_called_once()
        self.assertIs(config['_openai_client'], client)

    def test_non_pdf_handler_does_not_import_pdf_runtime(self):
        from app.resources.task.main import get_handler

        self.assertEqual(get_handler('.txt').__name__, 'app.translate.txt')
        self.assertNotIn('app.translate.pdf', sys.modules)

    def test_translate_start_validation_is_mode_aware(self):
        customer = Customer(level='common')
        openai_data = {
            'server': 'openai',
            'model': 'model-a',
            'lang': '英语',
            'uuid': 'task-uuid',
            'prompt': 'Translate to {target_lang}',
            'threads': 'not-a-number',
            'file_name': 'source.txt',
            'api_url': 'https://api.example.com',
            'api_key': 'secret',
        }
        with self.assertRaises(TranslateStartValidationError):
            _validate_translate_start(openai_data, customer, {})

        baidu_data = {
            **openai_data,
            'server': 'baidu',
            'threads': '2',
            'app_id': 'app-id',
            'app_key': 'app-key',
        }
        baidu_data.pop('lang')
        with self.assertRaises(TranslateStartValidationError):
            _validate_translate_start(baidu_data, customer, {})

        baidu_data['to_lang'] = 'zh'
        baidu_data['needIntervene'] = 'false'
        values = _validate_translate_start(baidu_data, customer, {})
        self.assertIsNone(values['comparison_id'])

    def test_translate_start_rejects_bad_input_before_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.txt'
            source.write_text('source', encoding='utf-8')
            with self.app.app_context():
                record = Translate(
                    uuid='invalid-start-uuid',
                    customer_id=self.first_id,
                    origin_filename='source.txt',
                    origin_filepath=str(source),
                    target_filepath='',
                    status='none',
                    deleted_flag='N',
                )
                db.session.add(record)
                db.session.commit()

            response = self.client.post(
                '/api/translate',
                headers={'token': self.user_token},
                data={
                    'server': 'openai',
                    'model': 'model-a',
                    'lang': '英语',
                    'uuid': 'invalid-start-uuid',
                    'prompt': 'Translate',
                    'threads': 'invalid',
                    'file_name': 'source.txt',
                    'api_url': 'https://api.example.com',
                    'api_key': 'secret',
                },
            )
            self.assertEqual(response.status_code, 400)
            with self.app.app_context():
                record = Translate.query.filter_by(uuid='invalid-start-uuid').first()
                self.assertEqual(record.status, 'none')
                self.assertEqual(record.target_filepath, '')

    @patch('app.task_queue.enqueue_translation')
    def test_translate_start_failure_is_persisted(self, enqueue_translation):
        enqueue_translation.side_effect = RuntimeError('queue unavailable')
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.txt'
            source.write_text('source', encoding='utf-8')
            with self.app.app_context():
                record = Translate(
                    uuid='start-failure-uuid',
                    customer_id=self.first_id,
                    origin_filename='source.txt',
                    origin_filepath=str(source),
                    target_filepath=str(Path(temp_dir) / 'target.txt'),
                    status='none',
                    deleted_flag='N',
                )
                db.session.add(record)
                db.session.commit()
                record_id = record.id
                started = TranslateEngine(record_id).execute()
                self.assertFalse(started)
                db.session.expire_all()
                failed = db.session.get(Translate, record_id)
                self.assertEqual(failed.status, 'failed')
                self.assertIn('queue unavailable', failed.failed_reason)

    @patch('app.task_queue.enqueue_translation')
    def test_start_endpoint_does_not_report_failed_engine_as_success(
        self, enqueue_translation
    ):
        enqueue_translation.side_effect = RuntimeError('queue unavailable')
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.txt'
            source.write_text('source', encoding='utf-8')
            with self.app.app_context():
                record = Translate(
                    uuid='engine-failure-uuid',
                    customer_id=self.first_id,
                    origin_filename='source.txt',
                    origin_filepath=str(source),
                    target_filepath='',
                    status='none',
                    deleted_flag='N',
                )
                db.session.add(record)
                db.session.commit()
                record_id = record.id

            response = self.client.post(
                '/api/translate',
                headers={'token': self.user_token},
                data={
                    'server': 'openai',
                    'model': 'model-a',
                    'lang': '英语',
                    'uuid': 'engine-failure-uuid',
                    'prompt': 'Translate',
                    'threads': '2',
                    'file_name': 'source.txt',
                    'api_url': 'https://api.example.com',
                    'api_key': 'secret',
                },
            )
            self.assertEqual(response.status_code, 500)
            with self.app.app_context():
                failed = db.session.get(Translate, record_id)
                self.assertEqual(failed.status, 'failed')
                self.assertIn('queue unavailable', failed.failed_reason)

    def test_translation_resources_require_owner_or_share(self):
        with self.app.app_context():
            private_prompt = Prompt(
                title='private prompt',
                content='private content',
                customer_id=self.second_id,
                share_flag='N',
                deleted_flag='N',
            )
            private_terms = Comparison(
                title='private terms',
                origin_lang='zh',
                target_lang='en',
                content='源词,target',
                customer_id=self.second_id,
                share_flag='N',
                deleted_flag='N',
            )
            task = Translate(
                uuid='authorization-uuid',
                customer_id=self.first_id,
                origin_filename='source.txt',
                origin_filepath='source.txt',
                target_filepath='target.txt',
                status='none',
                deleted_flag='N',
            )
            db.session.add_all([private_prompt, private_terms, task])
            db.session.commit()
            task.prompt_id = private_prompt.id
            task.comparison_id = private_terms.id
            db.session.commit()

            engine = TranslateEngine(task.id)
            with self.assertRaises(ValueError):
                engine._get_final_prompt(task)
            with self.assertRaises(ValueError):
                engine._get_matched_terms(task)

            private_prompt.share_flag = 'Y'
            private_terms.share_flag = 'Y'
            db.session.commit()
            self.assertEqual(engine._get_final_prompt(task), 'private content')
            self.assertEqual(
                engine._get_matched_terms(task),
                [{'source': '源词', 'target': 'target'}],
            )

    @patch('app.translate.to_translate.db.execute', return_value=True)
    def test_completion_uses_physical_output_size(self, execute):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'translated.txt'
            target.write_bytes(b'123456789')
            completed = to_translate.complete(
                {'id': 42, 'target_file': str(target)},
                text_count=3,
                spend_time=1,
            )
        self.assertTrue(completed)
        self.assertEqual(execute.call_args.args[1], 9)

    def test_task_is_done_only_after_result_storage_succeeds(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.app.app_context():
            source = Path(temp_dir) / 'source.txt'
            target = Path(temp_dir) / 'translated.txt'
            source.write_text('source', encoding='utf-8')
            target.write_bytes(b'translated')
            task = Translate(
                uuid=str(uuid.uuid4()),
                customer_id=self.first_id,
                origin_filename='source.txt',
                origin_filepath=str(source),
                target_filepath=str(target),
                status='process',
                deleted_flag='N',
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id
            fake_storage = MagicMock(backend_name='oss')

            def finalize(record):
                record.target_storage_backend = 'oss'
                record.target_storage_key = f'translations/{record.uuid}/source.txt'
                record.target_filesize = target.stat().st_size
                return FinalizedResult(
                    'oss', record.target_storage_key, str(target)
                )

            fake_storage.finalize_result.side_effect = finalize
            with patch(
                'app.result_storage.get_result_storage',
                return_value=fake_storage,
            ):
                self.assertTrue(TranslateEngine(task_id)._complete_task(True))

            db.session.expire_all()
            stored = db.session.get(Translate, task_id)
            self.assertEqual(stored.status, 'done')
            self.assertEqual(stored.target_storage_backend, 'oss')
            self.assertTrue(stored.target_storage_key)
            self.assertEqual(stored.target_filesize, len(b'translated'))
            self.assertFalse(target.exists())
            db.session.delete(stored)
            db.session.commit()

    def test_result_storage_failure_marks_task_failed_and_keeps_local_file(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.app.app_context():
            source = Path(temp_dir) / 'source.txt'
            target = Path(temp_dir) / 'translated.txt'
            source.write_text('source', encoding='utf-8')
            target.write_bytes(b'translated')
            task = Translate(
                uuid=str(uuid.uuid4()),
                customer_id=self.first_id,
                origin_filename='source.txt',
                origin_filepath=str(source),
                target_filepath=str(target),
                status='process',
                deleted_flag='N',
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.id
            fake_storage = MagicMock(backend_name='oss')
            fake_storage.finalize_result.side_effect = RuntimeError(
                'credential-bearing SDK detail'
            )
            with patch(
                'app.result_storage.get_result_storage',
                return_value=fake_storage,
            ):
                self.assertFalse(TranslateEngine(task_id)._complete_task(True))

            db.session.expire_all()
            stored = db.session.get(Translate, task_id)
            self.assertEqual(stored.status, 'failed')
            self.assertIsNone(stored.target_storage_key)
            self.assertNotIn('credential-bearing', stored.failed_reason)
            self.assertTrue(target.exists())
            db.session.delete(stored)
            db.session.commit()

    def test_babeldoc_output_is_moved_to_unchanged_target_name(self):
        class TranslateResult:
            no_watermark_mono_pdf_path = None
            mono_pdf_path = None

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            intermediate = temp_dir / 'report.v2.no_watermark.en.mono.pdf'
            intermediate.write_bytes(b'translated-pdf')
            target = temp_dir / 'report.v2.pdf'
            target.write_bytes(b'stale-result')
            result = TranslateResult()
            result.no_watermark_mono_pdf_path = intermediate

            final_path = move_babeldoc_output(
                {'type': 'finish', 'translate_result': result},
                target,
            )

            self.assertEqual(final_path, target)
            self.assertEqual(target.read_bytes(), b'translated-pdf')
            self.assertFalse(intermediate.exists())

    @patch('app.translate.to_translate.error')
    @patch('app.translate.to_translate.db.execute', return_value=True)
    @patch('app.translate.to_translate._translate_text_block')
    def test_nonfatal_block_failure_fails_batch(self, translate_block, execute, mark_error):
        translate_block.side_effect = [
            RuntimeError('bad block'),
            {'translated_text': 'translated', 'count': 10},
        ]
        texts = [
            {'text': 'first', 'complete': False},
            {'text': 'second', 'complete': False},
        ]
        success = to_translate.translate_batch(
            {'id': 8, 'threads': 1}, texts, Event()
        )
        self.assertFalse(success)
        mark_error.assert_called_once()
        self.assertIn('1个文本块', mark_error.call_args.args[1])

    @patch('app.resources.api.doc2x.Doc2XService.start_task', return_value='doc2x-uid')
    def test_doc2x_uses_source_size_without_double_charging(self, start_task):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pdf'
            source.write_bytes(b'%PDF-physical-size')
            physical_size = source.stat().st_size
            with self.app.app_context():
                customer = db.session.get(Customer, self.first_id)
                initial_storage = customer.storage
                customer.storage += physical_size
                record = Translate(
                    uuid='doc2x-source-uuid',
                    customer_id=self.first_id,
                    origin_filename='source.pdf',
                    origin_filepath=str(source),
                    target_filepath='',
                    status='none',
                    deleted_flag='N',
                    origin_filesize=physical_size,
                    size=physical_size,
                )
                db.session.add(record)
                db.session.commit()
                record_id = record.id

            response = self.client.post(
                '/api/doc2x/start',
                headers={'token': self.user_token},
                data={
                    'server': 'doc2x',
                    'doc2x_secret_key': 'secret',
                    'lang': 'zh',
                    'file_name': 'source.pdf',
                    'translate_id': str(record_id),
                    'size': '999999999',
                },
            )
            self.assertEqual(response.status_code, 200)
            with self.app.app_context():
                customer = db.session.get(Customer, self.first_id)
                record = db.session.get(Translate, record_id)
                self.assertEqual(record.size, physical_size)
                self.assertEqual(customer.storage, initial_storage + physical_size)

    def test_queue_deduplicates_and_recovers_expired_leases(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.app.app_context():
            db.session.query(Job).delete()
            text_task = Translate(
                uuid='queue-text-task',
                customer_id=self.first_id,
                origin_filename='notes.txt',
                origin_filepath=str(Path(temp_dir) / 'notes.txt'),
                target_filepath=str(Path(temp_dir) / 'translated.txt'),
                status='none',
                deleted_flag='N',
            )
            pdf_task = Translate(
                uuid='queue-pdf-task',
                customer_id=self.first_id,
                origin_filename='report.pdf',
                origin_filepath=str(Path(temp_dir) / 'report.pdf'),
                target_filepath=str(Path(temp_dir) / 'translated.pdf'),
                status='none',
                deleted_flag='N',
            )
            db.session.add_all([text_task, pdf_task])
            db.session.commit()

            enqueue_translation(text_task.id)
            enqueue_translation(text_task.id)
            enqueue_translation(pdf_task.id)
            self.assertEqual(Job.query.count(), 2)
            self.assertEqual(
                {job.queue for job in Job.query.all()}, {'default', 'pdf'}
            )

            first_claim = claim_next_job('default', lease_seconds=1)
            self.assertEqual(first_claim['payload']['translate_id'], text_task.id)
            self.assertIsNone(claim_next_job('default', lease_seconds=1))

            leased_job = db.session.get(Job, first_claim['id'])
            leased_job.reserved_at = int(time.time()) - 10
            db.session.commit()
            second_claim = claim_next_job('default', lease_seconds=1)
            self.assertEqual(second_claim['id'], first_claim['id'])
            self.assertEqual(second_claim['attempts'], 2)

            db.session.query(Job).delete()
            db.session.delete(text_task)
            db.session.delete(pdf_task)
            db.session.commit()

    def test_database_queue_is_the_default_backend(self):
        with self.app.app_context():
            self.assertEqual(queue_backend_name(), 'database')

    def test_celery_backend_routes_without_creating_database_job(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.app.app_context():
            db.session.query(Job).delete()
            source = Path(temp_dir) / 'celery-source.txt'
            source.write_text('source', encoding='utf-8')
            task = Translate(
                uuid='celery-routing-task',
                customer_id=self.first_id,
                origin_filename='celery-source.txt',
                origin_filepath=str(source),
                target_filepath=str(Path(temp_dir) / 'target.txt'),
                status='none',
                deleted_flag='N',
            )
            pdf_source = Path(temp_dir) / 'celery-source.pdf'
            pdf_source.write_bytes(b'%PDF-test')
            pdf_task = Translate(
                uuid='celery-routing-pdf-task',
                customer_id=self.first_id,
                origin_filename='celery-source.pdf',
                origin_filepath=str(pdf_source),
                target_filepath=str(Path(temp_dir) / 'target.pdf'),
                status='none',
                deleted_flag='N',
            )
            db.session.add_all([task, pdf_task])
            db.session.commit()
            task_id = task.id
            self.app.config['TRANSLATION_QUEUE_BACKEND'] = 'celery'
            try:
                with patch('app.task_queue._publish_celery') as publish:
                    self.assertTrue(
                        enqueue_translation(task_id, commit=False)
                    )
                    self.assertTrue(
                        enqueue_translation(pdf_task.id, commit=False)
                    )
                    self.assertEqual(publish.call_count, 2)
                    self.assertEqual(publish.call_args_list[0].args[2], DEFAULT_QUEUE)
                    self.assertEqual(publish.call_args_list[1].args[2], PDF_QUEUE)
                self.assertEqual(Job.query.count(), 0)
            finally:
                self.app.config['TRANSLATION_QUEUE_BACKEND'] = 'database'
                db.session.delete(task)
                db.session.delete(pdf_task)
                db.session.commit()

    def test_celery_task_registration_contract(self):
        class FakeCelery:
            def task(self, **options):
                self.options = options

                def decorator(function):
                    self.function = function
                    return function

                return decorator

        fake = FakeCelery()
        registered = register_tasks(fake)
        self.assertIs(registered, fake.function)
        self.assertEqual(
            fake.options['name'], 'app.celery_tasks.execute_translation'
        )
        self.assertTrue(fake.options['acks_late'])
        self.assertTrue(fake.options['reject_on_worker_lost'])
        self.assertTrue(fake.options['ignore_result'])

    def test_celery_lock_heartbeat_renews_the_full_ttl(self):
        lock = MagicMock()
        lock.extend.return_value = True
        stop_event = MagicMock()
        stop_event.wait.side_effect = [False, True]

        _refresh_lock(lock, stop_event)

        lock.extend.assert_called_once_with(
            TestingConfig.CELERY_LOCK_TIMEOUT,
            replace_ttl=True,
        )

    def test_redelivered_celery_task_waits_for_active_lock(self):
        class FakeCelery:
            def task(self, **_options):
                return lambda function: function

        task = SimpleNamespace(
            request=SimpleNamespace(
                delivery_info={'redelivered': True},
                retries=0,
            ),
            max_retries=TestingConfig.CELERY_MAX_RETRIES,
            retry=MagicMock(side_effect=Retry()),
        )
        execute_translation = register_tasks(FakeCelery())

        with patch(
            'app.celery_tasks.create_app', return_value=self.app
        ), patch('app.celery_tasks._translation_lock', return_value=None):
            with self.assertRaises(Retry):
                execute_translation(task, 123)

        task.retry.assert_called_once_with(
            countdown=max(15, TestingConfig.CELERY_LOCK_TIMEOUT // 2),
            max_retries=100,
        )

    def test_database_worker_exits_when_celery_backend_is_selected(self):
        import worker

        previous_backend = self.app.config['TRANSLATION_QUEUE_BACKEND']
        self.app.config['TRANSLATION_QUEUE_BACKEND'] = 'celery'
        try:
            with patch('worker.create_app', return_value=self.app), patch(
                'worker.ThreadPoolExecutor'
            ) as executor:
                worker.run_worker()
            executor.assert_not_called()
        finally:
            self.app.config['TRANSLATION_QUEUE_BACKEND'] = previous_backend

    def test_celery_config_requires_broker_url(self):
        class MissingBrokerConfig(TestingConfig):
            TRANSLATION_QUEUE_BACKEND = 'celery'
            CELERY_BROKER_URL = ''

        with self.assertRaisesRegex(RuntimeError, 'CELERY_BROKER_URL'):
            create_app(MissingBrokerConfig)

        class InvalidBrokerConfig(TestingConfig):
            TRANSLATION_QUEUE_BACKEND = 'celery'
            CELERY_BROKER_URL = 'amqp://broker'

        with self.assertRaisesRegex(RuntimeError, 'redis://'):
            create_app(InvalidBrokerConfig)

    def test_invalid_queue_backend_is_rejected(self):
        class InvalidQueueConfig(TestingConfig):
            TRANSLATION_QUEUE_BACKEND = 'sidekiq'

        with self.assertRaisesRegex(RuntimeError, 'database或celery'):
            create_app(InvalidQueueConfig)

    def test_zip_rejects_path_traversal(self):
        archive_bytes = BytesIO()
        with zipfile.ZipFile(archive_bytes, 'w') as archive:
            archive.writestr('../outside.txt', 'unsafe')
        archive_bytes.seek(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(archive_bytes) as archive:
                with self.assertRaisesRegex(ValueError, '非法路径'):
                    extract_zip_documents(
                        archive,
                        Path(temp_dir) / 'source',
                        Path(temp_dir) / 'result',
                        max_files=5,
                        max_file_size=1024,
                        max_total_size=2048,
                        max_compression_ratio=10,
                    )

    def test_exhausted_queue_job_marks_translation_failed(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.app.app_context():
            db.session.query(Job).delete()
            db.session.query(FailedJob).delete()
            task = Translate(
                uuid='exhausted-queue-task',
                customer_id=self.first_id,
                origin_filename='source.txt',
                origin_filepath=str(Path(temp_dir) / 'source.txt'),
                target_filepath=str(Path(temp_dir) / 'target.txt'),
                status='process',
                deleted_flag='N',
            )
            db.session.add(task)
            db.session.commit()
            enqueue_translation(task.id)
            job = Job.query.one()
            job.attempts = 3
            db.session.commit()

            retry_or_fail_job(job.id, RuntimeError('worker crashed'))
            db.session.refresh(task)
            self.assertEqual(task.status, 'failed')
            self.assertIn('worker crashed', task.failed_reason)
            self.assertEqual(Job.query.count(), 0)
            self.assertEqual(FailedJob.query.count(), 1)

            db.session.query(FailedJob).delete()
            db.session.delete(task)
            db.session.commit()

    def test_zip_batch_api_preserves_paths_and_checks_ownership(self):
        archive_bytes = BytesIO()
        with zipfile.ZipFile(archive_bytes, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('reports/quarter.txt', 'quarter source')
            archive.writestr('notes.txt', 'notes source')
        archive_bytes.seek(0)

        response = self.client.post(
            '/api/translate/batches/zip',
            headers={'token': self.user_token},
            data={
                'file': (archive_bytes, 'source-documents.zip'),
                'server': 'openai',
                'model': 'model-a',
                'lang': '英语',
                'prompt': 'Translate',
                'threads': '2',
                'api_url': 'https://api.example.com',
                'api_key': 'secret',
            },
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()['data']
        batch_id = payload['batch_id']
        self.assertEqual(payload['total'], 2)

        denied = self.client.get(
            f'/api/translate/batches/{batch_id}',
            headers={'token': self.second_token},
        )
        self.assertEqual(denied.status_code, 404)

        with self.app.app_context():
            batch = db.session.get(TranslateBatch, batch_id)
            tasks = Translate.query.filter_by(batch_id=batch_id).all()
            self.assertEqual(batch.origin_filename, 'source-documents.zip')
            self.assertEqual(
                {task.batch_relative_path for task in tasks},
                {'reports/quarter.txt', 'notes.txt'},
            )
            for task in tasks:
                output = Path(task.target_filepath)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(f'translated {task.origin_filename}', encoding='utf-8')
                task.status = 'done'
                task.process = 100
            db.session.commit()

        detail = self.client.get(
            f'/api/translate/batches/{batch_id}',
            headers={'token': self.user_token},
        )
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()['data']['status'], 'done')
        batch_list = self.client.get(
            '/api/translate/batches', headers={'token': self.user_token}
        )
        self.assertEqual(batch_list.status_code, 200)
        self.assertIn(
            batch_id,
            {item['id'] for item in batch_list.get_json()['data']['batches']},
        )

        download = self.client.get(
            f'/api/translate/batches/{batch_id}/download',
            headers={'token': self.user_token},
        )
        self.assertEqual(download.status_code, 200)
        with zipfile.ZipFile(BytesIO(download.data)) as result_archive:
            self.assertEqual(
                set(result_archive.namelist()),
                {'reports/quarter.txt', 'notes.txt'},
            )
        download.close()

        with self.app.app_context():
            removed_task = Translate.query.filter_by(batch_id=batch_id).first()
            removed_task.deleted_flag = 'Y'
            db.session.commit()
        partial = self.client.get(
            f'/api/translate/batches/{batch_id}',
            headers={'token': self.user_token},
        )
        self.assertEqual(partial.get_json()['data']['status'], 'partial')
        self.assertEqual(partial.get_json()['data']['failed'], 1)
        self.assertEqual(partial.get_json()['data']['total'], 2)

        with self.app.app_context():
            batch_root = (
                Path(self.app.root_path).parent / 'storage' / 'batches' / batch_id
            )
            task_ids = [
                task.id for task in Translate.query.filter_by(batch_id=batch_id).all()
            ]
            db.session.query(Job).delete()
            Translate.query.filter(Translate.id.in_(task_ids)).delete(
                synchronize_session=False
            )
            db.session.delete(db.session.get(TranslateBatch, batch_id))
            db.session.commit()
            remove_batch_directory(batch_root)

    def test_existing_files_can_be_started_as_one_batch(self):
        with tempfile.TemporaryDirectory() as temp_dir, self.app.app_context():
            tasks = []
            for index in range(2):
                source = Path(temp_dir) / f'source-{index}.txt'
                source.write_text(f'source {index}', encoding='utf-8')
                task = Translate(
                    uuid=f'existing-batch-{index}',
                    customer_id=self.first_id,
                    origin_filename=f'document-{index}.txt',
                    origin_filepath=str(source),
                    target_filepath='',
                    status='none',
                    deleted_flag='N',
                )
                db.session.add(task)
                tasks.append(task)
            db.session.commit()
            task_ids = [task.id for task in tasks]

        response = self.client.post(
            '/api/translate/batches',
            headers={'token': self.user_token},
            json={
                'translate_ids': task_ids,
                'server': 'openai',
                'model': 'model-a',
                'lang': '英语',
                'prompt': 'Translate',
                'threads': 2,
                'api_url': 'https://api.example.com',
                'api_key': 'secret',
            },
        )
        self.assertEqual(response.status_code, 200)
        batch_id = response.get_json()['data']['batch_id']

        with self.app.app_context():
            queued = Translate.query.filter(Translate.id.in_(task_ids)).all()
            self.assertTrue(all(task.batch_id == batch_id for task in queued))
            self.assertEqual(Job.query.count(), 2)
            db.session.query(Job).delete()
            Translate.query.filter(Translate.id.in_(task_ids)).delete(
                synchronize_session=False
            )
            db.session.delete(db.session.get(TranslateBatch, batch_id))
            db.session.commit()


class TermMatchingTests(unittest.TestCase):
    def test_pure_cjk_term_matches_adjacent_particles(self):
        match = to_translate._is_term_matched_in_text
        self.assertTrue(match('试验', '试验的数据表明该方法有效。'))
        self.assertTrue(match('客户声音报告', '内部的客户声音报告显示增长。'))
        self.assertTrue(match('客户声音报告', '的客户声音报告'))
        self.assertTrue(match('试验', '这是试验，注意安全。'))

    def test_pure_cjk_japanese_term_matches_adjacent_particles(self):
        match = to_translate._is_term_matched_in_text
        self.assertTrue(match('機械学習', '機械学習のモデル'))
        self.assertTrue(match('機械学習', '先進的な機械学習'))
        self.assertTrue(match('データ', 'このデータを分析する'))

    def test_pure_cjk_term_still_matches_punctuation_boundaries(self):
        self.assertTrue(
            to_translate._is_term_matched_in_text('大家好', '大家好。')
        )

    def test_pure_cjk_term_absent_text_not_matched(self):
        match = to_translate._is_term_matched_in_text
        self.assertFalse(match('试验', '没有任何相关词汇'))
        self.assertFalse(match('数据库', 'The database is large.'))
        self.assertFalse(match('', '任意文本'))
        self.assertFalse(match('试验', ''))

    def test_non_cjk_terms_keep_original_strategies(self):
        match = to_translate._is_term_matched_in_text
        self.assertTrue(match('database', 'The database is large.'))
        self.assertFalse(match('database', 'The databases are large.'))
        self.assertTrue(match('API接口', '使用API接口进行调用'))

    def _inject(self, term_pairs, text):
        trans = {
            'terms_dict': [
                {'source': source, 'target': target}
                for source, target in term_pairs
            ]
        }
        return to_translate._inject_matched_terms(
            trans, text, '请将以下文本翻译成{target_lang}：', '日语'
        )

    def test_cjk_short_term_fully_covered_by_longer_term_dropped(self):
        prompt = self._inject(
            [('人工', 'マニュアル'), ('人工智能', '人工知能')],
            '人工智能正在改变世界。',
        )
        self.assertIn('人工智能 → 人工知能', prompt)
        self.assertNotIn('人工 → マニュアル', prompt)

    def test_cjk_short_term_with_independent_hit_kept(self):
        prompt = self._inject(
            [('人工', 'マニュアル'), ('人工智能', '人工知能')],
            '人工智能与人工审核流程。',
        )
        self.assertIn('人工智能 → 人工知能', prompt)
        self.assertIn('人工 → マニュアル', prompt)

    def test_cjk_nested_terms_keep_longest_only(self):
        prompt = self._inject(
            [('智能', 'A'), ('人工智能', 'B'), ('人工智能芯片', 'C')],
            '人工智能芯片发布了。',
        )
        self.assertIn('人工智能芯片 → C', prompt)
        self.assertNotIn('人工智能 → B', prompt)
        self.assertNotIn('智能 → A', prompt)

    def test_japanese_nested_terms_keep_longest_only(self):
        prompt = self._inject(
            [('データ', 'A'), ('データベース', 'B')],
            'データベースを更新する。',
        )
        self.assertIn('データベース → B', prompt)
        self.assertNotIn('データ → A', prompt)

    def test_japanese_short_term_with_independent_hit_kept(self):
        prompt = self._inject(
            [('データ', 'A'), ('データベース', 'B')],
            'データベースとデータを分析する。',
        )
        self.assertIn('データベース → B', prompt)
        self.assertIn('データ → A', prompt)

    def test_cjk_particle_fix_survives_term_filter(self):
        prompt = self._inject(
            [('试验', 'テスト')],
            '试验的数据表明该方法有效。',
        )
        self.assertIn('试验 → テスト', prompt)

    def test_injected_terms_sorted_longest_first(self):
        prompt = self._inject(
            [('database', '数据库'), ('database field', '数据库字段')],
            'The database field is large.',
        )
        self.assertLess(
            prompt.index('database field → 数据库字段'),
            prompt.index('database → 数据库'),
        )


if __name__ == '__main__':
    unittest.main()
