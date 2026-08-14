#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "🔄 开始更新 DocTranslator"
echo "=========================================="

if [[ -n "$(git status --porcelain)" ]]; then
    echo "❌ 工作区存在未提交或未跟踪的文件；请先提交、暂存或清理后再更新。" >&2
    exit 1
fi

echo "📥 正在从 GitHub 拉取最新代码..."
git pull --ff-only origin main

echo "🚀 使用最新代码重新部署全部服务..."
exec bash "$PROJECT_ROOT/deploy.sh"
