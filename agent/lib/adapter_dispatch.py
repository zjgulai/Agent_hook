from __future__ import annotations

from . import adapter_codex, adapter_cursor, adapter_kimi, adapter_opencode
from .manifest import Manifest

ADAPTERS = {
    "opencode": adapter_opencode,
    "codex": adapter_codex,
    "cursor": adapter_cursor,
    "kimi": adapter_kimi,
}


def _resolve(client: str):
    if client not in ADAPTERS:
        raise ValueError(f"unknown client {client!r}; expected one of {sorted(ADAPTERS)}")
    return ADAPTERS[client]


def install(m: Manifest, client: str) -> dict:
    return _resolve(client).install(m)


def uninstall(name: str, client: str) -> dict:
    return _resolve(client).uninstall(name)


def list_installed(client: str) -> list[dict]:
    return _resolve(client).list_installed()


def status_for(name: str, client: str) -> str:
    return _resolve(client).status_for(name)


def install_all_clients(m: Manifest, clients: list[str] | None = None) -> list[dict]:
    targets = clients or list(ADAPTERS.keys())
    out = []
    for c in targets:
        try:
            out.append(_resolve(c).install(m))
        except Exception as e:
            out.append({"client": c, "name": m.name, "error": str(e)})
    return out
