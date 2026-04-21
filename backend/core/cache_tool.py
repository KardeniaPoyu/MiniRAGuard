from __future__ import annotations

import hashlib, json, secrets, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "cache.db")


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS cache (md5 TEXT PRIMARY KEY, result TEXT)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_stats (
                risk_type TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_seen TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_stats_log (
                image_md5 TEXT,
                risk_type TEXT,
                PRIMARY KEY (image_md5, risk_type)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                openid TEXT PRIMARY KEY,
                nickname TEXT DEFAULT '',
                school TEXT DEFAULT '',
                grade TEXT DEFAULT '',
                student_id TEXT DEFAULT '',
                is_vip INTEGER DEFAULT 0,
                free_uses_remaining INTEGER DEFAULT 3,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_tokens (
                token TEXT PRIMARY KEY,
                openid TEXT NOT NULL,
                created_at TEXT,
                expires_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyze_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                openid TEXT NOT NULL,
                image_md5 TEXT NOT NULL,
                overall_risk TEXT NOT NULL,
                summary TEXT NOT NULL,
                clause_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_records_openid 
            ON analyze_records(openid, created_at DESC)
        """)
        conn.commit()


# ──────────────────────────── cache ────────────────────────────


def get_cache(text: str) -> dict | None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT result FROM cache WHERE md5=?", (_md5(text),)).fetchone()
    return json.loads(row[0]) if row else None


def set_cache(text: str, result: dict) -> None:
    init_db()
    payload = json.dumps(result, ensure_ascii=False)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO cache (md5, result) VALUES (?, ?)", (_md5(text), payload))
        conn.commit()


def get_cache_by_md5(md5: str) -> dict | None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT result FROM cache WHERE md5=?", (md5,)).fetchone()
    return json.loads(row[0]) if row else None


def set_cache_by_md5(md5: str, result: dict) -> None:
    init_db()
    payload = json.dumps(result, ensure_ascii=False)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO cache (md5, result) VALUES (?, ?)", (md5, payload))
        conn.commit()


# ──────────────────────────── risk stats ────────────────────────────


def update_risk_stats(analysis_results: list, image_md5: str) -> None:
    from datetime import date
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        for item in analysis_results:
            risk_type = (item.get("risk_type") or "").strip()
            if not risk_type:
                continue

            exists = conn.execute(
                "SELECT 1 FROM risk_stats_log WHERE image_md5=? AND risk_type=?",
                (image_md5, risk_type)
            ).fetchone()
            if exists:
                continue

            conn.execute(
                "INSERT OR IGNORE INTO risk_stats_log (image_md5, risk_type) VALUES (?, ?)",
                (image_md5, risk_type)
            )

            conn.execute("""
                INSERT INTO risk_stats (risk_type, count, last_seen)
                VALUES (?, 1, ?)
                ON CONFLICT(risk_type) DO UPDATE SET
                    count = count + 1,
                    last_seen = excluded.last_seen
            """, (risk_type, today))
        conn.commit()


def get_risk_stats() -> list:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT risk_type, count, last_seen FROM risk_stats ORDER BY count DESC"
        ).fetchall()
    return [{"risk_type": r[0], "count": r[1], "last_seen": r[2]} for r in rows]


# ──────────────────────────── users ────────────────────────────


def _row_to_user(row: tuple) -> dict:
    return {
        "openid": row[0],
        "nickname": row[1],
        "school": row[2],
        "grade": row[3],
        "student_id": row[4],
        "is_vip": row[5],
        "free_uses_remaining": row[6],
        "created_at": row[7],
    }


def get_or_create_user(openid: str) -> dict:
    """openid 不存在则创建新用户，存在则返回已有用户信息。"""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT openid, nickname, school, grade, student_id, is_vip, free_uses_remaining, created_at "
            "FROM users WHERE openid=?",
            (openid,)
        ).fetchone()
        if row:
            return _row_to_user(row)
        now = _now_iso()
        conn.execute(
            "INSERT INTO users (openid, nickname, school, grade, student_id, is_vip, free_uses_remaining, created_at) "
            "VALUES (?, '', '', '', '', 0, 3, ?)",
            (openid, now)
        )
        conn.commit()
        return {
            "openid": openid,
            "nickname": "",
            "school": "",
            "grade": "",
            "student_id": "",
            "is_vip": 0,
            "free_uses_remaining": 3,
            "created_at": now,
        }


def get_user_by_token(token: str) -> dict | None:
    """通过 token 查找用户，token 不存在或已过期返回 None。"""
    init_db()
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT openid FROM user_tokens WHERE token=? AND expires_at > ?",
            (token, now)
        ).fetchone()
        if not row:
            return None
        openid = row[0]
        user_row = conn.execute(
            "SELECT openid, nickname, school, grade, student_id, is_vip, free_uses_remaining, created_at "
            "FROM users WHERE openid=?",
            (openid,)
        ).fetchone()
    return _row_to_user(user_row) if user_row else None


def save_user_token(openid: str, token: str) -> None:
    """保存 token，有效期 30 天。"""
    init_db()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=30)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_tokens (token, openid, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, openid, now.isoformat(), expires.isoformat())
        )
        conn.commit()


def update_user_profile(
    openid: str, nickname: str, school: str, grade: str, student_id: str
) -> None:
    """更新用户资料。"""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE users SET nickname=?, school=?, grade=?, student_id=? WHERE openid=?",
            (nickname, school, grade, student_id, openid)
        )
        conn.commit()


def consume_free_use(openid: str) -> bool:
    """
    消耗一次免费次数。
    返回 True：还有余量，消耗成功。
    返回 False：次数已用完。
    不再区分 VIP。
    """
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT free_uses_remaining FROM users WHERE openid=?",
            (openid,)
        ).fetchone()
        if not row or row[0] <= 0:
            return False
        conn.execute(
            "UPDATE users SET free_uses_remaining = free_uses_remaining - 1 WHERE openid=?",
            (openid,)
        )
        conn.commit()
        return True


def restore_free_use(openid: str, count: int = 3) -> dict:
    """看广告后恢复次数，每次看广告恢复 count 次，上限 10 次。"""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE users SET free_uses_remaining = MIN(free_uses_remaining + ?, 10)
            WHERE openid=?
        """, (count, openid))
        conn.commit()
        row = conn.execute(
            "SELECT free_uses_remaining FROM users WHERE openid=?",
            (openid,)
        ).fetchone()
    return {"free_uses_remaining": row[0] if row else 0}


# ──────────────────────────── analyze_records ────────────────────────────

def save_analyze_record(
    openid: str,
    image_md5: str,
    overall_risk: str,
    summary: str,
    clause_count: int
) -> None:
    """保存一条审查记录，同一用户同一图片不重复记录。"""
    init_db()
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        exists = conn.execute(
            "SELECT 1 FROM analyze_records WHERE openid=? AND image_md5=?",
            (openid, image_md5)
        ).fetchone()
        if exists:
            return
        conn.execute(
            """INSERT INTO analyze_records
               (openid, image_md5, overall_risk, summary, clause_count, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (openid, image_md5, overall_risk, summary, clause_count, now)
        )
        conn.commit()


def get_analyze_records(openid: str, limit: int = 20) -> list:
    """获取用户的审查记录列表，最多返回 limit 条，按时间倒序。"""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """SELECT id, image_md5, overall_risk, summary, clause_count, created_at
               FROM analyze_records
               WHERE openid=?
               ORDER BY created_at DESC
               LIMIT ?""",
            (openid, limit)
        ).fetchall()
    return [
        {
            "id": r[0],
            "image_md5": r[1],
            "overall_risk": r[2],
            "summary": r[3],
            "clause_count": r[4],
            "created_at": r[5]
        }
        for r in rows
    ]


def get_record_detail(openid: str, image_md5: str) -> dict | None:
    """
    获取某条记录的完整审查结果。
    先验证该记录属于该用户，再从 cache 表取完整 JSON。
    """
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        record = conn.execute(
            "SELECT 1 FROM analyze_records WHERE openid=? AND image_md5=?",
            (openid, image_md5)
        ).fetchone()
        if not record:
            return None
        row = conn.execute(
            "SELECT result FROM cache WHERE md5=?",
            (image_md5,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def delete_analyze_record(openid: str, record_id: int) -> bool:
    """删除一条审查记录（只删索引，不删缓存）。"""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM analyze_records WHERE id=? AND openid=?",
            (record_id, openid)
        )
        conn.commit()
    return cur.rowcount > 0
