import os
import logging
import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator

logging.basicConfig(level=logging.INFO)
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
        with flask_app_context() as app:
            import inspect
            sig = inspect.signature(func)
            if 'app' in sig.parameters and 'app' not in kwargs:
                kwargs['app'] = app
            return func(*args, **kwargs)
    return wrapper


async def _run_in_thread(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token, TokenClaim
from app.mcp.auth import McpApiKeyAuthProvider

user_mcp = FastMCP(
    "DocTranslator-User",
    auth=McpApiKeyAuthProvider(scope='user'),
    instructions=(
        "DocTranslator 文档翻译服务。"
        "你可以翻译文档、查询翻译进度、管理术语库和提示词模板。"
        "api_url/api_key/model 等翻译配置由 MCP 密钥自动提供，无需每次传入。"
    ),
)

admin_mcp = FastMCP(
    "DocTranslator-Admin",
    auth=McpApiKeyAuthProvider(scope='admin'),
    instructions=(
        "DocTranslator 管理后台MCP服务。"
        "你可以查看翻译统计、管理用户、管理翻译任务、修改系统设置。"
    ),
)


# ==================== 用户端 Tools ====================

@user_mcp.tool()
async def translate_file(
    file_name: str = "",
    file_content: str = "",
    file_url: str = "",
    target_lang: str = "",
    origin_lang: str = "",
    translate_type: str = "",
    comparison_id: int = 0,
) -> dict:
    """翻译文档文件。提供文件名和文件内容（Base64编码）或文件下载链接即可启动翻译任务。

    Args:
        file_name: 文件名（含扩展名），如 report.docx。使用 file_content 时必填。
        file_content: 文件内容的 Base64 编码字符串。与 file_url 至少提供一个。
        file_url: 文件下载链接URL。与 file_content 至少提供一个。
        target_lang: 目标翻译语言，如"中文"、"英语"、"日语"等。不填则使用密钥配置中的默认语言。
        origin_lang: 源语言。不填则自动检测。
        translate_type: 翻译类型。可选值：trans_all_only_inherit（全译继承格式）、trans_all_only（全译不继承）、trans_partial_only_inherit（部分翻译继承）、trans_partial_only（部分翻译不继承）。不填则使用密钥配置中的默认类型。
        comparison_id: 术语库ID。不填则使用密钥配置中的默认术语库。
    """
    from app.mcp.tools import translate_file as _translate_file
    token = get_access_token()
    config = token.claims.get('config', {})
    customer_id = int(token.claims.get('customer_id', 0))
    if target_lang:
        config['lang'] = target_lang
    if origin_lang:
        config['origin_lang'] = origin_lang
    if translate_type:
        config['type'] = translate_type
    if comparison_id:
        config['comparison_id'] = comparison_id
    func = _run_sync(_translate_file)
    return await _run_in_thread(func, config=config, customer_id=customer_id,
                                 file_content=file_content, file_url=file_url,
                                 file_name=file_name, target_lang=target_lang,
                                 origin_lang=origin_lang, translate_type=translate_type,
                                 comparison_id=comparison_id)


@user_mcp.tool()
async def query_translate_status(task_id: int) -> dict:
    """查询翻译任务的状态和进度。返回任务ID、状态、进度百分比、耗时等信息。

    Args:
        task_id: 翻译任务ID（启动翻译时返回的 task_id 字段值）
    """
    from app.mcp.tools import query_translate_status as _query
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_query)
    return await _run_in_thread(func, customer_id=customer_id, task_id=task_id)


@user_mcp.tool()
async def list_translates(page: int = 1, limit: int = 20, status: str = "", keyword: str = "") -> dict:
    """列出当前用户的翻译历史记录。返回任务列表，包含任务ID、文件名、状态、进度等。

    Args:
        page: 页码，从1开始。默认第1页。
        limit: 每页数量。默认20条。
        status: 按状态过滤。可选值：none（未开始）、process（进行中）、done（已完成）、failed（失败）。不填则返回所有状态。
        keyword: 按文件名关键词搜索。不填则不筛选。
    """
    from app.mcp.tools import list_translates as _list
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_list)
    return await _run_in_thread(func, customer_id=customer_id, page=page, limit=limit, status=status, keyword=keyword)


@user_mcp.tool()
async def download_translate(task_id: int) -> dict:
    """下载翻译结果文件。仅已完成（done）状态的任务可下载。返回 Base64 编码的文件内容。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import download_translate as _download
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_download)
    return await _run_in_thread(func, customer_id=customer_id, task_id=task_id)


@user_mcp.tool()
async def delete_translate(task_id: int) -> dict:
    """删除一条翻译记录。删除后释放该文件占用的存储空间。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import delete_translate as _delete
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_delete)
    return await _run_in_thread(func, customer_id=customer_id, task_id=task_id)


@user_mcp.tool()
async def restart_translate(task_id: int) -> dict:
    """重新启动一个失败或未开始的翻译任务。仅状态为 failed 或 none 的任务可重启。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import restart_translate as _restart
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_restart)
    return await _run_in_thread(func, customer_id=customer_id, task_id=task_id)


@user_mcp.tool()
async def list_comparisons() -> dict:
    """列出当前用户的所有术语库。返回术语库ID、名称、源语言、目标语言、术语数量等信息。"""
    from app.mcp.tools import list_comparisons as _list
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_list)
    return await _run_in_thread(func, customer_id=customer_id)


@user_mcp.tool()
async def list_prompts() -> dict:
    """列出当前用户的所有提示词模板。返回模板ID、名称、是否共享等信息。"""
    from app.mcp.tools import list_prompts as _list
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_list)
    return await _run_in_thread(func, customer_id=customer_id)


@user_mcp.tool()
async def get_account_info() -> dict:
    """获取当前用户的账户信息。返回邮箱、姓名、等级、已用存储空间、总存储空间等。"""
    from app.mcp.tools import get_account_info as _info
    token = get_access_token()
    customer_id = int(token.claims.get('customer_id', 0))
    func = _run_sync(_info)
    return await _run_in_thread(func, customer_id=customer_id)


@user_mcp.tool()
async def get_supported_formats() -> dict:
    """获取系统支持的文件格式列表和最大文件大小限制。支持 docx、xlsx、pptx、pdf 等格式。"""
    from app.mcp.tools import get_supported_formats as _formats
    func = _run_sync(_formats)
    return await _run_in_thread(func)


# ==================== 管理员端 Tools ====================

@admin_mcp.tool()
async def get_statistics() -> dict:
    """获取系统翻译统计数据。返回总用户数、总翻译数、各状态翻译数、总存储用量等。"""
    from app.mcp.tools import get_statistics as _stats
    func = _run_sync(_stats)
    return await _run_in_thread(func)


@admin_mcp.tool()
async def list_customers(page: int = 1, limit: int = 20, search: str = "") -> dict:
    """列出所有客户信息。返回客户ID、邮箱、姓名、等级、存储用量等。

    Args:
        page: 页码，从1开始。默认第1页。
        limit: 每页数量。默认20条。
        search: 按邮箱或姓名关键词搜索。不填则返回全部。
    """
    from app.mcp.tools import list_customers as _list
    func = _run_sync(_list)
    return await _run_in_thread(func, page=page, limit=limit, search=search)


@admin_mcp.tool()
async def update_customer(customer_id: int, level: str = "", add_storage_mb: int = 0, status: str = "") -> dict:
    """修改客户信息。可调整等级、增加存储空间、启用/禁用账户。

    Args:
        customer_id: 客户ID（必填）
        level: 客户等级。可选值：common（普通）、vip。不填则不修改。
        add_storage_mb: 为客户增加的存储空间大小（MB）。0表示不修改。
        status: 客户状态。可选值：enabled（启用）、disabled（禁用）。不填则不修改。
    """
    from app.mcp.tools import update_customer as _update
    func = _run_sync(_update)
    return await _run_in_thread(func, customer_id=customer_id, level=level,
                                 add_storage_mb=add_storage_mb, status=status)


@admin_mcp.tool()
async def admin_list_translates(page: int = 1, limit: int = 20, status: str = "", keyword: str = "") -> dict:
    """管理员查看所有用户的翻译记录。返回翻译编号、客户ID、文件名、状态、进度等。

    Args:
        page: 页码，从1开始。默认第1页。
        limit: 每页数量。默认20条。
        status: 按状态过滤。可选值：none（未开始）、process（进行中）、done（已完成）、failed（失败）。不填则返回所有状态。
        keyword: 按文件名或翻译编号关键词搜索。不填则不筛选。
    """
    from app.mcp.tools import admin_list_translates as _list
    func = _run_sync(_list)
    return await _run_in_thread(func, page=page, limit=limit, status=status, keyword=keyword)


@admin_mcp.tool()
async def admin_restart_translate(task_id: int) -> dict:
    """重新启动一个失败或未开始的翻译任务。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import admin_restart_translate as _restart
    func = _run_sync(_restart)
    return await _run_in_thread(func, task_id=task_id)


@admin_mcp.tool()
async def admin_delete_translate(task_id: int) -> dict:
    """管理员删除任意翻译记录。删除后释放该文件占用的存储空间。

    Args:
        task_id: 翻译任务ID
    """
    from app.mcp.tools import admin_delete_translate as _delete
    func = _run_sync(_delete)
    return await _run_in_thread(func, task_id=task_id)


@admin_mcp.tool()
async def get_system_settings() -> dict:
    """获取系统全局设置。返回所有配置项，按分组组织。"""
    from app.mcp.tools import get_system_settings as _settings
    func = _run_sync(_settings)
    return await _run_in_thread(func)


@admin_mcp.tool()
async def get_storage_info() -> dict:
    """获取系统存储详情。返回总用户存储用量、总翻译数、存储目录路径等。"""
    from app.mcp.tools import get_storage_info as _info
    func = _run_sync(_info)
    return await _run_in_thread(func)


# ==================== 创建 ASGI 应用 ====================

def create_mcp_starlette():
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware

    user_app = user_mcp.http_app(path="/", stateless_http=True)
    admin_app = admin_mcp.http_app(path="/", stateless_http=True)

    user_lifespan = getattr(user_app, 'lifespan', None)
    admin_lifespan = getattr(admin_app, 'lifespan', None)

    mcp_lifespans = []
    if user_lifespan:
        mcp_lifespans.append(user_lifespan)
    if admin_lifespan:
        mcp_lifespans.append(admin_lifespan)

    @asynccontextmanager
    async def combined_lifespan(app: Starlette) -> AsyncGenerator[None, None]:
        import contextlib
        async with contextlib.AsyncExitStack() as stack:
            for lf in mcp_lifespans:
                try:
                    await stack.enter_async_context(lf(app))
                except Exception as e:
                    logger.warning(f"MCP lifespan启动失败: {e}")
            yield

    starlette_app = Starlette(
        routes=[
            Mount("/mcp/user", app=user_app),
            Mount("/mcp/admin", app=admin_app),
        ],
        lifespan=combined_lifespan if mcp_lifespans else None,
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        ],
    )

    return starlette_app


if __name__ == "__main__":
    from app import create_app
    from app.mcp.auth import set_flask_app_for_auth

    flask_app = create_app()
    set_flask_app(flask_app)
    set_flask_app_for_auth(flask_app)

    import uvicorn
    port = int(os.environ.get("MCP_PORT", 5001))
    logger.info(f"MCP 服务器启动在端口 {port}")
    logger.info(f"  用户端: http://0.0.0.0:{port}/mcp/user")
    logger.info(f"  管理端: http://0.0.0.0:{port}/mcp/admin")

    app = create_mcp_starlette()
    uvicorn.run(app, host="0.0.0.0", port=port)
