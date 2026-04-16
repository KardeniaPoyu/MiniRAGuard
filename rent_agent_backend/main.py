import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from core.db_tool import (
    init_db,
    seed_mock_data,
    seed_users,
    create_clue,
    update_clue_alert,
    get_clue,
    list_clues,
    update_clue_risk,
    create_push_record,
    feedback_push_record,
    mark_resolved,
    get_stats,
    get_user_by_username,
    create_audit_log,
    get_audit_logs,
    create_notification,
    get_unread_notifications,
    mark_notifications_read,
    DB_PATH
)
from core.chat_tool import chat
from core.rag_tool import retrieve_legal_context
from core.judger import judge_clue
from core.alerter import trigger_alert
from core.vision_tool import extract_contract
from core.auth_tool import verify_password, create_access_token, decode_access_token

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
    seed_mock_data()  
    seed_users()  # 植入测试用户
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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), request: Request = None):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的 Token")
    username = payload.get("sub")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ===================== Models =====================

class IngestClue(BaseModel):
    title: str
    source: str
    domain: str
    content: str
    enterprise_name: Optional[str] = ""
    personnel_count: Optional[int] = 1
    amount: Optional[float] = 0.0
    claimant_privacy: Optional[str] = '公开'
    images: Optional[list[str]] = []

class PushTaskRequest(BaseModel):
    to_dept: str
    req_content: str
    password: str

class FeedbackTaskRequest(BaseModel):
    feedback: str
    evidence_urls: Optional[list[str]] = []

class ChatRequest(BaseModel):
    question: str
    context: dict[str, Any]
    history: list[dict[str, Any]]


# ===================== API: Auth =====================

@app.post("/api/auth/login")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(400, "用户名或密码错误")
    
    ip = request.client.host if request.client else ""
    create_audit_log(user["username"], "登录系统", "成功登录", ip)
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"], "role": current_user["role"]}


# ===================== API: Logs =====================

@app.get("/api/logs")
async def api_get_logs(current_user: dict = Depends(get_current_user)):
    # Everyone can see logs for MVP demonstration
    return get_audit_logs()

# ===================== API: Ingest & Alert =====================

def _do_alert_work(clue_id: int):
    clue = get_clue(clue_id)
    if not clue: return
    
    amount = clue.get("amount", 0.0)
    if amount >= 100000:
        alert_level = "红色预警"
        factors = [{"factor": "涉案金额特别巨大", "desc": "总计金额超过10万元阈值"}]
    elif amount >= 10000:
        alert_level = "黄色预警"
        factors = [{"factor": "涉案金额较大", "desc": "总计金额超过1万元阈值"}]
    else:
        alert_level = "蓝色预警"
        factors = [{"factor": "一般性质隐患", "desc": "金额在常规阈值之下"}]

    update_clue_alert(clue_id, alert_level, factors)

@app.post("/api/ingest")
async def api_ingest_clue(req: IngestClue, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user), request: Request = None):
    # 关键词捕捉过滤
    keywords = ["拖欠", "欠薪", "工资", "不发钱", "报酬", "血汗钱", "讨薪"]
    matched_keyword = next((k for k in keywords if k in req.content), None)
    if not matched_keyword:
        raise HTTPException(400, "非欠薪类线索，不进入本系统流转")
        
    final_content = req.content
    if req.images:
        for b64 in req.images:
            try:
                ocr_text = extract_contract(b64)
                final_content += f"\n【图片证据文字提取】: {ocr_text}"
            except Exception as e:
                logger.error(f"OCR提取失败: {e}")

    # 发送通知提醒检察官和上级领导
    create_notification("检察官", f"预警：系统通过 12345 拦截到新线索！触发关键词: '{matched_keyword}'，涉及企业: {req.enterprise_name or '未知'}")
    create_notification("部门负责人", f"主管审阅：有新传入的系统线索触及底线 ({req.enterprise_name or '未知'})。")

    # Log it
    ip = request.client.host if request and request.client else ""
    create_audit_log(current_user["username"], "录入流转线索", f"添加了针对企业 {req.enterprise_name} 的案件", ip)

    clue_id = create_clue(
        title=req.title, source=req.source, domain=req.domain, content=final_content,
        enterprise_name=req.enterprise_name, personnel_count=req.personnel_count, amount=req.amount
    )
    
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE clues SET claimant_privacy=? WHERE id=?", (req.claimant_privacy, clue_id))
        conn.commit()

    background_tasks.add_task(_do_alert_work, clue_id)
    return {"clue_id": clue_id, "message": "收到数据，正在规则引擎预警中"}

# ===================== API: Judger =====================

def _do_judger_work(clue_id: int):
    clue = get_clue(clue_id)
    if not clue: return
    legal_context = retrieve_legal_context(clue["content"])
    result = judge_clue(
        title=clue["title"], enterprise=clue["enterprise_name"], amount=clue["amount"],
        count=clue["personnel_count"], clue_content=clue["content"], legal_context=legal_context
    )
    update_clue_risk(
        clue_id=clue_id, risk_level=result.get("risk_level", "中风险"),
        risk_summary=result.get("risk_summary", ""), risk_detail=result,
        case_type=result.get("case_type", "行政监督线索")
    )

@app.post("/api/clues/{id}/judge")
async def api_judge_clue(id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    if current_user["role"] == "观察员":
        raise HTTPException(403, "权限不足：观察员无法触发核心研判")

    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
        
    ip = request.client.host if request and request.client else ""
    create_audit_log(current_user["username"], "触发智能研判", f"针对线索 ID: {id} 发起了定性定案评估", ip)

    async with analyze_semaphore:
        await asyncio.to_thread(_do_judger_work, id)
        
    return get_clue(id)

# ===================== API: Query =====================

@app.get("/api/clues/{id}")
async def api_get_clue(id: int, current_user: dict = Depends(get_current_user)):
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
    return clue

@app.get("/api/clues")
async def api_list_clues(status: Optional[str] = None, alert_level: Optional[str] = None, case_type: Optional[str] = None, limit: int = 50, current_user: dict = Depends(get_current_user)):
    return list_clues(status, alert_level, case_type, limit)

@app.get("/api/stats")
async def api_get_stats(current_user: dict = Depends(get_current_user)):
    return get_stats()

# ===================== API: Collaboration & Decision =====================

@app.post("/api/clues/{id}/push_task")
async def api_push_task(id: int, req: PushTaskRequest, current_user: dict = Depends(get_current_user), request: Request = None):
    if current_user["role"] not in ["检察官", "管理员"]:
        raise HTTPException(403, "权限不足：无权签发协同表单")
        
    if not verify_password(req.password, current_user["hashed_password"]):
        raise HTTPException(403, "身份验明失败，密码错误！")
        
    clue = get_clue(id)
    if not clue:
        raise HTTPException(404, "线索不存在")
        
    ip = request.client.host if request and request.client else ""
    create_audit_log(current_user["username"], "验明签发协同工单", f"操作人:{current_user['real_name']}, 验证通过并发送至 {req.to_dept} 部门", ip)

    task_id = create_push_record(id, req.to_dept, req.req_content)
    return {"message": "协同信函已发出，身份已验证留痕", "task_id": task_id}

@app.post("/api/clues/{id}/synergy_reply")
async def api_synergy_reply(id: int, req: FeedbackTaskRequest, current_user: dict = Depends(get_current_user), request: Request = None):
    if current_user["role"] == "观察员":
        raise HTTPException(403, "权限不足")
    
    clue = get_clue(id)
    if not clue or not clue.get('tasks'):
        raise HTTPException(404, "线索或工单不存在")
        
    # Find the latest open task
    task_id = clue['tasks'][-1]['id']

    ip = request.client.host if request and request.client else ""
    create_audit_log(current_user["username"], "回传监督反馈", f"为线索 {id} 的工单上传了回执", ip)
        
    feedback_push_record(task_id, req.feedback, req.evidence_urls)
    return {"message": "外部协同单位已反馈"}

@app.post("/api/clues/{id}/resolve")
async def api_resolve_clue(id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    if current_user["role"] == "观察员":
        raise HTTPException(403, "权限不足：观察员无法结案")

    ip = request.client.host if request and request.client else ""
    create_audit_log(current_user["username"], "完结线索", f"核准线索 ID: {id} 闭环", ip)
        
    mark_resolved(id)
    return {"message": "已结案打标"}

# ===================== API: Document & Notifications =====================

from fastapi import File, UploadFile
import tempfile
import pypdf
import docx2txt

@app.post("/api/upload_doc")
async def api_upload_doc(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp:
        content = await file.read()
        temp.write(content)
        temp.flush()
        temp_path = temp.name
        
    parsed_text = ""
    try:
        if ext == 'pdf':
            reader = pypdf.PdfReader(temp_path)
            for page in reader.pages:
                parsed_text += page.extract_text() + "\n"
        elif ext in ['docx', 'doc']:
            parsed_text = docx2txt.process(temp_path)
        else:
            parsed_text = content.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Failed to parse document: {e}")
        raise HTTPException(400, "文件解析失败，请确保格式正确。")
    finally:
        import os
        os.remove(temp_path)
        
    return {"parsed_text": parsed_text}

@app.get("/api/notifications/unread")
async def api_notifications(current_user: dict = Depends(get_current_user)):
    return get_unread_notifications(current_user["role"])

@app.post("/api/notifications/read")
async def api_mark_notifications_read(current_user: dict = Depends(get_current_user)):
    mark_notifications_read(current_user["role"])
    return {"message": "状态已更新为已读"}

# ===================== API: Other =====================

@app.post("/api/chat")
async def api_chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
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
