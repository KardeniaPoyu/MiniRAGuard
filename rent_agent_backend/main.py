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
    seed_mock_data,
    create_clue,
    update_clue_alert,
    get_clue,
    list_clues,
    update_clue_risk,
    create_collaboration_task,
    feedback_collaboration_task,
    mark_resolved,
    get_stats,
    DB_PATH
)
from core.chat_tool import chat
from core.rag_tool import retrieve_legal_context
from core.judger import judge_clue
from core.alerter import trigger_alert
from core.vision_tool import extract_contract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

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
    seed_mock_data()  # 植入种子数据
    required_keys = ["DEEPSEEK_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"缺少必要环境变量：{missing}，请检查 .env 文件")

    logger.info("[startup] 预加载 RAG 索引...")
    try:
        retrieve_legal_context("拖欠工资")
    except Exception as e:
        logger.warning(f"RAG预加载未完成: {e}")
    logger.info("[startup] RAG 索引预加载完成")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================== Models =====================

class IngestClue(BaseModel):
    title: str
    source: str
    domain: str
    content: str
    enterprise_name: Optional[str] = ""
    personnel_count: Optional[int] = 1
    amount: Optional[float] = 0.0

class PushTaskRequest(BaseModel):
    to_dept: str
    req_content: str

class FeedbackTaskRequest(BaseModel):
    feedback: str
    evidence_urls: Optional[list[str]] = []

class ChatRequest(BaseModel):
    question: str
    context: dict[str, Any]
    history: list[dict[str, Any]]


# ===================== API: Ingest & Alert =====================

def _do_alert_work(clue_id: int):
    # Rule engine evaluation immediately after ingest
    clue = get_clue(clue_id)
    if not clue: return
    
    # 算一下该企业被投诉多少次(历史单量)
    import sqlite3
    duplicate_count = 0
    if clue.get("enterprise_name"):
        with sqlite3.connect(DB_PATH) as conn:
            duplicate_count = conn.execute("SELECT COUNT(*) FROM clues WHERE enterprise_name=?", (clue["enterprise_name"],)).fetchone()[0]
    
    alert_level, factors = trigger_alert(
        clue_content=clue["content"], 
        personnel_count=clue["personnel_count"], 
        amount=clue["amount"], 
        source=clue["source"], 
        duplicate_enterprise_count=duplicate_count
    )
    
    update_clue_alert(clue_id, alert_level, factors)
    logger.info(f"线索 {clue_id} 预警分析完成: {alert_level}")

@app.post("/api/ingest")
async def api_ingest_clue(req: IngestClue, background_tasks: BackgroundTasks):
    """用于12345流水线或外部平台结构化数据汇入，入口执行自动红黄蓝预警拦截"""
    clue_id = create_clue(
        title=req.title, source=req.source, domain=req.domain, content=req.content,
        enterprise_name=req.enterprise_name, personnel_count=req.personnel_count, amount=req.amount
    )
    background_tasks.add_task(_do_alert_work, clue_id)
    return {"clue_id": clue_id, "message": "收到数据，正在规则引擎预警中"}

# ===================== API: Judger =====================

def _do_judger_work(clue_id: int):
    clue = get_clue(clue_id)
    if not clue: return
    
    logger.info(f"开始 AI 检务研判线索 {clue_id}")
    legal_context = retrieve_legal_context(clue["content"])
    result = judge_clue(
        title=clue["title"],
        enterprise=clue["enterprise_name"],
        amount=clue["amount"],
        count=clue["personnel_count"],
        clue_content=clue["content"],
        legal_context=legal_context
    )
    
    update_clue_risk(
        clue_id=clue_id,
        risk_level=result.get("risk_level", "中风险"),
        risk_summary=result.get("risk_summary", ""),
        risk_detail=result,
        case_type=result.get("case_type", "行政监督线索")
    )
    logger.info(f"线索 {clue_id} 研判完成: {result.get('case_type')}")

@app.post("/api/clues/{id}/judge")
async def api_judge_clue(id: int):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
        
    async with analyze_semaphore:
        await asyncio.to_thread(_do_judger_work, id)
        
    updated_clue = get_clue(id)
    return updated_clue

# ===================== API: Query =====================

@app.get("/api/clues/{id}")
async def api_get_clue(id: int):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
    return clue

@app.get("/api/clues")
async def api_list_clues(status: Optional[str] = None, alert_level: Optional[str] = None, case_type: Optional[str] = None, limit: int = 50):
    return list_clues(status, alert_level, case_type, limit)

@app.get("/api/stats")
async def api_get_stats():
    return get_stats()

# ===================== API: Collaboration =====================

@app.post("/api/clues/{id}/push_task")
async def api_push_task(id: int, req: PushTaskRequest):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
    task_id = create_collaboration_task(id, req.to_dept, req.req_content)
    return {"message": "协同信函已发送", "task_id": task_id}

@app.post("/api/tasks/{task_id}/feedback")
async def api_feedback_task(task_id: int, req: FeedbackTaskRequest):
    feedback_collaboration_task(task_id, req.feedback, req.evidence_urls)
    return {"message": "反馈已提交"}

@app.post("/api/clues/{id}/resolve")
async def api_resolve_clue(id: int):
    mark_resolved(id)
    return {"message": "已结案打标"}

# ===================== API: Other =====================

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    answer = chat(req.question, req.context, req.history)
    return {"answer": answer}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "max_concurrent": get_max_concurrent()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
