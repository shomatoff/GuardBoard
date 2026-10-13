from fastapi.testclient import TestClient
from backend.main import CSRF, TOKEN, create_app


def test_public_ip_requires_auth_csrf_and_explicit_post(monkeypatch):
    calls = []
    monkeypatch.setattr('backend.main.public_ip', lambda: calls.append(1) or '203.0.113.7')
    with TestClient(create_app(False), base_url='http://127.0.0.1:8765') as client:
        assert client.get('/api/network/public-ip').status_code == 401
        assert client.post('/api/network/public-ip').status_code == 401
        client.get('/?key=' + TOKEN)
        assert client.get('/api/network/public-ip').status_code == 405
        assert client.post('/api/network/public-ip').status_code == 403
        assert calls == []
        response = client.post('/api/network/public-ip', headers={'x-csrf-token': CSRF})
        assert response.status_code == 200
        assert response.json()['ip'] == '203.0.113.7'
        assert calls == [1]


def test_download_sample_requires_explicit_authorized_post(monkeypatch):
    calls = []
    monkeypatch.setattr('backend.main.download_sample', lambda: calls.append(1) or {'download_mbps': 12.5, 'bytes_downloaded': 5_000_000, 'seconds': 3.2})
    with TestClient(create_app(False), base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        assert client.get('/api/network/download-sample').status_code == 405
        assert client.post('/api/network/download-sample').status_code == 403
        assert calls == []
        result = client.post('/api/network/download-sample', headers={'x-csrf-token': CSRF})
        assert result.json()['result']['bytes_downloaded'] == 5_000_000
        assert calls == [1]


def test_latency_sample_never_runs_without_consent_post(monkeypatch):
    calls = []
    monkeypatch.setattr('backend.main.tcp_latency_sample', lambda: calls.append(1) or {'target': '1.1.1.1:443', 'mean_ms': 10.0, 'jitter_ms': 1.0, 'failed_probes': 0, 'total_probes': 5})
    with TestClient(create_app(False), base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        assert client.get('/api/network/latency-sample').status_code == 405
        assert client.post('/api/network/latency-sample').status_code == 403
        assert calls == []
        result = client.post('/api/network/latency-sample', headers={'x-csrf-token': CSRF})
        assert result.json()['result']['total_probes'] == 5
        assert calls == [1]
