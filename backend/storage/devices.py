"""Local known/trusted device state, written only after ownership confirmation."""
from __future__ import annotations

import sqlite3
from backend.storage.private import ensure_private_file
import time
from pathlib import Path


class DeviceStore:
    def __init__(self, path: Path):
        self.path = path
        ensure_private_file(self.path)
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS devices (mac TEXT PRIMARY KEY, first_seen REAL NOT NULL, last_seen REAL NOT NULL, trusted INTEGER NOT NULL DEFAULT 0)')

    def observe(self, devices: list[dict]) -> list[dict]:
        now = time.time()
        result = []
        with sqlite3.connect(self.path) as db:
            for device in devices:
                row = db.execute('SELECT first_seen, trusted FROM devices WHERE mac = ?', (device['mac'],)).fetchone()
                if row is None:
                    db.execute('INSERT INTO devices(mac, first_seen, last_seen, trusted) VALUES (?, ?, ?, 0)', (device['mac'], now, now))
                    first_seen, trusted, new = now, False, True
                else:
                    db.execute('UPDATE devices SET last_seen = ? WHERE mac = ?', (now, device['mac']))
                    first_seen, trusted, new = row[0], bool(row[1]), False
                result.append({**device, 'first_seen': first_seen, 'last_seen': now,
                               'trusted': trusted, 'newly_observed': new})
        return result

    def set_trusted(self, mac: str, trusted: bool) -> bool:
        with sqlite3.connect(self.path) as db:
            result = db.execute('UPDATE devices SET trusted = ? WHERE mac = ?', (int(trusted), mac))
            return result.rowcount == 1
