# doctranslator-local-mcp

DocTranslator 本地MCP服务器，支持通过MCP客户端（如 Claude Desktop）翻译本地文档文件。

## 功能

- 📄 翻译本地文件（提供文件路径即可）
- 🔗 通过 URL 翻译在线文档
- 📊 查询翻译进度和状态
- 📥 下载翻译结果
- 📚 管理术语库和提示词模板

## 快速开始

### uvx（推荐）


```json
{
  "mcpServers": {
    "doctranslator": {
      "command": "uvx",
      "args": ["doctranslator-local-mcp"],
      "env": {
        "DOCTRANSLATOR_URL": "https://your-domain.com",
        "DOCTRANSLATOR_API_KEY": "dtk_xxxxx"
      }
    }
  }
}
```

### pip

```bash
pip install doctranslator-local-mcp
doctranslator-local-mcp
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DOCTRANSLATOR_URL` | ✅ | 平台地址，如 `https://your-domain.com` |
| `DOCTRANSLATOR_API_KEY` | ✅ | 在平台生成的MCP Key，如 `dtk_xxxxx` |
| `API_URL` | ❌ | 翻译 API 地址，如 `https://api.ezworkapi.top` |
| `API_KEY` | ❌ | 翻译 API Key |
| `MODEL` | ❌ | 翻译模型，如 `gpt-4o` |
| `LANG` | ❌ | 默认目标语言，如 `中文`（默认） |
| `TYPE` | ❌ | 默认翻译类型（默认 `trans_all_only_inherit`） |
| `THREADS` | ❌ | 翻译线程数（默认 `5`） |
| `COMPARISON_ID` | ❌ | 默认术语库 ID |
| `PROMPT_ID` | ❌ | 默认提示词模板 ID |
| `DOC2X_FLAG` | ❌ | 启用 Doc2X（默认 `N`） |
| `DOC2X_SECRET_KEY` | ❌ | Doc2X 密钥 |

> 如果 MCP Key 已在平台上配置了翻译参数，则 `API_URL`/`API_KEY`/`MODEL` 等可以不填，会自动使用 Key 中的配置。

## 支持的文件格式

docx、xlsx、pptx、pdf、txt、md、csv、xls、doc、html、htm等

