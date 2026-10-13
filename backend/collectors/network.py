"""Read-only network state and traffic rates."""
from __future__ import annotations

import ipaddress
import socket
import threading
import time
from pathlib import Path
from typing import Any

import psutil


class NetworkSampler:
    def __init__(self):
        self._previous: dict[str, tuple[int, int, float]] = {}
        self._lock = threading.Lock()

    def sample(self, now: float | None = None) -> dict[str, Any]:
        timestamp = time.monotonic() if now is None else now
        counters = psutil.net_io_counters(pernic=True)
        addresses = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        interfaces = []
        current = {}
        with self._lock:
            for name, counter in counters.items():
                old = self._previous.get(name)
                current[name] = (counter.bytes_recv, counter.bytes_sent, timestamp)
                download = upload = None
                if old and timestamp > old[2]:
                    seconds = timestamp - old[2]
                    download = max(0.0, (counter.bytes_recv - old[0]) / seconds)
                    upload = max(0.0, (counter.bytes_sent - old[1]) / seconds)
                ips = [address.address for address in addresses.get(name, [])
                       if address.family in (socket.AF_INET, socket.AF_INET6)]
                interface_stats = stats.get(name)
                interfaces.append({
                    'name': name, 'up': interface_stats.isup if interface_stats else None,
                    'speed_mbps': interface_stats.speed if interface_stats and interface_stats.speed > 0 else None,
                    'addresses': ips, 'received_bytes': counter.bytes_recv,
                    'sent_bytes': counter.bytes_sent,
                    'download_bytes_per_second': download,
                    'upload_bytes_per_second': upload,
                })
            self._previous = current
        return {'interfaces': interfaces, 'sampled_at': time.time()}


def parse_default_gateway(route_text: str) -> str | None:
    for line in route_text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4 or parts[1] != '00000000':
            continue
        try:
            if not int(parts[3], 16) & 2:
                continue
            address = bytes.fromhex(parts[2])[::-1]
            return str(ipaddress.IPv4Address(address))
        except (ValueError, ipaddress.AddressValueError):
            continue
    return None


def dns_servers() -> list[str]:
    try:
        content = Path('/etc/resolv.conf').read_text()
    except OSError:
        return []
    result = []
    for line in content.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == 'nameserver':
            try:
                result.append(str(ipaddress.ip_address(parts[1].split('%')[0])))
            except ValueError:
                pass
    return result


def connections() -> dict[str, Any]:
    try:
        observed = psutil.net_connections(kind='inet')
    except (OSError, psutil.AccessDenied):
        return {'available': False, 'reason': 'permission denied', 'active': [], 'listening': []}
    active = []
    listening = []
    for conn in observed:
        local = f'{conn.laddr.ip}:{conn.laddr.port}' if conn.laddr else None
        remote = f'{conn.raddr.ip}:{conn.raddr.port}' if conn.raddr else None
        row = {'local': local, 'remote': remote, 'status': conn.status, 'pid': conn.pid}
        if conn.status == psutil.CONN_LISTEN:
            listening.append(row)
        elif remote:
            active.append(row)
        if len(active) >= 200 and len(listening) >= 200:
            break
    return {'available': True, 'reason': None, 'active': active[:200], 'listening': listening[:200]}


def snapshot(sampler: NetworkSampler) -> dict[str, Any]:
    try:
        route = Path('/proc/net/route').read_text()
        gateway = parse_default_gateway(route)
    except OSError:
        gateway = None
    return {'traffic': sampler.sample(), 'dns_servers': dns_servers(),
            'default_gateway': gateway, 'connections': connections()}
