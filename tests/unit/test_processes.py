from backend.collectors.processes import ProcessSampler


def test_process_sampler_does_not_invent_first_rate():
    sampler = ProcessSampler()
    first = sampler.sample()
    assert first['process_count'] >= 1
    assert first['top_memory']
    assert first['top_cpu'] == []
    assert first['top_disk'] == []
