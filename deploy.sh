#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/backend/.env}"
STORAGE_DIR="${STORAGE_DIR:-$PROJECT_ROOT/backend-storage}"
DB_DIR="${DB_DIR:-$PROJECT_ROOT/backend/db}"
NETWORK_NAME="${NETWORK_NAME:-my-network}"
IMAGE_NAME="${IMAGE_NAME:-doctranslator}"

require_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ 未找到环境配置文件: $ENV_FILE" >&2
    echo "请先复制 backend/.env.example 为 backend/.env 并完成生产配置。" >&2
    exit 1
  fi
}

get_queue_backend() {
  local value
  value="$(get_env_value TRANSLATION_QUEUE_BACKEND)"
  printf '%s\n' "${value:-database}" | tr '[:upper:]' '[:lower:]'
}

get_result_storage_backend() {
  local value
  value="$(get_env_value RESULT_STORAGE_BACKEND)"
  printf '%s\n' "${value:-local}" | tr '[:upper:]' '[:lower:]'
}

get_env_value() {
  local key="$1"
  local line
  local value
  line="$(grep -E "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE" | head -n 1 || true)"
  value="${line#*=}"
  value="${value%%#*}"
  value="$(printf '%s' "$value" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  if [[ "$value" == \"*\" && "$value" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s\n' "$value"
}

require_production_secret() {
  local key="$1"
  local value
  value="$(get_env_value "$key")"
  case "$value" in
    ''|your-secret-key|dev-key|fallback-secret-key|change-me-before-startup|sxxxxxx)
      echo "❌ $key 未设置为安全的生产随机值。请在 $ENV_FILE 中配置后重试。" >&2
      exit 1
      ;;
  esac
}

require_production_environment() {
  local value
  value="$(get_env_value FLASK_ENV)"
  value="$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')"
  if [[ "$value" != "production" ]]; then
    echo "❌ FLASK_ENV 必须设置为 production；部署脚本不允许以开发模式发布。" >&2
    exit 1
  fi
}

require_production_database_url() {
  local value
  value="$(get_env_value PROD_DATABASE_URL)"
  case "$value" in
    ''|mysql+pymysql://user:pwd@localhost/xxxx|mysql://user:password@localhost/prod_db\?charset=utf8mb4)
      echo "❌ PROD_DATABASE_URL 未设置为可用的生产数据库地址。请在 $ENV_FILE 中配置后重试。" >&2
      exit 1
      ;;
  esac
}

require_env_value() {
  local key="$1"
  if [[ -z "$(get_env_value "$key")" ]]; then
    echo "❌ $key 不能为空；请在 $ENV_FILE 中配置后重试。" >&2
    exit 1
  fi
}

validate_deployment_config() {
  local broker_url
  local storage_backend

  require_production_environment
  require_production_secret SECRET_KEY
  require_production_secret JWT_SECRET_KEY
  require_production_database_url

  case "$QUEUE_BACKEND" in
    celery)
      require_env_value CELERY_BROKER_URL
      broker_url="$(get_env_value CELERY_BROKER_URL)"
      case "$broker_url" in
        redis://*|rediss://*)
          ;;
        *)
          echo "❌ CELERY_BROKER_URL 必须是 redis:// 或 rediss:// 地址。" >&2
          exit 1
          ;;
      esac
      ;;
  esac

  storage_backend="$(get_result_storage_backend)"
  case "$storage_backend" in
    oss)
      require_env_value OSS_ENDPOINT
      require_env_value OSS_BUCKET
      require_env_value OSS_ACCESS_KEY_ID
      require_env_value OSS_ACCESS_KEY_SECRET
      ;;
    ''|local)
      ;;
    *)
      echo "❌ RESULT_STORAGE_BACKEND 必须是 local 或 oss。" >&2
      exit 1
      ;;
  esac
}

ensure_network() {
  if ! docker network inspect "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "   -> 创建网络 $NETWORK_NAME..."
    docker network create "$NETWORK_NAME" >/dev/null
  else
    echo "   -> 网络 $NETWORK_NAME 已存在，跳过创建。"
  fi
}

cleanup_containers() {
  local name
  for name in \
    backend-container \
    backend-worker-container \
    doctranslator-redis \
    doctranslator-celery-document \
    doctranslator-celery-pdf \
    nginx-container; do
    docker rm -f "$name" >/dev/null 2>&1 || true
  done
}

start_backend() {
  echo "🌐 启动后端容器..."
  docker run -d \
    --name backend-container \
    --env-file "$ENV_FILE" \
    --network "$NETWORK_NAME" \
    -p 5000:5000 \
    -p 5001:5001 \
    -v "$DB_DIR:/app/db" \
    -v "$STORAGE_DIR:/app/storage" \
    "$IMAGE_NAME" >/dev/null
}

wait_for_backend() {
  local attempt
  echo "⏳ 等待后端完成迁移并就绪..."
  for attempt in $(seq 1 60); do
    if docker exec backend-container python -c \
      "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/translate/test', timeout=2)" \
      >/dev/null 2>&1; then
      return
    fi
    sleep 2
  done

  echo "❌ 后端在 120 秒内未就绪，以下为最后 50 行日志：" >&2
  docker logs --tail 50 backend-container >&2 || true
  exit 1
}

start_database_worker() {
  echo "⚙️  启动数据库队列 worker..."
  docker run -d \
    --name backend-worker-container \
    --env-file "$ENV_FILE" \
    --network "$NETWORK_NAME" \
    -v "$DB_DIR:/app/db" \
    -v "$STORAGE_DIR:/app/storage" \
    "$IMAGE_NAME" python worker.py >/dev/null
}

start_redis() {
  local attempt

  echo "⚙️  启动 Redis..."
  docker run -d \
    --name doctranslator-redis \
    --network "$NETWORK_NAME" \
    --network-alias redis \
    -v doctranslator-redis-data:/data \
    redis:7-alpine redis-server --appendonly yes >/dev/null

  for attempt in $(seq 1 30); do
    if [[ "$(docker exec doctranslator-redis redis-cli ping 2>/dev/null || true)" == "PONG" ]]; then
      break
    fi
    sleep 1
  done
  if [[ "$(docker exec doctranslator-redis redis-cli ping 2>/dev/null || true)" != "PONG" ]]; then
    echo "❌ Redis 在 30 秒内未就绪。" >&2
    docker logs --tail 50 doctranslator-redis >&2 || true
    exit 1
  fi
}

start_celery_workers() {
  echo "⚙️  启动 Celery workers..."

  docker run -d \
    --name doctranslator-celery-document \
    --env-file "$ENV_FILE" \
    --network "$NETWORK_NAME" \
    -v "$DB_DIR:/app/db" \
    -v "$STORAGE_DIR:/app/storage" \
    "$IMAGE_NAME" celery -A app.celery_app:celery worker \
      --queues=translation.default --concurrency=2 --hostname=document@%h >/dev/null

  docker run -d \
    --name doctranslator-celery-pdf \
    --env-file "$ENV_FILE" \
    --network "$NETWORK_NAME" \
    -v "$DB_DIR:/app/db" \
    -v "$STORAGE_DIR:/app/storage" \
    "$IMAGE_NAME" celery -A app.celery_app:celery worker \
      --queues=translation.pdf --concurrency=1 --hostname=pdf@%h >/dev/null
}

start_nginx() {
  echo "🌍 启动 Nginx 容器..."
  docker run -d \
    --name nginx-container \
    -p 1475:80 \
    -p 8081:8081 \
    -v "$PROJECT_ROOT/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro" \
    -v "$PROJECT_ROOT/frontend/dist:/usr/share/nginx/html/frontend:ro" \
    -v "$PROJECT_ROOT/admin/dist:/usr/share/nginx/html/admin:ro" \
    --network "$NETWORK_NAME" \
    nginx:stable-alpine >/dev/null
}

echo "=========================================="
echo "🚀 开始一键部署 DocTranslator"
echo "=========================================="

require_env_file
QUEUE_BACKEND="$(get_queue_backend)"
case "$QUEUE_BACKEND" in
  database|celery)
    ;;
  *)
    echo "❌ TRANSLATION_QUEUE_BACKEND 必须是 database 或 celery，当前为: $QUEUE_BACKEND" >&2
    exit 1
    ;;
esac
validate_deployment_config

echo "📡 检查 Docker 网络..."
ensure_network

echo "📁 创建本地数据目录..."
mkdir -p "$STORAGE_DIR" "$DB_DIR"

echo "🔨 构建后端 Docker 镜像..."
docker build -t "$IMAGE_NAME" "$PROJECT_ROOT/backend"

echo "🧹 清理旧容器..."
cleanup_containers

if [[ "$QUEUE_BACKEND" == "celery" ]]; then
  start_redis
fi

start_backend
wait_for_backend

case "$QUEUE_BACKEND" in
  database)
    start_database_worker
    ;;
  celery)
    start_celery_workers
    ;;
esac

start_nginx

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "前端地址: http://localhost:1475"
echo "管理端地址: http://localhost:8081"
echo "后端 API: http://localhost:5000"
echo "任务队列后端: $QUEUE_BACKEND"
echo "=========================================="
