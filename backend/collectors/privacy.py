"""Read-only local DNS and NetworkManager VPN evidence."""
from __future__ import annotations

import shutil
import subprocess

from backend.collectors.network import dns_servers


def split_nmcli(line: str) -> list[str]:
    fields, current, escaped = [], [], False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            fields.append(''.join(current))
            current = []
        else:
            current.append(char)
    fields.append(''.join(current))
    return fields


def parse_active_connections(output: str) -> dict:
    vpns = []
    for line in output.splitlines():
        parts = split_nmcli(line)
        if len(parts) < 3:
            continue
        kind, name, device = parts[:3]
        if kind.lower() in {'vpn', 'wireguard'}:
            vpns.append({'type': kind.lower(), 'name': name[:100], 'device': device[:40]})
    return {'state': 'connected' if vpns else 'no_nm_vpn', 'connections': vpns, 'reason': None}


def collect() -> dict:
    result = {'dns_servers': dns_servers(), 'dns_leak_test': 'not_run',
              'public_ip': None, 'vpn': {'state': 'unknown', 'connections': [], 'reason': 'nmcli_unavailable'}}
    nmcli = shutil.which('nmcli')
    if not nmcli:
        return result
    try:
        response = subprocess.run([nmcli, '-t', '-f', 'TYPE,NAME,DEVICE', 'connection', 'show', '--active'],
                                  capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        result['vpn']['reason'] = 'nmcli_failed'
        return result
    if response.returncode != 0 or len(response.stdout) > 16384:
        result['vpn']['reason'] = 'nmcli_failed'
        return result
    result['vpn'] = parse_active_connections(response.stdout)
    return result
