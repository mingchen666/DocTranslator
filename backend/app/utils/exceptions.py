# app/exceptions.py
class APIException(Exception):
    """基础API异常 [^1][^4]"""
    def __init__(self, message, code=400, payload=None):
        super().__init__()
        self.message = message
        self.code = code
        self.payload = payload

class NotFoundException(APIException):
    def __init__(self, message='资源不存在'):
        super().__init__(message, 404)

class PermissionDenied(APIException):
    def __init__(self, message='权限不足'):
        super().__init__(message, 403)

class ValidationError(APIException):
    def __init__(self, message='参数验证失败', errors=None):
        super().__init__(message, 400)
        self.errors = errors
