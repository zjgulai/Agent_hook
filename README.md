# Agent_hook

> 🛡️ Hook layer of the [agent-kit](https://github.com/zjgulai) workflow factory · for opencode + codex + cursor + kimi
>
> **Docs site**: [zjgulai.github.io/Agent_hook](https://zjgulai.github.io/Agent_hook/)

## What

**Agent_hook** is the single source of truth for AI agent hooks — Python scripts following the Claude Code stdin/stdout/exit-2 protocol. One script, four client adapters: opencode (native JS plugin), cursor (degraded Rule), kimi (config.toml hooks=[] entry), codex (no-op, no native hook concept).

| | |
|---|---|
| Hooks registered | **9** (5 P0 + 4 P1) |
| Tests passing | **81** (28 schema + 39 behavior + 14 adapter) |
| Clients supported | opencode, codex (skipped), cursor, kimi |
| Companion repos | [Agent_skills](https://github.com/zjgulai/Agent_skills) · [Agent_mcp](https://github.com/zjgulai/Agent_mcp) |

## Quick start

```bash
git clone https://github.com/zjgulai/Agent_hook.git ~/project/Agent_hook
cd ~/project/Agent_hook
python3 -m pip install --user pyyaml tomli tomli_w

./bin/agent-hook list
./bin/agent-hook install protect-sensitive-files --client all
./bin/agent-hook doctor
```

Real evidence the hook actually blocks (run with [opencode](https://github.com/sst/opencode) installed):

```bash
$ echo '{"tool":"Write","parameters":{"filePath":"/proj/.env"}}' \
    | python3 registry/protect-sensitive-files/source/hook.py
{"block": true, "reason": "...matches exact name '.env'..."}
$ echo $?
2
```

## The 9 hooks

**P0 (must-install)**:

| Name | Event | What it does |
|---|---|---|
| protect-sensitive-files | PreToolUse | Block writes to .env, *.pem, credentials, migrations |
| guard-bash | PreToolUse | Block rm -rf, git reset --hard, curl\|sh, DROP TABLE, ... |
| post-edit-format | PostToolUse | Auto-run prettier / ruff / gofmt / shfmt by suffix |
| session-context-injector | SessionStart | Inject branch / last commit / active plans |
| final-verify | Stop | Report changed files, open TODOs, optional test run |

**P1 (recommended)**:

| Name | Event | What it does |
|---|---|---|
| prompt-context-enricher | UserPromptSubmit | Prepend project context block to user message |
| subagent-acceptance | SubagentStop | Catch shallow-completion claims in subagent reports |
| notify-on-idle | Notification | macOS osascript desktop notification |
| pre-compact-save | PreCompact | Snapshot project state before context compaction |

## Architecture

See [Architecture](https://zjgulai.github.io/Agent_hook/architecture.html) and [Handbook](https://zjgulai.github.io/Agent_hook/handbook.html).

```
registry/<name>/manifest.yaml            ← single source of truth
registry/<name>/source/hook.py           ← Python (zero 3rd-party imports)

agent/lib/manifest.py                    ← shared schema (byte-identical 3 repos)
agent/lib/adapter_opencode.py            ← generates JS plugin
agent/lib/adapter_codex.py               ← always skips (codex unsupported)
agent/lib/adapter_cursor.py              ← generates Rule (.mdc) — soft constraint only
agent/lib/adapter_kimi.py                ← writes config.toml hooks=[] entry
agent/lib/cli.py                         ← agent-hook list/install/uninstall/doctor/show
```

## Test

```bash
python3 -m pytest tests/   # 81 tests, all green
```

## License

MIT.

## Related

- [Agent_skills](https://github.com/zjgulai/Agent_skills) — the **methodology** layer (16 skills)
- [Agent_mcp](https://github.com/zjgulai/Agent_mcp) — the **context** layer (10 MCPs)
