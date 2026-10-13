"""Read-only power and CPU tuning evidence. Never applies a profile."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import psutil


def _read(path: str) -> str | None:
    try:
        value = Path(path).read_text().strip()
        return value[:100] or None
    except OSError:
        return None


def collect() -> dict:
    power_profile = None
    binary = shutil.which('powerprofilesctl')
    if binary:
        try:
            response = subprocess.run([binary, 'get'], capture_output=True, text=True, timeout=2, check=False)
            if response.returncode == 0 and len(response.stdout) < 100:
                power_profile = response.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            pass
    battery = psutil.sensors_battery()
    return {'power_profile': power_profile,
            'cpu_governor': _read('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'),
            'swappiness': _read('/proc/sys/vm/swappiness'),
            'battery_percent': battery.percent if battery else None,
            'plugged': battery.power_plugged if battery else None,
            'benchmark': None, 'changes_applied': False}
