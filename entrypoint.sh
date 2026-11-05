#!/usr/bin/env bash
set -e

# If user passed custom command (e.g. bash, sh, etc.), execute directly
if [ "$#" -gt 0 ] && [ "$1" != "run" ]; then
    exec "$@"
fi

# Normalize MODE (case-insensitive, fallback to ENGINE or sb)
TARGET_MODE=$(echo "${MODE:-${ENGINE:-sb}}" | tr '[:upper:]' '[:lower:]')

echo "========================================================"
echo " >> Discord Bot Worker Service Initializing..."
echo " >> Target Profile: ${TARGET_MODE}"
echo "========================================================"

case "${TARGET_MODE}" in
    sb|singbox|1|alpha|worker-a)
        echo ">> Starting Core Engine Profile A (python-sb)..."
        cd /app/python-sb
        exec python -u main.py
        ;;
    xa|xray|2|beta|worker-b)
        echo ">> Starting Core Engine Profile B (python-xa)..."
        cd /app/python-xa
        exec python -u main.py
        ;;
    *)
        echo ">> [ERROR] Unknown Profile MODE: '${TARGET_MODE}'"
        echo ">> Valid options are: 'sb' (default, Profile A) or 'xa' (Profile B)"
        exit 1
        ;;
esac
