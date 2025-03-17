import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（优先加载项目根目录的.env文件）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')  # 显式指定.env文件位置
# print(os.getenv('FLASK_ENV'))

class Config:
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=360000)  # 1小时过期
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)  # 刷新令牌7天
    JWT_TOKEN_LOCATION = ['headers']  # 只从请求头获取
    JWT_HEADER_NAME = 'token'  # 匹配原项目可能的头部名称
    JWT_HEADER_TYPE = ''  # 不使用Bearer前缀
    # 通用基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮件配置（所有环境通用）
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_DEBUG = True  # 开启SMTP调试
    # 业务配置
    CODE_EXPIRATION = 1800  # 30分钟（单位：秒）
    # 文件上传配置
    # 允许上传的文件类型
    UPLOAD_BASE_DIR='storage'
    UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), 'uploads')  # 与 app.py 同级
    DATE_FORMAT = "%Y-%m-%d"  # 日期格式
    ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'pptx', 'pdf', 'txt', 'md', 'csv', 'xls', 'doc'}
    # UPLOAD_FOLDER = '/uploads'  # 建议使用绝对路径
    MB = 1024 * 1024
    MAX_FILE_SIZE = 20 * MB  # 10MB
    MAX_USER_STORAGE = int(os.getenv('MAX_USER_STORAGE', 100 * MB))  # 800MB
    # 翻译结果存储配置
    STORAGE_FOLDER = '/app/storage'  # 翻译结果存储路径
    STATIC_FOLDER = '/public/static'  # 设置静态文件路径

    # 系统版本配置
    SYSTEM_VERSION = 'business'  # business/community
    SITE_NAME = '智能翻译平台'

    # API配置
    API_URL = 'https://api.example.com'
    TRANSLATE_MODELS = ['gpt-3.5', 'gpt-4']
    @property
    def allowed_domains(self):
        """获取格式化的域名列表"""
        domains = os.getenv('ALLOWED_DOMAINS', '')
        return [d.strip() for d in domains.split(',') if d.strip()]



class DevelopmentConfig(Config):
    DEBUG = True
    # SQLite配置（开发环境）
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        f'sqlite:////www/wwwroot/ez-work/backend/dev.db'  # 显式绝对路径
    )
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///yourdatabase.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'echo': False  # 输出SQL日志
    }


class TestingConfig(Config):
    TESTING = True
    # 内存型SQLite（测试环境）
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # 禁用CSRF保护


class ProductionConfig(Config):
    # MySQL/PostgreSQL配置（生产环境）
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'PROD_DATABASE_URL',
        'mysql+pymysql://user:password@localhost/prod_db?charset=utf8mb4'
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 30,
        'pool_timeout': 10
    }


# 配置映射字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """安全获取配置对象的工厂方法"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])
