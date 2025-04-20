from flask import jsonify


class APIResponse:
    @staticmethod
    def success(data=None, message='操作成功', code=200):
        return {
            'code': code,
            'message': message,
            'data': data
        }, code

    @staticmethod
    def error(message='请求错误', code=400, errors=None):
        payload = {
            'code': code,
            'message': f"{message}"
        }
        if errors:
            payload['errors'] = errors
        return payload, code

    @classmethod
    def not_found(cls, message='资源不存在'):
        return cls.error(message=message, code=404)

    @classmethod
    def unauthorized(cls, message='身份验证失败'):
        return cls.error(message=message, code=401)


# ========== utils/responses.py ==========
class APIResponse1111:
    @staticmethod
    def success(data=None, message='操作成功', code=200):
        return {
            'code': code,
            'message': message,
            'data': data
        }, code

    @staticmethod
    def error(message='请求错误', code=400, errors=None):
        payload = {
            'code': code,
            'message': message
        }
        if errors:
            payload['errors'] = errors
        return payload, code

    @classmethod
    def not_found(cls, message='资源不存在'):
        return cls.error(message=message, code=404)

    @classmethod
    def unauthorized(cls, message='身份验证失败'):
        return cls.error(message=message, code=401)

    @classmethod
    def forbidden(cls, message='权限不足'):
        return cls.error(message=message, code=403)
