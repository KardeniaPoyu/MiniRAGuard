# MiniRaguard Backend | MiniRaguard后端

基于 FastAPI 构建的高性能法律风险审查引擎。

## 🛠️ 核心功能

1.  **多模态合同解析**：利用 `Qwen-VL-Max` 进行高精度 OCR，支持手写、模糊照片等复杂场景。
2.  **RAG 法律知识增强**：
    - 使用 `Sentence-Transformers` 进行本地向量化。
    - 针对《民法典》、《租赁条例》等法规进行切片检索。
    - 确保 AI 回复具备法律依据，规避幻觉。
3.  **智能判别系统**：调用 `DeepSeek-Chat` 进行结构化风险分析。
4.  **性能优化**：
    - **MD5 缓存**：相同文件不重复解析，节省算力。
    - **并发限流**：针对大模型调用进行信号量控制，防止服务器过载。

## ⚙️ 环境配置

在根目录下创建 `.env` 文件（参考 `.env.example`）：

```env
QWEN_API_KEY=你的阿里云Key
DEEPSEEK_API_KEY=你的DeepSeek Key
ALLOWED_ORIGINS=允许访问的前端域名
MAX_CONCURRENT_ANALYZE=并发数
```

## 🚀 启动指引

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行开发服务器
```bash
python main.py
```
默认运行在 `http://127.0.0.1:8000`。

## 📚 API 文档

启动后访问 `http://127.0.0.1:8000/docs` 查看 Swagger 文档。

### 主要接口：
- `POST /api/analyze`：合同上传与分析。
- `POST /api/chat`：法律咨询对话。
