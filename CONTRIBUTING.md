# Contributing to Agent_hook

Thanks for considering a contribution! Agent_hook is the **enforcement layer** of a three-repo system. Hooks here run in real AI CLI runtimes (opencode/cursor/kimi), so the contract is strict.

## Three-repo system

- **[Agent_skills](https://github.com/zjgulai/Agent_skills)** — methodology · 16 skills
- **[Agent_hook](https://github.com/zjgulai/Agent_hook)** (this repo) — enforcement · 9 hooks
- **[Agent_mcp](https://github.com/zjgulai/Agent_mcp)** — context · 10 MCPs

`agent/lib/manifest.py` is **byte-identical** across all three repos (md5 `b46c2f55980b9aa2ea93b87941c833e2`).

## Quick start (development)

```bash
git clone https://github.com/zjgulai/Agent_hook.git ~/project/Agent_hook
cd ~/project/Agent_hook
python3 -m pip install --user pyyaml tomli tomli_w pytest

python3 -m pytest tests/   # 81 tests must pass

./bin/agent-hook list
./bin/agent-hook doctor
```

## Hook source contract

Every `registry/<name>/source/hook.py` **MUST**:

1. **Single entry point**: `def hook(event: dict) -> dict | None`. Input is JSON via stdin; output is JSON via stdout (or empty for "no opinion").
2. **Exit code semantics**:
   - `0` — proceed (allow the tool call / no annotation)
   - `2` — **block** (PreToolUse only). The runtime refuses the action with the reason from stderr.
   - other — error
3. **Zero third-party imports** — only Python stdlib. The hook runs in 4 different client processes; we cannot rely on a shared `pip install`.
4. **Top-level docstring** explaining `event=` shape and `matcher=` triggers.
5. **Companion test**: `tests/test_<name>.py` covering happy path, block path, and edge cases (override env vars, missing fields, invalid input).

Example skeleton:

```python
"""Block writes to .env files. Triggers on PreToolUse with matcher Write|Edit."""

import json, sys

def hook(event):
    if event.get("tool", "") not in {"Write", "Edit", "MultiEdit"}:
        return None
    path = (event.get("parameters") or {}).get("filePath", "")
    if "/.env" in path or path.endswith(".env"):
        return {"block": True, "reason": f"refusing to write {path}"}
    return None

def main():
    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    r = hook(event)
    if r is None:
        return 0
    if r.get("block"):
        print(json.dumps(r), file=sys.stderr)
        return 2
    print(json.dumps(r))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Adapter contracts

Each `agent/lib/adapter_<client>.py` must:

- **opencode** — write a JS plugin to `~/.config/opencode/plugins/agent-hook-<name>.js` that follows the [opencode plugin API](https://opencode.ai/docs/plugins/): `export const PluginName = async (ctx) => ({ "tool.execute.before": ... })`. Block via `throw new Error(reason)`.
- **codex** — return `{skipped: True, reason: "codex unsupported"}` (codex has no native hook concept yet).
- **cursor** — degrade to a Rule (`.mdc` file in `~/.cursor/rules/`). Soft constraint, no enforcement.
- **kimi** — append to `~/.kimi/config.toml` `hooks=[]` array.

**Common rules**:

1. Anchor every write: `// managed-by: agent-hook · <name> · <ts>` (JS) or `# managed-by: agent-hook · <name>` (TOML).
2. Backup before mutate; `prune_backups(keep=5)` after.
3. Refuse to delete entries without our anchor.
4. Test with `monkeypatch` — never touch real `~/.config/opencode`.

## Pull request rules

1. **Tests pass** — 81+ tests, all green. Add tests for new hooks/adapters.
2. **Hook source has zero third-party imports** (linter check in `tests/test_hooks.py::test_all_hooks_zero_third_party_imports`).
3. **Manifest schema valid** — `python3 -m pytest tests/test_manifest_schema.py`.
4. **Conventional commit message** (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
5. **CHANGELOG.md updated** under `[Unreleased]`.
6. If touching `agent/lib/manifest.py` → run `bash agent/lib/sync_manifest_lib.sh` and verify all 3 repos still byte-identical.

## Adding a new hook

```bash
# 1. Scaffold via agent-kit
~/project/Agent/agent-kit/bin/agent-kit new hook my-new-hook

# This creates:
#   registry/my-new-hook/manifest.yaml
#   registry/my-new-hook/source/hook.py  (template, executable)

# 2. Edit manifest TODOs (description, hook_events, matchers, compatibility)
# 3. Implement the hook logic in source/hook.py
# 4. Add tests in tests/test_hooks.py
# 5. python3 -m pytest tests/   ← must pass
# 6. ./bin/agent-hook install my-new-hook --client opencode   ← smoke test
# 7. Open PR
```

## Issue reporting

<https://github.com/zjgulai/Agent_hook/issues>. Include:

- Hook name + repo SHA
- `agent-hook doctor` output
- For runtime issues: opencode log line `service=plugin path=...`
- Minimum reproducing event JSON (the stdin payload)

## License

By contributing, you agree your work is licensed under [MIT](LICENSE).
