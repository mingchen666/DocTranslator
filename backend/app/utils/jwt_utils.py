from .response import APIResponse


def configure_jwt_callbacks(jwt):
    """
    配置 JWT 的错误处理回调函数
    :param jwt: 已初始化的 JWTManager 实例
    """
    # 拦截 Token 过期错误
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return APIResponse.unauthorized(message="Token has expired")

    # 拦截无效 Token 错误
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return APIResponse.unauthorized(message="Invalid token")

    # 拦截缺少 Token 的情况
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return APIResponse.unauthorized(message="Missing Authorization Header")


