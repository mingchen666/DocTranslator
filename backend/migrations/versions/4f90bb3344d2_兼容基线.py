"""Create the current schema for an empty database.

Existing installations can run this revision from base. Existing tables are
left untouched while missing baseline tables are created.
"""

from alembic import op
import sqlalchemy as sa


revision = '4f90bb3344d2'
down_revision = None
branch_labels = None
depends_on = None


def _create_table(table_name, *columns, **kwargs):
    """Create a baseline table only when a legacy database lacks it."""
    if not sa.inspect(op.get_bind()).has_table(table_name):
        op.create_table(table_name, *columns, **kwargs)


def upgrade():
    _create_table(
        'cache',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('expiration', sa.Integer(), nullable=False),
    )
    _create_table(
        'cache_locks',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('owner', sa.String(255), nullable=False),
        sa.Column('expiration', sa.Integer(), nullable=False),
    )
    _create_table(
        'comparison',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('origin_lang', sa.String(32), nullable=False),
        sa.Column('target_lang', sa.String(32), nullable=False),
        sa.Column('share_flag', sa.Enum('N', 'Y'), nullable=True),
        sa.Column('added_count', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_flag', sa.Enum('N', 'Y'), nullable=True),
    )
    _create_table(
        'comparison_fav',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('comparison_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    _create_table(
        'customer',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_no', sa.String(32)),
        sa.Column('phone', sa.String(11)),
        sa.Column('name', sa.String(255)),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('level', sa.Enum('common', 'vip')),
        sa.Column('status', sa.Enum('enabled', 'disabled')),
        sa.Column('deleted_flag', sa.Enum('N', 'Y')),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('storage', sa.BigInteger()),
        sa.Column('total_storage', sa.BigInteger()),
    )
    _create_table(
        'failed_jobs',
        sa.Column(
            'id',
            sa.BigInteger().with_variant(sa.Integer(), 'sqlite'),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column('uuid', sa.String(255), unique=True),
        sa.Column('connection', sa.Text(), nullable=False),
        sa.Column('queue', sa.Text(), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('exception', sa.Text(), nullable=False),
        sa.Column('failed_at', sa.DateTime()),
    )
    _create_table(
        'job_batches',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('total_jobs', sa.Integer(), nullable=False),
        sa.Column('pending_jobs', sa.Integer(), nullable=False),
        sa.Column('failed_jobs', sa.Integer(), nullable=False),
        sa.Column('failed_job_ids', sa.Text(), nullable=False),
        sa.Column('options', sa.Text()),
        sa.Column('cancelled_at', sa.Integer()),
        sa.Column('created_at', sa.Integer(), nullable=False),
        sa.Column('finished_at', sa.Integer()),
    )
    _create_table(
        'jobs',
        sa.Column(
            'id',
            sa.BigInteger().with_variant(sa.Integer(), 'sqlite'),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column('queue', sa.String(255), nullable=False),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('attempts', sa.SmallInteger(), nullable=False),
        sa.Column('reserved_at', sa.Integer()),
        sa.Column('available_at', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False),
    )
    _create_table(
        'mcp_api_key',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(12), nullable=False),
        sa.Column('name', sa.String(100)),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('scope', sa.Enum('user', 'admin'), default='user'),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('active', 'revoked'), default='active'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('last_used_at', sa.DateTime()),
        sa.Column('deleted_flag', sa.Enum('N', 'Y'), default='N'),
    )
    _create_table(
        'message',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customer.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('unread', 'read'), default='unread'),
        sa.Column('msg_type', sa.String(50)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('deleted_flag', sa.CHAR(1), nullable=False, default='N'),
    )
    _create_table(
        'migrations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('migration', sa.String(255), nullable=False),
        sa.Column('batch', sa.Integer(), nullable=False),
    )
    _create_table(
        'password_reset_tokens',
        sa.Column('email', sa.String(255), primary_key=True),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime()),
    )
    _create_table(
        'prompt',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('share_flag', sa.Enum('N', 'Y')),
        sa.Column('added_count', sa.Integer()),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('customer_id', sa.Integer()),
        sa.Column('created_at', sa.Date()),
        sa.Column('updated_at', sa.Date()),
        sa.Column('deleted_flag', sa.Enum('N', 'Y')),
    )
    _create_table(
        'prompt_fav',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('prompt_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    _create_table(
        'send_code',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer()),
        sa.Column('send_type', sa.Integer(), nullable=False),
        sa.Column('send_to', sa.String(100), nullable=False),
        sa.Column('code', sa.String(6), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    _create_table(
        'sessions',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.BigInteger()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('last_activity', sa.Integer(), nullable=False),
    )
    _create_table(
        'setting',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('alias', sa.String(64)),
        sa.Column('value', sa.Text()),
        sa.Column('serialized', sa.Boolean()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_flag', sa.Enum('N', 'Y')),
        sa.Column('group', sa.String(32)),
    )
    _create_table(
        'translate',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('translate_no', sa.String(32)),
        sa.Column('uuid', sa.String(64)),
        sa.Column('customer_id', sa.Integer()),
        sa.Column('rand_user_id', sa.String(64)),
        sa.Column('origin_filename', sa.String(520), nullable=False),
        sa.Column('origin_filepath', sa.String(520), nullable=False),
        sa.Column('target_filepath', sa.String(520), nullable=False),
        sa.Column('status', sa.Enum('none', 'process', 'done', 'failed')),
        sa.Column('start_at', sa.DateTime()),
        sa.Column('end_at', sa.DateTime()),
        sa.Column('deleted_flag', sa.Enum('N', 'Y')),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('origin_filesize', sa.BigInteger()),
        sa.Column('target_filesize', sa.BigInteger()),
        sa.Column('lang', sa.String(32)),
        sa.Column('model', sa.String(64)),
        sa.Column('prompt', sa.String(1024)),
        sa.Column('api_url', sa.String(255)),
        sa.Column('api_key', sa.String(255)),
        sa.Column('threads', sa.Integer()),
        sa.Column('failed_reason', sa.Text()),
        sa.Column('failed_count', sa.Integer()),
        sa.Column('word_count', sa.Integer()),
        sa.Column('backup_model', sa.String(64)),
        sa.Column('md5', sa.String(32)),
        sa.Column('type', sa.String(64)),
        sa.Column('origin_lang', sa.String(32)),
        sa.Column('process', sa.Float(precision=5)),
        sa.Column('doc2x_flag', sa.Enum('N', 'Y')),
        sa.Column('doc2x_secret_key', sa.String(32)),
        sa.Column('prompt_id', sa.BigInteger()),
        sa.Column('comparison_id', sa.BigInteger()),
        sa.Column('size', sa.BigInteger()),
        sa.Column('server', sa.String(32)),
        sa.Column('app_id', sa.String(64)),
        sa.Column('app_key', sa.String(64)),
    )
    _create_table(
        'translate_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('md5_key', sa.String(100), nullable=False, unique=True),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('target_lang', sa.String(32)),
        sa.Column('model', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('prompt', sa.String(1024)),
        sa.Column('api_url', sa.String(255)),
        sa.Column('api_key', sa.String(255)),
        sa.Column('word_count', sa.Integer()),
        sa.Column('backup_model', sa.String(64)),
    )
    _create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255)),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('deleted_flag', sa.Enum('N', 'Y')),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )


def downgrade():
    for table_name in (
        'user', 'translate_logs', 'translate', 'setting', 'sessions',
        'send_code', 'prompt_fav', 'prompt', 'password_reset_tokens',
        'migrations', 'message', 'mcp_api_key', 'jobs', 'job_batches',
        'failed_jobs', 'customer', 'comparison_fav', 'comparison',
        'cache_locks', 'cache',
    ):
        op.drop_table(table_name)
