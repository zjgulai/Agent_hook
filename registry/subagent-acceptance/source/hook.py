#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys


SHALLOW_PHRASES = [
    re.compile(r"\bI think it'?s done\b", re.I),
    re.compile(r"\b(should|might|likely) work\b", re.I),
    re.compile(r"\bnot fully tested\b", re.I),
    re.compile(r"\bdid not run\b", re.I),
    re.compile(r"\bdidn'?t run the tests?\b", re.I),
]

INCOMPLETE_MARKERS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bplaceholder\b", re.I),
    re.compile(r"\bstub\b", re.I),
]


def analyze(report):
    flags = []
    for pat in SHALLOW_PHRASES:
        m = pat.search(report)
        if m:
            flags.append(f"shallow-completion: {m.group(0)!r}")
    for pat in INCOMPLETE_MARKERS:
        if pat.search(report):
            flags.append(f"incomplete-marker: {pat.pattern}")
    return {"flags": flags, "ok": len(flags) == 0}


def hook(event):
    if event.get("event") != "SubagentStop":
        return None
    report = event.get("report") or event.get("summary") or event.get("output") or ""
    if not isinstance(report, str):
        report = str(report)
    if not report:
        return None
    result = analyze(report)
    if result["ok"]:
        return {"acceptance": "ok"}
    return {
        "acceptance": "needs-review",
        "flags": result["flags"],
        "advice": "Subagent report contains warning patterns. Verify before accepting result.",
    }


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
