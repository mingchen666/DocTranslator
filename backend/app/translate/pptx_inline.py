"""Inline token parsing and safe text replacement for PPTX paragraphs."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lxml import etree
from pptx.oxml.ns import qn


TOKEN_RE = re.compile(r'⟦[A-Z_]+_\d+⟧')
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'


@dataclass
class InlineAnchor:
    token: str
    kind: str
    display_text: str = ''
    inline: bool = False


@dataclass
class InlineSpan:
    span_id: int
    text_nodes: List[Any]
    run_elements: List[Any]
    style_key: bytes
    original_text: str
    payload_text: str
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
                parts.extend((value.start_token, value.payload_text, value.end_token))
            else:
                parts.append(value.token)
        return ''.join(parts)

    @property
    def fallback_payload(self) -> str:
        parts = []
        for kind, value in self.sequence:
            parts.append(value.payload_text if kind == 'span' else value.token)
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

    def compatible_with(self, other: 'InlinePlan') -> bool:
        if self.token_sequence != other.token_sequence:
            return False
        return [anchor.kind for anchor in self.anchors] == [
            anchor.kind for anchor in other.anchors
        ]

    def apply(self, translated: str, fallback_used: bool = False):
        expected = (
            self.fallback_token_sequence if fallback_used else self.token_sequence
        )
        if TOKEN_RE.findall(translated or '') != expected:
            raise ValueError('PPTX译文保护标记与段落结构不一致')
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

    def nonempty_run_elements(self) -> Iterable[Any]:
        seen = set()
        for span in self.spans:
            for run_element in span.run_elements:
                identity = id(run_element)
                if identity in seen or not _run_text(run_element):
                    continue
                seen.add(identity)
                yield run_element

    def _apply_styled(self, translated: str):
        start_map = {span.start_token: span for span in self.spans}
        end_map = {span.end_token: span for span in self.spans}
        anchor_map = {anchor.token: anchor for anchor in self.anchors}
        values = {span.span_id: [] for span in self.spans}
        current: Optional[InlineSpan] = None
        cursor = 0

        for match in TOKEN_RE.finditer(translated):
            between = translated[cursor:match.start()]
            token = match.group(0)
            if current is not None:
                values[current.span_id].append(between)
            elif between.strip():
                raise ValueError('PPTX译文包含样式边界外文本')

            if token in start_map:
                if current is not None:
                    raise ValueError('PPTX样式边界嵌套异常')
                current = start_map[token]
            elif token in end_map:
                if current is None or current.span_id != end_map[token].span_id:
                    raise ValueError('PPTX样式边界顺序异常')
                current = None
            elif token in anchor_map:
                anchor = anchor_map[token]
                if anchor.inline:
                    if current is None:
                        raise ValueError('PPTX行内锚点脱离了文本样式')
                    values[current.span_id].append(anchor.display_text)
                elif current is not None:
                    raise ValueError('PPTX结构锚点出现在样式边界内部')
            else:
                raise ValueError(f'PPTX出现未知占位符: {token}')
            cursor = match.end()

        tail = translated[cursor:]
        if current is not None:
            values[current.span_id].append(tail)
            raise ValueError('PPTX样式边界未闭合')
        if tail.strip():
            raise ValueError('PPTX译文末尾包含边界外文本')

        for span in self.spans:
            _set_span_text(span, ''.join(values[span.span_id]))

    def _apply_fallback(self, translated: str):
        regions = self._region_spans()
        region_values = [''] * len(regions)
        anchor_map = {anchor.token: anchor for anchor in self.anchors}
        region_index = 0
        cursor = 0

        for match in TOKEN_RE.finditer(translated):
            token = match.group(0)
            anchor = anchor_map.get(token)
            if anchor is None:
                raise ValueError(f'PPTX降级译文出现未知占位符: {token}')
            region_values[region_index] += translated[cursor:match.start()]
            if anchor.inline:
                region_values[region_index] += anchor.display_text
            else:
                region_index += 1
                if region_index >= len(region_values):
                    raise ValueError('PPTX降级译文结构锚点数量异常')
            cursor = match.end()
        region_values[region_index] += translated[cursor:]

        if region_index != len(regions) - 1:
            raise ValueError('PPTX降级译文区域数量不一致')
        for spans, value in zip(regions, region_values):
            if not spans:
                if value.strip():
                    raise ValueError('PPTX降级译文跨越了结构锚点')
                continue
            primary = max(spans, key=lambda span: len(span.original_text))
            _set_span_text(primary, value)
            for span in spans:
                if span is not primary:
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
        self.anchor_index = 0
        self.span_index = 0

    def build(self) -> InlinePlan:
        for child in self.plan.paragraph._p:
            if child.tag in {qn('a:pPr'), qn('a:endParaRPr')}:
                continue
            if child.tag == qn('a:r'):
                self._add_run(child)
            elif child.tag == qn('a:br'):
                self._add_anchor('break', '\v')
            elif child.tag == qn('a:fld'):
                self._add_anchor('field', child.text or '')
            else:
                self._add_anchor(_local_name(child.tag))
        return self.plan

    def _add_run(self, run_element):
        text_node = run_element.find(qn('a:t'))
        text = text_node.text if text_node is not None else ''
        if not text:
            return

        r_pr = run_element.find(qn('a:rPr'))
        has_hyperlink = bool(
            r_pr is not None
            and (
                r_pr.find(qn('a:hlinkClick')) is not None
                or r_pr.find(qn('a:hlinkMouseOver')) is not None
            )
        )
        if has_hyperlink:
            self._add_anchor('hyperlink_start')

        payload_text = self._encode_inline_controls(text)
        self._add_text(text_node, run_element, text, payload_text)

        if has_hyperlink:
            self._add_anchor('hyperlink_end')

    def _encode_inline_controls(self, text: str) -> str:
        parts = []
        cursor = 0
        for match in re.finditer(r'[\t\n]', text):
            parts.append(text[cursor:match.start()])
            anchor = self._new_anchor('tab' if match.group(0) == '\t' else 'line_feed',
                                      match.group(0), inline=True)
            parts.append(anchor.token)
            cursor = match.end()
        parts.append(text[cursor:])
        return ''.join(parts)

    def _add_text(self, text_node, run_element, text: str, payload_text: str):
        style_key = _style_key(run_element)
        if (
            self.plan.sequence
            and self.plan.sequence[-1][0] == 'span'
            and self.plan.sequence[-1][1].style_key == style_key
        ):
            span = self.plan.sequence[-1][1]
            span.text_nodes.append(text_node)
            span.run_elements.append(run_element)
            span.original_text += text
            span.payload_text += payload_text
            return

        self.span_index += 1
        span = InlineSpan(
            span_id=self.span_index,
            text_nodes=[text_node],
            run_elements=[run_element],
            style_key=style_key,
            original_text=text,
            payload_text=payload_text,
            start_token=f'⟦PPTX_STYLE_START_{self.span_index}⟧',
            end_token=f'⟦PPTX_STYLE_END_{self.span_index}⟧',
        )
        self.plan.spans.append(span)
        self.plan.sequence.append(('span', span))

    def _new_anchor(self, kind: str, display_text: str = '',
                    inline: bool = False) -> InlineAnchor:
        self.anchor_index += 1
        anchor = InlineAnchor(
            token=f'⟦PPTX_ANCHOR_{self.anchor_index}⟧',
            kind=kind,
            display_text=display_text,
            inline=inline,
        )
        self.plan.anchors.append(anchor)
        return anchor

    def _add_anchor(self, kind: str, display_text: str = ''):
        anchor = self._new_anchor(kind, display_text)
        self.plan.sequence.append(('anchor', anchor))


def build_inline_plan(paragraph) -> InlinePlan:
    return _PlanBuilder(paragraph).build()


def _style_key(run_element) -> bytes:
    run_properties = run_element.find(qn('a:rPr'))
    return etree.tostring(run_properties) if run_properties is not None else b''


def _set_span_text(span: InlineSpan, value: str):
    if not span.text_nodes:
        raise ValueError('PPTX文本span缺少文本节点')
    for node in span.text_nodes:
        node.text = ''
        node.attrib.pop(XML_SPACE, None)
    first = span.text_nodes[0]
    first.text = value
    if value[:1].isspace() or value[-1:].isspace():
        first.set(XML_SPACE, 'preserve')


def _run_text(run_element) -> str:
    text_node = run_element.find(qn('a:t'))
    return text_node.text if text_node is not None and text_node.text else ''


def _local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1].lower()
