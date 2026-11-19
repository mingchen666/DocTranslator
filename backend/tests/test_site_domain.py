import unittest

from flask_jwt_extended import create_access_token

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Setting
from app.utils.site_domain import (
    DomainValidationError,
    get_site_domain_config,
    normalize_project_domain,
)
from app.script.insert_init_db import insert_initial_settings
from migrate_startup import run_migrations


class SiteDomainNormalizationTests(unittest.TestCase):
    def test_accepts_host_without_scheme_and_adds_http(self):
        self.assertEqual(
            normalize_project_domain('192.168.1.10:35555'),
            'http://192.168.1.10:35555',
        )
        self.assertEqual(
            normalize_project_domain('Example.COM:35555/'),
            'http://example.com:35555',
        )

    def test_keeps_https_and_explicit_port(self):
        self.assertEqual(
            normalize_project_domain('https://dt.example.com:8443'),
            'https://dt.example.com:8443',
        )

    def test_supports_ipv6_literal(self):
        self.assertEqual(
            normalize_project_domain('http://[::1]:35555'),
            'http://[::1]:35555',
        )

    def test_rejects_paths_queries_and_credentials(self):
        for value in (
            'http://example.com:35555/app',
            'http://example.com:35555?x=1',
            'http://example.com:35555#top',
            'http://user:pass@example.com:35555',
            'ftp://example.com:35555',
        ):
            with self.subTest(value=value):
                with self.assertRaises(DomainValidationError):
                    normalize_project_domain(value)

    def test_rejects_invalid_ports(self):
        for value in ('http://example.com:0', 'http://example.com:65536', 'http://example.com:abc'):
            with self.subTest(value=value):
                with self.assertRaises(DomainValidationError):
                    normalize_project_domain(value)

    def test_missing_value_is_rejected(self):
        for value in ('', '   ', None):
            with self.subTest(value=value):
                with self.assertRaises(DomainValidationError):
                    normalize_project_domain(value)


class FreshInstallSiteDomainTests(unittest.TestCase):
    def test_empty_database_seeds_explicit_auto_mode(self):
        import os
        import tempfile

        handle, db_path = tempfile.mkstemp(suffix='.sqlite')
        os.close(handle)
        try:
            class FreshTestingConfig(TestingConfig):
                SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

            app = create_app(FreshTestingConfig)
            run_migrations(app, seed=True)
            payload = app.test_client().get('/api/common/site-config').get_json()['data']
            self.assertTrue(payload['configured'])
            self.assertFalse(payload['legacy'])
            self.assertEqual(payload['domain_mode'], 'auto')
            self.assertIsNone(payload['api_prefix'])
        finally:
            os.unlink(db_path)


class SiteDomainApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestingConfig)
        run_migrations(cls.app, seed=True)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            admin_token = create_access_token(
                identity='site-config-admin', additional_claims={'role': 'admin'}
            )
        cls.admin_headers = {'token': admin_token}

    def setUp(self):
        # 每个用例从「未配置」的历史站点开始，单独验证默认行为。
        with self.app.app_context():
            Setting.query.filter(
                Setting.alias.in_(('domain_mode', 'domain'))
            ).delete(synchronize_session=False)
            db.session.commit()

    def test_fresh_install_seeds_auto_mode(self):
        # 全新站点初始化时会显式写入 domain_mode=auto。
        insert_initial_settings(self.app, fresh_install=True)
        with self.app.app_context():
            config = get_site_domain_config()
        self.assertTrue(config['configured'])
        self.assertEqual(config['domain_mode'], 'auto')

    def test_existing_database_upgrade_keeps_legacy_default(self):
        # 非空数据库再次迁移不会补写 domain_mode，保持「沿用原部署配置」。
        run_migrations(self.app, seed=True)
        with self.app.app_context():
            config = get_site_domain_config()
        self.assertFalse(config['configured'])
        response = self.client.get('/api/common/site-config')
        payload = response.get_json()['data']
        self.assertTrue(payload['legacy'])
        self.assertIsNone(payload['api_prefix'])

    def test_public_endpoint_defaults_to_auto_legacy(self):
        response = self.client.get('/api/common/site-config')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()['data']
        self.assertEqual(payload['domain_mode'], 'legacy')
        self.assertTrue(payload['legacy'])
        self.assertIsNone(payload['project_url'])
        self.assertEqual(response.headers['Cache-Control'], 'no-store, no-cache, must-revalidate')

    def test_admin_get_includes_domain_settings(self):
        response = self.client.get(
            '/api/admin/setting/site', headers=self.admin_headers
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()['data']
        self.assertEqual(payload['version'], 'community')
        self.assertEqual(payload['domain_mode'], 'legacy')
        self.assertTrue(payload['legacy'])

    def test_manual_domain_round_trip(self):
        response = self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={
                'version': 'business',
                'domain_mode': 'manual',
                'domain': '192.168.1.10:35555',
            },
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()['data']
        self.assertEqual(payload['domain'], 'http://192.168.1.10:35555')
        self.assertEqual(payload['project_url'], 'http://192.168.1.10:35555')
        self.assertEqual(payload['api_prefix'], 'http://192.168.1.10:35555/api')

        public_payload = self.client.get('/api/common/site-config').get_json()['data']
        self.assertFalse(public_payload['legacy'])
        self.assertEqual(public_payload['domain_mode'], 'manual')
        self.assertEqual(public_payload['api_prefix'], 'http://192.168.1.10:35555/api')

    def test_auto_mode_keeps_manual_value_but_returns_no_prefix(self):
        self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'domain_mode': 'manual', 'domain': 'dt.example.com:35555'},
        )
        response = self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'domain_mode': 'auto'},
        )
        payload = response.get_json()['data']
        self.assertEqual(payload['domain_mode'], 'auto')
        self.assertEqual(payload['domain'], 'http://dt.example.com:35555')
        self.assertIsNone(payload['api_prefix'])

    def test_invalid_domain_is_rejected_without_changing_config(self):
        self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'domain_mode': 'manual', 'domain': 'http://dt.example.com:35555'},
        )
        response = self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'domain_mode': 'manual', 'domain': 'http://dt.example.com:35555/app'},
        )
        self.assertEqual(response.status_code, 400)
        public_payload = self.client.get('/api/common/site-config').get_json()['data']
        self.assertEqual(public_payload['domain'], 'http://dt.example.com:35555')

    def test_version_only_update_does_not_create_domain_rows(self):
        response = self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'version': 'business'},
        )
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            config = get_site_domain_config()
            version = Setting.query.filter_by(alias='version').first()
        self.assertFalse(config['configured'])
        self.assertEqual(version.value, 'business')

    def test_legacy_mode_can_be_saved_explicitly(self):
        response = self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'domain_mode': 'legacy'},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()['data']
        self.assertEqual(payload['domain_mode'], 'legacy')
        self.assertTrue(payload['legacy'])
        self.assertTrue(payload['configured'])
        self.assertIsNone(payload['api_prefix'])

        public_payload = self.client.get('/api/common/site-config').get_json()['data']
        self.assertEqual(public_payload['domain_mode'], 'legacy')
        self.assertTrue(public_payload['legacy'])

    def test_invalid_mode_is_rejected(self):
        response = self.client.post(
            '/api/admin/setting/site',
            headers=self.admin_headers,
            json={'domain_mode': 'proxy'},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
