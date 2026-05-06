# translate/html.py
"""
HTML/HTM文件翻译处理器
核心策略：占位符替换法
1. 用BeautifulSoup解析HTML
2. 遍历DOM树，提取所有需要翻译的文本节点和属性值
3. 用占位符替换原文，记录映射关系
4. 对提取的文本分块并翻译
5. 将翻译结果按映射关系替换回占位符
6. 还原完整HTML，确保结构完全不变
"""

import re
import datetime
import logging
import threading
from typing import List, Dict, Tuple
from . import to_translate
from . import common

MAX_CHUNK_SIZE = 2000

SKIP_TAGS = frozenset({
    'script', 'style', 'noscript'
})

PRESERVE_TAGS = frozenset({
    'code', 'kbd', 'samp', 'var'
})

VOID_TAGS = frozenset({
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr'
})

TRANSLATABLE_ATTRS = frozenset({
    'alt', 'title', 'placeholder', 'aria-label', 'aria-description'
})

_counter_lock = threading.Lock()
_counter = 0

PLACEHOLDER_PREFIX = '[[HTMLTRANS_'
PLACEHOLDER_SUFFIX = ']]'


def _next_placeholder(tag: str) -> str:
    global _counter
    with _counter_lock:
        _counter += 1
        return f'{PLACEHOLDER_PREFIX}{tag}_{_counter}{PLACEHOLDER_SUFFIX}'


def start(trans: Dict) -> bool:
    translate_id = trans['id']
    start_time = datetime.datetime.now()

    try:
        content, encoding = _read_file(trans['file_path'])
    except Exception as e:
        logging.error(f"[任务{translate_id}] 读取文件失败: {e}")
        to_translate.error(translate_id, f"读取文件失败: {str(e)}")
        return False

    if not content or not content.strip():
        logging.info(f"[任务{translate_id}] 文件内容为空")
        _write_file(trans['target_file'], "")
        to_translate.complete(trans, 0, "0秒")
        return True

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logging.error(f"[任务{translate_id}] 需要安装 beautifulsoup4")
        to_translate.error(translate_id, "需要安装 beautifulsoup4: pip install beautifulsoup4")
        return False

    try:
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        logging.error(f"[任务{translate_id}] HTML解析失败: {e}")
        to_translate.error(translate_id, f"HTML解析失败: {str(e)}")
        return False

    placeholder_map = {}
    extracted_texts = []

    try:
        _extract_and_placeholder(soup, placeholder_map, extracted_texts)
    except Exception as e:
        logging.error(f"[任务{translate_id}] 提取文本节点失败: {e}")
        to_translate.error(translate_id, f"提取文本节点失败: {str(e)}")
        return False

    if not extracted_texts:
        logging.info(f"[任务{translate_id}] 没有需要翻译的文本内容")
        _write_file(trans['target_file'], content)
        to_translate.complete(trans, 0, "0秒")
        return True

    texts = _build_text_items(extracted_texts)

    to_translate_count = sum(1 for t in texts if not t.get('skip', False))
    if to_translate_count == 0:
        logging.info(f"[任务{translate_id}] 没有需要翻译的内容")
        _write_file(trans['target_file'], content)
        to_translate.complete(trans, 0, "0秒")
        return True

    logging.info(
        f"[任务{translate_id}] 提取 {len(extracted_texts)} 个文本段，"
        f"其中 {to_translate_count} 个需要翻译")

    event = threading.Event()
    success = to_translate.translate_batch(trans, texts, event)
    if not success:
        return False

    try:
        text_count = _write_result(trans, texts, extracted_texts, placeholder_map, soup)
    except Exception as e:
        logging.error(f"[任务{translate_id}] 写入文件失败: {e}")
        to_translate.error(translate_id, f"写入文件失败: {str(e)}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    to_translate.complete(trans, text_count, spend_time)
    return True


def _read_file(file_path: str) -> Tuple[str, str]:
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'big5', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
        except Exception:
            raise
    raise ValueError("无法识别文件编码")


def _write_file(file_path: str, content: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def _extract_and_placeholder(soup, placeholder_map: Dict, extracted_texts: List[Dict]):
    """
    遍历DOM树，提取文本并用占位符替换
    所有操作都在同一个soup对象上完成，保证引用有效
    """
    try:
        from bs4 import NavigableString, Comment, Tag, ProcessingInstruction, Doctype
    except ImportError:
        raise ImportError("需要安装 beautifulsoup4")

    def walk(element, in_preserve: bool = False):
        try:
            if isinstance(element, (Comment, ProcessingInstruction, Doctype)):
                return

            if isinstance(element, NavigableString):
                text = str(element)
                if not text.strip():
                    return

                if in_preserve:
                    ph = _next_placeholder('p')
                    placeholder_map[ph] = text
                    extracted_texts.append({
                        'placeholder': ph,
                        'original': text,
                        'skip': True,
                        'type': 'text'
                    })
                    element.replace_with(NavigableString(ph))
                    return

                if _should_translate(text):
                    ph = _next_placeholder('t')
                    placeholder_map[ph] = text
                    extracted_texts.append({
                        'placeholder': ph,
                        'original': text,
                        'skip': False,
                        'type': 'text'
                    })
                    element.replace_with(NavigableString(ph))
                else:
                    ph = _next_placeholder('s')
                    placeholder_map[ph] = text
                    extracted_texts.append({
                        'placeholder': ph,
                        'original': text,
                        'skip': True,
                        'type': 'text'
                    })
                    element.replace_with(NavigableString(ph))
                return

            if isinstance(element, Tag):
                tag_name = (element.name or '').lower()

                if tag_name in SKIP_TAGS:
                    return

                is_preserve = in_preserve or tag_name in PRESERVE_TAGS

                if tag_name in VOID_TAGS:
                    for attr_name in TRANSLATABLE_ATTRS:
                        attr_val = element.get(attr_name, '')
                        if attr_val and isinstance(attr_val, str) and _should_translate(attr_val):
                            ph = _next_placeholder('a')
                            placeholder_map[ph] = attr_val
                            extracted_texts.append({
                                'placeholder': ph,
                                'original': attr_val,
                                'skip': False,
                                'type': 'attr',
                                'element': element,
                                'attr_name': attr_name
                            })
                            element[attr_name] = ph
                    return

                for child in list(element.children):
                    walk(child, is_preserve)

        except Exception as e:
            logging.warning(f"遍历DOM节点时异常(已跳过): {e}")

    for child in list(soup.children):
        walk(child, False)


def _should_translate(text: str) -> bool:
    if not text or not text.strip():
        return False
    text = text.strip()
    if common.is_all_punc(text):
        return False
    if re.match(r'^[\d\s\.\-\+\*\/\=\%\(\)\,]+$', text):
        return False
    if len(text) <= 1:
        return False
    return True


def _build_text_items(extracted_texts: List[Dict]) -> List[Dict]:
    """
    将提取的文本段构建为翻译引擎需要的 texts 列表
    超长文本进行切分，切分后的所有子块共享同一个占位符
    """
    texts = []
    for item in extracted_texts:
        if item['skip']:
            texts.append({
                'text': item['original'],
                'original': item['original'],
                'complete': True,
                'skip': True,
                'count': 0,
                'placeholder': item['placeholder'],
                'is_sub': False
            })
        elif len(item['original']) <= MAX_CHUNK_SIZE:
            texts.append({
                'text': item['original'],
                'original': item['original'],
                'complete': False,
                'skip': False,
                'count': 0,
                'placeholder': item['placeholder'],
                'is_sub': False
            })
        else:
            sub_chunks = _split_by_sentences(item['original'], MAX_CHUNK_SIZE)
            for i, chunk in enumerate(sub_chunks):
                texts.append({
                    'text': chunk,
                    'original': chunk,
                    'complete': False,
                    'skip': False,
                    'count': 0,
                    'placeholder': item['placeholder'],
                    'is_sub': True,
                    'sub_index': i,
                    'sub_total': len(sub_chunks)
                })
    return texts


def _split_by_sentences(text: str, max_size: int) -> List[str]:
    sentence_endings = r'([.!?。！？；;][\s]*)'
    parts = re.split(sentence_endings, text)
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

    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(sentence) > max_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            for j in range(0, len(sentence), max_size):
                chunk = sentence[j:j + max_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
            continue
        if len(current_chunk) + len(sentence) <= max_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks if chunks else [text]


def _write_result(trans: Dict, texts: List[Dict], extracted_texts: List[Dict],
                  placeholder_map: Dict, soup) -> int:
    """
    写入翻译结果
    步骤：
    1. 从texts中收集每个占位符对应的翻译结果
    2. 将attr类型的翻译结果直接设置到DOM元素上
    3. 将soup序列化为HTML字符串
    4. 用字符串替换将文本占位符替换为翻译结果
    HTML文件始终保持完整HTML结构输出，不进行only_translation处理
    """
    text_count = 0

    placeholder_translations = {}

    for item in texts:
        if item.get('skip', False):
            placeholder_translations[item['placeholder']] = item['original']
            continue

        translated = item.get('text', item.get('original', ''))
        text_count += item.get('count', 0)
        ph = item['placeholder']

        if item.get('is_sub', False):
            if ph not in placeholder_translations:
                placeholder_translations[ph] = ''
            placeholder_translations[ph] += translated
        else:
            placeholder_translations[ph] = translated

    for item in extracted_texts:
        if item['type'] == 'attr':
            element = item.get('element')
            attr_name = item.get('attr_name')
            if element is not None and attr_name:
                translated_val = placeholder_translations.get(item['placeholder'], item['original'])
                try:
                    element[attr_name] = translated_val
                except Exception as e:
                    logging.warning(f"替换属性值失败: {e}")

    html_str = str(soup)

    for ph, original_text in placeholder_map.items():
        translated_text = placeholder_translations.get(ph, original_text)
        html_str = html_str.replace(ph, translated_text)

    _write_file(trans['target_file'], html_str)

    return text_count
