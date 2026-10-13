from backend.collectors.network import NetworkSampler, parse_default_gateway


def test_gateway_parser():
    data = 'Iface Destination Gateway Flags RefCnt Use Metric Mask\neth0 00000000 0101A8C0 0003 0 0 0 00000000\n'
    assert parse_default_gateway(data) == '192.168.1.1'
    assert parse_default_gateway('Iface Destination Gateway Flags\n') is None
    malformed = 'Iface Destination Gateway Flags\neth0 00000000 0101A8C0 ZZZZ\n' + data.split('\n', 1)[1]
    assert parse_default_gateway(malformed) == '192.168.1.1'


def test_network_rate_needs_second_sample():
    sampler = NetworkSampler()
    first = sampler.sample(now=10)
    second = sampler.sample(now=12)
    assert first['interfaces']
    assert all(item['download_bytes_per_second'] is None for item in first['interfaces'])
    assert all(item['download_bytes_per_second'] is not None for item in second['interfaces'])
