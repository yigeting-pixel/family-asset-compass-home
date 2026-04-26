
from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path("workspace/advisor_workbench.sqlite3")


ROLE_PERMISSIONS = {
    "advisor": [
        "client:create",
        "client:read",
        "consultation:create",
        "consultation:read",
        "proposal:submit",
    ],
    "supervisor": [
        "client:create",
        "client:read",
        "consultation:create",
        "consultation:read",
        "proposal:submit",
        "proposal:review",
        "report:export",
    ],
    "risk": [
        "client:read",
        "consultation:read",
        "proposal:review",
        "risk:review",
        "report:export",
    ],
    "admin": ["*"],
}


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def init_auth_db(db_path: str | Path = DB_PATH) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            role TEXT NOT NULL,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.commit()
    return db_path


def create_user(
    username: str,
    password: str,
    role: str = "advisor",
    display_name: str = "",
    db_path: str | Path = DB_PATH,
) -> int:
    if role not in ROLE_PERMISSIONS:
        raise ValueError(f"Unknown role: {role}")
    init_auth_db(db_path)
    salt = secrets.token_hex(12)
    password_hash = _hash_password(password, salt)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO users(username, display_name, role, salt, password_hash, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, display_name or username, role, salt, password_hash, now, now),
        )
        conn.commit()
        return int(cur.lastrowid)


def create_demo_users(db_path: str | Path = DB_PATH) -> None:
    init_auth_db(db_path)
    demos = [
        ("advisor", "advisor123", "advisor", "演示顾问"),
        ("supervisor", "supervisor123", "supervisor", "演示主管"),
        ("risk", "risk123", "risk", "演示风控"),
        ("admin", "admin123", "admin", "演示管理员"),
    ]
    for username, password, role, display_name in demos:
        try:
            create_user(username, password, role, display_name, db_path)
        except sqlite3.IntegrityError:
            pass


def authenticate(username: str, password: str, db_path: str | Path = DB_PATH) -> dict[str, Any] | None:
    init_auth_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,)).fetchone()
        if not row:
            return None
        expected = _hash_password(password, row["salt"])
        if expected != row["password_hash"]:
            return None
        user = dict(row)
        user.pop("salt", None)
        user.pop("password_hash", None)
        return user


def list_users(db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    init_auth_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT id, username, display_name, role, is_active, created_at, updated_at FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, [])
    return "*" in perms or permission in perms


def permission_matrix() -> list[dict[str, Any]]:
    permissions = sorted({p for ps in ROLE_PERMISSIONS.values() for p in ps if p != "*"})
    rows = []
    for role, perms in ROLE_PERMISSIONS.items():
        row = {"role": role}
        for p in permissions:
            row[p] = "*" in perms or p in perms
        rows.append(row)
    return rows
