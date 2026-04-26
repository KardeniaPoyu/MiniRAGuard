<<<<<<< Updated upstream
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
=======
<div align="center">

<h1>MiniRAGuard</h1>

<p>
    <strong>Full-stack Multimodal RAG Template for Auditing and Compliance Review</strong>
</p>

<p>
    <a href="https://github.com/KardeniaPoyu/MiniRAGuard/stargazers"><img src="https://img.shields.io/github/stars/KardeniaPoyu/MiniRAGuard?style=flat-square" alt="Stars"></a>
    <a href="https://github.com/KardeniaPoyu/MiniRAGuard/network/members"><img src="https://img.shields.io/github/forks/KardeniaPoyu/MiniRAGuard?style=flat-square" alt="Forks"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
</p>

<p>
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/UniApp-2B9939?style=flat-square&logo=vuedotjs" alt="UniApp">
    <img src="https://img.shields.io/badge/DeepSeek-0d6efd?style=flat-square" alt="DeepSeek">
    <img src="https://img.shields.io/badge/Qwen__VL-ff6a00?style=flat-square" alt="Qwen-VL">
</p>

[**English**](./README.md) | [**简体中文**](./README_zh.md) | [**日本語**](./README_ja.md)

</div>

---

## Overview

MiniRAGuard is a full-stack technical template integrating Vision Large Models (VLM) and Retrieval-Augmented Generation (RAG). It provides a standardized implementation for document auditing, compliance review, and automated structured parsing in vertical domains.

## Technical Features

- **Fact-based Retrieval-Augmented Generation**: Utilizes Sentence-Transformers and a local vector database to ensure model reasoning is grounded in predefined regulations, reducing hallucinations.
- **Multimodal Document Parsing**: Integrated VLM support (defaulting to Qwen-VL) for automated structured data extraction from scans, images, and PDFs.
- **Audit Workflow Constraints**: Built-in "review-feedback" Prompt templates to define output boundaries for sensitive business scenarios like legal or financial audits.

## Demo

Video demonstration of the built-in Rental Compliance Assistant:

https://github.com/user-attachments/assets/28709a21-b789-4ed4-9fc6-ffad16611da7

## Engineering Components
  - **Backend**: High-performance asynchronous API built with FastAPI.
  - **Frontend**: Cross-platform business interface built with UniApp/Vue.
- **System Stability & Optimization**:
  - **Request Caching**: MD5-based file verification to intercept redundant requests and reduce API costs.
  - **Concurrency Control**: Semaphore-based flow control to limit concurrent requests to LLM endpoints, ensuring service stability.

## Architecture
>>>>>>> Stashed changes

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

## Directory Structure

<<<<<<< Updated upstream
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
=======
- `miniraguard/`: Abstract core framework.
- `examples/`: Business implementation examples (e.g., Rental Compliance Assistant).
  - `backend/`: Backend business logic.
  - `frontend/`: Frontend UniApp source code.
  - `data/`: Knowledge base and vector storage.
- `docs/`: Technical documentation.

## Quick Start
>>>>>>> Stashed changes

### 1. Backend Deployment

<<<<<<< Updated upstream
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
=======
```bash
git clone https://github.com/KardeniaPoyu/MiniRAGuard.git
cd MiniRAGuard/examples/rent_assistant/backend
pip install -r ../../../requirements.txt 
cp .env.example .env # Add your API_KEY
python main.py
```

### 2. Frontend Deployment

1. Import `examples/rent_assistant/frontend` into HBuilderX.
2. Update `BASE_URL` in `config.js` to your backend address.
3. Run in the built-in browser or WeChat DevTools.

## Customization

1. **Inject Knowledge**: Replace files in `examples/rent_assistant/data/` with your own TXT or Markdown files.
2. **Reset Index**: Delete the `vector_store` directory; the index will be rebuilt on the next startup.
3. **Adjust Logic**: Modify the System Prompt in `backend/prompts.py`.

## License

This project is licensed under the [MIT](LICENSE) License.
>>>>>>> Stashed changes
