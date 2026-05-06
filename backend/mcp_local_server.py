"""
DocTranslator 本地 MCP 服务器 (stdio 传输)

本地 MCP 可以直接读取本地文件进行翻译，无需手动 Base64 编码。
翻译配置有两种来源：
1. 环境变量（优先）：API_URL, API_KEY, MODEL 等
2. 远程 MCP Key 配置：如果环境变量未设置，使用 MCP Key 中保存的配置

使用方法：
无需手动安装依赖，首次运行会自动安装。
在 Claude Desktop 的 claude_desktop_config.json 中添加：

{
  "mcpServers": {
    "doctranslator": {
      "command": "python",
      "args": ["mcp_local_server.py"],
      "env": {
        "DOCTRANSLATOR_URL": "https://your-domain.com:5002",
        "DOCTRANSLATOR_API_KEY": "dtk_xxxxx",
        "API_URL": "https://api.openai.com",
        "API_KEY": "sk-xxxx",
        "MODEL": "gpt-4o",
        "TYPE": "trans_all_only_inherit",
        "PROMPT_ID": "0",
        "BACKUP_MODEL": "",
        "THREADS": "5",
        "LANG": "中文",
        "COMPARISON_ID": "",
        "DOC2X_FLAG": "N",
        "DOC2X_SECRET_KEY": ""
      }
    }
  }
}

注意：如果 DOCTRANSLATOR_API_KEY 对应的 MCP Key 已经配置了翻译参数，
      则环境变量中的 API_URL/API_KEY/MODEL 等可以不填，会自动使用 Key 中的配置。
"""

import subprocess
import sys

def _ensure_deps():
    deps = ["fastmcp>=2.0.0", "requests>=2.28.0"]
    missing = []
    for dep in deps:
        pkg = dep.split(">=")[0].split("==")[0].split("[")[0]
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(dep)
    if missing:
        sys.stderr.write(f"正在安装依赖: {', '.join(missing)} ...\n")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

_ensure_deps()

import os
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
        "你可以直接翻译本地文件（提供文件路径即可）、查询翻译进度、下载翻译结果。"
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

    if hasattr(result, 'data') and result.data:
        return result.data

    content_list = []
    if hasattr(result, 'content') and result.content:
        for item in result.content:
            if hasattr(item, 'text') and item.text:
                try:
                    parsed = json.loads(item.text)
                    if isinstance(parsed, dict):
                        return parsed
                    content_list.append(item.text)
                except (json.JSONDecodeError, TypeError):
                    content_list.append(item.text)

    if content_list:
        return {"result": "\n".join(content_list)}
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
    翻译本地文档文件。直接提供本地文件路径，无需手动编码。

    Args:
        file_path: 本地文件绝对路径
        target_lang: 目标语言（中文/英语/日语等），不填使用默认配置
        origin_lang: 源语言，不填则自动检测
        translate_type: 翻译类型，不填使用默认配置
        comparison_id: 术语库ID
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
    通过URL下载文件并翻译。

    Args:
        file_url: 文件下载链接
        file_name: 文件名（可选，不填则从URL推断）
        target_lang: 目标语言
        origin_lang: 源语言
        translate_type: 翻译类型
        comparison_id: 术语库ID
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
    查询翻译任务状态。

    Args:
        task_id: 翻译任务ID
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
    列出翻译历史记录。

    Args:
        page: 页码
        limit: 每页数量
        status: 按状态过滤
        keyword: 关键词搜索
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
    下载翻译结果文件，返回Base64编码内容。

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
    删除翻译记录。

    Args:
        task_id: 翻译任务ID
    """
    try:
        return await _call_remote_tool("delete_translate", {"task_id": task_id})
    except Exception as e:
        return {"error": f"删除失败: {str(e)}"}


@mcp.tool
async def list_comparisons() -> dict:
    """获取术语库列表。"""
    try:
        return await _call_remote_tool("list_comparisons", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def list_prompts() -> dict:
    """获取提示词模板列表。"""
    try:
        return await _call_remote_tool("list_prompts", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def get_account_info() -> dict:
    """获取当前账户信息。"""
    try:
        return await _call_remote_tool("get_account_info", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


@mcp.tool
async def get_supported_formats() -> dict:
    """获取支持的文件格式列表。"""
    try:
        return await _call_remote_tool("get_supported_formats", {})
    except Exception as e:
        return {"error": f"查询失败: {str(e)}"}


if __name__ == "__main__":
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