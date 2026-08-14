import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup
from openpyxl import Workbook

from app.config import Config
from app.resources.api.translate import (
    TranslateStartValidationError,
    _validate_translate_start,
)
from app.resources.api.translate_batch import _validate_batch_sources
from app.translate import csv_handle, excel, html, md, to_translate
from app.translate.batch_service import extract_zip_documents


class TranslationQualityTests(unittest.TestCase):
    def test_legacy_office_extensions_are_not_allowed(self):
        self.assertNotIn('doc', Config.ALLOWED_EXTENSIONS)
        self.assertNotIn('xls', Config.ALLOWED_EXTENSIONS)
        self.assertNotIn('ppt', Config.ALLOWED_EXTENSIONS)
        with self.assertRaisesRegex(TranslateStartValidationError, '旧版Office'):
            _validate_translate_start(
                {
                    'server': 'openai',
                    'model': 'model',
                    'uuid': 'uuid',
                    'prompt': 'Translate',
                    'file_name': 'legacy.doc',
                    'threads': '1',
                    'lang': '英语',
                    'api_url': 'https://api.example.com',
                    'api_key': 'secret',
                },
                SimpleNamespace(level='normal'),
                {},
            )

    def test_baidu_pdf_is_rejected_before_queueing(self):
        with self.assertRaisesRegex(TranslateStartValidationError, '百度翻译.*PDF'):
            _validate_translate_start(
                {
                    'server': 'baidu',
                    'model': 'ignored',
                    'uuid': 'uuid',
                    'prompt': 'Translate',
                    'file_name': 'report.pdf',
                    'threads': '1',
                    'to_lang': 'en',
                    'app_id': 'appid',
                    'app_key': 'appkey',
                },
                SimpleNamespace(level='normal'),
                {},
            )
        with self.assertRaisesRegex(TranslateStartValidationError, '百度翻译.*PDF'):
            _validate_batch_sources(['notes.txt', 'report.pdf'], 'baidu')

    def test_zip_rejects_legacy_office_member(self):
        archive_bytes = BytesIO()
        with zipfile.ZipFile(archive_bytes, 'w') as archive:
            archive.writestr('legacy.doc', b'old office')
        archive_bytes.seek(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(archive_bytes) as archive:
                with self.assertRaisesRegex(ValueError, '旧版Office'):
                    extract_zip_documents(
                        archive,
                        Path(temp_dir) / 'source',
                        Path(temp_dir) / 'result',
                        max_files=5,
                        max_file_size=1024,
                        max_total_size=2048,
                        max_compression_ratio=10,
                    )

    def test_spreadsheet_formulas_are_skipped(self):
        self.assertFalse(excel._should_translate('=SUM(A1:A3)'))
        self.assertFalse(csv_handle._should_translate('=SUM(A1:A3)'))

        workbook = Workbook()
        worksheet = workbook.active
        worksheet['A1'] = '=SUM(B1:B2)'
        worksheet['B1'] = 'Translate this'
        texts = []
        cell_map = []
        excel._extract_sheet_texts(worksheet, 'Sheet', texts, cell_map)
        self.assertEqual([item['original'] for item in texts], ['Translate this'])
        self.assertEqual(cell_map[0]['row'], 1)
        self.assertEqual(cell_map[0]['col'], 2)

    def test_html_translation_is_inserted_as_text(self):
        soup = BeautifulSoup(
            '<p>Hello</p><img alt="Image description">',
            'html.parser',
        )
        placeholder_map = {}
        extracted = []
        html._extract_and_placeholder(soup, placeholder_map, extracted)
        texts = html._build_text_items(extracted)
        for item in texts:
            if item.get('skip'):
                continue
            item['text'] = '<b>A & B</b>' if item['original'] == 'Hello' else 'A & B'
            item['complete'] = True

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / 'translated.html'
            html._write_result(
                {'target_file': str(target)},
                texts,
                extracted,
                placeholder_map,
                soup,
            )
            output = BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser')

        self.assertEqual(output.p.string, '<b>A & B</b>')
        self.assertIsNone(output.p.find('b'))
        self.assertEqual(output.img['alt'], 'A & B')

    def test_markdown_protected_tokens_must_survive_translation(self):
        processed, protected = md._protect_special_syntax(
            'Read `code()` and [the docs](https://example.com).'
        )
        texts = md._smart_chunk_markdown(processed)
        md._validate_protected_token_assignment(texts, protected)
        translated_item = next(item for item in texts if not item.get('skip'))
        tokens = translated_item['protected_tokens']
        self.assertTrue(tokens)
        self.assertTrue(
            to_translate._preserves_protected_tokens(
                translated_item,
                translated_item['text'],
            )
        )
        self.assertFalse(
            to_translate._preserves_protected_tokens(
                translated_item,
                translated_item['text'].replace(tokens[0], ''),
            )
        )
        self.assertFalse(
            to_translate._preserves_protected_tokens(
                translated_item,
                translated_item['text'] + tokens[0],
            )
        )

    @patch('app.translate.to_translate.time.sleep')
    @patch('app.translate.to_translate._translate_openai', return_value='missing token')
    def test_token_mismatch_exhausts_translation_retries(self, translate_openai, sleep):
        result = to_translate._try_translate_with_retries(
            {'id': 1, 'server': 'openai'},
            {
                'text': 'source ⟦CODE_BLOCK_1⟧',
                'protected_tokens': ['⟦CODE_BLOCK_1⟧'],
            },
            'model',
        )
        self.assertIsNone(result)
        self.assertEqual(translate_openai.call_count, to_translate.MAX_RETRIES)


if __name__ == '__main__':
    unittest.main()
