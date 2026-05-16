from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from .adapter_dispatch import ADAPTERS, install_all_clients, uninstall as adapter_uninstall
from .manifest import iter_registry, load_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _format_table(rows, cols):
    if not rows:
        return "(empty)"
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    head = "  ".join(c.ljust(widths[c]) for c in cols)
    sep = "  ".join("-" * widths[c] for c in cols)
    body = "\n".join("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols) for r in rows)
    return f"{head}\n{sep}\n{body}"


def cmd_list(args):
    manifests = list(iter_registry(REPO_ROOT, expected_kind="hook"))
    rows = []
    for m in manifests:
        row = {
            "name": m.name,
            "priority": m.priority,
            "events": ",".join(m.hook_events),
        }
        for c in ADAPTERS:
            row[c] = ADAPTERS[c].status_for(m.name)
        rows.append(row)
    print(_format_table(rows, ["name", "priority", "events"] + list(ADAPTERS.keys())))
    return 0


def cmd_install(args):
    p = REPO_ROOT / "registry" / args.name / "manifest.yaml"
    if not p.exists():
        print(f"ERROR: registry/{args.name}/manifest.yaml not found", file=sys.stderr)
        return 2
    m = load_manifest(p, expected_kind="hook")
    targets = list(ADAPTERS.keys()) if args.client == "all" else [args.client]
    results = install_all_clients(m, clients=targets)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


def cmd_uninstall(args):
    targets = list(ADAPTERS.keys()) if args.client == "all" else [args.client]
    results = []
    for c in targets:
        try:
            results.append(adapter_uninstall(args.name, c))
        except Exception as e:
            results.append({"client": c, "error": str(e)})
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


def cmd_doctor(args):
    issues = 0
    print("== schema ==")
    for m in iter_registry(REPO_ROOT, expected_kind="hook"):
        print(f"  ok {m.name} v{m.version}")

    print("\n== source files (executable, no 3rd-party imports) ==")
    forbidden_imports = ("import yaml", "import requests", "import httpx", "import click")
    for m in iter_registry(REPO_ROOT, expected_kind="hook"):
        src = REPO_ROOT / "registry" / m.name / "source" / "hook.py"
        ok = src.exists()
        if not ok:
            issues += 1
            print(f"  MISSING {m.name}: {src}")
            continue
        execp = bool(os.access(src, os.X_OK))
        text = src.read_text(encoding="utf-8", errors="ignore")
        bad = [i for i in forbidden_imports if i in text]
        flag = "ok" if execp and not bad else "WARN"
        if not execp or bad:
            issues += 1
        print(f"  {flag:5s} {m.name:30s} exec={execp}  bad-imports={bad or 'none'}")

    print("\n== required binaries ==")
    for m in iter_registry(REPO_ROOT, expected_kind="hook"):
        for b in m.requires.get("binaries", []):
            f = shutil.which(b)
            mark = "ok" if f else "MISSING"
            if not f:
                issues += 1
            print(f"  {mark:7s} {m.name:30s} -> {b}")

    print("\n== client install status ==")
    for c, mod in ADAPTERS.items():
        rows = mod.list_installed()
        managed = [r["name"] for r in rows if r.get("managed")]
        print(f"  {c:8s}: {len(managed)} managed by agent-hook ({', '.join(managed) if managed else 'none'})")

    return 0 if issues == 0 else 1


def cmd_show(args):
    p = REPO_ROOT / "registry" / args.name / "manifest.yaml"
    if not p.exists():
        print(f"ERROR: registry/{args.name}/manifest.yaml not found", file=sys.stderr)
        return 2
    m = load_manifest(p, expected_kind="hook")
    print(json.dumps(m.raw, indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agent-hook", description="Manage local hooks across opencode/codex/cursor/kimi.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List all registered hooks and their install status across clients.")
    p_list.set_defaults(func=cmd_list)

    p_install = sub.add_parser("install", help="Install a hook to a client (or all).")
    p_install.add_argument("name")
    p_install.add_argument("--client", choices=list(ADAPTERS.keys()) + ["all"], default="all")
    p_install.set_defaults(func=cmd_install)

    p_uninstall = sub.add_parser("uninstall", help="Uninstall a hook from a client (or all).")
    p_uninstall.add_argument("name")
    p_uninstall.add_argument("--client", choices=list(ADAPTERS.keys()) + ["all"], default="all")
    p_uninstall.set_defaults(func=cmd_uninstall)

    p_doctor = sub.add_parser("doctor", help="Health check.")
    p_doctor.set_defaults(func=cmd_doctor)

    p_show = sub.add_parser("show", help="Print manifest.")
    p_show.add_argument("name")
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
