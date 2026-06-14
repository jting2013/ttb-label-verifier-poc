import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.config import get_settings


def _db_path() -> Path:
    url = get_settings().database_url
    if not url.startswith("sqlite:///"):
        raise ValueError("Prototype currently supports sqlite:/// database URLs only")
    return Path(url.replace("sqlite:///", "", 1))


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    db_file = _db_path()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS review_results (
                result_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                application_id TEXT NOT NULL,
                status TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )


def save_result(batch_id: str, result: dict) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO review_results
            (result_id, batch_id, filename, application_id, status, uploaded_at, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["result_id"],
                batch_id,
                result["filename"],
                result["application_id"],
                result["status"],
                result["uploaded_at"],
                json.dumps(result),
            ),
        )


def list_results() -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT payload_json FROM review_results ORDER BY uploaded_at DESC LIMIT 500"
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def list_batch(batch_id: str) -> list[dict]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT payload_json FROM review_results WHERE batch_id = ? ORDER BY uploaded_at ASC",
            (batch_id,),
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]
