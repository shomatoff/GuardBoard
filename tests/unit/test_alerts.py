from backend.storage.alerts import AlertStore


def test_alerts_use_actual_values_and_deduplicate(tmp_path):
    store = AlertStore(tmp_path / 'alerts.sqlite')
    values = {'cpu_temperature': {'value': 92.0}, 'memory': {'value': 94.0},
              'disk': {'value': None}, 'battery': {'value': {'percent': 8, 'plugged': True}}}
    assert store.observe(values, now=1000) == 2
    assert store.observe(values, now=1010) == 0
    assert store.observe(values, now=1301) == 2
    recent = store.recent(now=1301)
    assert len(recent) == 4
    assert {event['kind'] for event in recent} == {'cpu_temperature', 'memory'}
    assert all(event['value'] in (92.0, 94.0) for event in recent)


def test_low_battery_only_when_unplugged_and_unknowns_ignored(tmp_path):
    store = AlertStore(tmp_path / 'alerts.sqlite')
    assert store.observe({'battery': {'value': {'percent': 10, 'plugged': False}}, 'gpu_temperature': {'value': None}}, now=1000) == 1
    assert store.recent(now=1000)[0]['kind'] == 'battery'
