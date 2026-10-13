from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from backend.main import CSRF, TOKEN, create_app
from backend.storage.wifi_rooms import RoomStore


def test_relative_attenuation_and_local_storage():
    with TemporaryDirectory() as tmp:
        store = RoomStore(Path(tmp) / 'rooms.sqlite')
        store.add('Desk', -40)
        store.add('Kitchen', -60)
        rows = store.list()
        assert rows[0]['relative_attenuation_db'] == 0
        assert rows[1]['relative_attenuation_db'] == 20


def test_room_api_requires_csrf_and_valid_name(monkeypatch):
    with TemporaryDirectory() as tmp:
        with TestClient(create_app(False, Path(tmp)/'history.sqlite', Path(tmp)/'rooms.sqlite'), base_url='http://127.0.0.1:8765') as client:
            client.get('/?key=' + TOKEN)
            monkeypatch.setattr('backend.main.wifi_adapter', lambda: {'rssi_dbm': -55})
            assert client.post('/api/wifi/rooms', json={'room': 'Office'}).status_code == 403
            assert client.post('/api/wifi/rooms', json={'room': 'bad\nname'}, headers={'x-csrf-token': CSRF}).status_code == 422
            result = client.post('/api/wifi/rooms', json={'room': 'Office'}, headers={'x-csrf-token': CSRF})
            assert result.json()['samples'][0]['rssi_dbm'] == -55
