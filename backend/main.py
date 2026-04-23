import asyncio
import logging
import os
import json
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Request

logger = logging.getLogger(__name__)

# ── 系统启动状态追踪 ──────────────────────────────────────────────────────
class StartupStatus:
    stage = "booting"  # booting, seeding, loading_rag, ready
    message = "系统核心正在启动..."

    @classmethod
    def update(cls, stage: str, message: str):
        cls.stage = stage
        cls.message = message
        logger.info(f"[status] {stage}: {message}")

startup_status = StartupStatus()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    get_sys_configs,
    update_sys_configs,
    update_password as db_update_password,
    DB_PATH
)
from core.chat_tool import chat
from core.rag_tool import retrieve_legal_context
from core.judger import judge_clue
from core.alerter import trigger_alert
from core.vision_tool import extract_contract
from core.auth_tool import verify_password, create_access_token, decode_access_token, get_password_hash
from core.reviewer import review_contract

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
    is_prod = os.getenv("PRODUCTION", "false").lower() == "true"
    StartupStatus.update("seeding", "正在初始化系统数据环境...")
    if is_prod:
        logger.info("[startup] 生产模式启动，跳过内置数据植入")
    else:
        seed_mock_data()  
        seed_users()  # 植入测试用户
    
    if not os.getenv("DEEPSEEK_API_KEY"):
        logger.warning("[startup] 未检测到 DEEPSEEK_API_KEY，AI 研判功能将不可用")

    async def warmup_rag():
        from core.rag_tool import is_rag_available
        if not is_rag_available():
            logger.info("[startup] RAG 系统已禁用或不可用，切换到纯 API 轻量模式")
            StartupStatus.update("ready", "系统已就绪（轻量模式）")
            return

        StartupStatus.update("loading_rag", "正在初始化法律库语义检索系统 (BGE Local)...")
        logger.info("[startup] 开始预加载 RAG 索引 (后台)...")
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            # 在子线程运行耗时检索任务
            await loop.run_in_executor(None, retrieve_legal_context, "合同违约")
            StartupStatus.update("ready", "系统已就绪，正在准备主界面")
            logger.info("[startup] RAG 索引预加载完成")
        except Exception as e:
            StartupStatus.update("ready", "系统已就绪（轻量模式 - 检索引擎加载失败）")
            logger.warning(f"RAG预加载由于数据库版本或连接问题未完成: {e}")

    # 异步启动热身任务，不阻塞 yield
    import asyncio
    asyncio.create_task(warmup_rag())
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 生产模式：托管前端静态资源 ──────────────────────────────────────────
# 安装后路径结构: {app}/backend/ 和 {app}/frontend/
# 修改为直接指向管理后台的编译目录
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "admin_frontend", "dist")
if os.path.isdir(_frontend_dir):
    _assets_dir = os.path.join(_frontend_dir, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")
    
    @app.get("/", include_in_schema=False)
    @app.get("/login", include_in_schema=False)
    @app.get("/dashboard", include_in_schema=False)
    async def serve_spa():
        return FileResponse(os.path.join(_frontend_dir, "index.html"))



# ── 系统状态接口 ───────────────────────────────────────────────────────
@app.get("/api/system/status")
async def get_system_status():
    """供加载页查询真实启动进度"""
    return {
        "stage": StartupStatus.stage,
        "message": StartupStatus.message,
        "ready": StartupStatus.stage == "ready"
    }


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

class ApiKeyUpdate(BaseModel):
    key: str

@app.post("/api/system/update_api_key")
async def update_api_key(update: ApiKeyUpdate, user: dict = Depends(get_current_user)):
    if user["role"] != "管理员":
        raise HTTPException(status_code=403, detail="只有管理员可以更新 API 密钥")
    
    key = update.key.strip()
    if not key.startswith("sk-") or len(key) < 20:
        raise HTTPException(status_code=400, detail="无效的 API 密钥格式")
    
    # Update in-memory for current session
    os.environ["DEEPSEEK_API_KEY"] = key
    
    # Persist to ~/.shulv_config.json for future launches
    config_path = os.path.join(os.path.expanduser("~"), ".shulv_config.json")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"api_key": key}, f)
        return {"status": "success", "message": "API 密钥已更新且已持久化"}
    except Exception as e:
        logger.error(f"Failed to persist API key: {e}")
        return {"status": "success", "message": "API 密钥已在当前会话生效，但保存到文件失败"}

@app.get("/api/system/config_info")
async def get_config_info(user: dict = Depends(get_current_user)):
    """获取脱敏后的配置信息"""
    key = os.getenv("DEEPSEEK_API_KEY", "")
    masked_key = f"{key[:6]}***{key[-4:]}" if len(key) > 10 else "***"
    return {
        "has_key": bool(key),
        "masked_key": masked_key
    }


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

class AnalyzeRequest(BaseModel):
    title: str
    content: str
    enterprise_name: Optional[str] = ""
    personnel_count: Optional[int] = 1
    amount: Optional[float] = 0.0
    images: Optional[list[str]] = []

class SettingsUpdateRequest(BaseModel):
    configs: dict[str, Any]

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


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
    return {
        "username": current_user["username"], 
        "role": current_user["role"],
        "real_name": current_user.get("real_name", current_user["username"])
    }

@app.post("/api/auth/change_password")
async def change_password(req: PasswordChangeRequest, current_user: dict = Depends(get_current_user)):
    if not verify_password(req.old_password, current_user["hashed_password"]):
        raise HTTPException(400, "原密码不正确")
    
    new_hashed = get_password_hash(req.new_password)
    db_update_password(current_user["username"], new_hashed)
    return {"message": "密码修改成功"}


# ===================== API: Logs =====================

@app.get("/api/logs")
async def api_get_logs(current_user: dict = Depends(get_current_user)):
    # Everyone can see logs for MVP demonstration
    return get_audit_logs()

# ===================== API: Ingest & Alert =====================

def _do_alert_work(clue_id: int):
    clue = get_clue(clue_id)
    if not clue: return
    
    configs = get_sys_configs()
    red_thresh = float(configs.get("red_alert_threshold", 100000))
    yellow_thresh = float(configs.get("yellow_alert_threshold", 10000))

    amount = clue.get("amount", 0.0)
    if amount >= red_thresh:
        alert_level = "红色预警"
        factors = [{"factor": "涉案金额巨大", "desc": f"总计金额超过配置阈值({red_thresh}元)"}]
    elif amount >= yellow_thresh:
        alert_level = "黄色预警"
        factors = [{"factor": "涉案金额较大", "desc": f"总计金额超过配置阈值({yellow_thresh}元)"}]
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
                import asyncio
                ocr_text = await asyncio.to_thread(extract_contract, b64)
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

@app.get("/api/settings")
async def api_get_settings(current_user: dict = Depends(get_current_user)):
    return get_sys_configs()

@app.post("/api/settings")
async def api_update_settings(req: SettingsUpdateRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "管理员":
        raise HTTPException(403, "仅管理员可修改系统配置")
    update_sys_configs(req.configs)
    return {"message": "配置已更新"}

@app.post("/api/analyze")
async def api_analyze_clue_public(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """公开接口：市民线索提交 + AI 研判入库一体化，不强制登录"""
    # 1. 整合全案文本 (表单内容 + 图片 OCR)
    final_content = req.content
    if req.images:
        for b64 in req.images:
            try:
                ocr_text = await asyncio.to_thread(extract_contract, b64)
                final_content += f"\n【图片证据文字提取】: {ocr_text}"
            except Exception as e:
                logger.error(f"OCR 提取失败: {e}")
                continue

    # 2. 预研判检索法律依据
    legal_context = await asyncio.to_thread(retrieve_legal_context, final_content)
    
    # 3. 调用 AI 核心研判
    result = await asyncio.to_thread(
        judge_clue,
        title=req.title,
        enterprise=req.enterprise_name,
        amount=req.amount,
        count=req.personnel_count,
        clue_content=final_content,
        legal_context=legal_context
    )

    # 4. 异步持久化入库 (来源固定为群众投诉)
    clue_id = create_clue(
        title=req.title,
        source="群众投诉",
        domain="劳动违法",
        content=final_content,
        enterprise_name=req.enterprise_name,
        personnel_count=req.personnel_count,
        amount=req.amount
    )
    
    # 手动触发金额分流量表预警
    background_tasks.add_task(_do_alert_work, clue_id)
    
    # 回填 AI 研判结果到数据库以供检察官查看
    update_clue_risk(
        clue_id=clue_id,
        risk_level=result.get("risk_level", "中风险"),
        risk_summary=result.get("risk_summary", ""),
        risk_detail=result,
        case_type=result.get("case_type", "行政监督线索")
    )

    # 5. 为了适配前端 LeadSubmission.vue 的特定 UI，进行格式转换
    # 映射 risk_factors 到 LeadSubmission.vue 的 analysis_results
    ui_analysis_results = []
    for factor in result.get("risk_factors", []):
        ui_analysis_results.append({
            "risk_type": factor.get("factor", "违法特征识别"),
            "risk_level": "高风险" if factor.get("severity") == "高" else ("中风险" if factor.get("severity") == "中" else "低风险"),
            "reason": factor.get("description", ""),
            "legal_basis": factor.get("legal_basis", ""),
            "advice": result.get("recommended_action", "建议向当地检察院或人社局咨询。")
        })

    return {
        "clue_id": clue_id,
        "overall_risk": result.get("risk_level", "自动研判中"),
        "summary": result.get("risk_summary", ""),
        "analysis_results": ui_analysis_results,
        "recommended_action": result.get("recommended_action", "")
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "max_concurrent": get_max_concurrent()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
