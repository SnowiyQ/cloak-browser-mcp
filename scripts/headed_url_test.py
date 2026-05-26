#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from cloak_browser_mcp.config import BrowserConfig
from cloak_browser_mcp.controller import BrowserController


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError('empty URL')
    if not urlparse(raw).scheme:
        raw = 'https://' + raw
    return raw


async def main() -> None:
    parser = argparse.ArgumentParser(description='Launch headed Chromium via Xvfb and capture a URL screenshot.')
    parser.add_argument('url')
    parser.add_argument('--display', default=':77')
    parser.add_argument('--wait-ms', type=int, default=3000)
    parser.add_argument('--wait-until', default='domcontentloaded', choices=['commit', 'domcontentloaded', 'load', 'networkidle'])
    args = parser.parse_args()

    url = normalize_url(args.url)
    deps = Path('/home/lumio/.local/playwright-deps/root')
    env = os.environ.copy()
    env['DISPLAY'] = args.display
    env['PATH'] = f"{deps}/usr/bin:" + env.get('PATH', '')
    env['LD_LIBRARY_PATH'] = f"{deps}/usr/lib/x86_64-linux-gnu:" + env.get('LD_LIBRARY_PATH', '')
    xvfb_bin = os.environ.get('XVFB_BIN') or ('/usr/bin/Xvfb' if Path('/usr/bin/Xvfb').exists() else str(deps / 'usr/bin/Xvfb'))
    xkb_dir = deps / 'usr/share/X11/xkb'

    xvfb = subprocess.Popen(
        [xvfb_bin, args.display, '-screen', '0', '1280x720x24', '-nolisten', 'tcp', '-xkbdir', str(xkb_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    started_at = time.time()
    try:
        await asyncio.sleep(2)
        if xvfb.poll() is not None:
            out, err = xvfb.communicate(timeout=5)
            raise RuntimeError(f'Xvfb failed rc={xvfb.returncode}\nstdout={out}\nstderr={err}')

        os.environ.update(env)
        cfg = BrowserConfig.load('/home/lumio/cloak-browser-mcp/config.yaml')
        cfg.cdp_url = None
        cfg.launch_when_no_cdp = True
        cfg.headless = False
        cfg.browser_args = ['--no-sandbox', '--disable-dev-shm-usage']
        c = BrowserController(cfg)
        try:
            print('connect:', json.dumps(await c.connect(launch=True, headless=False), ensure_ascii=False, default=str))
            nav = await c.goto(url, wait_until=args.wait_until)
            print('goto:', json.dumps(nav, ensure_ascii=False, default=str))
            if args.wait_ms > 0:
                await c.wait(ms=args.wait_ms)
            title = await c.evaluate('() => document.title')
            location = await c.evaluate('() => location.href')
            text = await c.text('body', max_chars=1000)
            shot = await c.screenshot(full_page=False)
            print('title:', json.dumps(title, ensure_ascii=False, default=str))
            print('location:', json.dumps(location, ensure_ascii=False, default=str))
            print('text:', json.dumps(text, ensure_ascii=False, default=str))
            print('screenshot:', json.dumps(shot, ensure_ascii=False, default=str))
            print('elapsed:', json.dumps({'seconds': round(time.time() - started_at, 2)}, ensure_ascii=False))
        finally:
            await c.close()
    finally:
        if xvfb.poll() is None:
            xvfb.send_signal(signal.SIGTERM)
            try:
                xvfb.wait(timeout=5)
            except subprocess.TimeoutExpired:
                xvfb.kill()


if __name__ == '__main__':
    asyncio.run(main())
