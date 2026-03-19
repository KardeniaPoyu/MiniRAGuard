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

from core.cache_tool import get_cache_by_md5, init_db, set_cache_by_md5
from core.chat_tool import chat
from core.rag_tool import retrieve_legal_context
from core.reviewer import review_contract
from core.vision_tool import extract_contract

logger = logging.getLogger("uvicorn")


class AnalyzeRequest(BaseModel):
    images: list[str]


class ChatRequest(BaseModel):
    question: str
    context: dict[str, Any]
    history: list[dict[str, Any]]


@asynccontextmanager
async def lifespan(app_ctx: FastAPI):  # type: ignore[no-untyped-def]
    init_db()

    # 启动时预加载
    import logging
    logger = logging.getLogger("uvicorn")
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
    print("UNHANDLED_EXCEPTION:", repr(exc))
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": "服务内部错误，请稍后重试"})


def _do_analyze_work(req: AnalyzeRequest, image_md5: str) -> Any:
    pages: list[str] = []
    for img_b64 in req.images:
        pages.append(extract_contract(img_b64))

    contract_text = "\n\n".join(pages).strip()
    legal_context = retrieve_legal_context(contract_text)
    result = review_contract(contract_text, legal_context)

    set_cache_by_md5(image_md5, result)
    return result


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> Any:
    # 优化三：图片 MD5 层面的精确缓存，跳过提取变动
    image_md5 = hashlib.md5("".join(req.images).encode()).hexdigest()

    cached = get_cache_by_md5(image_md5)
    if cached is not None:
        return cached

    try:
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

