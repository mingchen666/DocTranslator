from flask_restful import Resource
from flask_jwt_extended import jwt_required

from app.models.prompt import Prompt
from app.utils.response import APIResponse


class AdminPromptListResource(Resource):
    @jwt_required()
    def get(self):
        prompts = Prompt.query.filter_by(deleted_flag='N').order_by(Prompt.created_at.desc()).all()
        result = []
        for p in prompts:
            # customer = Customer.query.get(p.customer_id)
            result.append({
                'id': p.id,
                'title': p.title,
                'content': p.content,
                'share_flag': p.share_flag,
                'customer_id': p.customer_id,
                # 'customer_email': customer.email if customer else '',
                'created_at': p.created_at.isoformat() if p.created_at else None
            })
        return APIResponse.success({'data': result, 'total': len(result)})