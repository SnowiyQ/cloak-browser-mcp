from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config import BrowserConfig


class BrowserController:
    """Persistent Playwright controller for one browser/session."""

    def __init__(self, config: BrowserConfig):
        self.config = config
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.mode = "disconnected"

    async def _ensure_playwright(self):
        if self._playwright is not None:
            return self._playwright
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Python package 'playwright' is not installed. Run `pip install -e .` from the project root."
            ) from exc
        self._playwright = await async_playwright().start()
        return self._playwright

    async def status(self) -> dict[str, Any]:
        browser_connected = bool(self.browser and self.browser.is_connected())
        pages = []
        if self.context:
            for idx, page in enumerate(self.context.pages):
                pages.append({"index": idx, "url": page.url, "title": await _safe_title(page)})
        return {
            "mode": self.mode,
            "connected": browser_connected,
            "active_url": self.page.url if self.page else None,
            "pages": pages,
            "config": self.config.safe_dict(),
        }

    async def connect(
        self,
        cdp_url: str | None = None,
        launch: bool | None = None,
        headless: bool | None = None,
    ) -> dict[str, Any]:
        if self.browser and self.browser.is_connected():
            return await self.status()

        target_cdp_url = cdp_url if cdp_url is not None else self.config.cdp_url
        if launch is True and cdp_url is None:
            target_cdp_url = None
        if target_cdp_url:
            pw = await self._ensure_playwright()
            self.browser = await pw.chromium.connect_over_cdp(target_cdp_url)
            self.mode = "cdp"
            self.context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context()
        else:
            should_launch = self.config.launch_when_no_cdp if launch is None else launch
            if not should_launch:
                raise RuntimeError(
                    "No CDP URL configured. Start CloakBrowser with a CDP endpoint or call browser_connect(cdp_url='http://127.0.0.1:9222')."
                )
            if self.config.launch_backend == "cloakbrowser":
                self.browser = await self._launch_cloakbrowser(headless=headless)
                self.mode = "cloakbrowser"
            else:
                pw = await self._ensure_playwright()
                self.browser = await pw.chromium.launch(
                    headless=self.config.headless if headless is None else headless,
                    executable_path=self.config.executable_path,
                    args=self.config.browser_args,
                )
                self.mode = "playwright"
            self.context = await self.browser.new_context()

        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        self.page.set_default_timeout(self.config.default_timeout_ms)
        return await self.status()

    async def _launch_cloakbrowser(self, headless: bool | None = None):
        try:
            from cloakbrowser import launch_async
        except ImportError as exc:
            raise RuntimeError(
                "Python package 'cloakbrowser' is not installed. Run `pip install -e .` from the project root."
            ) from exc
        if self.config.executable_path:
            raise RuntimeError("executable_path is only supported with launch_backend='playwright'.")
        return await launch_async(
            headless=self.config.headless if headless is None else headless,
            args=self.config.browser_args,
            stealth_args=self.config.cloak_stealth_args,
            proxy=self.config.cloak_proxy,
            timezone=self.config.cloak_timezone,
            locale=self.config.cloak_locale,
            geoip=self.config.cloak_geoip,
            humanize=self.config.cloak_humanize,
            human_preset=self.config.cloak_human_preset,
        )

    async def ensure_page(self):
        if not (self.browser and self.browser.is_connected()):
            await self.connect()
        if self.page and not self.page.is_closed():
            return self.page
        if self.context and self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config.default_timeout_ms)
        return self.page

    async def new_page(self, url: str | None = None) -> dict[str, Any]:
        await self.connect() if not (self.browser and self.browser.is_connected()) else None
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config.default_timeout_ms)
        if url:
            await self.page.goto(url, wait_until="domcontentloaded")
        return {"url": self.page.url, "title": await _safe_title(self.page)}

    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        page = await self.ensure_page()
        response = await page.goto(url, wait_until=wait_until)
        return {
            "url": page.url,
            "title": await _safe_title(page),
            "status": response.status if response else None,
        }

    async def click(self, selector: str, timeout_ms: int | None = None) -> dict[str, Any]:
        page = await self.ensure_page()
        await page.click(selector, timeout=timeout_ms or self.config.default_timeout_ms)
        return {"clicked": selector, "url": page.url}

    async def type_text(
        self,
        selector: str,
        text: str,
        clear: bool = False,
        press_enter: bool = False,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        page = await self.ensure_page()
        locator = page.locator(selector)
        if clear:
            await locator.fill("", timeout=timeout_ms or self.config.default_timeout_ms)
            await locator.fill(text, timeout=timeout_ms or self.config.default_timeout_ms)
        else:
            await locator.type(text, timeout=timeout_ms or self.config.default_timeout_ms)
        if press_enter:
            await locator.press("Enter")
        return {"typed_chars": len(text), "selector": selector, "url": page.url}

    async def press(self, key: str) -> dict[str, Any]:
        page = await self.ensure_page()
        await page.keyboard.press(key)
        return {"pressed": key, "url": page.url}

    async def mouse_click(self, x: float, y: float, button: str = "left") -> dict[str, Any]:
        page = await self.ensure_page()
        await page.mouse.click(x, y, button=button)
        return {"clicked": {"x": x, "y": y, "button": button}, "url": page.url}

    async def text(self, selector: str = "body", max_chars: int = 8000) -> dict[str, Any]:
        page = await self.ensure_page()
        value = await page.locator(selector).inner_text(timeout=self.config.default_timeout_ms)
        if len(value) > max_chars:
            value = value[:max_chars] + "\n...[truncated]"
        return {"selector": selector, "text": value, "url": page.url, "title": await _safe_title(page)}

    async def evaluate(self, script: str) -> dict[str, Any]:
        page = await self.ensure_page()
        result = await page.evaluate(script)
        return {"result": result, "url": page.url}

    async def screenshot(self, path: str | None = None, full_page: bool = True) -> dict[str, Any]:
        page = await self.ensure_page()
        if path is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            path = str(Path(self.config.screenshots_dir).expanduser() / f"screenshot-{ts}.png")
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        out = await page.screenshot(path=str(Path(path).expanduser()), full_page=full_page)
        return {"path": str(Path(path).expanduser()), "bytes": len(out), "url": page.url}

    async def wait(self, selector: str | None = None, ms: int | None = None) -> dict[str, Any]:
        page = await self.ensure_page()
        if selector:
            await page.wait_for_selector(selector, timeout=self.config.default_timeout_ms)
            return {"waited_for": selector, "url": page.url}
        wait_ms = ms if ms is not None else 1000
        await page.wait_for_timeout(wait_ms)
        return {"waited_ms": wait_ms, "url": page.url}

    async def close(self) -> dict[str, Any]:
        if self.browser and self.browser.is_connected():
            await self.browser.close()
        if self._playwright is not None:
            await self._playwright.stop()
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.mode = "disconnected"
        return {"closed": True}


async def _safe_title(page) -> str | None:
    try:
        return await page.title()
    except Exception:
        return None
