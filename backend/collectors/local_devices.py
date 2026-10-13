"""Passive ARP inventory limited to the current connected Wi-Fi subnet."""
from __future__ import annotations

import ipaddress
import re
from pathlib import Path

import psutil

from backend.collectors.wifi import adapter

MAC = re.compile(r'^(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$')


def current_subnet() -> ipaddress.IPv4Network | None:
    current = adapter()
    if not current:
        return None
    for address in psutil.net_if_addrs().get(current['name'], []):
        if address.family != 2 or not address.netmask:
            continue
        try:
            return ipaddress.IPv4Interface(f'{address.address}/{address.netmask}').network
        except ValueError:
            continue
    return None


def parse_arp(content: str, subnet: ipaddress.IPv4Network) -> list[dict]:
    devices = []
    for line in content.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6:
            continue
        try:
            address = ipaddress.IPv4Address(parts[0])
            flags = int(parts[2], 16)
        except ValueError:
            continue
        if address not in subnet or not flags & 2 or not MAC.fullmatch(parts[3]):
            continue
        devices.append({'ip': str(address), 'mac': parts[3].lower(), 'interface': parts[5]})
    return devices[:254]


def passive_inventory() -> dict:
    subnet = current_subnet()
    if subnet is None or subnet.num_addresses > 256:
        raise ValueError('Current Wi-Fi subnet unavailable or too large')
    try:
        content = Path('/proc/net/arp').read_text()
    except OSError as exc:
        raise ValueError('ARP cache unavailable') from exc
    return {'subnet': str(subnet), 'devices': parse_arp(content, subnet),
            'source': 'passive ARP cache; no discovery packets sent'}
