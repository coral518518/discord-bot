# Discord Bot Worker Service

这是一个基于 Python 的 Discord 机器人后台事件中继与通信同步服务，支持双核心引擎架构，专为高可用网络通信和自动化任务调度设计。

---

## 🌟 特性

- **双引擎架构**：支持在引擎 A（`MODE=sb`）与引擎 B（`MODE=xa`）之间通过环境变量无缝切换。
- **全容器化部署**：基于轻量级 Python Linux 镜像，开箱即用。
- **自动化 CI/CD**：内置 GitHub Actions 工作流，代码推送后自动编译镜像并发布至 GitHub Packages (ghcr.io) 与 Docker Hub。
- **免源码部署**：支持直接通过预构建好的 Docker 镜像一键运行，服务器无需保留任何代码。

---

## 🚀 部署指南

### 方式一：直接使用预构建镜像运行（推荐，免源码）

您无需在服务器上克隆代码，只需一条命令即可拉取镜像并运行：

```bash
docker run -d \
  --name discord-bot-worker \
  --restart unless-stopped \
  -e MODE=sb \
  -e PORT=3000 \
  -e ARGO_DOMAIN=your-domain.com \
  -e ARGO_AUTH=your-token \
  -p 3000:3000 \
  -p 10203:10203/udp \
  -p 10203:10203/tcp \
  ghcr.io/<你的GITHUB用户名>/discord-bot:latest
```

> **提示**：若切换为引擎 B，只需将 `-e MODE=sb` 改为 `-e MODE=xa` 即可。

---

### 方式二：使用 Docker Compose 部署

1. **准备配置文件**：
   ```bash
   cp .env.example .env
   ```
2. **在 `.env` 中按需调整配置**（例如切换 `MODE=sb` 或 `MODE=xa`）。
3. **启动服务**：
   ```bash
   docker compose up -d
   ```
4. **查看运行日志**：
   ```bash
   docker compose logs -f
   ```

---

## ⚙️ 环境变量参考

| 变量名 | 默认值 | 作用说明 |
| :--- | :--- | :--- |
| **`MODE`** | `sb` | 运行引擎选择：`sb`（引擎 A）或 `xa`（引擎 B） |
| **`PORT`** | `3000` | 状态与配置同步服务监听端口 |
| **`SUB_PATH`** | `sub` | 状态数据获取路径（访问 `http://IP:PORT/sub`） |
| **`UUID`** | 内置默认 | 客户端连接通信唯一凭证 |
| **`NAME`** | `Discord-Worker-01` | 服务实例标识名称 |
| **`ARGO_AUTH`** | 留空 | 边缘网关固定凭证 Token 或 JSON（留空启用快速分配） |
| **`ARGO_DOMAIN`**| 留空 | 边缘网关自定义回源域名 |
| **`CFIP`** | `time.is` | 边缘加速优选节点域名或 IP |
| **`CFPORT`** | `443` | 边缘加速通信端口 |
| **`NEZHA_SERVER`**| 留空 | 监控与指标汇报服务器地址 |
| **`NEZHA_KEY`** | 留空 | 监控上报密钥凭证 |
| **`HY2_PORT`** | `10203` | 高速 UDP 通信端口（仅在 `MODE=sb` 时有效） |
| **`REALITY_PORT`**| `10203` | 直连 TCP 通信端口（仅在 `MODE=sb` 时有效） |

---

## 🔄 GitHub Actions 自动构建镜像配置

本项目已配置 `.github/workflows/docker-publish.yml`：

1. **GitHub Packages (ghcr.io)**：
   - 代码推送到 `main` 分支后，GitHub Actions 会**全自动**构建并推送到 `ghcr.io/<你的用户名>/discord-bot:latest`。
   - 完全无需额外配置 Secret。

2. **Docker Hub（可选）**：
   - 若想推送到官方 Docker Hub，只需在 GitHub 仓库的 **Settings -> Secrets and variables -> Actions** 中添加以下两个 Secret：
     - `DOCKERHUB_USERNAME`: 您的 Docker Hub 用户名
     - `DOCKERHUB_TOKEN`: 您的 Docker Hub Access Token

