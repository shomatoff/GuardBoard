from backend.collectors.system import collect, safe


def test_independent_sensor_failure():
    def broken():
        raise OSError('missing')
    assert safe(broken) == {'value': None, 'available': False, 'reason': 'OSError'}
    assert safe(lambda: 42)['value'] == 42


def test_real_collector_shape():
    data = collect()
    assert {'cpu', 'memory', 'disk', 'gpu', 'battery'} <= data.keys()
    for item in data.values():
        assert {'value', 'available', 'reason'} <= item.keys()


def test_battery_health_only_from_sensor(monkeypatch, tmp_path):
    from backend.collectors import system
    battery_dir = tmp_path / 'BAT0'
    battery_dir.mkdir()
    (battery_dir / 'charge_full').write_text('80')
    (battery_dir / 'charge_full_design').write_text('100')
    class FakeBattery:
        percent = 65
        power_plugged = False
        secsleft = -1
    monkeypatch.setattr(system.psutil, 'sensors_battery', lambda: FakeBattery())
    original_path = system.Path
    monkeypatch.setattr(system, 'Path', lambda value: tmp_path if value == '/sys/class/power_supply' else original_path(value))
    result = system.battery()
    assert result['health_percent'] == 80.0
    assert result['seconds_left'] is None
    assert result['unplugged_seconds'] is None


def test_disk_rate_requires_two_samples(monkeypatch):
    from collections import namedtuple
    from backend.collectors import system
    IO = namedtuple('IO', 'read_bytes write_bytes')
    values = iter([IO(100, 200), IO(300, 500)])
    times = iter([10.0, 12.0])
    monkeypatch.setattr(system.psutil, 'disk_io_counters', lambda: next(values))
    monkeypatch.setattr(system.time, 'monotonic', lambda: next(times))
    sampler = system.DiskRateSampler()
    assert sampler.sample() is None
    assert sampler.sample() == {'read_bytes_per_second': 100.0, 'write_bytes_per_second': 150.0}
