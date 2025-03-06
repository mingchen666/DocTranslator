# resources/customer.py
from app.utils.response import APIResponse
import uuid
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required
from app.models.customer import Customer
class GuestIdResource(Resource):
    def get(self):
        """生成临时访客唯一标识[^1]"""
        guest_id = str(uuid.uuid4())
        return APIResponse.success({
            'guest_id': guest_id
        })





class CustomerDetailResource(Resource):
    @jwt_required()
    def get(self, customer_id):
        """获取客户详细信息[^2]"""
        customer = Customer.query.get_or_404(customer_id)
        return APIResponse.success({
            'id': customer.id,
            'email': customer.email,
            'level': customer.level,
            'created_at': customer.created_at.isoformat(),
            'storage': customer.storage
        })


