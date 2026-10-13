from unittest.mock import patch
from backend.collectors.optimizer import collect


def test_optimizer_read_only_unknowns_are_not_invented():
    with patch('backend.collectors.optimizer.shutil.which', return_value=None), patch('backend.collectors.optimizer._read', return_value=None), patch('backend.collectors.optimizer.psutil.sensors_battery', return_value=None):
        report = collect()
    assert report['power_profile'] is None
    assert report['cpu_governor'] is None
    assert report['battery_percent'] is None
    assert report['benchmark'] is None
    assert report['changes_applied'] is False
