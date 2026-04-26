from __future__ import annotations
import json, os, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Text, Float, select, desc, insert
from sqlalchemy.engine import Engine

DEFAULT_SQLITE_PATH = Path("workspace/cloud_sync.sqlite3")

def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url
    DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_SQLITE_PATH}"

def get_engine(database_url: str | None = None) -> Engine:
    return create_engine(database_url or get_database_url(), future=True, pool_pre_ping=True)

metadata = MetaData()
family_states = Table("family_states", metadata,
    Column("id", Integer, primary_key=True),
    Column("family_key_hash", String(128), index=True, nullable=False),
    Column("family_label", String(200)),
    Column("payload_json", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
fund_snapshots = Table("fund_snapshots", metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String(20), index=True, nullable=False),
    Column("name", String(200)),
    Column("nav", Float),
    Column("nav_date", String(20)),
    Column("source", String(100)),
    Column("payload_json", Text),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
environment_snapshots = Table("environment_snapshots", metadata,
    Column("id", Integer, primary_key=True),
    Column("source", String(100)),
    Column("score", Float),
    Column("level", String(50)),
    Column("payload_json", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

def init_db(engine: Engine | None = None) -> None:
    metadata.create_all(engine or get_engine())

def hash_family_key(family_key: str) -> str:
    return hashlib.sha256(family_key.encode("utf-8")).hexdigest()

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def save_family_state(family_key: str, payload: dict[str, Any], family_label: str = "", engine: Engine | None = None) -> int:
    engine = engine or get_engine(); init_db(engine)
    with engine.begin() as conn:
        r = conn.execute(insert(family_states).values(
            family_key_hash=hash_family_key(family_key), family_label=family_label,
            payload_json=json.dumps(payload, ensure_ascii=False, default=str), created_at=now_utc()))
        return int(r.inserted_primary_key[0])

def load_latest_family_state(family_key: str, engine: Engine | None = None) -> dict[str, Any] | None:
    engine = engine or get_engine(); init_db(engine)
    stmt = select(family_states).where(family_states.c.family_key_hash == hash_family_key(family_key)).order_by(desc(family_states.c.created_at)).limit(1)
    with engine.connect() as conn:
        row = conn.execute(stmt).mappings().first()
        if not row: return None
        return {"id": row["id"], "family_label": row["family_label"], "created_at": row["created_at"].isoformat() if row["created_at"] else None, "payload": json.loads(row["payload_json"])}

def save_fund_snapshot(row: dict[str, Any], engine: Engine | None = None) -> int:
    engine = engine or get_engine(); init_db(engine)
    with engine.begin() as conn:
        r = conn.execute(insert(fund_snapshots).values(
            code=str(row.get("code","")).zfill(6), name=row.get("name",""),
            nav=float(row.get("nav")) if row.get("nav") not in [None, ""] else None,
            nav_date=str(row.get("nav_date","")), source=row.get("source",""),
            payload_json=json.dumps(row, ensure_ascii=False, default=str), created_at=now_utc()))
        return int(r.inserted_primary_key[0])

def latest_fund_snapshots(engine: Engine | None = None, limit: int = 200) -> list[dict[str, Any]]:
    engine = engine or get_engine(); init_db(engine)
    with engine.connect() as conn:
        rows = conn.execute(select(fund_snapshots).order_by(desc(fund_snapshots.c.created_at)).limit(limit)).mappings().all()
        out=[]
        for r in rows:
            item=dict(r); item["created_at"] = item["created_at"].isoformat() if item["created_at"] else None
            try: item["payload"] = json.loads(item.pop("payload_json") or "{}")
            except Exception: item["payload"] = {}
            out.append(item)
        return out

def save_environment_snapshot(payload: dict[str, Any], engine: Engine | None = None) -> int:
    engine = engine or get_engine(); init_db(engine)
    with engine.begin() as conn:
        r = conn.execute(insert(environment_snapshots).values(
            source=payload.get("source","manual/sample"), score=float(payload.get("score",0)), level=payload.get("level",""),
            payload_json=json.dumps(payload, ensure_ascii=False, default=str), created_at=now_utc()))
        return int(r.inserted_primary_key[0])

def latest_environment_snapshot(engine: Engine | None = None) -> dict[str, Any] | None:
    engine = engine or get_engine(); init_db(engine)
    with engine.connect() as conn:
        r = conn.execute(select(environment_snapshots).order_by(desc(environment_snapshots.c.created_at)).limit(1)).mappings().first()
        if not r: return None
        return {"id": r["id"], "created_at": r["created_at"].isoformat() if r["created_at"] else None, "source": r["source"], "score": r["score"], "level": r["level"], "payload": json.loads(r["payload_json"])}
