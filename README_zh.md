<div align="center">
  <!-- <img src="./docs/assets/banner.png" width="100%" alt="MiniRAGuard Banner"> -->

  <h1>🛡️ MiniRAGuard</h1>

  <p>
        <strong>轻量级全栈 RAG 审查智能体模板</strong><br>
    <em>让任何人用 10 分钟，快速搭建属于自己的垂直领域多模态 AI RAG审查助手。</em>
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

[**English**](./README.md) | [**简体中文**](./README_zh.md) | [**日本語**](./README_ja.md)

</div>

<br/>

## 📖 目录

- [✨ 什么是 MiniRAGuard？](#-什么是-miniraguard)
- [🔥 核心亮点](#-核心亮点)
- [🏗️ 技术架构](#-技术架构)
- [🚀 快速开始](#-快速开始)
- [🛠️ 打造属于你的 AI 智能体](#-打造属于你的-ai-智能体)
- [🤝 贡献与许可](#-贡献与许可)

---

## ✨ 什么是 MiniRAGuard？

在医疗审核、财务报表、信访审查等**垂直审核领域**，开发者常面临三大痛点：**图像数据模糊无序**、**LLM 幻觉频发**、**高并发请求难处理**。

针对这三点，**MiniRAGuard** 提供了一个**极轻量、开箱即用**的全栈 RAG 业务模板。它将 **VLM（视觉大模型）** 与 **RAG（检索增强生成）** 相结合，强迫 AI 严格基于你的本地知识库进行推理，帮助开发者快速为垂直领域应用接入文档检索与输出约束机制。

**MiniRAGuard** 旨在为 LLM 赋能的复杂文档审查流程提供工程上的确定性与边界控制。它不仅包含一个极简的 RAG 实现，还自带了完整的业务展示界面。只需**将 TXT 放入库中并修改一段 Prompt**，即可上线属于你的垂直领域助手，十分钟完成一个微信小程序/网站的上线及部署，非常方便初学者学习 RAG 架构。

---

## 🚀 业务实例演示 (Demo)

以自带的 **“单据/合同合规风控助手”** 实例为演示：

<video src="./demo.mp4" width="100%" controls></video>

<br/>

## 🔥 核心功能

- **结合本地知识库的 RAG 检索生成 (Fact-based RAG)**
  针对法务、财务等严肃场景，系统使用 Sentence-Transformers 构建本地向量数据库（VectorDB）。大模型在进行推理前会优先从本地数据库检索相关的规范条例，从而减少常识性“幻觉”并提供具体的判断出处。
- **开箱即用的多模态文档接入**  
  集成了主流的 VLM 接口调用逻辑（默认Qwen-VL API），支持直接上传合同扫描件、图片或 PDF，快速提取关键信息，开发者无需从零编写复杂的多模态解析代码。
- **轻量级合规审查工作流**  
  内置了一套基础的“审查-反馈” Prompt 模板设计，能有效约束大模型在处理敏感文本（如租约、格式条款）时的输出边界，非常适合进行业务侧的 PoC（概念验证）。
- **前后端分离的完整业务脚手架**  
  提供 `backend` (FastAPI) 和 `frontend` (Vue/UniApp) 完整的工程化源码。开发者不仅能学到 RAG 怎么写，还能直接拥有一套可以直接向老板或导师演示的 UI 界面。
- **基本并发与缓存控制 (Concurrency & Caching)**
  - **MD5 缓存机制**：计算文件 MD5，拦截重复文件的校验请求并直接返回本地缓存，减少不必要的 LLM API 调用开销及响应时间。
  - **并发信号量控制**：后端部署了基于信号量的线程流控机制，限制高并发场景下抛向大模型的并发数，保障服务稳定运行。

---

## 🏗️ 技术架构

秉承高内聚、低耦合的优雅设计理念，业务流如丝般顺滑：

```mermaid
graph TD
    User((客户端)) -->|上传图片| API_Gateway[FastAPI 网关]
    
    subgraph 模块化 AI 管道
        API_Gateway -->|1. 视觉解析| VL[VLM 引擎]
        VL -->|2. 文本内容| RAG_Engine[轻量级 RAG]
        
        subgraph 本地知识库
            RAG_Engine <-->|3. 知识匹配| VectorDB[(本地向量库)]
        end
        
        RAG_Engine -->|4. 增强上下文| LLM[执行模型 DeepSeek]
    end
    
    LLM -->|5. 结构化结果| API_Gateway
    API_Gateway -->|6. 动态呈现| User
```

---

## 🚀 快速开始

### 1. 部署后端 (Backend)

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

### 2. 部署前端 (Frontend)

1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html) IDE。
2. 将 `frontend` 目录导入。
3. 修改 `config.js` 中的 `BASE_URL` 为你刚刚部署的后端服务地址。
4. 一键运行至内置浏览器或微信开发者工具！

---

## 🛠️ 打造属于你的 AI 智能体

1. **注入私有知识**：清空 `backend/data/`，放入你的 TXT 或 Markdown 手册。
2. **重建向量索引**：删除 `vector_store/` 目录，下次启动将自动重新构建。
3. **调整业务逻辑**：修改 `backend/core/chat_tool.py` 中的 System Prompt。

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=KardeniaPoyu/MiniRAGuard&type=Date)](https://star-history.com/#KardeniaPoyu/MiniRAGuard&Date)

## 🤝 参与贡献与开源协议

无论你是修补了一个拼写错误，还是在你的业务中用 MiniRAGuard 做出了惊艳的落地应用，我们都期待你的 Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

本项目采用 **[MIT](LICENSE)** 开源协议。如果你觉得这个项目对你有帮助，不妨点一个 ⭐ **Star** 鼓励一下作者！

