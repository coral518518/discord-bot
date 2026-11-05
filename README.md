# Discord Bot Worker Service (生产发布与模块化架构)

基于 Python 架构的 Discord 机器人后台事件中继与通信同步服务，采用高可用解耦设计与双引擎架构，支持使用 Nuitka 编译为完全独立的单一可执行文件（Standalone Onefile），客户无需安装 Python 环境即可一键部署。

---

## 🌟 架构与优化特性

1. **清晰的模块化分层**：
   - `main.py`：程序入口。处理 CLI 命令行参数、系统信号（SIGINT/SIGTERM 优雅停机）、环境加载与服务生命周期调度。
   - `core.py`：核心业务逻辑。双核心引擎（Profile Alpha / Profile Beta）配置动态生成、Cloudflare 边缘中继隧道建立与域名解析、通信通道同步、HTTP 状态探针、90 秒运行时自动回收机制。
   - `utils.py`：通用底层工具函数。跨平台架构检测（ARM / AMD）、命令执行安全封装、流式文件下载、IP/GeoIP 检测、Telegram 推送、订阅聚合与保活上报。
   - `config.py`：配置集中管理与敏感常量混淆保护。自动从当前路径或可执行文件所在目录读取 `.env`，内置敏感常量动态解码。
2. **源码级敏感信息保护**：
   - 所有内置的远程节点下发地址、WireGuard 敏感密钥、探针下载地址均采用动态解码机制（Base64 + XOR 混淆），源码与二进制文件中均无明文敏感 URL。
   - 生产级脱敏日志：启动时自动掩码 UUID，不再在终端明文打印私钥或长订阅文本。
3. **彻底清理生产冗余**：
   - 移除原代码中的清屏控制字符（`\033c`）、调试用 print、随意打印的密钥，采用标准 Python `logging` 输出规范的时间戳日志。
4. **Nuitka 独立二进制分发（Standalone Onefile）**：
   - 直接将 Python 源代码翻译为 C 语言并调用底层 C 编译器（GCC/Clang/MSVC）编译为机器码。
   - 彻底摆脱对客户端服务器 Python 版本及环境依赖，单文件分发，逆向难度大幅提高。

---

## 📁 重构后项目目录结构

```text
discord-bot/
├── main.py                 # [程序入口] CLI参数解析、信号监听、服务生命周期管理
├── core.py                 # [核心逻辑] 双引擎业务、配置组装、隧道中继、HTTP状态端点
├── utils.py                # [通用工具] 系统检测、安全命令、流式下载、IP探测、外部推送
├── config.py               # [配置管理] 集中配置模型、.env自动加载、内部字符串混淆解码
├── build_nuitka.py         # [构建脚本] 一键调用 Nuitka 编译为单一可执行文件的自动化脚本
├── .env                    # [生产配置] 实际运行环境配置文件
├── .env.example            # [配置模板] 完整的环境变量说明模板
├── requirements.txt        # [运行依赖] requests, python-dotenv
├── Dockerfile              # [标准容器] 轻量 Python 容器镜像构建文件
├── Dockerfile.nuitka       # [原生容器] 多阶段构建，容器内仅包含编译后的纯二进制文件
└── docker-compose.yml      # [容器编排] Docker Compose 一键启动文件
```

---

## 🛠️ Nuitka 编译与独立可执行文件打包

通过 Nuitka 将整个项目编译为单一独立二进制文件（Standalone Onefile），编译产物包含所有的 CPython 运行时、底层依赖和业务逻辑编译出的机器码，分发给客户时**不需要安装 Python**。

### 1. 准备编译环境

```bash
# 安装编译所需 Python 包
pip install -r requirements.txt
pip install nuitka zstandard ordered-set

# Linux 环境需确保已安装 GCC 或 Clang
# Ubuntu/Debian:
# sudo apt-get update && sudo apt-get install -y build-essential patchelf ccache
# CentOS/RHEL:
# sudo yum groupinstall "Development Tools" && sudo yum install patchelf
```

### 2. 执行编译命令

#### 方式 A：使用内置自动化编译脚本（推荐）
```bash
python build_nuitka.py
```

#### 方式 B：直接执行 Nuitka 命令

**在 Linux 上编译（生成独立 ELF 二进制文件）**：
```bash
python -m nuitka \
  --standalone \
  --onefile \
  --follow-imports \
  --include-package=requests \
  --include-package=dotenv \
  --output-filename=discord-bot-worker \
  --output-dir=dist \
  --remove-output \
  --assume-yes-for-downloads \
  --plugin-enable=anti-bloat \
  --python-flag=-O \
  --lto=yes \
  main.py
```

**在 Windows 上编译（生成独立 `.exe` 文件）**：
```bash
python -m nuitka `
  --standalone `
  --onefile `
  --follow-imports `
  --include-package=requests `
  --include-package=dotenv `
  --output-filename=discord-bot-worker.exe `
  --output-dir=dist `
  --remove-output `
  --assume-yes-for-downloads `
  --plugin-enable=anti-bloat `
  --python-flag=-O `
  --windows-console-mode=force `
  main.py
```

> **Windows 编译器兼容性提示**：
> - 若使用 **Python 3.13 / 3.14+**：Nuitka 会自动拉取并使用 **Zig** 或系统中的 **MSVC**，**切勿添加 `--mingw64` 参数**（否则会报 MinGW64 不兼容错误）。
> - 若使用 **Python <= 3.12**：可追加 `--mingw64` 自动下载 MinGW-w64 工具链。
> - 推荐直接运行 `python build_nuitka.py`，脚本已自动适配当前系统平台和 Python 版本的最佳编译参数。

> **核心参数说明**：
> - `--standalone`：打包所有依赖动态库。
> - `--onefile`：将所有内容压缩包装为单一的可执行文件。
> - `--follow-imports`：递归将 `core.py`、`utils.py`、`config.py` 编译为 C 代码机器码。
> - `--include-package=requests,dotenv`：确保动态包和依赖完整打包进二进制。
> - `--python-flag=-O`：启用优化，剥离断言与调试信息。
> - `--lto=yes`：启用链接时优化（Link Time Optimization），减小体积并增强防逆向保护。

---

## 📦 客户部署与交付方式

### 交付物打包
编译完成后，仅需将以下两个文件打包交付给客户：
1. `discord-bot-worker`（或 `discord-bot-worker.exe`）
2. `.env`（根据客户需求预填好配置）

### 客户服务器上运行

1. 给执行权限并启动：
   ```bash
   chmod +x discord-bot-worker
   ./discord-bot-worker
   ```
2. 使用 systemd 后台常驻服务管理（以 Linux 为例）：
   创建服务文件 `/etc/systemd/system/discord-worker.service`：
   ```ini
   [Unit]
   Description=Discord Bot Worker Service
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/discord-worker
   ExecStart=/opt/discord-worker/discord-bot-worker
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```
   启用并启动服务：
   ```bash
   systemctl daemon-reload
   systemctl enable --now discord-worker
   systemctl status discord-worker
   ```

---

## 🐳 Docker 部署（可选）

如果您希望仍然通过 Docker 容器分发：

### 1. 使用 Docker Compose 启动源码版
```bash
docker compose up -d
```

### 2. 使用 Nuitka 多阶段镜像（超小体积，完全免源码）
```bash
docker build -f Dockerfile.nuitka -t discord-bot-worker:native .
docker run -d --name bot-worker --restart unless-stopped -p 3000:3000 discord-bot-worker:native
```
