# utils/validators.py
from datetime import datetime, timedelta
from app.models import SendCode


def validate_verification_code(email: str, code: str, code_type: int):
    """验证验证码有效性[^1]"""
    expire_time = datetime.utcnow() - timedelta(minutes=10)
    send_code = SendCode.query.filter(
        SendCode.send_to == email,
        SendCode.code == code,
        SendCode.send_type == code_type,
        SendCode.created_at > expire_time
    ).order_by(SendCode.created_at.desc()).first()

    if not send_code:
        return False, '验证码已过期或无效'
    return True, None


def validate_password_confirmation(data: dict):
    """验证密码一致性[^2]"""
    if data['password'] != data.get('password_confirmation'):
        return False, '两次密码不一致'
    return True, None

# utils/validators.py 新增方法
def validate_password_complexity(password: str):
    """密码复杂度验证[^5]"""
    if len(password) < 6:
        return False, "密码至少需要6位"
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return False, "密码需包含字母和数字"
    return True, None


# utils/validators.py
from flask import request
from app.utils.response import APIResponse


def validate_pagination_params(req):
    """验证并获取分页参数[^1]

    返回:
        tuple: (page, limit)
    """
    try:
        page = int(req.args.get('page', 1))
        limit = int(req.args.get('limit', 20))

        if page < 1:
            raise ValueError('页码必须大于0')
        if limit < 1 or limit > 100:
            raise ValueError('每页数量必须在1到100之间')

        return page, limit
    except ValueError as e:
        raise APIResponse.error(str(e), 400)


def validate_date_range(start_date, end_date):
    """验证日期范围参数[^2]
    参数:
        start_date (str): 起始日期
        end_date (str): 结束日期
    返回:
        tuple: (start_date, end_date) 转换后的datetime对象
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        if start and end and start > end:
            raise ValueError('起始日期不能晚于结束日期')

        return start, end
    except ValueError as e:
        raise APIResponse.error('日期格式错误', 400)


def validate_id_list(ids):
    """验证ID列表参数[^3]
    参数:
        ids (list): ID列表
    返回:
        list: 验证后的ID列表
    """
    if not ids or not isinstance(ids, list):
        raise APIResponse.error('参数错误', 400)

    try:
        return [int(id) for id in ids]
    except ValueError:
        raise APIResponse.error('ID格式错误', 400)


