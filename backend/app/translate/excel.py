import threading
import openpyxl
from . import to_translate
from . import common
import os
import sys
import time
import datetime

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
    wb = openpyxl.load_workbook(trans['file_path']) 
    sheets = wb.get_sheet_names()
    texts=[]
    for sheet in sheets:
        ws = wb.get_sheet_by_name(sheet)
        read_row(ws.rows, texts)
        
    # print(texts)
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
    for sheet in sheets:
        ws = wb.get_sheet_by_name(sheet)
        text_count+=write_row(ws.rows, texts)

    wb.save(trans['target_file'])
    end_time = datetime.datetime.now()
    spend_time=common.display_spend(start_time, end_time)
    to_translate.complete(trans,text_count,spend_time)
    return True


def read_row(rows,texts):
    for row in rows:
        text=""
        for cell in row:
            value=cell.value
            if value!=None and not common.is_all_punc(value):
                texts.append({"text":value, "complete":False})
        #         if text=="":
        #             text=value
        #         else:
        #             text=text+"\n"+value
        # if text!=None and not common.is_all_punc(text):
        #     texts.append({"text":text, "complete":False})

def write_row(rows, texts):
    text_count=0
    for row in rows:
        text=""
        for cell in row:
            value=cell.value
            if value!=None and not common.is_all_punc(value) and len(texts)>0:
                item=texts.pop(0)
                text_count+=item['count']
                cell.value=item['text']
        #         if text=="":
        #             text=value
        #         else:
        #             text=text+"\n"+value
        # if text!=None and not common.is_all_punc(text):
        #     item=texts.pop(0)
        #     values=item['text'].split("\n")
        #     text_count+=item['count']
        #     for cell in row:
        #         value=cell.value
        #         if value!=None and not common.is_all_punc(value):
        #             if len(values)>0:
        #                 cell.value=values.pop(0)
    return text_count



