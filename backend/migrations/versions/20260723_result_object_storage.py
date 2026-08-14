"""add result object storage location fields

Revision ID: 20260723_result_storage
Revises: 20260721_translation_batches
Create Date: 2026-07-23
"""

from alembic import op
import sqlalchemy as sa


revision = '20260723_result_storage'
down_revision = '20260721_translation_batches'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column['name']: column for column in inspector.get_columns('translate')
    }
    constraints = {
        constraint.get('name')
        for constraint in inspector.get_check_constraints('translate')
    }
    with op.batch_alter_table('translate') as batch_op:
        if 'target_storage_backend' not in columns:
            batch_op.add_column(sa.Column(
                'target_storage_backend', sa.String(length=16),
                nullable=False, server_default='local'
            ))
        else:
            op.execute(
                "UPDATE translate SET target_storage_backend='local' "
                "WHERE target_storage_backend IS NULL"
            )
            batch_op.alter_column(
                'target_storage_backend',
                existing_type=sa.String(length=16),
                nullable=False,
                server_default='local',
            )
        if 'target_storage_key' not in columns:
            batch_op.add_column(sa.Column(
                'target_storage_key', sa.String(length=1024), nullable=True
            ))
        if 'ck_translate_target_storage_backend' not in constraints:
            batch_op.create_check_constraint(
                'ck_translate_target_storage_backend',
                "target_storage_backend IN ('local', 'oss')",
            )


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {
        column['name'] for column in inspector.get_columns('translate')
    }
    constraints = {
        constraint.get('name')
        for constraint in inspector.get_check_constraints('translate')
    }
    with op.batch_alter_table('translate') as batch_op:
        if 'ck_translate_target_storage_backend' in constraints:
            batch_op.drop_constraint(
                'ck_translate_target_storage_backend', type_='check'
            )
        if 'target_storage_key' in columns:
            batch_op.drop_column('target_storage_key')
        if 'target_storage_backend' in columns:
            batch_op.drop_column('target_storage_backend')
