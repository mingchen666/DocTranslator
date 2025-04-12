from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils.jwt_utils import configure_jwt_callbacks

# 初始化扩展实例

mail = Mail()
limiter = Limiter(key_func=get_remote_address)
# 创建扩展实例（尚未初始化）
api = Api()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    api.init_app(app)
    jwt.init_app(app)
    # 拦截jwt
    configure_jwt_callbacks(jwt)
    mail.init_app(app)
    migrate.init_app(app, db)
    # 延迟初始化API（避免循环导入）
    from app.routes import register_routes
    # 注册路由
    register_routes(api)
    api.init_app(app)



    # @jwt.user_lookup_loader
    # def user_lookup_callback(_jwt_header, jwt_data):
    #     from app.models.user import User
    #     identity = jwt_data["sub"]
    #     return User.query.get(identity)