import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = str(DATA_DIR / "risk_platform.db")

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
                claimant_privacy TEXT DEFAULT '公开', -- 保密/公开
                prosecution_decision TEXT DEFAULT '待定', -- 待定/拟起诉/不起诉
                
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
            CREATE TABLE IF NOT EXISTS push_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clue_id INTEGER,
                to_dept TEXT,
                req_content TEXT,
                feedback_content TEXT DEFAULT '',
                feedback_images TEXT DEFAULT '[]', -- 证据交换记录
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                hashed_password TEXT,
                role TEXT,
                real_name TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sys_configs (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        # Initialize default configs if not present
        defaults = [
            ("system_name", "数律智检", _now_iso()),
            ("dept_name", "XX人民检察院", _now_iso()),
            ("red_alert_threshold", "100000", _now_iso()),
            ("yellow_alert_threshold", "10000", _now_iso()),
            ("ai_model", "deepseek-chat", _now_iso())
        ]
        conn.executemany("INSERT OR IGNORE INTO sys_configs (key, value, updated_at) VALUES (?, ?, ?)", defaults)
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

def create_push_record(clue_id: int, to_dept: str, req_content: str) -> int:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO push_records (clue_id, to_dept, req_content, request_time) VALUES (?, ?, ?, ?)",
            (clue_id, to_dept, req_content, now)
        )
        # Update clue assignment marking
        conn.execute("UPDATE clues SET assigned_to=? WHERE id=?", (to_dept, clue_id))
        conn.commit()
        return cur.lastrowid

def feedback_push_record(task_id: int, feedback_content: str, feedback_images: list = None) -> None:
    now = _now_iso()
    images_str = json.dumps(feedback_images or [], ensure_ascii=False)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE push_records SET feedback_content=?, feedback_images=?, feedback_time=?, status='已反馈' WHERE id=?",
            (feedback_content, images_str, now, task_id)
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
        tasks = conn.execute("SELECT * FROM push_records WHERE clue_id=?", (clue_id,)).fetchall()
        res['tasks'] = [dict(t) for t in tasks]
        for task in res['tasks']:
            if task.get('feedback_images'):
                try:
                    task['feedback_images'] = json.loads(task['feedback_images'])
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
        total = conn.execute("SELECT COUNT(*) as c FROM clues WHERE status IN ('已结案', '已反馈')").fetchone()["c"]
        
        status_rows = conn.execute("SELECT status, COUNT(*) as c FROM clues WHERE status IN ('已结案', '已反馈') GROUP BY status").fetchall()
        status_dist = {r["status"]: r["c"] for r in status_rows}
        
        domain_rows = conn.execute("SELECT domain, COUNT(*) as c FROM clues WHERE status IN ('已结案', '已反馈') GROUP BY domain").fetchall()
        domain_dist = [{"name": r["domain"], "value": r["c"]} for r in domain_rows]

        case_type_rows = conn.execute("SELECT case_type, COUNT(*) as c FROM clues WHERE status IN ('已结案', '已反馈') AND case_type != '' GROUP BY case_type").fetchall()
        case_type_dist = [{"name": r["case_type"], "value": r["c"]} for r in case_type_rows]
        
        # Dashboard wants enterprise hot spots (e.g., enterprise with >1 complaint)
        hot_enterprises = conn.execute("SELECT enterprise_name, COUNT(*) as c, SUM(personnel_count) as pc FROM clues WHERE enterprise_name!='' GROUP BY enterprise_name ORDER BY c DESC LIMIT 5").fetchall()
        
        alert_rows = conn.execute("SELECT alert_level, COUNT(*) as c FROM clues WHERE alert_level!='' GROUP BY alert_level").fetchall()
        alert_dist = {r["alert_level"]: r["c"] for r in alert_rows}

    return {
        "total": total,
        "status_distribution": status_dist,
        "domain_distribution": domain_dist,
        "case_type_distribution": case_type_dist,
        "alert_distribution": alert_dist,
        "hot_enterprises": [{"name": r["enterprise_name"], "count": r["c"], "personnel": r["pc"]} for r in hot_enterprises]
    }

# Mock data ingest for cold start
def seed_mock_data():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.execute("SELECT COUNT(*) as c FROM clues").fetchone()[0]
        if c > 0 or os.getenv("SEED_MOCK_DATA", "true").lower() == 'false':
            return # already seeded or disabled
    
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

def seed_users():
    from core.auth_tool import get_password_hash
    if os.getenv("SEED_USERS", "true").lower() == 'false':
        return
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if c > 0: return
        now = _now_iso()
        users = [
            ("admin", get_password_hash("admin123"), "管理员", "系统管理员", now),
            ("director", get_password_hash("dir123"), "部门负责人", "张主任", now),
            ("procurator", get_password_hash("proc123"), "检察官", "李检察官", now),
            ("observer", get_password_hash("obs123"), "观察员", "测试观察员", now)
        ]
        conn.executemany("INSERT INTO users (username, hashed_password, role, real_name, created_at) VALUES (?, ?, ?, ?, ?)", users)
        conn.commit()

def get_user_by_username(username: str) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(row) if row else None

def create_audit_log(username: str, action: str, details: str, ip: str = "") -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO audit_logs (username, action, details, ip_address, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, action, details, ip, now)
        )
        conn.commit()
        
def get_audit_logs(limit: int = 100) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def create_notification(target_role: str, message: str) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO notifications (target_role, message, created_at) VALUES (?, ?, ?)", (target_role, message, now))
        conn.commit()

def get_unread_notifications(role: str) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM notifications WHERE target_role=? AND is_read=0 ORDER BY created_at DESC", (role,)).fetchall()
        return [dict(r) for r in rows]

def mark_notifications_read(role: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE notifications SET is_read=1 WHERE target_role=? AND is_read=0", (role,))
        conn.commit()

def get_sys_configs() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT key, value FROM sys_configs").fetchall()
        return {r["key"]: r["value"] for r in rows}

def update_sys_configs(configs: dict) -> None:
    now = _now_iso()
    with sqlite3.connect(DB_PATH) as conn:
        for k, v in configs.items():
            conn.execute("INSERT OR REPLACE INTO sys_configs (key, value, updated_at) VALUES (?, ?, ?)", (k, str(v), now))
        conn.commit()

def update_password(username: str, hashed_password: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE users SET hashed_password=? WHERE username=?", (hashed_password, username))
        conn.commit()
