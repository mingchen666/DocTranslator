#!/bin/bash

# 设置脚本在遇到错误时立即退出
set -e

echo "=========================================="
echo "🔄 开始一键更新 DocTranslator"
echo "=========================================="

# 1. 拉取最新代码
echo "📥 正在从 GitHub 拉取最新代码..."
# 如果你有本地修改，这可能会失败。你需要先处理你的修改（如 git stash）。
git pull origin main

# 2. 停止并删除旧容器（为了用新镜像启动）
echo "🧹 清理旧容器..."
docker stop backend-container 2>/dev/null || true
docker rm backend-container 2>/dev/null || true
docker stop nginx-container 2>/dev/null || true
docker rm nginx-container 2>/dev/null || true

# 3. 用新代码重新构建后端镜像
echo "🔨 重新构建后端 Docker 镜像..."
docker build -t doctranslator ./backend

# 4. 启动后端容器
echo "🌐 启动后端容器..."
docker run -d \
  --name backend-container \
  --network my-network \
  -p 5000:5000 \
  -v ./backend-storage:/app/storage \
  doctranslator

# 5. 启动 Nginx 容器
echo "🌍 启动 Nginx 容器..."
docker run -d \
  --name nginx-container \
  -p 1475:80 \
  -p 8081:8081 \
  -v $(pwd)/nginx/nginx.conf:/etc/nginx/conf.d/default.conf \
  -v $(pwd)/frontend/dist:/usr/share/nginx/html/frontend \
  -v $(pwd)/admin/dist:/usr/share/nginx/html/admin \
  --network my-network \
  nginx:stable-alpine

echo ""
echo "=========================================="
echo "✅ 更新并重新部署完成！"
echo "=========================================="
echo "前端地址: http://localhost:1475"
echo "管理端地址: http://localhost:8081"
echo "后端 API: http://localhost:5000"
echo "=========================================="
