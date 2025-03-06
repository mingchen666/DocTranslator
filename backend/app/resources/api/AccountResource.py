
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app import db
from app.models import Customer, SendCode
from app.utils.security import hash_password, verify_password
from app.utils.response import APIResponse
from app.utils.mail_service import EmailService
from app.utils.validators import (
    validate_verification_code,
    validate_password_confirmation,
    validate_password_complexity
)
import random


class ChangePasswordResource(Resource):
    @jwt_required()
    def post(self):
        """修改密码（旧密码验证）[^1]"""
        user_id = get_jwt_identity()
        data = request.json

        # 参数校验
        required_fields = ['oldpwd', 'newpwd', 'newpwd_confirmation']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        # 密码一致性验证
        is_valid, msg = validate_password_confirmation({
            'password': data['newpwd'],
            'password_confirmation': data['newpwd_confirmation']
        })
        if not is_valid:
            return APIResponse.error(msg, 400)

        # 密码复杂度验证
        is_valid, msg = validate_password_complexity(data['newpwd'])
        if not is_valid:
            return APIResponse.error(msg, 422)

        customer = Customer.query.get(user_id)
        if not verify_password(customer.password, data['oldpwd']):
            return APIResponse.error('旧密码不正确', 401)

        customer.password = hash_password(data['newpwd'])
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        return APIResponse.success(message='密码修改成功')


class SendChangeCodeResource(Resource):
    @jwt_required()
    def post(self):
        """发送修改密码验证码[^2]"""
        user_id = get_jwt_identity()
        customer = Customer.query.get(user_id)

        code = ''.join(random.choices('0123456789', k=6))
        send_code = SendCode(
            send_type=3,  # 密码修改验证码类型[^6]
            send_to=customer.email,
            code=code,
            created_at=datetime.utcnow()
        )
        db.session.add(send_code)
        try:
            EmailService.send_verification_code(customer.email, code)
            db.session.commit()
            return APIResponse.success(message='验证码已发送')
        except Exception as e:
            db.session.rollback()
            return APIResponse.error('邮件发送失败', 500)


class EmailChangePasswordResource(Resource):
    @jwt_required()
    def post(self):
        """通过邮箱验证码修改密码[^3]"""
        user_id = get_jwt_identity()
        data = request.json

        # 参数校验
        required_fields = ['code', 'newpwd', 'newpwd_confirmation']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        # 密码一致性验证
        is_valid, msg = validate_password_confirmation({
            'password': data['newpwd'],
            'password_confirmation': data['newpwd_confirmation']
        })
        if not is_valid:
            return APIResponse.error(msg, 400)

        # 验证码有效性验证
        customer = Customer.query.get(user_id)
        is_valid, msg = validate_verification_code(
            customer.email, data['code'], 3
        )
        if not is_valid:
            return APIResponse.error(msg, 400)

        # 更新密码
        customer.password = hash_password(data['newpwd'])
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        return APIResponse.success(message='密码修改成功')


class StorageInfoResource(Resource):
    @jwt_required()
    def get(self):
        """获取存储空间信息[^2]"""
        user_id = get_jwt_identity()
        customer = Customer.query.get(user_id)

        total = current_app.config['MAX_USER_STORAGE'] / (1024 * 1024)  # 转换为MB
        used = customer.storage / (1024 * 1024)  # 转换为MB
        percentage = (used / total) * 100 if total > 0 else 0

        return APIResponse.success({
            'storage': f"{total:.2f}",
            'used': f"{used:.2f}",
            'percentage': f"{percentage:.1f}"
        })


class UserInfoResource(Resource):
    @jwt_required()
    def get(self):
        """获取用户基本信息[^5]"""
        user_id = get_jwt_identity()
        customer = Customer.query.get(user_id)

        return APIResponse.success({
            'email': customer.email,
            'level': customer.level,
            'created_at': customer.created_at.isoformat(),
            'storage': customer.storage
        })
