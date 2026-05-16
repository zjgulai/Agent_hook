from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib as _toml_r
else:
    import tomli as _toml_r
import tomli_w

from .adapter_common import backup_file, hook_source_path, prune_backups, python_executable
from .manifest import Manifest

CLIENT_NAME = "kimi"
CONFIG_PATH = Path.home() / ".kimi" / "config.toml"
MANAGED_REGISTRY = Path.home() / ".kimi" / ".agent-hook-managed.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as f:
        return _toml_r.load(f)


def _save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("wb") as f:
        tomli_w.dump(data, f)


def _load_registry() -> dict:
    if not MANAGED_REGISTRY.exists():
        return {}
    with MANAGED_REGISTRY.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_registry(data: dict) -> None:
    MANAGED_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    with MANAGED_REGISTRY.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def install(m: Manifest) -> dict:
    compat = m.compatibility.get("kimi")
    if compat == "unsupported":
        return {"client": CLIENT_NAME, "name": m.name, "skipped": True, "reason": "kimi=unsupported"}

    src = hook_source_path(m.name)
    if not src.exists():
        raise FileNotFoundError(f"hook source not found at {src}")

    backup = backup_file(CONFIG_PATH)
    data = _load_config()
    hooks = data.get("hooks") or []
    if not isinstance(hooks, list):
        hooks = []
    hooks = [h for h in hooks if not (isinstance(h, dict) and h.get("name") == m.name)]
    entry = {
        "name": m.name,
        "events": list(m.hook_events),
        "matchers": list(m.matchers),
        "command": [python_executable(), str(src)],
        "managed_by": "agent-hook",
    }
    hooks.append(entry)
    data["hooks"] = hooks
    _save_config(data)
    prune_backups(CONFIG_PATH, keep=5)

    reg = _load_registry()
    reg[m.name] = {
        "installed_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "manifest_version": m.version,
    }
    _save_registry(reg)

    return {
        "client": CLIENT_NAME, "name": m.name,
        "config": str(CONFIG_PATH),
        "backup": str(backup) if backup else None,
        "note": "added to kimi config.toml hooks=[...] (kimi-side enforcement depends on CLI support)",
    }


def uninstall(name: str) -> dict:
    if not CONFIG_PATH.exists():
        return {"client": CLIENT_NAME, "name": name, "removed": False, "reason": "config-missing"}
    reg = _load_registry()
    if name not in reg:
        return {"client": CLIENT_NAME, "name": name, "removed": False, "reason": "not-managed-by-agent-hook"}
    backup = backup_file(CONFIG_PATH)
    data = _load_config()
    hooks = [h for h in (data.get("hooks") or []) if not (isinstance(h, dict) and h.get("name") == name)]
    data["hooks"] = hooks
    _save_config(data)
    prune_backups(CONFIG_PATH, keep=5)
    del reg[name]
    _save_registry(reg)
    return {"client": CLIENT_NAME, "name": name, "removed": True, "backup": str(backup) if backup else None}


def list_installed() -> list[dict]:
    data = _load_config()
    reg = _load_registry()
    out = []
    for h in (data.get("hooks") or []):
        if not isinstance(h, dict):
            continue
        n = h.get("name")
        if not n:
            continue
        out.append({"name": n, "managed": n in reg, "events": h.get("events", [])})
    return out


def status_for(name: str) -> str:
    for row in list_installed():
        if row["name"] == name:
            return "managed" if row["managed"] else "external"
    return "absent"
