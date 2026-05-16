#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys

DANGEROUS = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"), "rm -rf"),
    (re.compile(r"\brm\s+-r\b.+(/|\$HOME|~)"), "rm -r on tree"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "git reset --hard"),
    (re.compile(r"\bgit\s+push\s+.*--force\b"), "git push --force"),
    (re.compile(r"\bgit\s+push\s+.*-f\b"), "git push -f"),
    (re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f"), "git clean -f*"),
    (re.compile(r"\bgit\s+checkout\s+.*--\s+\."), "git checkout -- . (discard all)"),
    (re.compile(r"\bsudo\s+rm\b"), "sudo rm"),
    (re.compile(r":\(\)\{\s*:\|:&\s*\};:"), "fork bomb"),
    (re.compile(r"\bdd\s+if=.*of=/dev/(sd|nvme|disk)"), "dd to raw device"),
    (re.compile(r"\bmkfs\."), "mkfs.*"),
    (re.compile(r"\bchmod\s+-R\s+777\b"), "chmod -R 777"),
    (re.compile(r"\bcurl\s+.*\|\s*(sudo\s+)?(bash|sh|zsh|fish)\b"), "curl | sh"),
    (re.compile(r"\bwget\s+.*\|\s*(sudo\s+)?(bash|sh|zsh|fish)\b"), "wget | sh"),
    (re.compile(r">\s*/dev/sda\b"), "redirect to /dev/sda"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "DROP DATABASE"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "TRUNCATE TABLE"),
]

SCAN_BUDGET = 4096


def hook(event: dict) -> dict | None:
    if event.get("tool", "") != "Bash":
        return None
    cmd = ""
    params = event.get("parameters") or event.get("args") or {}
    for key in ("command", "cmd", "shell"):
        v = params.get(key)
        if isinstance(v, str):
            cmd = v
            break
    if not cmd:
        return None

    snippet = cmd[:SCAN_BUDGET]

    if os.environ.get("AGENT_HOOK_BASH_YOLO") == "1":
        return None

    for pat, label in DANGEROUS:
        if pat.search(snippet):
            return {
                "block": True,
                "reason": f"guard-bash: blocked dangerous pattern ({label}). "
                          f"Override via AGENT_HOOK_BASH_YOLO=1 if intentional.",
                "matched": label,
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
