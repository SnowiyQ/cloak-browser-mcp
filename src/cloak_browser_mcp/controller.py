from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from .config import BrowserConfig

_SNAPSHOT_JS = r"""
(() => {
  const INTERESTING = new Set(['A','BUTTON','INPUT','SELECT','TEXTAREA','LABEL','SUMMARY','DETAILS','OPTION']);
  const TEXTUAL = new Set(['H1','H2','H3','H4','H5','H6','P','LI','TD','TH','DT','DD','FIGCAPTION','BLOCKQUOTE','PRE','CODE']);
  const roleMap = { A:'link', BUTTON:'button', INPUT:'textbox', SELECT:'combobox', TEXTAREA:'textbox',
                    H1:'heading', H2:'heading', H3:'heading', H4:'heading', H5:'heading', H6:'heading',
                    LI:'listitem', OPTION:'option', LABEL:'label', SUMMARY:'button' };
  document.querySelectorAll('[data-cloak-ref]').forEach(n => n.removeAttribute('data-cloak-ref'));
  const lines = [];
  let counter = 0;
  function visible(el) {
    if (!(el instanceof Element)) return false;
    const cs = el.ownerDocument.defaultView.getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }
  function nameOf(el) {
    const aria = el.getAttribute('aria-label');
    if (aria) return aria;
    const labelledby = el.getAttribute('aria-labelledby');
    if (labelledby) {
      const ref = document.getElementById(labelledby);
      if (ref) return (ref.innerText || '').trim().slice(0, 120);
    }
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      const ph = el.getAttribute('placeholder');
      if (ph) return ph;
      if (el.id) {
        const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (lbl) return (lbl.innerText || '').trim().slice(0, 120);
      }
      const v = el.value;
      if (v) return String(v).slice(0, 80);
    }
    if (el.tagName === 'IMG') return el.getAttribute('alt') || '';
    const txt = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ');
    return txt.slice(0, 120);
  }
  function isInteresting(el) {
    if (!visible(el)) return false;
    if (INTERESTING.has(el.tagName)) return true;
    if (TEXTUAL.has(el.tagName)) return true;
    if (el.getAttribute('role')) return true;
    if (el.hasAttribute('onclick') || el.getAttribute('tabindex') === '0') return true;
    return false;
  }
  function walk(el, depth) {
    for (const child of el.children) {
      if (isInteresting(child)) {
        counter += 1;
        const ref = 'e' + counter;
        child.setAttribute('data-cloak-ref', ref);
        const role = child.getAttribute('role') || roleMap[child.tagName] || child.tagName.toLowerCase();
        const name = nameOf(child).replace(/\n/g, ' ');
        const pad = '  '.repeat(depth);
        const qname = name ? ` "${name.replace(/"/g, '\\"')}"` : '';
        lines.push(`${pad}[@${ref}] ${role}${qname}`);
        walk(child, depth + 1);
      } else {
        walk(child, depth);
      }
    }
  }
  walk(document.body, 0);
  return { tree: lines.join('\n'), count: counter, url: location.href, title: document.title };
})()
"""

_MARKDOWN_JS = r"""
(() => {
  const SKIP = new Set(['SCRIPT','STYLE','NOSCRIPT','SVG','IFRAME','TEMPLATE']);
  const out = [];
  function walk(node) {
    if (node.nodeType === Node.TEXT_NODE) {
      const t = node.textContent.replace(/\s+/g, ' ');
      if (t.trim()) out.push(t);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (SKIP.has(node.tagName)) return;
    const tag = node.tagName;
    if (/^H[1-6]$/.test(tag)) {
      const level = parseInt(tag[1], 10);
      out.push('\n\n' + '#'.repeat(level) + ' ');
      for (const c of node.childNodes) walk(c);
      out.push('\n\n');
      return;
    }
    if (tag === 'P' || tag === 'DIV' || tag === 'SECTION' || tag === 'ARTICLE') {
      out.push('\n\n');
      for (const c of node.childNodes) walk(c);
      out.push('\n\n');
      return;
    }
    if (tag === 'BR') { out.push('\n'); return; }
    if (tag === 'HR') { out.push('\n\n---\n\n'); return; }
    if (tag === 'LI') {
      out.push('\n- ');
      for (const c of node.childNodes) walk(c);
      return;
    }
    if (tag === 'A') {
      const href = node.getAttribute('href') || '';
      out.push('[');
      for (const c of node.childNodes) walk(c);
      out.push(`](${href})`);
      return;
    }
    if (tag === 'STRONG' || tag === 'B') {
      out.push('**');
      for (const c of node.childNodes) walk(c);
      out.push('**');
      return;
    }
    if (tag === 'EM' || tag === 'I') {
      out.push('*');
      for (const c of node.childNodes) walk(c);
      out.push('*');
      return;
    }
    if (tag === 'CODE') {
      out.push('`');
      for (const c of node.childNodes) walk(c);
      out.push('`');
      return;
    }
    if (tag === 'PRE') {
      out.push('\n\n```\n');
      out.push(node.innerText || '');
      out.push('\n```\n\n');
      return;
    }
    if (tag === 'IMG') {
      const alt = node.getAttribute('alt') || '';
      const src = node.getAttribute('src') || '';
      out.push(`![${alt}](${src})`);
      return;
    }
    for (const c of node.childNodes) walk(c);
  }
  walk(document.body);
  return out.join('').replace(/\n{3,}/g, '\n\n').trim();
})()
"""


class BrowserController:
    """Persistent controller for one browser/session."""

    def __init__(self, config: BrowserConfig):
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
        self.mode = "disconnected"
        self._route_rules: dict[str, dict[str, Any]] = {}
        self._console_buffers: dict[int, list[dict[str, Any]]] = {}

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

    async def connect(self, headless: bool | None = None) -> dict[str, Any]:
        if self.browser and self.browser.is_connected():
            return await self.status()
        self.browser = await self._launch_cloakbrowser(headless=headless)
        self.mode = "cloakbrowser"
        self.context = await self.browser.new_context()
        await self._install_console_capture(self.context)
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        self.page.set_default_timeout(self.config.default_timeout_ms)
        self._attach_console(self.page)
        return await self.status()

    async def _launch_cloakbrowser(self, headless: bool | None = None):
        try:
            from cloakbrowser import launch_async
        except ImportError as exc:
            raise RuntimeError(
                "Python package 'cloakbrowser' is not installed. Run `pip install -e .` from the project root."
            ) from exc
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
        self._attach_console(self.page)
        return self.page

    # --- page lifecycle -------------------------------------------------

    async def new_page(self, url: str | None = None) -> dict[str, Any]:
        if not (self.browser and self.browser.is_connected()):
            await self.connect()
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config.default_timeout_ms)
        self._attach_console(self.page)
        if url:
            await self.page.goto(url, wait_until="domcontentloaded")
        return {"url": self.page.url, "title": await _safe_title(self.page), "index": self.context.pages.index(self.page)}

    async def list_pages(self) -> dict[str, Any]:
        if not self.context:
            return {"pages": []}
        pages = []
        for idx, p in enumerate(self.context.pages):
            pages.append({"index": idx, "url": p.url, "title": await _safe_title(p), "active": p is self.page})
        return {"pages": pages}

    async def close_page(self, index: int) -> dict[str, Any]:
        if not self.context:
            return {"closed": False, "reason": "no_context"}
        pages = list(self.context.pages)
        if index < 0 or index >= len(pages):
            return {"closed": False, "reason": "index_out_of_range"}
        target = pages[index]
        was_active = target is self.page
        await target.close()
        if was_active:
            remaining = [p for p in self.context.pages if not p.is_closed()]
            self.page = remaining[-1] if remaining else None
        return {"closed": True, "index": index, "active_url": self.page.url if self.page else None}

    # --- navigation -----------------------------------------------------

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        page = await self.ensure_page()
        response = await page.goto(url, wait_until=wait_until)
        await self._settle(page)
        return {"url": page.url, "title": await _safe_title(page), "status": response.status if response else None}

    async def back(self) -> dict[str, Any]:
        page = await self.ensure_page()
        await page.go_back(wait_until="domcontentloaded")
        return {"url": page.url, "title": await _safe_title(page)}

    async def forward(self) -> dict[str, Any]:
        page = await self.ensure_page()
        await page.go_forward(wait_until="domcontentloaded")
        return {"url": page.url, "title": await _safe_title(page)}

    # --- snapshot / read ------------------------------------------------

    async def snapshot(self) -> dict[str, Any]:
        page = await self.ensure_page()
        await self._settle(page)
        data = await page.evaluate(_SNAPSHOT_JS)
        return {"url": data["url"], "title": data["title"], "count": data["count"], "tree": data["tree"]}

    async def read_page(self, max_chars: int = 20_000) -> dict[str, Any]:
        page = await self.ensure_page()
        md = await page.evaluate(_MARKDOWN_JS)
        truncated = False
        if len(md) > max_chars:
            md = md[:max_chars] + "\n...[truncated]"
            truncated = True
        return {"url": page.url, "title": await _safe_title(page), "markdown": md, "truncated": truncated}

    # --- interactions (ref-based) --------------------------------------

    def _ref_selector(self, ref: str) -> str:
        clean = ref.lstrip("@")
        return f'[data-cloak-ref="{clean}"]'

    async def _locate(self, ref: str, retry: bool = True):
        page = await self.ensure_page()
        selector = self._ref_selector(ref)
        loc = page.locator(selector)
        try:
            await loc.wait_for(state="attached", timeout=1500)
        except Exception:
            if retry:
                await page.evaluate(_SNAPSHOT_JS)
                loc = page.locator(selector)
                await loc.wait_for(state="attached", timeout=self.config.default_timeout_ms)
            else:
                raise
        return page, loc

    async def click(self, ref: str, timeout_ms: int | None = None) -> dict[str, Any]:
        page, loc = await self._locate(ref)
        await loc.click(timeout=timeout_ms or self.config.default_timeout_ms)
        return {"clicked": ref, "url": page.url}

    async def type_text(
        self,
        ref: str,
        text: str,
        clear: bool = False,
        submit: bool = False,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        page, loc = await self._locate(ref)
        timeout = timeout_ms or self.config.default_timeout_ms
        if clear:
            await loc.fill(text, timeout=timeout)
        else:
            await loc.type(text, timeout=timeout)
        if submit:
            await loc.press("Enter")
        return {"typed_chars": len(text), "ref": ref, "url": page.url}

    async def select(self, ref: str, value: str | list[str]) -> dict[str, Any]:
        page, loc = await self._locate(ref)
        selected = await loc.select_option(value)
        return {"ref": ref, "selected": selected, "url": page.url}

    async def hover(self, ref: str) -> dict[str, Any]:
        page, loc = await self._locate(ref)
        await loc.hover()
        return {"ref": ref, "url": page.url}

    async def check(self, ref: str, checked: bool = True) -> dict[str, Any]:
        page, loc = await self._locate(ref)
        if checked:
            await loc.check()
        else:
            await loc.uncheck()
        return {"ref": ref, "checked": checked, "url": page.url}

    # --- keyboard / scroll ----------------------------------------------

    async def press_key(self, key: str) -> dict[str, Any]:
        page = await self.ensure_page()
        await page.keyboard.press(key)
        return {"pressed": key, "url": page.url}

    async def scroll(self, direction: str = "down", amount: int | None = None) -> dict[str, Any]:
        page = await self.ensure_page()
        dy = amount if amount is not None else 600
        if direction == "up":
            dy = -abs(dy)
        elif direction == "down":
            dy = abs(dy)
        elif direction == "top":
            await page.evaluate("window.scrollTo(0, 0)")
            return {"scrolled": "top", "url": page.url}
        elif direction == "bottom":
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return {"scrolled": "bottom", "url": page.url}
        await page.evaluate(f"window.scrollBy(0, {dy})")
        return {"scrolled": direction, "amount": dy, "url": page.url}

    async def wait(self, ms: int | None = None) -> dict[str, Any]:
        page = await self.ensure_page()
        await self._settle(page, extra_ms=ms)
        return {"settled": True, "url": page.url}

    async def _settle(self, page, extra_ms: int | None = None) -> None:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=self.config.default_timeout_ms)
        except Exception:
            pass
        try:
            await page.wait_for_load_state("networkidle", timeout=2_500)
        except Exception:
            pass
        if extra_ms:
            await asyncio.sleep(extra_ms / 1000)

    # --- evaluate / screenshot ------------------------------------------

    async def evaluate(self, script: str) -> dict[str, Any]:
        page = await self.ensure_page()
        result = await page.evaluate(script)
        return {"result": result, "url": page.url}

    async def screenshot(self, path: str | None = None, full_page: bool = True, annotate: bool = True) -> dict[str, Any]:
        page = await self.ensure_page()
        if path is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            path = str(Path(self.config.screenshots_dir).expanduser() / f"screenshot-{ts}.png")
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        indices: list[dict[str, Any]] = []
        if annotate:
            indices = await page.evaluate(
                """
                () => Array.from(document.querySelectorAll('[data-cloak-ref]')).map(el => {
                  const r = el.getBoundingClientRect();
                  return { ref: el.getAttribute('data-cloak-ref'),
                           x: Math.round(r.x), y: Math.round(r.y),
                           w: Math.round(r.width), h: Math.round(r.height) };
                })
                """
            )
        out = await page.screenshot(path=str(Path(path).expanduser()), full_page=full_page)
        return {"path": str(Path(path).expanduser()), "bytes": len(out), "url": page.url, "indices": indices}

    # --- close ----------------------------------------------------------

    async def close(self) -> dict[str, Any]:
        if self.browser and self.browser.is_connected():
            await self.browser.close()
        self.browser = None
        self.context = None
        self.page = None
        self.mode = "disconnected"
        self._route_rules.clear()
        self._console_buffers.clear()
        self._console_installed = False
        return {"closed": True}

    # --- network (capability: network) ---------------------------------

    async def network_intercept(self, pattern: str, action: str = "block", body: str | None = None,
                                status: int = 200, content_type: str = "text/plain") -> dict[str, Any]:
        page = await self.ensure_page()
        if pattern in self._route_rules:
            await page.unroute(pattern)

        async def handler(route, request):
            rule = self._route_rules.get(pattern)
            if not rule:
                await route.continue_()
                return
            act = rule["action"]
            if act == "block":
                await route.abort()
            elif act == "mock":
                await route.fulfill(status=rule.get("status", 200),
                                    body=rule.get("body", ""),
                                    content_type=rule.get("content_type", "text/plain"))
            else:
                await route.continue_()

        self._route_rules[pattern] = {
            "action": action, "body": body or "", "status": status, "content_type": content_type,
        }
        await page.route(pattern, handler)
        return {"pattern": pattern, "action": action, "active_rules": list(self._route_rules.keys())}

    async def network_continue(self, pattern: str) -> dict[str, Any]:
        page = await self.ensure_page()
        if pattern not in self._route_rules:
            return {"removed": False, "reason": "no_rule", "pattern": pattern}
        await page.unroute(pattern)
        del self._route_rules[pattern]
        return {"removed": True, "pattern": pattern, "active_rules": list(self._route_rules.keys())}

    # --- cookies (capability: cookies) ---------------------------------

    async def get_cookies(self, urls: list[str] | None = None) -> dict[str, Any]:
        if not self.context:
            await self.connect()
        cookies = await self.context.cookies(urls) if urls else await self.context.cookies()
        return {"cookies": cookies, "count": len(cookies)}

    async def set_cookies(self, cookies: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.context:
            await self.connect()
        await self.context.add_cookies(cookies)
        return {"added": len(cookies)}

    # --- pdf (capability: pdf) ------------------------------------------

    async def pdf(self, path: str | None = None) -> dict[str, Any]:
        page = await self.ensure_page()
        if path is None:
            ts = time.strftime("%Y%m%d-%H%M%S")
            path = str(Path(self.config.screenshots_dir).expanduser() / f"page-{ts}.pdf")
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        await page.pdf(path=str(Path(path).expanduser()))
        return {"path": str(Path(path).expanduser()), "url": page.url}

    # --- console (capability: console) ---------------------------------

    async def _install_console_capture(self, context) -> None:
        if getattr(self, "_console_installed", False):
            return
        init = """
        (() => {
          if (window.__cloakConsolePatched) return;
          window.__cloakConsolePatched = true;
          window.__cloakLogs = window.__cloakLogs || [];
          const push = (kind, args) => {
            try {
              const text = Array.prototype.map.call(args, (a) => {
                if (a instanceof Error) return a.stack || a.message || String(a);
                if (typeof a === 'string') return a;
                try { return JSON.stringify(a); } catch (_) { return String(a); }
              }).join(' ');
              window.__cloakLogs.push({type: kind, text: text, t: Date.now()});
              if (window.__cloakLogs.length > 1000) window.__cloakLogs.splice(0, window.__cloakLogs.length - 1000);
            } catch (_) {}
          };
          const kinds = ['log','warn','error','info','debug','trace'];
          const orig = {};
          kinds.forEach((k) => {
            orig[k] = console[k] ? console[k].bind(console) : null;
            console[k] = function() { push(k, arguments); if (orig[k]) try { orig[k].apply(console, arguments); } catch (_) {} };
          });
          window.addEventListener('error', (e) => push('error', [(e && e.message) || 'error']));
          window.addEventListener('unhandledrejection', (e) => {
            const r = e && e.reason;
            push('error', ['unhandledrejection: ' + (r && r.message ? r.message : String(r))]);
          });
        })();
        """
        try:
            await context.add_init_script(init)
        except Exception as exc:
            import sys
            sys.stderr.write(f"cloak add_init_script failed: {exc!r}\n")
            return
        self._console_installed = True

    def _attach_console(self, page) -> None:
        pid = id(page)
        if pid in self._console_buffers:
            return
        self._console_buffers[pid] = []

        def on_close():
            self._console_buffers.pop(pid, None)

        try:
            page.on("close", on_close)
        except Exception:
            pass

    async def console(self, clear: bool = False, limit: int = 200) -> dict[str, Any]:
        page = await self.ensure_page()
        pid = id(page)
        buf = self._console_buffers.setdefault(pid, [])
        try:
            drained = await page.evaluate(
                "(() => { const a = window.__cloakLogs || []; window.__cloakLogs = []; return a; })()"
            )
            if isinstance(drained, list):
                for entry in drained:
                    if isinstance(entry, dict):
                        buf.append({"type": str(entry.get("type", "")), "text": str(entry.get("text", ""))})
                if len(buf) > 500:
                    del buf[:-500]
        except Exception:
            pass
        messages = buf[-limit:]
        if clear:
            buf.clear()
        return {"url": page.url, "messages": messages, "count": len(messages)}


async def _safe_title(page) -> str | None:
    try:
        return await page.title()
    except Exception:
        return None
