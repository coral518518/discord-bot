#!/usr/bin/env bash
set -e

# If user passed custom command (e.g. bash, sh, etc.), execute directly
if [ "$#" -gt 0 ] && [ "$1" != "run" ]; then
    exec "$@"
fi

TARGET_MODE=$(echo "${MODE:-${ENGINE:-sb}}" | tr '[:upper:]' '[:lower:]')

echo "========================================================"
echo " >> Discord Bot Worker Service Initializing..."
echo " >> Target Profile: ${TARGET_MODE}"
echo "========================================================"

cd /app

# 1. If compiled Nuitka standalone binary exists, run binary directly (ultra-fast, zero Python overhead)
if [ -f "/app/discord-bot-worker" ]; then
    echo ">> Running compiled native binary: /app/discord-bot-worker"
    exec /app/discord-bot-worker
fi

# 2. Otherwise run with Python
echo ">> Running modular Python service (main.py)..."
exec python -u main.py
