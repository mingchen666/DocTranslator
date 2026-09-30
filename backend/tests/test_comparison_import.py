from io import BytesIO
import unittest

import pandas as pd
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.comparison import Comparison
from app.models.customer import Customer
from migrate_startup import run_migrations


class ComparisonImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestingConfig)
        run_migrations(cls.app, seed=True)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            user = Customer(
                email='glossary-import@example.com',
                password='unused',
                storage=0,
                total_storage=1024 * 1024,
            )
            db.session.add(user)
            db.session.commit()
            cls.user_id = user.id
            cls.user_token = create_access_token(
                identity=str(user.id), additional_claims={'role': 'user'}
            )

    def test_import_excel_recognizes_rows_from_third_line(self):
        output = BytesIO()
        pd.DataFrame(
            [
                {'源术语': '苹果', '目标术语': 'apple'},
                {'源术语': '香蕉', '目标术语': 'banana'},
                {'源术语': '橙子', '目标术语': 'orange'},
            ]
        ).to_excel(output, index=False)
        output.seek(0)

        response = self.client.post(
            '/api/comparison/import',
            headers={'token': self.user_token},
            data={'file': (output, 'terms.xlsx')},
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        comparison_id = response.get_json()['data']['id']

        listed = self.client.get(
            '/api/comparison/my',
            headers={'token': self.user_token},
        )
        self.assertEqual(listed.status_code, 200)
        items = listed.get_json()['data']['data']
        imported = next(item for item in items if item['id'] == comparison_id)
        self.assertEqual(
            [term['origin'] for term in imported['content']],
            ['苹果', '香蕉', '橙子'],
        )

        with self.app.app_context():
            saved = db.session.get(Comparison, comparison_id)
            self.assertIn('; ', saved.content)