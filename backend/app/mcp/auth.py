import logging
import asyncio
from datetime import datetime
from typing import Optional

from fastmcp.server.auth import AuthProvider, AccessToken

logger = logging.getLogger(__name__)

_flask_app = None


def set_flask_app_for_auth(app):
    global _flask_app
    _flask_app = app


def _get_flask_app():
    if _flask_app:
        return _flask_app
    try:
        from flask import current_app
        return current_app._get_current_object()
    except RuntimeError:
        return None


def _verify_token_sync(token: str, scope: str) -> Optional[dict]:
    app = _get_flask_app()
    if app is None:
        logger.error("MCP鉴权异常: Flask app 不可用")
        return None

    with app.app_context():
        try:
            from app.models.mcp_api_key import McpApiKey
            from app.extensions import db

            key_hash = McpApiKey.hash_key(token)
            mcp_key = McpApiKey.query.filter_by(
                key_hash=key_hash,
                status='active',
                deleted_flag='N',
                scope=scope,
            ).first()

            if not mcp_key:
                logger.warning(f"MCP鉴权失败: token无效 scope={scope}")
                return None

            mcp_key.last_used_at = datetime.utcnow()
            db.session.commit()

            config = mcp_key.get_config()
            customer_id = str(mcp_key.customer_id)

            return {
                'token': token,
                'client_id': customer_id,
                'scopes': [scope],
                'expires_at': None,
                'claims': {
                    'customer_id': customer_id,
                    'mcp_key_id': str(mcp_key.id),
                    'scope': scope,
                    'config': config,
                }
            }
        except Exception as e:
            logger.error(f"MCP鉴权异常: {e}")
            return None


class McpApiKeyAuthProvider(AuthProvider):
    def __init__(self, scope: str = 'user'):
        super().__init__()
        self.scope = scope

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, _verify_token_sync, token, self.scope
            )

            if result is None:
                return None

            return AccessToken(
                token=result['token'],
                client_id=result['client_id'],
                scopes=result['scopes'],
                expires_at=result['expires_at'],
                claims=result['claims'],
            )
        except Exception as e:
            logger.error(f"MCP鉴权异常(async): {e}")
            return None


def verify_api_key(raw_key: str, scope: str = 'user') -> Optional[dict]:
    try:
        from app.models.mcp_api_key import McpApiKey
        from app.extensions import db

        key_hash = McpApiKey.hash_key(raw_key)
        mcp_key = McpApiKey.query.filter_by(
            key_hash=key_hash,
            status='active',
            deleted_flag='N',
            scope=scope,
        ).first()

        if not mcp_key:
            return None

        mcp_key.last_used_at = datetime.utcnow()
        db.session.commit()

        return {
            'customer_id': mcp_key.customer_id,
            'mcp_key_id': mcp_key.id,
            'scope': mcp_key.scope,
            'config': mcp_key.get_config(),
        }
    except Exception as e:
        logger.error(f"MCP鉴权异常: {e}")
        return None
