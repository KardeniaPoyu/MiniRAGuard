import asyncio
import hashlib
import logging
import os
import secrets
import sys
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

# Add the project root to sys.path so we can import miniraguard
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import framework components
from miniraguard.core.cache_tool import (
    consume_free_use,
    get_cache_by_md5,
    get_or_create_user,
    get_risk_stats,
    get_user_by_token,
    init_db,
    save_user_token,
    set_cache_by_md5,
    update_risk_stats,
    update_user_profile,
    restore_free_use,
    save_analyze_record,
    get_analyze_records,
    get_record_detail,
    delete_analyze_record,
)
from miniraguard.core.chat_tool import chat
from miniraguard.core.rag_tool import retrieve_legal_context
from miniraguard.core.reviewer import review_contract
from miniraguard.core.vision_tool import extract_contract

# Import demo-specific prompts and configuration
from .prompts import (
    VISION_SYSTEM_PROMPT,
    VISION_USER_PROMPT_TPL,
    REVIEW_SYSTEM_PROMPT,
    REVIEW_USER_PROMPT_TPL,
    RENTAL_KEYWORD_MAP
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store" # Adjusting to the example's data dir

# ──────────────────────────── Pydantic Models ────────────────────────────

class AnalyzeRequest(BaseModel):
    images: list[str]


class ChatRequest(BaseModel):
    question: str
    context: dict[str, Any]
    history: list[dict[str, Any]]


class LoginRequest(BaseModel):
    code: str


class ProfileUpdateRequest(BaseModel):
    nickname: str = ""
    school: str = ""
    grade: str = ""
    student_id: str = ""


# ──────────────────────────── Helpers ────────────────────────────

def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):].strip()
        return token if token else None
    return None


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


# ──────────────────────────── Lifespan ────────────────────────────

@asynccontextmanager
async def lifespan(app_ctx: FastAPI):  # type: ignore[no-untyped-def]
    init_db()

    required_keys = ["QWEN_API_KEY", "DEEPSEEK_API_KEY"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}. Please check your .env file.")

    logger.info("[startup] Pre-loading RAG index...")
    try:
        retrieve_legal_context("deposit rental repair", VECTOR_STORE_PATH, RENTAL_KEYWORD_MAP)
        logger.info("[startup] RAG index pre-loaded successfully.")
    except Exception as e:
        logger.warning(f"[startup] Failed to pre-load RAG index: {e}")

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


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request, exc: Exception):  # type: ignore[no-untyped-def]
    logger.error("UNHANDLED_EXCEPTION:", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error. Please try again later."})


# ──────────────────────────── /api/login ────────────────────────────

@app.post("/api/login")
async def login(req: LoginRequest):
    if req.code == "test_code":
        openid = "mock_test_user_openid"
        user = get_or_create_user(openid)
        token = secrets.token_hex(32)
        save_user_token(openid, token)
        logger.info("Mock login successful")
        return {
            "token": token,
            "user": {
                "openid": user["openid"],
                "nickname": user["nickname"] or "Test User",
                "school": user["school"] or "Test University",
                "grade": user["grade"] or "Junior",
                "student_id": user["student_id"],
                "is_vip": user["is_vip"],
                "free_uses_remaining": user["free_uses_remaining"],
            }
        }

    appid = os.getenv("WECHAT_APPID", "")
    secret = os.getenv("WECHAT_SECRET", "")

    wx_url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={appid}&secret={secret}&js_code={req.code}&grant_type=authorization_code"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(wx_url)
            wx_data = resp.json()
        except Exception:
            logger.error("WeChat API request failed", exc_info=True)
            return JSONResponse(status_code=400, content={"error": "Login failed"})

    if "errcode" in wx_data and wx_data["errcode"] != 0:
        logger.warning("WeChat jscode2session error: %s", wx_data)
        return JSONResponse(status_code=400, content={"error": "Login failed"})

    openid = wx_data.get("openid")
    if not openid:
        return JSONResponse(status_code=400, content={"error": "Login failed"})

    user = get_or_create_user(openid)
    token = secrets.token_hex(32)
    save_user_token(openid, token)

    return {
        "token": token,
        "user": {
            "openid": user["openid"],
            "nickname": user["nickname"],
            "school": user["school"],
            "grade": user["grade"],
            "student_id": user["student_id"],
            "is_vip": user["is_vip"],
            "free_uses_remaining": user["free_uses_remaining"],
        }
    }


# ──────────────────────────── /api/user ────────────────────────────

@app.get("/api/user/profile")
async def get_profile(request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Login expired"})
    return user


@app.post("/api/user/profile")
async def update_profile(req: ProfileUpdateRequest, request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Login expired"})

    update_user_profile(
        openid=user["openid"],
        nickname=req.nickname,
        school=req.school,
        grade=req.grade,
        student_id=req.student_id,
    )

    return get_user_by_token(token)


@app.post("/api/user/watch-ad")
async def watch_ad(request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Login expired"})

    result = restore_free_use(user["openid"], count=3)
    return {
        "free_uses_remaining": result["free_uses_remaining"],
        "message": "Credits restored successfully"
    }


@app.get("/api/user/records")
async def get_records(request: Request, limit: int = 20):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Login expired"})

    limit = min(max(limit, 1), 50)
    return get_analyze_records(user["openid"], limit)


@app.get("/api/user/records/{image_md5}")
async def get_record(image_md5: str, request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Login expired"})

    detail = get_record_detail(user["openid"], image_md5)
    if not detail:
        return JSONResponse(status_code=404, content={"error": "Record not found"})
    detail["cache_hit"] = True
    return detail


@app.delete("/api/user/records/{record_id}")
async def delete_record(record_id: int, request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Login expired"})

    if delete_analyze_record(user["openid"], record_id):
        return {"message": "Deleted"}
    return JSONResponse(status_code=404, content={"error": "Record not found"})


# ──────────────────────────── /api/analyze ────────────────────────────

def _do_analyze_work(req: AnalyzeRequest, image_md5: str) -> Any:
    pages: list[str] = []
    for img_b64 in req.images:
        pages.append(extract_contract(img_b64, VISION_SYSTEM_PROMPT, VISION_USER_PROMPT_TPL))

    contract_text = "\n\n".join(pages).strip()
    legal_context = retrieve_legal_context(contract_text, VECTOR_STORE_PATH, RENTAL_KEYWORD_MAP)
    result = review_contract(contract_text, legal_context, REVIEW_SYSTEM_PROMPT, REVIEW_USER_PROMPT_TPL)

    result["contract_text"] = contract_text
    update_risk_stats(result.get("analysis_results", []), image_md5)
    set_cache_by_md5(image_md5, result)
    return result


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest, request: Request) -> Any:
    image_md5 = hashlib.md5("".join(req.images).encode()).hexdigest()
    cached = get_cache_by_md5(image_md5)
    token = _extract_token(request)
    user = None
    if token:
        user = get_user_by_token(token)

    if cached is not None:
        cached["cache_hit"] = True
        if token and user:
            save_analyze_record(
                openid=user["openid"],
                image_md5=image_md5,
                overall_risk=cached.get("overall_risk", ""),
                summary=cached.get("summary", ""),
                clause_count=len(cached.get("analysis_results", []))
            )
        return cached

    if token and user:
        if not consume_free_use(user["openid"]):
            return JSONResponse(
                status_code=403,
                content={"error": "Usage limit reached. Please visit the profile page to restore credits."}
            )

    if analyze_semaphore.locked():
        return JSONResponse(
            status_code=429,
            content={"error": "Server busy. Please try again in 30s.", "retry_after": 30}
        )

    try:
        async with analyze_semaphore:
            result = await asyncio.wait_for(
                asyncio.to_thread(_do_analyze_work, req, image_md5),
                timeout=180.0
            )
            result["cache_hit"] = False
            if token and user:
                save_analyze_record(
                    openid=user["openid"],
                    image_md5=image_md5,
                    overall_risk=result.get("overall_risk", ""),
                    summary=result.get("summary", ""),
                    clause_count=len(result.get("analysis_results", []))
                )
            return result
    except asyncio.TimeoutError:
        return JSONResponse(status_code=408, content={"error": "Analysis timed out."})
    except ValueError as e:
        if str(e) == "INVALID_DOCUMENT":
            return JSONResponse(status_code=400, content={"error": "Invalid document images detected."})
        raise


# ──────────────────────────── Other endpoints ────────────────────────────

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
        "vector_store": os.path.exists(VECTOR_STORE_PATH),
        "qwen_key_set": bool(os.getenv("QWEN_API_KEY")),
        "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
        "wechat_configured": bool(os.getenv("WECHAT_APPID") and os.getenv("WECHAT_SECRET")),
        "max_concurrent": get_max_concurrent()
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
