import logging
from sqlalchemy import inspect, text


logger = logging.getLogger(__name__)


def _validate_recorded_revisions(app, versions):
    if not versions:
        return

    from alembic.script import ScriptDirectory
    from alembic.util import CommandError

    extension = app.extensions['migrate']
    config = extension.migrate.get_config(extension.directory)
    script = ScriptDirectory.from_config(config)
    unknown = []
    for version in versions:
        try:
            script.get_revision(version)
        except CommandError:
            unknown.append(version)
    if unknown:
        raise RuntimeError(
            '数据库包含未知 Alembic 版本: ' + ', '.join(unknown)
        )


def run_migrations(app=None, seed=True):
    """Migrate one database and optionally insert idempotent application data."""
    from flask_migrate import upgrade
    from app import create_app

    app = app or create_app()
    with app.app_context():
        engine = app.extensions['migrate'].db.engine
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        has_version_table = 'alembic_version' in table_names

        with engine.connect() as connection:
            versions = []
            if has_version_table:
                versions = [
                    row[0] for row in connection.execute(
                        text('SELECT version_num FROM alembic_version')
                    ).fetchall()
                ]

        _validate_recorded_revisions(app, versions)

        if not table_names - {'alembic_version'}:
            logger.info('空数据库，执行完整 Alembic 基线')
        else:
            if not has_version_table or not versions:
                logger.warning(
                    '旧数据库未记录 Alembic 版本，将从基线补齐缺失结构'
                )
            else:
                logger.info('数据库当前 Alembic 版本: %s', ', '.join(versions))

            # create_all is intentionally limited to missing tables. Existing
            # tables and data remain untouched; Alembic owns column changes.
            from app import models as _models  # noqa: F401
            from app.extensions import db
            db.create_all()

        # The compatibility baseline skips existing tables and creates only
        # missing ones, so unversioned legacy databases can safely upgrade
        # from base instead of being stamped past required DDL.
        upgrade()

        if seed:
            from app.script.insert_init_db import (
                insert_admin_from_env,
                insert_initial_data,
                insert_initial_settings,
            )
            insert_initial_data(app)
            insert_initial_settings(app)
            insert_admin_from_env(app)

    logger.info('数据库迁移完成')
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_migrations()
