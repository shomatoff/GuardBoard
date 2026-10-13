from unittest.mock import patch
from subprocess import CompletedProcess

from backend.security.firewall import parse_ufw, collect


def test_ufw_parser_extracts_state_defaults_and_rules():
    report = parse_ufw('Status: active\nDefault: deny (incoming), allow (outgoing)\n22/tcp ALLOW IN Anywhere\n')
    assert report['state'] == 'active'
    assert 'deny (incoming)' in report['defaults']
    assert report['rules'] == ['22/tcp ALLOW IN Anywhere']
    assert parse_ufw('permission denied')['state'] == 'unknown'


def test_firewall_permission_denial_stays_unknown():
    denied = CompletedProcess(['ufw'], 1, '', 'need root')
    with patch('backend.security.firewall.shutil.which', side_effect=lambda binary: '/usr/sbin/' + binary), patch('backend.security.firewall._run', return_value=denied):
        report = collect()
    assert report['state'] == 'unknown'
    assert report['reason'] == 'firewall_permission'
