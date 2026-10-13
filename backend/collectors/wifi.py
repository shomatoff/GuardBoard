"""Normal Wi-Fi link diagnostics and rate-limited NetworkManager scans."""
from __future__ import annotations

import re
from functools import lru_cache
import subprocess
import threading
import time
from pathlib import Path

SCAN_INTERVAL = 30.0


def run(args: list[str], timeout: int = 5, limit: int = 65536) -> str:
    result = subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    if result.returncode != 0:
        raise OSError(result.stderr[:500].decode('utf-8', 'replace').strip() or 'command failed')
    return result.stdout[:limit].decode('utf-8', 'replace')


def split_nmcli(line: str) -> list[str]:
    result = []
    current = []
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            result.append(''.join(current))
            current = []
        else:
            current.append(char)
    result.append(''.join(current))
    return result


def parse_networks(content: str) -> list[dict]:
    networks = []
    for line in content.splitlines():
        parts = split_nmcli(line)
        if len(parts) != 7:
            continue
        in_use, ssid, bssid, channel, frequency, signal, security = parts
        match = re.search(r'(\d+)', frequency)
        try:
            mhz = int(match.group(1)) if match else None
            value = int(signal)
            ch = int(channel)
        except ValueError:
            continue
        band = '6 GHz' if mhz and mhz >= 5925 else '5 GHz' if mhz and mhz >= 4900 else '2.4 GHz'
        networks.append({'in_use': in_use == '*', 'ssid': ssid or None,
                         'bssid': bssid, 'channel': ch, 'frequency_mhz': mhz,
                         'band': band, 'signal_percent': max(0, min(100, value)),
                         'security': security or None, 'open': not security or security == '--'})
    return networks[:200]


def parse_link(content: str) -> dict:
    signal = re.search(r'signal:\s*(-?\d+)\s*dBm', content)
    tx = re.search(r'tx bitrate:\s*([\d.]+)\s*MBit/s', content)
    return {'connected': 'Connected to ' in content, 'rssi_dbm': int(signal.group(1)) if signal else None,
            'tx_mbps': float(tx.group(1)) if tx else None}


def parse_phy(content: str) -> dict:
    enabled_frequencies = []
    for line in content.splitlines():
        match = re.search(r'\*\s+(\d+(?:\.\d+)?) MHz', line)
        if match and '(disabled)' not in line:
            enabled_frequencies.append(float(match.group(1)))
    return {
        'wifi4': 'HT Capabilities' in content or 'HT20' in content,
        'wifi5': 'VHT Capabilities' in content,
        'wifi6': 'HE Iftypes' in content,
        'wifi6e': 'HE Iftypes' in content and any(freq >= 5925 for freq in enabled_frequencies),
        'wifi7': 'EHT Iftypes' in content,
        'bands': [band for band, pred in [('2.4 GHz', lambda x: 2400 <= x < 2500),
                                          ('5 GHz', lambda x: 4900 <= x < 5925),
                                          ('6 GHz', lambda x: x >= 5925)]
                  if any(pred(freq) for freq in enabled_frequencies)],
    }


@lru_cache(maxsize=8)
def phy_capabilities(phy_name: str) -> dict:
    return parse_phy(run(['iw', 'phy', phy_name, 'info'], limit=131072))


def adapter() -> dict | None:
    try:
        output = run(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'dev', 'status'])
    except OSError:
        return None
    for line in output.splitlines():
        parts = split_nmcli(line)
        if len(parts) < 3 or parts[1] != 'wifi' or parts[2] != 'connected':
            continue
        name = parts[0]
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,32}', name):
            continue
        path = Path('/sys/class/net') / name / 'device'
        try:
            driver = (path / 'driver').resolve().name
        except OSError:
            driver = None
        try:
            link = parse_link(run(['iw', 'dev', name, 'link']))
        except OSError:
            link = {'connected': True, 'rssi_dbm': None, 'tx_mbps': None}
        phy_path = Path('/sys/class/net') / name / 'phy80211'
        try:
            phy_name = phy_path.resolve().name
            standards = phy_capabilities(phy_name)
        except OSError:
            standards = None
        try:
            regulatory = re.search(r'country ([A-Z]{2}):', run(['iw', 'reg', 'get']))
            country = regulatory.group(1) if regulatory else None
        except OSError:
            country = None
        try:
            pci_address = path.resolve().name
            chipset = run(['lspci', '-s', pci_address], limit=500).strip().split(': ', 1)[-1]
        except OSError:
            chipset = None
        return {'name': name, 'driver': driver, 'chipset': chipset,
                'standards': standards, 'regulatory_country': country, **link}
    return None


class WifiScanner:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_scan = 0.0

    def cached(self) -> dict:
        current = adapter()
        if not current:
            return {'adapter': None, 'networks': [], 'reason': 'No connected Wi-Fi adapter'}
        try:
            output = run(['nmcli', '-t', '-f', 'IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY',
                          'dev', 'wifi', 'list', 'ifname', current['name'], '--rescan', 'no'])
            networks = parse_networks(output)
        except OSError:
            networks = []
        return {'adapter': current, 'networks': networks, 'reason': None}

    def scan(self) -> dict:
        current = adapter()
        if not current:
            raise ValueError('No connected Wi-Fi adapter')
        with self._lock:
            now = time.monotonic()
            if now - self._last_scan < SCAN_INTERVAL:
                raise ValueError('Scan rate limit')
            self._last_scan = now
        run(['nmcli', 'dev', 'wifi', 'rescan', 'ifname', current['name']], timeout=15)
        return self.cached()
