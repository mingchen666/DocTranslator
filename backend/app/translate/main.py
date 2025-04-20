import threading
import openai
import os
import sys
import time
import getopt
from . import to_translate
from . import word
import excel
import powerpoint
import pdf
import gptpdf
import txt
import csv_handle
import md
import pymysql
import db
from . import common
import traceback
from . import rediscon

# 当前正在执行的线程
run_threads=0

def main():
    global run_threads
    # 允许的最大线程
    max_threads=10
    # 当前执行的索引位置
    run_index=0
    # 是否保留原文
    keep_original=False
    # 要翻译的文件路径
    file_path=''
    # 翻译后的目标文件路径
    target_file=''
    uuid=sys.argv[1]
    storage_path=sys.argv[2]
    trans=db.get("select * from translate where uuid=%s", uuid)
    translate_id=trans['id']
    origin_filename=trans['origin_filename']
    origin_filepath=trans['origin_filepath']
    target_filepath=trans['target_filepath']
    api_key=trans['api_key']
    api_url=trans['api_url']
    comparison=get_comparison(trans['comparison_id'])
    prompt=get_prompt(trans['prompt_id'], comparison)
    if comparison:
        prompt = (
            "术语对照表:\n"
            f"{comparison}\n"
            "请按照以下规则进行翻译：\n"
            "1. 遇到术语时，请使用术语对照表中的对应翻译，无论翻译成什么语言。\n"
            "2. 未在术语对照表中的文本，请遵循翻译说明进行翻译。\n"
            "3. 确保翻译结果不包含原文或任何解释。\n"
            "翻译说明:\n"
            f"{prompt}"
        )
    trans['prompt']=prompt
    
    file_path=storage_path+origin_filepath
    target_file=storage_path+target_filepath

    origin_path_dir=os.path.dirname(file_path)
    target_path_dir=os.path.dirname(target_file)
    
    if not os.path.exists(origin_path_dir):
        os.makedirs(origin_path_dir, mode=0o777, exist_ok=True)

    if not os.path.exists(target_path_dir):
        os.makedirs(target_path_dir, mode=0o777, exist_ok=True)

    trans['file_path']=file_path
    trans['target_file']=target_file
    trans['storage_path']=storage_path
    trans['target_path_dir']=target_path_dir
    extension = origin_filename[origin_filename.rfind('.'):]
    trans['extension']=extension
    trans['run_complete']=True
    item_count=0
    spend_time=''
    try:
        status=True
        # 设置OpenAI API
        to_translate.init_openai(api_url, api_key)
        if extension=='.docx' or extension == '.doc':
            status=word.start(trans)
        elif extension=='.xls' or extension == '.xlsx':
            status=excel.start(trans)
        elif extension=='.ppt' or extension == '.pptx':
            status=powerpoint.start(trans)
        elif extension == '.pdf':
            if pdf.is_scanned_pdf(trans['file_path']):
                status=gptpdf.start(trans)
            else:
                status=pdf.start(trans)
        elif extension == '.txt':
            status=txt.start(trans)
        elif extension == '.csv':
            status=csv_handle.start(trans)
        elif extension == '.md':
            status=md.start(trans)
        if status:
            print("success")
            #before_active_count=threading.activeCount()
            #mredis.decr(api_url,threading_num-before_active_count)
            # print(item_count + ";" + spend_time)
        else:
            #before_active_count=threading.activeCount()
            #mredis.decr(api_url,threading_num-before_active_count)
            print("翻译出错了")
    except Exception as e:
        to_translate.error(translate_id, str(e))
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = exc_traceback.tb_lineno  # 异常抛出的具体行号
        print(f"Error occurred on line: {line_number}")
        #before_active_count=threading.activeCount()
        #mredis.set(api_url,threading_num-before_active_count)
        print(e)

def get_prompt(prompt_id, comparison):
    if prompt_id>0:
        prompt=db.get("select content from prompt where id=%s and deleted_flag='N'", prompt_id)
        if prompt and len(prompt['content'])>0:
            return prompt['content']

    prompt=db.get("select value from setting where `group`='other_setting' and alias='prompt'")
    return prompt['value']

def get_comparison(comparison_id):
    if comparison_id>0:
        comparison=db.get("select content from comparison where id=%s and deleted_flag='N'", comparison_id)
        if comparison and len(comparison['content'])>0:
            return comparison['content'].replace(',',':').replace(';','\n');

if __name__ == '__main__':
    main()


