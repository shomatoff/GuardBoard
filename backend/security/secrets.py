"""Bounded local secret indicators; never return matched values."""
from __future__ import annotations

import os
import re
from pathlib import Path

from backend.security.integrity import EXCLUDE, MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_DIRS

PATTERNS = {
    'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'private_key_header': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential_assignment': re.compile(rb'\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|password)\b\s*[:=]\s*["\']?[^\s"\']{8,}', re.I),
}
MAX_FINDINGS = 100


def scan(project: Path) -> dict:
    findings: list[dict] = []
    total_bytes = 0
    count = 0
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
            size = path.stat().st_size
            if size > MAX_FILE_BYTES or total_bytes + size > MAX_TOTAL_BYTES or count >= MAX_FILES:
                raise ValueError('Project exceeds safe scan limits')
            total_bytes += size
            count += 1
            relative = path.relative_to(project).as_posix()
            if name == '.env' and len(findings) < MAX_FINDINGS:
                findings.append({'path': relative, 'line': None, 'kind': 'env_file'})
            with path.open('rb') as source:
                for number, line in enumerate(source, 1):
                    if len(line) > 65536 or b'\0' in line:
                        continue
                    for kind, pattern in PATTERNS.items():
                        if pattern.search(line) and len(findings) < MAX_FINDINGS:
                            findings.append({'path': relative, 'line': number, 'kind': kind})
    return {'checked_files': count, 'findings': findings, 'truncated': len(findings) >= MAX_FINDINGS}
