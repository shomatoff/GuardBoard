from subprocess import CompletedProcess
from unittest.mock import patch

from backend.collectors.privacy import split_nmcli, parse_active_connections, collect


def test_nmcli_vpn_parser_handles_escaped_names():
    assert split_nmcli(r'vpn:Work\:VPN:tun0') == ['vpn', 'Work:VPN', 'tun0']
    report = parse_active_connections('wifi:Home:wlp1s0\nvpn:Work\\:VPN:tun0\nwireguard:wg-home:wg0')
    assert report['state'] == 'connected'
    assert len(report['connections']) == 2
    assert report['connections'][0]['name'] == 'Work:VPN'


def test_privacy_unknown_when_nmcli_fails():
    with patch('backend.collectors.privacy.shutil.which', return_value='/usr/bin/nmcli'), patch('backend.collectors.privacy.subprocess.run', return_value=CompletedProcess([], 1, '', 'error')):
        report = collect()
    assert report['vpn']['state'] == 'unknown'
    assert report['dns_leak_test'] == 'not_run'
    assert report['public_ip'] is None
