"""备注页与图表文本（图表标题、坐标轴标题、系列名、分类名）翻译的回归测试。"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches

from app.translate import powerpoint

CHART_NS = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}

REPLACEMENTS = {
    'Quarterly revenue': 'Chiffre affaires trimestriel',
    'Sales revenue': 'Chiffre affaires',
    'Operating cost': 'Cout operationnel',
    'First quarter': 'Premier trimestre',
    'Second quarter': 'Deuxieme trimestre',
    'Speaker note: explain the growth.': 'Note du presentateur: expliquer la croissance.',
    'Revenue by quarter': 'Chiffre affaires par trimestre',
}


def _fake_translate_batch(trans, texts, event):
    for item in texts:
        translated = item['text']
        for original, replacement in REPLACEMENTS.items():
            translated = translated.replace(original, replacement)
        item['text'] = translated
        item['count'] = 1
        item['complete'] = True
        item['fallback_used'] = False
    return True


def _empty_translate_batch(trans, texts, event):
    for item in texts:
        item['text'] = ''
        item['count'] = 1
        item['complete'] = True
        item['fallback_used'] = False
    return True


def _add_chart(slide):
    chart_data = CategoryChartData()
    chart_data.categories = ['First quarter', 'Second quarter']
    chart_data.add_series('Sales revenue', (1.0, 2.0))
    chart_data.add_series('Operating cost', (0.5, 1.2))
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.5), Inches(2.0), Inches(6.0), Inches(4.0), chart_data,
    ).chart
    chart.has_title = True
    chart.chart_title.text_frame.text = 'Quarterly revenue'
    chart.category_axis.has_title = True
    chart.category_axis.axis_title.text_frame.text = 'Revenue by quarter'
    return chart


def _build_presentation(path: Path, with_notes: bool = True, second_slide_notes: bool = False):
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    textbox = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(6.0), Inches(1.0))
    textbox.text_frame.text = 'Quarterly revenue'
    _add_chart(slide)
    if with_notes:
        slide.notes_slide.notes_text_frame.text = 'Speaker note: explain the growth.'

    second = presentation.slides.add_slide(presentation.slide_layouts[6])
    second_box = second.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(6.0), Inches(1.0))
    second_box.text_frame.text = 'Quarterly revenue'
    if second_slide_notes:
        second.notes_slide.notes_text_frame.text = 'Speaker note: explain the growth.'

    presentation.save(path)


def _chart_of(slide):
    for shape in slide.shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.CHART or getattr(shape, 'has_chart', False):
            return shape.chart
    raise AssertionError('slide has no chart')


def _chart_title(chart):
    return chart.chart_title.text_frame.text


def _chart_names(chart, path):
    return [node.text for node in chart._element.findall(path, CHART_NS)]


class PptxNotesAndChartTests(unittest.TestCase):
    def _run(self, source: Path, target: Path, mode: str = 'trans_all_only_inherit',
             batch=_fake_translate_batch):
        with patch.object(powerpoint.to_translate, 'translate_batch', batch), \
                patch.object(powerpoint.to_translate, 'complete', return_value=True), \
                patch.object(powerpoint.to_translate, 'error'):
            return powerpoint.start({
                'id': 21,
                'file_path': str(source),
                'target_file': str(target),
                'type': mode,
                'lang': '法语',
            })

    def test_notes_page_text_is_translated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            target = Path(temp_dir) / 'target.pptx'
            _build_presentation(source)
            self.assertTrue(self._run(source, target))

            slide = Presentation(target).slides[0]
            self.assertTrue(slide.has_notes_slide)
            self.assertEqual(
                slide.notes_slide.notes_text_frame.text,
                REPLACEMENTS['Speaker note: explain the growth.'],
            )

    def test_chart_title_and_axis_title_are_translated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            target = Path(temp_dir) / 'target.pptx'
            _build_presentation(source)
            self.assertTrue(self._run(source, target))

            chart = _chart_of(Presentation(target).slides[0])
            self.assertEqual(_chart_title(chart), REPLACEMENTS['Quarterly revenue'])
            self.assertEqual(
                chart.category_axis.axis_title.text_frame.text,
                REPLACEMENTS['Revenue by quarter'],
            )

    def test_chart_series_and_category_names_are_translated_in_every_series(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            target = Path(temp_dir) / 'target.pptx'
            _build_presentation(source)
            self.assertTrue(self._run(source, target))

            chart = _chart_of(Presentation(target).slides[0])
            self.assertEqual(
                _chart_names(chart, './/c:ser/c:tx//c:v'),
                [REPLACEMENTS['Sales revenue'], REPLACEMENTS['Operating cost']],
            )
            categories = _chart_names(chart, './/c:cat//c:strCache/c:pt/c:v')
            self.assertEqual(
                categories,
                [REPLACEMENTS['First quarter'], REPLACEMENTS['Second quarter']] * 2,
            )

    def test_equal_chart_labels_share_a_single_translation_block(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            _build_presentation(source)
            blocks = powerpoint._extract_all_blocks(Presentation(source))
            chart_blocks = [
                block for block in blocks if block.location_type == 'chart_node'
            ]
            # 2 个系列名 + 2 个分类名（同一分类在两个系列中各有一份缓存）
            self.assertEqual(
                sorted(block.original_text for block in chart_blocks),
                sorted(['Sales revenue', 'Operating cost', 'First quarter', 'Second quarter']),
            )

    def test_extraction_does_not_create_missing_notes_slide(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            _build_presentation(source, with_notes=False)
            presentation = Presentation(source)
            powerpoint._extract_all_blocks(presentation)
            for slide in presentation.slides:
                self.assertFalse(slide.has_notes_slide)

    def test_empty_translation_keeps_source_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            target = Path(temp_dir) / 'target.pptx'
            _build_presentation(source)
            self.assertTrue(self._run(source, target, batch=_empty_translate_batch))

            slide = Presentation(target).slides[0]
            self.assertEqual(
                slide.notes_slide.notes_text_frame.text,
                'Speaker note: explain the growth.',
            )
            chart = _chart_of(slide)
            self.assertEqual(_chart_title(chart), 'Quarterly revenue')
            self.assertEqual(
                _chart_names(chart, './/c:ser/c:tx//c:v'),
                ['Sales revenue', 'Operating cost'],
            )

    def test_bilingual_mode_still_validates_with_notes_and_charts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / 'source.pptx'
            target = Path(temp_dir) / 'target.pptx'
            _build_presentation(source, second_slide_notes=True)
            source_snapshot = powerpoint._snapshot_slide(Presentation(source).slides[0])
            self.assertTrue(self._run(source, target, mode='trans_all_both_inherit'))

            output = Presentation(target)
            self.assertEqual(len(output.slides), 4)
            self.assertEqual(
                powerpoint._snapshot_slide(output.slides[0]), source_snapshot
            )
            self.assertEqual(
                powerpoint._snapshot_slide(output.slides[0])['structure'],
                powerpoint._snapshot_slide(output.slides[1])['structure'],
            )
            self.assertEqual(
                output.slides[0].notes_slide.notes_text_frame.text,
                REPLACEMENTS['Speaker note: explain the growth.'],
            )
            self.assertEqual(
                _chart_title(_chart_of(output.slides[1])), REPLACEMENTS['Quarterly revenue']
            )


if __name__ == '__main__':
    unittest.main()
