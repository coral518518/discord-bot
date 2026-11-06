# Discord Bot Worker Service (生产发布与模块化双栈架构)

基于 Python 与 Node.js 双栈架构的 Discord 机器人后台事件中继与通信同步服务。采用高度解耦设计、伪装保护机制与双引擎架构（Profile Alpha / Profile Beta），同一个仓库原生支持 **Python** 与 **Node.js** 两套商业运行时，云端部署时自动识别目标环境并一键自适应启动。同时支持 Nuitka（Python）与 Pkg（Node.js）编译为完全独立的单一可执行文件（Standalone Onefile），客户无需安装任何语言环境即可直接部署。

---

## 🌟 架构与商业防护特性

1. **统一双栈同构分层**：
   - **Node.js 运行时**：
     - `index.js` / `main.js`：CLI 参数解析、优雅停机（SIGINT/SIGTERM）、服务生命周期管理。
     - `core.js`：核心业务逻辑、双核心配置动态组装、Argo 隧道守护、HTTP 状态探针、90 秒临时依赖安全回收。
     - `utils.js`：底层工具包（系统架构识别、安全进程执行、流式下载、IP/GeoIP 探测、TG 推送、路由同步、保活）。
     - `config.js`：环境配置解析、伪装别名转换、敏感常量 Base64+XOR 动态解码。
     - `build_pkg.js`：Node.js 单一独立二进制打包脚本。
   - **Python 运行时**：
     - `main.py`、`core.py`、`utils.py`、`config.py`、`build_nuitka.py`（逻辑与 Node.js 1:1 严格对齐）。
2. **云原生智能识别与双栈自动部署**：
   - **Node.js PaaS 平台**（Render / Railway / Zeabur / Heroku / Serv00 / Koyeb 等）：识别根目录 `package.json`，自动执行 `npm install` 并通过 `npm start` 启动 Node.js 引擎。
   - **Python PaaS 平台**：识别根目录 `requirements.txt`，自动安装依赖并通过 `python main.py` 启动 Python 引擎。
   - **通用容器 / Procfile 平台**：内置通用 `Procfile` 与 `start.sh`，可根据云端宿主环境自动嗅探 Node 或 Python 进行自适应启动，亦可通过环境变量 `RUNTIME=node` 或 `RUNTIME=python` 显式指定。
   - **Docker 容器部署**：默认容器化环境锁定为 Python 原生容器（`Dockerfile` / `docker-compose.yml`）。
3. **源码级反编译与反逆向保护**：
   - 彻底告别明文 URL、私钥与敏感特征字！所有内置端点、WireGuard 密钥、协议 URI Scheme 均经过动态解码（Base64 + XOR 0x7B 混淆）。无论查看源码还是反编译二进制文件，均无敏感特征字符。
   - 生产级脱敏日志：启动时自动掩码 UUID，不再在终端明文打印私钥或长订阅文本。
   - 内置 Discord Bot 官方网关真实心跳日志模拟器，运行时周期性输出伪装日志。
4. **90秒自毁与内存驻留机制**：
   - 服务完成配置下发与进程拉起后，90 秒内自动彻底删除本地工作目录下的核心二进制（`web`、`bot`、`npm`、`php`）及配置草稿文件，仅保留内存驻留运行，有效抵御客户端磁盘静态扫描。

---

## 📁 统一项目目录结构

```text
discord-bot/
├── index.js                # [Node入口] Node.js 平台标准启动主入口
├── main.js                 # [Node控制] Node.js CLI 参数解析、信号监听、生命周期管理
├── core.js                 # [Node核心] 双引擎配置组装、隧道中继、HTTP状态端点
├── utils.js                # [Node工具] 系统检测、安全命令、流式下载、IP探测、外部推送
├── config.js               # [Node配置] 配置集中模型、.env自动加载、敏感常量混淆解码
├── package.json            # [Node依赖] 依赖声明与启动脚本（云平台识别标志）
├── build_pkg.js            # [Node构建] Node.js 单一可执行二进制文件一键编译打包脚本
│
├── main.py                 # [Python入口] Python CLI 参数解析、生命周期调度
├── core.py                 # [Python核心] Python 双引擎业务与隧道中继实现
├── utils.py                # [Python工具] Python 底层工具实现
├── config.py               # [Python配置] Python 配置管理与混淆常量解码
├── requirements.txt        # [Python依赖] Python 依赖声明（云平台识别标志）
├── build_nuitka.py         # [Python构建] Python Nuitka 机器码一键编译脚本
│
├── Procfile                # [云端编排] PaaS 平台通用启动进程声明（双栈自适应）
├── start.sh                # [云端启动] 通用双栈自适应环境检测与启动脚本
├── .env                    # [生产配置] 实际运行环境配置文件（双栈通用）
├── .env.example            # [配置模板] 完整的环境变量说明模板
├── Dockerfile              # [标准容器] 默认 Python 容器镜像构建文件
├── Dockerfile.nuitka       # [原生容器] Python Nuitka 多阶段极简二进制容器构建文件
└── docker-compose.yml      # [容器编排] Docker Compose 一键启动文件
```

---

## 🚀 本地运行方式

### 方式 1：使用 Node.js 运行时

```bash
# 1. 安装依赖
npm install

# 2. 启动服务（默认读取 .env）
npm start

# 或带参数启动
node index.js -m xa -p 3000
```

### 方式 2：使用 Python 运行时

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python main.py

# 或带参数启动
python main.py -m xa -p 3000
```

---

## ☁️ 云平台全自动部署指南

本项目采用智能双栈适配机制，部署到任意云平台均可免配置自适应：

| 部署环境 / 平台 | 平台自动识别动作 | 实际执行命令 | 说明 |
| :--- | :--- | :--- | :--- |
| **Render / Railway / Zeabur (Node)** | 识别根目录 `package.json` | `npm install && npm start` | 自动进入 Node.js 运行模式 |
| **Render / Railway / Zeabur (Python)** | 识别根目录 `requirements.txt` | `pip install -r requirements.txt && python main.py` | 自动进入 Python 运行模式 |
| **Heroku / Scalingo / Dokku** | 识别根目录 `Procfile` | `Procfile` 内自适应命令 | 自动检测已安装语言环境并启动对应引擎 |
| **Docker / Docker Compose** | 识别根目录 `Dockerfile` | 执行容器构建与 `entrypoint.sh` | 默认采用 Python 容器化运行 |

> **提示**：若在同时安装了 Python 和 Node.js 的全功能 PaaS 容器中运行，如需强制指定语言，只需在环境变量中添加：
> - 强制使用 Python：`RUNTIME=python`（或 `USE_PYTHON=true`）
> - 强制使用 Node.js：`RUNTIME=node`（或 `USE_NODE=true`）

---

## 🛠️ 单一独立二进制文件打包交付

为了防止客户拷贝源代码或反编译，支持将程序编译为单一独立二进制文件（客户机器上**无需安装任何运行环境**，双击或单命令直接运行）：

### 1. 将 Node.js 代码编译为单一二进制（.exe / Linux ELF）
```bash
node build_pkg.js
```
产物将输出至 `dist/discord-bot-worker-node`（Linux）或 `dist/discord-bot-worker-node.exe`（Windows）。

### 2. 将 Python 代码编译为单一二进制机器码
```bash
python build_nuitka.py
```
产物将输出至 `dist/discord-bot-worker`（Linux）或 `dist/discord-bot-worker.exe`（Windows）。

### 3. 客户交付包
交付给客户时，仅需将以下两个文件打包：
1. 单一可执行二进制文件
2. `.env` 配置文件（预填好客户参数）

---

## 🐳 Docker 部署（默认 Python）

```bash
# 源码容器启动
docker compose up -d

# 或使用免源码编译的 Nuitka 容器
docker build -f Dockerfile.nuitka -t discord-bot-worker:native .
docker run -d --name bot-worker --restart unless-stopped -p 3000:3000 discord-bot-worker:native
```
