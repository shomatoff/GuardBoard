"""Bounded local telemetry history with parameterized SQLite statements."""
from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from backend.storage.private import ensure_private_file

RETENTION_SECONDS = 7 * 24 * 3600
WRITE_INTERVAL_SECONDS = 5


class HistoryStore:
    def __init__(self, path: Path):
        self.path = path
        ensure_private_file(self.path)
        self._lock = threading.Lock()
        self._last_write = 0.0
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS samples ("
                "timestamp REAL PRIMARY KEY, cpu REAL, memory REAL, disk REAL, "
                "cpu_temp REAL, gpu_temp REAL, gpu_usage REAL, battery REAL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=2)

    def record(self, readings: dict, now: float | None = None) -> bool:
        timestamp = time.time() if now is None else now
        if timestamp - self._last_write < WRITE_INTERVAL_SECONDS:
            return False
        def get(name: str):
            return readings.get(name, {}).get('value')
        gpu = get('gpu')
        battery = get('battery')
        row = (
            timestamp, get('cpu'), get('memory'), get('disk'),
            get('cpu_temperature'), get('gpu_temperature'),
            gpu.get('usage_percent') if isinstance(gpu, dict) else None,
            battery.get('percent') if isinstance(battery, dict) else None,
        )
        with self._lock:
            if timestamp - self._last_write < WRITE_INTERVAL_SECONDS:
                return False
            with self._connect() as connection:
                connection.execute(
                    "INSERT OR REPLACE INTO samples VALUES (?, ?, ?, ?, ?, ?, ?, ?)", row
                )
                connection.execute("DELETE FROM samples WHERE timestamp < ?", (timestamp - RETENTION_SECONDS,))
            self._last_write = timestamp
        return True

    def query(self, window_seconds: int, now: float | None = None) -> list[dict]:
        if window_seconds not in (3600, 86400):
            raise ValueError('Unsupported history window')
        timestamp = time.time() if now is None else now
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT timestamp, cpu, memory, disk, cpu_temp, gpu_temp, gpu_usage, battery "
                "FROM samples WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC LIMIT 20000",
                (timestamp - window_seconds, timestamp),
            ).fetchall()
        return [dict(row) for row in rows]
