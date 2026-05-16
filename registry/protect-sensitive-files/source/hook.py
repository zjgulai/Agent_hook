#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

EXACT_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.staging",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "service-account.json",
    ".aws/credentials",
    ".kube/config",
    "id_rsa",
    "id_ed25519",
    "auth.json",
}

PATTERNS = [
    re.compile(r"(^|/)\.env(\..+)?$"),
    re.compile(r"(^|/)secrets?\.(json|yaml|yml|toml)$"),
    re.compile(r"(^|/)\.git/(?!hooks/).*"),
    re.compile(r"(^|/)node_modules/"),
    re.compile(r"\.pem$"),
    re.compile(r"\.key$"),
    re.compile(r"\.p12$"),
    re.compile(r"\.pfx$"),
    re.compile(r"(^|/)migrations?/.+\.sql$"),
]


def _is_sensitive(path_str: str) -> tuple[bool, str | None]:
    path = Path(path_str)
    name = path.name
    if name in EXACT_NAMES:
        return True, f"matches exact name {name!r}"
    s = str(path)
    for pat in PATTERNS:
        if pat.search(s):
            return True, f"matches pattern {pat.pattern!r}"
    return False, None


def hook(event: dict) -> dict | None:
    tool = event.get("tool", "")
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return None

    candidates: list[str] = []
    params = event.get("parameters") or event.get("args") or {}
    for key in ("filePath", "file_path", "path"):
        if key in params and isinstance(params[key], str):
            candidates.append(params[key])
    if isinstance(params.get("edits"), list):
        for ed in params["edits"]:
            if isinstance(ed, dict) and isinstance(ed.get("filePath"), str):
                candidates.append(ed["filePath"])

    overrides = {p.strip() for p in os.environ.get("AGENT_HOOK_ALLOW_SENSITIVE", "").split(":") if p.strip()}

    for c in candidates:
        if c in overrides:
            continue
        bad, reason = _is_sensitive(c)
        if bad:
            return {
                "block": True,
                "reason": f"protect-sensitive-files: blocked write to {c!r} — {reason}. "
                          f"Override via AGENT_HOOK_ALLOW_SENSITIVE=path1:path2 if intentional.",
            }
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}

    result = hook(event)
    if result is None:
        return 0
    if result.get("block"):
        print(json.dumps(result), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
