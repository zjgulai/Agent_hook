"""Shared manifest schema for Agent_skills / Agent_hook / Agent_mcp.

This file is vendored (copied) into all three repos at agent/lib/manifest.py.
Single-source-of-truth lives in Agent_hook (canonical). Other two repos must
keep their copies byte-identical and run `agent/lib/sync_manifest_lib.sh` to
copy any update.

Public API:
    load_manifest(path) -> Manifest      Load and validate a single manifest
    validate_manifest(data, kind) -> []  Return list of error strings (empty=ok)
    iter_registry(root) -> Iter[Manifest] Yield all manifests under root/registry/
    Manifest                              Dataclass with .name/.kind/.compat etc.

Schema (kind ∈ {skill, hook, mcp}):

    kind:           one of skill|hook|mcp                          REQUIRED
    name:           kebab-case-name                                REQUIRED
    version:        semver string                                  REQUIRED
    description:    >= 20 chars (WHAT + WHEN)                      REQUIRED
    domain:         meta|code-quality|desktop|founder|frontend|research|data|ops|general  REQUIRED
    priority:       P0|P1|P2                                       REQUIRED
    compatibility:  dict with keys opencode/codex/cursor/kimi      REQUIRED
                    each value ∈ {native, adapter, unsupported}
    source:                                                        REQUIRED
        type:       local|external|git|npm|pypi
        path:       (local|external)
        ref:        (git)
        package:    (npm|pypi)
    requires:                                                      OPTIONAL
        binaries:   [str]   executables that must be on PATH
        env:        [str]   environment variables names (no values!)
    triggers:       [str]                                          OPTIONAL (skill/hook)
    hook_events:    [PreToolUse|PostToolUse|UserPromptSubmit|SessionStart|
                     Stop|SubagentStop|Notification|PreCompact]    REQUIRED if kind=hook
    matchers:       [str regex]                                    OPTIONAL (hook)
    mcp_command:    [str]                                          REQUIRED if kind=mcp
    links:                                                         OPTIONAL
        upstream:   url
        docs:       url
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml

KINDS = {"skill", "hook", "mcp"}
PRIORITIES = {"P0", "P1", "P2"}
DOMAINS = {
    "meta",
    "code-quality",
    "desktop",
    "founder",
    "frontend",
    "research",
    "data",
    "ops",
    "general",
}
CLIENTS = {"opencode", "codex", "cursor", "kimi"}
COMPAT_VALUES = {"native", "adapter", "unsupported"}
HOOK_EVENTS = {
    "PreToolUse",
    "PostToolUse",
    "UserPromptSubmit",
    "SessionStart",
    "Stop",
    "SubagentStop",
    "Notification",
    "PreCompact",
}
SOURCE_TYPES = {"local", "external", "git", "npm", "pypi"}

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.\-]+)?$")
TOKEN_LITERAL_RE = re.compile(r"(ghp_|gho_|sk-[a-zA-Z0-9]{10,}|AIza[0-9A-Za-z\-_]{20,})")


@dataclass
class Manifest:
    path: Path
    raw: dict
    name: str
    kind: str
    version: str
    description: str
    domain: str
    priority: str
    compatibility: dict
    source: dict
    requires: dict = field(default_factory=dict)
    triggers: list = field(default_factory=list)
    hook_events: list = field(default_factory=list)
    matchers: list = field(default_factory=list)
    mcp_command: list = field(default_factory=list)
    links: dict = field(default_factory=dict)


def validate_manifest(data: Any, *, expected_kind: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"manifest root must be a dict, got {type(data).__name__}"]

    def req(key: str):
        if key not in data:
            errors.append(f"missing required key: {key}")

    for k in ("kind", "name", "version", "description", "domain", "priority",
              "compatibility", "source"):
        req(k)

    kind = data.get("kind")
    if kind not in KINDS:
        errors.append(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    if expected_kind and kind != expected_kind:
        errors.append(f"expected kind={expected_kind}, got {kind!r}")

    name = data.get("name", "")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append(f"name must be kebab-case [a-z][a-z0-9-]{{1,63}}, got {name!r}")

    version = data.get("version", "")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f"version must be semver, got {version!r}")

    desc = data.get("description", "")
    if not isinstance(desc, str) or len(desc.strip()) < 20:
        errors.append(f"description too short (need >= 20 chars), got {len(str(desc))}")

    if data.get("domain") not in DOMAINS:
        errors.append(f"domain must be one of {sorted(DOMAINS)}, got {data.get('domain')!r}")
    if data.get("priority") not in PRIORITIES:
        errors.append(f"priority must be one of {sorted(PRIORITIES)}, got {data.get('priority')!r}")

    compat = data.get("compatibility")
    if not isinstance(compat, dict):
        errors.append("compatibility must be a dict")
    else:
        missing_clients = CLIENTS - set(compat.keys())
        if missing_clients:
            errors.append(f"compatibility missing clients: {sorted(missing_clients)}")
        for c, v in compat.items():
            if c not in CLIENTS:
                errors.append(f"compatibility has unknown client {c!r}")
            if v not in COMPAT_VALUES:
                errors.append(f"compatibility.{c} must be one of {sorted(COMPAT_VALUES)}, got {v!r}")

    src = data.get("source")
    if not isinstance(src, dict):
        errors.append("source must be a dict")
    else:
        if src.get("type") not in SOURCE_TYPES:
            errors.append(f"source.type must be one of {sorted(SOURCE_TYPES)}, got {src.get('type')!r}")
        st = src.get("type")
        if st in {"local", "external"} and not src.get("path"):
            errors.append(f"source.path required for type={st}")
        if st == "git" and not src.get("ref"):
            errors.append("source.ref required for type=git")
        if st in {"npm", "pypi"} and not src.get("package"):
            errors.append(f"source.package required for type={st}")

    if kind == "hook":
        evts = data.get("hook_events", [])
        if not isinstance(evts, list) or not evts:
            errors.append("hook_events required (non-empty list) when kind=hook")
        else:
            for e in evts:
                if e not in HOOK_EVENTS:
                    errors.append(f"hook_events item {e!r} not in {sorted(HOOK_EVENTS)}")
        matchers = data.get("matchers", [])
        if matchers and not isinstance(matchers, list):
            errors.append("matchers must be a list of regex strings")

    if kind == "mcp":
        cmd = data.get("mcp_command")
        if not isinstance(cmd, list) or not cmd:
            errors.append("mcp_command required (non-empty list) when kind=mcp")
        elif not all(isinstance(x, str) for x in cmd):
            errors.append("mcp_command entries must be strings")

    requires = data.get("requires", {})
    if requires and not isinstance(requires, dict):
        errors.append("requires must be a dict")
    else:
        for sub in ("binaries", "env"):
            v = requires.get(sub, [])
            if v and not isinstance(v, list):
                errors.append(f"requires.{sub} must be a list")
            elif isinstance(v, list) and not all(isinstance(x, str) for x in v):
                errors.append(f"requires.{sub} items must be strings")

    serialized = yaml.safe_dump(data, allow_unicode=True)
    m = TOKEN_LITERAL_RE.search(serialized)
    if m:
        errors.append(
            f"manifest appears to contain a literal secret near {m.group(0)!r}; "
            "use requires.env: [VAR_NAME] instead"
        )

    return errors


def load_manifest(path: str | Path, *, expected_kind: str | None = None) -> Manifest:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    errors = validate_manifest(data, expected_kind=expected_kind)
    if errors:
        msg = "\n  - ".join([f"manifest {p} invalid:"] + errors)
        raise ValueError(msg)
    return Manifest(
        path=p,
        raw=data,
        name=data["name"],
        kind=data["kind"],
        version=data["version"],
        description=data["description"],
        domain=data["domain"],
        priority=data["priority"],
        compatibility=data["compatibility"],
        source=data["source"],
        requires=data.get("requires") or {},
        triggers=data.get("triggers") or [],
        hook_events=data.get("hook_events") or [],
        matchers=data.get("matchers") or [],
        mcp_command=data.get("mcp_command") or [],
        links=data.get("links") or {},
    )


def iter_registry(repo_root: str | Path, *, expected_kind: str | None = None) -> Iterator[Manifest]:
    root = Path(repo_root) / "registry"
    if not root.exists():
        return
    for manifest_path in sorted(root.glob("*/manifest.yaml")):
        yield load_manifest(manifest_path, expected_kind=expected_kind)
