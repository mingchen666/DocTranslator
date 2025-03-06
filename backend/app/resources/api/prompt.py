# resources/prompt.py
from datetime import datetime, date

from flask import request
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app import db
from app.models import Customer
from app.models.prompt import Prompt, PromptFav
from app.utils.response import APIResponse

# 获取提示语列表
class MyPromptListResource(Resource):
    @jwt_required()
    def get(self):
        """获取我的提示语列表[^1]"""
        # 直接查询所有数据（不解析查询参数）
        query = Prompt.query.filter_by(customer_id=get_jwt_identity(), deleted_flag='N')
        prompts = [{
            'id': p.id,
            'title': p.title,
            'content': p.content[:100] + '...' if len(p.content) > 100 else p.content,
            'share_flag': p.share_flag,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in query.all()]

        # 返回结果
        return APIResponse.success({
            'data': prompts,
            'total': len(prompts)
        })



# 获取共享提示语列表
class SharedPromptListResource(Resource):
    def get(self):
        """获取共享提示语列表[^4]"""
        # 从查询字符串中解析参数
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')  # 分页参数
        parser.add_argument('limit', type=int, default=10, location='args')  # 分页参数
        parser.add_argument('porder', type=str, default='latest', location='args')  # 排序参数
        args = parser.parse_args()

        # 查询共享的提示语
        query = db.session.query(
            Prompt,  # 获取完整的 Prompt 信息
            func.count(PromptFav.id).label('fav_count'),  # 动态计算收藏量
            Customer.email.label('customer_email')  # 获取用户的 email
        ).outerjoin(
            PromptFav, Prompt.id == PromptFav.prompt_id
        ).outerjoin(
            Customer, Prompt.customer_id == Customer.id  # 通过 customer_id 关联 Customer
        ).filter(
            Prompt.share_flag == 'Y',
            Prompt.deleted_flag == 'N'
        ).group_by(
            Prompt.id
        )

        # 根据 porder 参数排序
        if args['porder'] == 'latest':
            query = query.order_by(Prompt.created_at.desc())  # 按最新发表排序
        elif args['porder'] == 'added':
            query = query.order_by(Prompt.added_count.desc())  # 按添加量排序
        elif args['porder'] == 'fav':
            query = query.order_by(func.count(PromptFav.id).desc())  # 按收藏量排序

        # 分页查询
        pagination = query.paginate(page=args['page'], per_page=args['limit'], error_out=False)
        prompts = [{
            'id': prompt.id,
            'title': prompt.title,
            'content': prompt.content,  # 返回完整的提示语内容
            'email': customer_email if customer_email else '匿名用户',  # 使用查询结果中的 email
            'share_flag': prompt.share_flag,
            'added_count': prompt.added_count,
            'created_at': prompt.created_at.strftime('%Y-%m-%d') if prompt.created_at else None,  # 处理 None 值
            'updated_at': prompt.updated_at.strftime('%Y-%m-%d') if prompt.updated_at else None,  # 处理 None 值
            'fav_count': fav_count
        } for prompt, fav_count, customer_email in pagination.items]

        # 返回结果
        return APIResponse.success({
            'data': prompts,
            'total': pagination.total
        })




# 修改提示语内容
class EditPromptResource(Resource):
    @jwt_required()
    def post(self, id):
        """修改提示语内容[^3]"""
        prompt = Prompt.query.filter_by(
            id=id,
            customer_id=get_jwt_identity(),
            deleted_flag='N'
        ).first_or_404()

        data = request.form
        if 'title' in data:
            if len(data['title']) > 255:
                return APIResponse.error('标题过长', 400)
            prompt.title = data['title']

        if 'content' in data:
            if len(data['content']) > 5000:
                return APIResponse.error('内容超过5000字符限制', 400)
            prompt.content = data['content']

        db.session.commit()
        return APIResponse.success(message='提示语更新成功')

# 更新共享状态
class SharePromptResource(Resource):
    @jwt_required()
    def post(self, id):
        """
        修改共享状态[^4]
        :param id: prompt 的 ID（路径参数）
        """
        # 根据 id 和当前用户查询 prompt
        prompt = Prompt.query.filter_by(
            id=id,
            customer_id=get_jwt_identity(),
            deleted_flag='N'
        ).first_or_404()

        # 从请求体中获取 share_flag
        data = request.form  # 或者 request.form 如果是表单数据
        if not data or 'share_flag' not in data or data['share_flag'] not in ['Y', 'N']:
            return APIResponse.error('无效的共享状态参数', 400)

        # 更新共享状态
        prompt.share_flag = data['share_flag']
        db.session.commit()

        return APIResponse.success(message='共享状态已更新')


# 复制到我的提示语库
class CopyPromptResource(Resource):
    @jwt_required()
    def post(self, id):
        """复制到我的提示语库[^5]"""
        original = Prompt.query.filter_by(
            id=id,
            share_flag='Y',
            deleted_flag='N'
        ).first_or_404()

        new_prompt = Prompt(
            title=f"{original.title} (副本)",
            content=original.content,
            customer_id=get_jwt_identity(),
            share_flag='N',
            added_count=0
        )
        db.session.add(new_prompt)
        db.session.commit()
        return APIResponse.success({
            'new_id': new_prompt.id,
            'message': '复制成功'
        })

# 收藏/取消收藏
class FavoritePromptResource(Resource):
    @jwt_required()
    def post(self, id):
        """收藏/取消收藏[^6]"""
        prompt = Prompt.query.get_or_404(id)
        customer_id = get_jwt_identity()

        fav = PromptFav.query.filter_by(
            prompt_id=id,
            customer_id=customer_id
        ).first()

        if fav:
            db.session.delete(fav)
            action = '取消收藏'
        else:
            new_fav = PromptFav(
                prompt_id=id,
                customer_id=customer_id
            )
            db.session.add(new_fav)
            action = '收藏'

        prompt.added_count = prompt.added_count + (1 if not fav else -1)
        db.session.commit()
        return APIResponse.success(message=f'{action}成功')

# 创建新的提示语

class CreatePromptResource(Resource):
    @jwt_required()
    def post(self):
        """创建新提示语[^7]"""
        data = request.form
        required_fields = ['title', 'content']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        if len(data['title']) > 255:
            return APIResponse.error('标题过长', 400)
        if len(data['content']) > 5000:
            return APIResponse.error('内容超过5000字符限制', 400)

        # 创建时自动设置 created_at 为当前时间
        prompt = Prompt(
            title=data['title'],
            content=data['content'],
            customer_id=get_jwt_identity(),
            share_flag=data.get('share_flag', 'N'),
            created_at=date.today()  # 自动设置当前时间
        )
        db.session.add(prompt)
        db.session.commit()
        return APIResponse.success({
            'id': prompt.id,
            'message': '创建成功'
        })


# 删除提示语
class DeletePromptResource(Resource):
    @jwt_required()
    def delete(self, id):
        """删除提示语[^8]"""
        prompt = Prompt.query.filter_by(
            id=id,
            customer_id=get_jwt_identity()
        ).first_or_404()

        prompt.deleted_flag = 'Y'
        db.session.commit()
        return APIResponse.success(message='删除成功')


