#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FORMATTERS = {
    ".js":   [["prettier", "--write"], ["biome", "format", "--write"]],
    ".jsx":  [["prettier", "--write"], ["biome", "format", "--write"]],
    ".ts":   [["prettier", "--write"], ["biome", "format", "--write"]],
    ".tsx":  [["prettier", "--write"], ["biome", "format", "--write"]],
    ".json": [["prettier", "--write"], ["biome", "format", "--write"]],
    ".md":   [["prettier", "--write"]],
    ".yaml": [["prettier", "--write"]],
    ".yml":  [["prettier", "--write"]],
    ".css":  [["prettier", "--write"]],
    ".html": [["prettier", "--write"]],
    ".py":   [["ruff", "format"], ["black", "-q"]],
    ".go":   [["gofmt", "-w"]],
    ".rs":   [["rustfmt"]],
    ".sh":   [["shfmt", "-w"]],
}


def _find_formatter(suffix: str) -> list[str] | None:
    for cmd in FORMATTERS.get(suffix, []):
        if shutil.which(cmd[0]):
            return cmd
    return None


def _run(cmd: list[str], file: str, timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd + [file],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, (proc.stderr or proc.stdout).strip()
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"
    except Exception as e:
        return 1, str(e)


def hook(event: dict) -> dict | None:
    tool = event.get("tool", "")
    if tool not in {"Write", "Edit", "MultiEdit"}:
        return None
    if os.environ.get("AGENT_HOOK_SKIP_FORMAT") == "1":
        return None

    params = event.get("parameters") or event.get("args") or {}
    files: list[str] = []
    for key in ("filePath", "file_path", "path"):
        v = params.get(key)
        if isinstance(v, str):
            files.append(v)
    if isinstance(params.get("edits"), list):
        for ed in params["edits"]:
            if isinstance(ed, dict) and isinstance(ed.get("filePath"), str):
                files.append(ed["filePath"])

    timeout = int(os.environ.get("AGENT_HOOK_FORMAT_TIMEOUT", "10"))

    results = []
    for f in files:
        p = Path(f)
        if not p.exists() or not p.is_file():
            results.append({"file": f, "status": "skip", "reason": "not-a-regular-file"})
            continue
        formatter = _find_formatter(p.suffix)
        if formatter is None:
            results.append({"file": f, "status": "skip", "reason": f"no formatter for {p.suffix}"})
            continue
        rc, msg = _run(formatter, str(p), timeout)
        results.append({
            "file": f,
            "status": "ok" if rc == 0 else "failed",
            "formatter": formatter[0],
            "rc": rc,
            "msg": msg[:200] if msg else None,
        })

    return {"formatted": results} if results else None


def main() -> int:
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
