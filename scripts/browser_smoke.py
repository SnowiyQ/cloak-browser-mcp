#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
from urllib.parse import urlparse

from cloak_browser_mcp.config import BrowserConfig
from cloak_browser_mcp.controller import BrowserController


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError("empty URL")
    if not urlparse(raw).scheme:
        raw = "https://" + raw
    return raw


async def main() -> None:
    parser = argparse.ArgumentParser(description="Launch CloakBrowser and smoke-test a URL.")
    parser.add_argument("url")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--wait-ms", type=int, default=1000)
    parser.add_argument("--wait-until", default="domcontentloaded", choices=["commit", "domcontentloaded", "load", "networkidle"])
    args = parser.parse_args()

    cfg = BrowserConfig.load()
    cfg.headless = args.headless

    controller = BrowserController(cfg)
    try:
        print("connect:", json.dumps(await controller.connect(headless=args.headless), ensure_ascii=False, default=str))
        print("goto:", json.dumps(await controller.goto(normalize_url(args.url), wait_until=args.wait_until), ensure_ascii=False, default=str))
        if args.wait_ms > 0:
            await controller.wait(ms=args.wait_ms)
        print("text:", json.dumps(await controller.text("body", max_chars=1000), ensure_ascii=False, default=str))
        print("screenshot:", json.dumps(await controller.screenshot(full_page=False), ensure_ascii=False, default=str))
    finally:
        await controller.close()


if __name__ == "__main__":
    asyncio.run(main())
