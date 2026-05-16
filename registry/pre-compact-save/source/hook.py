#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path


def _gather_snapshot(cwd):
    snapshot = {"timestamp": _dt.datetime.now().isoformat(timespec="seconds"), "cwd": cwd}

    def _git(args):
        try:
            r = subprocess.run(["git", "-C", cwd] + args, capture_output=True, text=True, timeout=3)
            return (r.stdout or "").strip()
        except Exception:
            return ""

    snapshot["branch"] = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    snapshot["last_commit"] = _git(["log", "-1", "--pretty=%h %s (%ar)"])
    diff_stat = _git(["diff", "--stat"])
    if diff_stat:
        snapshot["working_tree"] = diff_stat.splitlines()[-1]

    plans_dir = Path(cwd) / ".sisyphus" / "plans"
    if plans_dir.exists():
        snapshot["plans"] = sorted(p.name for p in plans_dir.glob("*.md"))

    return snapshot


def hook(event):
    if event.get("event") != "PreCompact":
        return None
    cwd = event.get("cwd") or os.getcwd()
    save_dir = Path(cwd) / ".sisyphus" / "snapshots"
    save_dir.mkdir(parents=True, exist_ok=True)
    snapshot = _gather_snapshot(cwd)
    snapshot["compact_reason"] = event.get("reason", "manual-or-auto")
    fname = f"pre-compact-{_dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    path = save_dir / fname
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return {"saved_to": str(path), "fields": sorted(snapshot.keys())}


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
