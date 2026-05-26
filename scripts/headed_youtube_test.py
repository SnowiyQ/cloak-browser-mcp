#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
from pathlib import Path

from cloak_browser_mcp.config import BrowserConfig
from cloak_browser_mcp.controller import BrowserController


async def main() -> None:
    deps = Path('/home/lumio/.local/playwright-deps/root')
    env = os.environ.copy()
    env['DISPLAY'] = ':77'
    env['LD_LIBRARY_PATH'] = f"{deps}/usr/lib/x86_64-linux-gnu:" + env.get('LD_LIBRARY_PATH', '')

    xvfb = subprocess.Popen(
        ['/usr/bin/Xvfb', ':77', '-screen', '0', '1280x720x24', '-nolisten', 'tcp'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
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
            print('goto:', json.dumps(await c.goto('https://www.youtube.com', wait_until='domcontentloaded'), ensure_ascii=False, default=str))
            title = await c.evaluate('() => document.title')
            print('title:', json.dumps(title, ensure_ascii=False, default=str))
            shot = await c.screenshot(full_page=False)
            print('screenshot:', json.dumps(shot, ensure_ascii=False, default=str))
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
