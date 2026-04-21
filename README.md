# 数律智检 · 基层治理风险研判平台

> 基于 AI 的检察智能辅助系统，实现从线索录入 → 风险研判 → 协同跟进的全流程数字化闭环。

---

## 快速开始

### 方式一：生产安装包（推荐）

适合最终用户，提供标准 Windows 安装/卸载体验。

```bash
# 开发者在 installer/ 目录运行
installer\build_installer.bat
```

生成产物：`dist_installer\数律智检_Setup_v1.0.0.exe`

**前置条件（仅开发机需要）**：
- [Node.js 18+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)
- [Inno Setup 6](https://jrsoftware.org/isdl.php)

---

### 方式二：Docker 本地部署（团队内部共享）

适合内网多人访问，无需安装包。

```bash
# 1. 复制并填写环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 2. 一键启动
docker-compose up -d --build

# 3. 访问
# 管理端：http://localhost
```

---

### 方式三：开发环境运行

```bash
# 后端
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000

# 前端（新终端）
cd admin_frontend
npm install && npm run dev
```

---

## 架构说明

```
数律智检/
├── backend/                 # FastAPI 后端（Python 3.11）
│   ├── core/                # 业务核心（RAG、研判、数据库、鉴权）
│   ├── scripts/             # 初始化脚本（构建向量索引）
│   └── main.py              # 应用入口，生产模式自动托管前端
├── admin_frontend/          # Vue 3 管理端前端
│   └── src/views/           # 大屏、工作台、设置等页面
├── installer/               # 安装包工程
│   ├── build_installer.bat  # 一键构建脚本（开发者用）
│   ├── installer.iss        # Inno Setup 安装向导配置
│   └── launcher.py          # 轻量级桌面启动器源码
├── deploy/                  # 服务器部署配置
│   └── nginx.conf           # Nginx 反向代理配置
└── docker-compose.yml       # Docker 编排文件
```

---

## 环境变量

复制 `.env.example` 为 `.env` 并填写：

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | ✅ |
| `JWT_SECRET_KEY` | JWT 签名密钥（随机字符串） | ✅ |
| `PRODUCTION` | 设为 `true` 跳过测试数据植入 | 可选 |

---

## 默认账号

| 角色 | 用户名 | 初始密码 |
|------|--------|----------|
| 管理员 | `admin` | `admin123` |

> **安全提示**：生产部署前请修改初始密码。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | FastAPI + uvicorn |
| AI | LlamaIndex + ChromaDB + DeepSeek |
| 嵌入模型 | sentence-transformers (HuggingFace) |
| 数据库 | SQLite |
| 容器 | Docker + Nginx |
| 安装包 | Inno Setup 6 |
