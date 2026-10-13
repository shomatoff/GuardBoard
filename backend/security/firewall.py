"""Read-only firewall inventory with explicit unknown states."""
from __future__ import annotations

import re
import shutil
import subprocess

MAX_OUTPUT = 32768


def parse_ufw(output: str) -> dict:
    status_match = re.search(r'^Status:\s*(active|inactive)\s*$', output, re.MULTILINE | re.IGNORECASE)
    if not status_match:
        return {'state': 'unknown', 'defaults': None, 'rules': [], 'reason': 'firewall_parse_failed'}
    defaults_match = re.search(r'^Default:\s*(.+)$', output, re.MULTILINE)
    rules = []
    for line in output.splitlines():
        if re.search(r'\b(ALLOW|DENY|REJECT|LIMIT)\b', line) and not line.startswith('Default:'):
            rules.append(line.strip()[:300])
    return {'state': status_match.group(1).lower(), 'defaults': defaults_match.group(1)[:300] if defaults_match else None,
            'rules': rules[:100], 'reason': None}


def _run(args: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if len(result.stdout) > MAX_OUTPUT or len(result.stderr) > MAX_OUTPUT:
        return None
    return result


def collect() -> dict:
    """No privilege escalation: permission errors remain visible as unknown."""
    ufw = shutil.which('ufw')
    nft = shutil.which('nft')
    result = {'manager': None, 'state': 'unknown', 'defaults': None, 'rules': [],
              'reason': 'firewall_no_tool'}
    if ufw:
        response = _run([ufw, 'status', 'verbose'])
        if response and response.returncode == 0:
            parsed = parse_ufw(response.stdout)
            if parsed['state'] != 'unknown':
                return {'manager': 'ufw', **parsed}
        result.update(manager='ufw', reason='firewall_permission')
    if nft:
        response = _run([nft, '-j', 'list', 'ruleset'])
        if response and response.returncode == 0:
            # An empty ruleset does not prove whether another firewall manager is active.
            return {'manager': 'nftables', 'state': 'observed', 'defaults': None,
                    'rules': [], 'reason': 'firewall_policy_unassessed'}
        result['reason'] = 'firewall_permission' if ufw else 'firewall_nft_permission'
    return result
