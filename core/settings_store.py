"""Cross-platform settings persistence.

Stores config as JSON in the OS-appropriate app-data directory:
  Windows: %APPDATA%/ZombieSlayer/settings.json
  macOS:   ~/Library/Application Support/ZombieSlayer/settings.json
  Linux:   ~/.config/ZombieSlayer/settings.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

APP_NAME = "ZombieSlayer"

DEFAULT_SETTINGS: Dict[str, Any] = {
    "authorized_ips": [],
    "ports_to_scan": [],
    "options": {
        "logging": True,
        "authentication": True,
        "encryption": False,
        "input_validation": True,
        "rate_limiting": False,
        "automated_response": False,
        "regular_updates": False,
        "testing": False,
        "permissions": False,
        "alerting": True,
        "suspicious_processes": False,
        "resource_intensive_activities": False,
        "dos_attacks": False,
        "data_exfiltration": False,
        "malware_detection": False,
        "unauthorized_access_attempts": True,
        "system_integrity_checks": False,
        "security_patch_management": False,
    },
}


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home()))
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    # Linux and other unix-likes
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / APP_NAME


def config_path() -> Path:
    return config_dir() / "settings.json"


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_path()
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._data = {**DEFAULT_SETTINGS, **loaded}
                self._data["options"] = {
                    **DEFAULT_SETTINGS["options"],
                    **loaded.get("options", {}),
                }
            except (json.JSONDecodeError, OSError):
                self._data = dict(DEFAULT_SETTINGS)
        else:
            self._data = dict(DEFAULT_SETTINGS)
            self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get_option(self, name: str) -> bool:
        return bool(self._data.get("options", {}).get(name, False))

    def set_option(self, name: str, value: bool) -> None:
        self._data.setdefault("options", {})[name] = bool(value)

    @property
    def all_options(self) -> Dict[str, bool]:
        return dict(self._data.get("options", {}))
