import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（优先加载项目根目录的.env文件）
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def normalize_oss_prefix(value):
    """Return a safe relative OSS prefix with one trailing slash."""
    prefix = str(value or '').strip()
    if (
        not prefix
        or '..' in prefix
        or '\\' in prefix
        or any(ord(character) < 32 or ord(character) == 127 for character in prefix)
    ):
        raise RuntimeError('OSS_PREFIX必须是安全的相对路径前缀')
    normalized = prefix.strip('/')
    if not normalized:
        raise RuntimeError('OSS_PREFIX不能为空')
    return f'{normalized}/'

class Config:
    # Translation queue backend: database (default) or celery.
    TRANSLATION_QUEUE_BACKEND = os.getenv(
        'TRANSLATION_QUEUE_BACKEND', 'database'
    ).strip().lower()
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', '').strip()
    CELERY_VISIBILITY_TIMEOUT = int(
        os.getenv('CELERY_VISIBILITY_TIMEOUT', 21600)
    )
    CELERY_MAX_RETRIES = int(os.getenv('CELERY_MAX_RETRIES', 3))
    CELERY_LOCK_TIMEOUT = int(os.getenv('CELERY_LOCK_TIMEOUT', 120))
    RESULT_STORAGE_BACKEND = os.getenv(
        'RESULT_STORAGE_BACKEND', 'local'
    ).strip().lower()
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', '').strip()
    OSS_BUCKET = os.getenv('OSS_BUCKET', '').strip()
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID', '').strip()
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET', '').strip()
    OSS_PREFIX = os.getenv('OSS_PREFIX', 'translations/').strip()

    @classmethod
    def validate_queue_backend(cls):
        if cls.TRANSLATION_QUEUE_BACKEND not in {'database', 'celery'}:
            raise RuntimeError(
                'TRANSLATION_QUEUE_BACKEND必须是database或celery'
            )
        if cls.TRANSLATION_QUEUE_BACKEND == 'celery':
            if not cls.CELERY_BROKER_URL:
                raise RuntimeError(
                    'TRANSLATION_QUEUE_BACKEND=celery时必须设置CELERY_BROKER_URL'
                )
            if not cls.CELERY_BROKER_URL.startswith(('redis://', 'rediss://')):
                raise RuntimeError('CELERY_BROKER_URL必须是redis://或rediss://地址')
            if cls.CELERY_LOCK_TIMEOUT < 30:
                raise RuntimeError('CELERY_LOCK_TIMEOUT不能小于30秒')

    @classmethod
    def validate_result_storage(cls):
        if cls.RESULT_STORAGE_BACKEND not in {'local', 'oss'}:
            raise RuntimeError('RESULT_STORAGE_BACKEND必须是local或oss')
        cls.OSS_PREFIX = normalize_oss_prefix(cls.OSS_PREFIX)
        if cls.RESULT_STORAGE_BACKEND == 'oss':
            missing = [
                name for name in (
                    'OSS_ENDPOINT',
                    'OSS_BUCKET',
                    'OSS_ACCESS_KEY_ID',
                    'OSS_ACCESS_KEY_SECRET',
                )
                if not getattr(cls, name, '')
            ]
            if missing:
                raise RuntimeError(
                    'RESULT_STORAGE_BACKEND=oss时缺少配置: '
                    + ', '.join(missing)
                )
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=20)
    # JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)  # 刷新令牌7天
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'token'
    JWT_HEADER_TYPE = ''
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
    UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), 'uploads')
    DATE_FORMAT = "%Y-%m-%d"  # 日期格式
    ALLOWED_EXTENSIONS = {
        'docx', 'xlsx', 'pptx', 'pdf', 'txt', 'md', 'csv', 'html', 'htm'
    }
    # UPLOAD_FOLDER = '/uploads'  # 建议使用绝对路径
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50)) * 1024 * 1024  # 50MB
    MAX_USER_STORAGE = int(os.getenv('MAX_USER_STORAGE', 100 ))* 1024 * 1024  # 默认100MB
    BATCH_MAX_FILES = int(os.getenv('BATCH_MAX_FILES', 20))
    BATCH_MAX_UNCOMPRESSED_SIZE = int(
        os.getenv('BATCH_MAX_UNCOMPRESSED_SIZE_MB', 200)
    ) * 1024 * 1024
    BATCH_MAX_COMPRESSION_RATIO = int(
        os.getenv('BATCH_MAX_COMPRESSION_RATIO', 100)
    )
    # 翻译结果存储配置
    STORAGE_FOLDER = '/app/storage'  # 翻译结果存储路径
    STATIC_FOLDER = '/public/static'  # 设置静态文件路径

    # 系统版本配置
    SYSTEM_VERSION = 'business'  # business/community
    SITE_NAME = '智能翻译平台'

    # API配置
    API_URL = 'https://api.example.com'
    TRANSLATE_MODELS = ['gpt-3.5', 'gpt-4']

    # 时区
    TIMEZONE = 'Asia/Shanghai'#'UTC' #'Asia/Shanghai'
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
        f'sqlite:///instance/dev.db'  # 显式绝对路径
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
        'mysql://user:password@localhost/prod_db?charset=utf8mb4'
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
