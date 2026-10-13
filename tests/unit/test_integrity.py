from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from backend.security.integrity import IntegrityStore, validate_project
from backend.security.integrity import hash_files


def test_integrity_new_modified_deleted_and_symlink_skip():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        project = root / 'project';project.mkdir()
        (project / 'a.txt').write_text('one')
        (project / 'b.txt').write_text('two')
        (project / 'outside').symlink_to(root)
        store = IntegrityStore(root / 'baseline.sqlite')
        assert store.baseline(project) == 2
        (project / 'a.txt').write_text('changed')
        (project / 'b.txt').unlink()
        (project / 'c.txt').write_text('new')
        result = store.compare(project)
        assert result['modified'] == ['a.txt']
        assert result['deleted'] == ['b.txt']
        assert result['new'] == ['c.txt']
        assert validate_project(str(project), root) == project
        with pytest.raises(ValueError):
            validate_project(str(root), root)


def test_directory_count_is_bounded(tmp_path, monkeypatch):
    import backend.security.integrity as integrity
    monkeypatch.setattr(integrity, 'MAX_DIRS', 1)
    project = tmp_path / 'project'
    (project / 'nested').mkdir(parents=True)
    with pytest.raises(ValueError, match='directory limit'):
        hash_files(project)


def test_project_api_confirmation_and_diff(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import CSRF, TOKEN, create_app
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        project = root / 'project';project.mkdir()
        (project / 'file.txt').write_text('before')
        monkeypatch.setattr('backend.main.psutil.sensors_battery', lambda: None)
        monkeypatch.setattr('backend.main.psutil.cpu_percent', lambda interval: 1.0)
        app = create_app(False, root/'history.sqlite', root/'rooms.sqlite', root/'devices.sqlite', root/'integrity.sqlite', root)
        with TestClient(app, base_url='http://127.0.0.1:8765') as client:
            client.get('/?key=' + TOKEN)
            payload = {'path': str(project), 'confirmed': True}
            assert client.post('/api/projects/baseline', json=payload).status_code == 403
            assert client.post('/api/projects/baseline', json={**payload, 'confirmed': False}, headers={'x-csrf-token': CSRF}).status_code == 403
            assert client.post('/api/projects/baseline', json=payload, headers={'x-csrf-token': CSRF}).json()['files'] == 1
            (project / 'file.txt').write_text('after')
            result = client.post('/api/projects/check', json=payload, headers={'x-csrf-token': CSRF}).json()['result']
            assert result['modified'] == ['file.txt']
