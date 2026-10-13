from pathlib import Path
from unittest.mock import patch
from backend.actions.av_scan import ScanManager, command_for
from fastapi.testclient import TestClient
from backend.main import CSRF, TOKEN, create_app
from backend.actions.av_scan import ScanJob


def test_command_is_allowlisted_and_non_destructive(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'source.py').write_text('print(1)')
    with patch('backend.actions.av_scan.shutil.which', return_value='/usr/bin/clamscan'), patch('backend.actions.av_scan.Path.glob', return_value=[Path('/var/lib/clamav/daily.cvd')]):
        command = command_for(project)
    assert command[0] == '/usr/bin/clamscan'
    assert '--follow-dir-symlinks=0' in command
    assert '--follow-file-symlinks=0' in command
    assert not any(arg.startswith(('--remove', '--move', '--copy')) for arg in command)
    assert command[-1] == str(project / 'source.py')


def test_scan_refuses_oversized_or_symlink_only_project(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'link').symlink_to(tmp_path)
    with patch('backend.actions.av_scan.shutil.which', return_value='/usr/bin/clamscan'), patch('backend.actions.av_scan.Path.glob', return_value=[Path('/var/lib/clamav/daily.cvd')]):
        try:
            command_for(project)
            assert False, 'Expected empty project rejection'
        except ValueError as exc:
            assert 'No regular files' in str(exc)
        (project / 'large.bin').write_bytes(b'0' * (10 * 1024 * 1024 + 1))
        try:
            command_for(project)
            assert False, 'Expected size rejection'
        except ValueError as exc:
            assert 'safe scan limits' in str(exc)


def test_scan_manager_starts_empty():
    assert ScanManager().jobs == {}


def test_av_api_requires_confirmation_csrf_and_supports_cancel(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    project.mkdir()
    (project / 'source.py').write_text('print(1)')
    monkeypatch.setattr('backend.main.psutil.sensors_battery', lambda: None)
    monkeypatch.setattr('backend.main.psutil.cpu_percent', lambda interval: 1.0)
    app = create_app(False, tmp_path/'history.sqlite', tmp_path/'rooms.sqlite', tmp_path/'devices.sqlite', tmp_path/'integrity.sqlite', tmp_path)
    job = ScanJob(id='test-job', project=str(project), status='running')
    app.state.av.jobs[job.id] = job

    async def fake_start(path):
        assert path == project
        return job

    async def fake_cancel(job_id):
        assert job_id == job.id
        job.status = 'cancelled'
        return job

    monkeypatch.setattr(app.state.av, 'start', fake_start)
    monkeypatch.setattr(app.state.av, 'cancel', fake_cancel)
    with TestClient(app, base_url='http://127.0.0.1:8765') as client:
        payload = {'path': str(project), 'confirmed': True}
        assert client.post('/api/av/scans', json=payload).status_code == 401
        client.get('/?key=' + TOKEN)
        assert client.post('/api/av/scans', json=payload).status_code == 403
        assert client.post('/api/av/scans', json={**payload, 'confirmed': False}, headers={'x-csrf-token': CSRF}).status_code == 403
        assert client.post('/api/av/scans', json=payload, headers={'x-csrf-token': CSRF}).json()['status'] == 'running'
        assert client.get('/api/av/scans/test-job').json()['status'] == 'running'
        assert client.post('/api/av/scans/test-job/cancel').status_code == 403
        assert client.post('/api/av/scans/test-job/cancel', headers={'x-csrf-token': CSRF}).json()['status'] == 'cancelled'
        assert client.get('/api/av/scans/unknown').status_code == 404
