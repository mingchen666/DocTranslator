# translate/common.py
import string
import uuid
import datetime
import os
import platform
import subprocess
from typing import Union

# 线程控制常量
MIN_THREADS = 1
MAX_THREADS = 10
DEFAULT_THREADS = 5


def is_all_punc(strings) -> bool:
    """
    判断字符串是否全部由标点符号、数字、空白组成
    """
    if strings is None:
        return True
    if isinstance(strings, (datetime.time, datetime.datetime)):
        return True
    if isinstance(strings, (int, float, complex)):
        return True

    chinese_punctuations = get_chinese_punctuation()

    for s in str(strings):
        if (s not in string.punctuation and
                not s.isdigit() and
                not s.isdecimal() and
                s != "" and
                not s.isspace() and
                s not in chinese_punctuations):
            return False
    return True


def is_chinese(char: str) -> bool:
    """判断字符是否为中文"""
    if len(char) != 1:
        return False
    return '\u4e00' <= char <= '\u9fff'


def get_chinese_punctuation() -> list:
    """获取中文标点符号列表"""
    return ['：', '【', '】', '，', '。', '、', '？', '」', '「',
            '；', '！', '@', '￥', '（', '）', '"', '"', ''', ''',
            '《', '》', '—', '…', '·']


def display_spend(start_time: datetime.datetime, end_time: datetime.datetime) -> str:
    """
    格式化显示耗时
    """
    left_time = end_time - start_time
    days = left_time.days
    hours, remainder = divmod(left_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    spend = "用时"
    if days > 0:
        spend += f"{days}天"
    if hours > 0:
        spend += f"{hours}小时"
    if minutes > 0:
        spend += f"{minutes}分钟"
    if seconds > 0 or spend == "用时":
        spend += f"{seconds}秒"

    return spend


def random_uuid(length: int = 8) -> str:
    """生成随机UUID"""
    result = str(uuid.uuid4()).replace('-', '')[:length]
    return result


def find_command_location(command: str) -> str:
    """查找命令的安装位置"""
    if platform.system() == 'Windows':
        cmd = 'where'
    else:
        cmd = 'which'

    try:
        location = subprocess.check_output([cmd, command]).strip()
        return location.decode('utf-8')
    except subprocess.CalledProcessError as e:
        raise Exception(f"未安装{command}")


def format_file_path(filepath: str) -> str:
    """格式化文件路径（处理空格等特殊字符）"""
    filename = os.path.basename(filepath)
    filename = filename.replace(" ", r"\ ").replace("/", "\\")
    parentpath = os.path.dirname(filepath)
    return f"{parentpath}/{filename}"


def convert_language_name_to_code(language_name: str) -> str:
    """将中文语言名称转换为标准语言代码"""
    language_mapping = {
        '中文': 'zh',
        '英语': 'en',
        '英文': 'en',
        '日语': 'ja',
        '日文': 'ja',
        '法语': 'fr',
        '法文': 'fr',
        '德语': 'de',
        '德文': 'de',
        '俄语': 'ru',
        '俄文': 'ru',
        '西班牙语': 'es',
        '西班牙文': 'es',
        '韩语': 'ko',
        '韩文': 'ko',
        '阿拉伯语': 'ar',
        '葡萄牙语': 'pt',
        '意大利语': 'it'
    }
    return language_mapping.get(language_name, 'en')


def parse_threads(threads_config: Union[int, str, None]) -> int:
    """
    安全解析线程数配置
    :param threads_config: 可能是 int, str, None
    :return: 有效的线程数 (1-10)
    """
    try:
        # 处理 None
        if threads_config is None:
            return DEFAULT_THREADS

        # 处理字符串
        if isinstance(threads_config, str):
            threads_config = threads_config.strip()
            if not threads_config:
                return DEFAULT_THREADS
            threads = int(threads_config)
        else:
            threads = int(threads_config)

        # 边界检查
        if threads < MIN_THREADS:
            return MIN_THREADS
        if threads > MAX_THREADS:
            return MAX_THREADS

        return threads

    except (ValueError, TypeError):
        return DEFAULT_THREADS


def count_words(text: str) -> int:
    """
    统计文本字数
    中文按字计数，英文按0.5计数
    """
    if not text:
        return 0

    count = 0
    for char in text:
        if is_chinese(char):
            count += 1
        elif char and char.strip():
            count += 0.5

    return int(count)


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名
    移除或替换不安全的字符
    """
    # 不安全字符
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename


def ensure_dir(dir_path: str) -> bool:
    """
    确保目录存在
    :return: 是否成功
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception:
        return False


def get_file_extension(filepath: str) -> str:
    """获取文件扩展名（小写）"""
    return os.path.splitext(filepath)[1].lower()


def is_supported_file(filepath: str) -> bool:
    """判断是否为支持的文件类型"""
    supported_extensions = [
        '.docx', '.doc',
        '.xlsx', '.xls',
        '.pptx', '.ppt',
        '.pdf',
        '.txt',
        '.csv',
        '.md',
        '.html', '.htm'
    ]
    ext = get_file_extension(filepath)
    return ext in supported_extensions
