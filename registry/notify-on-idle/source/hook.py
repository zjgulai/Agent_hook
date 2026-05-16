#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys


def _notify_macos(title, msg):
    if not shutil.which("osascript"):
        return False
    safe_title = title.replace('"', '\\"')
    safe_msg = msg.replace('"', '\\"')
    try:
        proc = subprocess.run(
            ["osascript", "-e", f'display notification "{safe_msg}" with title "{safe_title}"'],
            capture_output=True, text=True, timeout=3,
        )
        return proc.returncode == 0
    except Exception:
        return False


def hook(event):
    if event.get("event") != "Notification":
        return None
    if os.environ.get("AGENT_HOOK_SKIP_NOTIFY") == "1":
        return None
    title = event.get("title") or "AI Agent"
    message = event.get("message") or event.get("text") or "Idle / needs input"
    if len(message) > 200:
        message = message[:200] + "..."
    success = _notify_macos(title, message)
    return {"notified": success, "method": "osascript" if success else "none"}


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
