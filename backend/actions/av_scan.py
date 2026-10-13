"""Bounded, user-triggered ClamAV jobs. No delete/move options exist."""
from __future__ import annotations

import asyncio
import os
import secrets
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from backend.security.integrity import EXCLUDE, MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_DIRS

MAX_OUTPUT_BYTES = 65536
SCAN_TIMEOUT = 180


def command_for(project: Path) -> list[str]:
    binary = shutil.which('clamscan')
    if not binary:
        raise ValueError('ClamAV unavailable')
    if not any(Path('/var/lib/clamav').glob('*.cvd')):
        raise ValueError('ClamAV signatures unavailable')
    files: list[str] = []
    total_bytes = 0
    argument_bytes = 0
    visited_dirs = 0
    for current, dirs, names in os.walk(project, followlinks=False):
        visited_dirs += 1
        if visited_dirs > MAX_DIRS:
            raise ValueError('Project exceeds safe directory limit')
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDE and not (Path(current) / name).is_symlink())
        for name in sorted(names):
            path = Path(current) / name
            if path.is_symlink() or not path.is_file():
                continue
            size = path.stat().st_size
            argument_bytes += len(os.fsencode(path)) + 1
            if size > MAX_FILE_BYTES or total_bytes + size > MAX_TOTAL_BYTES or len(files) >= MAX_FILES or argument_bytes > 100000:
                raise ValueError('Project exceeds safe scan limits')
            total_bytes += size
            files.append(str(path))
    if not files:
        raise ValueError('No regular files to scan')
    return [binary, '--infected', '--no-summary',
            '--follow-dir-symlinks=0', '--follow-file-symlinks=0',
            '--max-filesize=10M', '--max-scansize=100M', '--max-files=2000', *files]


@dataclass
class ScanJob:
    id: str
    project: str
    status: str = 'queued'
    started_at: float | None = None
    finished_at: float | None = None
    findings: list[str] = field(default_factory=list)
    error: str | None = None
    process: asyncio.subprocess.Process | None = field(default=None, repr=False)
    task: asyncio.Task | None = field(default=None, repr=False)

    def public(self) -> dict:
        return {'id': self.id, 'project': self.project, 'status': self.status,
                'started_at': self.started_at, 'finished_at': self.finished_at,
                'findings': self.findings, 'error': self.error}


class ScanManager:
    def __init__(self):
        self.jobs: dict[str, ScanJob] = {}
        self._lock = asyncio.Lock()

    async def start(self, project: Path) -> ScanJob:
        async with self._lock:
            if any(job.status in ('queued', 'running') for job in self.jobs.values()):
                raise ValueError('A scan is already running')
            command = await asyncio.to_thread(command_for, project)
            job = ScanJob(id=secrets.token_urlsafe(16), project=str(project))
            self.jobs[job.id] = job
            if len(self.jobs) > 20:
                for key in list(self.jobs)[:-20]:
                    if self.jobs[key].status not in ('queued', 'running'):
                        self.jobs.pop(key, None)
            job.task = asyncio.create_task(self._run(job, command))
            return job

    async def _read_limited(self, stream: asyncio.StreamReader) -> bytes:
        output = bytearray()
        while chunk := await stream.read(4096):
            if len(output) + len(chunk) > MAX_OUTPUT_BYTES:
                raise ValueError('Scanner output exceeded safe limit')
            output.extend(chunk)
        return bytes(output)

    async def _stop_process(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=3)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

    async def _run(self, job: ScanJob, command: list[str]) -> None:
        if job.status == 'cancelled':
            return
        job.status = 'running'
        job.started_at = time.time()
        try:
            process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE,
                                                           stderr=asyncio.subprocess.PIPE)
            job.process = process
            stdout, stderr, _ = await asyncio.wait_for(
                asyncio.gather(self._read_limited(process.stdout),
                               self._read_limited(process.stderr), process.wait()),
                timeout=SCAN_TIMEOUT)
            job.findings = [line[:500] for line in stdout.decode('utf-8', 'replace').splitlines()
                            if line.endswith(' FOUND')][:100]
            job.status = 'completed' if process.returncode in (0, 1) else 'failed'
            if job.status == 'failed':
                job.error = stderr[:500].decode('utf-8', 'replace') or f'ClamAV exit {process.returncode}'
        except (asyncio.TimeoutError, ValueError) as exc:
            if job.process:
                await self._stop_process(job.process)
            job.status = 'failed'
            job.error = 'Scan timed out' if isinstance(exc, asyncio.TimeoutError) else str(exc)
        except OSError as exc:
            job.status = 'failed'
            job.error = type(exc).__name__
        except asyncio.CancelledError:
            if job.process:
                await self._stop_process(job.process)
            job.status = 'cancelled'
            raise
        finally:
            job.finished_at = time.time()

    async def cancel(self, job_id: str) -> ScanJob:
        job = self.jobs.get(job_id)
        if not job:
            raise KeyError(job_id)
        if job.status in ('queued', 'running'):
            job.status = 'cancelled'
            if job.process:
                await self._stop_process(job.process)
            if job.task and not job.task.done():
                job.task.cancel()
                try:
                    await job.task
                except asyncio.CancelledError:
                    pass
            job.status = 'cancelled'
            job.finished_at = time.time()
        return job
