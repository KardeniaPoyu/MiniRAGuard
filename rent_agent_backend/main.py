from __future__ import annotations

import logging
import time
import traceback
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.cache_tool import get_cache, init_db, set_cache
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


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request, exc: Exception):  # type: ignore[no-untyped-def]
    print("UNHANDLED_EXCEPTION:", repr(exc))
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": "服务内部错误，请稍后重试"})


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> Any:
    try:
        pages: list[str] = []
        for img_b64 in req.images:
            pages.append(extract_contract(img_b64))
    except ValueError as e:
        if str(e) == "NOT_CONTRACT":
            return JSONResponse(
                status_code=400,
                content={"error": "请上传合同图片，检测到非合同内容"},
            )
        raise

    contract_text = "\n\n".join(pages).strip()
    cached = get_cache(contract_text)
    if cached is not None:
        return cached

    legal_context = retrieve_legal_context(contract_text)
    result = review_contract(contract_text, legal_context)

    set_cache(contract_text, result)
    return result


@app.post("/api/chat")
async def chat_api(req: ChatRequest) -> dict[str, str]:
    answer = chat(req.question, req.context, req.history)
    return {"answer": answer}


if __name__ == "__main__":
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

