import os
import logging
import asyncio
from typing import Optional
from contextlib import contextmanager
from fastmcp import FastMCP
from fastmcp.dependencies import CurrentAccessToken
from fastmcp.server.auth import AccessToken

from app.mcp.auth import McpApiKeyAuthProvider

logger = logging.getLogger(__name__)

_flask_app = None


def set_flask_app(app):
    global _flask_app
    _flask_app = app


def get_flask_app():
    if _flask_app:
        return _flask_app
    try:
        from flask import current_app
        return current_app._get_current_object()
    except RuntimeError:
        return None


@contextmanager
def flask_app_context():
    app = get_flask_app()
    if app is None:
        raise RuntimeError("Flask app 不可用")
    with app.app_context():
        yield app


def _run_sync(func):
    def wrapper(*args, **kwargs):
        with flask_app_context():
            return func(*args, **kwargs)
    return wrapper


async def _run_in_thread(func, *args):
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)
    except Exception as e:
        logger.error(f"MCP tool 执行失败: {e}", exc_info=True)
        return {'error': str(e)}


user_mcp = FastMCP(
    "DocTranslator-User",
    stateless_http=True,
    auth=McpApiKeyAuthProvider(scope='user'),
    instructions=(
        "DocTranslator 文档翻译服务。"
        "你可以翻译文档、查询翻译进度、管理术语库和提示词模板。"
        "api_url/api_key/model 等翻译配置由 MCP 密钥自动提供，无需每次传入。"
    ),
)


@user_mcp.tool
async def translate_file(
    file_content: Optional[str] = None,
    file_url: Optional[str] = None,
    file_name: str = "",
    target_lang: str = "",
    origin_lang: str = "",
    translate_type: str = "",
    comparison_id: Optional[int] = None,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    翻译文档文件。

    传文件方式（三选一）：
    - file_content: 文件Base64编码（推荐，适用于Claude Desktop等MCP客户端）
    - file_url: 文件下载URL（需公网可访问）
    - 两者都不传时，file_name 视为服务器本地绝对路径

    api_url/api_key/model/prompt_id/threads 等配置由你的MCP密钥自动提供，无需传入。

    Args:
        file_content: 文件内容的Base64编码
        file_url: 文件下载链接
        file_name: 原始文件名（含扩展名，如report.docx）
        target_lang: 目标语言（中文/英语/日语/韩语/法语/德语/西班牙语/俄语等），不填则使用MCP密钥配置中的默认语言
        origin_lang: 源语言（不填则自动检测）
        translate_type: 翻译类型 - trans_all_only_inherit(继承原版面,默认), trans_all_both_inherit(双语继承版面), trans_text_only(仅译文), trans_text_only_new(仅译文新排版)
        comparison_id: 术语库ID（可通过list_comparisons获取）
    """
    from app.mcp.tools import translate_file as do_translate

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])
    config = token.claims['config']

    @_run_sync
    def _do():
        app = get_flask_app()
        return do_translate(config, customer_id, app,
                            file_content, file_url, file_name,
                            target_lang, origin_lang, translate_type,
                            comparison_id)

    return await _run_in_thread(_do)


@user_mcp.tool
async def query_translate_status(
    task_id: Optional[int] = None,
    uuid: Optional[str] = None,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    查询翻译任务进度和状态。

    Args:
        task_id: 翻译任务ID（启动翻译时返回）
        uuid: 翻译任务UUID(推荐使用这个查询)
    """
    from app.mcp.tools import query_translate_status as do_query

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_query(customer_id, task_id, uuid)

    return await _run_in_thread(_do)


@user_mcp.tool
async def list_translates(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    获取翻译历史记录列表。

    Args:
        page: 页码，默认1
        limit: 每页数量，默认20
        status: 按状态过滤（none/process/done/failed）
    """
    from app.mcp.tools import list_translates as do_list

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_list(customer_id, page, limit, status)

    return await _run_in_thread(_do)


@user_mcp.tool
async def download_translate(
    task_id: int,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    下载翻译完成的文件，返回Base64编码的文件内容。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import download_translate as do_download

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_download(customer_id, task_id)

    return await _run_in_thread(_do)


@user_mcp.tool
async def delete_translate(
    task_id: int,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    删除翻译记录。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import delete_translate as do_delete

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_delete(customer_id, task_id)

    return await _run_in_thread(_do)


@user_mcp.tool
async def list_comparisons(
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """获取我的术语库列表。返回每个术语库的ID、标题、源语言、目标语言和术语数量。"""
    from app.mcp.tools import list_comparisons as do_list

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_list(customer_id)

    return await _run_in_thread(_do)


@user_mcp.tool
async def list_prompts(
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """获取我的提示词模板列表。返回每个模板的ID、标题和共享状态。"""
    from app.mcp.tools import list_prompts as do_list

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_list(customer_id)

    return await _run_in_thread(_do)


@user_mcp.tool
async def get_account_info(
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """获取当前账户信息，包括邮箱、会员等级、存储空间使用情况。"""
    from app.mcp.tools import get_account_info as do_get

    if not token:
        return {'error': '鉴权失败'}

    customer_id = int(token.claims['customer_id'])

    @_run_sync
    def _do():
        return do_get(customer_id)

    return await _run_in_thread(_do)


@user_mcp.tool
async def get_supported_formats() -> dict:
    """获取系统支持的文件翻译格式列表。"""
    from app.mcp.tools import get_supported_formats as do_get
    return do_get()


admin_mcp = FastMCP(
    "DocTranslator-Admin",
    stateless_http=True,
    auth=McpApiKeyAuthProvider(scope='admin'),
    instructions=(
        "DocTranslator 管理后台MCP服务。"
        "你可以查看翻译统计、管理用户、管理翻译任务、修改系统设置。"
    ),
)


@admin_mcp.tool
async def get_statistics(
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """获取翻译统计信息：总数、完成数、处理中、失败数。"""
    from app.models.translate import Translate

    @_run_sync
    def _do():
        total = Translate.query.count()
        done_count = Translate.query.filter_by(status='done').count()
        processing_count = Translate.query.filter_by(status='process').count()
        failed_count = Translate.query.filter_by(status='failed').count()
        return {
            'total': total,
            'done_count': done_count,
            'processing_count': processing_count,
            'failed_count': failed_count,
        }

    return await _run_in_thread(_do)


@admin_mcp.tool
async def list_customers(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    获取客户列表。

    Args:
        page: 页码
        limit: 每页数量
        search: 按邮箱搜索
    """
    from app.models.customer import Customer

    @_run_sync
    def _do():
        query = Customer.query.filter_by(deleted_flag='N')
        if search:
            query = query.filter(Customer.email.ilike(f"%{search}%"))
        pagination = query.paginate(page=page, per_page=limit, error_out=False)

        data = [{
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'level': c.level,
            'status': c.status,
            'storage_mb': round(c.storage / (1024 * 1024), 2),
            'total_storage_mb': round(c.total_storage / (1024 * 1024), 2),
        } for c in pagination.items]

        return {'data': data, 'total': pagination.total}

    return await _run_in_thread(_do)


@admin_mcp.tool
async def update_customer(
    customer_id: int,
    level: Optional[str] = None,
    add_storage_mb: Optional[int] = None,
    status: Optional[str] = None,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    更新客户信息。

    Args:
        customer_id: 客户ID
        level: 会员等级（common/vip）
        add_storage_mb: 追加存储空间（MB）
        status: 账户状态（enabled/disabled）
    """
    from app.extensions import db
    from app.models.customer import Customer

    @_run_sync
    def _do():
        customer = Customer.query.get(customer_id)
        if not customer:
            return {'error': '客户不存在'}

        if level and level in ('common', 'vip'):
            customer.level = level
        if add_storage_mb:
            customer.total_storage += add_storage_mb * 1024 * 1024
        if status and status in ('enabled', 'disabled'):
            customer.status = status

        db.session.commit()
        return {'message': '更新成功'}

    return await _run_in_thread(_do)


@admin_mcp.tool
async def admin_list_translates(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    获取所有翻译记录（管理员视图）。

    Args:
        page: 页码
        limit: 每页数量
        status: 按状态过滤
        keyword: 按文件名搜索
    """
    from app.models.translate import Translate
    from app.models.customer import Customer

    @_run_sync
    def _do():
        query = Translate.query.filter_by(deleted_flag='N')
        if status and status in ('none', 'process', 'done', 'failed'):
            query = query.filter_by(status=status)
        if keyword:
            query = query.filter(Translate.origin_filename.ilike(f"%{keyword}%"))

        pagination = query.order_by(Translate.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )

        status_map = {'none': '未开始', 'process': '进行中', 'done': '已完成', 'failed': '失败'}
        data = []
        for t in pagination.items:
            customer = Customer.query.get(t.customer_id)
            data.append({
                'task_id': t.id,
                'file_name': t.origin_filename,
                'status': t.status,
                'status_name': status_map.get(t.status, '未知'),
                'progress': float(t.process),
                'customer_email': customer.email if customer else '未知',
                'target_lang': t.lang,
                'model': t.model,
            })

        return {'data': data, 'total': pagination.total}

    return await _run_in_thread(_do)


@admin_mcp.tool
async def admin_restart_translate(
    task_id: int,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    重启失败的翻译任务。

    Args:
        task_id: 翻译任务ID
    """
    from app.extensions import db
    from app.models.translate import Translate

    @_run_sync
    def _do():
        record = Translate.query.get(task_id)
        if not record:
            return {'error': '翻译记录不存在'}
        if record.status not in ('failed', 'done'):
            return {'error': f'当前状态 {record.status} 无法重启'}

        record.status = 'none'
        record.start_at = None
        record.end_at = None
        record.failed_reason = None
        db.session.commit()
        return {'message': '任务已重启'}

    return await _run_in_thread(_do)


@admin_mcp.tool
async def admin_delete_translate(
    task_id: int,
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """
    删除翻译记录。

    Args:
        task_id: 翻译任务ID
    """
    from app.extensions import db
    from app.models.translate import Translate

    @_run_sync
    def _do():
        record = Translate.query.get(task_id)
        if not record:
            return {'error': '翻译记录不存在'}
        db.session.delete(record)
        db.session.commit()
        return {'message': '记录删除成功'}

    return await _run_in_thread(_do)


@admin_mcp.tool
async def get_system_settings(
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """获取系统设置：API配置、默认模型、线程数等。"""
    from app.models.setting import Setting

    @_run_sync
    def _do():
        settings = Setting.query.filter(
            Setting.group.in_(['api_setting', 'other_setting']),
            Setting.deleted_flag == 'N'
        ).all()

        result = {}
        for s in settings:
            result[s.alias] = s.value
        return result

    return await _run_in_thread(_do)


@admin_mcp.tool
async def get_storage_info(
    token: AccessToken = CurrentAccessToken(),
) -> dict:
    """获取系统存储空间使用详情。"""

    @_run_sync
    def _do():
        app = get_flask_app()
        base_dir = os.path.dirname(app.root_path)
        storage_path = os.path.join(base_dir, 'storage')

        if not os.path.exists(storage_path):
            return {'error': 'storage目录不存在'}

        result = {}
        for category in os.listdir(storage_path):
            category_path = os.path.join(storage_path, category)
            if not os.path.isdir(category_path):
                continue
            total_size = 0
            file_count = 0
            for root, _, files in os.walk(category_path):
                for f in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                        file_count += 1
                    except OSError:
                        continue
            result[category] = {
                'size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
            }
        return result

    return await _run_in_thread(_do)


def create_mcp_apps():
    user_app = user_mcp.streamable_http_app(streamable_http_path="/")
    admin_app = admin_mcp.streamable_http_app(streamable_http_path="/")
    return user_app, admin_app
