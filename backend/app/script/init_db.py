import os
import platform
import time
from flask import Flask
import pymysql
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

# 配置跨平台兼容的日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_init.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def safe_init_mysql(app: Flask, sql_file: str = 'init.sql') -> bool:

    if not app or not isinstance(app, Flask):
        logger.error("无效的Flask应用实例")
        return False

    with app.app_context():
        try:
            # 跨平台路径处理
            sql_path = get_platform_path(sql_file)
            if not sql_path.exists():
                logger.warning(f"SQL文件 {sql_path} 不存在，跳过初始化")
                return False

            # 获取数据库配置（兼容环境变量）
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', os.getenv('PROD_DATABASE_URL'))
            if not db_url:
                logger.error("数据库配置未找到")
                return False

            # 解析连接信息（增强兼容性）
            conn_info = parse_db_url(db_url)
            if not conn_info:
                logger.error("无效的数据库连接字符串")
                return False

            # 检查是否已初始化（带重试机制）
            if check_database_initialized(conn_info):
                logger.info("数据库已初始化，跳过执行")
                return False

            logger.info("开始安全初始化MySQL数据库...")
            return execute_with_retry(conn_info, sql_path)

        except Exception as e:
            logger.error(f"数据库初始化异常: {str(e)}", exc_info=True)
            return False


def get_platform_path(file_path: str) -> Path:
    """处理跨平台文件路径问题"""
    # 统一转换为绝对路径
    path = Path(file_path).absolute()

    # 在Linux/macOS下检查路径大小写敏感性
    if platform.system() in ('Linux', 'Darwin'):
        try:
            # 尝试找到实际存在的路径（解决大小写问题）
            if path.exists():
                return path
            # 尝试查找忽略大小写的匹配路径
            parent = path.parent
            for f in parent.iterdir():
                if f.name.lower() == path.name.lower():
                    return f
        except Exception as e:
            logger.warning(f"路径检查异常: {str(e)}")

    return path


def parse_db_url(db_url: str) -> Optional[dict]:
    """增强的数据库URL解析"""
    try:
        result = urlparse(db_url)
        # 处理Windows下的特殊字符
        password = result.password.replace('%', '%%') if result.password else None

        return {
            'host': result.hostname,
            'port': result.port or 3306,
            'user': result.username,
            'password': password,
            'db': result.path[1:].split('?')[0],  # 去掉路径前的/和查询参数
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'connect_timeout': 10,
            'read_timeout': 30
        }
    except Exception as e:
        logger.error(f"解析数据库URL失败: {str(e)}")
        return None


def check_database_initialized(conn_info: dict, retries: int = 3) -> bool:
    """带重试机制的数据库初始化检查"""
    for attempt in range(retries):
        try:
            connection = None
            connection = pymysql.connect(**conn_info)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = 'alembic_version'
                """, (conn_info['db'],))
                result = cursor.fetchone()
                return result['count'] > 0
        except pymysql.OperationalError as e:
            if attempt == retries - 1:
                logger.warning(f"数据库连接失败（尝试{retries}次）: {str(e)}")
                return False
            logger.warning(f"数据库连接异常，重试中... ({attempt + 1}/{retries})")
            time.sleep(2 ** attempt)  # 指数退避
        except Exception as e:
            logger.warning(f"数据库检查异常: {str(e)}")
            return False
        finally:
            if connection:
                connection.close()
    return False


def execute_with_retry(conn_info: dict, sql_path: Path, retries: int = 3) -> bool:
    """带重试机制的数据库初始化"""
    for attempt in range(retries):
        try:
            return execute_safe_init(conn_info, sql_path)
        except pymysql.OperationalError as e:
            if attempt == retries - 1:
                logger.error(f"数据库操作最终失败（尝试{retries}次）: {str(e)}")
                return False
            logger.warning(f"数据库操作异常，重试中... ({attempt + 1}/{retries})")
            time.sleep(2 ** attempt)
    return False


def execute_safe_init(conn_info: dict, sql_path: Path) -> bool:
    """增强的安全初始化执行"""
    connection = None
    try:
        # 创建连接（设置更长的超时时间）
        conn_info['connect_timeout'] = 20
        connection = pymysql.connect(**conn_info)

        with connection.cursor() as cursor:
            # 创建数据库（兼容各种字符集）
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS `{conn_info['db']}` 
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"USE `{conn_info['db']}`")

            # 读取SQL文件（处理不同平台的换行符）
            with open(sql_path, 'r', encoding='utf-8-sig') as f:  # 处理BOM
                content = f.read().replace('\r\n', '\n')  # 统一换行符

            # 执行SQL语句
            for statement in parse_sql_content(content):
                execute_safe_sql(cursor, statement)

        connection.commit()
        logger.info("数据库初始化成功完成")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        raise  # 重新抛出异常供重试机制处理
    finally:
        if connection:
            connection.close()


def parse_sql_content(content: str) -> list:
    """改进的SQL内容解析"""
    # 移除BOM头和注释
    lines = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            # 处理行内注释
            line = line.split('--')[0].strip()
            if line:
                lines.append(line)

    # 合并语句（处理跨行语句）
    statements = []
    current = ""
    for line in lines:
        current += " " + line if current else line
        if ';' in line:
            stmt, _, remaining = current.partition(';')
            statements.append(stmt.strip())
            current = remaining.strip()

    if current:
        statements.append(current)

    return statements


def execute_safe_sql(cursor, sql: str):
    """增强的安全SQL执行"""
    try:
        if sql.strip():  # 忽略空语句
            cursor.execute(sql)
    except pymysql.Error as e:
        error_code = e.args[0]
        ignorable_errors = {
            1050: "表已存在",
            1060: "列已存在",
            1061: "键已存在",
            1062: "重复条目",
            1064: "语法警告",
            1054: "未知列",
            1146: "表不存在",
            2006: "MySQL服务器已断开",  # 连接问题
            2013: "查询期间丢失连接"
        }

        if error_code in ignorable_errors:
            logger.warning(f"安全跳过SQL执行（{error_code}-{ignorable_errors[error_code]}）")
        else:
            logger.error(f"SQL执行错误（{error_code}）: {str(e)}")
            raise



