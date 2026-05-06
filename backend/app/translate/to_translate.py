# translate/to_translate.py
import logging
import re
import time
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import  Lock
from . import common
from . import db

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒

# 进度更新锁
_progress_lock = Lock()

_last_reported_progress = {}  # 存储每个任务的上次报告进度 {task_id: progress}


def update_progress(texts, translate_id, force_update=False):
    """
    智能更新翻译进度
    :param texts: 文本块列表
    :param translate_id: 任务ID
    :param force_update: 是否强制更新（任务完成时使用）
    """
    total = len(texts)
    completed = sum(1 for t in texts if t.get('complete', False))

    if total <= 0:
        return

    current_progress = round((completed / total) * 100, 1)

    with _progress_lock:
        last_progress = _last_reported_progress.get(translate_id, 0)

        # 进度更新条件：
        # 1. 强制更新（任务完成/失败）
        # 2. 进度增长超过15%
        # 3. 首次更新（从0开始）
        # 4. 接近完成时的特殊处理（90%以上每10%更新）
        progress_delta = current_progress - last_progress

        should_update = (
                force_update or
                progress_delta >= 15.0 or  # 每15%更新一次
                (last_progress == 0 and current_progress > 0) or  # 首次进度
                (current_progress >= 90 and progress_delta >= 10.0)  # 90%后每10%更新
        )

        if should_update:
            try:
                db.execute("UPDATE translate SET process=%s WHERE id=%s",
                           current_progress, translate_id)
                _last_reported_progress[translate_id] = current_progress
                logging.info(f"[任务{translate_id}] 进度更新: {current_progress}%")
            except Exception as e:
                logging.error(f"更新进度失败: {e}")


def complete(trans, text_count, spend_time):
    """标记任务完成"""
    try:
        translate_id = trans['id']
        target_filesize = 1

        db.execute(
            "UPDATE translate SET status='done', end_at=NOW(), process=100, "
            "target_filesize=%s, word_count=%s WHERE id=%s",
            target_filesize, text_count, translate_id
        )

        # 清理进度缓存
        _last_reported_progress.pop(translate_id, None)

        logging.info(f"[任务{translate_id}] 翻译完成")

    except Exception as e:
        logging.error(f"更新完成状态失败: {e}")


def error(translate_id, message):
    """标记任务失败"""
    try:
        message = str(message)[:500] if message else "未知错误"

        # 清理进度缓存
        _last_reported_progress.pop(translate_id, None)

        db.execute(
            "UPDATE translate SET failed_count=failed_count+1, status='failed', "
            "end_at=NOW(), failed_reason=%s WHERE id=%s",
            message, translate_id
        )
    except Exception as e:
        logging.error(f"更新失败状态失败: {e}")


class TranslationError(Exception):
    """翻译异常基类"""
    pass


class FatalError(TranslationError):
    """致命错误，不可重试"""
    pass


def translate_batch(trans, texts, event):
    """
    批量翻译文本块（线程池模式）
    :param trans: 翻译配置
    :param texts: 文本块列表
    :param event: 中断事件
    :return: 是否全部成功
    """
    translate_id = trans['id']
    max_threads = common.parse_threads(trans.get('threads'))

    # 过滤需要翻译的文本块索引
    to_translate_indices = [
        i for i, t in enumerate(texts)
        if not t.get('complete', False) and not t.get('skip', False)
    ]

    if not to_translate_indices:
        return True

    logging.info(
        f"[任务{translate_id}] 开始翻译 {len(to_translate_indices)} 个文本块，线程数: {max_threads}")

    has_fatal_error = False
    completed_count = 0
    total_count = len(to_translate_indices)

    def translate_single(index):
        """翻译单个文本块"""
        nonlocal has_fatal_error, completed_count

        if event.is_set() or has_fatal_error:
            return False

        text_item = texts[index]

        try:
            result = _translate_text_block(trans, text_item)
            text_item['text'] = result['translated_text']
            text_item['count'] = result['count']
            text_item['complete'] = True

            # 更新进度
            with _progress_lock:
                completed_count += 1
                progress = round((completed_count / total_count) * 100, 1)
                db.execute("UPDATE translate SET process=%s WHERE id=%s", progress, translate_id)

            return True

        except FatalError as e:
            logging.error(f"[任务{translate_id}] 致命错误: {str(e)}")
            has_fatal_error = True
            error(translate_id, str(e))
            event.set()
            return False

        except Exception as e:
            logging.error(f"[任务{translate_id}] 文本块{index}翻译失败，保留原文: {str(e)}")
            text_item['complete'] = True
            text_item['count'] = count_text(text_item.get('text', ''))

            with _progress_lock:
                completed_count += 1

            return True  # 保留原文，继续处理其他块

    # 使用线程池执行
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(translate_single, idx): idx
            for idx in to_translate_indices
        }

        # 等待完成
        for future in as_completed(future_to_index):
            if event.is_set() or has_fatal_error:
                # 取消剩余任务
                executor.shutdown(wait=False, cancel_futures=True)
                return False

            try:
                future.result()
            except Exception as e:
                logging.error(f"[任务{translate_id}] 线程执行异常: {e}")

    return not has_fatal_error


def get(trans, event, texts, index):
    """
    翻译单个文本块的入口函数（兼容旧接口）
    :param trans: 翻译任务配置
    :param event: 线程事件，用于中断
    :param texts: 文本块列表
    :param index: 当前处理的索引
    """
    if event.is_set():
        return

    text_item = texts[index]
    translate_id = trans['id']

    try:
        # 执行翻译
        result = _translate_text_block(trans, text_item)

        # 更新结果
        text_item['text'] = result['translated_text']
        text_item['count'] = result['count']
        text_item['complete'] = True

    except FatalError as e:
        # 致命错误，标记任务失败
        logging.error(f"[任务{translate_id}] 致命错误: {str(e)}")
        if not event.is_set():
            error(translate_id, str(e))
        event.set()
        return

    except Exception as e:
        # 其他错误，保留原文，标记完成
        logging.error(f"[任务{translate_id}] 文本块{index}翻译失败，保留原文: {str(e)}")
        text_item['complete'] = True
        text_item['count'] = count_text(text_item.get('text', ''))

    finally:
        texts[index] = text_item
        if not event.is_set():
            update_progress(texts, translate_id)


def _translate_text_block(trans, text_item):
    """
    翻译单个文本块，包含重试和备用模型逻辑
    :return: {'translated_text': str, 'count': int}
    """
    original_text = text_item.get('text', '')
    if not original_text or not original_text.strip():
        return {'translated_text': original_text, 'count': 0}

    server = trans.get('server', 'openai')

    # 百度翻译没有备用模型的概念
    if server == 'baidu':
        result = _try_translate_with_retries(trans, text_item, 'baidu')
        if result:
            return result
        raise FatalError("百度翻译失败")
    else:
        # OpenAI等API有备用模型
        model = trans.get('model')
        backup_model = trans.get('backup_model')

        # 尝试主模型
        result = _try_translate_with_retries(trans, text_item, model)
        if result:
            return result

        # 主模型失败，尝试备用模型
        if backup_model and backup_model.strip():
            logging.info(f"[任务{trans['id']}] 主模型{model}失败，切换到备用模型{backup_model}")
            time.sleep(RETRY_DELAY)
            result = _try_translate_with_retries(trans, text_item, backup_model)
            if result:
                return result

        # 全部失败
        raise FatalError(f"主模型和备用模型均失败，最后使用模型: {backup_model or model}")


def _try_translate_with_retries(trans, text_item, model):
    """
    使用指定模型重试翻译
    :return: 成功返回结果dict，失败返回None
    """
    translate_id = trans['id']
    original_text = text_item.get('text', '')

    for attempt in range(1, MAX_RETRIES + 1):
        try:

            # 执行翻译
            server = trans.get('server', 'openai')
            if server == 'baidu':
                logging.info(f"[任务{translate_id}] 百度翻译 第{attempt}次请求")
                translated = _translate_baidu(trans, original_text)
            else:
                logging.info(f"[任务{translate_id}] ,翻译模型{model} ,第{attempt}次请求")
                translated = _translate_openai(trans, original_text, model)

            # 验证翻译结果
            if not _is_valid_translation(translated):
                logging.warning(
                    f"类型: {trans.get('server', '')}——[任务{translate_id}] 翻译结果无效: {translated[:50] if translated else 'None'}...")
                time.sleep(RETRY_DELAY)
                continue

            # 过滤deepseek思考标签
            translated = re.sub(r'', '', translated, flags=re.DOTALL).strip()

            return {'translated_text': translated, 'count': count_text(original_text)}

        except openai.RateLimitError as e:
            logging.warning(f"[任务{translate_id}] 速率限制，等待后重试: {e}")
            time.sleep(RETRY_DELAY * attempt * 2)  # 递增等待，限速时等待更长
            continue

        except openai.AuthenticationError as e:
            raise FatalError(f"API密钥无效: {e}")

        except openai.APIConnectionError as e:
            logging.warning(f"[任务{translate_id}] 连接错误: {e}")
            time.sleep(RETRY_DELAY)
            continue

        except Exception as e:
            logging.warning(f"[任务{translate_id}] 翻译异常: {e}")
            time.sleep(RETRY_DELAY)
            continue

    return None  # 所有重试失败


def _translate_openai(trans, text, model):
    """调用OpenAI兼容API翻译"""
    target_lang = trans.get('lang', '英语')
    base_prompt = trans.get('prompt', '')
    extension = trans.get('extension', '').lower()

    # 动态匹配术语并注入prompt
    final_prompt = _inject_matched_terms(trans, text, base_prompt, target_lang)

    # Markdown特殊处理
    if extension == '.md':
        final_prompt += "\n请保持Markdown格式不变，只翻译文本内容。"

    # HTML特殊处理
    if extension in ('.html', '.htm'):
        final_prompt += "\n请保持HTML标签和属性不变，只翻译标签之间的文本内容。不要添加或删除任何HTML标签。"

    messages = [
        {"role": "system", "content": final_prompt},
        {"role": "user", "content": text}
    ]
    print(f"[任务{trans['id']}] 模型{model} ，提示词: {final_prompt}")
    # 禁用日志
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7
    )

    return response.choices[0].message.content


def _translate_baidu(trans, text):
    """调用百度翻译API"""
    from .baidu.main import baidu_translate

    use_term_base = trans.get('use_baidu_terms', False)

    return baidu_translate(
        text=text,
        appid=trans.get('app_id'),
        app_key=trans.get('app_key'),
        from_lang='auto',
        to_lang=trans.get('lang', 'en'),
        use_term_base=use_term_base
    )


def _inject_matched_terms(trans, text, base_prompt, target_lang):
    """
    动态匹配术语并注入prompt
    使用正则表达式精确匹配术语（单词边界）
    """
    terms_dict = trans.get('terms_dict')
    if not terms_dict:
        logging.debug("无术语库数据，跳过术语匹配")
        return base_prompt.replace("{target_lang}", target_lang)

    matched_terms = []


    for term_pair in terms_dict:
        source_term = term_pair['source']
        target_term = term_pair['target']

        if _is_term_matched_in_text(source_term, text):
            matched_terms.append(f"{source_term} → {target_term}")
            logging.debug(f"匹配到术语: {source_term} → {target_term}")

    # 构建最终prompt
    if matched_terms:
        # 去重（防止重复术语）
        unique_terms = list(dict.fromkeys(matched_terms))
        terms_section = "【术语翻译对照表如下】\n" + "\n".join(unique_terms)
        full_prompt = f"{terms_section}\n\n{base_prompt}"
    else:
        full_prompt = base_prompt
        logging.debug("当前文本无匹配术语")

    return full_prompt.replace("{target_lang}", target_lang)


def _is_term_matched_in_text(source_term, text):
    """
    检查术语是否在文本中精确匹配
    使用多种匹配策略以提高准确性
    """
    if not source_term or not text:
        return False

    source_term = source_term.strip()
    if not source_term:
        return False

    # 策略1：单词边界匹配（适用于英文单词）
    if _is_word_boundary_match(source_term, text):
        return True

    # 策略2：完整词组匹配（适用于中文词组、专业术语）
    if _is_phrase_match(source_term, text):
        return True

    # 策略3：混合语言匹配（适用于中英混合术语）
    if _is_mixed_language_match(source_term, text):
        return True

    return False


def _is_word_boundary_match(source_term, text):
    """
    单词边界匹配：使用\b进行精确单词匹配
    适用于：API, JSON, HTTP, database 等英文术语
    """
    try:
        # 转义特殊字符
        escaped_term = re.escape(source_term)

        # 构建单词边界模式
        pattern = r'\b' + escaped_term + r'\b'

        # 不区分大小写匹配
        return bool(re.search(pattern, text, re.IGNORECASE))

    except Exception as e:
        logging.warning(f"单词边界匹配失败: {e}")
        return False


def _is_phrase_match(source_term, text):
    """
    词组匹配：适用于中文词组或多词术语
    使用标点符号和空白作为边界
    适用于：人工智能、机器学习、REST API 等
    """
    try:
        # 转义特殊字符
        escaped_term = re.escape(source_term)

        # 定义词组边界：空白、标点符号、行首行尾
        boundary = r'(?:^|[\s\p{P}])'  # 开始边界
        end_boundary = r'(?=[\s\p{P}]|$)'  # 结束边界

        # 构建词组模式
        pattern = boundary + escaped_term + end_boundary

        # 不区分大小写匹配
        return bool(re.search(pattern, text, re.IGNORECASE))

    except Exception:
        # 如果正则表达式不支持\p{P}，使用常见标点符号
        try:
            escaped_term = re.escape(source_term)
            punctuation = r'[\s.,!?;:()\[\]{}"\'`~@#$%^&*+=|\\/<>，。！？；：（）【】{}""''`～@#￥%…&*+=|\\/<>]'
            boundary = r'(?:^|' + punctuation + r')'
            end_boundary = r'(?=' + punctuation + r'|$)'
            pattern = boundary + escaped_term + end_boundary

            return bool(re.search(pattern, text, re.IGNORECASE))
        except Exception as e:
            logging.warning(f"词组匹配失败: {e}")
            return False


def _is_mixed_language_match(source_term, text):
    """
    混合语言匹配：适用于中英混合的术语
    如：API接口、JSON数据、HTTP请求 等
    """
    try:
        # 将术语按中英文拆分
        parts = _split_mixed_term(source_term)
        if len(parts) <= 1:
            return False

        # 检查各部分是否都存在且顺序正确
        current_pos = 0
        text_lower = text.lower()

        for part in parts:
            part_lower = part.lower()
            pos = text_lower.find(part_lower, current_pos)
            if pos == -1:
                return False
            current_pos = pos + len(part)

        return True

    except Exception as e:
        logging.warning(f"混合语言匹配失败: {e}")
        return False


def _split_mixed_term(term):
    """
    拆分中英混合术语
    例如：API接口 -> ["API", "接口"]
    """
    import re

    # 按中英文字符边界拆分
    pattern = r'([a-zA-Z]+|[\u4e00-\u9fff]+|[0-9]+)'
    parts = re.findall(pattern, term)

    # 过滤空字符串和单字符
    return [p for p in parts if len(p.strip()) > 0]

def _is_valid_translation(content):
    """验证翻译结果是否有效"""
    if not content:
        return False
    invalid_prefixes = [
        "Sorry, I cannot", "I am sorry,", "I'm sorry,",
        "Sorry, I can't", "Sorry, I need more", "抱歉，无法",
        "错误：提供的文本", "无法翻译", "抱歉，我无法",
        "对不起，我无法", "ご指示の内容は", "申し訳ございません",
        "Простите，", "Извините,", "Lo siento,"
    ]
    for prefix in invalid_prefixes:
        if content.startswith(prefix):
            return False
    return True


def count_text(text):
    """统计文本字数"""
    if not text:
        return 0
    count = 0
    for char in text:
        if common.is_chinese(char):
            count += 1
        elif char and char != " ":
            count += 0.5
    return int(count)


def init_openai(url, key):
    """初始化OpenAI配置"""
    openai.api_key = key
    if not url.endswith("/v1/"):
        if url.endswith("/v1"):
            url = url + "/"
        elif url.endswith("/"):
            url = url + "v1/"
        else:
            url = url + "/v1/"
    openai.base_url = url


def check(model):
    """检查模型可用性"""
    try:
        message = [
            {"role": "system", "content": "测试"},
            {"role": "user", "content": "你好"}
        ]
        openai.chat.completions.create(model=model, messages=message, max_tokens=10)
        return "OK"
    except openai.AuthenticationError:
        return "API密钥无效"
    except openai.APIConnectionError:
        return "无法连接到API服务器"
    except openai.RateLimitError:
        return "访问速率限制"
    except Exception as e:
        return f"检查失败: {str(e)}"
