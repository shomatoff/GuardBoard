"""Read-only, independent system sensors. Unavailable values stay null."""
from __future__ import annotations

from pathlib import Path
import threading
import time
from typing import Any, Callable

import psutil


def safe(call: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = call()
        return {"value": value, "available": value is not None, "reason": None if value is not None else "Sensor not available"}
    except (OSError, ValueError, RuntimeError, PermissionError) as exc:
        return {"value": None, "available": False, "reason": type(exc).__name__}


def temperature(label: str) -> float | None:
    for name, entries in psutil.sensors_temperatures().items():
        if label in name.lower():
            for entry in entries:
                if entry.current is not None and -20 < entry.current < 150:
                    return round(float(entry.current), 1)
    return None


def read_positive_int(path: Path) -> int | None:
    try:
        value = int(path.read_text().strip())
        return value if value > 0 else None
    except (OSError, ValueError):
        return None


def read_nonnegative_int(path: Path) -> int | None:
    try:
        value = int(path.read_text().strip())
        return value if value >= 0 else None
    except (OSError, ValueError):
        return None


def battery() -> dict[str, Any] | None:
    b = psutil.sensors_battery()
    if b is None:
        return None
    health = None
    for path in sorted(Path('/sys/class/power_supply').glob('BAT*')):
        full = read_positive_int(path / 'charge_full') or read_positive_int(path / 'energy_full')
        design = read_positive_int(path / 'charge_full_design') or read_positive_int(path / 'energy_full_design')
        if full and design:
            health = round(full / design * 100, 1)
            break
    return {"percent": b.percent, "plugged": b.power_plugged,
            "seconds_left": b.secsleft if b.secsleft >= 0 else None,
            "health_percent": health, "unplugged_seconds": None}


def gpu() -> dict[str, Any] | None:
    cards = sorted(Path('/sys/class/drm').glob('card[0-9]'))
    for card in cards:
        device = card / 'device'
        try:
            vendor = (device / 'vendor').read_text().strip()
        except OSError:
            continue
        if vendor == '0x1002':
            usage = None
            try:
                raw = (device / 'gpu_busy_percent').read_text().strip()
                parsed = int(raw)
                if 0 <= parsed <= 100:
                    usage = parsed
            except (OSError, ValueError):
                pass
            vram_used = read_nonnegative_int(device / 'mem_info_vram_used')
            vram_total = read_positive_int(device / 'mem_info_vram_total')
            power = None
            for path in (device / 'hwmon').glob('hwmon*/power1_input'):
                raw_power = read_nonnegative_int(path)
                if raw_power is not None:
                    power = round(raw_power / 1_000_000, 2)
                    break
            return {"vendor": "AMD", "usage_percent": usage,
                    "vram_used_bytes": vram_used, "vram_total_bytes": vram_total,
                    "power_watts": power}
        if vendor == '0x8086':
            return {"vendor": "Intel", "usage_percent": None}
        if vendor == '0x10de':
            return {"vendor": "NVIDIA", "usage_percent": None}
    return None


def fan_speeds() -> list[dict[str, Any]] | None:
    fans = psutil.sensors_fans()
    result = []
    for chip, entries in fans.items():
        for entry in entries:
            if entry.current is not None and entry.current >= 0:
                result.append({'chip': chip, 'label': entry.label or chip, 'rpm': entry.current})
    return result or None


def per_core_frequency() -> list[float] | None:
    entries = psutil.cpu_freq(percpu=True)
    return [round(entry.current, 1) for entry in entries] if entries else None


def memory_detail() -> dict[str, int]:
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {"total": memory.total, "available": memory.available,
            "used": memory.used, "swap_total": swap.total, "swap_used": swap.used}


def disk_detail() -> dict[str, int]:
    disk = psutil.disk_usage('/')
    return {"total": disk.total, "used": disk.used, "free": disk.free}


def cpu_frequency() -> float | None:
    frequency = psutil.cpu_freq()
    return round(frequency.current, 1) if frequency else None




class DiskRateSampler:
    def __init__(self):
        self._previous = None
        self._lock = threading.Lock()

    def sample(self) -> dict[str, float] | None:
        io = psutil.disk_io_counters()
        if io is None:
            return None
        now = time.monotonic()
        with self._lock:
            previous = self._previous
            self._previous = (io.read_bytes, io.write_bytes, now)
        if previous is None or now <= previous[2]:
            return None
        elapsed = now - previous[2]
        return {'read_bytes_per_second': max(0.0, (io.read_bytes - previous[0]) / elapsed),
                'write_bytes_per_second': max(0.0, (io.write_bytes - previous[1]) / elapsed)}


disk_rates = DiskRateSampler()


def collect() -> dict[str, dict[str, Any]]:
    return {
        "cpu": safe(lambda: psutil.cpu_percent(interval=None)),
        "memory": safe(lambda: psutil.virtual_memory().percent),
        "per_core": safe(lambda: psutil.cpu_percent(interval=None, percpu=True)),
        "cpu_frequency": safe(cpu_frequency),
        "per_core_frequency": safe(per_core_frequency),
        "memory_detail": safe(memory_detail),
        "disk": safe(lambda: psutil.disk_usage('/').percent),
        "disk_detail": safe(disk_detail),
        "disk_io": safe(disk_rates.sample),
        "cpu_temperature": safe(lambda: temperature('k10temp')),
        "gpu_temperature": safe(lambda: temperature('amdgpu')),
        "gpu": safe(gpu),
        "battery": safe(battery),
        "fans": safe(fan_speeds),
        "uptime_seconds": safe(lambda: round(__import__('time').time() - psutil.boot_time())),
    }
