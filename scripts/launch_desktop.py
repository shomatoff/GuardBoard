"""Start GuardBoard from a desktop shortcut and open its authenticated local URL."""
from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
URL_PREFIX = "GuardBoard local URL: http://127.0.0.1:8765/?key="


def main() -> int:
    if os.geteuid() == 0:
        print("GuardBoard must run as a normal user, never root.", file=sys.stderr)
        return 1

    server = subprocess.Popen(
        [str(ROOT / "run.sh"), *sys.argv[1:]],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        assert server.stdout is not None
        first_line = server.stdout.readline().strip()
        if not first_line.startswith(URL_PREFIX):
            print(first_line or "GuardBoard did not start.", file=sys.stderr)
            return 1

        url = first_line.removeprefix("GuardBoard local URL: ")
        for _ in range(50):
            if server.poll() is not None:
                print("GuardBoard stopped before becoming ready.", file=sys.stderr)
                return 1
            try:
                with socket.create_connection(("127.0.0.1", 8765), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            print("GuardBoard did not become ready. Check port 8765.", file=sys.stderr)
            return 1

        print(f"GuardBoard is running at {url}", flush=True)
        print("Keep this terminal open; press Ctrl+C to stop GuardBoard.", flush=True)
        if os.environ.get("GUARDBOARD_NO_BROWSER") != "1":
            try:
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                print("Could not open a browser. Open the URL above manually.", file=sys.stderr)
        for line in server.stdout:
            print(line, end="", flush=True)
        return server.wait()
    except KeyboardInterrupt:
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()


if __name__ == "__main__":
    raise SystemExit(main())
