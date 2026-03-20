import asyncio
import hashlib
import logging
import os
import traceback
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.cache_tool import get_cache_by_md5, get_risk_stats, init_db, set_cache_by_md5, update_risk_stats
from core.chat_tool import chat
from core.rag_tool import retrieve_legal_context
from core.reviewer import review_contract
from core.vision_tool import extract_contract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    images: list[str]


class ChatRequest(BaseModel):
    question: str
    context: dict[str, Any]
    history: list[dict[str, Any]]


def get_max_concurrent():
    # 优先从环境变量读取（部署时可调整）
    env_val = os.getenv("MAX_CONCURRENT_ANALYZE")
    if env_val:
        return int(env_val)
    # 降级：根据可用内存估算
    try:
        import psutil
        available_mb = psutil.virtual_memory().available / 1024 / 1024
        # 每个请求预留 400MB，最少保证 1 个，最多不超过 10 个
        return max(1, min(10, int(available_mb / 400)))
    except ImportError:
        return 2  # psutil 不可用时的保守默认值


analyze_semaphore = asyncio.Semaphore(get_max_concurrent())


@asynccontextmanager
async def lifespan(app_ctx: FastAPI):  # type: ignore[no-untyped-def]
    init_db()

    # 启动时环境变量检查
    required_keys = ["QWEN_API_KEY", "DEEPSEEK_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"缺少必要环境变量：{missing}，请检查 .env 文件")

    # 启动时预加载
    logger.info("[startup] 预加载 RAG 索引...")
    from core.rag_tool import retrieve_legal_context
    retrieve_legal_context("押金 提前退租 维修")  # dry run
    logger.info("[startup] RAG 索引预加载完成")

    yield


app = FastAPI(lifespan=lifespan)

# 生产环境请在 .env 中设置 ALLOWED_ORIGINS=https://your-domain.com
# 多个来源用英文逗号分隔；留空则允许所有来源（仅限开发环境）
_raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request, exc: Exception):  # type: ignore[no-untyped-def]
    logger.error("UNHANDLED_EXCEPTION:", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "服务内部错误，请稍后重试"})


def _do_analyze_work(req: AnalyzeRequest, image_md5: str) -> Any:
    pages: list[str] = []
    for img_b64 in req.images:
        pages.append(extract_contract(img_b64))

    contract_text = "\n\n".join(pages).strip()
    legal_context = retrieve_legal_context(contract_text)
    result = review_contract(contract_text, legal_context)

    result["contract_text"] = contract_text
    update_risk_stats(result.get("analysis_results", []), image_md5)
    set_cache_by_md5(image_md5, result)
    return result


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> Any:
    # 优化三：图片 MD5 层面的精确缓存，跳过提取变动
    image_md5 = hashlib.md5("".join(req.images).encode()).hexdigest()

    cached = get_cache_by_md5(image_md5)
    if cached is not None:
        return cached

    if analyze_semaphore.locked():
        return JSONResponse(
            status_code=429,
            content={
                "error": "当前分析任务较多，请等待约30秒后重试",
                "retry_after": 30
            }
        )

    try:
        async with analyze_semaphore:
            # 增加 180 秒的超时保护，熔断同步阻塞线程
            result = await asyncio.wait_for(
                asyncio.to_thread(_do_analyze_work, req, image_md5),
                timeout=180.0
            )
            return result
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=408,
            content={"error": "分析超时，请重试"}
        )
    except ValueError as e:
        if str(e) == "NOT_CONTRACT":
            return JSONResponse(
                status_code=400,
                content={"error": "请上传合同图片，检测到非合同内容"},
            )
        raise


@app.post("/api/chat")
async def chat_api(req: ChatRequest) -> dict[str, str]:
    answer = chat(req.question, req.context, req.history)
    return {"answer": answer}


@app.get("/api/risk-stats")
async def risk_stats_api() -> list:
    return get_risk_stats()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "vector_store": os.path.exists("./vector_store"),
        "cache_db": os.path.exists("./cache.db"),
        "qwen_key_set": bool(os.getenv("QWEN_API_KEY")),
        "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
        "max_concurrent": get_max_concurrent()
    }


if __name__ == "__main__":
    # 本地调试用（reload=True 仅限开发）；生产环境请使用 Dockerfile CMD 启动
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# -----------------------------
# .env 模板（示例值请自行替换）
# -----------------------------
#
# # Qwen-VL（阿里云 DashScope 兼容模式）
# # QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# # QWEN_MODEL=qwen-vl-max
# # QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
#
# # DeepSeek
# # DEEPSEEK_BASE_URL=https://api.deepseek.com
# # DEEPSEEK_MODEL=deepseek-chat
# # DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

MAX_CONCURRENT_ANALYZE=2   # 1GB内存填2，2GB内存填3

