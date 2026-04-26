
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path("workspace/advisor_workbench.sqlite3")


def init_approval_db(db_path: str | Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            consultation_id INTEGER,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            submitter TEXT,
            reviewer TEXT,
            proposal_json TEXT NOT NULL,
            review_comment TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.commit()
    return db_path


def submit_approval_request(
    title: str,
    proposal: dict[str, Any],
    client_id: int | None = None,
    consultation_id: int | None = None,
    submitter: str = "",
    db_path: str | Path = DB_PATH,
) -> int:
    init_approval_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO approval_requests(client_id, consultation_id, title, status, submitter, proposal_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (client_id, consultation_id, title, "待复核", submitter, json.dumps(proposal, ensure_ascii=False, default=str), now, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_approval_requests(status: str | None = None, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    init_approval_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute("SELECT * FROM approval_requests WHERE status=? ORDER BY id DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM approval_requests ORDER BY id DESC").fetchall()
        out = []
        for r in rows:
            item = dict(r)
            item["proposal"] = json.loads(item.pop("proposal_json"))
            out.append(item)
        return out


def update_approval_status(
    request_id: int,
    status: str,
    reviewer: str = "",
    review_comment: str = "",
    db_path: str | Path = DB_PATH,
) -> None:
    if status not in ["待复核", "已通过", "已退回", "已取消"]:
        raise ValueError("invalid approval status")
    init_approval_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE approval_requests SET status=?, reviewer=?, review_comment=?, updated_at=? WHERE id=?",
            (status, reviewer, review_comment, now, request_id),
        )
        conn.commit()
