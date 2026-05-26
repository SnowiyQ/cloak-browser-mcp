from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import BrowserConfig
from .controller import BrowserController

mcp = FastMCP("cloak-browser")
controller = BrowserController(BrowserConfig.load())


@mcp.tool()
async def browser_status() -> dict[str, Any]:
    """Return connection state, active page URL, open pages, and non-secret config."""
    return await controller.status()


@mcp.tool()
async def browser_connect(cdp_url: str | None = None, launch: bool | None = None, headless: bool | None = None) -> dict[str, Any]:
    """Connect to a CDP browser endpoint or launch local Chromium when launch=true."""
    return await controller.connect(cdp_url=cdp_url, launch=launch, headless=headless)


@mcp.tool()
async def browser_new_page(url: str | None = None) -> dict[str, Any]:
    """Open a new tab/page, optionally navigating to a URL."""
    return await controller.new_page(url=url)


@mcp.tool()
async def browser_goto(url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
    """Navigate active page to URL. wait_until can be load, domcontentloaded, networkidle, or commit."""
    return await controller.goto(url=url, wait_until=wait_until)


@mcp.tool()
async def browser_click(selector: str, timeout_ms: int | None = None) -> dict[str, Any]:
    """Click an element by CSS/text selector."""
    return await controller.click(selector=selector, timeout_ms=timeout_ms)


@mcp.tool()
async def browser_type(selector: str, text: str, clear: bool = False, press_enter: bool = False, timeout_ms: int | None = None) -> dict[str, Any]:
    """Type text into an element. Set clear=true to replace existing text."""
    return await controller.type_text(selector=selector, text=text, clear=clear, press_enter=press_enter, timeout_ms=timeout_ms)


@mcp.tool()
async def browser_press(key: str) -> dict[str, Any]:
    """Press a keyboard key like Enter, Escape, Tab, Control+A."""
    return await controller.press(key=key)


@mcp.tool()
async def browser_mouse_click(x: float, y: float, button: str = "left") -> dict[str, Any]:
    """Click absolute page coordinates."""
    return await controller.mouse_click(x=x, y=y, button=button)


@mcp.tool()
async def browser_wait(selector: str | None = None, ms: int | None = None) -> dict[str, Any]:
    """Wait for a selector or sleep for ms milliseconds."""
    return await controller.wait(selector=selector, ms=ms)


@mcp.tool()
async def browser_text(selector: str = "body", max_chars: int = 8000) -> dict[str, Any]:
    """Read visible inner text from a selector, default body."""
    return await controller.text(selector=selector, max_chars=max_chars)


@mcp.tool()
async def browser_evaluate(script: str) -> dict[str, Any]:
    """Run JavaScript in the active page and return the result."""
    return await controller.evaluate(script=script)


@mcp.tool()
async def browser_screenshot(path: str | None = None, full_page: bool = True) -> dict[str, Any]:
    """Take a screenshot. If path is omitted, saves under the configured screenshots directory."""
    return await controller.screenshot(path=path, full_page=full_page)


@mcp.tool()
async def browser_close() -> dict[str, Any]:
    """Close the browser connection/process controlled by this MCP server."""
    return await controller.close()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
