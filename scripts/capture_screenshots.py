"""Capture reproducible demo screenshots in each supported language."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENS = ("overview", "security", "settings")
LANGUAGES = ("uz", "en", "ru")


def main() -> None:
    chrome = shutil.which("google-chrome")
    if not chrome:
        raise SystemExit("Google Chrome is required for screenshot capture")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(
        [str(ROOT / "run.sh"), "--demo"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "GUARDBOARD_PORT": str(port)},
    )
    try:
        assert server.stdout is not None
        line = server.stdout.readline().strip()
        if not line.startswith("GuardBoard local URL: "):
            raise RuntimeError(f"Demo startup failed: {line}")
        url = line.removeprefix("GuardBoard local URL: ")
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    pass
                break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Demo server did not become ready")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chrome, headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            page.goto(url)
            expect(page.locator("#mode")).to_have_text("DEMO REJIM")
            for language in LANGUAGES:
                translations = json.loads((ROOT / "frontend" / "i18n" / f"{language}.json").read_text())
                page.locator("#language").select_option(language)
                for screen in SCREENS:
                    page.goto(f"http://127.0.0.1:{port}/#/{screen}")
                    expect(page.locator("#heading")).to_have_text(translations[screen])
                    expect(page.locator("#mode")).to_have_text(translations["demoMode"])
                    page.screenshot(path=str(ROOT / "docs" / "screenshots" / f"demo-{language}-{screen}.png"), full_page=True)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
