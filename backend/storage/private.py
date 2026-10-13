"""Create private application storage without following a final symlink."""
from __future__ import annotations

import os
from pathlib import Path


def ensure_private_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink():
        raise ValueError('Storage directory must not be a symlink')
    path.parent.chmod(0o700)


def ensure_private_file(path: Path) -> None:
    ensure_private_parent(path)
    if path.is_symlink():
        raise ValueError('Storage file must not be a symlink')
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    except FileExistsError:
        if not path.is_file() or path.is_symlink():
            raise ValueError('Invalid storage file')
    else:
        os.close(descriptor)
    path.chmod(0o600)
