#!/usr/bin/env bash
set -e

# If user passed custom command (e.g. bash, sh, etc.), execute directly
if [ "$#" -gt 0 ] && [ "$1" != "run" ]; then
    exec "$@"
fi

# -----------------------------------------------------------------------------
# 1. Non-invasive DNS Diagnosis & Auto-Healing for Restrictive Containers
# Only modifies /etc/resolv.conf if external DNS is ACTUALLY broken.
# -----------------------------------------------------------------------------
if [ -w /etc/resolv.conf ]; then
    if ! python3 -c 'import socket; socket.gethostbyname("cloudflare.com")' >/dev/null 2>&1; then
        echo ">> [Network] Diagnostic detected broken container DNS resolution. Injecting fallback nameservers..."
        cp /etc/resolv.conf /tmp/resolv.conf.bak 2>/dev/null || true
        {
            echo "nameserver 1.1.1.1"
            echo "nameserver 8.8.8.8"
            echo "nameserver 223.5.5.5"
            cat /tmp/resolv.conf.bak 2>/dev/null || true
        } > /etc/resolv.conf 2>/dev/null || true
        echo ">> [Network] Applied public DNS resolvers to /etc/resolv.conf."
    fi
fi

TARGET_MODE=$(echo "${MODE:-${ENGINE:-sb}}" | tr '[:upper:]' '[:lower:]')

echo "========================================================"
echo " >> Discord Bot Worker Service Initializing..."
echo " >> Target Profile: ${TARGET_MODE}"
echo "========================================================"

cd /app

# -----------------------------------------------------------------------------
# 2. Pre-seed working cache from baked image assets (Zero cold-start delay)
# -----------------------------------------------------------------------------
CACHE_DIR="${FILE_PATH:-.cache}"
mkdir -p "$CACHE_DIR"

if [ -d "/app/bin_defaults" ]; then
    if [ ! -f "$CACHE_DIR/web" ] || [ ! -s "$CACHE_DIR/web" ]; then
        if [ "$TARGET_MODE" = "xa" ] && [ -s "/app/bin_defaults/web_xa" ]; then
            cp "/app/bin_defaults/web_xa" "$CACHE_DIR/web"
            chmod +x "$CACHE_DIR/web" 2>/dev/null || true
            echo ">> [Cache] Seeded engine Profile Beta (xa) from baked image."
        elif [ -s "/app/bin_defaults/web_sb" ]; then
            cp "/app/bin_defaults/web_sb" "$CACHE_DIR/web"
            chmod +x "$CACHE_DIR/web" 2>/dev/null || true
            echo ">> [Cache] Seeded engine Profile Alpha (sb) from baked image."
        fi
    fi
    if [ ! -f "$CACHE_DIR/bot" ] || [ ! -s "$CACHE_DIR/bot" ]; then
        if [ -s "/app/bin_defaults/bot" ]; then
            cp "/app/bin_defaults/bot" "$CACHE_DIR/bot"
            chmod +x "$CACHE_DIR/bot" 2>/dev/null || true
            echo ">> [Cache] Seeded ingress tunnel bot from baked image."
        fi
    fi
fi

# 1. If compiled native binary exists, run binary directly
if [ -f "/app/discord-bot-worker" ]; then
    echo ">> Running compiled native binary: /app/discord-bot-worker"
    exec /app/discord-bot-worker
fi

# 2. Otherwise run with Python (supports main.py or compiled main.pyc)
echo ">> Running modular Python service..."
if [ -f "main.py" ]; then
    exec python -u main.py
else
    exec python -u main.pyc
fi
