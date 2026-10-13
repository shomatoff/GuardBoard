import pytest
from backend.storage.config import ConfigStore, DEFAULT_THRESHOLDS
from fastapi.testclient import TestClient
from backend.main import CSRF, TOKEN, create_app


def test_config_toml_roundtrip_and_validation(tmp_path):
    store = ConfigStore(tmp_path / 'config.toml')
    assert store.read() == DEFAULT_THRESHOLDS
    values = {**DEFAULT_THRESHOLDS, 'memory': 85.0}
    assert store.write(values) == values
    assert store.read() == values
    assert oct(store.path.stat().st_mode & 0o777) == '0o600'
    with pytest.raises(ValueError):
        store.write({**values, 'disk': 200})
    assert store.read() == values


def test_settings_api_requires_confirmation_and_csrf(tmp_path):
    app = create_app(False, tmp_path/'history.sqlite', tmp_path/'rooms.sqlite', tmp_path/'devices.sqlite', tmp_path/'integrity.sqlite', tmp_path)
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        assert client.get('/api/settings').json()['alert_thresholds'] == DEFAULT_THRESHOLDS
        values = {**DEFAULT_THRESHOLDS, 'memory': 88.0}
        payload = {'thresholds': values, 'confirmed': True}
        assert client.post('/api/settings/alerts', json=payload).status_code == 403
        assert client.post('/api/settings/alerts', json={**payload, 'confirmed': False}, headers={'x-csrf-token': CSRF}).status_code == 403
        assert client.post('/api/settings/alerts', json=payload, headers={'x-csrf-token': CSRF}).status_code == 200
        assert client.get('/api/settings').json()['alert_thresholds']['memory'] == 88.0
        assert client.post('/api/settings/alerts', json={**payload, 'thresholds': {**values, 'memory': 120}}, headers={'x-csrf-token': CSRF}).status_code == 422


def test_bad_config_does_not_stop_app(tmp_path):
    (tmp_path/'config.toml').write_text('[alerts]\nmemory = "bad"')
    app = create_app(False, tmp_path/'history.sqlite', tmp_path/'rooms.sqlite', tmp_path/'devices.sqlite', tmp_path/'integrity.sqlite', tmp_path)
    assert app.state.config_error == 'config_invalid'
    assert app.state.alerts.thresholds == DEFAULT_THRESHOLDS
