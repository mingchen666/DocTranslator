#!/bin/sh
set -eu

python migrate_startup.py

python mcp_server.py &
mcp_pid=$!
cleanup() {
    kill "$mcp_pid" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

exec gunicorn --bind 0.0.0.0:5000 --workers 4 --preload \
    --timeout 120 --access-logfile - run:app
