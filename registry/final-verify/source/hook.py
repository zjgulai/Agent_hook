#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: str, timeout: int = 60) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return proc.returncode, (proc.stdout + proc.stderr).strip()[-4000:]
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"
    except FileNotFoundError:
        return 127, "binary not found"
    except Exception as e:
        return 1, str(e)


def _changed_files(cwd: str) -> list[str]:
    rc = subprocess.run(["git", "-C", cwd, "status", "--short"], capture_output=True, text=True)
    if rc.returncode != 0:
        return []
    out = []
    for line in rc.stdout.splitlines():
        line = line.rstrip()
        if len(line) < 4:
            continue
        out.append(line[3:].split(" -> ")[-1])
    return out


def _find_open_todos(cwd: str, files: list[str]) -> list[dict]:
    todos: list[dict] = []
    pat = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b[:\s]?(.{0,140})")
    for rel in files:
        p = Path(cwd) / rel
        if not p.exists() or not p.is_file():
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            m = pat.search(line)
            if m:
                todos.append({"file": rel, "line": i, "tag": m.group(1), "text": line.strip()[:200]})
                if len(todos) >= 50:
                    return todos
    return todos


def _detect_test_cmd(cwd: str) -> list[str] | None:
    if (Path(cwd) / "pyproject.toml").exists() or (Path(cwd) / "pytest.ini").exists() \
            or (Path(cwd) / "tests").exists() or (Path(cwd) / "conftest.py").exists():
        return ["python3", "-m", "pytest", "-q", "--maxfail=3"]
    pkg = Path(cwd) / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
            if isinstance(data.get("scripts"), dict) and "test" in data["scripts"]:
                return ["npm", "test", "--silent"]
        except Exception:
            pass
    if (Path(cwd) / "Cargo.toml").exists():
        return ["cargo", "test", "--quiet"]
    if (Path(cwd) / "go.mod").exists():
        return ["go", "test", "./..."]
    return None


def hook(event: dict) -> dict | None:
    cwd = event.get("cwd") or os.getcwd()
    if os.environ.get("AGENT_HOOK_SKIP_FINAL") == "1":
        return {"skipped": True, "reason": "AGENT_HOOK_SKIP_FINAL=1"}

    report: dict = {"cwd": cwd}

    files = _changed_files(cwd)
    report["changed_files_count"] = len(files)
    if files:
        report["changed_files"] = files[:30]

    open_todos = _find_open_todos(cwd, files)
    if open_todos:
        report["open_todos"] = open_todos

    test_cmd = _detect_test_cmd(cwd)
    if test_cmd and os.environ.get("AGENT_HOOK_FINAL_RUN_TESTS", "0") == "1":
        timeout = int(os.environ.get("AGENT_HOOK_FINAL_TEST_TIMEOUT", "180"))
        rc, out = _run(test_cmd, cwd, timeout=timeout)
        report["tests"] = {
            "command": " ".join(test_cmd),
            "rc": rc,
            "passed": rc == 0,
            "tail": out[-1500:],
        }
    elif test_cmd:
        report["tests"] = {
            "command": " ".join(test_cmd),
            "status": "skipped (set AGENT_HOOK_FINAL_RUN_TESTS=1 to run)",
        }

    return report


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
