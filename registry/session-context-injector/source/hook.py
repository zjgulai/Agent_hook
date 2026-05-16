#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: str | None = None, timeout: int = 3) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return (proc.stdout or "").strip()
    except Exception:
        return ""


def gather(cwd: str) -> dict:
    info: dict = {"cwd": cwd}

    branch = _run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"])
    if branch:
        info["git_branch"] = branch
    last_commit = _run(["git", "-C", cwd, "log", "-1", "--pretty=%h %s (%ar)"])
    if last_commit:
        info["git_last_commit"] = last_commit
    dirty = _run(["git", "-C", cwd, "status", "--short"])
    if dirty:
        info["git_dirty_count"] = len(dirty.splitlines())

    for fname in ("AGENTS.md", "CLAUDE.md", "README.md"):
        p = Path(cwd) / fname
        if p.exists() and p.is_file():
            try:
                info.setdefault("project_docs", []).append(str(p))
            except Exception:
                pass

    todo_dir = Path(cwd) / ".sisyphus" / "plans"
    if todo_dir.exists():
        info["sisyphus_plans"] = [str(p) for p in sorted(todo_dir.glob("*.md"))]

    info["python"] = sys.version.split()[0]
    info["platform"] = sys.platform
    return info


def hook(event: dict) -> dict | None:
    cwd = event.get("cwd") or os.getcwd()
    if event.get("event") == "SessionStart" or event.get("matcher") == "startup" or "matcher" not in event:
        ctx = gather(cwd)
        return {"context": ctx}
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}
    result = hook(event)
    if result is not None:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
