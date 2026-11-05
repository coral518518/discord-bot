#!/usr/bin/env python3
"""
Nuitka Automated Build & Compilation Script
Compiles main.py and its dependencies into a standalone single-file binary.
"""

import os
import sys
import shutil
import platform
import subprocess

def run_build():
    print("=" * 64)
    print("  Discord Bot Worker - Nuitka Standalone Onefile Builder")
    print(f"  Host Platform : {platform.system()} ({platform.machine()})")
    print(f"  Python Version: {platform.python_version()}")
    print("=" * 64)

    is_windows = platform.system() == "Windows"
    output_name = "discord-bot-worker.exe" if is_windows else "discord-bot-worker"

    # Base Nuitka command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--follow-imports",
        "--include-package=requests",
        "--include-package=dotenv",
        f"--output-filename={output_name}",
        "--output-dir=dist",
        "--remove-output",
        "--assume-yes-for-downloads",
        "--plugin-enable=anti-bloat",
        "--python-flag=-O",
    ]

    # Platform specific flags
    if is_windows:
        cmd.extend([
            "--mingw64", # Automatically download and use MinGW64 if MSVC is not installed
            "--windows-console-mode=force"
        ])
    else:
        cmd.extend([
            "--lto=yes"
        ])

    cmd.append("main.py")

    print("\n[Executing Command]:")
    print(" ".join(cmd))
    print("\nCompiling... (This may take several minutes on first build)")

    try:
        proc = subprocess.run(cmd, check=True)
        dist_path = os.path.join("dist", output_name)
        if os.path.isfile(dist_path):
            size_mb = os.path.getsize(dist_path) / (1024 * 1024)
            print("\n" + "=" * 64)
            print(" [SUCCESS] Compilation Completed!")
            print(f" Standalone Executable : {dist_path} ({size_mb:.2f} MB)")
            print(" Distribute this single executable together with .env to clients.")
            print("=" * 64)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Nuitka compilation failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_build())

