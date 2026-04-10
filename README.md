<div align="center">
  <!-- <img src="./docs/assets/banner.png" width="100%" alt="MiniRAGuard Banner"> -->

  <h1>🛡️ MiniRAGuard</h1>

  <p>
    <strong>A Lightweight Full-stack RAG Audit Agent Template</strong><br>
    <em>Build your own vertical multimodal AI RAG audit assistant in just 10 minutes.</em>
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

## 📖 Table of Contents

- [✨ What is MiniRAGuard?](#-what-is-miniraguard)
- [🔥 Core Highlights](#-core-highlights)
- [🏗️ Architecture](#-architecture)
- [🚀 Quick Start](#-quick-start)
- [🛠️ Build Your Own AI Agent](#-build-your-own-ai-agent)
- [🤝 Contributing & License](#-contributing--license)

---

## ✨ What is MiniRAGuard?

In **vertical audit fields** such as medical auditing, financial reporting, and petition review, developers often face three major pain points: **unstructured/blurry image data**, **frequent LLM hallucinations**, and **difficulty handling high-concurrency requests**.

Addressing these issues, **MiniRAGuard** provides a **lightweight, out-of-the-box** full-stack RAG business template. By combining **VLM (Vision Large Models)** with **RAG (Retrieval-Augmented Generation)**, it forces the AI to reason strictly based on your local knowledge base, helping developers quickly integrate document retrieval and output constraint mechanisms into vertical applications.

**MiniRAGuard** aims to provide engineering certainty and boundary control for complex document review processes powered by LLMs. It includes not only a minimalist RAG implementation but also a complete business showcase UI. Simply **drop your TXT files into the library and modify a single Prompt** to launch your specialized assistant. Launch and deploy a WeChat mini-program or website in just ten minutes—perfect for beginners to learn the RAG architecture.

---

## 🚀 Business Instance Demo

Demonstrating with the built-in **"Receipt/Contract Compliance Risk Assistant"** instance:

<video src="./demo.mp4" width="100%" controls></video>

<br/>

## 🔥 Core Highlights

- **Fact-based RAG Search & Generation**  
  Specifically for legal, financial, and other serious scenarios, the system uses Sentence-Transformers to build a local vector database (VectorDB). The LLM retrieves relevant regulations from the local database before reasoning, significantly reducing "hallucinations" and providing concrete sources for judgments.
- **Out-of-the-box Multimodal Document Access**  
  Integrated mainstream VLM interface call logic (default Qwen-VL API), supporting direct upload of contract scans, images, or PDFs to quickly extract key information. No need to write complex multimodal parsing code from scratch.
- **Lightweight Compliance Review Workflow**  
  Built-in basic "review-feedback" Prompt template design, effectively constraining output boundaries for sensitive texts (like leases or boilerplate clauses). Ideal for business-side PoCs (Proof of Concept).
- **Full-stack Scaffold with Separated Frontend/Backend**  
  Provides complete production-grade source code for `backend` (FastAPI) and `frontend` (Vue/UniApp). Developers can learn RAG implementation while having a ready-to-use UI for demonstrations to stakeholders.
- **Concurrency & Cache Control (Concurrency & Caching)**
  - **MD5 Caching Mechanism**: Intercepts repeated verifications by calculating file MD5, reducing unnecessary API Token consumption and latency.
  - **Semaphore Flow Control**: Backend thread flow control ensures stable service operation during traffic spikes by limiting concurrent requests to the LLM.

---

## 🏗️ Architecture

Adhering to high cohesion and low coupling design principles, ensuring a silky smooth business flow:

```mermaid
graph TD
    User((Client)) -->|Upload Images| API_Gateway[FastAPI Gateway]
    
    subgraph Modular AI Pipeline
        API_Gateway -->|1. Vision Parse| VL[VLM Engine]
        VL -->|2. Text Content| RAG_Engine[Lightweight RAG]
        
        subgraph Local Knowledge Base
            RAG_Engine <-->|3. Knowledge Match| VectorDB[(Local Vector Store)]
        end
        
        RAG_Engine -->|4. Augmented Context| LLM[DeepSeek Model]
    end
    
    LLM -->|5. Structured Result| API_Gateway
    API_Gateway -->|6. Dynamic Rendering| User
```

---

## 🚀 Quick Start

### 1. Deploy Backend

```bash
# 1. Clone the repository
git clone https://github.com/KardeniaPoyu/MiniRAGuard.git
cd MiniRAGuard/backend

# 2. Install Python dependencies 
pip install -r requirements.txt

# 3. Environment configuration (Add your API KEY)
cp .env.example .env

# 4. Launch!
python main.py
```
> 👉 Visit `http://localhost:8000/docs` to view the interactive API documentation.

### 2. Deploy Frontend

1. Download the [HBuilderX](https://www.dcloud.io/hbuilderx.html) IDE.
2. Import the `frontend` directory.
3. Update `BASE_URL` in `config.js` to your deployed backend address.
4. Run in the built-in browser or WeChat DevTools!

---

## 🛠️ Build Your Own AI Agent

1. **Inject Private Knowledge**: Clear `backend/data/` and add your own TXT or Markdown manuals.
2. **Rebuild Vector Index**: Delete the `vector_store/` directory; it will be automatically rebuilt on the next startup.
3. **Adjust Business Logic**: Modify the System Prompt in `backend/core/chat_tool.py`.

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=KardeniaPoyu/MiniRAGuard&type=Date)](https://star-history.com/#KardeniaPoyu/MiniRAGuard&Date)

## 🤝 Contributing & License

Whether you fixed a typo or built an amazing application in a vertical field using MiniRAGuard, we look forward to your Pull Request! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

This project is licensed under the **[MIT](LICENSE)** license. If you find this project helpful, please give it a ⭐ **Star** for encouragement!
