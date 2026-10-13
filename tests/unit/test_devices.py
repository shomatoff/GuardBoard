from pathlib import Path
from tempfile import TemporaryDirectory
from backend.storage.devices import DeviceStore


def test_new_known_and_trusted_states():
    with TemporaryDirectory() as tmp:
        store = DeviceStore(Path(tmp) / 'devices.sqlite')
        device = {'ip': '192.168.1.2', 'mac': 'aa:bb:cc:dd:ee:ff', 'interface': 'wlan0'}
        first = store.observe([device])[0]
        assert first['newly_observed'] and not first['trusted']
        assert store.set_trusted(device['mac'], True)
        second = store.observe([device])[0]
        assert not second['newly_observed'] and second['trusted']
        assert second['first_seen'] == first['first_seen']
