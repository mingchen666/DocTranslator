"""Expand password columns for Werkzeug hashes."""

from alembic import op
import sqlalchemy as sa


revision = '20260720_password_columns'
down_revision = '4f90bb3344d2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer') as batch_op:
        batch_op.alter_column(
            'password',
            existing_type=sa.Text(),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column(
            'password',
            existing_type=sa.Text(),
            type_=sa.String(length=255),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.alter_column(
            'password',
            existing_type=sa.String(length=255),
            type_=sa.Text(),
            existing_nullable=False,
        )
    with op.batch_alter_table('customer') as batch_op:
        batch_op.alter_column(
            'password',
            existing_type=sa.String(length=255),
            type_=sa.Text(),
            existing_nullable=False,
        )
