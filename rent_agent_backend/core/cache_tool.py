from __future__ import annotations

import hashlib, json, sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "cache.db")


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


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


def update_risk_stats(analysis_results: list, image_md5: str) -> None:
    from datetime import date
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        for item in analysis_results:
            risk_type = (item.get("risk_type") or "").strip()
            if not risk_type:
                continue
            
            # 去重：检查是否已记录
            exists = conn.execute(
                "SELECT 1 FROM risk_stats_log WHERE image_md5=? AND risk_type=?",
                (image_md5, risk_type)
            ).fetchone()
            if exists:
                continue

            # 写入日志
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
