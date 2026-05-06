# translate/md.py
"""
Markdown文件翻译处理器
分块策略：
1. 保护代码块、行内代码、公式、HTML标签结构
2. 按语义块切分（标题、列表、引用、表格、段落）
3. 保持块的完整性
4. 超长块按句子边界切分
5. 链接/图片只保留，不翻译
"""

import re
import datetime
import logging
from threading import Event
from typing import List, Dict, Tuple
from dataclasses import dataclass
from . import to_translate
from . import common

# 分块配置
MAX_CHUNK_SIZE = 2000


@dataclass
class ProtectedBlock:
    """受保护的块（不翻译）"""
    placeholder: str
    content: str
    block_type: str  # code_block, inline_code, formula, html_tag, link, image


def start(trans: Dict) -> bool:
    """
    Markdown文件翻译入口
    :param trans: 翻译配置字典
    :return: 是否成功
    """
    translate_id = trans['id']
    start_time = datetime.datetime.now()

    # 读取文件
    try:
        with open(trans['file_path'], 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(trans['file_path'], 'r', encoding='gbk') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"[任务{translate_id}] 读取文件失败: {e}")
            to_translate.error(translate_id, f"读取文件失败: {str(e)}")
            return False
    except Exception as e:
        logging.error(f"[任务{translate_id}] 读取文件失败: {e}")
        to_translate.error(translate_id, f"读取文件失败: {str(e)}")
        return False

    if not content or not content.strip():
        logging.info(f"[任务{translate_id}] 文件内容为空")
        with open(trans['target_file'], 'w', encoding='utf-8') as f:
            f.write("")
        to_translate.complete(trans, 0, "0秒")
        return True

    # 预处理：保护特殊语法
    processed_content, protected_blocks = _protect_special_syntax(content)

    # 智能分块
    texts = _smart_chunk_markdown(processed_content)

    # 统计需要翻译的块数
    to_translate_count = sum(1 for t in texts if not t.get('skip', False))

    if to_translate_count == 0:
        logging.info(f"[任务{translate_id}] 没有需要翻译的内容")
        with open(trans['target_file'], 'w', encoding='utf-8') as f:
            f.write(content)
        to_translate.complete(trans, 0, "0秒")
        return True

    logging.info(
        f"[任务{translate_id}] 分割为 {len(texts)} 个块，其中 {to_translate_count} 个需要翻译")

    # 执行翻译
    event = Event()
    success = to_translate.translate_batch(trans, texts, event)
    if not success:
        return False

    # 重建文档并写入结果
    try:
        text_count = _write_result(trans, texts, protected_blocks)
    except Exception as e:
        logging.error(f"[任务{translate_id}] 写入文件失败: {e}")
        to_translate.error(translate_id, f"写入文件失败: {str(e)}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    to_translate.complete(trans, text_count, spend_time)
    return True


def _protect_special_syntax(content: str) -> Tuple[str, List[ProtectedBlock]]:
    """
    预处理：用占位符替换不需要翻译的特殊语法
    :return: (处理后的内容, 受保护块列表)
    """
    protected_blocks = []
    placeholder_counter = [0]

    def make_placeholder(block_type: str) -> str:
        placeholder_counter[0] += 1
        return f"⟦{block_type.upper()}_{placeholder_counter[0]}⟧"

    def protect(match, block_type: str) -> str:
        placeholder = make_placeholder(block_type)
        protected_blocks.append(ProtectedBlock(
            placeholder=placeholder,
            content=match.group(0),
            block_type=block_type
        ))
        return placeholder

    # 1. 保护代码块 ```...``` （必须先处理，避免内部内容被其他规则匹配）
    content = re.sub(
        r'```[\s\S]*?```',
        lambda m: protect(m, 'code_block'),
        content
    )

    # 2. 保护行内代码 `...`
    content = re.sub(
        r'`[^`\n]+`',
        lambda m: protect(m, 'inline_code'),
        content
    )

    # 3. 保护LaTeX公式块 $$...$$
    content = re.sub(
        r'\$\$[\s\S]*?\$\$',
        lambda m: protect(m, 'formula_block'),
        content
    )

    # 4. 保护行内公式 $...$
    content = re.sub(
        r'\$[^\$\n]+\$',
        lambda m: protect(m, 'formula_inline'),
        content
    )

    # 5. 保护图片 ![alt](url) 或 ![alt](url "title")
    content = re.sub(
        r'!\[[^\]]*\]\([^)]+\)',
        lambda m: protect(m, 'image'),
        content
    )

    # 6. 保护链接URL部分，但保留显示文本
    # [显示文本](url) -> [显示文本](⟦LINK_URL_X⟧)
    def protect_link(match):
        full_match = match.group(0)
        text = match.group(1)  # 显示文本
        url = match.group(2)  # URL部分

        # 只保护URL部分
        url_placeholder = make_placeholder('link_url')
        protected_blocks.append(ProtectedBlock(
            placeholder=url_placeholder,
            content=f"]({url})",
            block_type='link_url'
        ))
        return f"[{text}{url_placeholder}"

    content = re.sub(
        r'\[([^\]]+)\](\([^)]+\))',
        protect_link,
        content
    )

    # 7. 保护HTML标签（保留标签结构，内部文本会被翻译）
    # 只保护自闭合标签和纯标签（无内容）
    content = re.sub(
        r'<[^>]+/>',
        lambda m: protect(m, 'html_self_closing'),
        content
    )

    # 保护HTML注释
    content = re.sub(
        r'<!--[\s\S]*?-->',
        lambda m: protect(m, 'html_comment'),
        content
    )

    return content, protected_blocks


def _smart_chunk_markdown(content: str) -> List[Dict]:
    """
    智能分块Markdown内容
    按语义块切分：标题、列表、引用、表格、普通段落
    """
    texts = []

    # 统一换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # 按行处理
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # 空行 - 作为分隔符
        if not line.strip():
            texts.append(_make_text_item('', skip=True, block_type='separator'))
            i += 1
            continue

        # 分隔线 (---, ***, ___)
        if re.match(r'^[\-\*_]{3,}\s*$', line.strip()):
            texts.append(_make_text_item(line, skip=True, block_type='hr'))
            i += 1
            continue

        # 标题 (# ## ### 等)
        if re.match(r'^#{1,6}\s+', line):
            # 检查标题内容是否需要翻译
            header_match = re.match(r'^(#{1,6}\s+)(.*)$', line)
            if header_match:
                prefix = header_match.group(1)
                title_text = header_match.group(2)
                if _should_translate(title_text):
                    texts.append(_make_text_item(
                        line,
                        block_type='header',
                        prefix=prefix,
                        content_text=title_text
                    ))
                else:
                    texts.append(_make_text_item(line, skip=True, block_type='header'))
            i += 1
            continue

        # 表格 (以|开头)
        if line.strip().startswith('|'):
            table_lines, end_i = _collect_table(lines, i)
            table_text = '\n'.join(table_lines)
            if _should_translate(table_text):
                if len(table_text) > MAX_CHUNK_SIZE:
                    # 表格太大，按行切分
                    sub_chunks = _split_table(table_lines)
                    for j, chunk in enumerate(sub_chunks):
                        texts.append(_make_text_item(
                            chunk,
                            block_type='table',
                            is_sub=True,
                            sub_index=j,
                            sub_total=len(sub_chunks)
                        ))
                else:
                    texts.append(_make_text_item(table_text, block_type='table'))
            else:
                texts.append(_make_text_item(table_text, skip=True, block_type='table'))
            i = end_i
            continue

        # 引用块 (以>开头)
        if line.strip().startswith('>'):
            quote_lines, end_i = _collect_quote(lines, i)
            quote_text = '\n'.join(quote_lines)
            if _should_translate(quote_text):
                if len(quote_text) > MAX_CHUNK_SIZE:
                    sub_chunks = _split_quote(quote_lines)
                    for j, chunk in enumerate(sub_chunks):
                        texts.append(_make_text_item(
                            chunk,
                            block_type='quote',
                            is_sub=True,
                            sub_index=j,
                            sub_total=len(sub_chunks)
                        ))
                else:
                    texts.append(_make_text_item(quote_text, block_type='quote'))
            else:
                texts.append(_make_text_item(quote_text, skip=True, block_type='quote'))
            i = end_i
            continue

        # 无序列表 (以- * +开头)
        if re.match(r'^[\s]*[-\*\+]\s+', line):
            list_lines, end_i = _collect_list(lines, i, 'unordered')
            list_text = '\n'.join(list_lines)
            if _should_translate(list_text):
                if len(list_text) > MAX_CHUNK_SIZE:
                    sub_chunks = _split_list(list_lines)
                    for j, chunk in enumerate(sub_chunks):
                        texts.append(_make_text_item(
                            chunk,
                            block_type='list',
                            is_sub=True,
                            sub_index=j,
                            sub_total=len(sub_chunks)
                        ))
                else:
                    texts.append(_make_text_item(list_text, block_type='list'))
            else:
                texts.append(_make_text_item(list_text, skip=True, block_type='list'))
            i = end_i
            continue

        # 有序列表 (以数字.开头)
        if re.match(r'^[\s]*\d+\.\s+', line):
            list_lines, end_i = _collect_list(lines, i, 'ordered')
            list_text = '\n'.join(list_lines)
            if _should_translate(list_text):
                if len(list_text) > MAX_CHUNK_SIZE:
                    sub_chunks = _split_list(list_lines)
                    for j, chunk in enumerate(sub_chunks):
                        texts.append(_make_text_item(
                            chunk,
                            block_type='list',
                            is_sub=True,
                            sub_index=j,
                            sub_total=len(sub_chunks)
                        ))
                else:
                    texts.append(_make_text_item(list_text, block_type='list'))
            else:
                texts.append(_make_text_item(list_text, skip=True, block_type='list'))
            i = end_i
            continue

        # 普通段落（连续的非空行）
        para_lines, end_i = _collect_paragraph(lines, i)
        para_text = '\n'.join(para_lines)
        if _should_translate(para_text):
            if len(para_text) > MAX_CHUNK_SIZE:
                sub_chunks = _split_by_sentences_md(para_text)
                for j, chunk in enumerate(sub_chunks):
                    texts.append(_make_text_item(
                        chunk,
                        block_type='paragraph',
                        is_sub=True,
                        sub_index=j,
                        sub_total=len(sub_chunks)
                    ))
            else:
                texts.append(_make_text_item(para_text, block_type='paragraph'))
        else:
            texts.append(_make_text_item(para_text, skip=True, block_type='paragraph'))
        i = end_i

    return texts


def _collect_table(lines: List[str], start: int) -> Tuple[List[str], int]:
    """收集表格行"""
    table_lines = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('|') or (table_lines and re.match(r'^[\s]*[\|\-\:]+\s*$', line)):
            table_lines.append(line)
            i += 1
        elif not line.strip() and len(table_lines) > 0:
            # 表格后的空行
            break
        elif len(table_lines) > 0:
            # 非表格行
            break
        else:
            break
    return table_lines, i


def _collect_quote(lines: List[str], start: int) -> Tuple[List[str], int]:
    """收集引用块"""
    quote_lines = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('>') or (
                quote_lines and line.strip() and not _is_block_starter(line)):
            quote_lines.append(line)
            i += 1
        elif not line.strip() and quote_lines:
            # 检查下一行是否还是引用
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('>'):
                quote_lines.append(line)
                i += 1
            else:
                break
        else:
            break
    return quote_lines, i


def _collect_list(lines: List[str], start: int, list_type: str) -> Tuple[List[str], int]:
    """收集列表"""
    list_lines = []
    i = start

    if list_type == 'unordered':
        pattern = r'^[\s]*[-\*\+]\s+'
    else:
        pattern = r'^[\s]*\d+\.\s+'

    while i < len(lines):
        line = lines[i]

        # 列表项
        if re.match(pattern, line):
            list_lines.append(line)
            i += 1
            continue

        # 列表项的续行（以空格开头的缩进内容）
        if line.startswith('  ') or line.startswith('\t'):
            list_lines.append(line)
            i += 1
            continue

        # 嵌套列表
        if re.match(r'^[\s]+[-\*\+]\s+', line) or re.match(r'^[\s]+\d+\.\s+', line):
            list_lines.append(line)
            i += 1
            continue

        # 空行可能是列表内的分隔
        if not line.strip() and list_lines:
            # 检查下一行是否还是列表
            if i + 1 < len(lines) and (
                    re.match(pattern, lines[i + 1]) or lines[i + 1].startswith('  ')):
                list_lines.append(line)
                i += 1
                continue
            else:
                break

        break

    return list_lines, i


def _collect_paragraph(lines: List[str], start: int) -> Tuple[List[str], int]:
    """收集普通段落"""
    para_lines = []
    i = start
    while i < len(lines):
        line = lines[i]

        # 空行结束段落
        if not line.strip():
            break

        # 遇到其他块级元素
        if _is_block_starter(line):
            if not para_lines:  # 第一行就是块元素
                para_lines.append(line)
                i += 1
            break

        para_lines.append(line)
        i += 1

    return para_lines, i


def _is_block_starter(line: str) -> bool:
    """判断是否是块级元素开始"""
    line_stripped = line.strip()

    # 标题
    if re.match(r'^#{1,6}\s+', line_stripped):
        return True
    # 列表
    if re.match(r'^[-\*\+]\s+', line_stripped):
        return True
    if re.match(r'^\d+\.\s+', line_stripped):
        return True
    # 引用
    if line_stripped.startswith('>'):
        return True
    # 表格
    if line_stripped.startswith('|'):
        return True
    # 分隔线
    if re.match(r'^[\-\*_]{3,}\s*$', line_stripped):
        return True

    return False


def _should_translate(text: str) -> bool:
    """判断文本是否需要翻译"""
    if not text or not text.strip():
        return False

    # 移除占位符后检查
    clean_text = re.sub(r'⟦[A-Z_]+_\d+⟧', '', text)
    clean_text = clean_text.strip()

    if not clean_text:
        return False

    if common.is_all_punc(clean_text):
        return False

    return True


def _split_table(table_lines: List[str]) -> List[str]:
    """切分大表格（保持表头）"""
    if len(table_lines) <= 2:
        return ['\n'.join(table_lines)]

    header = table_lines[0]
    separator = table_lines[1] if len(table_lines) > 1 and re.match(r'^[\s]*[\|\-\:\s]+$',
                                                                    table_lines[1]) else None

    chunks = []
    current_chunk = [header]
    if separator:
        current_chunk.append(separator)
        data_start = 2
    else:
        data_start = 1

    current_size = len('\n'.join(current_chunk))

    for line in table_lines[data_start:]:
        if current_size + len(line) + 1 > MAX_CHUNK_SIZE:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [header]
            if separator:
                current_chunk.append(separator)
            current_size = len('\n'.join(current_chunk))

        current_chunk.append(line)
        current_size += len(line) + 1

    if current_chunk and len(current_chunk) > (2 if separator else 1):
        chunks.append('\n'.join(current_chunk))

    return chunks if chunks else ['\n'.join(table_lines)]


def _split_quote(quote_lines: List[str]) -> List[str]:
    """切分大引用块"""
    chunks = []
    current_chunk = []
    current_size = 0

    for line in quote_lines:
        if current_size + len(line) + 1 > MAX_CHUNK_SIZE:
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = len(line)
        else:
            current_chunk.append(line)
            current_size += len(line) + 1

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks if chunks else ['\n'.join(quote_lines)]


def _split_list(list_lines: List[str]) -> List[str]:
    """
    切分大列表
    尽量按完整的列表项切分
    """
    # 识别列表项的开始位置
    item_starts = []
    for i, line in enumerate(list_lines):
        if re.match(r'^[\s]*[-\*\+]\s+', line) or re.match(r'^[\s]*\d+\.\s+', line):
            item_starts.append(i)

    if not item_starts:
        return ['\n'.join(list_lines)]

    # 按列表项分组
    items = []
    for i, start in enumerate(item_starts):
        end = item_starts[i + 1] if i + 1 < len(item_starts) else len(list_lines)
        items.append(list_lines[start:end])

    # 合并列表项直到接近MAX_CHUNK_SIZE
    chunks = []
    current_chunk = []
    current_size = 0

    for item in items:
        item_text = '\n'.join(item)
        item_size = len(item_text)

        if current_size + item_size + 1 > MAX_CHUNK_SIZE:
            if current_chunk:
                chunks.append('\n'.join(['\n'.join(it) for it in current_chunk]))
            current_chunk = [item]
            current_size = item_size
        else:
            current_chunk.append(item)
            current_size += item_size + 1

    if current_chunk:
        chunks.append('\n'.join(['\n'.join(it) for it in current_chunk]))

    return chunks if chunks else ['\n'.join(list_lines)]


def _split_by_sentences_md(text: str) -> List[str]:
    """按句子边界切分Markdown段落"""
    # 句子结束标记
    sentence_endings = r'([.!?。！？][\s]*)'

    parts = re.split(sentence_endings, text)

    # 重新组合
    sentences = []
    i = 0
    while i < len(parts):
        sentence = parts[i]
        if i + 1 < len(parts) and re.match(sentence_endings, parts[i + 1]):
            sentence += parts[i + 1]
            i += 2
        else:
            i += 1
        if sentence.strip():
            sentences.append(sentence)

    # 合并句子
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(sentence) > MAX_CHUNK_SIZE:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            for j in range(0, len(sentence), MAX_CHUNK_SIZE):
                chunk = sentence[j:j + MAX_CHUNK_SIZE]
                if chunk.strip():
                    chunks.append(chunk.strip())
            continue

        if len(current_chunk) + len(sentence) <= MAX_CHUNK_SIZE:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def _make_text_item(text: str, skip: bool = False, block_type: str = 'paragraph',
                    is_sub: bool = False, sub_index: int = 0, sub_total: int = 1,
                    prefix: str = '', content_text: str = '') -> Dict:
    """创建文本块对象"""
    return {
        'text': text,
        'original': text,
        'complete': skip,
        'skip': skip,
        'count': 0,
        'block_type': block_type,
        'is_sub': is_sub,
        'sub_index': sub_index,
        'sub_total': sub_total,
        'prefix': prefix,  # 用于标题的#前缀
        'content_text': content_text  # 用于标题的实际内容
    }


def _write_result(trans: Dict, texts: List[Dict], protected_blocks: List[ProtectedBlock]) -> int:
    """
    写入翻译结果
    :return: 翻译字数统计
    """
    trans_type = trans.get('type', '')
    only_translation = 'only' in trans_type
    keep_both = 'both' in trans_type
    text_count = 0

    result_parts = []

    # 用于合并子块
    sub_original = ""
    sub_translated = ""
    sub_block_type = ""
    in_sub_sequence = False

    for item in texts:
        text_count += item.get('count', 0)
        block_type = item.get('block_type', 'paragraph')

        # 分隔符
        if block_type == 'separator':
            if in_sub_sequence:
                _flush_sub_block(result_parts, sub_original, sub_translated,
                                 only_translation, keep_both)
                sub_original = ""
                sub_translated = ""
                in_sub_sequence = False
            result_parts.append("")
            continue

        original = item.get('original', '')
        translated = item.get('text', original)

        if item.get('is_sub', False):
            sub_original += original
            sub_translated += translated
            sub_block_type = block_type
            in_sub_sequence = True

            if item.get('sub_index', 0) == item.get('sub_total', 1) - 1:
                _flush_sub_block(result_parts, sub_original, sub_translated,
                                 only_translation, keep_both)
                sub_original = ""
                sub_translated = ""
                in_sub_sequence = False
        else:
            if item.get('skip', False):
                result_parts.append(original)
            elif keep_both:
                result_parts.append(original)
                result_parts.append(translated)
            elif only_translation:
                result_parts.append(translated)
            else:
                result_parts.append(original)
                result_parts.append(translated)

    # 处理残留的子块
    if in_sub_sequence:
        _flush_sub_block(result_parts, sub_original, sub_translated,
                         only_translation, keep_both)

    # 合并结果
    content = '\n'.join(result_parts)

    # 还原受保护的块
    for block in protected_blocks:
        content = content.replace(block.placeholder, block.content)

    with open(trans['target_file'], 'w', encoding='utf-8') as f:
        f.write(content)

    return text_count


def _flush_sub_block(result_parts: List[str], original: str, translated: str,
                     only_translation: bool, keep_both: bool):
    """输出子块合并结果"""
    if not original and not translated:
        return

    if keep_both:
        result_parts.append(original)
        result_parts.append(translated)
    elif only_translation:
        result_parts.append(translated)
    else:
        result_parts.append(original)
        result_parts.append(translated)
