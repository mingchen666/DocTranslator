from flask import Flask, jsonify
from flask_cors import CORS
from .config import get_config
from .extensions import init_extensions, db, api
from .models.setting import Setting
from .utils.response import APIResponse


def create_app(config_class=None):
    app = Flask(__name__)

    from .routes import register_routes
    # 加载配置
    if config_class is None:
        config_class = get_config()
    config_class.validate_queue_backend()
    config_class.validate_result_storage()
    app.config.from_object(config_class)
    # Database migration and seed operations are owned by migrate_startup.py.
    init_extensions(app)
    if not api.resources:
        register_routes(api)
    api.init_app(app)

    @app.errorhandler(404)
    def handle_404(e):
        return APIResponse.not_found()

    from jwt.exceptions import ExpiredSignatureError

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_token_error(e):
        return jsonify({"message": "身份验证信息已过期，请重新登录"}), 401

    @app.errorhandler(500)
    def handle_500(e):
        return APIResponse.error(message='服务器错误', code=500)

    return app
