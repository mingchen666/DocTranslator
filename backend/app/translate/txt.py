import os
import threading
from . import to_translate
from . import common
import datetime
import time
import re


def start(trans):
    # 允许的最大线程
    threads = trans['threads']
    if threads is None or int(threads) < 0:
        max_threads = 10
    else:
        max_threads = int(threads)
    # 当前执行的索引位置
    run_index = 0
    start_time = datetime.datetime.now()

    try:
        with open(trans['file_path'], 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"无法读取文件 {trans['file_path']}: {e}")
        return False

    texts = []

    # 按段落分割内容
    paragraphs = content.split('\n\n')  # 假设段落之间用两个换行符分隔
    # 支持最多单词量
    max_word = 1000
    # 翻译每个段落
    for paragraph in paragraphs:
        if check_text(paragraph):
            # 如果段落长度超过 1000 字，进行分割
            if len(paragraph) > max_word:
                sub_paragraphs = split_paragraph(paragraph, max_word)
                for sub_paragraph in sub_paragraphs:
                    texts.append({"text": sub_paragraph, "origin": sub_paragraph, "complete": False,
                                  "sub": True})
            else:
                texts.append(
                    {"text": paragraph, "origin": paragraph, "complete": False, "sub": False})

    # print(texts)
    max_run = max_threads if len(texts) > max_threads else len(texts)
    before_active_count = threading.activeCount()
    event = threading.Event()
    while run_index <= len(texts) - 1:
        if threading.activeCount() < max_run + before_active_count:
            if not event.is_set():
                thread = threading.Thread(target=to_translate.get,args=(trans, event, texts, run_index))
                thread.start()
                run_index += 1
            else:
                return False

    while True:
        complete = True
        for text in texts:
            if not text['complete']:
                complete = False
        if complete:
            break
        else:
            time.sleep(1)

    text_count = 0
    # print(texts)
    trans_type = trans['type']
    onlyTransText = False
    if trans_type == "trans_text_only_inherit" or trans_type == "trans_text_only_new" or trans_type == "trans_all_only_new" or trans_type == "trans_all_only_inherit":
        onlyTransText = True

    # 将翻译结果写入新的 TXT 文件
    try:
        with open(trans['target_file'], 'w', encoding='utf-8') as file:
            translated_paragraph = ""
            origin_paragraph = ""
            for item in texts:
                if item["sub"]:
                    translated_paragraph += item["text"]
                    origin_paragraph += item["origin"]
                else:
                    if translated_paragraph != "":
                        if onlyTransText == False:
                            file.write(origin_paragraph + '\n')
                        file.write(translated_paragraph + '\n\n')
                        translated_paragraph = ""
                        origin_paragraph = ""
                    if onlyTransText == False:
                        file.write(item["origin"] + '\n')
                    file.write(item["text"] + '\n\n')

            if translated_paragraph != "":
                if onlyTransText == False:
                    file.write(origin_paragraph + '\n')
                file.write(translated_paragraph + '\n')
    except Exception as e:
        print(f"无法写入文件 {trans['target_file']}: {e}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    to_translate.complete(trans, text_count, spend_time)
    return True


def split_paragraph(paragraph, max_length):
    """将段落分割成多个部分，每部分不超过 max_length 字符，并考虑断句"""
    sentences = re.split(r'(?<=[.!?。！？]) +|(?<=[。！？])\s*', paragraph)  # 按句子分割
    current_length = 0
    current_part = []
    parts = []

    for sentence in sentences:
        if current_length + len(sentence) > max_length:
            # 如果当前部分长度加上句子长度超过最大长度，保存当前部分
            parts.append(' '.join(current_part))
            current_part = [sentence]  # 开始新的部分
            current_length = len(sentence)
        else:
            current_part.append(sentence)
            current_length += len(sentence)

    # 添加最后一部分
    if current_part:
        parts.append(' '.join(current_part))

    return parts


def check_text(text):
    return text != None and len(text) > 0 and not common.is_all_punc(text)
