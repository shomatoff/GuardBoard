from unittest.mock import patch
from backend.security.hardening import ssh, secure_boot


def test_effective_ssh_config_parser():
    with patch('backend.security.hardening.shutil.which', return_value='/usr/sbin/sshd'), patch('backend.security.hardening._run', return_value='permitrootlogin no\npasswordauthentication no\n'):
        result = ssh()
    assert result['status'] == 'observed'
    assert result['permit_root_login'] == 'no'
    assert result['password_authentication'] == 'no'


def test_secure_boot_unknown_without_evidence():
    with patch('backend.security.hardening.shutil.which', return_value=None):
        assert secure_boot()['status'] == 'unknown'
