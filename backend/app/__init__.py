from flask import Flask
from flask_cors import CORS

from .config import get_config
from .extensions import init_extensions, db, api
from .models.setting import Setting
from .resources.task.translate_service import TranslateEngine
from .script.insert_init_db import insert_initial_data
from .utils.response import APIResponse


def create_app(config_class=None):
    app = Flask(__name__)

    from .routes import register_routes
    # 加载配置
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # 初始化扩展（此时不注册路由）
    init_extensions(app)
    register_routes(api)

    @app.errorhandler(404)
    def handle_404(e):
        return APIResponse.not_found()

    @app.errorhandler(500)
    def handle_500(e):
        return APIResponse.error(message='服务器错误', code=500)

    # 初始化数据库
    with app.app_context():
        db.create_all()
        # 在这里调用 TranslateEngine
        # engine = TranslateEngine(task_id=1, app=app)
        # engine.execute()
        # 初始化默认配置
        # if not SystemSetting.query.filter_by(key='version').first():
        #     db.session.add(SystemSetting(key='version', value='business'))
        #     db.session.commit()
    insert_initial_data(app)
    # 开发环境路由打印
    # if app.debug:
    #     with app.app_context():
    #         print("\n=== 已注册路由 ===")
    #         for rule in app.url_map.iter_rules():
    #             methods = ','.join(rule.methods)
    #             print(f"{rule.endpoint}: {methods} -> {rule}")
    #         print("===================\n")

    return app