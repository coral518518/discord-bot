#!/usr/bin/env bash
set -e

# 如果用户传入了自定义命令（例如 bash、sh 等），则直接执行
if [ "$#" -gt 0 ] && [ "$1" != "run" ]; then
    exec "$@"
fi

# -----------------------------------------------------------------------------
# 1. 针对受限容器的非侵入式 DNS 诊断与自愈机制
# 仅在外部 DNS 解析确实失效/异常时，才修改 /etc/resolv.conf。
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

RAW_MODE="${MODE:-${CLUSTER_PROFILE:-${ENGINE:-sb}}}"
case "$(echo "$RAW_MODE" | tr '[:upper:]' '[:lower:]')" in
    xa|profile-b|2|beta|worker-b|b)
        TARGET_MODE="xa"
        ;;
    *)
        TARGET_MODE="sb"
        ;;
esac

echo "========================================================"
echo " >> Discord Bot Worker Service Initializing..."
echo " >> Target Profile: ${TARGET_MODE}"
echo "========================================================"

cd /app

# -----------------------------------------------------------------------------
# 2. 利用容器镜像内嵌资源预填充工作缓存（消除冷启动延迟）
# -----------------------------------------------------------------------------
CACHE_DIR="${FILE_PATH:-.cache}"
mkdir -p "$CACHE_DIR"

if [ -d "/app/bin_defaults" ]; then
    TARGET_BIN="web_${TARGET_MODE}"
    CURRENT_PROFILE=$(cat "$CACHE_DIR/.profile" 2>/dev/null || echo "")
    if [ ! -f "$CACHE_DIR/web" ] || [ ! -s "$CACHE_DIR/web" ] || [ "$CURRENT_PROFILE" != "$TARGET_MODE" ]; then
        if [ -s "/app/bin_defaults/$TARGET_BIN" ]; then
            cp "/app/bin_defaults/$TARGET_BIN" "$CACHE_DIR/web"
            chmod +x "$CACHE_DIR/web" 2>/dev/null || true
            echo "$TARGET_MODE" > "$CACHE_DIR/.profile"
            echo ">> [Cache] Seeded engine Profile (${TARGET_MODE}) from baked image."
        elif [ -s "/app/bin_defaults/web_sb" ]; then
            cp "/app/bin_defaults/web_sb" "$CACHE_DIR/web"
            chmod +x "$CACHE_DIR/web" 2>/dev/null || true
            echo "sb" > "$CACHE_DIR/.profile"
            echo ">> [Cache] Seeded engine Profile Alpha (sb) fallback."
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

# 1. 如果存在已编译的原生二进制程序，直接执行二进制文件
if [ -f "/app/discord-bot-worker" ]; then
    echo ">> Running compiled native binary: /app/discord-bot-worker"
    exec /app/discord-bot-worker
fi

# 2. 否则使用 Python 运行（支持源码 main.py 或已编译的字节码 main.pyc）
echo ">> Running modular Python service..."
if [ -f "main.py" ]; then
    exec python -u main.py
else
    exec python -u main.pyc
fi