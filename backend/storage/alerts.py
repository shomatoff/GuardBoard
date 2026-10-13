"""Local, deduplicated telemetry alerts with bounded retention."""
from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from backend.storage.config import DEFAULT_THRESHOLDS, validate_thresholds
from backend.storage.private import ensure_private_file

DEDUP_SECONDS = 300
RETENTION_SECONDS = 7 * 86400


class AlertStore:
    def __init__(self, path: Path, thresholds: dict | None = None):
        ensure_private_file(path)
        self.path = path
        self._lock = threading.Lock()
        self.thresholds = validate_thresholds(thresholds or DEFAULT_THRESHOLDS)
        self._last_cleanup = 0.0
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, timestamp REAL NOT NULL, kind TEXT NOT NULL, severity TEXT NOT NULL, value REAL NOT NULL)')
            db.execute('CREATE INDEX IF NOT EXISTS alerts_time ON alerts(timestamp DESC)')

    def observe(self, readings: dict, now: float | None = None) -> int:
        timestamp = time.time() if now is None else now
        candidates = []
        for kind, threshold in self.thresholds.items():
            value = readings.get(kind, {}).get('value')
            if kind == 'battery':
                if not isinstance(value, dict) or value.get('plugged') is not False:
                    continue
                value = value.get('percent')
                triggered = isinstance(value, (int, float)) and value < threshold
            else:
                triggered = isinstance(value, (int, float)) and value >= threshold
            if triggered:
                candidates.append((kind, 'critical' if kind.endswith('temperature') else 'warning', float(value)))
        if not candidates and timestamp - self._last_cleanup < 3600:
            return 0
        added = 0
        with self._lock, sqlite3.connect(self.path, timeout=2) as db:
            for kind, severity, value in candidates:
                previous = db.execute('SELECT timestamp FROM alerts WHERE kind = ? ORDER BY timestamp DESC LIMIT 1', (kind,)).fetchone()
                if previous and timestamp - previous[0] < DEDUP_SECONDS:
                    continue
                db.execute('INSERT INTO alerts(timestamp, kind, severity, value) VALUES (?,?,?,?)', (timestamp, kind, severity, value))
                added += 1
            db.execute('DELETE FROM alerts WHERE timestamp < ?', (timestamp - RETENTION_SECONDS,))
            self._last_cleanup = timestamp
        return added

    def set_thresholds(self, values: dict) -> None:
        self.thresholds = validate_thresholds(values)

    def recent(self, limit: int = 100, now: float | None = None) -> list[dict]:
        if not 1 <= limit <= 100:
            raise ValueError('Invalid alert limit')
        with sqlite3.connect(self.path, timeout=2) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute('SELECT id, timestamp, kind, severity, value FROM alerts WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT ?',
                              ((time.time() if now is None else now) - RETENTION_SECONDS, limit)).fetchall()
        return [dict(row) for row in rows]
