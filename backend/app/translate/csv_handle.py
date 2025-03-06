import os
import threading
from . import to_translate
from . import common
import datetime
import time
import csv
import io

def start(trans):
    # 允许的最大线程
    threads = trans.get('threads')
    max_threads = 10 if threads is None or int(threads) < 0 else int(threads)

    # 当前执行的索引位置
    run_index = 0
    start_time = datetime.datetime.now()

    encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1']
    content = None

    for encoding in encodings:
        try:
            with open(trans['file_path'], 'r', encoding=encoding, newline='') as file:
                reader = csv.reader(file)
                content = list(reader)
            break  # 如果成功读取，跳出循环
        except UnicodeDecodeError:
            continue  # 如果解码失败，尝试下一种编码
        except Exception as e:
            print(f"无法读取CSV文件 {trans['file_path']}: {e}")
            return False

    if content is None:
        print(f"无法以任何支持的编码格式读取CSV文件 {trans['file_path']}")
        return False

    texts = []

    # 支持最多单词量
    max_word = 1000

    # 处理每一行CSV数据
    for row in content:
        for cell in row:
            if check_text(cell):
                if len(cell) > max_word:
                    sub_cells = split_cell(cell, max_word)
                    for sub_cell in sub_cells:
                        texts.append({"text": sub_cell, "origin": sub_cell, "complete": False, "sub": True})
                else:
                    texts.append({"text": cell, "origin": cell, "complete": False, "sub": False})


    max_run = min(max_threads, len(texts))
    before_active_count = threading.activeCount()
    event = threading.Event()

    while run_index <= len(texts) - 1:
        if threading.activeCount() < max_run + before_active_count:
            if not event.is_set():
                thread = threading.Thread(target=translate.get, args=(trans, event, texts, run_index))
                thread.start()
                run_index += 1
            else:
                return False

    while True:
        if all(text['complete'] for text in texts):
            break
        else:
            time.sleep(1)

    text_count = len(texts)
    trans_type = trans['type']
    only_trans_text = trans_type in ["trans_text_only_inherit", "trans_text_only_new", "trans_all_only_new", "trans_all_only_inherit"]

    # 将翻译结果写入新的 CSV 文件
    try:
        with open(trans['target_file'], 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            translated_row = []
            origin_row = []
            text_index = 0

            for row in content:
                for cell in row:
                    if check_text(cell):
                        translated_cell = ""
                        while text_index < len(texts) and texts[text_index]['origin'] == cell:
                            translated_cell += texts[text_index]['text']
                            text_index += 1
                        translated_row.append(translated_cell)
                        origin_row.append(cell)
                    else:
                        translated_row.append(cell)
                        origin_row.append(cell)

                if only_trans_text:
                    writer.writerow(translated_row)
                else:
                    writer.writerow(origin_row)
                    writer.writerow(translated_row)

                translated_row = []
                origin_row = []

    except Exception as e:
        print(f"无法写入CSV文件 {trans['target_file']}: {e}")
        return False

    end_time = datetime.datetime.now()
    spend_time = common.display_spend(start_time, end_time)
    to_translate.complete(trans, text_count, spend_time)
    return True

def split_cell(cell, max_length):
    """将单元格内容分割成多个部分，每部分不超过 max_length 字符"""
    parts = []
    current_part = ""

    words = cell.split()
    for word in words:
        if len(current_part) + len(word) + 1 > max_length:
            parts.append(current_part.strip())
            current_part = word
        else:
            current_part += " " + word if current_part else word

    if current_part:
        parts.append(current_part.strip())

    return parts

def check_text(text):
    return text is not None and len(text) > 0 and not common.is_all_punc(text)
