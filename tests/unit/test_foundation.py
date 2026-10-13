from fastapi.testclient import TestClient
from backend.main import create_app, TOKEN


def test_session_and_host_controls():
    with TestClient(create_app(True), base_url="http://127.0.0.1:8765") as c:
        assert c.get('/api/bootstrap').status_code == 401
        assert c.get('/').status_code == 401
        assert c.get('/?key=' + TOKEN).status_code == 200
        assert c.get('/api/bootstrap').json()['demo'] is True
        assert c.get('/api/telemetry').json()['mode'] == 'demo'
        assert c.get('/api/telemetry').json()['cpu'] == 18.5
        assert c.get('/api/telemetry', headers={'host': 'evil.example'}).status_code == 403
        assert c.get('/api/telemetry', headers={'origin': 'http://evil.example'}).status_code == 403
        assert c.post('/api/telemetry').status_code == 403


def test_real_mode_never_uses_demo_data():
    with TestClient(create_app(False), base_url="http://127.0.0.1:8765") as c:
        c.get('/?key=' + TOKEN)
        body = c.get('/api/telemetry').json()
        assert body['mode'] == 'real'
        assert body.get('source') != 'deterministic demo'


def test_websocket_origin():
    with TestClient(create_app(True), base_url="http://127.0.0.1:8765") as c:
        c.get('/?key=' + TOKEN)
        with c.websocket_connect('/ws', headers={'origin': 'http://127.0.0.1:8765', 'host': '127.0.0.1:8765', 'cookie': 'gb_session=' + TOKEN}) as ws:
            assert ws.receive_json()['status'] == 'connected'
