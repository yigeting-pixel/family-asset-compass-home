
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path("workspace/advisor_workbench.sqlite3")


def init_audit_db(db_path: str | Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            payload_json TEXT,
            created_at TEXT NOT NULL
        )
        """)
        conn.commit()
    return db_path


def log_event(
    action: str,
    actor: str = "",
    entity_type: str = "",
    entity_id: str = "",
    payload: dict[str, Any] | None = None,
    db_path: str | Path = DB_PATH,
) -> int:
    init_audit_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO audit_logs(actor, action, entity_type, entity_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (actor, action, entity_type, entity_id, json.dumps(payload or {}, ensure_ascii=False, default=str), now),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_audit_logs(limit: int = 200, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    init_audit_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out = []
        for r in rows:
            item = dict(r)
            try:
                item["payload"] = json.loads(item.pop("payload_json") or "{}")
            except Exception:
                item["payload"] = {}
            out.append(item)
        return out
