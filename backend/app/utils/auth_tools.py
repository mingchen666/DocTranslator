# ========== utils/auth_tools.py ==========
import random
from functools import wraps
from datetime import datetime, timedelta
from flask_jwt_extended import get_jwt, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash

from .response import APIResponse


def generate_code(length=6):
    """生成数字验证码"""
    return ''.join(random.choices('0123456789', k=length))


def validate_code(code_record):
    """验证码有效性检查"""
    if not code_record:
        return False
    return (datetime.utcnow() - code_record.created_at) < timedelta(seconds=1800)


def hash_password(password):
    """密码哈希处理"""
    return generate_password_hash(password)


def check_password(hashed_password, password):
    """密码校验"""
    return check_password_hash(hashed_password, password)


def is_password_hash(value):
    """Return whether a stored value looks like a Werkzeug password hash."""
    if not value or '$' not in value:
        return False
    return value.split(':', 1)[0] in {'pbkdf2', 'scrypt'}


def verify_legacy_password(stored_password, candidate):
    """Verify hashed passwords and allow a one-time plaintext transition."""
    if is_password_hash(stored_password):
        return check_password(stored_password, candidate), False
    return stored_password == candidate, stored_password == candidate


def admin_required(fn):
    """Require a valid JWT explicitly issued for an administrator."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if get_jwt().get('role') != 'admin':
            return APIResponse.error('管理员权限不足', 403)
        return fn(*args, **kwargs)

    return wrapper
