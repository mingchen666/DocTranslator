# import tiktoken
import datetime
import hashlib
import logging
import os
import sys
import re
import openai
from . import common
from . import db
import time


def get(trans, event, texts, index):
    if event.is_set():
        exit(0)
    threads = trans['threads']
    if threads is None or threads == "" or int(threads) < 0:
        max_threads = 10
    else:
        max_threads = int(threads)
    # mredis=rediscon.get_conn()
    # threading_num=get_threading_num(mredis)
    # while threading_num>=max_threads:
    #    time.sleep(1)
    # print('trans配置项', trans)
    translate_id = trans['id']
    target_lang = trans['lang']
    model = trans['model']
    backup_model = trans['backup_model']
    prompt = trans['prompt']
    extension = trans['extension'].lower()
    text = texts[index]
    api_key = trans['api_key']
    api_url = trans['api_url']
    old_text = text['text']
    md5_key = md5_encryption(
        str(api_key) + str(api_url) + str(old_text) + str(prompt) + str(backup_model) + str(
            model) + str(target_lang))
    try:
        oldtrans = db.get("select * from translate_logs where md5_key=%s", md5_key)
        # mredis.set("threading_count",threading_num+1)
        if text['complete'] == False:
            content = ''
            if oldtrans:
                content = oldtrans['content']
                # 特别处理PDF类型
            # elif extension == ".pdf":
            #     return handle_pdf(trans, event, texts, index)
            # elif extension == ".pdf":
            #     if text['type'] == "text":
            #         content = translate_html(text['text'], target_lang, model, prompt)
            #         time.sleep(0.1)
            #     else:
            #         content = get_content_by_image(text['text'], target_lang)
            #         time.sleep(0.1)
            # ---------------这里实现不同模型格式的请求--------------
            elif extension == ".md":
                content = req(text['text'], target_lang, model, prompt, True)
            else:
                content = req(text['text'], target_lang, model, prompt, False)
                # print("content", text['content'])
            text['count'] = count_text(text['text'])
            if check_translated(content):
                # 过滤deepseek思考过程
                text['text'] = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                if oldtrans is None:
                    db.execute("INSERT INTO translate_logs set api_url=%s,api_key=%s,"
                               + "backup_model=%s ,created_at=%s ,prompt=%s,  "
                               + "model=%s,target_lang=%s,source=%s,content=%s,md5_key=%s",
                               str(api_url), str(api_key),
                               str(backup_model),
                               datetime.datetime.now(), str(prompt), str(model), str(target_lang),
                               str(old_text),
                               str(content), str(md5_key))
            text['complete'] = True
    except openai.AuthenticationError as e:
        # set_threading_num(mredis)
        return use_backup_model(trans, event, texts, index, "openai密钥或令牌无效")
    except openai.APIConnectionError as e:
        # set_threading_num(mredis)
        return use_backup_model(trans, event, texts, index, "请求无法与openai服务器或建立安全连接")
    except openai.PermissionDeniedError as e:
        # set_threading_num(mredis)
        texts[index] = text
        # return use_backup_model(trans, event, texts, index, "令牌额度不足")
    except openai.RateLimitError as e:
        # set_threading_num(mredis)
        if "retry" not in text:
            trans['model'] = backup_model
            trans['backup_model'] = model
            time.sleep(1)
            print("访问速率达到限制,交换备用模型与模型重新重试")
            get(trans, event, texts, index)
        else:
            return use_backup_model(trans, event, texts, index,
                                    "访问速率达到限制,10分钟后再试" + str(text['text']))
    except openai.InternalServerError as e:
        # set_threading_num(mredis)
        if "retry" not in text:
            trans['model'] = backup_model
            trans['backup_model'] = model
            time.sleep(1)
            print("当前分组上游负载已饱和，交换备用模型与模型重新重试")
            get(trans, event, texts, index)
        else:
            return use_backup_model(trans, event, texts, index,
                                    "当前分组上游负载已饱和，请稍后再试" + str(text['text']))
    except openai.APIStatusError as e:
        # set_threading_num(mredis)
        return use_backup_model(trans, event, texts, index, e.response)
    except Exception as e:
        # set_threading_num(mredis)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = exc_traceback.tb_lineno  # 异常抛出的具体行号
        print(f"Error occurred on line: {line_number}")
        print(e)
        if "retry" not in text:
            text["retry"] = 0
        text["retry"] += 1
        if text["retry"] <= 3:
            trans['model'] = backup_model
            trans['backup_model'] = model
            print("当前模型执行异常，交换备用模型与模型重新重试")
            time.sleep(1)
            get(trans, event, texts, index)
            return
        else:
            text['complete'] = True
        # traceback.print_exc()
        # print("translate error")
    texts[index] = text
    # print(text)
    if not event.is_set():
        process(texts, translate_id)
    # set_threading_num(mredis)
    exit(0)


def handle_pdf(trans, event, texts, index):
    try:
        from . import pdf_parser
        success = pdf_parser.start(trans)
        if success:
            texts[index]['complete'] = True
        else:
            return use_backup_model(trans, event, texts, index, "PDF解析失败")
    except Exception as e:
        return use_backup_model(trans, event, texts, index, str(e))


def get11(trans, event, texts, index):
    if event.is_set():
        exit(0)
    threads = trans['threads']
    if threads is None or threads == "" or int(threads) < 0:
        max_threads = 10
    else:
        max_threads = int(threads)
    # mredis=rediscon.get_conn()
    # threading_num=get_threading_num(mredis)
    # while threading_num>=max_threads:
    #    time.sleep(1)
    print('trans配置项', trans)
    translate_id = trans['id']
    target_lang = trans['lang']
    model = trans['model']
    backup_model = trans['backup_model']
    prompt = trans['prompt']
    extension = trans['extension'].lower()
    text = texts[index]
    api_key = trans['api_key']
    api_url = trans['api_url']
    old_text = text['text']
    md5_key = md5_encryption(
        str(api_key) + str(api_url) + str(old_text) + str(prompt) + str(backup_model) + str(
            model) + str(target_lang))
    try:
        oldtrans = db.get("select * from translate_logs where md5_key=%s", md5_key)
        # mredis.set("threading_count",threading_num+1)
        if text['complete'] == False:
            content = ''
            if oldtrans:
                content = oldtrans['content']
            elif extension == ".pdf":
                if text['type'] == "text":
                    content = translate_html(text['text'], target_lang, model, prompt)
                    time.sleep(0.1)
                else:
                    content = get_content_by_image(text['text'], target_lang)
                    time.sleep(0.1)
            # ---------------这里实现不同模型格式的请求--------------
            elif extension == ".md":
                content = req(text['text'], target_lang, model, prompt, True)
            else:
                content = req(text['text'], target_lang, model, prompt, False)
                # print("content", text['content'])
            text['count'] = count_text(text['text'])
            if check_translated(content):
                # 过滤deepseek思考过程
                text['text'] = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                if oldtrans is None:
                    db.execute("INSERT INTO translate_logs set api_url=%s,api_key=%s,"
                               + "backup_model=%s ,created_at=%s ,prompt=%s,  "
                               + "model=%s,target_lang=%s,source=%s,content=%s,md5_key=%s",
                               str(api_url), str(api_key),
                               str(backup_model),
                               datetime.datetime.now(), str(prompt), str(model), str(target_lang),
                               str(old_text),
                               str(content), str(md5_key))
            text['complete'] = True
    except openai.AuthenticationError as e:
        # set_threading_num(mredis)
        return use_backup_model(trans, event, texts, index, "openai密钥或令牌无效")
    except openai.APIConnectionError as e:
        # set_threading_num(mredis)
        return use_backup_model(trans, event, texts, index, "请求无法与openai服务器或建立安全连接")
    except openai.PermissionDeniedError as e:
        # set_threading_num(mredis)
        texts[index] = text
        # return use_backup_model(trans, event, texts, index, "令牌额度不足")
    except openai.RateLimitError as e:
        # set_threading_num(mredis)
        if "retry" not in text:
            trans['model'] = backup_model
            trans['backup_model'] = model
            time.sleep(1)
            print("访问速率达到限制,交换备用模型与模型重新重试")
            get(trans, event, texts, index)
        else:
            return use_backup_model(trans, event, texts, index,
                                    "访问速率达到限制,10分钟后再试" + str(text['text']))
    except openai.InternalServerError as e:
        # set_threading_num(mredis)
        if "retry" not in text:
            trans['model'] = backup_model
            trans['backup_model'] = model
            time.sleep(1)
            print("当前分组上游负载已饱和，交换备用模型与模型重新重试")
            get(trans, event, texts, index)
        else:
            return use_backup_model(trans, event, texts, index,
                                    "当前分组上游负载已饱和，请稍后再试" + str(text['text']))
    except openai.APIStatusError as e:
        # set_threading_num(mredis)
        return use_backup_model(trans, event, texts, index, e.response)
    except Exception as e:
        # set_threading_num(mredis)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = exc_traceback.tb_lineno  # 异常抛出的具体行号
        print(f"Error occurred on line: {line_number}")
        print(e)
        if "retry" not in text:
            text["retry"] = 0
        text["retry"] += 1
        if text["retry"] <= 3:
            trans['model'] = backup_model
            trans['backup_model'] = model
            print("当前模型执行异常，交换备用模型与模型重新重试")
            time.sleep(1)
            get(trans, event, texts, index)
            return
        else:
            text['complete'] = True
        # traceback.print_exc()
        # print("translate error")
    texts[index] = text
    # print(text)
    if not event.is_set():
        process(texts, translate_id)
    # set_threading_num(mredis)
    exit(0)


# def get_threading_num(mredis):
#    threading_count=mredis.get("threading_count")
#    if threading_count is None or threading_count=="" or int(threading_count)<0:
#        threading_num=0
#    else:
#        threading_num=int(threading_count)
#    return threading_num
# def set_threading_num(mredis):
#    threading_count=mredis.get("threading_count")
#    if threading_count is None or threading_count=="" or int(threading_count)<1:
#        mredis.set("threading_count",0)
#    else:
#        threading_num=int(threading_count)
#        mredis.set("threading_count",threading_num-1)

def md5_encryption(data):
    md5 = hashlib.md5(data.encode('utf-8'))  # 创建一个md5对象
    return md5.hexdigest()  # 返回加密后的十六进制字符串


def req(text, target_lang, model, prompt, ext):
    # 判断是否是md格式
    if ext == True:
        # 如果是 md 格式，追加提示文本
        prompt += "。 请帮助我翻译以下 Markdown 文件中的内容。请注意，您只需翻译文本部分，而不应更改任何 Markdown 标签或格式。保持原有的标题、列表、代码块、链接和其他 Markdown 标签的完整性。"
    # 构建 message
    message = [
        {"role": "system", "content": prompt.replace("{target_lang}", target_lang)},
        {"role": "user", "content": text}
    ]
    # print(openai.base_url)
    print(message)
    # 禁用 OpenAI 的日志输出
    logging.getLogger("openai").setLevel(logging.WARNING)
    # 禁用 httpx 的日志输出
    logging.getLogger("httpx").setLevel(logging.WARNING)
    response = openai.chat.completions.create(
        model=model,  # 使用GPT-3.5版本
        messages=message,
        temperature=0.8
    )
    # for choices in response.choices:
    #     print(choices.message.content)
    content = response.choices[0].message.content
    # print(content)
    return content


def translate_html(html, target_lang, model, prompt):
    message = [
        {"role": "system",
         "content": "把下面的html翻译成{},只返回翻译后的内容".format(target_lang)},
        {"role": "user", "content": html}
    ]
    # print(openai.base_url)
    response = openai.chat.completions.create(
        model=model,
        messages=message
    )
    # for choices in response.choices:
    #     print(choices.message.content)
    content = response.choices[0].message.content
    return content


def get_content_by_image(base64_image, target_lang):
    # print(image_path)
    # file_object = openai.files.create(file=Path(image_path), purpose="这是一张图片")
    # print(file_object)
    message = [
        {"role": "system", "content": "你是一个图片ORC识别专家"},
        {"role": "user", "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": base64_image
                }
            },
            {
                "type": "text",
                # "text": "读取图片链接并提取其中的文本数据,只返回识别后的数据，将文本翻译成英文,并按照图片中的文字布局返回html。只包含body(不包含body本身)部分",
                # "text": f"提取图片中的所有文字数据，将提取的文本翻译成{target_lang},只返回原始文本和翻译结果",
                "text": f"提取图片中的所有文字数据,将提取的文本翻译成{target_lang},只返回翻译结果",
            }
        ]}
    ]
    # print(message)
    # print(openai.base_url)
    response = openai.chat.completions.create(
        model="gpt-4o",  # 使用GPT-3.5版本
        messages=message
    )
    # for choices in response.choices:
    #     print(choices.message.content)
    content = response.choices[0].message.content
    # return content
    # print(''.join(map(lambda x: f'<p>{x}</p>',content.split("\n"))))
    return ''.join(map(lambda x: f'<p>{x}</p>', content.split("\n")))


def check(model):
    try:
        message = [
            {"role": "system", "content": "你通晓世界所有语言,可以用来从一种语言翻译成另一种语言"},
            {"role": "user", "content": "你现在能翻译吗？"}
        ]
        response = openai.chat.completions.create(
            model=model,
            messages=message
        )
        return "OK"
    except openai.AuthenticationError as e:
        return "openai密钥或令牌无效"
    except openai.APIConnectionError as e:
        return "请求无法与openai服务器或建立安全连接"
    except openai.PermissionDeniedError as e:
        return "令牌额度不足"
    except openai.RateLimitError as e:
        return "访问速率达到限制,10分钟后再试"
    except openai.InternalServerError as e:
        return "当前分组上游负载已饱和，请稍后再试"
    except openai.APIStatusError as e:
        return e.response
    except Exception as e:
        return "当前无法完成翻译"


def process(texts, translate_id):
    total = 0
    complete = 0
    for text in texts:
        total += 1
        if text['complete']:
            complete += 1
    if total != complete:
        if (total != 0):
            process = format((complete / total) * 100, '.1f')
            db.execute("update translate set process=%s where id=%s", str(process), translate_id)


def complete(trans, text_count, spend_time):
    target_filesize = 1 #os.stat(trans['target_file']).st_size
    db.execute(
        "update translate set status='done',end_at=now(),process=100,target_filesize=%s,word_count=%s where id=%s",
        target_filesize, text_count, trans['id'])


def error(translate_id, message):
    db.execute(
        "update translate set failed_count=failed_count+1,status='failed',end_at=now(),failed_reason=%s where id=%s",
        message, translate_id)


def count_text(text):
    count = 0
    for char in text:
        if common.is_chinese(char):
            count += 1;
        elif char is None or char == " ":
            continue
        else:
            count += 0.5
    return count


def init_openai(url, key):
    openai.api_key = key
    if "v1" not in url:
        if url[-1] == "/":
            url += "v1/"
        else:
            url += "/v1/"
    openai.base_url = url


def check_translated(content):
    if content.startswith("Sorry, I cannot") or content.startswith(
            "I am sorry,") or content.startswith(
            "I'm sorry,") or content.startswith("Sorry, I can't") or content.startswith(
        "Sorry, I need more") or content.startswith("抱歉，无法") or content.startswith(
        "错误：提供的文本") or content.startswith("无法翻译") or content.startswith(
        "抱歉，我无法") or content.startswith(
        "对不起，我无法") or content.startswith("ご指示の内容は") or content.startswith(
        "申し訳ございません") or content.startswith("Простите，") or content.startswith(
        "Извините,") or content.startswith("Lo siento,"):
        return False
    else:
        return True


# def get_model_tokens(model,content):
#     encoding=tiktoken.encoding_for_model(model)
#     return en(encoding.encode(content))

def use_backup_model(trans, event, texts, index, message):
    if trans['backup_model'] != None and trans['backup_model'] != "":
        trans['model'] = trans['backup_model']
        trans['backup_model'] = ""
        get(trans, event, texts, index)
    else:
        if not event.is_set():
            error(trans['id'], message)
            print(message)
        event.set()
