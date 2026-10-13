"""Local Chrome flow; runs only when Chrome is installed."""
import shutil
import os
import socket
import subprocess
import time
from urllib.request import urlopen

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.mark.parametrize('demo', [False, True])
def test_navigation_language_theme_and_palette(demo):
    chrome = shutil.which('google-chrome')
    if not chrome:
        pytest.skip('Google Chrome unavailable')
    command = ['./run.sh'] + (['--demo'] if demo else [])
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, env={**os.environ, 'GUARDBOARD_PORT': str(port)})
    try:
        first_line = server.stdout.readline().strip()
        assert first_line.startswith('GuardBoard local URL: '), f'Server failed to start: {first_line}'
        url = first_line.removeprefix('GuardBoard local URL: ')
        for _ in range(50):
            try:
                urlopen(url, timeout=1).close()
                break
            except OSError:
                time.sleep(.1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chrome, headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.goto(url)
            page.locator('#mode').wait_for()
            assert page.locator('#mode').inner_text() == ('DEMO REJIM' if demo else 'REAL REJIM')
            page.locator('nav a[href="#/security"]').click()
            expect(page.locator('#heading')).to_have_text('Xavfsizlik')
            expect(page.get_by_role('heading', name='ClamAV antivirus skani')).to_be_visible()
            expect(page.get_by_role('heading', name='Firewall holati')).to_be_visible()
            expect(page.get_by_role('heading', name='Linux hardening dalillari')).to_be_visible()
            page.locator('nav a[href="#/privacy"]').click()
            expect(page.get_by_role('heading', name='Maxfiylik chegaralari')).to_be_visible()
            expect(page.get_by_text('Hech bir vosita 100% anonimlik yoki to‘liq himoya bermaydi.')).to_be_visible()
            page.locator('nav a[href="#/alerts"]').click()
            expect(page.get_by_role('heading', name='Xavfsizlik va tizim hodisalari')).to_be_visible()
            assert page.locator('nav a.active').get_attribute('aria-current') == 'page'
            page.locator('#language').select_option('en')
            expect(page.locator('#heading')).to_have_text('Alerts & Logs')
            page.locator('#theme').click()
            assert 'light' in page.locator('body').get_attribute('class')
            page.keyboard.press('Control+k')
            assert page.locator('#palette').evaluate('(node) => node.open')
            page.locator('#quick-search').fill('network')
            page.locator('.palette-result').first.click()
            expect(page.locator('#heading')).to_have_text('Network')
            page.locator('#back').click()
            expect(page.locator('#heading')).to_have_text('Overview')
            page.locator('nav a[href="#/learn"]').click()
            expect(page.locator('.learn-topic')).to_have_count(14)
            page.locator('.learn-topic summary').first.click()
            expect(page.locator('.learn-topic').first.get_by_text('What it protects against', exact=False)).to_be_visible()
            page.locator('nav a[href="#/settings"]').click()
            expect(page.get_by_role('heading', name='Alert thresholds')).to_be_visible()
            expect(page.locator('.settings-field')).to_have_count(5)
            page.locator('nav a[href="#/optimizer"]').click()
            expect(page.get_by_role('heading', name='Current power state')).to_be_visible()
            expect(page.get_by_text('Proposal only — no system change was applied.')).to_have_count(3)
            page.locator('nav a[href="#/system"]').click()
            expect(page.locator('#heading')).to_have_text('System')
            if not demo:
                expect(page.locator('.core-cell').first).to_be_visible()
                expect(page.locator('svg.line-chart')).to_be_visible()
                expect(page.locator('.process-table')).to_be_visible()
                page.locator('nav a[href="#/network"]').click()
                expect(page.locator('#heading')).to_have_text('Network')
                expect(page.locator('.interface-row').first).to_be_visible()
                requests = []
                page.on('request', lambda request: requests.append(request.url))
                page.get_by_role('button', name='Check now').click()
                assert not any('/api/network/public-ip' in url for url in requests)
                page.locator('nav a[href="#/wifi"]').click()
                expect(page.locator('#heading')).to_have_text('Wi-Fi')
                expect(page.locator('.standard-list span').first).to_be_visible()
                assert not any('/api/wifi/scan' in url for url in requests)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
