from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class BrowserConfig:
    cdp_url: str | None = None
    launch_when_no_cdp: bool = False
    headless: bool = False
    executable_path: str | None = None
    browser_args: list[str] = field(default_factory=list)
    default_timeout_ms: int = 10_000
    screenshots_dir: str = "/home/lumio/.hermes/media/cloak-browser"

    @classmethod
    def load(cls, path: str | None = None) -> "BrowserConfig":
        data: dict[str, Any] = {}
        config_path = path or os.getenv("CLOAK_BROWSER_CONFIG")
        if config_path and Path(config_path).expanduser().exists():
            loaded = yaml.safe_load(Path(config_path).expanduser().read_text()) or {}
            if not isinstance(loaded, dict):
                raise ValueError(f"Config must be a YAML mapping: {config_path}")
            data.update(loaded)

        # Env vars override YAML for easy gateway/systemd config.
        if os.getenv("CLOAK_BROWSER_CDP_URL"):
            data["cdp_url"] = os.getenv("CLOAK_BROWSER_CDP_URL")
        if os.getenv("CLOAK_BROWSER_EXECUTABLE"):
            data["executable_path"] = os.getenv("CLOAK_BROWSER_EXECUTABLE")
        if os.getenv("CLOAK_BROWSER_SCREENSHOTS_DIR"):
            data["screenshots_dir"] = os.getenv("CLOAK_BROWSER_SCREENSHOTS_DIR")
        if os.getenv("CLOAK_BROWSER_TIMEOUT_MS"):
            data["default_timeout_ms"] = int(os.getenv("CLOAK_BROWSER_TIMEOUT_MS", "10000"))
        if os.getenv("CLOAK_BROWSER_LAUNCH") is not None:
            data["launch_when_no_cdp"] = _env_bool("CLOAK_BROWSER_LAUNCH", False)
        if os.getenv("CLOAK_BROWSER_HEADLESS") is not None:
            data["headless"] = _env_bool("CLOAK_BROWSER_HEADLESS", False)

        cfg = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        Path(cfg.screenshots_dir).expanduser().mkdir(parents=True, exist_ok=True)
        return cfg

    def safe_dict(self) -> dict[str, Any]:
        return {
            "cdp_url": self.cdp_url,
            "launch_when_no_cdp": self.launch_when_no_cdp,
            "headless": self.headless,
            "executable_path": self.executable_path,
            "browser_args": self.browser_args,
            "default_timeout_ms": self.default_timeout_ms,
            "screenshots_dir": self.screenshots_dir,
        }
