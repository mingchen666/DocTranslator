import string
import uuid
import datetime
import os
import platform
import subprocess
from pathlib import Path

def is_all_punc(strings):
    if isinstance(strings, datetime.time):
        return True
    elif isinstance(strings, datetime.datetime):
        return True
    elif isinstance(strings, (int, float, complex)):
        return True
    # print(type(strings))
    chinese_punctuations=get_chinese_punctuation()
    for s in strings:
        if s not in string.punctuation and not s.isdigit() and not s.isdecimal() and s != "" and not s.isspace() and s not in chinese_punctuations:
            return False
    return True

def is_chinese(char):
    if '\u4e00' <= char <= '\u9fff':
        return True
    return False

def get_chinese_punctuation():
    return ['：','【','】','，','。','、','？','」','「','；','！','@','￥','（','）']

def display_spend(start_time,end_time):
    left_time = end_time - start_time
    days = left_time.days
    hours, remainder = divmod(left_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    spend="用时"
    if days>0:
        spend+="{}天".format(days)
    if hours>0:
        spend+="{}小时".format(hours)
    if minutes>0:
        spend+="{}分钟".format(minutes)
    if seconds>0:
        spend+="{}秒".format(seconds)
    return spend

def random_uuid(length):
    result = str(uuid.uuid4())[:length]
    return result


def find_command_location(command):
    if platform.system() == 'Windows':
        cmd = 'where'
    else:
        cmd = 'which'
    try:
        print(command)
        location = subprocess.check_output([cmd, command]).strip()
        print(location.decode("utf-8"))
        return location.decode('utf-8')  # 解码为字符串
    except subprocess.CalledProcessError as e:
        print(e)
        raise Exception("未安装"+command)

def format_file_path(filepath):
    filename=os.path.basename(filepath)
    filename=filename.replace(" ",r"\ ").replace("/","\\");
    parentpath=os.path.dirname(filepath)
    return "{}/{}".format(parentpath, filename)
