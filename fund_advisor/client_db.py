
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path("workspace/advisor_workbench.sqlite3")


def init_db(db_path: str | Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            city TEXT,
            family_stage TEXT,
            tags TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            consultation_id INTEGER,
            note_type TEXT,
            content TEXT NOT NULL,
            next_action TEXT,
            next_follow_up_date TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            FOREIGN KEY(consultation_id) REFERENCES consultations(id)
        )
        """)
        conn.commit()
    return db_path


def create_client(
    name: str,
    phone: str = "",
    city: str = "",
    family_stage: str = "",
    tags: list[str] | None = None,
    db_path: str | Path = DB_PATH,
) -> int:
    init_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO clients(name, phone, city, family_stage, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, city, family_stage, json.dumps(tags or [], ensure_ascii=False), now, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_clients(db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM clients ORDER BY updated_at DESC, id DESC").fetchall()
        return [dict(r) for r in rows]


def save_consultation(
    client_id: int | None,
    title: str,
    profile: dict[str, Any],
    result: dict[str, Any],
    notes: str = "",
    db_path: str | Path = DB_PATH,
) -> int:
    init_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO consultations(client_id, title, profile_json, result_json, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                client_id,
                title,
                json.dumps(profile, ensure_ascii=False, default=str),
                json.dumps(result, ensure_ascii=False, default=str),
                notes,
                now,
            ),
        )
        if client_id:
            conn.execute("UPDATE clients SET updated_at=? WHERE id=?", (now, client_id))
        conn.commit()
        return int(cur.lastrowid)


def list_consultations(client_id: int | None = None, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if client_id:
            rows = conn.execute("SELECT * FROM consultations WHERE client_id=? ORDER BY created_at DESC", (client_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM consultations ORDER BY created_at DESC").fetchall()
        out = []
        for r in rows:
            item = dict(r)
            item["profile"] = json.loads(item.pop("profile_json"))
            item["result"] = json.loads(item.pop("result_json"))
            out.append(item)
        return out


def add_meeting_note(
    client_id: int | None,
    consultation_id: int | None,
    content: str,
    note_type: str = "会谈纪要",
    next_action: str = "",
    next_follow_up_date: str = "",
    db_path: str | Path = DB_PATH,
) -> int:
    init_db(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO meeting_notes(client_id, consultation_id, note_type, content, next_action, next_follow_up_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client_id, consultation_id, note_type, content, next_action, next_follow_up_date, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_meeting_notes(client_id: int | None = None, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if client_id:
            rows = conn.execute("SELECT * FROM meeting_notes WHERE client_id=? ORDER BY created_at DESC", (client_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM meeting_notes ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
