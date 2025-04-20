from flask import Flask
import pymysql
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def safe_init_mysql(app: Flask, sql_file: str = 'init.sql') -> bool:
    """
    安全初始化MySQL数据库（兼容Flask-Migrate）
    """
    if not app or not isinstance(app, Flask):
        logger.error("无效的Flask应用实例")
        return False

    with app.app_context():
        try:
            # 检查SQL文件是否存在
            if not Path(sql_file).exists():
                logger.warning(f"SQL文件 {sql_file} 不存在，跳过初始化")
                return False

            # 获取数据库配置
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
            if not db_url:
                logger.error("数据库配置未找到")
                return False

            # 解析连接信息
            conn_info = parse_db_url(db_url)
            if not conn_info:
                logger.error("无效的数据库连接字符串")
                return False

            # 检查是否已初始化
            if is_database_initialized(conn_info):
                logger.info("数据库已初始化，跳过执行")
                return False

            logger.info("开始安全初始化MySQL数据库...")
            return execute_safe_init(conn_info, sql_file)

        except Exception as e:
            logger.error(f"数据库初始化异常: {str(e)}", exc_info=True)
            return False


def parse_db_url(db_url: str) -> Optional[dict]:
    """解析数据库连接URL为字典格式"""
    try:
        result = urlparse(db_url)
        return {
            'host': result.hostname,
            'port': result.port or 3306,
            'user': result.username,
            'password': result.password,
            'db': result.path[1:],  # 去掉路径前的/
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    except Exception as e:
        logger.error(f"解析数据库URL失败: {str(e)}")
        return None


def is_database_initialized(conn_info: dict) -> bool:
    """
    检查数据库是否已初始化
    通过检查alembic_version表是否存在来判断
    """
    connection = None
    try:
        connection = pymysql.connect(**conn_info)
        with connection.cursor() as cursor:
            # 检查alembic_version表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'alembic_version'
            """, (conn_info['db'],))
            result = cursor.fetchone()
            return result['count'] > 0
    except pymysql.Error as e:
        # 如果数据库不存在或其他错误，视为未初始化
        logger.warning(f"数据库检查异常: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()


def execute_safe_init(conn_info: dict, sql_file: str) -> bool:
    """执行安全的数据库初始化"""
    connection = None
    try:
        connection = pymysql.connect(**conn_info)
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{conn_info['db']}` "
                           f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE `{conn_info['db']}`")

            # 读取并处理SQL文件
            statements = parse_sql_file(sql_file)
            for statement in statements:
                execute_safe_sql(cursor, statement)

        connection.commit()
        logger.info("数据库初始化成功完成")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            connection.close()


def parse_sql_file(sql_file: str) -> list:
    """智能解析SQL文件，返回可执行的语句列表"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除注释和空行
    lines = [line.strip() for line in content.split('\n')
             if line.strip() and not line.strip().startswith('--')]

    # 合并跨行语句
    statements = []
    current = ""
    for line in lines:
        current += " " + line if current else line
        if line.endswith(';'):
            statements.append(current)
            current = ""

    if current:  # 处理最后未以分号结尾的语句
        statements.append(current + ';')

    return statements


def execute_safe_sql(cursor, sql: str):
    """安全执行单个SQL语句"""
    try:
        cursor.execute(sql)
    except pymysql.Error as e:
        error_code = e.args[0]
        # 忽略常见无害错误
        ignorable_errors = {
            1050: "表已存在",
            1060: "列已存在",
            1061: "键已存在",
            1062: "重复条目",
            1064: "语法警告",
            1054: "未知列",
            1146: "表不存在"
        }

        if error_code in ignorable_errors:
            logger.warning(
                f"安全跳过SQL执行（{error_code}-{ignorable_errors[error_code]}）: {str(e)}")
        else:
            logger.error(f"SQL执行错误（{error_code}）: {str(e)}")
            raise
