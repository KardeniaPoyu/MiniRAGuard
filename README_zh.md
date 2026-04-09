<div align="center">
  <!-- <img src="./docs/assets/banner.png" width="100%" alt="MiniRAGuard Banner"> -->

  <h1>🛡️ MiniRAGuard</h1>

  <p>
    <strong>A Plug-and-Play Multimodal RAG Guardrail Framework</strong><br>
    <em>让任何人用 10 分钟，从零构建企业级文档智能风控系统。</em>
  </p>

  <p>
    <a href="https://github.com/KardeniaPoyu/MiniRAGuard/stargazers"><img src="https://img.shields.io/github/stars/KardeniaPoyu/MiniRAGuard?style=for-the-badge&color=F3DFA2&logo=github" alt="Stars"></a>
    <a href="https://github.com/KardeniaPoyu/MiniRAGuard/network/members"><img src="https://img.shields.io/github/forks/KardeniaPoyu/MiniRAGuard?style=for-the-badge&color=7E8D85&logo=github" alt="Forks"></a>
    <a href="https://github.com/KardeniaPoyu/MiniRAGuard/issues"><img src="https://img.shields.io/github/issues/KardeniaPoyu/MiniRAGuard?style=for-the-badge&color=E8C8CD&logo=github" alt="Issues"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=B0C4B1" alt="License"></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/UniApp-2B9939?style=flat-square&logo=vuedotjs" alt="UniApp">
    <img src="https://img.shields.io/badge/DeepSeek-0d6efd?style=flat-square" alt="DeepSeek">
    <img src="https://img.shields.io/badge/Qwen__VL-ff6a00?style=flat-square" alt="Qwen-VL">
  </p>

[**English**](./README.md) | [**简体中文**](./README_zh.md)

</div>

<br/>

## ✨ 什么是 MiniRAGuard?

在各类垂直领域（医疗审核、财务报表、信访维权、合同法务），我们经常面临三大阻碍：**图片数据模糊**、**大模型幻觉频发**、**高并发难以承载**。

**MiniRAGuard** 提供了一个**极轻量、开箱即用**的开源全栈解决方案（后端分析引擎 + 跨端小程序）。它创新性地结合了 **VLM (大视觉模型)** 和 **RAG (检索增强生成)**，强制 AI 基于你的本地知识库进行事实推理。

无论你是想搭建一个“医疗单据智审助手”，还是“社区民情研判总机”，只需**扔进你的 TXT 库，修改一段 Prompt**，即可立刻上线。

---

## 🚀 业务实例演示 (Demo)

以自带的 **“单据/合同合规风控助手”** 实例为演示：

![MiniRAGuard Demo](./demo.mp4)

<br/>

## 🔥 核心功能

- **基于 Qwen-VL API 的深度视觉提取 (Vision LLM)**
  系统化集成 Qwen-VL API 进行文档识别，直接规避传统 OCR 在复杂排版或模糊单据上的识别错误。
- **结合本地知识库的 RAG 推理护栏 (Fact-based RAG)**
  针对医疗、财务等严谨场景，通过 Sentence-Transformers 检索私有向量库（VectorDB），强制模型进行基于事实的“智审”，彻底杜绝常识性幻觉。
- **动态缓存命中与并发流控 (Performance & Tech)**
  - **MD5 热缓存命中**：自动比对上传文件指纹，对于重复任务实现 **100% 缓存命中回调**，极大程度节省 Token 消耗与计算时长。
  - **基于信号量的并发保护**：防止突发请求导致内存溢出或 API 熔断，保障系统在高压环境下的业务可用性。
- **开箱即用的极简全栈架构 (Full-Stack Support)**
  提供 FastAPI (Backend) 与 UniApp (Frontend) 完整代码，开发者仅需修改 Prompt 定位即可快速平移至其他审核业务场景。

---

## 🏗️ 技术架构

秉承高内聚、低耦合的优雅设计理念，业务流如丝般顺滑：

```mermaid
graph TD
    User((Client Device)) -->|Upload Image Base64| API_Gateway[FastAPI Gateway]
    
    subgraph Modular AI Pipeline
        API_Gateway -->|1. Vision Parse| VL[VLM Engine]
        VL -->|2. High-confidence Text| RAG_Engine[Lightweight RAG]
        
        subgraph Local Knowledge Base
            RAG_Engine <-->|3. Chunk Match| VectorDB[(Local Vector Store)]
        end
        
        RAG_Engine -->|4. Strict Context| LLM[Generative DL DeepSeek]
    end
    
    LLM -->|5. Structured JSON| API_Gateway
    API_Gateway -->|6. Dynamic Rendering| User
```

---

## 🚀 快速开始

构建你的 AI 应用？只需十分钟！

### 1. 部署高可用后端 (Backend)

```bash
# 1. 克隆代码仓库
git clone https://github.com/KardeniaPoyu/MiniRAGuard.git
cd MiniRAGuard/backend

# 2. 安装 Python 依赖 
pip install -r requirements.txt

# 3. 环境变量配置 (填入你的 API KEY)
cp .env.example .env

# 4. 一键起飞！
python main.py
```
> 👉 访问 `http://localhost:8000/docs` 查看交互式 API 文档。

### 2. 部署跨端客户端 (Frontend)

1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html) IDE。
2. 将 `frontend` 目录导入。
3. 修改 `config.js` 中的 `BASE_URL` 为你刚刚部署的后端服务地址。
4. 一键运行至内置浏览器或微信开发者工具！

---

## 🛠️ 打造你自己的应用
把这套框架变成你的专属利器！黄金三步走：

1. **注入私有知识**：清空 `backend/data/` 目录，扔进符合你业务场景的 TXT 或 Markdown 手册。
2. **清理缓存重塑**：删除 `backend/cache.db` 和 `vector_store/` 目录，系统下次启动将自动“消化”新知识。
3. **注入灵魂 Prompt**：打开 `backend/core/chat_tool.py`，更改顶栏的 System Prompt 定位。（比如从“风控顾问”改成“三甲医院财务报销审核员”）。

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=KardeniaPoyu/MiniRAGuard&type=Date)](https://star-history.com/#KardeniaPoyu/MiniRAGuard&Date)

---

## 🤝 参与贡献与开源协议

**“致敬开源精神。”**

无论你是修补了一个拼写错误，还是在你的业务中用 MiniRAGuard 做出了惊艳的落地应用，我们都期待你的 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

本项目采用 **[MIT](LICENSE)** 开源协议。如果你觉得这个项目对你有帮助，不妨点一个 ⭐ **Star** 鼓励一下作者！

