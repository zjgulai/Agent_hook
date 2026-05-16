# Changelog

All notable changes to **Agent_hook** are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning is [SemVer](https://semver.org/).

## [Unreleased]

Pre-1.0. Coordinated 1.0.0 will land alongside [Agent_skills](https://github.com/zjgulai/Agent_skills) and [Agent_mcp](https://github.com/zjgulai/Agent_mcp) once the `manifest.py` schema and CLI surface are pinned.

## [0.1.1] — 2026-05-16

### Fixed

- **opencode plugin format** (commit `b8ab172`). The previous JS template used `export default { onPreToolUse, ... }`, which silently fails because opencode actually requires `export const PluginName = async (ctx) => ({ "tool.execute.before": ... })`. Aligned the template per [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins/). Verified end-to-end:
  - opencode startup log: `service=plugin path=...agent-hook-protect-sensitive-files.js loading plugin`
  - Node import + simulate `tool.execute.before`:
    - `Write '/proj/.env'` → throws ✓
    - `Write '/safe.ts'` → passes ✓
    - `Write '/server.pem'` → throws ✓
    - `Read '/proj/.env'` → passes (matcher excludes Read) ✓

### Documentation

- Full Chinese i18n coverage on all 4 content pages plus 3 redirect stubs (commit `0e7c410`):
  - index: 41 dict keys / 332 zh chars rendered
  - getting-started: 19 keys / 109 chars
  - architecture: 36 keys / 368 chars
  - handbook: 81 keys / 577 chars
  - All 8 pages pass `linkedom` zh-switch simulation with `unfilled keys = 0`

## [0.1.0] — 2026-05-16

Initial release. Single source of truth for AI agent hooks shared by opencode, codex, cursor, kimi.

### Added

- 9 hooks (5 P0 + 4 P1):
  - **P0**: `protect-sensitive-files`, `guard-bash`, `post-edit-format`, `session-context-injector`, `final-verify`
  - **P1**: `prompt-context-enricher`, `subagent-acceptance`, `notify-on-idle`, `pre-compact-save`
- 4-client adapter system: opencode (native JS plugin), codex (unsupported, no-op), cursor (degraded Rule), kimi (`config.toml` `hooks=[]`)
- `agent/lib/manifest.py` — shared schema validator (byte-identical with Agent_skills, Agent_mcp; md5 `b46c2f55980b9aa2ea93b87941c833e2`)
- `agent/lib/cli.py` + `bin/agent-hook` — `list / install / uninstall / doctor / show`
- Hook source contract: Python `def hook(event: dict) -> dict | None`, stdin/stdout JSON, exit code `0`/`2` semantics, zero third-party imports
- Test suite: 28 schema + 39 behavior + 14 adapter = **81 tests, all green**
- GitHub Pages site: index / getting-started / architecture / handbook (amber accent, dark zinc base) + 3 redirect stubs
- Companion-repo links to Agent_skills and Agent_mcp in README

## Compatibility

| Version | manifest.py md5 | Companion repos required |
|---|---|---|
| 0.1.x | `b46c2f55980b9aa2ea93b87941c833e2` | Agent_skills ≥ 0.2.0, Agent_mcp ≥ 0.1.1 |
