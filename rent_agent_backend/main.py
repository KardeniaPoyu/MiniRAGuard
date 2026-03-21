import asyncio
import hashlib
import logging
import os
import secrets
import traceback
from contextlib import asynccontextmanager
from typing import Any, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.cache_tool import (
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
)
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
        raise RuntimeError(f"缺少必要环境变量：{missing}，请检查 .env 文件")

    logger.info("[startup] 预加载 RAG 索引...")
    from core.rag_tool import retrieve_legal_context
    retrieve_legal_context("押金 提前退租 维修")
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


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request, exc: Exception):  # type: ignore[no-untyped-def]
    logger.error("UNHANDLED_EXCEPTION:", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "服务内部错误，请稍后重试"})


# ──────────────────────────── /api/login ────────────────────────────

@app.post("/api/login")
async def login(req: LoginRequest):
    # 🌟 新增：开发测试/答辩演示 专用免授权 Mock 通道
    if req.code == "test_code":
        openid = "mock_test_user_openid"
        user = get_or_create_user(openid)
        token = secrets.token_hex(32)
        save_user_token(openid, token)
        logger.info("使用 Mock 账号免授权登录成功")
        return {
            "token": token,
            "user": {
                "openid": user["openid"],
                "nickname": user["nickname"] or "测试用户",
                "school": user["school"] or "测试大学",
                "grade": user["grade"] or "大三",
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
            logger.error("微信接口请求失败", exc_info=True)
            return JSONResponse(status_code=400, content={"error": "登录失败"})

    if "errcode" in wx_data and wx_data["errcode"] != 0:
        logger.warning("微信 jscode2session 返回错误: %s", wx_data)
        return JSONResponse(status_code=400, content={"error": "登录失败"})

    openid = wx_data.get("openid")
    if not openid:
        return JSONResponse(status_code=400, content={"error": "登录失败"})

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


# ──────────────────────────── /api/user/profile ────────────────────────────

@app.get("/api/user/profile")
async def get_profile(request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "未登录"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "登录已过期，请重新登录"})
    return {
        "openid": user["openid"],
        "nickname": user["nickname"],
        "school": user["school"],
        "grade": user["grade"],
        "student_id": user["student_id"],
        "is_vip": user["is_vip"],
        "free_uses_remaining": user["free_uses_remaining"],
    }


@app.post("/api/user/profile")
async def update_profile(req: ProfileUpdateRequest, request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "未登录"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "登录已过期，请重新登录"})

    update_user_profile(
        openid=user["openid"],
        nickname=req.nickname,
        school=req.school,
        grade=req.grade,
        student_id=req.student_id,
    )

    updated = get_user_by_token(token)
    return {
        "openid": updated["openid"],
        "nickname": updated["nickname"],
        "school": updated["school"],
        "grade": updated["grade"],
        "student_id": updated["student_id"],
        "is_vip": updated["is_vip"],
        "free_uses_remaining": updated["free_uses_remaining"],
    }


@app.post("/api/user/watch-ad")
async def watch_ad(request: Request):
    token = _extract_token(request)
    if not token:
        return JSONResponse(status_code=401, content={"error": "未登录"})
    user = get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "登录已过期，请重新登录"})

    result = restore_free_use(user["openid"], count=3)
    return {
        "free_uses_remaining": result["free_uses_remaining"],
        "message": "已恢复3次审查机会"
    }


# ──────────────────────────── /api/analyze ────────────────────────────

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
async def analyze(req: AnalyzeRequest, request: Request) -> Any:
    # 第一步：先查缓存（缓存命中不消耗次数）
    image_md5 = hashlib.md5("".join(req.images).encode()).hexdigest()
    cached = get_cache_by_md5(image_md5)
    if cached is not None:
        cached["cache_hit"] = True
        return cached

    # 第二步：缓存未命中，才检查并消耗次数
    token = _extract_token(request)
    if token:
        user = get_user_by_token(token)
        if user:
            allowed = consume_free_use(user["openid"])
            if not allowed:
                return JSONResponse(
                    status_code=403,
                    content={"error": "免费次数已用完，请订阅会员"}
                )

    # 第三步：并发限制检查
    if analyze_semaphore.locked():
        return JSONResponse(
            status_code=429,
            content={
                "error": "当前分析任务较多，请等待约30秒后重试",
                "retry_after": 30
            }
        )

    # 第四步：执行分析
    try:
        async with analyze_semaphore:
            result = await asyncio.wait_for(
                asyncio.to_thread(_do_analyze_work, req, image_md5),
                timeout=180.0
            )
            result["cache_hit"] = False
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
        "vector_store": os.path.exists("./vector_store"),
        "cache_db": os.path.exists("./cache.db"),
        "qwen_key_set": bool(os.getenv("QWEN_API_KEY")),
        "deepseek_key_set": bool(os.getenv("DEEPSEEK_API_KEY")),
        "wechat_configured": bool(os.getenv("WECHAT_APPID") and os.getenv("WECHAT_SECRET")),
        "max_concurrent": get_max_concurrent()
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
