from backend.security.secrets import scan
from fastapi.testclient import TestClient
from backend.main import CSRF, TOKEN, create_app


def test_secret_indicators_redact_values_and_skip_symlinks(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    secret = 'AKIAABCDEFGHIJKLMNOP'
    (project / '.env').write_text('API_KEY="super-secret-value"\n')
    (project / 'code.py').write_text(f'key = "{secret}"\n')
    (project / 'outside').symlink_to(tmp_path)
    report = scan(project)
    assert report['checked_files'] == 2
    assert {finding['kind'] for finding in report['findings']} == {'env_file', 'credential_assignment', 'aws_access_key'}
    assert secret not in str(report)
    assert 'super-secret-value' not in str(report)


def test_secret_api_is_confirmed_and_redacted(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    project.mkdir()
    value = 'super-secret-value'
    (project / '.env').write_text('API_KEY=' + value)
    monkeypatch.setattr('backend.main.psutil.sensors_battery', lambda: None)
    monkeypatch.setattr('backend.main.psutil.cpu_percent', lambda interval: 1.0)
    app = create_app(False, tmp_path/'history.sqlite', tmp_path/'rooms.sqlite', tmp_path/'devices.sqlite', tmp_path/'integrity.sqlite', tmp_path)
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        payload = {'path': str(project), 'confirmed': True}
        assert client.post('/api/projects/secrets', json=payload).status_code == 403
        assert client.post('/api/projects/secrets', json={**payload, 'confirmed': False}, headers={'x-csrf-token': CSRF}).status_code == 403
        response = client.post('/api/projects/secrets', json=payload, headers={'x-csrf-token': CSRF})
        assert response.status_code == 200
        assert value not in response.text
        assert response.json()['result']['checked_files'] == 1
