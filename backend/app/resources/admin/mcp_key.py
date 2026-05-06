from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.mcp_api_key import McpApiKey
from app.models.customer import Customer
from app.utils.response import APIResponse


class AdminMcpKeyListResource(Resource):
    @jwt_required()
    def get(self):
        admin_id = get_jwt_identity()
        scope = request.args.get('scope', '')
        customer_id = request.args.get('customer_id', '')

        query = McpApiKey.query.filter_by(deleted_flag='N')
        if scope in ('user', 'admin'):
            query = query.filter_by(scope=scope)
        if customer_id:
            query = query.filter_by(customer_id=int(customer_id))
        keys = query.order_by(McpApiKey.created_at.desc()).all()

        result = []
        for k in keys:
            d = k.to_dict(include_config=True)
            customer = Customer.query.get(k.customer_id)
            d['customer_email'] = customer.email if customer else ''
            result.append(d)

        admin_keys = McpApiKey.query.filter_by(
            customer_id=admin_id, scope='admin', deleted_flag='N'
        ).count()
        result.append(admin_keys)
        return APIResponse.success(
            data=result,
        )


class AdminMcpKeyCreateResource(Resource):
    @jwt_required()
    def post(self):
        data = request.json
        admin_id = get_jwt_identity()

        name = data.get('name', '')
        scope = data.get('scope', 'admin')
        config = data.get('config', {})
        customer_id = data.get('customer_id')

        if scope not in ('user', 'admin'):
            return APIResponse.error('scope 必须为 user 或 admin', 400)

        target_customer_id = admin_id
        if scope == 'user':
            if not customer_id:
                return APIResponse.error('创建用户端密钥时必须指定 customer_id', 400)
            customer = Customer.query.get(int(customer_id))
            if not customer:
                return APIResponse.error('用户不存在', 400)
            target_customer_id = int(customer_id)
        else:
            current_count = McpApiKey.query.filter_by(
                customer_id=admin_id, scope='admin', deleted_flag='N'
            ).count()
            if current_count >= 3:
                return APIResponse.error('管理员最多创建 3 个管理端密钥', 400)

        default_config = dict(McpApiKey.DEFAULT_CONFIG)
        default_config.update(config)

        if scope == 'admin':
            required_fields = ['api_url', 'api_key', 'model']
            for field in required_fields:
                if not default_config.get(field):
                    return APIResponse.error(f'config 中 {field} 为必填项', 400)

        raw_key, key_hash, key_prefix = McpApiKey.generate_key()

        mcp_key = McpApiKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            customer_id=target_customer_id,
            scope=scope,
            config=default_config,
        )
        db.session.add(mcp_key)
        db.session.commit()

        return APIResponse.success({
            'id': mcp_key.id,
            'key': raw_key,
            'key_prefix': key_prefix,
        })


class AdminMcpKeyDetailResource(Resource):
    @jwt_required()
    def get(self, id):
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id, deleted_flag='N'
        ).first()
        if not mcp_key:
            return APIResponse.error('密钥不存在', 404)
        result = mcp_key.to_dict(include_config=True)
        customer = Customer.query.get(mcp_key.customer_id)
        result['customer_email'] = customer.email if customer else ''
        return APIResponse.success(result)

    @jwt_required()
    def post(self, id):
        data = request.json
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id, deleted_flag='N'
        ).first()
        if not mcp_key:
            return APIResponse.error('密钥不存在', 404)

        if 'name' in data:
            mcp_key.name = data['name']
        if 'config' in data:
            current_config = mcp_key.get_config()
            current_config.update(data['config'])
            mcp_key.config = current_config
        if 'status' in data and data['status'] in ('active', 'revoked'):
            mcp_key.status = data['status']

        db.session.commit()
        result = mcp_key.to_dict(include_config=True)
        customer = Customer.query.get(mcp_key.customer_id)
        result['customer_email'] = customer.email if customer else ''
        return APIResponse.success(result)

    @jwt_required()
    def delete(self, id):
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id, deleted_flag='N'
        ).first()
        if not mcp_key:
            return APIResponse.error('密钥不存在', 404)
        mcp_key.deleted_flag = 'Y'
        db.session.commit()
        return APIResponse.success(message='密钥已删除')


class AdminMcpKeyRegenerateResource(Resource):
    @jwt_required()
    def post(self, id):
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id, deleted_flag='N'
        ).first()
        if not mcp_key:
            return APIResponse.error('密钥不存在', 404)

        raw_key, new_hash, new_prefix = McpApiKey.generate_key()
        mcp_key.key_hash = new_hash
        mcp_key.key_prefix = new_prefix
        mcp_key.last_used_at = None
        db.session.commit()

        return APIResponse.success({
            'id': mcp_key.id,
            'key': raw_key,
            'key_prefix': new_prefix,
        })
