from backend.collectors.capabilities import collect, package_state
from fastapi.testclient import TestClient
from backend.main import TOKEN, create_app


def test_capability_schema():
    tools = collect()
    assert 'clamav' in tools and 'smart' in tools
    for entry in tools.values():
        assert isinstance(entry['available'], bool)
        assert isinstance(entry['package_state'], str)
        assert isinstance(entry['binary'], str)


def test_unknown_package_not_ready():
    assert package_state('guardboard-does-not-exist-xyz') == 'not installed'


def test_demo_capabilities_do_not_read_host_tools(monkeypatch):
    def fail():
        raise AssertionError('Real tool inventory must not run in demo')
    monkeypatch.setattr('backend.main.collect_capabilities', fail)
    with TestClient(create_app(True), base_url='http://127.0.0.1:8765') as client:
        client.get('/?key=' + TOKEN)
        result = client.get('/api/capabilities').json()
        assert result['mode'] == 'demo'
        assert all(item['package_state'] == 'demo_sample' for item in result['tools'].values())
