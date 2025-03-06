# resources/admin/auth.py
from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.utils.response import APIResponse
from app.utils.security import verify_password



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
                return APIResponse.unauthorized('账号或密码错误')

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



