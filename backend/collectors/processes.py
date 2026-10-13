"""Read-only process rates calculated from two observations."""
from __future__ import annotations

import threading
import time
from typing import Any

import psutil


class ProcessSampler:
    def __init__(self):
        self._previous: dict[tuple[int, float], tuple[float, int, float]] = {}
        self._lock = threading.Lock()

    def sample(self, now: float | None = None) -> dict[str, Any]:
        timestamp = time.monotonic() if now is None else now
        current: dict[tuple[int, float], tuple[float, int, float]] = {}
        rows = []
        with self._lock:
            for process in psutil.process_iter(attrs=['pid', 'name', 'create_time', 'memory_info', 'cpu_times', 'io_counters'], ad_value=None):
                try:
                    info = process.info
                    identity = (info['pid'], info['create_time'])
                    cpu_times = info['cpu_times']
                    memory = info['memory_info']
                    io = info['io_counters']
                    cpu_total = cpu_times.user + cpu_times.system if cpu_times else None
                    io_total = io.read_bytes + io.write_bytes if io else None
                    prior = self._previous.get(identity)
                    cpu_percent = None
                    disk_rate = None
                    if prior and cpu_total is not None:
                        elapsed = timestamp - prior[2]
                        if elapsed > 0:
                            cpu_percent = max(0.0, (cpu_total - prior[0]) / elapsed * 100)
                            if io_total is not None and prior[1] is not None:
                                disk_rate = max(0.0, (io_total - prior[1]) / elapsed)
                    current[identity] = (cpu_total, io_total, timestamp)
                    rows.append({
                        'pid': info['pid'], 'name': (info['name'] or 'Unknown')[:120],
                        'memory_bytes': memory.rss if memory else None,
                        'cpu_percent': round(cpu_percent, 1) if cpu_percent is not None else None,
                        'disk_bytes_per_second': round(disk_rate, 1) if disk_rate is not None else None,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError, TypeError, KeyError):
                    continue
            self._previous = current
        def ranked(key: str) -> list[dict]:
            return sorted((row for row in rows if row[key] is not None), key=lambda row: row[key], reverse=True)[:10]
        return {'top_cpu': ranked('cpu_percent'), 'top_memory': ranked('memory_bytes'), 'top_disk': ranked('disk_bytes_per_second'),
                'sampled_at': time.time(), 'process_count': len(rows)}
