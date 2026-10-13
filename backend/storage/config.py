"""Validated, atomic local TOML settings storage."""
from __future__ import annotations

import os
import tempfile
import tomllib
from pathlib import Path
from backend.storage.private import ensure_private_parent

DEFAULT_THRESHOLDS = {'cpu_temperature': 90.0, 'gpu_temperature': 90.0,
                      'memory': 90.0, 'disk': 90.0, 'battery': 15.0}
RANGES = {'cpu_temperature': (50.0, 120.0), 'gpu_temperature': (50.0, 120.0),
          'memory': (50.0, 99.0), 'disk': (50.0, 99.0), 'battery': (1.0, 50.0)}


def validate_thresholds(values: dict) -> dict[str, float]:
    if set(values) != set(DEFAULT_THRESHOLDS):
        raise ValueError('Invalid threshold names')
    result = {}
    for name, (low, high) in RANGES.items():
        value = values[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            raise ValueError('Invalid alert threshold')
        result[name] = float(value)
    return result


class ConfigStore:
    def __init__(self, path: Path):
        self.path = path
        ensure_private_parent(path)
        if path.is_symlink():
            raise ValueError('Configuration file must not be a symlink')
        if path.exists():
            if not path.is_file():
                raise ValueError('Configuration path must be a file')
            path.chmod(0o600)

    def read(self) -> dict[str, float]:
        try:
            with self.path.open('rb') as source:
                config = tomllib.load(source)
        except FileNotFoundError:
            return DEFAULT_THRESHOLDS.copy()
        return validate_thresholds(config.get('alerts', {}))

    def write(self, values: dict) -> dict[str, float]:
        result = validate_thresholds(values)
        content = '[alerts]\n' + ''.join(f'{name} = {value:.1f}\n' for name, value in result.items())
        fd, temporary = tempfile.mkstemp(prefix='config-', suffix='.toml', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as target:
                target.write(content)
                target.flush()
                os.fsync(target.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return result
