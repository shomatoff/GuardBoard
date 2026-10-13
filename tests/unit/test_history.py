from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient
from backend.main import create_app, TOKEN
from backend.storage.history import HistoryStore, RETENTION_SECONDS


def readings(value):
    return {'cpu': {'value': value}, 'memory': {'value': value}, 'disk': {'value': value}}


def test_write_interval_window_and_retention():
    with TemporaryDirectory() as tmp:
        store = HistoryStore(Path(tmp) / 'history.sqlite')
        now = 2_000_000_000.0
        assert store.record(readings(20), now=now - RETENTION_SECONDS - 20)
        assert store.record(readings(30), now=now - 60)
        assert not store.record(readings(99), now=now - 59)
        assert store.record(readings(40), now=now)
        assert [row['cpu'] for row in store.query(3600, now)] == [30, 40]
        with pytest.raises(ValueError):
            store.query(42, now)


def test_history_api_authenticated_and_demo_isolated():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / 'real.sqlite'
        with TestClient(create_app(False, path), base_url='http://127.0.0.1:8765') as client:
            assert client.get('/api/history').status_code == 401
            client.get('/?key=' + TOKEN)
            client.get('/api/telemetry')
            body = client.get('/api/history?window=1h').json()
            assert body['mode'] == 'real' and body['samples']
            assert client.get('/api/history?window=bad').status_code == 422
        with TestClient(create_app(True, path), base_url='http://127.0.0.1:8765') as client:
            client.get('/?key=' + TOKEN)
            assert client.get('/api/history').json()['samples'] == []
