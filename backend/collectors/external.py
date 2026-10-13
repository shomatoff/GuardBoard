"""Explicitly triggered external diagnostics. Never called by periodic collectors."""
from __future__ import annotations

import ipaddress
import json
import urllib.request

PUBLIC_IP_URL = 'https://api64.ipify.org?format=json'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def public_ip() -> str:
    """Send one bounded HTTPS request to the fixed ipify endpoint."""
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(PUBLIC_IP_URL, headers={'User-Agent': 'GuardBoard/0.1'})
    with opener.open(request, timeout=5) as response:
        body = response.read(1025)
    if len(body) > 1024:
        raise ValueError('Response too large')
    parsed = json.loads(body)
    return str(ipaddress.ip_address(parsed['ip']))


def download_sample() -> dict[str, float | int]:
    """Bounded 5 MB Cloudflare download sample, not a guaranteed line-speed result."""
    import time
    size = 5_000_000
    url = f'https://speed.cloudflare.com/__down?bytes={size}'
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={'User-Agent': 'GuardBoard/0.1', 'Accept-Encoding': 'identity'})
    started = time.perf_counter()
    received = 0
    with opener.open(request, timeout=15) as response:
        while received < size:
            chunk = response.read(min(65536, size - received))
            if not chunk:
                break
            received += len(chunk)
    elapsed = time.perf_counter() - started
    if received < size or elapsed <= 0:
        raise ValueError('Incomplete speed sample')
    return {'download_mbps': round(received * 8 / elapsed / 1_000_000, 2),
            'bytes_downloaded': received, 'seconds': round(elapsed, 3)}


def tcp_latency_sample() -> dict[str, float | int | None]:
    """Five opt-in TCP handshakes to fixed 1.1.1.1:443; not ICMP packet loss."""
    import socket
    import statistics
    import time
    timings = []
    failures = 0
    for _ in range(5):
        started = time.perf_counter()
        try:
            with socket.create_connection(('1.1.1.1', 443), timeout=1):
                timings.append((time.perf_counter() - started) * 1000)
        except OSError:
            failures += 1
    jitter = statistics.mean(abs(b - a) for a, b in zip(timings, timings[1:])) if len(timings) > 1 else None
    return {'target': '1.1.1.1:443', 'mean_ms': round(statistics.mean(timings), 1) if timings else None,
            'jitter_ms': round(jitter, 1) if jitter is not None else None,
            'failed_probes': failures, 'total_probes': 5}
