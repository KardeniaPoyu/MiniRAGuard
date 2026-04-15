import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.db_tool import (
    init_db,
    create_clue,
    get_clue,
    list_clues,
    update_clue_risk,
    push_clue,
    mark_resolved,
    get_stats,
    save_snapshot
)
from core.chat_tool import chat
from core.rag_tool import retrieve_legal_context
from core.judger import judge_clue
from core.vision_tool import extract_contract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Semaphores mapped to judger process
def get_max_concurrent():
    env_val = os.getenv("MAX_CONCURRENT_ANALYZE")
    if env_val:
        return int(env_val)
    try:
        import psutil
        available_mb = psutil.virtual_memory().available / 1024 / 1024
        return max(1, min(10, int(available_mb / 400)))
    except ImportError:
        return 2

analyze_semaphore = asyncio.Semaphore(get_max_concurrent())

@asynccontextmanager
async def lifespan(app_ctx: FastAPI):
    init_db()
    required_keys = ["DEEPSEEK_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"缺少必要环境变量：{missing}，请检查 .env 文件")

    logger.info("[startup] 预加载 RAG 索引...")
    try:
        retrieve_legal_context("食品安全")
    except Exception as e:
        logger.warning(f"RAG预加载未完成: {e}")
    logger.info("[startup] RAG 索引预加载完成")
    yield

app = FastAPI(lifespan=lifespan)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== Models =====================

class ClueCreate(BaseModel):
    title: str
    source: str
    domain: str
    content: str
    images: Optional[list[str]] = None

class PushRequest(BaseModel):
    department: str

class ResolveRequest(BaseModel):
    feedback: str

class ChatRequest(BaseModel):
    question: str
    context: dict[str, Any]
    history: list[dict[str, Any]]


# ===================== API: Clues =====================

def _do_judger_work(clue_id: int, clue_content: str):
    logger.info(f"开始研判线索 {clue_id}")
    legal_context = retrieve_legal_context(clue_content)
    result = judge_clue(clue_content, legal_context)
    
    update_clue_risk(
        clue_id=clue_id,
        risk_level=result.get("risk_level", "中风险"),
        risk_summary=result.get("risk_summary", ""),
        risk_detail=result
    )
    logger.info(f"线索 {clue_id} 研判完成: {result.get('risk_level')}")

@app.post("/api/clues")
async def api_create_clue(req: ClueCreate, background_tasks: BackgroundTasks):
    content = req.content
    file_md5 = ""
    if req.images:
        pages = []
        for img_b64 in req.images:
            pages.append(extract_contract(img_b64))
        content += "\n\n【附件文字】\n" + "\n\n".join(pages)

    clue_id = create_clue(req.title, req.source, req.domain, content, file_md5)
    
    # Trigger background judger
    async def run_judge():
        async with analyze_semaphore:
            await asyncio.to_thread(_do_judger_work, clue_id, content)

    background_tasks.add_task(run_judge)
    return {"clue_id": clue_id}

@app.post("/api/clues/{id}/judge")
async def api_judge_clue(id: int):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
        
    async with analyze_semaphore:
        await asyncio.to_thread(_do_judger_work, id, clue["content"])
        
    updated_clue = get_clue(id)
    return updated_clue

@app.get("/api/clues/{id}")
async def api_get_clue(id: int):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
    return clue

@app.get("/api/clues")
async def api_list_clues(status: Optional[str] = None, domain: Optional[str] = None, risk_level: Optional[str] = None, limit: int = 50):
    return list_clues(status, domain, risk_level, limit)

@app.post("/api/clues/{id}/push")
async def api_push_clue(id: int, req: PushRequest):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
    push_clue(id, req.department)
    return {"message": "已推送", "department": req.department}

@app.post("/api/clues/{id}/resolve")
async def api_resolve_clue(id: int, req: ResolveRequest):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
    mark_resolved(id, req.feedback)
    return {"message": "已办结"}

@app.get("/api/stats")
async def api_get_stats():
    return get_stats()

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    answer = chat(req.question, req.context, req.history)
    return {"answer": answer}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "vector_store": os.path.exists("./vector_store"),
        "db_status": os.path.exists("./risk_platform.db"),
        "max_concurrent": get_max_concurrent()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
