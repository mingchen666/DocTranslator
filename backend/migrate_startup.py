import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_startup():
    from app import create_app
    app = create_app()

    with app.app_context():
        from flask_migrate import upgrade, stamp
        from sqlalchemy import inspect

        inspector = inspect(app.extensions['migrate'].db.engine)
        existing_tables = inspector.get_table_names()

        has_alembic = 'alembic_version' in existing_tables
        has_translate = 'translate' in existing_tables

        if not has_alembic and not has_translate:
            logger.info("全新数据库，执行 init.sql 建表...")
            from app.script.init_db import safe_init_mysql
            safe_init_mysql(app, 'app/init.sql')

            logger.info("标记迁移版本到最新...")
            stamp()

        elif not has_alembic and has_translate:
            logger.info("数据库已有表但无迁移记录，标记初始版本...")
            stamp(revision='001_initial')

            logger.info("执行增量迁移...")
            upgrade()

        else:
            logger.info("执行增量迁移...")
            upgrade()

    logger.info("数据库迁移完成")
    return app


if __name__ == '__main__':
    run_startup()
