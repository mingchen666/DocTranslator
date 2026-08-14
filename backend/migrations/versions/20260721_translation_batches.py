"""Add durable queue indexes and translation batch metadata."""

from alembic import op
import sqlalchemy as sa


revision = '20260721_translation_batches'
down_revision = '20260720_password_columns'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('translate_batch'):
        op.create_table(
            'translate_batch',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('customer_id', sa.Integer(), nullable=False),
            sa.Column('source_type', sa.Enum('files', 'zip'), nullable=False),
            sa.Column('origin_filename', sa.String(length=520)),
            sa.Column(
                'status',
                sa.Enum('pending', 'process', 'done', 'partial', 'failed'),
                nullable=False,
            ),
            sa.Column('total_count', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('finished_at', sa.DateTime()),
        )

    inspector = sa.inspect(bind)
    batch_indexes = {
        index['name'] for index in inspector.get_indexes('translate_batch')
    }
    if 'ix_translate_batch_customer_id' not in batch_indexes:
        op.create_index(
            'ix_translate_batch_customer_id',
            'translate_batch',
            ['customer_id'],
        )

    translate_columns = {
        column['name'] for column in inspector.get_columns('translate')
    }
    translate_indexes = {
        index['name'] for index in inspector.get_indexes('translate')
    }
    if (
        'batch_id' not in translate_columns
        or 'batch_relative_path' not in translate_columns
        or 'ix_translate_batch_id' not in translate_indexes
    ):
        with op.batch_alter_table('translate') as batch_op:
            if 'batch_id' not in translate_columns:
                batch_op.add_column(sa.Column('batch_id', sa.String(length=36)))
            if 'batch_relative_path' not in translate_columns:
                batch_op.add_column(
                    sa.Column('batch_relative_path', sa.String(length=520))
                )
            if 'ix_translate_batch_id' not in translate_indexes:
                batch_op.create_index('ix_translate_batch_id', ['batch_id'])

    inspector = sa.inspect(bind)
    job_indexes = {index['name'] for index in inspector.get_indexes('jobs')}
    if 'ix_jobs_claim' not in job_indexes:
        op.create_index(
            'ix_jobs_claim',
            'jobs',
            ['queue', 'available_at', 'reserved_at'],
        )


def downgrade():
    op.drop_index('ix_jobs_claim', table_name='jobs')
    with op.batch_alter_table('translate') as batch_op:
        batch_op.drop_index('ix_translate_batch_id')
        batch_op.drop_column('batch_relative_path')
        batch_op.drop_column('batch_id')
    op.drop_index('ix_translate_batch_customer_id', table_name='translate_batch')
    op.drop_table('translate_batch')
