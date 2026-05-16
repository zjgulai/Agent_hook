from __future__ import annotations

import datetime as _dt
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

ANCHOR = "managed-by: agent-hook"


def backup_file(path: Path):
    if not path.exists():
        return None
    ts = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak.{ts}")
    shutil.copy2(path, backup)
    return backup


def prune_backups(path: Path, keep: int = 5) -> int:
    parent = path.parent
    if not parent.exists():
        return 0
    pattern = path.name + ".bak.*"
    backups = sorted(parent.glob(pattern), key=lambda p: p.name, reverse=True)
    pruned = 0
    for b in backups[keep:]:
        b.unlink()
        pruned += 1
    return pruned


def hook_source_path(name: str) -> Path:
    return REPO_ROOT / "registry" / name / "source" / "hook.py"


def python_executable() -> str:
    return sys.executable or "python3"
