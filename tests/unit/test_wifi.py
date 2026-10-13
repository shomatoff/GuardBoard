from backend.collectors.wifi import parse_link, parse_networks, split_nmcli


def test_nmcli_escaping_and_network_parser():
    line = r'*:Home\:Lab:AA\:BB\:CC\:DD\:EE\:FF:11:2462 MHz:78:WPA2 WPA3'
    network = parse_networks(line)[0]
    assert network['ssid'] == 'Home:Lab'
    assert network['bssid'] == 'AA:BB:CC:DD:EE:FF'
    assert network['band'] == '2.4 GHz'
    assert not network['open']
    assert split_nmcli(r'a\:b:c') == ['a:b', 'c']


def test_link_parser_does_not_invent_signal():
    assert parse_link('Not connected.')['rssi_dbm'] is None
    assert parse_link('Connected to 00:11:22:33:44:55\n signal: -65 dBm\n tx bitrate: 72.2 MBit/s')['tx_mbps'] == 72.2


def test_scan_endpoint_requires_csrf_and_get_never_scans(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import CSRF, TOKEN, create_app
    calls = []
    with TestClient(create_app(False), base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        app = client.app
        monkeypatch.setattr(app.state.wifi, 'cached', lambda: {'adapter': None, 'networks': [], 'reason': None})
        monkeypatch.setattr(app.state.wifi, 'scan', lambda: calls.append(1) or {'adapter': None, 'networks': [], 'reason': None})
        assert client.get('/api/wifi').status_code == 200
        assert calls == []
        assert client.post('/api/wifi/scan').status_code == 403
        assert calls == []
        assert client.post('/api/wifi/scan', headers={'x-csrf-token': CSRF}).status_code == 200
        assert calls == [1]


def test_phy_parser_excludes_disabled_6ghz():
    from backend.collectors.wifi import parse_phy
    info = 'HT Capabilities\nVHT Capabilities\nHE Iftypes: managed\n* 2412.0 MHz\n* 5180.0 MHz\n* 5955.0 MHz (disabled)'
    result = parse_phy(info)
    assert result['wifi4'] and result['wifi5'] and result['wifi6']
    assert not result['wifi6e'] and not result['wifi7']
    assert result['bands'] == ['2.4 GHz', '5 GHz']
