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
        MAX_FILE_SIZE = current_app.config['MAX_FILE_SIZE']#10 * 1024 * 1024  # 10MB
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




class FileManager11:
    @staticmethod
    def allowed_file(filename):
        """验证文件类型是否允许[^1]"""
        ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'pptx', 'pdf', 'txt', 'md', 'csv', 'xls', 'doc'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file_size(file_stream):
        """验证文件大小是否超过限制[^2]"""
        MAX_FILE_SIZE =current_app.config['MAX_FILE_SIZE'] #10 * 1024 * 1024  # 10MB
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        return file_size <= MAX_FILE_SIZE

    @staticmethod
    def get_upload_dir():
        """获取基于配置的上传目录"""
        upload_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            datetime.now().strftime('%Y-%m-%d')
        )

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        return upload_dir

    def get_upload_dir1111(self):
        """获取按日期分类的上传目录"""
        # 获取项目根目录，并再上一级到所需目录
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        print(base_dir)
        upload_dir = os.path.join(base_dir, 'uploads', datetime.now().strftime('%Y-%m-%d'))

        # 如果目录不存在则创建
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        return upload_dir

    @staticmethod
    def generate_filename(filename):
        """生成安全文件名（带随机后缀防冲突）"""
        safe_name = secure_filename(filename)
        name_part, ext_part = os.path.splitext(safe_name)
        random_str = uuid.uuid4().hex[:6]  # 6位随机字符
        return f"{name_part}_{random_str}{ext_part}"

    @staticmethod
    def generate_filename111(filename):
        """生成安全的文件名，如果文件已存在则附加随机字符串[^4]"""
        safe_filename = secure_filename(filename)
        name, ext = os.path.splitext(safe_filename)
        return f"{name}_{str(uuid.uuid4())[:5]}{ext}"

    @staticmethod
    def safe_remove(filepath):
        """安全删除文件"""
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"File {filepath} has been deleted.")
            except Exception as e:
                print(f"Error occurred while deleting file {filepath}: {e}")
        else:
            print(f"File {filepath} does not exist.")

    @staticmethod
    def exists(file_path: str) -> bool:
        """验证文件是否存在并检查路径安全性[^1]
        Args:
            file_path: 文件路径，支持相对路径和绝对路径
        Returns:
            bool: 文件是否存在且路径合法
        """
        try:
            # 标准化路径，防止路径遍历攻击
            normalized_path = Path(file_path).resolve(strict=False)

            # 验证路径是否在允许的目录下
            upload_dir = Path(current_app.config['UPLOAD_FOLDER']).resolve()
            if not normalized_path.is_relative_to(upload_dir):
                return False

            return normalized_path.exists() and normalized_path.is_file()

        except Exception as e:
            current_app.logger.error(f"文件路径验证失败: {str(e)}")
            return False

    @staticmethod
    def get_storage_dir():
        """获取按日期分类的存储目录[^2]"""
        base_dir = Path(current_app.config['STORAGE_FOLDER'])
        storage_dir = base_dir / datetime.now().strftime('%Y-%m-%d')

        if not storage_dir.exists():
            storage_dir.mkdir(parents=True, exist_ok=True)

        return str(storage_dir)

    @staticmethod
    def is_secure_path(file_path: str, base_dir: str) -> bool:
        """验证文件路径是否安全[^3]
        Args:
            file_path: 文件路径
            base_dir: 基准目录
        Returns:
            bool: 路径是否安全
        """
        try:
            normalized_path = Path(file_path).resolve(strict=False)
            base_dir_path = Path(base_dir).resolve()
            return normalized_path.is_relative_to(base_dir_path)
        except Exception as e:
            current_app.logger.error(f"路径安全验证失败: {str(e)}")
            return False

    @staticmethod
    def exists111xin(file_path: str, base_dir: str) -> bool:
        """验证文件是否存在并检查路径安全性[^4]
        Args:
            file_path: 文件路径
            base_dir: 基准目录
        Returns:
            bool: 文件是否存在且路径合法
        """
        if not FileManager.is_secure_path(file_path, base_dir):
            return False

        normalized_path = Path(file_path).resolve(strict=False)
        return normalized_path.exists() and normalized_path.is_file()

    @staticmethod
    def calculate_md5(file_path):
        """计算文件的MD5值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


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
