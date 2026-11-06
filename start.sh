#!/usr/bin/env bash
# ==============================================================================
# Dual-Stack Universal Cloud Startup Launcher
# Automatically detects whether cloud runtime environment is Node.js or Python.
# ==============================================================================

set -e

echo "========================================================"
echo " >> Discord Bot Worker Service (Dual-Stack Cloud Launcher)"
echo " >> Detecting runtime environment..."
echo "========================================================"

# 1. Check for manual environment override
if [ "$RUNTIME" = "python" ] || [ "$ENGINE_LANG" = "python" ] || [ "$USE_PYTHON" = "true" ] || [ "$USE_PYTHON" = "1" ]; then
    echo "[Launcher] Manual override detected: Python runtime selected."
    if command -v python3 >/dev/null 2>&1; then
        exec python3 -u main.py "$@"
    else
        exec python -u main.py "$@"
    fi
fi

if [ "$RUNTIME" = "node" ] || [ "$ENGINE_LANG" = "node" ] || [ "$USE_NODE" = "true" ] || [ "$USE_NODE" = "1" ]; then
    echo "[Launcher] Manual override detected: Node.js runtime selected."
    exec node index.js "$@"
fi

# 2. Check if a compiled standalone native binary exists (produced by build_nuitka or build_pkg)
if [ -f "./discord-bot-worker" ] && [ -x "./discord-bot-worker" ]; then
    echo "[Launcher] Found compiled native binary. Executing directly..."
    exec ./discord-bot-worker "$@"
fi

# 3. Environment detection: Prefer Node.js if node runtime is available and package.json is installed
if command -v node >/dev/null 2>&1 && [ -f "index.js" ]; then
    echo "[Launcher] Auto-detected Node.js environment ($(node -v)). Launching Node engine..."
    exec node index.js "$@"
fi

# 4. Fallback to Python if python is available
if command -v python3 >/dev/null 2>&1 && [ -f "main.py" ]; then
    echo "[Launcher] Auto-detected Python 3 environment ($(python3 --version)). Launching Python engine..."
    exec python3 -u main.py "$@"
elif command -v python >/dev/null 2>&1 && [ -f "main.py" ]; then
    echo "[Launcher] Auto-detected Python environment ($(python --version)). Launching Python engine..."
    exec python -u main.py "$@"
fi

echo "[Launcher ERROR] Neither Node.js nor Python runtime was found on this host!"
exit 1

