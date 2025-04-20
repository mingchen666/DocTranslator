# resources/admin/user.py
from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from app import db
from app.models import User
from app.utils.auth_tools import hash_password
from app.utils.response import APIResponse


class AdminUserListResource(Resource):
    @jwt_required()
    def get(self):
        """获取用户列表[^1]"""
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('limit', type=int, default=20)
        parser.add_argument('search', type=str)
        args = parser.parse_args()

        query = User.query
        if args['search']:
            query = query.filter(User.email.ilike(f"%{args['search']}%"))

        pagination = query.paginate(page=args['page'], per_page=args['limit'], error_out=False)
        users = [{
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'status': 'active' if u.deleted_flag == 'N' else 'deleted'
        } for u in pagination.items]

        return APIResponse.success({
            'data': users,
            'total': pagination.total
        })


# 创建新用户
class AdminCreateUserResource(Resource):
    @jwt_required()
    def put(self):
        """创建新用户[^2]"""
        data = request.json
        required_fields = ['name', 'email', 'password']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        if User.query.filter_by(email=data['email']).first():
            return APIResponse.error('邮箱已存在', 400)

        user = User(
            name=data['name'],
            email=data['email'],
            password=hash_password(data['password'])
        )
        db.session.add(user)
        db.session.commit()
        return APIResponse.success({
            'user_id': user.id,
            'message': '用户创建成功'
        })


# 获取用户详细信息
class AdminUserDetailResource(Resource):
    @jwt_required()
    def get(self, id):
        """获取用户详细信息[^3]"""
        user = User.query.get_or_404(id)
        return APIResponse.success({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'status': 'active' if user.deleted_flag == 'N' else 'deleted',
            'created_at': user.created_at.isoformat()
        })


# 编辑用户信息
class AdminUpdateUserResource(Resource):
    @jwt_required()
    def post(self, id):
        """编辑用户信息[^4]"""
        user = User.query.get_or_404(id)
        data = request.json

        if 'email' in data and User.query.filter(User.email == data['email'],User.id != id).first():
            return APIResponse.error('邮箱已被使用', 400)

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']

        db.session.commit()
        return APIResponse.success(message='用户信息更新成功')


# 删除用户
class AdminDeleteUserResource(Resource):
    @jwt_required()
    def delete(self, id):
        """删除用户[^5]"""
        user = User.query.get_or_404(id)
        user.deleted_flag = 'Y'
        db.session.commit()
        return APIResponse.success(message='用户删除成功')
