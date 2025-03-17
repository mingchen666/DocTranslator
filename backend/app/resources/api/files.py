# resources/file.py
import hashlib
import uuid
from werkzeug.utils import secure_filename
import os
from app import db
from app.models.customer import Customer
from app.models.translate import Translate
from app.utils.response import APIResponse
from pathlib import Path
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import request, current_app
from datetime import datetime


class FileUploadResource1(Resource):
    @jwt_required()
    def post(self):
        """文件上传接口"""
        # 验证文件存在性
        if 'file' not in request.files:
            return APIResponse.error('未选择文件', 400)
        file = request.files['file']

        # 验证文件名有效性
        if file.filename == '':
            return APIResponse.error('无效文件名', 400)

        # 验证文件类型
        if not self.allowed_file(file.filename):
            return APIResponse.error(
                f"仅支持以下格式：{', '.join(current_app.config['ALLOWED_EXTENSIONS'])}", 400)

        # 验证文件大小
        file_stream = file.stream
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        
        if file_size > current_app.config['MAX_FILE_SIZE']:
            return APIResponse.error(
                f"文件大小超过{current_app.config['MAX_FILE_SIZE'] // (1024 * 1024)}MB限制", 400)

        # 获取用户存储信息
        user_id = get_jwt_identity()
        customer = Customer.query.get(user_id)

        # 验证存储空间
        if customer.storage + file_size > current_app.config['MAX_USER_STORAGE']:
            return APIResponse.error('存储空间不足', 403)

        try:
            # 生成存储路径
            save_dir = self.get_upload_dir()
            filename = file.filename  # 直接使用原始文件名
            save_path = os.path.join(save_dir, filename)

            # 检查路径是否安全
            if not self.is_safe_path(save_dir, save_path):
                return APIResponse.error('文件名包含非法字符', 400)

            # 保存文件
            file.save(save_path)
            # 更新用户存储空间
            customer.storage += file_size
            db.session.commit()
            # 生成 UUID
            file_uuid = str(uuid.uuid4())
            # 计算文件的 MD5
            file_md5 = self.calculate_md5(save_path)

            # 创建翻译记录
            translate_record = Translate(
                translate_no=f"TRANS{datetime.now().strftime('%Y%m%d%H%M%S')}",
                uuid=file_uuid,
                customer_id=user_id,
                origin_filename=filename,
                origin_filepath=os.path.abspath(save_path),  # 使用绝对路径
                target_filepath='',  # 目标文件路径暂为空
                status='none',  # 初始状态为 none
                origin_filesize=file_size,
                md5=file_md5,
                created_at=datetime.utcnow()
            )
            db.session.add(translate_record)
            db.session.commit()

            # 返回响应，包含文件名、UUID 和翻译记录 ID
            return APIResponse.success({
                'filename': filename,
                'uuid': file_uuid,
                'translate_id': translate_record.id,
                'save_path': os.path.abspath(save_path)  # 返回绝对路径
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"文件上传失败：{str(e)}")
            return APIResponse.error('文件上传失败', 500)

    @staticmethod
    def allowed_file(filename):
        # """验证文件类型是否允许"""# 暂不支持PDF 'pdf',
        ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'pptx', 'txt', 'md', 'csv', 'xls', 'doc', 'pdf'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file_size(file_stream):
        """验证文件大小是否超过限制"""
        MAX_FILE_SIZE = current_app.config['MAX_FILE_SIZE']
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        return file_size <= MAX_FILE_SIZE

    @staticmethod
    def get_upload_dir():
        """获取按日期分类的上传目录"""
        # 获取上传根目录
        base_dir = Path(current_app.config['UPLOAD_BASE_DIR'])
        upload_dir = base_dir / 'uploads' / datetime.now().strftime('%Y-%m-%d')

        # 如果目录不存在则创建
        if not upload_dir.exists():
            upload_dir.mkdir(parents=True, exist_ok=True)

        return str(upload_dir)

    @staticmethod
    def calculate_md5(file_path):
        """计算文件的 MD5 值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def is_safe_path(base_dir, file_path):
        """检查文件路径是否安全，防止路径遍历攻击"""
        base_dir = Path(base_dir).resolve()
        file_path = Path(file_path).resolve()
        return file_path.is_relative_to(base_dir)



class FileUploadResource(Resource):
    @jwt_required()
    def post(self):
        """文件上传接口"""
        # 验证文件存在性
        if 'file' not in request.files:
            return APIResponse.error('未选择文件', 400)
        file = request.files['file']

        # 验证文件名有效性
        if file.filename == '':
            return APIResponse.error('无效文件名', 400)

        # 验证文件类型
        if not self.allowed_file(file.filename):
            return APIResponse.error(
                f"仅支持以下格式：{', '.join(current_app.config['ALLOWED_EXTENSIONS'])}", 400)

        # 验证文件大小
        file_stream = file.stream
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        
        if file_size > current_app.config['MAX_FILE_SIZE']:
            return APIResponse.error(
                f"文件大小超过{current_app.config['MAX_FILE_SIZE'] // (1024 * 1024)}MB限制", 400)

        # 获取用户存储信息
        user_id = get_jwt_identity()
        customer = Customer.query.get(user_id)

        # 验证存储空间
        if customer.storage + file_size > current_app.config['MAX_USER_STORAGE']:
            return APIResponse.error('存储空间不足', 403)

        try:
            # 生成存储路径
            save_dir = Path(self.get_upload_dir())
            filename = file.filename  # 直接使用原始文件名
            save_path = save_dir / filename

            # 检查路径是否安全
            if not self.is_safe_path(save_dir, save_path):
                return APIResponse.error('文件名包含非法字符', 400)

            # 保存文件
            file.save(save_path)
            # 更新用户存储空间
            customer.storage += file_size
            db.session.commit()
            # 生成 UUID
            file_uuid = str(uuid.uuid4())
            # 计算文件的 MD5
            file_md5 = self.calculate_md5(save_path)

            # 创建翻译记录
            translate_record = Translate(
                translate_no=f"TRANS{datetime.now().strftime('%Y%m%d%H%M%S')}",
                uuid=file_uuid,
                customer_id=user_id,
                origin_filename=filename,
                origin_filepath=str(save_path.resolve()),  # 使用绝对路径
                target_filepath='',  # 目标文件路径暂为空
                status='none',  # 初始状态为 none
                origin_filesize=file_size,
                md5=file_md5,
                created_at=datetime.utcnow()
            )
            db.session.add(translate_record)
            db.session.commit()

            # 返回响应，包含文件名、UUID 和翻译记录 ID
            return APIResponse.success({
                'filename': filename,
                'uuid': file_uuid,
                'translate_id': translate_record.id,
                'save_path': str(save_path.resolve())  # 返回绝对路径
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"文件上传失败：{str(e)}")
            return APIResponse.error('文件上传失败', 500)

    @staticmethod
    def allowed_file(filename):
        """验证文件类型是否允许"""
        ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'pptx', 'txt', 'md', 'csv', 'xls', 'doc', 'pdf'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def validate_file_size(file_stream):
        """验证文件大小是否超过限制"""
        MAX_FILE_SIZE = current_app.config['MAX_FILE_SIZE']
        file_stream.seek(0, os.SEEK_END)
        file_size = file_stream.tell()
        file_stream.seek(0)
        return file_size <= MAX_FILE_SIZE

    @staticmethod
    def get_upload_dir():
        """获取按日期分类的上传目录"""
        # 获取上传根目录
        base_dir = Path(current_app.config['UPLOAD_BASE_DIR'])
        upload_dir = base_dir / 'uploads' / datetime.now().strftime('%Y-%m-%d')

        # 如果目录不存在则创建
        if not upload_dir.exists():
            upload_dir.mkdir(parents=True, exist_ok=True)

        return str(upload_dir)

    @staticmethod
    def calculate_md5(file_path):
        """计算文件的 MD5 值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def is_safe_path(base_dir, file_path):
        """检查文件路径是否安全，防止路径遍历攻击"""
        base_dir = Path(base_dir).resolve()
        file_path = Path(file_path).resolve()
        return file_path.is_relative_to(base_dir)



class FileDeleteResource1(Resource):
    @jwt_required()
    def post(self):
        """文件删除接口[^1]"""
        data = request.form
        if 'uuid' not in data:
            return APIResponse.error('缺少必要参数', 400)

        try:
            # 根据 UUID 查询翻译记录
            translate_record = Translate.query.filter_by(uuid=data['uuid']).first()
            if not translate_record:
                return APIResponse.error('文件记录不存在', 404)

            # 获取文件绝对路径
            file_path = translate_record.origin_filepath

            # 删除物理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                current_app.logger.warning(f"文件不存在：{file_path}")

            # 删除数据库记录
            db.session.delete(translate_record)
            db.session.commit()

            return APIResponse.success(message='文件删除成功')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"文件删除失败：{str(e)}")
            return APIResponse.error('文件删除失败', 500)



class FileDeleteResource(Resource):
    @jwt_required()
    def post(self):
        """文件删除接口"""
        data = request.form
        if 'uuid' not in data:
            return APIResponse.error('缺少必要参数', 400)

        try:
            # 根据 UUID 查询翻译记录
            translate_record = Translate.query.filter_by(uuid=data['uuid']).first()
            if not translate_record:
                return APIResponse.error('文件记录不存在', 404)

            # 获取文件绝对路径
            file_path = Path(translate_record.origin_filepath)

            # 删除物理文件
            if file_path.exists():
                file_path.unlink()
            else:
                current_app.logger.warning(f"文件不存在：{file_path}")

            # 删除数据库记录
            db.session.delete(translate_record)
            db.session.commit()

            return APIResponse.success(message='文件删除成功')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"文件删除失败：{str(e)}")
            return APIResponse.error('文件删除失败', 500)
