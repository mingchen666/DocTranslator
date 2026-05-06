from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.mcp_api_key import McpApiKey
from app.utils.response import APIResponse

MAX_KEYS_PER_USER = 5
MAX_KEYS_PER_ADMIN = 3


class McpKeyListResource(Resource):
    @jwt_required()
    def get(self):
        customer_id = get_jwt_identity()
        keys = McpApiKey.query.filter_by(
            customer_id=customer_id,
            scope='user',
            deleted_flag='N'
        ).order_by(McpApiKey.created_at.desc()).all()
        return APIResponse.success(
            data=[k.to_dict() for k in keys],
        )


class McpKeyCreateResource(Resource):
    @jwt_required()
    def post(self):
        data = request.json
        customer_id = get_jwt_identity()

        name = data.get('name', '')
        scope = data.get('scope', 'user')
        config = data.get('config', {})

        if scope not in ('user', 'admin'):
            return APIResponse.error('scope 必须为 user 或 admin', 400)

        max_keys = MAX_KEYS_PER_USER if scope == 'user' else MAX_KEYS_PER_ADMIN
        current_count = McpApiKey.query.filter_by(
            customer_id=customer_id,
            scope=scope,
            deleted_flag='N'
        ).count()
        if current_count >= max_keys:
            return APIResponse.error(f'每个用户最多创建 {max_keys} 个 {scope} 密钥', 400)

        default_config = dict(McpApiKey.DEFAULT_CONFIG)
        default_config.update(config)

        required_fields = ['api_url', 'api_key', 'model']
        for field in required_fields:
            if not default_config.get(field):
                return APIResponse.error(f'config 中 {field} 为必填项', 400)

        raw_key, key_hash, key_prefix = McpApiKey.generate_key()

        mcp_key = McpApiKey(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            customer_id=customer_id,
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


class McpKeyDetailResource(Resource):
    @jwt_required()
    def get(self, id):
        customer_id = get_jwt_identity()
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id,
            customer_id=customer_id,
            deleted_flag='N'
        ).first()
        if not mcp_key:
            return APIResponse.error('密钥不存在', 404)
        return APIResponse.success(mcp_key.to_dict(include_config=True))

    @jwt_required()
    def post(self, id):
        data = request.json
        customer_id = get_jwt_identity()
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id,
            customer_id=customer_id,
            deleted_flag='N'
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
        return APIResponse.success(mcp_key.to_dict(include_config=True))

    @jwt_required()
    def delete(self, id):
        customer_id = get_jwt_identity()
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id,
            customer_id=customer_id,
            deleted_flag='N'
        ).first()
        if not mcp_key:
            return APIResponse.error('密钥不存在', 404)
        mcp_key.deleted_flag = 'Y'
        db.session.commit()
        return APIResponse.success(message='密钥已删除')


class McpKeyRegenerateResource(Resource):
    @jwt_required()
    def post(self, id):
        customer_id = get_jwt_identity()
        mcp_key = McpApiKey.query.filter_by(
            key_prefix=id,
            customer_id=customer_id,
            deleted_flag='N'
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
