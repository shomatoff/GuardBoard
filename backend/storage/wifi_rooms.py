"""Local, user-labeled Wi-Fi signal walk-test observations."""
from __future__ import annotations

import sqlite3
from backend.storage.private import ensure_private_file
import time
from pathlib import Path


class RoomStore:
    def __init__(self, path: Path):
        self.path = path
        ensure_private_file(self.path)
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS room_samples (id INTEGER PRIMARY KEY, timestamp REAL NOT NULL, room TEXT NOT NULL, rssi_dbm INTEGER NOT NULL)')

    def add(self, room: str, rssi_dbm: int) -> dict:
        timestamp = time.time()
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO room_samples(timestamp, room, rssi_dbm) VALUES (?, ?, ?)', (timestamp, room, rssi_dbm))
        return {'timestamp': timestamp, 'room': room, 'rssi_dbm': rssi_dbm}

    def list(self) -> list[dict]:
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            baseline = db.execute('SELECT rssi_dbm FROM room_samples ORDER BY id ASC LIMIT 1').fetchone()
            rows = db.execute('SELECT timestamp, room, rssi_dbm FROM room_samples ORDER BY id DESC LIMIT 100').fetchall()
        result = [dict(row) for row in reversed(rows)]
        if result and baseline:
            reference = baseline['rssi_dbm']
            for row in result:
                row['relative_attenuation_db'] = reference - row['rssi_dbm']
        return result
