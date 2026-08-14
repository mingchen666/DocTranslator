from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
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
    jwt.init_app(app)
    # 拦截jwt
    configure_jwt_callbacks(jwt)
    mail.init_app(app)
    migrate.init_app(
        app,
        db,
        directory=str(Path(app.root_path).parent / 'migrations'),
    )

