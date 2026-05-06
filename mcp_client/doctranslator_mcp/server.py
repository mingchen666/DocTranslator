import os
import sys
import json
import base64
import logging
from typing import Optional

from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

REMOTE_URL = os.environ.get("DOCTRANSLATOR_URL", "").rstrip("/")
API_KEY = os.environ.get("DOCTRANSLATOR_API_KEY", "")

ENV_CONFIG = {
    "api_url": os.environ.get("API_URL", ""),
    "api_key": os.environ.get("API_KEY", ""),
    "model": os.environ.get("MODEL", ""),
    "type": os.environ.get("TYPE", "trans_all_only_inherit"),
    "prompt_id": int(os.environ.get("PROMPT_ID", "0")),
    "backup_model": os.environ.get("BACKUP_MODEL", ""),
    "threads": int(os.environ.get("THREADS", "5")),
    "lang": os.environ.get("LANG", "中文"),
    "comparison_id": os.environ.get("COMPARISON_ID") or None,
    "doc2x_flag": os.environ.get("DOC2X_FLAG", "N"),
    "doc2x_secret_key": os.environ.get("DOC2X_SECRET_KEY", ""),
}


def _has_env_config():
    return bool(ENV_CONFIG.get("api_url") and ENV_CONFIG.get("api_key") and ENV_CONFIG.get("model"))


mcp = FastMCP(
    "DocTranslator-Local",
    instructions=(
        "DocTranslator 文档翻译本地服务。"
        "你可以直接翻译本地文件（提供文件路径即可）或通过URL翻译文件，还可以查询翻译进度、下载翻译结果。"
        "翻译配置来自环境变量或 MCP Key 中保存的配置，无需每次传入。"
    ),
)


async def _call_remote_tool(tool_name: str, arguments: dict) -> dict:
    transport = StreamableHttpTransport(
        url=f"{REMOTE_URL}/mcp/user",
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    client = Client(transport)

    async with client:
        result = await client.call_tool(tool_name, arguments)

    if hasattr(result, 'data') and result.data is not None:
        if isinstance(result.data, dict):
            return result.data
        try:
            parsed = json.loads(result.data)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    if hasattr(result, 'content') and result.content:
        for item in result.content:
            if hasattr(item, 'text') and item.text:
                try:
                    parsed = json.loads(item.text)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    return {"result": item.text}

    return {"result": str(result)}


@mcp.tool
async def translate_file(
    file_path: str,
    target_lang: str = "",
    origin_lang: str = "",
    translate_type: str = "",
    comparison_id: Optional[int] = None,
) -> dict:
    """
    翻译本地文档文件。直接提供本地文件路径即可，无需手动编码。

    Args:
        file_path: 本地文件绝对路径，如 /Users/user/Documents/report.docx
        target_lang: 目标翻译语言，如"中文"、"英语"、"日语"等。不填则使用默认配置。
        origin_lang: 源语言。不填则自动检测。
        translate_type: 翻译类型。可选值：trans_all_only_inherit（全译继承格式）、trans_all_only（全译不继承）、trans_partial_only_inherit（部分翻译继承）、trans_partial_only（部分翻译不继承）。不填则使用默认配置。
        comparison_id: 术语库ID。不填则使用默认配置。
    """
    if not os.path.exists(file_path):
        return {"error": f"文件不存在: {file_path}"}

    with open(file_path, "rb") as f:
        file_content = base64.b64encode(f.read()).decode()

    file_name = os.path.basename(file_path)

    args = {
        "file_name": file_name,
        "file_content": file_content,
    }
    if target_lang:
        args["target_lang"] = target_lang
    if origin_lang:
        args["origin_lang"] = origin_lang
    if translate_type:
        args["translate_type"] = translate_type
    if comparison_id:
        args["comparison_id"] = comparison_id

    try:
        return await _call_remote_tool("translate_file", args)
    except Exception as e:
        logger.error(f"翻译调用失败: {e}")
        return {"error": f"翻译调用失败: {str(e)}"}


@mcp.tool
async def translate_by_url(
    file_url: str,
    file_name: str = "",
    target_lang: str = "",
    origin_lang: str = "",
    translate_type: str = "",
    comparison_id: Optional[int] = None,
) -> dict:
    """
    通过URL下载文件并翻译。适用于在线文档或可公开访问的文件链接。

    Args:
        file_url: 文件下载链接URL
        file_name: 文件名（含扩展名），不填则从URL推断
        target_lang: 目标翻译语言，如"中文"、"英语"、"日语"等。不填则使用默认配置。
        origin_lang: 源语言。不填则自动检测。
        translate_type: 翻译类型。可选值：trans_all_only_inherit（全译继承格式）、trans_all_only（全译不继承）、trans_partial_only_inherit（部分翻译继承）、trans_partial_only（部分翻译不继承）。不填则使用默认配置。
        comparison_id: 术语库ID。不填则使用默认配置。
    """
    args = {
        "file_url": file_url,
        "file_name": file_name,
    }
    if target_lang:
        args["target_lang"] = target_lang
    if origin_lang:
        args["origin_lang"] = origin_lang
    if translate_type:
        args["translate_type"] = translate_type
    if comparison_id:
        args["comparison_id"] = comparison_id

    try:
        return await _call_remote_tool("translate_file", args)
    except Exception as e:
        logger.error(f"URL翻译调用失败: {e}")
        return {"error": f"翻译调用失败: {str(e)}"}


@mcp.tool
async def query_translate_status(task_id: int) -> dict:
    """
    查询翻译任务的状态和进度。返回任务ID、状态、进度百分比、耗时等信息。

    Args:
        task_id: 翻译任务ID（启动翻译时返回的 task_id 字段值）
    """
    try:
        return await _call_remote_tool("query_translate_status", {"task_id": task_id})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def list_translates(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
) -> dict:
    """
    列出翻译历史记录。返回任务列表，包含任务ID、文件名、状态、进度等。

    Args:
        page: 页码，从1开始。默认第1页。
        limit: 每页数量。默认20条。
        status: 按状态过滤。可选值：none（未开始）、process（进行中）、done（已完成）、failed（失败）。不填则返回所有状态。
        keyword: 按文件名关键词搜索。不填则不筛选。
    """
    args = {"page": page, "limit": limit}
    if status:
        args["status"] = status
    if keyword:
        args["keyword"] = keyword
    try:
        return await _call_remote_tool("list_translates", args)
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def download_translate(task_id: int) -> dict:
    """
    下载翻译结果文件。仅已完成（done）状态的任务可下载，返回 Base64 编码的文件内容。

    Args:
        task_id: 翻译任务ID
    """
    try:
        return await _call_remote_tool("download_translate", {"task_id": task_id})
    except Exception as e:
        return {"error": f"下载失败: {str(e)}"}


@mcp.tool
async def delete_translate(task_id: int) -> dict:
    """
    删除一条翻译记录。删除后释放该文件占用的存储空间。

    Args:
        task_id: 翻译任务ID
    """
    try:
        return await _call_remote_tool("delete_translate", {"task_id": task_id})
    except Exception as e:
        return {"error": f"删除失败: {str(e)}"}


@mcp.tool
async def restart_translate(task_id: int) -> dict:
    """
    重新启动一个失败或未开始的翻译任务。仅状态为 failed 或 none 的任务可重启。

    Args:
        task_id: 翻译任务ID
    """
    try:
        return await _call_remote_tool("restart_translate", {"task_id": task_id})
    except Exception as e:
        return {"error": f"重启失败: {str(e)}"}


@mcp.tool
async def list_comparisons() -> dict:
    """列出当前用户的所有术语库。返回术语库ID、名称、源语言、目标语言、术语数量等信息。"""
    try:
        return await _call_remote_tool("list_comparisons", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def list_prompts() -> dict:
    """列出当前用户的所有提示词模板。返回模板ID、名称、是否共享等信息。"""
    try:
        return await _call_remote_tool("list_prompts", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def get_account_info() -> dict:
    """获取当前用户的账户信息。返回邮箱、姓名、等级、已用存储空间、总存储空间等。"""
    try:
        return await _call_remote_tool("get_account_info", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def get_supported_formats() -> dict:
    """获取系统支持的文件格式列表和最大文件大小限制。支持 docx、xlsx、pptx、pdf 等格式。"""
    try:
        return await _call_remote_tool("get_supported_formats", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


def main():
    if not REMOTE_URL:
        sys.stderr.write("错误: 请设置 DOCTRANSLATOR_URL 环境变量（如 https://your-domain.com:5002）\n")
        sys.exit(1)
    if not API_KEY:
        sys.stderr.write("错误: 请设置 DOCTRANSLATOR_API_KEY 环境变量（如 dtk_xxxxx）\n")
        sys.exit(1)

    logger.info(f"本地 MCP 服务器启动，远程端点: {REMOTE_URL}/mcp/user")
    logger.info(f"API Key: {API_KEY[:12]}...")
    if _has_env_config():
        logger.info("翻译配置来源: 环境变量")
    else:
        logger.info("翻译配置来源: MCP Key 中保存的配置（环境变量未设置翻译参数）")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
