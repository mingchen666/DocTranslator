# -- coding: utf-8 --**
# resources/admin/customer.py
from decimal import Decimal

from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Customer
from app.utils.auth_tools import hash_password
from app.utils.response import APIResponse


# 获取用户列表
class AdminCustomerListResource(Resource):
    @jwt_required()
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, required=False, location='args')  # 可选，默认值为 1
        parser.add_argument('limit', type=int, required=False, location='args')  # 可选，默认值为 10
        parser.add_argument('keyword', type=str, required=False, location='args')  # 可选，无默认值
        args = parser.parse_args()
        query = Customer.query
        if args['keyword']:
            query = query.filter(Customer.email.ilike(f"%{args['keyword']}%"))

        pagination = query.paginate(page=args['page'], per_page=args['limit'], error_out=False)
        customers = [c.to_dict() for c in pagination.items]
        print(customers)
        return APIResponse.success({
            'data': customers,
            'total': pagination.total
        })


# 更新用户状态
class CustomerStatusResource(Resource):
    @jwt_required()
    def post(self, id):
        """
        更改用户状态
        """
        # 解析请求体中的状态参数
        parser = reqparse.RequestParser()
        parser.add_argument('status', type=str, required=True, choices=('enabled', 'disabled'),
                            help="状态必须是 'enabled' 或 'disabled'")
        args = parser.parse_args()

        # 查询用户
        customer = Customer.query.get(id)
        if not customer:
            return APIResponse.error(message="用户不存在", code=404)

        # 更新用户状态
        customer.status = args['status']
        db.session.commit()  # 假设 db 是你的 SQLAlchemy 实例
        # 更新用户状态
        customer.status = args['status']
        print(f"更新前的状态: {customer.status}")  # 调试
        db.session.commit()
        print(f"更新后的状态: {customer.status}")  # 调试

        # 返回更新后的用户信息
        return APIResponse.success(data=customer.to_dict())


# 创建新用户
class AdminCreateCustomerResource(Resource):
    @jwt_required()
    def put(self):
        """创建新用户[^2]"""
        data = request.json
        required_fields = ['email', 'password']  # 'name',
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数!', 400)

        if Customer.query.filter_by(email=data['email']).first():
            return APIResponse.error('邮箱已存在', 400)

        customer = Customer(
            # name=data['name'],
            email=data['email'],
            password=hash_password(data['password']),
            level=data.get('level', 'common')
        )
        db.session.add(customer)
        db.session.commit()
        return APIResponse.success({
            'customer_id': customer.id,
            'message': '用户创建成功'
        })


# 获取用户信息
class AdminCustomerDetailResource(Resource):
    @jwt_required()
    def get(self, id):
        """获取用户详细信息[^3]"""
        customer = Customer.query.get_or_404(id)
        return APIResponse.success({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'status': 'active' if customer.deleted_flag == 'N' else 'deleted',
            'level': customer.level,
            'created_at': customer.created_at.isoformat(),
            'storage': customer.storage
        })


# 编辑用户信息
class AdminUpdateCustomerResource(Resource):
    @jwt_required()
    def post(self, id):
        """编辑用户信息[^4]"""
        customer = Customer.query.get_or_404(id)
        data = request.json

        if 'email' in data and Customer.query.filter(Customer.email == data['email'],
                                                     Customer.id != id).first():
            return APIResponse.error('邮箱已被使用', 400)

        if 'name' in data:
            customer.name = data['name']
        if 'email' in data:
            customer.email = data['email']
        if 'level' in data:
            customer.level = data['level']
        if 'add_storage' in data:
            customer.storage = customer.storage-int(data['add_storage'])*1024*1024
        db.session.commit()
        return APIResponse.success(message='用户信息更新成功')


# 删除用户
class AdminDeleteCustomerResource(Resource):
    @jwt_required()
    def delete(self, id):
        """删除用户[^5]"""
        customer = Customer.query.get_or_404(id)
        customer.deleted_flag = 'Y'
        db.session.commit()
        return APIResponse.success(message='用户删除成功')
