import tempfile
import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask import Flask

from app.config import TestingConfig, normalize_oss_prefix
from app.result_storage import (
    FinalizedResult,
    LocalResultStorage,
    ResultStorage,
    ResultStorageError,
    build_object_key,
    commit_completed_result,
    get_record_storage,
    send_result_file,
)


class FakeOssStorage(ResultStorage):
    backend_name = 'oss'

    def __init__(self, fail_upload=False):
        self.objects = {}
        self.fail_upload = fail_upload

    def put_file(self, local_path, object_key, content_type=None):
        if self.fail_upload:
            raise ResultStorageError('fake upload failure')
        self.objects[object_key] = Path(local_path).read_bytes()

    @contextmanager
    def open_reader(self, record):
        key = record.target_storage_key
        if key not in self.objects:
            raise FileNotFoundError(key)
        with BytesIO(self.objects[key]) as reader:
            yield reader

    def exists(self, record):
        return record.target_storage_key in self.objects

    def delete(self, record):
        self.objects.pop(record.target_storage_key, None)

    def finalize_result(self, record):
        key = record.target_storage_key or build_object_key(record)
        self.put_file(record.target_filepath, key)
        record.target_storage_backend = 'oss'
        record.target_storage_key = key
        record.target_filesize = Path(record.target_filepath).stat().st_size
        return FinalizedResult('oss', key, record.target_filepath)


class ResultStorageUnitTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            RESULT_STORAGE_BACKEND='local',
            OSS_PREFIX='translations/',
            OSS_ENDPOINT='https://oss.example.test',
            OSS_BUCKET='private-bucket',
            OSS_ACCESS_KEY_ID='id',
            OSS_ACCESS_KEY_SECRET='secret',
        )

    def test_prefix_normalization_and_validation(self):
        self.assertEqual(normalize_oss_prefix('/results/path/'), 'results/path/')
        for invalid in ('', '../results', 'results\\private', 'bad\x00path'):
            with self.assertRaises(RuntimeError):
                normalize_oss_prefix(invalid)

    def test_oss_configuration_is_required_only_for_oss(self):
        class LocalConfig(TestingConfig):
            RESULT_STORAGE_BACKEND = 'local'
            OSS_PREFIX = 'translations/'
            OSS_ENDPOINT = ''
            OSS_BUCKET = ''
            OSS_ACCESS_KEY_ID = ''
            OSS_ACCESS_KEY_SECRET = ''

        LocalConfig.validate_result_storage()

        class MissingOssConfig(LocalConfig):
            RESULT_STORAGE_BACKEND = 'oss'

        with self.assertRaisesRegex(RuntimeError, 'OSS_ENDPOINT'):
            MissingOssConfig.validate_result_storage()

    def test_local_storage_reads_and_deletes_idempotently(self):
        storage = LocalResultStorage()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'result.txt'
            path.write_bytes(b'translated')
            record = SimpleNamespace(
                target_filepath=str(path),
                target_storage_backend=None,
                target_storage_key='stale-key',
                target_filesize=0,
            )
            result = storage.finalize_result(record)
            self.assertEqual(result.backend_name, 'local')
            self.assertEqual(record.target_storage_backend, 'local')
            self.assertIsNone(record.target_storage_key)
            self.assertEqual(record.target_filesize, 10)
            with storage.open_reader(record) as reader:
                self.assertEqual(reader.read(), b'translated')
            storage.delete(record)
            storage.delete(record)
            self.assertFalse(path.exists())

    def test_object_key_is_stable_private_and_uses_result_extension(self):
        with self.app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            record = SimpleNamespace(
                uuid=str(uuid.uuid4()),
                customer_id=987654,
                origin_filename='report.pdf',
                target_filepath=str(Path(temp_dir) / 'report_doc2x.docx'),
                created_at=datetime(2026, 7, 23, 12, 0, 0),
            )
            first = build_object_key(record)
            second = build_object_key(record)
            self.assertEqual(first, second)
            self.assertTrue(first.startswith('translations/2026/07/23/'))
            self.assertTrue(first.endswith('/report.docx'))
            self.assertNotIn(str(record.customer_id), first)

            record.origin_filename = '../secret.docx'
            with self.assertRaises(ValueError):
                build_object_key(record)

    def test_record_backend_routes_independently_of_current_backend(self):
        record = SimpleNamespace(target_storage_backend='oss')
        fake = FakeOssStorage()
        with self.app.app_context(), patch(
            'app.result_storage.get_result_storage', return_value=fake
        ) as factory:
            self.assertIs(get_record_storage(record), fake)
            factory.assert_called_once_with('oss')

    def test_oss_result_downloads_when_current_backend_is_local(self):
        fake = FakeOssStorage()
        record = SimpleNamespace(
            target_storage_backend='oss',
            target_storage_key='translations/task/result.txt',
            target_filepath='deleted-local-result.txt',
        )
        fake.objects[record.target_storage_key] = b'from oss'
        with self.app.test_request_context(), patch(
            'app.result_storage.get_result_storage', return_value=fake
        ) as factory:
            response = send_result_file(record, 'result.txt')
            response.direct_passthrough = False
            self.assertEqual(response.get_data(), b'from oss')
            response.close()
            factory.assert_called_once_with('oss')

    def test_upload_failure_does_not_assign_storage_key(self):
        fake = FakeOssStorage(fail_upload=True)
        with self.app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'result.txt'
            path.write_bytes(b'result')
            record = SimpleNamespace(
                uuid=str(uuid.uuid4()),
                origin_filename='result.txt',
                target_filepath=str(path),
                target_storage_key=None,
                created_at=datetime(2026, 7, 23),
            )
            with self.assertRaises(ResultStorageError):
                fake.finalize_result(record)
            self.assertIsNone(record.target_storage_key)
            self.assertTrue(path.exists())

    def test_database_commit_failure_removes_uploaded_object(self):
        fake = FakeOssStorage()
        with self.app.app_context(), tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'result.txt'
            path.write_bytes(b'result')
            record = SimpleNamespace(
                id=42,
                uuid=str(uuid.uuid4()),
                origin_filename='result.txt',
                target_filepath=str(path),
                target_storage_backend='local',
                target_storage_key=None,
                target_filesize=0,
                created_at=datetime(2026, 7, 23),
            )
            fake_db = SimpleNamespace(session=MagicMock())
            fake_db.session.commit.side_effect = RuntimeError('commit failed')
            with patch(
                'app.result_storage.get_result_storage', return_value=fake
            ), patch('app.extensions.db', fake_db):
                with self.assertRaises(RuntimeError):
                    commit_completed_result(record)
            self.assertEqual(fake.objects, {})
            self.assertTrue(path.exists())


if __name__ == '__main__':
    unittest.main()
