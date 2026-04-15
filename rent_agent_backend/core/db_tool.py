import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "risk_platform.db")

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source TEXT,
                domain TEXT,
                content TEXT,
                file_md5 TEXT,
                risk_level TEXT,
                risk_summary TEXT,
                risk_detail TEXT,
                status TEXT DEFAULT '待研判',
                assigned_to TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS push_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clue_id INTEGER,
                department TEXT,
                push_time TEXT,
                feedback TEXT DEFAULT '',
                resolved INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT,
                total_clues INTEGER,
                high_risk INTEGER,
                mid_risk INTEGER,
                low_risk INTEGER,
                pushed INTEGER,
                resolved INTEGER
            )
        """)
        conn.commit()

init_db()

def create_clue(title: str, source: str, domain: str, content: str, file_md5: str = None) -> int:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO clues (title, source, domain, content, file_md5, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, source, domain, content, file_md5, now, now)
        )
        conn.commit()
        return cur.lastrowid

def get_clue(clue_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM clues WHERE id=?", (clue_id,)).fetchone()
        if not row:
            return None
        res = dict(row)
        if res.get("risk_detail"):
            try:
                res["risk_detail"] = json.loads(res["risk_detail"])
            except Exception:
                pass
        return res

def list_clues(status: str = None, domain: str = None, risk_level: str = None, limit: int = 50) -> list:
    query = "SELECT * FROM clues WHERE 1=1"
    params = []
    if status is not None:
        query += " AND status=?"
        params.append(status)
    if domain is not None:
        query += " AND domain=?"
        params.append(domain)
    if risk_level is not None:
        query += " AND risk_level=?"
        params.append(risk_level)
    
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("risk_detail"):
                try:
                    d["risk_detail"] = json.loads(d["risk_detail"])
                except Exception:
                    pass
            result.append(d)
        return result

def update_clue_risk(clue_id: int, risk_level: str, risk_summary: str, risk_detail: dict) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """UPDATE clues 
               SET risk_level=?, risk_summary=?, risk_detail=?, status='已研判', updated_at=?
               WHERE id=?""",
            (risk_level, risk_summary, json.dumps(risk_detail, ensure_ascii=False), now, clue_id)
        )
        conn.commit()

def push_clue(clue_id: int, department: str) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE clues SET status='已推送', assigned_to=?, updated_at=? WHERE id=?",
            (department, now, clue_id)
        )
        conn.execute(
            "INSERT INTO push_records (clue_id, department, push_time) VALUES (?, ?, ?)",
            (clue_id, department, now)
        )
        conn.commit()

def mark_resolved(clue_id: int, feedback: str) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE clues SET status='已办结', updated_at=? WHERE id=?",
            (now, clue_id)
        )
        conn.execute(
            "UPDATE push_records SET feedback=?, resolved=1 WHERE clue_id=? AND resolved=0",
            (feedback, clue_id)
        )
        conn.commit()

def get_stats() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c FROM clues").fetchone()["c"]
        
        status_rows = conn.execute("SELECT status, COUNT(*) as c FROM clues GROUP BY status").fetchall()
        status_dist = {r["status"]: r["c"] for r in status_rows}
        
        level_rows = conn.execute("SELECT risk_level, COUNT(*) as c FROM clues WHERE risk_level IS NOT NULL GROUP BY risk_level").fetchall()
        level_dist = {r["risk_level"]: r["c"] for r in level_rows}
        
        domain_rows = conn.execute("SELECT domain, COUNT(*) as c FROM clues GROUP BY domain").fetchall()
        domain_dist = {r["domain"]: r["c"] for r in domain_rows}

    return {
        "total": total,
        "status_distribution": status_dist,
        "risk_distribution": level_dist,
        "domain_distribution": domain_dist
    }

def save_snapshot() -> None:
    from datetime import date
    today = date.today().isoformat()
    stats = get_stats()
    
    total = stats["total"]
    levels = stats["risk_distribution"]
    status_dist = stats["status_distribution"]
    
    high = levels.get("高风险", 0)
    mid = levels.get("中风险", 0)
    low = levels.get("低风险", 0)
    pushed = status_dist.get("已推送", 0)
    resolved = status_dist.get("已办结", 0)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """INSERT INTO stats_snapshot 
               (snapshot_date, total_clues, high_risk, mid_risk, low_risk, pushed, resolved)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (today, total, high, mid, low, pushed, resolved)
        )
        conn.commit()
