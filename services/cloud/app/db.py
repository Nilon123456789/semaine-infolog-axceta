"""
SQLite persistence for devices and time-series samples.

Uses WAL mode for concurrent readers (API) and a single writer (MQTT ingest).
"""

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    device_id   TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    powered     INTEGER NOT NULL DEFAULT 1,
    last_seen   REAL NOT NULL,
    last_watts  REAL NOT NULL DEFAULT 0,
    last_amps   REAL NOT NULL DEFAULT 0,
    last_voltage REAL NOT NULL DEFAULT 120
);

CREATE TABLE IF NOT EXISTS samples (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id   TEXT NOT NULL,
    watts       REAL NOT NULL,
    amps        REAL NOT NULL,
    voltage     REAL NOT NULL,
    powered     INTEGER NOT NULL,
    ts          REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_samples_ts ON samples(ts);
CREATE INDEX IF NOT EXISTS idx_samples_device_ts ON samples(device_id, ts);
"""


class Database:
    """Thread-safe thin wrapper around a SQLite database file."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = self._connect()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def upsert_sample(
        self,
        *,
        device_id: str,
        device_name: str,
        device_type: str,
        watts: float,
        amps: float,
        voltage: float,
        powered: bool,
        ts: float,
    ) -> None:
        """Insert a sample and refresh the device registry row."""
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO devices (
                    device_id, device_name, device_type, powered,
                    last_seen, last_watts, last_amps, last_voltage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    device_name=excluded.device_name,
                    device_type=excluded.device_type,
                    powered=excluded.powered,
                    last_seen=excluded.last_seen,
                    last_watts=excluded.last_watts,
                    last_amps=excluded.last_amps,
                    last_voltage=excluded.last_voltage
                """,
                (
                    device_id,
                    device_name,
                    device_type,
                    1 if powered else 0,
                    ts,
                    watts,
                    amps,
                    voltage,
                ),
            )
            conn.execute(
                """
                INSERT INTO samples (device_id, watts, amps, voltage, powered, ts)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (device_id, watts, amps, voltage, 1 if powered else 0, ts),
            )

    def list_devices(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM devices ORDER BY device_name COLLATE NOCASE"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM devices WHERE device_id = ?", (device_id,)
            ).fetchone()
        return dict(row) if row else None

    def samples_between(self, start_ts: float, end_ts: float) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT device_id, watts, ts
                FROM samples
                WHERE ts >= ? AND ts < ?
                ORDER BY ts ASC
                """,
                (start_ts, end_ts),
            ).fetchall()
        return [dict(r) for r in rows]

    def prune_old_samples(self, retain_days: float = 7.0) -> int:
        """Drop samples older than retain_days. Returns deleted row count."""
        cutoff = time.time() - retain_days * 86400
        with self.connection() as conn:
            cur = conn.execute("DELETE FROM samples WHERE ts < ?", (cutoff,))
            return cur.rowcount
