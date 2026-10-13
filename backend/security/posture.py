"""Evidence-aware, read-only defensive posture checks."""
from __future__ import annotations

from pathlib import Path

from backend.collectors.capabilities import collect as collect_tools

WEIGHTS = {
    'firewall': 20,
    'antivirus': 15,
    'updates': 15,
    'networkExposure': 15,
    'privacy': 10,
    'projectProtection': 10,
    'hardening': 15,
}


def check() -> dict:
    """Never returns a healthy total while any category lacks evidence."""
    tools = collect_tools()
    categories = {
        key: {'status': 'unknown', 'score': None, 'weight': weight, 'evidence': 'not assessed'}
        for key, weight in WEIGHTS.items()
    }
    # Firewall state requires privileged rule inspection; binary presence is insufficient.
    categories['firewall']['evidence'] = 'rules require privileged inspection'
    categories['antivirus']['evidence'] = 'ClamAV engine or signatures unavailable'
    signatures = sorted(Path('/var/lib/clamav').glob('*.cvd'))
    if tools['clamav']['available'] and signatures:
        categories['antivirus'].update(
            status='partial', score=50,
            evidence='ClamAV engine and local signatures present; on-demand protection only'
        )
    elif tools['clamav']['available']:
        categories['antivirus']['evidence'] = 'ClamAV installed; signatures unavailable'
    config = Path('/etc/apt/apt.conf.d/20auto-upgrades')
    try:
        content = config.read_text()
    except OSError:
        content = ''
    if 'APT::Periodic::Unattended-Upgrade "1";' in content:
        categories['updates'].update(
            status='partial', score=50,
            evidence='Unattended upgrades configured; package state not assessed'
        )
    else:
        categories['updates']['evidence'] = 'Automatic update configuration unavailable'
    categories['networkExposure']['evidence'] = 'listener baseline and external exposure not assessed'
    categories['privacy']['evidence'] = 'DNS/VPN privacy checks not assessed'
    categories['projectProtection']['evidence'] = 'no project baseline selected'
    categories['hardening']['evidence'] = 'host hardening checks incomplete'
    complete = all(item['score'] is not None for item in categories.values())
    total = round(sum(item['score'] * item['weight'] / 100 for item in categories.values())) if complete else None
    return {'score': total, 'status': 'assessed' if complete else 'insufficient_evidence', 'categories': categories}
