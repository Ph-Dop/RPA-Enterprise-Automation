"""SQLite persistence for orders and run audit logs.

SQLite (instead of Excel) is the system of record: the Excel file is only
the human-readable report output. The run log table provides the audit
trail expected by European SME compliance.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    order_id   TEXT PRIMARY KEY,
    customer   TEXT,
    ordered_at TEXT,
    product    TEXT,
    amount     REAL,
    status     TEXT,
    source     TEXT,
    ingested_at TEXT
);
CREATE TABLE IF NOT EXISTS run_log (
    run_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    step       TEXT,
    status     TEXT,
    started_at TEXT,
    finished_at TEXT,
    error      TEXT,
    message    TEXT
);
"""


class OrderStore:
    """Thread-safe-enough SQLite wrapper used by the pipeline."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # -- orders ---------------------------------------------------------
    def save_orders(self, df: pd.DataFrame, source: str = "mock") -> int:
        """Insert or replace orders. Returns number of rows written."""
        if df.empty:
            return 0
        now = datetime.now().isoformat(timespec="seconds")
        rows = [
            (
                str(r.order_id),
                str(r.customer),
                str(r.ordered_at),
                str(r.product),
                float(r.amount),
                str(r.status),
                source,
                now,
            )
            for r in df.itertuples(index=False)
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO orders
                (order_id, customer, ordered_at, product, amount, status, source, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def load_orders(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query("SELECT * FROM orders", conn)

    # -- run audit log --------------------------------------------------
    def start_run(self, step: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO run_log (step, status, started_at) VALUES (?, ?, ?)",
                (step, "running", datetime.now().isoformat(timespec="seconds")),
            )
            return int(cur.lastrowid)

    def finish_run(
        self,
        run_id: int,
        status: str,
        error: str | None = None,
        message: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE run_log SET status = ?, finished_at = ?, error = ?, message = ? "
                "WHERE run_id = ?",
                (
                    status,
                    datetime.now().isoformat(timespec="seconds"),
                    error,
                    message,
                    run_id,
                ),
            )

    def recent_run_statuses(self, limit: int = 50) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status FROM run_log WHERE step = 'pipeline' ORDER BY run_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [r["status"] for r in rows]
