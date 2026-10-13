from backend.security.posture import WEIGHTS, check


def test_weights_and_incomplete_score():
    assert sum(WEIGHTS.values()) == 100
    result = check()
    assert result['score'] is None
    assert result['status'] == 'insufficient_evidence'
    assert result['categories']['firewall']['score'] is None
    assert set(result['categories']) == set(WEIGHTS)
