# resources/admin/auth.py
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import db
from app.models.user import User
from app.utils.response import APIResponse



class AdminLoginResource(Resource):
    def post(self):
        """管理员登录[^1]"""
        data = request.json
        required_fields = ['email', 'password']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        try:
            # 查询管理员用户
            admin = User.query.filter_by(
                email=data['email'],
                deleted_flag='N'
            ).first()

            # 验证用户是否存在
            if not admin:
                current_app.logger.warning(f"用户不存在：{data['email']}")
                return APIResponse.unauthorized('账号或密码错误')

            # 直接比较明文密码
            if admin.password != data['password']:
                current_app.logger.warning(f"密码错误：{data['email']}")
                return APIResponse.error('账号或密码错误')

            # 生成JWT令牌
            access_token = create_access_token(identity=str(admin.id))
            return APIResponse.success({
                'token': access_token,
                'email': admin.email,
                'name': admin.name
            })

        except Exception as e:
            current_app.logger.error(f"登录失败：{str(e)}")
            return APIResponse.error('服务器内部错误', 500)


class AdminChangePasswordResource(Resource):
    @jwt_required()
    def post(self):
        """管理员修改邮箱和密码"""
        try:
            # 获取当前管理员 ID
            admin_id = get_jwt_identity()
            # 解析请求体
            data = request.get_json()
            required_fields = ['old_password']
            if not all(field in data for field in required_fields):
                return APIResponse.error('缺少必要参数', 400)

            # 查询管理员用户
            admin = User.query.get(admin_id)
            if not admin:
                return APIResponse.error('管理员不存在', 404)

            # 验证旧密码
            if admin.password != data['old_password']:
                return APIResponse.error(message='旧密码错误')

            # 更新邮箱（如果 user 不为空）
            if 'user' in data and data['user']:
                admin.email = data['user']

            # 更新密码（如果 new_password 和 confirm_password 不为空且一致）
            if 'new_password' in data and 'confirm_password' in data:
                if data['new_password'] and data['confirm_password']:
                    if data['new_password'] != data['confirm_password']:
                        return APIResponse.error('新密码和确认密码不一致', 400)
                    admin.password = data['new_password']  # 明文存储

            # 保存到数据库
            db.session.commit()

            return APIResponse.success(message='修改成功')

        except Exception as e:
            current_app.logger.error(f"修改失败：{str(e)}")
            return APIResponse.error('服务器内部错误', 500)




