<div align="center">
  <!-- TODO: 添加项目高分辨率 Logo 或 横幅图像 -->
  <!-- <img src="./docs/assets/banner.png" width="100%" alt="Qingju Banner"> -->

  <h1>🏠 青居智选 (Qingju AI)</h1>

  <p>
    <strong>基于 AI 大模型与 RAG 技术的“年轻态”租房合同双端法律风险审查平台</strong>
  </p>

  <p>
    🛡️ 识别合同陷阱 | 📖 精准法律溯源 | 👁️ 端云协同 OCR | 💬 智能多轮打磨
  </p>

  <p>
    <a href="https://github.com/KardeniaPoyu/Qingju/stargazers"><img src="https://img.shields.io/github/stars/KardeniaPoyu/Qingju?style=for-the-badge&color=F3DFA2&logo=github" alt="Stars"></a>
    <a href="https://github.com/KardeniaPoyu/Qingju/network/members"><img src="https://img.shields.io/github/forks/KardeniaPoyu/Qingju?style=for-the-badge&color=7E8D85&logo=github" alt="Forks"></a>
    <a href="https://github.com/KardeniaPoyu/Qingju/issues"><img src="https://img.shields.io/github/issues/KardeniaPoyu/Qingju?style=for-the-badge&color=E8C8CD&logo=github" alt="Issues"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=B0C4B1" alt="License"></a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Frontend-UniApp-2B9939?style=flat-square&logo=vuedotjs" alt="UniApp">
    <img src="https://img.shields.io/badge/LLM-DeepSeek-0d6efd?style=flat-square" alt="DeepSeek">
    <img src="https://img.shields.io/badge/VLM-Qwen__VL-ff6a00?style=flat-square" alt="Qwen">
  </p>
</div>

---

## 📖 目录 (Table of Contents)

- [✨ 项目愿景](#-项目愿景)
- [🖼️ 产品演示 (Demo)](#-产品演示)
- [🌟 核心特性](#-核心特性)
- [🏗️ 技术架构](#-技术架构)
- [🚀 快速开始](#-快速开始)
- [📊 目录结构](#-目录结构)
- [🤝 参与贡献](#-参与贡献)
- [📄 开源协议](#-开源协议)

---

## ✨ 项目愿景

在城市化进程中，租房群体（特别是高校学生、新市民）在面临复杂的长租合同时，往往缺乏法律审查能力。“青居智选”取意于**“青春年华，居心安稳”**。本项目提供开箱即用的解决方案：用户仅需手机拍照，AI 即可极速找出“霸王条款”、“暗病陷阱”，并提供权威的法律依据，让每一份契约都成为真正的保障。

**📢 适合关注：** `AI-Agent` / `RAG` / `Legal-Tech` / `Tech-for-Good` (科技向善) / `Social-Governance` (社会治理)

---

## 🖼️ 产品演示

*(💡 提示：在此处上传真实的小程序交互 GIF 或多张截图。以下为占位符。)*

<div align="center">
  <table>
    <tr>
      <td align="center"><b>📸 智能拍照扫描</b></td>
      <td align="center"><b>⚠️ 风险条款高亮</b></td>
      <td align="center"><b>💬 AI 法律顾问互动</b></td>
    </tr>
    <tr>
      <td><img src="https://via.placeholder.com/250x500.png?text=Home+Page" width="200" alt="首页上传"></td>
      <td><img src="https://via.placeholder.com/250x500.png?text=Risk+Result" width="200" alt="风险分析结果"></td>
      <td><img src="https://via.placeholder.com/250x500.png?text=AI+Chat" width="200" alt="AI 多轮问答"></td>
    </tr>
  </table>
</div>

---

## 🌟 核心特性

- **一拍极验 (端云协同视觉)**：基于 **Qwen-VL-Max**，无惧合同折叠、光线昏暗、手写笔记，极速提取精准条文。
- **拒止幻觉 (法律级 RAG)**：不盲目依赖大模型底座知识。采用 `Sentence-Transformer` 外挂《民法典》、《北京市住房租赁条例》，让每一条判定都**“言必有法”**。
- **深度解析 (DeepSeek 驱动)**：结构化输出「高/中/低」风险，动态生成可读性极强的白话防坑指南，支持沉浸式多轮追问。
- **极客性能 (并发与缓冲保障)**：引入 **MD5 热缓存** (命中相同合同不再触发大模型) 与 **动态信号量** 控制并发，用最少的显存/Token，跑出最快的响应。

---

## 🏗️ 技术架构

系统采用清晰的前后端分离架构，模型层轻耦合设计，极易二次开发及迁移至其他社会治理/文书审查领域：

```mermaid
graph TD
    User((用户端/小程序)) -->|1. 图片上传 (Base64)| API_Gateway[FastAPI 核心网关]
    
    subgraph AI 审查矩阵
        API_Gateway -->|2. 图片流| VL[Qwen-VL: 多模态字符抓取]
        VL -->|3. 干净文本| RAG_Engine[轻量级 RAG 检索器]
        
        subgraph 本地知识库 📚
            RAG_Engine <-->|4. 相似度匹配| VectorDB[(Faiss/Chroma 向量数据库)]
            VectorDB -.包含.-> LawDocs[民法典/地方法规片段]
        end
        
        RAG_Engine -->|5. 聚合(Context + 条文)| LLM[DeepSeek-Chat: 逻辑推理]
    end
    
    LLM -->|6. JSON 结构化分析| API_Gateway
    API_Gateway -->|7. UI 渲染渲染| User
```

---

## 🚀 快速开始

本项目坚持“开箱即用”原则，只需三步即可在本地跑起属于你的 AI 法律顾问引擎：

### 🔧 1. 后端部署 (FastAPI 核心)

环境要求：`Python 3.9+`

```bash
# 1. 克隆项目
git clone https://github.com/KardeniaPoyu/Qingju.git
cd Qingju/rent_agent_backend

# 2. 安装环境依赖
pip install -r requirements.txt

# 3. 环境变量配置
cp .env.example .env
# 编辑 .env 文件，填入你的 QWEN_API_KEY 与 DEEPSEEK_API_KEY

# 4. 启动服务 (默认端口 8000)
python main.py
```

🎉 启动后，浏览器访问 `http://localhost:8000/docs` 即可查看并交互测试 Swagger API。

### 📱 2. 前端部署 (Uni-app 微信小程序)

1. 下载并安装 [HBuilderX](https://www.dcloud.io/hbuilderx.html)。
2. 将 `rent_agent_frontend` 目录拖入 HBuilderX。
3. 打开 `config.js`，核对/修改 `BASE_URL` 为你的后端地址（如果在本地，默认为 `http://127.0.0.1:8000`）。
4. 先运行至内置浏览器或连接本地微信开发者工具查看效果！

---

## 📊 目录结构精要

```text
Qingju/
├── rent_agent_backend/    # 🐍 核心后端与 AI 枢纽
│   ├── core/              # RAG 模块、视觉提取、Agent 工具集
│   ├── data/              # 预置法律法规原始文本
│   └── main.py            # FastAPI 入口点
├── rent_agent_frontend/   # 📱 跨端前端应用 (Vue)
│   ├── pages/             # 页面视图 (扫描、结果、聊天互动)
│   └── uni.scss           # 全局法律商务风样式 (Navy Blue / Safe Green)
├── docs/                  # 📚 产品分析与技术架构深度文档
└── README.md              # 你正在阅读的指南
```

---

## 🤝 参与贡献

**“开源改变世界，AI 回报社会。”** 

无论你是发现了 Bug、有酷炫的 Feature 想法、还是想完善文档，我们都热烈欢迎！这不仅仅是一个校园项目，更是**AI赋能基层社会治理**的探索。

1. **Fork** 本仓库。
2. 创建属于你的特性分支: `git checkout -b feature/AmazingFeature`。
3. 提交你的改动: `git commit -m 'feat: Add some AmazingFeature'`。
4. 推送至分支: `git push origin feature/AmazingFeature`。
5. 发起一个 **Pull Request**！

详细规范请查阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 开源协议

本项目源自对技术的纯粹热爱与对弱势群体的安全承诺。代码遵循 [MIT License](LICENSE) 协议完全开源。

*(注：系统输出不作为正式法律意见，重大纠纷请及时咨询专业律师或诉诸公堂。)*

<div align="center">
  <i>Made with ❤️ by the Qingju Team.</i>
</div>

