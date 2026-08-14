# translate/txt.py
"""
TXT文件翻译处理器
分块策略：
1. 按空行分割段落
2. 保持段落完整性
3. 超长段落按句子边界切分
4. 跳过纯标点/数字行
"""

import re
import datetime
import logging
from threading import Event
from typing import List, Dict, Tuple
from . import to_translate
from . import common

# 分块配置
MAX_CHUNK_SIZE = 2000


def start(trans: Dict) -> bool:
    """
    TXT文件翻译入口
    :param trans: 翻译配置字典
    :return: 是否成功
    """
    translate_id = trans['id']
    start_time = datetime.datetime.now()

    # 读取文件
    try:
        content, encoding = _read_file(trans['file_path'])
    except Exception as e:
        logging.error(f"[任务{translate_id}] 读取文件失败: {e}")
        to_translate.error(translate_id, f"读取文件失败: {str(e)}")
        return False

    if not content or not content.strip():
        logging.info(f"[任务{translate_id}] 文件内容为空")
        _write_file(trans['target_file'], "")
        return to_translate.complete(trans, 0, "0秒")

    # 智能分块
    texts = _smart_chunk(content)

    # 统计需要翻译的块数
    to_translate_count = sum(1 for t in texts if not t.get('skip', False))

    if to_translate_count == 0:
        logging.info(f"[任务{translate_id}] 没有需要翻译的内容")
        _write_file(trans['target_file'], content)
        return to_translate.complete(trans, 0, "0秒")

    logging.info(
        f"[任务{translate_id}] 分割为 {len(texts)} 个块，其中 {to_translate_count} 个需要翻译")

    # 执行翻译
    event = Event()
    success = to_translate.translate_batch(trans, texts, event)
    if not success:
        return False

    # 写入结果
    try:
        text_count = _write_result(trans, texts)
    except Exception as e:
        logging.error(f"[任务{translate_id}] 写入文件失败: {e}")
        to_translate.error(translate_id, f"写入文件失败: {str(e)}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    return to_translate.complete(trans, text_count, spend_time)


def _read_file(file_path: str) -> Tuple[str, str]:
    """
    读取文件内容，尝试多种编码
    :return: (内容, 使用的编码)
    """
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'big5', 'iso-8859-1']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise

    raise ValueError("无法识别文件编码")


def _write_file(file_path: str, content: str):
    """写入文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def _smart_chunk(content: str) -> List[Dict]:
    """
    智能分块策略：
    1. 按空行分割成段落
    2. 保持段落完整性
    3. 超长段落按句子边界切分
    """
    texts = []

    # 统一换行符
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # 按空行分割（一个或多个空行）
    paragraphs = re.split(r'\n\s*\n', content)

    for para in paragraphs:
        para = para.strip()

        # 空段落，保留为分隔符
        if not para:
            texts.append(_make_text_item('', skip=True, is_separator=True))
            continue

        # 检查是否需要翻译
        if not _should_translate(para):
            texts.append(_make_text_item(para, skip=True))
            continue

        # 检查长度
        if len(para) <= MAX_CHUNK_SIZE:
            # 段落不超过限制，整段作为一个块
            texts.append(_make_text_item(para))
        else:
            # 超长段落，按句子边界切分
            sub_chunks = _split_by_sentences(para, MAX_CHUNK_SIZE)
            for i, chunk in enumerate(sub_chunks):
                texts.append(_make_text_item(
                    chunk,
                    is_sub=True,
                    sub_index=i,
                    sub_total=len(sub_chunks)
                ))

    return texts


def _should_translate(text: str) -> bool:
    """判断文本是否需要翻译"""
    if not text or not text.strip():
        return False

    text = text.strip()

    # 纯标点/数字/空白
    if common.is_all_punc(text):
        return False

    # 纯数字（可能是页码、序号等）
    if re.match(r'^[\d\s\.\-\+\*\/\=\%\(\)]+$', text):
        return False

    return True


def _split_by_sentences(text: str, max_size: int) -> List[str]:
    """
    按句子边界切分长文本
    优先保持句子完整性
    """
    # 句子结束标记（中英文）
    sentence_endings = r'([.!?。！？；;][\s]*)'

    # 按句子分割，保留分隔符
    parts = re.split(sentence_endings, text)

    # 重新组合（句子+标点）
    sentences = []
    i = 0
    while i < len(parts):
        sentence = parts[i]
        # 如果下一个是标点，合并
        if i + 1 < len(parts) and re.match(sentence_endings, parts[i + 1]):
            sentence += parts[i + 1]
            i += 2
        else:
            i += 1
        if sentence.strip():
            sentences.append(sentence)

    # 合并句子直到接近max_size
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # 单个句子就超过限制，需要强制切分
        if len(sentence) > max_size:
            # 先保存当前块
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # 强制按字符切分超长句子
            for j in range(0, len(sentence), max_size):
                chunk = sentence[j:j + max_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
            continue

        # 检查是否可以合并
        if len(current_chunk) + len(sentence) <= max_size:
            current_chunk += sentence
        else:
            # 当前块已满，保存并开始新块
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    # 保存最后一个块
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def _make_text_item(text: str, skip: bool = False, is_sub: bool = False,
                    sub_index: int = 0, sub_total: int = 1,
                    is_separator: bool = False) -> Dict:
    """创建文本块对象"""
    return {
        'text': text,
        'original': text,
        'complete': skip,  # 跳过的块标记为已完成
        'skip': skip,
        'count': 0,
        'is_sub': is_sub,  # 是否是切分后的子块
        'sub_index': sub_index,
        'sub_total': sub_total,
        'is_separator': is_separator  # 是否是段落分隔符
    }


def _write_result(trans: Dict, texts: List[Dict]) -> int:
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
    in_sub_sequence = False

    for item in texts:
        text_count += item.get('count', 0)

        # 段落分隔符
        if item.get('is_separator', False):
            # 先处理之前的子块序列
            if in_sub_sequence:
                if keep_both:
                    result_parts.append(sub_original)
                    result_parts.append(sub_translated)
                elif only_translation:
                    result_parts.append(sub_translated)
                else:
                    result_parts.append(sub_original)
                    result_parts.append(sub_translated)
                sub_original = ""
                sub_translated = ""
                in_sub_sequence = False
            result_parts.append("")  # 空行分隔
            continue

        original = item.get('original', '')
        translated = item.get('text', original)

        if item.get('is_sub', False):
            # 子块，累加
            sub_original += original
            sub_translated += translated
            in_sub_sequence = True

            # 如果是最后一个子块，输出
            if item.get('sub_index', 0) == item.get('sub_total', 1) - 1:
                if keep_both:
                    result_parts.append(sub_original)
                    result_parts.append(sub_translated)
                elif only_translation:
                    result_parts.append(sub_translated)
                else:
                    result_parts.append(sub_original)
                    result_parts.append(sub_translated)
                sub_original = ""
                sub_translated = ""
                in_sub_sequence = False
        else:
            # 普通块
            if item.get('skip', False):
                # 跳过的块保留原文
                result_parts.append(original)
            elif keep_both:
                result_parts.append(original)
                result_parts.append(translated)
            elif only_translation:
                result_parts.append(translated)
            else:
                result_parts.append(original)
                result_parts.append(translated)

    # 处理最后可能残留的子块
    if in_sub_sequence:
        if keep_both:
            result_parts.append(sub_original)
            result_parts.append(sub_translated)
        elif only_translation:
            result_parts.append(sub_translated)
        else:
            result_parts.append(sub_original)
            result_parts.append(sub_translated)

    # 合并输出，用双换行分隔段落
    content = '\n\n'.join(result_parts)

    _write_file(trans['target_file'], content)

    return text_count
