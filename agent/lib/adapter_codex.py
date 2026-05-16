from __future__ import annotations

from .manifest import Manifest

CLIENT_NAME = "codex"


def install(m: Manifest) -> dict:
    return {
        "client": CLIENT_NAME,
        "name": m.name,
        "skipped": True,
        "reason": "codex has no native hook concept (compatibility=unsupported)",
    }


def uninstall(name: str) -> dict:
    return {"client": CLIENT_NAME, "name": name, "removed": False, "reason": "codex unsupported (no-op)"}


def list_installed() -> list[dict]:
    return []


def status_for(name: str) -> str:
    return "n/a"
