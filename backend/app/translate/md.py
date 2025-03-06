import os
import threading
from . import to_translate
from . import common
import datetime
import time
import re

def start(trans):
    # 允许的最大线程
    threads=trans['threads']
    if threads is None or int(threads)<0:
        max_threads=10
    else:
        max_threads=int(threads)
    # 当前执行的索引位置
    run_index=0
    start_time = datetime.datetime.now()

    try:
        with open(trans['file_path'], 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"无法读取文件 {trans['file_path']}: {e}")
        return False

    trans_type=trans['type']
    keepBoth=True
    if trans_type=="trans_text_only_inherit" or trans_type=="trans_text_only_new" or trans_type=="trans_all_only_new" or trans_type=="trans_all_only_inherit":
        keepBoth=False

    # 按段落分割内容，始终使用换行符分隔
    paragraphs = content.split('\n')  # 假设段落之间用换行符分隔
    # 支持最多单词量
    max_word = 1000
    texts = []
    current_text = ""  # 用于累加当前段落

    for paragraph in paragraphs:
        if check_text(paragraph) or paragraph.strip() == "":  # 检查段落是否有效或为空
            # if paragraph.strip() == "":
            #     # 如果是空行，直接加入到 texts
            #     texts.append({"text": "", "origin": "", "complete": True, "sub": False, "ext":"md"})
            #     continue  # 跳过后续处理，继续下一个段落

            if keepBoth:
                # 当 keepBoth 为 True 时，不累加 current_text
                if len(paragraph) > max_word:
                    # 如果段落长度超过 max_word，进行拆分
                    sub_paragraphs = split_paragraph(paragraph, max_word)
                    for sub_paragraph in sub_paragraphs:
                        # 直接将分段的内容追加到 texts
                        append_text(sub_paragraph, texts, True)
                else:
                    # 如果段落长度不超过 max_word，直接加入 texts
                    append_text(paragraph, texts, False)
            else:
                # 当 keepBoth 为 False 时，处理 current_text 的逻辑
                if len(paragraph) > max_word:
                    # 如果当前累加的文本不为空，先将其追加到 texts
                    if current_text:
                        append_text(current_text, texts, False)
                        current_text = ""  # 重置当前文本

                    # 分割段落并追加到 texts
                    sub_paragraphs = split_paragraph(paragraph, max_word)
                    for sub_paragraph in sub_paragraphs:
                        # 直接将分段的内容追加到 texts
                        append_text(sub_paragraph, texts, True)
                else:
                    # 在追加之前判断是否超出 max_word
                    if len(current_text) + len(paragraph) > max_word:  # 不再加1，因为我们要保留原有换行符
                        # 如果超出 max_word，将 current_text 追加到 texts
                        append_text(current_text, texts, False)
                        current_text = ""  # 重置当前文本

                    # 追加段落（保留原有换行符）
                    current_text += paragraph+"\n" # 直接追加段落，并加上换行符

    # 在循环结束后，如果还有累加的文本，追加到 texts
    append_text(current_text, texts, False)
    # print(texts);
    # exit()
    max_run=max_threads if len(texts)>max_threads else len(texts)
    before_active_count=threading.activeCount()
    event=threading.Event()
    while run_index<=len(texts)-1:
        if threading.activeCount()<max_run+before_active_count:
            if not event.is_set():
                thread = threading.Thread(target=to_translate.get, args=(trans, event, texts, run_index))
                thread.start()
                run_index+=1
            else:
                return False
    
    while True:
        complete=True
        for text in texts:
            if not text['complete']:
                complete=False
        if complete:
            break
        else:
            time.sleep(1)

    text_count=0
    # print(texts)
    # 将翻译结果写入新的 TXT 文件
    try:
        with open(trans['target_file'], 'w', encoding='utf-8') as file:
            translated_paragraph=""
            origin_paragraph=""
            for item in texts:
                if item["sub"]:
                    translated_paragraph+=item["text"]
                    origin_paragraph+=item["origin"]
                else:
                    if translated_paragraph!="":
                        if keepBoth:
                            file.write(origin_paragraph+'\n')
                        file.write(translated_paragraph+'\n')
                        translated_paragraph=""
                        origin_paragraph=""
                    if keepBoth and item["origin"].strip() != "":
                        file.write(item["origin"] + '\n')
                    file.write(item["text"] + '\n')

            if translated_paragraph!="":
                if keepBoth and item["origin"].strip() != "":
                    file.write(origin_paragraph+'\n')
                file.write(translated_paragraph+'\n')
    except Exception as e:
        print(f"无法写入文件 {target_file_path}: {e}")
        return False

    end_time = datetime.datetime.now()
    spend_time=common.display_spend(start_time, end_time)
    to_translate.complete(trans, text_count, spend_time)
    return True

def split_paragraph(paragraph, max_length):
    """将段落分割成多个部分，每部分不超过 max_length 字符，并考虑断"""
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

def append_text(text, texts, sub=False):
    if check_text(text):
        texts.append({"text": text, "origin": text, "complete": False, "sub": sub, "ext":"md"})
    else:
        texts.append({"text": "", "origin": "", "complete": True, "sub": sub, "ext":"md"})

def check_text(text):
    return text!=None and text!="\n" and len(text)>0 and not common.is_all_punc(text) 
