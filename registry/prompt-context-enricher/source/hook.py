#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd, cwd=None, timeout=3):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return (proc.stdout or "").strip()
    except Exception:
        return ""


def enrich(cwd, prompt):
    context_lines = []

    branch = _run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"])
    if branch and branch != "HEAD":
        context_lines.append(f"git branch: {branch}")

    last_commit = _run(["git", "-C", cwd, "log", "-1", "--pretty=%h %s"])
    if last_commit:
        context_lines.append(f"last commit: {last_commit}")

    diff_stat = _run(["git", "-C", cwd, "diff", "--stat", "--no-color"])
    if diff_stat:
        lines = diff_stat.splitlines()
        if len(lines) > 6:
            context_lines.append(f"working tree: {lines[-1]}")
        else:
            context_lines.append(f"working tree: {' | '.join(l.strip() for l in lines[:5])}")

    plans_dir = Path(cwd) / ".sisyphus" / "plans"
    if plans_dir.exists():
        latest_plans = sorted(plans_dir.glob("*.md"))[:3]
        if latest_plans:
            context_lines.append(f"active plans: {', '.join(p.name for p in latest_plans)}")

    if not context_lines:
        return {"prefix": None}
    prefix = "\n".join([
        "<project-context>",
        *(f"  {line}" for line in context_lines),
        "</project-context>",
        "",
    ])
    return {"prefix": prefix}


def hook(event):
    if event.get("event") != "UserPromptSubmit":
        return None
    if os.environ.get("AGENT_HOOK_SKIP_PROMPT_ENRICH") == "1":
        return None
    cwd = event.get("cwd") or os.getcwd()
    prompt = event.get("prompt") or event.get("text") or ""
    result = enrich(cwd, prompt)
    if not result.get("prefix"):
        return None
    return {"prepend": result["prefix"]}


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}
    result = hook(event)
    if result is not None:
        print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
