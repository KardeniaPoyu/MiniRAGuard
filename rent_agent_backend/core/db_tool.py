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
                source TEXT,             -- 12345热线/外部单位/等
                domain TEXT,             -- 领域: 欠薪/环境/等
                content TEXT,
                enterprise_name TEXT DEFAULT '',    -- 涉黑企业/单位标识
                personnel_count INTEGER DEFAULT 1,  -- 涉及人数
                amount REAL DEFAULT 0.0,            -- 涉案金额
                
                alert_level TEXT DEFAULT '',        -- 预警等级：红/黄/蓝
                alert_factors TEXT DEFAULT '[]',    -- 触发的多维风险因素 (json array)
                
                risk_level TEXT,                    -- AI研判高/中/低
                risk_summary TEXT,                  -- AI摘要
                risk_detail TEXT,                   -- AI详尽研判(json)
                case_type TEXT DEFAULT '',          -- 线索定性: 行政监督/民事实体支持起诉/刑事移送/公益诉讼
                
                status TEXT DEFAULT '待溯源',        -- 状态: 待溯源/待研判/流转中/已结案
                assigned_to TEXT,                   -- 主办部门
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collaboration_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clue_id INTEGER,
                to_dept TEXT,
                req_content TEXT,
                feedback TEXT DEFAULT '',
                evidence_urls TEXT DEFAULT '[]', -- 证据交换记录
                status TEXT DEFAULT '待签收', -- 待签收/处理中/已反馈
                request_time TEXT,
                feedback_time TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stats_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT,
                total_clues INTEGER,
                red_alert INTEGER DEFAULT 0,
                yellow_alert INTEGER DEFAULT 0,
                blue_alert INTEGER DEFAULT 0,
                pushed INTEGER,
                resolved INTEGER
            )
        """)
        conn.commit()

init_db()

def create_clue(title: str, source: str, domain: str, content: str, enterprise_name: str = "", personnel_count: int = 1, amount: float = 0.0) -> int:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO clues (title, source, domain, content, enterprise_name, personnel_count, amount, created_at, updated_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '待预警')""",
            (title, source, domain, content, enterprise_name, personnel_count, amount, now, now)
        )
        conn.commit()
        return cur.lastrowid

def update_clue_alert(clue_id: int, alert_level: str, alert_factors: list) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE clues SET alert_level=?, alert_factors=?, status='待研判', updated_at=? WHERE id=?",
            (alert_level, json.dumps(alert_factors, ensure_ascii=False), now, clue_id)
        )
        conn.commit()

def update_clue_risk(clue_id: int, risk_level: str, risk_summary: str, risk_detail: dict, case_type: str) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """UPDATE clues 
               SET risk_level=?, risk_summary=?, risk_detail=?, case_type=?, status='流转中', updated_at=?
               WHERE id=?""",
            (risk_level, risk_summary, json.dumps(risk_detail, ensure_ascii=False), case_type, now, clue_id)
        )
        conn.commit()

def create_collaboration_task(clue_id: int, to_dept: str, req_content: str) -> int:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO collaboration_tasks (clue_id, to_dept, req_content, request_time) VALUES (?, ?, ?, ?)",
            (clue_id, to_dept, req_content, now)
        )
        # Update clue assignment marking
        conn.execute("UPDATE clues SET assigned_to=? WHERE id=?", (to_dept, clue_id))
        conn.commit()
        return cur.lastrowid

def feedback_collaboration_task(task_id: int, feedback: str, evidence_urls: list = None) -> None:
    now = _now_iso()
    evidence_str = json.dumps(evidence_urls or [], ensure_ascii=False)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE collaboration_tasks SET feedback=?, evidence_urls=?, feedback_time=?, status='已反馈' WHERE id=?",
            (feedback, evidence_str, now, task_id)
        )
        conn.commit()

def mark_resolved(clue_id: int) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE clues SET status='已结案', updated_at=? WHERE id=?", (now, clue_id))
        conn.commit()

def get_clue(clue_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM clues WHERE id=?", (clue_id,)).fetchone()
        if not row:
            return None
        res = dict(row)
        for field in ['risk_detail', 'alert_factors']:
            if res.get(field):
                try:
                    res[field] = json.loads(res[field])
                except Exception:
                    pass
        
        # Get tasks
        tasks = conn.execute("SELECT * FROM collaboration_tasks WHERE clue_id=?", (clue_id,)).fetchall()
        res['tasks'] = [dict(t) for t in tasks]
        for task in res['tasks']:
            if task.get('evidence_urls'):
                try:
                    task['evidence_urls'] = json.loads(task['evidence_urls'])
                except:
                    pass
        return res

def list_clues(status: str = None, alert_level: str = None, case_type: str = None, limit: int = 50) -> list:
    query = "SELECT * FROM clues WHERE 1=1"
    params = []
    if status is not None:
        query += " AND status=?"
        params.append(status)
    if alert_level is not None:
        query += " AND alert_level=?"
        params.append(alert_level)
    if case_type is not None:
        query += " AND case_type=?"
        params.append(case_type)
        
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for field in ['risk_detail', 'alert_factors']:
                if d.get(field):
                    try:
                        d[field] = json.loads(d[field])
                    except Exception:
                        pass
            result.append(d)
        return result

def get_stats() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) as c FROM clues").fetchone()["c"]
        
        status_rows = conn.execute("SELECT status, COUNT(*) as c FROM clues GROUP BY status").fetchall()
        status_dist = {r["status"]: r["c"] for r in status_rows}
        
        # Dashboard wants enterprise hot spots (e.g., enterprise with >1 complaint)
        hot_enterprises = conn.execute("SELECT enterprise_name, COUNT(*) as c, SUM(personnel_count) as pc FROM clues WHERE enterprise_name!='' GROUP BY enterprise_name ORDER BY c DESC LIMIT 5").fetchall()
        
        alert_rows = conn.execute("SELECT alert_level, COUNT(*) as c FROM clues WHERE alert_level!='' GROUP BY alert_level").fetchall()
        alert_dist = {r["alert_level"]: r["c"] for r in alert_rows}

    return {
        "total": total,
        "status_distribution": status_dist,
        "alert_distribution": alert_dist,
        "hot_enterprises": [{"name": r["enterprise_name"], "count": r["c"], "personnel": r["pc"]} for r in hot_enterprises]
    }

# Mock data ingest for cold start
def seed_mock_data():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.execute("SELECT COUNT(*) as c FROM clues").fetchone()[0]
        if c > 0:
            return # already seeded
    
    # 模拟数据填充
    data = [
        ("张三等15人诉通州四建欠薪案", "12345热线", "劳动违法", "我们在通州四建负责泥瓦工，已经半年没发工资了，总共拖欠大概20万，老板跑路联系不上，我们准备集体去区政府拉横幅。", "通州四建包工队", 15, 200000),
        ("网民爆料xx火锅店克扣员工社保", "网络舆情", "劳动违法", "在xx火锅店打工3个多月都没有交社保，辞职的时候还被扣了最后半个月工资作为违约金，太坑了，大家避雷！", "XX火锅餐饮", 1, 3500),
        ("李四单人讨要年底奖金", "人社局移交", "劳动违法", "公司承诺的年终奖3000块不给发，说是在绩效未达标，但并没有明示标准。", "某科技发展公司", 1, 3000),
        ("某工程项目拖欠农民工进度款", "住建局移交", "劳动违法", "该项目未开设农民工工资专用账户，且资金监管未到位，目前总包拖欠底部分包人工费超50万元。", "通州某基建总承包", 45, 500000),
        ("重复投诉：通州四建包工队另外5人", "12345热线", "劳动违法", "连我们木工的钱也没结，通州四建老板彻底失联了，总计约8万块钱不知去哪讨要。", "通州四建包工队", 5, 80000)
    ]
    for d in data:
        create_clue(*d)
