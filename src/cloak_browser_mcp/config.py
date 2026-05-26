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
    headless: bool = False
    browser_args: list[str] = field(default_factory=list)
    cloak_stealth_args: bool = True
    cloak_humanize: bool = False
    cloak_human_preset: str = "default"
    cloak_proxy: str | None = None
    cloak_timezone: str | None = None
    cloak_locale: str | None = None
    cloak_geoip: bool = False
    default_timeout_ms: int = 10_000
    screenshots_dir: str = "~/.cloak-browser-mcp/screenshots"

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
        if os.getenv("CLOAK_BROWSER_PROXY"):
            data["cloak_proxy"] = os.getenv("CLOAK_BROWSER_PROXY")
        if os.getenv("CLOAK_BROWSER_TIMEZONE"):
            data["cloak_timezone"] = os.getenv("CLOAK_BROWSER_TIMEZONE")
        if os.getenv("CLOAK_BROWSER_LOCALE"):
            data["cloak_locale"] = os.getenv("CLOAK_BROWSER_LOCALE")
        if os.getenv("CLOAK_BROWSER_HUMAN_PRESET"):
            data["cloak_human_preset"] = os.getenv("CLOAK_BROWSER_HUMAN_PRESET")
        if os.getenv("CLOAK_BROWSER_SCREENSHOTS_DIR"):
            data["screenshots_dir"] = os.getenv("CLOAK_BROWSER_SCREENSHOTS_DIR")
        if os.getenv("CLOAK_BROWSER_TIMEOUT_MS"):
            data["default_timeout_ms"] = int(os.getenv("CLOAK_BROWSER_TIMEOUT_MS", "10000"))
        if os.getenv("CLOAK_BROWSER_HEADLESS") is not None:
            data["headless"] = _env_bool("CLOAK_BROWSER_HEADLESS", False)
        if os.getenv("CLOAK_BROWSER_STEALTH_ARGS") is not None:
            data["cloak_stealth_args"] = _env_bool("CLOAK_BROWSER_STEALTH_ARGS", True)
        if os.getenv("CLOAK_BROWSER_HUMANIZE") is not None:
            data["cloak_humanize"] = _env_bool("CLOAK_BROWSER_HUMANIZE", False)
        if os.getenv("CLOAK_BROWSER_GEOIP") is not None:
            data["cloak_geoip"] = _env_bool("CLOAK_BROWSER_GEOIP", False)

        cfg = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        Path(cfg.screenshots_dir).expanduser().mkdir(parents=True, exist_ok=True)
        return cfg

    def safe_dict(self) -> dict[str, Any]:
        return {
            "headless": self.headless,
            "browser_args": self.browser_args,
            "cloak_stealth_args": self.cloak_stealth_args,
            "cloak_humanize": self.cloak_humanize,
            "cloak_human_preset": self.cloak_human_preset,
            "cloak_proxy": "***" if self.cloak_proxy else None,
            "cloak_timezone": self.cloak_timezone,
            "cloak_locale": self.cloak_locale,
            "cloak_geoip": self.cloak_geoip,
            "default_timeout_ms": self.default_timeout_ms,
            "screenshots_dir": self.screenshots_dir,
        }
