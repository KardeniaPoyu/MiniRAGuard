<div align="center">
  <!-- TODO: 添加项目高分辨率 Logo 或 横幅图像 -->
  <!-- <img src="./docs/assets/banner.png" width="100%" alt="Qingju Banner"> -->

  <h1>🏠 青居 (Qingju) - 多模态 RAG 万能审查框架</h1>

  <p>
    <strong>一个基于 FastAPI + UniApp + VLM(大视觉模型) + RAG 的通用文档智能审查全栈模板</strong>
  </p>

  <p>
    🛡️ 开箱即用 | 📖 本地知识库增强 | 👁️ 多模态 OCR | 💬 智能多轮对话
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

- [✨ 框架愿景](#-框架愿景)
- [🖼️ 业务实例演示 (Demo)](#-业务实例演示-demo)
- [🌟 核心范式与优势](#-核心范式与优势)
- [🏗️ 技术架构](#-技术架构)
- [🚀 快速开始](#-快速开始)
- [📈 如何二次开发](#-如何进行二次开发改造)
- [🤝 参与贡献](#-参与贡献)
- [📄 开源协议](#-开源协议)

---

## ✨ 框架愿景

**“青居 (Qingju)”** 不仅仅是一个保护大学生的**租房合同审查工具**，它更是一个**泛用的多模态文档风控与解析模板**。

在基层社会治理、法务审核、投诉信访处理等场景中，经常面临“文档图片模糊”、“难以准确匹配法规”、“大模型幻觉严重”等共同痛点。本项目为你提供了一套可复用的标准全栈架构（`UniApp 小程序` + `FastAPI 并发服务端` + `VLM 视觉抽取` + `RAG 法律风控`）。你只需替换后端的知识库（TXT/MD文件）和稍微调整 Prompt，即可在 **10 分钟内** 将其改造为你专属领域的 AI 智能审查助手！

**📢 适用领域：** `基层社会治理风控平台` / `信访/调解意图分析工具` / `商业合同审查系统` / `AI 医疗单据诊断助手`

---

## 🖼️ 业务实例演示 (Demo)

为了展示框架的能力，本项目默认自带了 **“租房合同法律风险审查系统（青居智选）”** 这一具体实例。

👉 **[点击这里下载或观看演示视频](./demo.mp4)**

https://github.com/KardeniaPoyu/Qingju/raw/main/demo.mp4

<div align="center">
  <table>
    <tr>
      <td align="center"><b>📸 拍照 / 截图上传</b></td>
      <td align="center"><b>⚠️ 领域知识 RAG 匹配</b></td>
      <td align="center"><b>💬 多轮上下文追问</b></td>
    </tr>
  </table>
</div>
*通过该实例你可以看到，前端负责采集非结构化图像，后端 VLM 提取文本后，RAG 引擎从《民法典》中寻找依据，最终 DeepSeek 输出高亮风险与白话解读。*

---

## 🌟 核心范式与优势

- 🧩 **高度模块化的 Pipeline**：将业务逻辑抽象为 `上传 -> 视觉 OCR -> RAG 检索 -> LLM 推理 -> 结果渲染` 的单向数据流，极易解耦。
- 👁️ **端云协同的视觉基座**：彻底抛弃传统 OCR 易错漏的毛病，全面接入 **Qwen-VL-Max**，即使你的源文件是手写草书或是逆光拍摄，依然能精准识字。
- 🛡️ **拒止幻觉的设计**：强制 AI 推理必须基于 `Sentence-Transformer` 给出的本地领域知识切片，做到**“结论皆有出处”**。
- ⚡ **为高并发而生的极客后端**：
  - **MD5 热缓存**：用户反复上传或刷新历史报表，不再重新消耗大模型 Token，直接秒级出结果。
  - **动态信号量**：大模型接口极易被并发冲垮，我们内置了内存感知的并发锁，保护你的云服务器稳定运行。

---

## 🏗️ 技术架构

本框架是一套设计优雅的前后端分离系统：

```mermaid
graph TD
    User((用户/一线人员)) -->|多模态数据输入| MP[微信小程序 / Web / H5 (基于 Uni-app)]
    MP -->|统一分析接口| API_Gateway[FastAPI 核心调度层]
    
    subgraph AI Pipeline (可插拔)
        API_Gateway -->|1. 解析| VL[VLM 视觉模型: 图片转置信文本]
        VL -->|2. 检索| RAG_Engine[轻量级 RAG 检索器]
        
        subgraph 本领域私有知识库 📚
            RAG_Engine <-->|3. 计算相似度| VectorDB[(本地轻量级向量切片)]
            VectorDB -.自动生成.-> RawDocs[你的 TXT/ Markdown 文档档案]
        end
        
        RAG_Engine -->|4. 推理(Context + 条文)| LLM[生成式大模型 (DeepSeek等)]
    end
    
    LLM -->|5. 标准化 JSON 返回| API_Gateway
    API_Gateway -->|6. 动态渲染| MP
```

---

## 🚀 快速开始

克隆这套模板，在本地启动你的第一个 AI 全栈应用：

### 🔧 1. 后端部署 (FastAPI 原生风控引擎)

环境要求：`Python 3.9+`

```bash
# 1. 克隆项目
git clone https://github.com/KardeniaPoyu/Qingju.git
cd Qingju/rent_agent_backend

# 2. 安装环境依赖
pip install -r requirements.txt

# 3. 环境变量配置
cp .env.example .env
# 编辑 .env 文件，填入模型 API 密钥（默认支持 QWEN_VL 和 DEEPSEEK）

# 4. 启动服务 (默认端口 8000)
python main.py
```

🎉 启动后，访问 `http://localhost:8000/docs` 使用 Swagger 测试。

### 📱 2. 前端部署 (Uni-app 跨端展示)

1. 请使用 [HBuilderX](https://www.dcloud.io/hbuilderx.html) 导入 `rent_agent_frontend` 目录。
2. 打开 `config.js`，将 `BASE_URL` 指向你的后端接口。
3. 点击“运行 - 运行到小程序模拟器”！

---

## 📈 如何进行二次开发 (改造你的专属业务)

这是将本框架改造为**“基层信访/社会治理诉求分析平台”**或**“商业合同助手”**的黄金三步：

1. **替换领域知识**：清空 `rent_agent_backend/data/` 中的法律文件，放入你的业务文件（如：物业管理条例、劳动法、社区投诉处理手册）。
2. **重置缓存与向量**：删除 `rent_agent_backend/cache.db` 和 `vector_store/` 目录。系统再次启动时会自动消费你的新知识库。
3. **微调提示词 (Prompt)**：修改 `rent_agent_backend/core/chat_tool.py` 中的 System Prompt，让大模型的角色从“租房顾问”转变为“医保审核员”或“社区网格员”！

---

## 🤝 参与贡献

**“开源改变世界，AI 回报社会。”** 

无论你是想完善这个全栈生态，还是在你的领域基于该模板落地了惊艳的项目，我们都期待你的 Pull Request 与 Issue！

1. Fork 本仓库
2. 创建特性分支: `git checkout -b feature/NewBusinessScenario`
3. 提交改动: `git commit -m 'feat: Add support for X'`
4. 推送: `git push origin feature/NewBusinessScenario`
5. 提交 PR 🚀

---

## 📄 开源协议

本项目代码遵循 [MIT License](LICENSE) 协议完全开源。

*(注：系统默认搭载的“租房审查”实例仅作技术演示，输出不作为正式法律意见。)*

<div align="center">
  <i>Made with ❤️ by the Qingju Team.</i>
</div>


