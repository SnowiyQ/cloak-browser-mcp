from __future__ import annotations

import argparse
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import BrowserConfig
from .controller import BrowserController
from .install import install_mcp_servers, print_mcp_config, print_mcp_targets

VALID_CAPS = {"network", "cookies", "pdf", "console"}


def _parse_caps(raw: str | None) -> set[str]:
    if not raw:
        return set()
    parts = {p.strip().lower() for p in raw.split(",") if p.strip()}
    if "all" in parts:
        return set(VALID_CAPS)
    invalid = parts - VALID_CAPS
    if invalid:
        raise SystemExit(f"Unknown capabilities: {sorted(invalid)}. Valid: {sorted(VALID_CAPS)} or 'all'")
    return parts


CAPS: set[str] = _parse_caps(os.getenv("CLOAK_BROWSER_CAPS"))

mcp = FastMCP("cloak-browser")
controller = BrowserController(BrowserConfig.load())


@mcp.tool()
async def cloak_launch(headless: bool | None = None) -> dict[str, Any]:
    """Start the stealth browser (anti-detection on). Returns connection status."""
    return await controller.connect(headless=headless)


@mcp.tool()
async def cloak_close() -> dict[str, Any]:
    """Close the browser and release resources."""
    return await controller.close()


@mcp.tool()
async def cloak_status() -> dict[str, Any]:
    """Return connection mode, active URL, open pages, and non-secret config."""
    return await controller.status()


@mcp.tool()
async def cloak_snapshot() -> dict[str, Any]:
    """PRIMARY exploration tool. Returns an indented accessibility tree of the active page with [@eN] refs."""
    return await controller.snapshot()


@mcp.tool()
async def cloak_click(ref: str, timeout_ms: int | None = None) -> dict[str, Any]:
    """Click an element by its [@eN] ref from cloak_snapshot. Auto-retries by re-snapshotting."""
    return await controller.click(ref=ref, timeout_ms=timeout_ms)


@mcp.tool()
async def cloak_type(
    ref: str,
    text: str,
    clear: bool = False,
    submit: bool = False,
    timeout_ms: int | None = None,
) -> dict[str, Any]:
    """Type into an input by ref. clear=true overwrites existing value. submit=true presses Enter after typing."""
    return await controller.type_text(ref=ref, text=text, clear=clear, submit=submit, timeout_ms=timeout_ms)


@mcp.tool()
async def cloak_select(ref: str, value: str | list[str]) -> dict[str, Any]:
    """Select a dropdown option by ref. value can be a value, label, or list of values."""
    return await controller.select(ref=ref, value=value)


@mcp.tool()
async def cloak_hover(ref: str) -> dict[str, Any]:
    """Hover over an element by ref."""
    return await controller.hover(ref=ref)


@mcp.tool()
async def cloak_check(ref: str, checked: bool = True) -> dict[str, Any]:
    """Check or uncheck a checkbox/radio by ref."""
    return await controller.check(ref=ref, checked=checked)


@mcp.tool()
async def cloak_read_page(max_chars: int = 20_000) -> dict[str, Any]:
    """Return the active page content as clean markdown."""
    return await controller.read_page(max_chars=max_chars)


@mcp.tool()
async def cloak_screenshot(path: str | None = None, full_page: bool = True, annotate: bool = True) -> dict[str, Any]:
    """Take a screenshot. With annotate=true returns the bounding boxes of refs from the last snapshot."""
    return await controller.screenshot(path=path, full_page=full_page, annotate=annotate)


@mcp.tool()
async def cloak_navigate(url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
    """Navigate the active page to URL and wait for the page to settle."""
    return await controller.navigate(url=url, wait_until=wait_until)


@mcp.tool()
async def cloak_back() -> dict[str, Any]:
    """Navigate back in the active page's history."""
    return await controller.back()


@mcp.tool()
async def cloak_forward() -> dict[str, Any]:
    """Navigate forward in the active page's history."""
    return await controller.forward()


@mcp.tool()
async def cloak_press_key(key: str) -> dict[str, Any]:
    """Press a keyboard key on the active page, e.g. Enter, Escape, Tab, Control+A."""
    return await controller.press_key(key=key)


@mcp.tool()
async def cloak_scroll(direction: str = "down", amount: int | None = None) -> dict[str, Any]:
    """Scroll the active page. direction: up, down, top, bottom. amount is px for up/down (default 600)."""
    return await controller.scroll(direction=direction, amount=amount)


@mcp.tool()
async def cloak_wait(ms: int | None = None) -> dict[str, Any]:
    """Wait for the active page to settle (DOM + network idle). Optionally sleep extra ms."""
    return await controller.wait(ms=ms)


@mcp.tool()
async def cloak_evaluate(script: str) -> dict[str, Any]:
    """Execute JavaScript in the active page and return its result."""
    return await controller.evaluate(script=script)


@mcp.tool()
async def cloak_new_page(url: str | None = None) -> dict[str, Any]:
    """Open a new page/tab, optionally navigating to a URL. Becomes the active page."""
    return await controller.new_page(url=url)


@mcp.tool()
async def cloak_list_pages() -> dict[str, Any]:
    """List all open pages with their indices."""
    return await controller.list_pages()


@mcp.tool()
async def cloak_close_page(index: int) -> dict[str, Any]:
    """Close a specific page by its index from cloak_list_pages."""
    return await controller.close_page(index=index)


def _register_capability_tools(caps: set[str]) -> None:
    if "network" in caps:
        @mcp.tool()
        async def cloak_network_intercept(
            pattern: str,
            action: str = "block",
            body: str | None = None,
            status: int = 200,
            content_type: str = "text/plain",
        ) -> dict[str, Any]:
            """Intercept requests matching glob/regex pattern. action: block, mock, passthrough."""
            return await controller.network_intercept(
                pattern=pattern, action=action, body=body, status=status, content_type=content_type
            )

        @mcp.tool()
        async def cloak_network_continue(pattern: str) -> dict[str, Any]:
            """Remove an interception rule for the given pattern."""
            return await controller.network_continue(pattern=pattern)

    if "cookies" in caps:
        @mcp.tool()
        async def cloak_get_cookies(urls: list[str] | None = None) -> dict[str, Any]:
            """Get all cookies, optionally filtered by a list of URLs."""
            return await controller.get_cookies(urls=urls)

        @mcp.tool()
        async def cloak_set_cookies(cookies: list[dict[str, Any]]) -> dict[str, Any]:
            """Set cookies. Each item must have name+value plus url or domain+path."""
            return await controller.set_cookies(cookies=cookies)

    if "pdf" in caps:
        @mcp.tool()
        async def cloak_pdf(path: str | None = None) -> dict[str, Any]:
            """Save the active page as a PDF. Chromium-only."""
            return await controller.pdf(path=path)

    if "console" in caps:
        @mcp.tool()
        async def cloak_console(clear: bool = False, limit: int = 200) -> dict[str, Any]:
            """Get recent console messages from the active page. clear=true empties the buffer."""
            return await controller.console(clear=clear, limit=limit)


def main() -> None:
    parser = argparse.ArgumentParser(prog="cloak-browser-mcp", description="Cloak Browser MCP Server")
    parser.add_argument("--install", action="store_true", help="Install the MCP server into supported client configs")
    parser.add_argument("--uninstall", action="store_true", help="Remove the MCP server from supported client configs")
    parser.add_argument("--config", action="store_true", help="Print MCP config snippets")
    parser.add_argument("--target", "-t", action="append", help="Install/configure one target, e.g. codex or claude-code")
    parser.add_argument("--all", action="store_true", help="Install/uninstall all supported targets")
    parser.add_argument("--list-targets", action="store_true", help="List supported MCP client targets")
    parser.add_argument(
        "--caps",
        default=None,
        help="Comma-separated capability tools to enable: network,cookies,pdf,console or 'all'",
    )
    args, _unknown = parser.parse_known_args()

    if args.install and args.uninstall:
        parser.error("cannot install and uninstall at the same time")

    global CAPS
    if args.caps is not None:
        CAPS = _parse_caps(args.caps)
    _register_capability_tools(CAPS)

    targets = ["all"] if args.all else args.target
    if args.list_targets:
        print_mcp_targets()
        return
    if args.config:
        print_mcp_config(args.target[0] if args.target else None)
        return
    if args.install:
        install_mcp_servers(targets=targets)
        return
    if args.uninstall:
        install_mcp_servers(uninstall=True, targets=targets)
        return

    mcp.run()


if __name__ == "__main__":
    main()
