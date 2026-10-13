"""Bounded local SHA-256 project integrity baselines."""
from __future__ import annotations

import fnmatch
import hashlib
import os
import sqlite3
from backend.storage.private import ensure_private_file
from pathlib import Path

MAX_FILES = 2000
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_DIRS = 5000
EXCLUDE = {'.git', '.venv', 'node_modules', '__pycache__', '.mypy_cache', '.pytest_cache'}


def validate_project(path: str, allowed_root: Path) -> Path:
    root = allowed_root.resolve()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute() or candidate.is_symlink():
        raise ValueError('Project path must be an absolute, non-symlink directory')
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ValueError('Project directory unavailable') from exc
    if not resolved.is_dir() or not resolved.is_relative_to(root) or resolved == root:
        raise ValueError('Project must be a directory under the allowed home directory')
    return resolved


def hash_files(project: Path) -> dict[str, str]:
    hashes = {}
    total_bytes = 0
    visited_dirs = 0
    for current, dirs, files in os.walk(project, followlinks=False):
        visited_dirs += 1
        if visited_dirs > MAX_DIRS:
            raise ValueError('Project exceeds safe directory limit')
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDE and not (Path(current) / name).is_symlink())
        for name in sorted(files):
            path = Path(current) / name
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(project).as_posix()
            if any(fnmatch.fnmatch(relative, pattern) for pattern in ('*.pyc', '*.sqlite', '*.db')):
                continue
            size = path.stat().st_size
            if size > MAX_FILE_BYTES or total_bytes + size > MAX_TOTAL_BYTES or len(hashes) >= MAX_FILES:
                raise ValueError('Project exceeds safe scan limits')
            digest = hashlib.sha256()
            with path.open('rb') as source:
                while chunk := source.read(65536):
                    digest.update(chunk)
            hashes[relative] = digest.hexdigest()
            total_bytes += size
    return hashes


class IntegrityStore:
    def __init__(self, path: Path):
        ensure_private_file(path)
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS baselines (project TEXT NOT NULL, relative_path TEXT NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(project, relative_path))')
            db.execute('CREATE TABLE IF NOT EXISTS projects (project TEXT PRIMARY KEY, created_at REAL NOT NULL)')

    def baseline(self, project: Path) -> int:
        hashes = hash_files(project)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO projects(project, created_at) VALUES (?, strftime('%s','now'))", (str(project),))
            db.execute('DELETE FROM baselines WHERE project = ?', (str(project),))
            db.executemany('INSERT INTO baselines(project, relative_path, sha256) VALUES (?, ?, ?)',
                           [(str(project), relative, digest) for relative, digest in hashes.items()])
        return len(hashes)

    def compare(self, project: Path) -> dict:
        current = hash_files(project)
        with sqlite3.connect(self.path) as db:
            exists = db.execute('SELECT 1 FROM projects WHERE project = ?', (str(project),)).fetchone()
            previous = dict(db.execute('SELECT relative_path, sha256 FROM baselines WHERE project = ?', (str(project),)))
        if not exists:
            raise ValueError('No baseline for this project')
        return {'new': sorted(current.keys() - previous.keys()),
                'deleted': sorted(previous.keys() - current.keys()),
                'modified': sorted(key for key in current.keys() & previous.keys() if current[key] != previous[key]),
                'checked_files': len(current)}
