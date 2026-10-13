"""Smoke-test a frozen GuardBoard package without modifying system settings."""
from __future__ import annotations

import http.cookiejar
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import HTTPCookieProcessor, build_opener


def available_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def check(binary: Path, demo: bool) -> None:
    port = available_port()
    with tempfile.TemporaryDirectory(prefix="guardboard-smoke-") as data_home:
        process = subprocess.Popen(
            [str(binary), *(("--demo",) if demo else ())],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ, "GUARDBOARD_PORT": str(port), "XDG_DATA_HOME": data_home},
        )
        try:
            assert process.stdout is not None
            first_line = process.stdout.readline().strip()
            if not first_line.startswith("GuardBoard local URL: "):
                raise RuntimeError(f"Package startup failed: {first_line}")
            url = first_line.removeprefix("GuardBoard local URL: ")
            opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("Package exited before HTTP became ready")
                try:
                    with opener.open(url, timeout=0.5) as response:
                        assert b"GuardBoard" in response.read()
                    break
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            else:
                raise RuntimeError("Package HTTP server did not become ready")
            with opener.open(f"http://127.0.0.1:{port}/api/bootstrap", timeout=3) as response:
                assert json.load(response)["demo"] is demo
            with opener.open(f"http://127.0.0.1:{port}/assets/js/app.js", timeout=3) as response:
                assert b"renderRadar" in response.read()
            if not demo:
                with opener.open(f"http://127.0.0.1:{port}/api/telemetry", timeout=10) as response:
                    assert json.load(response)["mode"] == "real"
                assert (Path(data_home) / "guardboard" / "history-real.sqlite").exists()
            print(f"{('demo' if demo else 'real')} package smoke: PASS")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    package = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/GuardBoard/GuardBoard").resolve()
    check(package, demo=True)
    check(package, demo=False)
