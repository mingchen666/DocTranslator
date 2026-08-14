"""Inline token parsing and safe text replacement for DOCX paragraphs."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from lxml import etree
from docx.oxml.ns import qn


TOKEN_RE = re.compile(r'⟦[A-Z_]+_\d+⟧')
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


@dataclass
class InlineAnchor:
    token: str
    kind: str
    display_text: str = ''


@dataclass
class InlineSpan:
    span_id: int
    text_nodes: List[Any]
    run_element: Any
    style_key: bytes
    original_text: str
    start_token: str
    end_token: str


@dataclass
class InlinePlan:
    paragraph: Any
    sequence: List[Tuple[str, Any]] = field(default_factory=list)
    spans: List[InlineSpan] = field(default_factory=list)
    anchors: List[InlineAnchor] = field(default_factory=list)

    @property
    def original_text(self) -> str:
        parts = []
        for kind, value in self.sequence:
            if kind == 'span':
                parts.append(value.original_text)
            else:
                parts.append(value.display_text)
        return ''.join(parts)

    @property
    def payload(self) -> str:
        parts = []
        for kind, value in self.sequence:
            if kind == 'span':
                parts.extend((value.start_token, value.original_text, value.end_token))
            else:
                parts.append(value.token)
        return ''.join(parts)

    @property
    def fallback_payload(self) -> str:
        parts = []
        for kind, value in self.sequence:
            parts.append(value.original_text if kind == 'span' else value.token)
        return ''.join(parts)

    @property
    def protected_tokens(self) -> List[str]:
        return [anchor.token for anchor in self.anchors]

    @property
    def style_tokens(self) -> List[str]:
        tokens = []
        for span in self.spans:
            tokens.extend((span.start_token, span.end_token))
        return tokens

    @property
    def token_sequence(self) -> List[str]:
        return TOKEN_RE.findall(self.payload)

    @property
    def fallback_token_sequence(self) -> List[str]:
        return TOKEN_RE.findall(self.fallback_payload)

    def translation_metadata(self) -> Dict[str, Any]:
        return {
            'protected_tokens': self.protected_tokens,
            'style_tokens': self.style_tokens,
            'protected_token_sequence': self.token_sequence,
            'fallback_text': self.fallback_payload,
            'fallback_protected_tokens': self.protected_tokens,
            'fallback_token_sequence': self.fallback_token_sequence,
            'require_wrapped_content': bool(self.spans),
            'count_text': self.original_text,
        }

    def apply(self, translated: str, fallback_used: bool = False):
        if fallback_used:
            self._apply_fallback(translated)
        else:
            self._apply_styled(translated)

    def plain_translation(self, translated: str) -> str:
        replacements = {
            anchor.token: anchor.display_text for anchor in self.anchors
        }
        for span in self.spans:
            replacements[span.start_token] = ''
            replacements[span.end_token] = ''
        result = translated
        for token, value in replacements.items():
            result = result.replace(token, value)
        return result.strip()

    def _apply_styled(self, translated: str):
        start_map = {span.start_token: span for span in self.spans}
        end_map = {span.end_token: span for span in self.spans}
        values = {span.span_id: [] for span in self.spans}
        current: Optional[InlineSpan] = None
        cursor = 0

        for match in TOKEN_RE.finditer(translated):
            between = translated[cursor:match.start()]
            token = match.group(0)
            if current is not None:
                values[current.span_id].append(between)
            elif between.strip():
                raise ValueError('DOCX译文包含样式边界外文本')

            if token in start_map:
                if current is not None:
                    raise ValueError('DOCX样式边界嵌套异常')
                current = start_map[token]
            elif token in end_map:
                if current is None or current.span_id != end_map[token].span_id:
                    raise ValueError('DOCX样式边界顺序异常')
                current = None
            elif token not in self.protected_tokens:
                raise ValueError(f'DOCX出现未知占位符: {token}')
            elif current is not None:
                raise ValueError('DOCX结构锚点出现在样式边界内部')
            cursor = match.end()

        tail = translated[cursor:]
        if current is not None:
            values[current.span_id].append(tail)
            raise ValueError('DOCX样式边界未闭合')
        if tail.strip():
            raise ValueError('DOCX译文末尾包含边界外文本')

        for span in self.spans:
            _set_span_text(span, ''.join(values[span.span_id]))

    def _apply_fallback(self, translated: str):
        regions = self._region_spans()
        region_values = [''] * len(regions)
        anchor_tokens = set(self.protected_tokens)
        region_index = 0
        cursor = 0

        for match in TOKEN_RE.finditer(translated):
            token = match.group(0)
            if token not in anchor_tokens:
                raise ValueError(f'DOCX降级译文出现未知占位符: {token}')
            region_values[region_index] += translated[cursor:match.start()]
            region_index += 1
            cursor = match.end()
        region_values[region_index] += translated[cursor:]

        if len(region_values) != len(regions):
            raise ValueError('DOCX降级译文区域数量不一致')
        for spans, value in zip(regions, region_values):
            if not spans:
                if value.strip():
                    raise ValueError('DOCX降级译文跨越了结构锚点')
                continue
            _set_span_text(spans[0], value)
            for span in spans[1:]:
                _set_span_text(span, '')

    def _region_spans(self) -> List[List[InlineSpan]]:
        regions: List[List[InlineSpan]] = [[]]
        for kind, value in self.sequence:
            if kind == 'anchor':
                regions.append([])
            else:
                regions[-1].append(value)
        return regions


class _PlanBuilder:
    def __init__(self, paragraph):
        self.plan = InlinePlan(paragraph=paragraph)
        self.field_depth = 0
        self.anchor_index = 0
        self.span_index = 0

    def build(self) -> InlinePlan:
        for child in self.plan.paragraph._p:
            if child.tag == qn('w:pPr'):
                continue
            self._walk(child, hyperlink_id='')
        return self.plan

    def _walk(self, element, hyperlink_id: str):
        if element.tag == qn('w:r'):
            self._walk_run(element, hyperlink_id)
            return
        if element.tag == qn('w:hyperlink'):
            relation_id = element.get(qn('r:id'), '')
            self._add_anchor('hyperlink_start')
            for child in element:
                if child.tag != qn('w:hyperlinkPr'):
                    self._walk(child, hyperlink_id=relation_id or 'hyperlink')
            self._add_anchor('hyperlink_end')
            return
        if element.tag in {qn('w:smartTag'), qn('w:customXml')}:
            for child in element:
                self._walk(child, hyperlink_id)
            return
        if element.tag == qn('w:bookmarkStart'):
            self._add_anchor('bookmark_start')
            return
        if element.tag == qn('w:bookmarkEnd'):
            self._add_anchor('bookmark_end')
            return
        self._add_anchor(_local_name(element.tag))

    def _walk_run(self, run_element, hyperlink_id: str):
        style_key = _style_key(run_element, hyperlink_id)
        for child in run_element:
            if child.tag == qn('w:rPr'):
                continue
            if child.tag == qn('w:fldChar'):
                field_type = child.get(qn('w:fldCharType'), '')
                self._add_anchor(f'field_{field_type or "part"}')
                if field_type == 'begin':
                    self.field_depth += 1
                elif field_type == 'end' and self.field_depth:
                    self.field_depth -= 1
                continue
            if self.field_depth or child.tag == qn('w:instrText'):
                self._add_anchor('field_content')
                continue
            if child.tag == qn('w:t'):
                if child.text:
                    self._add_text(child, run_element, style_key)
                continue
            if child.tag == qn('w:tab'):
                self._add_anchor('tab', '\t')
                continue
            if child.tag in {qn('w:br'), qn('w:cr')}:
                self._add_anchor('break', '\n')
                continue
            self._add_anchor(_local_name(child.tag))

    def _add_text(self, text_node, run_element, style_key: bytes):
        text = text_node.text or ''
        if (
            self.plan.sequence
            and self.plan.sequence[-1][0] == 'span'
            and self.plan.sequence[-1][1].style_key == style_key
        ):
            span = self.plan.sequence[-1][1]
            span.text_nodes.append(text_node)
            span.original_text += text
            return

        self.span_index += 1
        span = InlineSpan(
            span_id=self.span_index,
            text_nodes=[text_node],
            run_element=run_element,
            style_key=style_key,
            original_text=text,
            start_token=f'⟦DOCX_STYLE_START_{self.span_index}⟧',
            end_token=f'⟦DOCX_STYLE_END_{self.span_index}⟧',
        )
        self.plan.spans.append(span)
        self.plan.sequence.append(('span', span))

    def _add_anchor(self, kind: str, display_text: str = ''):
        self.anchor_index += 1
        anchor = InlineAnchor(
            token=f'⟦DOCX_ANCHOR_{self.anchor_index}⟧',
            kind=kind,
            display_text=display_text,
        )
        self.plan.anchors.append(anchor)
        self.plan.sequence.append(('anchor', anchor))


def build_inline_plan(paragraph) -> InlinePlan:
    return _PlanBuilder(paragraph).build()


def _style_key(run_element, hyperlink_id: str) -> bytes:
    run_properties = run_element.find(qn('w:rPr'))
    xml = etree.tostring(run_properties) if run_properties is not None else b''
    return hyperlink_id.encode('utf-8') + b'\0' + xml


def _set_span_text(span: InlineSpan, value: str):
    if not span.text_nodes:
        raise ValueError('DOCX文本span缺少文本节点')
    for node in span.text_nodes:
        node.text = ''
        node.attrib.pop(XML_SPACE, None)
    first = span.text_nodes[0]
    first.text = value
    if value[:1].isspace() or value[-1:].isspace():
        first.set(XML_SPACE, 'preserve')


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1].lower()
