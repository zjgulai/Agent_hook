from __future__ import annotations

import datetime as _dt
from pathlib import Path

from .adapter_common import backup_file, prune_backups
from .manifest import Manifest

CLIENT_NAME = "cursor"
RULES_DIR = Path.home() / ".cursor" / "rules"

DEGRADE_TEMPLATES = {
    "protect-sensitive-files": """---
name: agent-hook-protect-sensitive-files
description: Soft rule (Cursor cannot enforce hooks). NEVER write to sensitive files.
alwaysApply: true
---

# Sensitive File Protection (degraded from agent-hook)

Cursor has no native PreToolUse hook. The following is a strong soft constraint:

**DO NOT WRITE TO**:
- `.env`, `.env.*`, `.npmrc`, `.pypirc`
- `credentials`, `credentials.json`, `service-account.json`, `auth.json`
- `~/.aws/credentials`, `~/.kube/config`
- SSH keys (`id_rsa`, `id_ed25519`)
- Any file matching `*.pem`, `*.key`, `*.p12`, `*.pfx`
- Already-applied SQL migrations (`migrations/*.sql`)
- Anything inside `.git/` (except `.git/hooks/`)

If the user explicitly asks to edit one of these, ask for confirmation first.
""",
    "guard-bash": """---
name: agent-hook-guard-bash
description: Soft rule. NEVER run dangerous shell commands without explicit user confirmation.
alwaysApply: true
---

# Dangerous Bash Guard (degraded from agent-hook)

NEVER execute (without explicit user confirmation):
- `rm -rf` (any form), `sudo rm`
- `git reset --hard`, `git push --force`, `git push -f`, `git clean -f*`
- `git checkout -- .` (discards all working changes)
- `curl ... | bash`, `wget ... | sh`
- `mkfs.*`, `dd if=... of=/dev/sd*`
- `chmod -R 777`
- SQL: `DROP TABLE`, `DROP DATABASE`, `TRUNCATE TABLE`
- Fork bombs, redirects to raw devices
""",
    "session-context-injector": """---
name: agent-hook-session-context-injector
description: Soft rule. At session start, gather and acknowledge project context.
alwaysApply: true
---

# Session Context Awareness (degraded from agent-hook)

Before responding to the user's first request:
1. Read `AGENTS.md` / `CLAUDE.md` / `README.md` if present
2. Note the current git branch and last commit
3. Check `.sisyphus/plans/` for active plans
4. Surface this context concisely if relevant
""",
}

DEGRADABLE = set(DEGRADE_TEMPLATES.keys())


def _rule_path(name: str) -> Path:
    return RULES_DIR / f"agent-hook-{name}.mdc"


def install(m: Manifest) -> dict:
    compat = m.compatibility.get("cursor")
    if compat == "unsupported":
        return {"client": CLIENT_NAME, "name": m.name, "skipped": True, "reason": "cursor=unsupported"}
    if m.name not in DEGRADABLE:
        return {
            "client": CLIENT_NAME, "name": m.name, "skipped": True,
            "reason": f"no degradation template for {m.name} (cursor cannot enforce, only soft-rule)",
        }
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    rule = _rule_path(m.name)
    backup = backup_file(rule)
    rule.write_text(DEGRADE_TEMPLATES[m.name], encoding="utf-8")
    prune_backups(rule, keep=5)
    return {
        "client": CLIENT_NAME, "name": m.name,
        "rule": str(rule),
        "backup": str(backup) if backup else None,
        "note": "degraded to soft rule (no enforcement)",
    }


def uninstall(name: str) -> dict:
    rule = _rule_path(name)
    if not rule.exists():
        return {"client": CLIENT_NAME, "name": name, "removed": False, "reason": "not-found"}
    text = rule.read_text(encoding="utf-8")
    if f"agent-hook-{name}" not in text:
        return {"client": CLIENT_NAME, "name": name, "removed": False, "reason": "not-managed-by-agent-hook"}
    backup = backup_file(rule)
    rule.unlink()
    return {"client": CLIENT_NAME, "name": name, "removed": True, "backup": str(backup) if backup else None}


def list_installed() -> list[dict]:
    if not RULES_DIR.exists():
        return []
    out = []
    for p in sorted(RULES_DIR.glob("agent-hook-*.mdc")):
        out.append({"name": p.stem.replace("agent-hook-", ""), "managed": True, "rule": str(p)})
    return out


def status_for(name: str) -> str:
    for row in list_installed():
        if row["name"] == name:
            return "managed"
    return "absent"
