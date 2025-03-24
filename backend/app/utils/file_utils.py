# utils/file_utils.py
import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from pathlib import Path
from datetime import datetime
from flask import current_app

import os
import hashlib
from pathlib import Path
from datetime import datetime
from flask import current_app


class FileManager:
    @staticmethod
    def get_upload_dir():
        """
        获取上传文件存储目录[^1]
        :return: 上传文件存储目录的绝对路径
        """
        base_dir = Path(current_app.config['UPLOAD_BASE_DIR'])
        date_str = datetime.now().strftime('%Y-%m-%d')
        upload_dir = base_dir / 'uploads' / date_str
        upload_dir.mkdir(parents=True, exist_ok=True)
        return str(upload_dir)

    @staticmethod
    def generate_filename(filename):
        """
        生成唯一的文件名[^3]
        :param filename: 原始文件名
        :return: 唯一的文件名
        """
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{name}_{timestamp}{ext}"

    @staticmethod
    def get_relative_path(full_path):
        """
        获取相对于存储根目录的相对路径[^4]
        :param full_path: 文件的绝对路径
        :return: 相对路径
        """
        base_dir = Path(current_app.config['UPLOAD_BASE_DIR'])
        return str(Path(full_path).relative_to(base_dir)).replace('\\', '/')

    @staticmethod
    def exists(file_path):
        """
        检查文件是否存在[^5]
        :param file_path: 文件的相对路径或绝对路径
        :return: 文件是否存在 (True/False)
        """
        if not file_path:
            return False
        full_path = os.path.join(current_app.config['UPLOAD_BASE_DIR'], file_path.lstrip('/'))
        return os.path.exists(full_path)

    @staticmethod
    def calculate_md5(file_path):
        """
        计算文件的 MD5 值[^6]
        :param file_path: 文件的绝对路径
        :return: 文件的 MD5 值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def allowed_file(filename):
        """
        验证文件类型是否允许[^7]
        :param filename: 文件名
        :return: 文件类型是否允许 (True/False)
        """
        ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'pptx', 'pdf', 'txt', 'md', 'csv', 'xls', 'doc'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file_size(file_stream):
        """
        验证文件大小是否超过限制[^8]
        :param file_stream: 文件流
        :return: 文件大小是否合法 (True/False)
        """
        MAX_FILE_SIZE = current_app.config['MAX_FILE_SIZE']# 10 * 1024 * 1024  # 10MB
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        return file_size <= MAX_FILE_SIZE

    @staticmethod
    def get_translate_absolute_path(filename):
        """
        获取翻译结果的绝对路径（保持原文件名）[^2]
        :param filename: 原始文件名
        :return: 翻译结果的绝对路径
        """
        base_dir = Path(current_app.config['UPLOAD_BASE_DIR'])
        date_str = datetime.now().strftime('%Y-%m-%d')
        translate_dir = base_dir / 'translate' / date_str
        translate_dir.mkdir(parents=True, exist_ok=True)
        return str(translate_dir / filename)





def get_upload_dir():
    """获取按日期分类的上传目录"""
    # 获取项目根目录，并再上一级到所需目录
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    print(base_dir)
    upload_dir = os.path.join(base_dir, 'uploads', datetime.now().strftime('%Y-%m-%d'))

    # 如果目录不存在则创建
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir
