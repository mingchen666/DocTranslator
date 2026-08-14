# translate/csv_handle.py
import os
import datetime
import csv
import logging
import re
from typing import List, Dict, Any, Tuple
from threading import Event
from . import to_translate
from . import common

# 分块配置
MAX_CHUNK_SIZE = 1500


def start(trans: Dict[str, Any]) -> bool:
    """
    CSV文件翻译入口
    :param trans: 翻译配置字典
    :return: 是否成功
    """
    translate_id = trans['id']
    start_time = datetime.datetime.now()

    # 读取CSV文件
    try:
        content, encoding, dialect = _read_csv_file(trans['file_path'])
    except Exception as e:
        logging.error(f"[任务{translate_id}] 读取CSV文件失败: {e}")
        to_translate.error(translate_id, f"读取CSV文件失败: {str(e)}")
        return False

    if not content:
        logging.info(f"[任务{translate_id}] CSV文件为空")
        _write_csv_file(trans['target_file'], content, encoding, dialect)
        return to_translate.complete(trans, 0, "0秒")

    # 提取需要翻译的单元格
    texts = []
    cell_map = []  # 记录单元格位置

    for row_idx, row in enumerate(content):
        for col_idx, cell in enumerate(row):
            if _should_translate(cell):
                # 检查是否需要分块
                if len(cell) > MAX_CHUNK_SIZE:
                    sub_cells = _split_cell(cell, MAX_CHUNK_SIZE)
                    parent_uid = f"cell_{row_idx}_{col_idx}"
                    for i, sub_cell in enumerate(sub_cells):
                        texts.append({
                            'text': sub_cell,
                            'original': sub_cell,
                            'complete': False,
                            'count': 0,
                            '_uid': f"{parent_uid}_{i}",
                            'is_sub': True,
                            'sub_index': i,
                            'sub_total': len(sub_cells)
                        })
                        cell_map.append({
                            'row': row_idx,
                            'col': col_idx,
                            'text_index': len(texts) - 1,
                            'is_sub': True,
                            'parent_uid': parent_uid
                        })
                else:
                    uid = f"cell_{row_idx}_{col_idx}"
                    texts.append({
                        'text': cell,
                        'original': cell,
                        'complete': False,
                        'count': 0,
                        '_uid': uid,
                        'is_sub': False
                    })
                    cell_map.append({
                        'row': row_idx,
                        'col': col_idx,
                        'text_index': len(texts) - 1,
                        'is_sub': False
                    })

    if not texts:
        logging.info(f"[任务{translate_id}] CSV中没有需要翻译的内容")
        _write_csv_file(trans['target_file'], content, encoding, dialect)
        return to_translate.complete(trans, 0, "0秒")

    logging.info(f"[任务{translate_id}] 提取到 {len(texts)} 个文本块")

    # 批量翻译
    event = Event()
    success = to_translate.translate_batch(trans, texts, event)
    if not success:
        return False

    # 重建CSV内容
    try:
        text_count = _rebuild_csv(content, texts, cell_map, trans.get('type', ''))
        _write_csv_file(trans['target_file'], content, encoding, dialect)
    except Exception as e:
        logging.error(f"[任务{translate_id}] 写入CSV文件失败: {e}")
        to_translate.error(translate_id, f"写入CSV文件失败: {str(e)}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    return to_translate.complete(trans, text_count, spend_time)


def _read_csv_file(file_path: str) -> Tuple[List[List[str]], str, Any]:
    """
    读取CSV文件，尝试多种编码和分隔符
    :return: (内容列表, 使用的编码, csv dialect)
    """
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'iso-8859-1', 'big5']

    # 先尝试检测分隔符
    with open(file_path, 'rb') as f:
        sample = f.read(1024).decode('utf-8', errors='ignore')
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(sample)
        except:
            dialect = csv.excel  # 默认使用Excel的CSV格式

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.reader(f, dialect=dialect)
                content = list(reader)
            return content, encoding, dialect
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise

    raise ValueError("无法识别CSV文件编码")


def _write_csv_file(file_path: str, content: List[List[str]],
                    encoding: str = 'utf-8', dialect: Any = None):
    """
    写入CSV文件，保持原始格式
    """
    if dialect is None:
        dialect = csv.excel

    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding=encoding, newline='') as f:
        writer = csv.writer(f, dialect=dialect)
        writer.writerows(content)


def _should_translate(text) -> bool:
    """
    判断单元格是否需要翻译
    过滤数字、日期、公式等不需要翻译的内容
    """
    if text is None:
        return False

    # 转换为字符串
    if not isinstance(text, str):
        # 尝试转换数字为字符串进行进一步检查
        try:
            text = str(text)
        except:
            return False

    text = text.strip()
    if not text:
        return False

    # CSV没有单元格类型元数据，以等号开头的内容按公式原样保留。
    if text.startswith('='):
        return False

    # 跳过纯标点符号
    if common.is_all_punc(text):
        return False

    # 跳过纯数字（包括科学计数法）
    if re.match(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?%?$', text):
        return False

    # 跳过货币格式
    if re.match(r'^[$￥€£]\s*[+-]?(\d{1,3}(,\d{3})*(\.\d+)?|\.\d+)$', text):
        return False

    # 跳过百分比格式
    if re.match(r'^[+-]?(\d{1,3}(,\d{3})*(\.\d+)?|\.\d+)%$', text):
        return False

    # 跳过日期格式
    date_patterns = [
        r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$',  # 2023-12-31
        r'^\d{1,2}[-/]\d{1,2}[-/]\d{4}$',  # 12-31-2023
        r'^\d{1,2}\.\d{1,2}\.\d{4}$',  # 31.12.2023
        r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}$',  # Dec 31, 2023
        r'^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}$',  # 31 Dec 2023
    ]
    for pattern in date_patterns:
        if re.match(pattern, text):
            return False

    # 跳过时间格式
    time_patterns = [
        r'^\d{1,2}:\d{2}(:\d{2})?(\s*[AP]M)?$',  # 12:30 PM
        r'^\d{1,2}:\d{2}(:\d{2})?(\s*[ap]m)?$',  # 12:30 pm
    ]
    for pattern in time_patterns:
        if re.match(pattern, text):
            return False

    # 跳过布尔值
    if text.lower() in ['true', 'false', 'yes', 'no', 'y', 'n']:
        return False

    # 跳过常见的标识符
    if re.match(r'^[A-Z]{2,4}\d{1,6}$', text):  # SKU123
        return False

    # 跳过邮箱
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text):
        return False

    # 跳过URL
    if re.match(r'^https?://', text):
        return False

    # 跳过文件路径
    if re.match(r'^[A-Za-z]:\\', text) or (text.startswith('/') and '\\' in text):
        return False

    # 跳过电话号码
    if re.match(r'^[\+]?[1-9][\d\-\s\(\)]{7,15}$', text):
        return False

    return True


def _split_cell(cell: str, max_length: int) -> List[str]:
    """
    将超长单元格内容分割
    优先按句子边界切分，保持语义完整
    """
    # 按句子分割（支持中英文）
    sentence_pattern = r'(?<=[.!?。！？；;])\s+'
    sentences = re.split(sentence_pattern, cell)

    parts = []
    current_part = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # 如果当前部分加上新句子超过限制
        if len(current_part) + len(sentence) + 1 > max_length:
            if current_part:
                parts.append(current_part)
                current_part = ""

            # 如果单个句子就超过限制，强制按字符切分
            if len(sentence) > max_length:
                for i in range(0, len(sentence), max_length):
                    parts.append(sentence[i:i + max_length])
            else:
                current_part = sentence
        else:
            if current_part:
                current_part += " " + sentence
            else:
                current_part = sentence

    if current_part:
        parts.append(current_part)

    return parts if parts else [cell]


def _rebuild_csv(content: List[List[str]], texts: List[Dict],
                 cell_map: List[Dict], trans_type: str) -> int:
    """
    重建CSV内容，处理分块合并
    """
    text_count = 0
    keep_both = 'both' in trans_type

    # 按单元格分组处理
    cell_translations = {}  # (row, col) -> {'original': str, 'translated': str}

    for mapping in cell_map:
        row = mapping['row']
        col = mapping['col']
        text_index = mapping['text_index']
        is_sub = mapping.get('is_sub', False)

        if text_index >= len(texts):
            continue

        text_item = texts[text_index]
        text_count += text_item.get('count', 0)

        key = (row, col)
        if key not in cell_translations:
            cell_translations[key] = {
                'original': '',
                'translated': ''
            }

        if is_sub:
            # 分块的内容需要合并
            cell_translations[key]['original'] += text_item.get('original', '')
            cell_translations[key]['translated'] += text_item.get('text', '')
        else:
            cell_translations[key]['original'] = text_item.get('original', '')
            cell_translations[key]['translated'] = text_item.get('text', '')

    # 应用翻译结果
    for (row, col), trans_data in cell_translations.items():
        if row < len(content) and col < len(content[row]):
            original = trans_data['original'].strip()
            translated = trans_data['translated'].strip()

            if keep_both:
                # 双语模式：保留原文和译文
                if original and translated:
                    content[row][col] = f"{original}\n{translated}"
                else:
                    content[row][col] = translated or original
            else:
                # 仅译文模式
                content[row][col] = translated or original

    return text_count
