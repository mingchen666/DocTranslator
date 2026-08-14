"""High-fidelity translation for modern PowerPoint documents (.pptx)."""

import copy
import datetime
import logging
import math
import os
import re
from dataclasses import dataclass
from enum import Enum
from threading import Event
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from pptx.shapes.base import BaseShape
from pptx.shapes.placeholder import PlaceholderPicture
from pptx.text.text import TextFrame, _Paragraph, _Run

from . import common
from . import to_translate
from .pptx_inline import InlinePlan, TOKEN_RE, build_inline_plan


MIN_FONT_SCALE = 0.6
MIN_FONT_POINTS = 10.0
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


class ElementType(Enum):
    TITLE = 'title'
    SUBTITLE = 'subtitle'
    BODY = 'body'
    TABLE_CELL = 'table_cell'
    TEXT_BOX = 'text_box'
    OTHER = 'other'


@dataclass
class RunStyle:
    font_name: Optional[str] = None
    font_name_ea: Optional[str] = None
    font_size: Optional[int] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    color_rgb: Optional[RGBColor] = None


@dataclass(frozen=True)
class ShapeGeometry:
    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0


@dataclass
class TextBlock:
    uid: str
    slide_index: int
    shape_id: int
    element_type: ElementType
    location_type: str = 'textframe'
    paragraph_index: int = 0
    cell_row: int = -1
    cell_col: int = -1
    cell_paragraph_index: int = 0
    original_text: str = ''
    translated_text: str = ''
    geometry: Optional[ShapeGeometry] = None
    complete: bool = False
    skip: bool = False
    count: int = 0
    inline_plan: Optional[InlinePlan] = None
    fallback_used: bool = False


def start(trans: Dict[str, Any]) -> bool:
    """Translate a PPTX while preserving slide and shape structure."""
    translate_id = trans['id']
    start_time = datetime.datetime.now()
    is_bilingual = 'both' in trans.get('type', 'trans_only_inherit')
    target_lang = trans.get('lang', '英语')

    try:
        prs = Presentation(trans['file_path'])
        baseline = _capture_presentation_baseline(prs)
    except Exception as exc:
        logging.error('[任务%s] 打开PPTX失败: %s', translate_id, exc)
        to_translate.error(translate_id, f'打开PPTX失败: {exc}')
        return False

    try:
        all_blocks = _extract_all_blocks(prs)
    except Exception as exc:
        logging.error('[任务%s] 提取PPTX文本失败: %s', translate_id, exc)
        to_translate.error(translate_id, f'提取PPTX文本失败: {exc}')
        return False

    blocks_to_translate = [block for block in all_blocks if not block.skip]
    if not blocks_to_translate:
        try:
            _save_and_validate_presentation(
                prs, trans['target_file'], baseline, is_bilingual=False
            )
        except Exception as exc:
            logging.error('[任务%s] 保存PPTX失败: %s', translate_id, exc)
            to_translate.error(translate_id, f'保存PPTX失败: {exc}')
            return False
        return to_translate.complete(trans, 0, '0秒')

    logging.info(
        '[任务%s] PPTX共%s个文本块，%s个需要翻译',
        translate_id, len(all_blocks), len(blocks_to_translate),
    )
    texts = _blocks_to_api_format(blocks_to_translate)
    event = Event()
    if not to_translate.translate_batch(trans, texts, event):
        return False
    _sync_translation_results(blocks_to_translate, texts)

    try:
        if is_bilingual:
            text_count = _apply_bilingual_mode(prs, all_blocks, target_lang)
        else:
            text_count = _apply_translation_mode(prs, all_blocks, target_lang)
        _save_and_validate_presentation(
            prs, trans['target_file'], baseline, is_bilingual=is_bilingual
        )
    except Exception as exc:
        logging.exception('[任务%s] PPTX写回或验收失败', translate_id)
        _remove_invalid_output(trans.get('target_file'))
        to_translate.error(translate_id, f'PPTX写回或验收失败: {exc}')
        return False

    spend_time = common.display_spend(start_time, datetime.datetime.now())
    return to_translate.complete(trans, text_count, spend_time)


def _extract_all_blocks(prs: Presentation) -> List[TextBlock]:
    blocks: List[TextBlock] = []
    uid_counter = 0

    def next_uid() -> str:
        nonlocal uid_counter
        uid_counter += 1
        return f'pptx_{uid_counter}'

    for slide_index, slide in enumerate(prs.slides):
        for shape in slide.shapes:
            blocks.extend(_extract_shape_blocks(shape, slide_index, next_uid))
    return blocks


def _extract_shape_blocks(shape: BaseShape, slide_index: int, next_uid) -> List[TextBlock]:
    if _is_nontext_object(shape):
        return []
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        blocks: List[TextBlock] = []
        for child in shape.shapes:
            blocks.extend(_extract_shape_blocks(child, slide_index, next_uid))
        return blocks

    geometry = _get_shape_geometry(shape)
    if shape.has_table:
        return _extract_table_blocks(
            shape.table, slide_index, shape.shape_id, geometry, next_uid
        )
    if shape.has_text_frame:
        return _extract_textframe_blocks(
            shape.text_frame,
            slide_index,
            shape.shape_id,
            _identify_element_type(shape),
            geometry,
            next_uid,
        )
    return []


def _is_nontext_object(shape: BaseShape) -> bool:
    if _is_picture(shape) or _is_chart(shape):
        return True
    try:
        return shape.shape_type in {
            MSO_SHAPE_TYPE.MEDIA,
            MSO_SHAPE_TYPE.EMBEDDED_OLE_OBJECT,
            MSO_SHAPE_TYPE.LINKED_OLE_OBJECT,
            MSO_SHAPE_TYPE.IGX_GRAPHIC,
        }
    except Exception:
        return False


def _is_picture(shape: BaseShape) -> bool:
    try:
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE or isinstance(shape, PlaceholderPicture):
            return True
    except Exception:
        pass
    try:
        blips = shape._element.findall('.//' + qn('a:blip'))
        return bool(blips and (not shape.has_text_frame or not shape.text_frame.text.strip()))
    except Exception:
        return False


def _is_chart(shape: BaseShape) -> bool:
    try:
        if shape.shape_type == MSO_SHAPE_TYPE.CHART:
            return True
    except Exception:
        pass
    try:
        return bool(shape._element.findall('.//' + qn('c:chart')))
    except Exception:
        return False


def _get_shape_geometry(shape: BaseShape) -> ShapeGeometry:
    try:
        return ShapeGeometry(
            left=int(shape.left or 0),
            top=int(shape.top or 0),
            width=int(shape.width or 0),
            height=int(shape.height or 0),
        )
    except Exception:
        return ShapeGeometry()


def _identify_element_type(shape: BaseShape) -> ElementType:
    try:
        if shape.is_placeholder:
            placeholder_type = shape.placeholder_format.type
            if placeholder_type in {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE}:
                return ElementType.TITLE
            if placeholder_type == PP_PLACEHOLDER.SUBTITLE:
                return ElementType.SUBTITLE
            if placeholder_type in {PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT}:
                return ElementType.BODY
    except Exception:
        pass
    return ElementType.TEXT_BOX if shape.has_text_frame else ElementType.OTHER


def _extract_textframe_blocks(
    text_frame: TextFrame,
    slide_index: int,
    shape_id: int,
    element_type: ElementType,
    geometry: ShapeGeometry,
    next_uid,
) -> List[TextBlock]:
    blocks = []
    for paragraph_index, paragraph in enumerate(text_frame.paragraphs):
        plan = build_inline_plan(paragraph)
        if not plan.original_text or not plan.original_text.strip() or not plan.spans:
            continue
        blocks.append(TextBlock(
            uid=next_uid(),
            slide_index=slide_index,
            shape_id=shape_id,
            element_type=element_type,
            paragraph_index=paragraph_index,
            original_text=plan.original_text,
            geometry=geometry,
            skip=not _should_translate(plan.original_text),
            inline_plan=plan,
        ))
    return blocks


def _extract_table_blocks(
    table,
    slide_index: int,
    shape_id: int,
    geometry: ShapeGeometry,
    next_uid,
) -> List[TextBlock]:
    blocks = []
    processed_cells: Set[int] = set()
    for row_index, row in enumerate(table.rows):
        for column_index, cell in enumerate(row.cells):
            cell_identity = id(cell._tc)
            if cell_identity in processed_cells:
                continue
            processed_cells.add(cell_identity)
            for paragraph_index, paragraph in enumerate(cell.text_frame.paragraphs):
                plan = build_inline_plan(paragraph)
                if not plan.original_text or not plan.original_text.strip() or not plan.spans:
                    continue
                blocks.append(TextBlock(
                    uid=next_uid(),
                    slide_index=slide_index,
                    shape_id=shape_id,
                    element_type=ElementType.TABLE_CELL,
                    location_type='table_cell',
                    cell_row=row_index,
                    cell_col=column_index,
                    cell_paragraph_index=paragraph_index,
                    original_text=plan.original_text,
                    geometry=geometry,
                    skip=not _should_translate(plan.original_text),
                    inline_plan=plan,
                ))
    return blocks


def _should_translate(text: str) -> bool:
    text = text.strip()
    if len(text) < 2 or common.is_all_punc(text):
        return False
    if re.fullmatch(r'[\d\s.\-+*/=%()\[\]{}#@&|\\:;,<>$€¥£]+', text):
        return False
    if re.fullmatch(r'(第?\s*\d+\s*页?|Page\s*\d+|\d+\s*/\s*\d+)', text, re.I):
        return False
    if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', text):
        return False
    if re.match(r'^https?://', text) or re.fullmatch(r'[\w.-]+@[\w.-]+\.\w+', text):
        return False
    return True


def _blocks_to_api_format(blocks: List[TextBlock]) -> List[Dict[str, Any]]:
    texts = []
    for block in blocks:
        if block.inline_plan is None:
            raise ValueError('PPTX文本块缺少行内计划')
        item = {
            'text': block.inline_plan.payload,
            'original': block.original_text,
            'complete': False,
            'count': 0,
            '_uid': block.uid,
        }
        item.update(block.inline_plan.translation_metadata())
        texts.append(item)
    return texts


def _sync_translation_results(blocks: List[TextBlock], texts: List[Dict[str, Any]]):
    block_map = {block.uid: block for block in blocks}
    for item in texts:
        block = block_map.get(item.get('_uid'))
        if block is None:
            continue
        block.translated_text = item.get('text', block.original_text)
        block.complete = item.get('complete', False)
        block.count = item.get('count', 0)
        block.fallback_used = item.get('fallback_used', False)


def _apply_translation_mode(
    prs: Presentation, blocks: List[TextBlock], target_lang: str
) -> int:
    slide_blocks = _group_by_slide(blocks)
    text_count = 0
    for slide_index, slide in enumerate(prs.slides):
        if slide_index not in slide_blocks:
            continue
        shape_map = _build_shape_map(slide)
        for shape_id, shape_blocks in _group_by_shape(slide_blocks[slide_index]).items():
            shape = shape_map.get(shape_id)
            if shape is None:
                raise ValueError(f'PPTX缺少shape_id={shape_id}')
            text_count += _apply_to_shape(shape, shape_blocks, target_lang)
    return text_count


def _group_by_slide(blocks: List[TextBlock]) -> Dict[int, List[TextBlock]]:
    result: Dict[int, List[TextBlock]] = {}
    for block in blocks:
        result.setdefault(block.slide_index, []).append(block)
    return result


def _group_by_shape(blocks: List[TextBlock]) -> Dict[int, List[TextBlock]]:
    result: Dict[int, List[TextBlock]] = {}
    for block in blocks:
        result.setdefault(block.shape_id, []).append(block)
    return result


def _build_shape_map(slide) -> Dict[int, BaseShape]:
    shape_map: Dict[int, BaseShape] = {}

    def add(shape):
        if shape.shape_id in shape_map:
            raise ValueError(f'PPTX幻灯片存在重复shape_id={shape.shape_id}')
        shape_map[shape.shape_id] = shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                add(child)

    for shape in slide.shapes:
        add(shape)
    return shape_map


def _apply_to_shape(shape: BaseShape, blocks: List[TextBlock], target_lang: str) -> int:
    if shape.has_table:
        return _apply_to_table(shape.table, blocks, target_lang)
    if shape.has_text_frame:
        return _apply_to_textframe(shape.text_frame, blocks, target_lang)
    raise ValueError(f'PPTX目标形状不包含可写文本: shape_id={shape.shape_id}')


def _apply_to_textframe(
    text_frame: TextFrame, blocks: List[TextBlock], target_lang: str
) -> int:
    text_count = 0
    for block in sorted(blocks, key=lambda item: item.paragraph_index):
        if block.skip:
            continue
        if block.paragraph_index >= len(text_frame.paragraphs):
            raise ValueError('PPTX文本框段落索引越界')
        paragraph = text_frame.paragraphs[block.paragraph_index]
        text_count += _apply_to_paragraph(paragraph, block, target_lang)
    _fit_text_frame_without_geometry_change(text_frame, blocks)
    return text_count


def _apply_to_table(table, blocks: List[TextBlock], target_lang: str) -> int:
    text_count = 0
    cell_blocks: Dict[Tuple[int, int], List[TextBlock]] = {}
    for block in blocks:
        cell_blocks.setdefault((block.cell_row, block.cell_col), []).append(block)

    for (row_index, column_index), current_blocks in sorted(cell_blocks.items()):
        try:
            cell = table.cell(row_index, column_index)
        except (IndexError, ValueError) as exc:
            raise ValueError('PPTX表格单元格索引越界') from exc
        for block in sorted(current_blocks, key=lambda item: item.cell_paragraph_index):
            if block.skip:
                continue
            try:
                paragraph = cell.text_frame.paragraphs[block.cell_paragraph_index]
            except IndexError as exc:
                raise ValueError('PPTX表格段落索引越界') from exc
            text_count += _apply_to_paragraph(paragraph, block, target_lang)
        _fit_text_frame_without_geometry_change(cell.text_frame, current_blocks)
    return text_count


def _apply_to_paragraph(
    paragraph: _Paragraph, block: TextBlock, target_lang: str
) -> int:
    source_plan = block.inline_plan
    if source_plan is None:
        raise ValueError('PPTX文本块缺少源行内计划')
    target_plan = build_inline_plan(paragraph)
    if not source_plan.compatible_with(target_plan):
        raise ValueError('PPTX目标段落结构与源段落不一致')

    translated = block.translated_text or source_plan.payload
    target_plan.apply(translated, block.fallback_used)
    _ensure_plan_font_compatibility(target_plan, target_lang)
    return block.count


def _ensure_plan_font_compatibility(plan: InlinePlan, target_lang: str):
    if not _is_cjk_target(target_lang):
        return
    for run_element in plan.nonempty_run_elements():
        run = _Run(run_element, plan.paragraph)
        style = _extract_run_style(run)
        _ensure_font_compatibility(run, target_lang, style)


def _fit_text_frame_without_geometry_change(
    text_frame: TextFrame, blocks: List[TextBlock]
):
    translated_blocks = [block for block in blocks if not block.skip]
    if not translated_blocks:
        return

    recommended_scale = min(
        _recommended_scale_for_block(block) for block in translated_blocks
    )
    original_auto_size = text_frame.auto_size
    must_lock_geometry = original_auto_size == MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    if recommended_scale >= 1.0 and not must_lock_geometry:
        return

    lower_bound = _minimum_text_frame_scale(text_frame)
    final_scale = max(recommended_scale, lower_bound)
    if original_auto_size == MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE:
        normal_autofit = text_frame._txBody.bodyPr.normAutofit
        existing_scale = (
            float(normal_autofit.fontScale) / 100.0
            if normal_autofit is not None else 1.0
        )
        final_scale = min(existing_scale, final_scale)

    text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    normal_autofit = text_frame._txBody.bodyPr.normAutofit
    if normal_autofit is None:
        raise ValueError('PPTX无法创建固定形状文字适配设置')
    normal_autofit.fontScale = round(final_scale * 100.0, 3)


def _recommended_scale_for_block(block: TextBlock) -> float:
    plan = block.inline_plan
    if plan is None:
        return 1.0
    translated = block.translated_text or plan.payload
    original_width = _visual_text_length(block.original_text)
    translated_width = _visual_text_length(plan.plain_translation(translated))
    if original_width <= 0 or translated_width <= original_width * 1.1:
        return 1.0
    ratio = translated_width / original_width
    if block.element_type in {ElementType.TITLE, ElementType.SUBTITLE}:
        scale = 1.0 / ratio
    else:
        scale = math.sqrt(1.0 / ratio)
    return max(MIN_FONT_SCALE, min(1.0, scale))


def _visual_text_length(text: str) -> float:
    total = 0.0
    for character in text or '':
        if '\u4e00' <= character <= '\u9fff' or '\u3040' <= character <= '\u30ff' or '\uac00' <= character <= '\ud7af':
            total += 1.0
        elif character.isspace():
            total += 0.3
        elif character.isalnum():
            total += 0.55
        else:
            total += 0.4
    return total


def _minimum_text_frame_scale(text_frame: TextFrame) -> float:
    lower_bound = MIN_FONT_SCALE
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            size = run.font.size
            if size is None or size.pt <= 0:
                continue
            lower_bound = max(
                lower_bound,
                min(1.0, MIN_FONT_POINTS / size.pt),
            )
    return min(1.0, lower_bound)


def _extract_run_style(run: _Run) -> RunStyle:
    style = RunStyle()
    font = run.font
    style.font_name = font.name
    style.font_size = font.size
    style.bold = font.bold
    style.italic = font.italic
    style.underline = font.underline
    try:
        style.color_rgb = font.color.rgb
    except (AttributeError, TypeError, ValueError):
        pass
    r_pr = run._r.get_or_add_rPr()
    east_asia = r_pr.find(qn('a:ea'))
    if east_asia is not None:
        style.font_name_ea = east_asia.get('typeface')
    return style


def _ensure_font_compatibility(run: _Run, target_lang: str, style: RunStyle):
    current_font = run.font.name
    if not _is_cjk_font(current_font):
        _set_font_names(run, style, target_lang)


def _set_font_names(run: _Run, style: RunStyle, target_lang: str):
    latin_font = style.font_name or 'Arial'
    east_asia_font = style.font_name_ea
    if not east_asia_font or not _is_cjk_font(east_asia_font):
        if '日语' in target_lang:
            east_asia_font = 'Yu Gothic'
        elif '韩语' in target_lang:
            east_asia_font = 'Malgun Gothic'
        else:
            east_asia_font = 'Microsoft YaHei'

    run.font.name = latin_font
    r_pr = run._r.get_or_add_rPr()
    latin = r_pr.find(qn('a:latin'))
    if latin is None:
        raise ValueError('PPTX无法创建拉丁字体节点')
    latin.set('typeface', latin_font)
    east_asia = r_pr.find(qn('a:ea'))
    if east_asia is None:
        east_asia = etree.Element(qn('a:ea'))
    elif east_asia.getparent() is r_pr:
        r_pr.remove(east_asia)
    r_pr.insert(r_pr.index(latin) + 1, east_asia)
    east_asia.set('typeface', east_asia_font)


def _is_cjk_target(target_lang: str) -> bool:
    return any(language in target_lang for language in ('中文', '日语', '韩语'))


def _is_cjk_font(font_name: Optional[str]) -> bool:
    if not font_name:
        return False
    keywords = (
        'yahei', '雅黑', 'simsun', '宋体', 'simhei', '黑体', 'kaiti', '楷体',
        'fangsong', '仿宋', 'gothic', 'mincho', 'meiryo', 'hiragino',
        'malgun', 'batang', 'gulim', 'dotum', 'noto sans cjk',
        'noto serif cjk', 'source han', 'pingfang', '苹方', 'heiti',
        'songti', 'microsoft jhenghei', '微軟正黑',
    )
    lowered = font_name.lower()
    return any(keyword in lowered for keyword in keywords)


def _apply_bilingual_mode(
    prs: Presentation, blocks: List[TextBlock], target_lang: str
) -> int:
    slide_blocks = _group_by_slide(blocks)
    text_count = 0
    original_count = len(prs.slides)

    for slide_index in range(original_count - 1, -1, -1):
        original_slide = prs.slides[slide_index]
        duplicated_slide = _duplicate_slide(prs, original_slide)
        _move_slide(prs, len(prs.slides) - 1, slide_index + 1)
        translated_slide = prs.slides[slide_index + 1]
        if translated_slide is not duplicated_slide:
            raise ValueError('PPTX译文页移动后定位失败')

        shape_mapping = _build_shape_mapping_by_id(original_slide, translated_slide)
        current_blocks = slide_blocks.get(slide_index, [])
        for block in current_blocks:
            if not block.skip:
                text_count += block.count
        _apply_blocks_with_mapping(
            current_blocks, shape_mapping, target_lang
        )
    return text_count


def _duplicate_slide(prs: Presentation, source_slide):
    """Duplicate the complete slide XML and remap every referenced relationship."""
    new_slide = prs.slides.add_slide(source_slide.slide_layout)
    source_element = source_slide._element
    target_element = new_slide._element

    target_element.attrib.clear()
    target_element.attrib.update(source_element.attrib)
    for child in list(target_element):
        target_element.remove(child)
    for child in source_element:
        cloned_child = copy.deepcopy(child)
        _remap_relationships(cloned_child, source_slide.part, new_slide.part)
        target_element.append(cloned_child)
    new_slide.__dict__.pop('shapes', None)
    new_slide.__dict__.pop('placeholders', None)
    new_slide.__dict__.pop('background', None)
    return new_slide


def _remap_relationships(element, source_part, target_part):
    relationship_map: Dict[str, str] = {}
    for child in element.iter():
        for attribute_name, old_rid in list(child.attrib.items()):
            if not attribute_name.startswith(f'{{{REL_NS}}}') or not old_rid:
                continue
            new_rid = relationship_map.get(old_rid)
            if new_rid is None:
                new_rid = _copy_relationship(source_part, target_part, old_rid)
                relationship_map[old_rid] = new_rid
            child.set(attribute_name, new_rid)


def _copy_relationship(source_part, target_part, rid: str) -> str:
    if rid not in source_part.rels:
        raise ValueError(f'PPTX源关系不存在: {rid}')
    relationship = source_part.rels[rid]
    if relationship.is_external:
        return target_part.relate_to(
            relationship.target_ref, relationship.reltype, is_external=True
        )
    return target_part.relate_to(relationship.target_part, relationship.reltype)


def _move_slide(prs: Presentation, from_index: int, to_index: int):
    slide_ids = prs.slides._sldIdLst
    slides = list(slide_ids)
    if not (0 <= from_index < len(slides)):
        raise IndexError('PPTX源幻灯片索引越界')
    slide_id = slides[from_index]
    slide_ids.remove(slide_id)
    destination = max(0, min(to_index, len(slide_ids)))
    if destination == len(slide_ids):
        slide_ids.append(slide_id)
    else:
        slide_ids.insert(destination, slide_id)


def _build_shape_mapping_by_id(original_slide, translated_slide) -> Dict[int, BaseShape]:
    original_map = _build_shape_map(original_slide)
    translated_map = _build_shape_map(translated_slide)
    if set(original_map) != set(translated_map):
        raise ValueError('PPTX双语页shape ID集合与原页不一致')
    for shape_id, original_shape in original_map.items():
        translated_shape = translated_map[shape_id]
        if original_shape.shape_type != translated_shape.shape_type:
            raise ValueError(f'PPTX双语页shape类型不一致: shape_id={shape_id}')
    return translated_map


def _apply_blocks_with_mapping(
    blocks: List[TextBlock], shape_mapping: Dict[int, BaseShape], target_lang: str
):
    for shape_id, shape_blocks in _group_by_shape(blocks).items():
        shape = shape_mapping.get(shape_id)
        if shape is None:
            raise ValueError(f'PPTX译文页缺少shape_id={shape_id}')
        _apply_to_shape(shape, shape_blocks, target_lang)


def _capture_presentation_baseline(prs: Presentation) -> Dict[str, Any]:
    return {
        'slide_width': int(prs.slide_width),
        'slide_height': int(prs.slide_height),
        'slides': [_snapshot_slide(slide) for slide in prs.slides],
    }


def _snapshot_slide(slide) -> Dict[str, Any]:
    structure = []
    text = []

    def collect(shape, path: Tuple[int, ...]):
        current_path = path + (shape.shape_id,)
        structure.append((
            current_path,
            int(shape.shape_type),
            _get_shape_geometry(shape),
            float(getattr(shape, 'rotation', 0.0) or 0.0),
            _table_structure_signature(shape),
        ))
        text.append((current_path, _shape_text_signature(shape)))
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                collect(child, current_path)

    for shape in slide.shapes:
        collect(shape, ())
    return {
        'structure': tuple(structure),
        'text': tuple(text),
        'relationships': _referenced_relationship_signatures(slide),
        'attributes': tuple(sorted(slide._element.attrib.items())),
    }


def _table_structure_signature(shape: BaseShape):
    if not shape.has_table:
        return None
    table = shape.table
    cells = []
    for row in table.rows:
        for cell in row.cells:
            cells.append((
                _optional_int(cell.margin_left),
                _optional_int(cell.margin_right),
                _optional_int(cell.margin_top),
                _optional_int(cell.margin_bottom),
                bool(getattr(cell, 'is_merge_origin', False)),
                bool(getattr(cell, 'is_spanned', False)),
                _optional_int(cell.vertical_anchor),
            ))
    return (len(table.rows), len(table.columns), tuple(cells))


def _optional_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def _shape_text_signature(shape: BaseShape):
    if shape.has_table:
        return tuple(
            tuple(paragraph.text for paragraph in cell.text_frame.paragraphs)
            for row in shape.table.rows
            for cell in row.cells
        )
    if shape.has_text_frame:
        return tuple(paragraph.text for paragraph in shape.text_frame.paragraphs)
    return None


def _referenced_relationship_signatures(slide) -> Tuple[Tuple[Any, ...], ...]:
    signatures = []
    for element in slide._element.iter():
        for attribute_name, rid in element.attrib.items():
            if not attribute_name.startswith(f'{{{REL_NS}}}'):
                continue
            if rid not in slide.part.rels:
                raise ValueError(f'PPTX关系引用不存在: {rid}')
            relationship = slide.part.rels[rid]
            target = (
                relationship.target_ref
                if relationship.is_external
                else str(relationship.target_part.partname)
            )
            signatures.append((
                attribute_name.rsplit('}', 1)[-1],
                relationship.reltype,
                relationship.is_external,
                target,
            ))
    return tuple(sorted(signatures))


def _save_and_validate_presentation(
    prs: Presentation,
    target_file: str,
    baseline: Dict[str, Any],
    is_bilingual: bool,
):
    try:
        prs.save(target_file)
        reopened = Presentation(target_file)
        _validate_presentation(reopened, baseline, is_bilingual)
        _traverse_internal_relationships(reopened)
    except Exception:
        _remove_invalid_output(target_file)
        raise


def _validate_presentation(
    prs: Presentation, baseline: Dict[str, Any], is_bilingual: bool
):
    if int(prs.slide_width) != baseline['slide_width'] or int(prs.slide_height) != baseline['slide_height']:
        raise ValueError('PPTX输出幻灯片尺寸发生变化')
    source_slides = baseline['slides']
    expected_count = len(source_slides) * (2 if is_bilingual else 1)
    if len(prs.slides) != expected_count:
        raise ValueError('PPTX输出页数不符合翻译模式')

    for source_index, expected in enumerate(source_slides):
        if is_bilingual:
            original = _snapshot_slide(prs.slides[source_index * 2])
            translated = _snapshot_slide(prs.slides[source_index * 2 + 1])
            _assert_slide_matches(original, expected, compare_text=True)
            _assert_slide_matches(translated, expected, compare_text=False)
        else:
            actual = _snapshot_slide(prs.slides[source_index])
            _assert_slide_matches(actual, expected, compare_text=False)

    for slide in prs.slides:
        _build_shape_map(slide)
        for paragraph in _iter_slide_paragraphs(slide):
            if TOKEN_RE.search(paragraph.text or ''):
                raise ValueError('PPTX输出残留内部保护标记')


def _assert_slide_matches(
    actual: Dict[str, Any], expected: Dict[str, Any], compare_text: bool
):
    if actual['structure'] != expected['structure']:
        raise ValueError('PPTX输出形状几何、层级或表格结构发生变化')
    if actual['relationships'] != expected['relationships']:
        raise ValueError('PPTX输出图片、超链接或其他对象关系发生变化')
    if actual['attributes'] != expected['attributes']:
        raise ValueError('PPTX输出幻灯片属性发生变化')
    if compare_text and actual['text'] != expected['text']:
        raise ValueError('PPTX双语模式修改了原文页文本')


def _iter_slide_paragraphs(slide) -> Iterable[_Paragraph]:
    def visit(shape):
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            for child in shape.shapes:
                yield from visit(child)
            return
        if shape.has_table:
            processed = set()
            for row in shape.table.rows:
                for cell in row.cells:
                    identity = id(cell._tc)
                    if identity in processed:
                        continue
                    processed.add(identity)
                    yield from cell.text_frame.paragraphs
        elif shape.has_text_frame:
            yield from shape.text_frame.paragraphs

    for shape in slide.shapes:
        yield from visit(shape)


def _traverse_internal_relationships(prs: Presentation):
    for part in prs.part.package.iter_parts():
        for relationship in part.rels.values():
            if not relationship.is_external:
                _ = relationship.target_part


def _remove_invalid_output(target_file: Optional[str]):
    if not target_file or not os.path.isfile(target_file):
        return
    try:
        os.remove(target_file)
    except OSError:
        logging.warning('删除无效PPTX输出失败: %s', target_file)
