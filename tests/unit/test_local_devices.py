import ipaddress
from fastapi.testclient import TestClient
from tempfile import TemporaryDirectory
from pathlib import Path
from backend.collectors.local_devices import parse_arp
from backend.main import CSRF, TOKEN, create_app


def test_arp_filter_current_subnet_only():
    data = 'IP address HW type Flags HW address Mask Device\n192.168.1.10 0x1 0x2 aa:bb:cc:dd:ee:ff * wlan0\n192.168.2.1 0x1 0x2 11:22:33:44:55:66 * wlan0\n192.168.1.20 0x1 0x0 00:00:00:00:00:00 * wlan0\n'
    result = parse_arp(data, ipaddress.IPv4Network('192.168.1.0/24'))
    assert result == [{'ip': '192.168.1.10', 'mac': 'aa:bb:cc:dd:ee:ff', 'interface': 'wlan0'}]


def test_inventory_requires_ownership_and_csrf(monkeypatch):
    calls = []
    monkeypatch.setattr('backend.main.passive_inventory', lambda: calls.append(1) or {'subnet': '192.168.1.0/24', 'devices': [], 'source': 'test'})
    with TemporaryDirectory() as tmp, TestClient(create_app(False, Path(tmp)/'history.sqlite', Path(tmp)/'rooms.sqlite', Path(tmp)/'devices.sqlite'), base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        assert client.post('/api/wifi/devices', json={'confirmed_ownership': True}).status_code == 403
        assert client.post('/api/wifi/devices', json={'confirmed_ownership': False}, headers={'x-csrf-token': CSRF}).status_code == 403
        assert calls == []
        assert client.post('/api/wifi/devices', json={'confirmed_ownership': True}, headers={'x-csrf-token': CSRF}).status_code == 200
        assert calls == [1]
