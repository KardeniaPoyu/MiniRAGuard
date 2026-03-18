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

