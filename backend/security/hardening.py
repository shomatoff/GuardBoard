"""Read-only Linux hardening indicators; each check fails independently."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _run(args: list[str]) -> str | None:
    try:
        response = subprocess.run(args, capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if response.returncode != 0 or len(response.stdout) > 32768:
        return None
    return response.stdout.strip()


def updates() -> dict:
    try:
        content = Path('/etc/apt/apt.conf.d/20auto-upgrades').read_text()
    except OSError:
        return {'status': 'unknown', 'evidence': 'config_unreadable'}
    value = 'APT::Periodic::Unattended-Upgrade "1";' in content
    return {'status': 'enabled' if value else 'not_enabled', 'evidence': 'local_apt_config'}


def ssh() -> dict:
    binary = shutil.which('sshd')
    if not binary:
        return {'status': 'unavailable', 'evidence': 'sshd_absent'}
    output = _run([binary, '-T'])
    if output is None:
        return {'status': 'unknown', 'evidence': 'sshd_effective_unreadable'}
    settings = dict(line.split(' ', 1) for line in output.splitlines() if ' ' in line)
    return {'status': 'observed', 'evidence': 'sshd_effective_config',
            'permit_root_login': settings.get('permitrootlogin'),
            'password_authentication': settings.get('passwordauthentication')}


def secure_boot() -> dict:
    binary = shutil.which('mokutil')
    if not binary:
        return {'status': 'unknown', 'evidence': 'mokutil_absent'}
    output = _run([binary, '--sb-state'])
    if output is None:
        return {'status': 'unknown', 'evidence': 'secure_boot_unreadable'}
    lower = output.lower()
    state = 'enabled' if 'secureboot enabled' in lower else 'not_enabled' if 'secureboot disabled' in lower else 'unknown'
    return {'status': state, 'evidence': 'mokutil_firmware_report'}


def fail2ban() -> dict:
    if not shutil.which('fail2ban-client'):
        return {'status': 'unavailable', 'evidence': 'fail2ban_absent'}
    systemctl = shutil.which('systemctl')
    if not systemctl:
        return {'status': 'unknown', 'evidence': 'systemctl_absent'}
    state = _run([systemctl, 'is-active', 'fail2ban.service'])
    return {'status': 'active' if state == 'active' else 'unknown',
            'evidence': 'systemd_service_state' if state == 'active' else 'service_state_unreadable'}


def collect() -> dict:
    return {'updates': updates(), 'ssh': ssh(), 'secure_boot': secure_boot(), 'fail2ban': fail2ban()}
