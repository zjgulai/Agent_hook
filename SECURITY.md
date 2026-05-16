# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue. Instead:

1. Email **zjgulai@github.com** (or open a private GitHub Security Advisory at <https://github.com/zjgulai/Agent_hook/security/advisories>)
2. Include:
   - Repo + commit SHA you reproduced on
   - Hook name, event, matcher
   - Minimum reproducing event JSON (the stdin payload)
   - opencode log line if relevant: `service=plugin path=...`

We aim to triage within **3 business days**.

## What we consider a security issue

Agent_hook is the **enforcement layer** — its whole job is to be a security control. Bugs here matter:

| Severity | Example |
|---|---|
| Critical | A hook bypass — `protect-sensitive-files` fails to block a `.env` write because of a regex flaw |
| Critical | A hook **silently injects** something into the LLM context that the user didn't authorize |
| High | `guard-bash` fails to catch a known-dangerous command pattern |
| High | An adapter writes user-provided strings into a client config without escaping (command injection on next CLI restart) |
| High | The opencode JS plugin allows a tool call through that the source `hook.py` returned `exit 2` for |
| Medium | `prune_backups()` deletes more than `keep=N` files |
| Medium | A hook crashes with stack trace exposing absolute paths that contain user identifiers |
| Low | Stale doc claims an event triggers when the code no longer supports it |

## What is NOT a security issue

- The user explicitly disabling a hook via documented escape-hatch env vars (`AGENT_HOOK_ALLOW_SENSITIVE=...`, `AGENT_HOOK_BASH_YOLO=1`, `AGENT_HOOK_SKIP_FORMAT=1`, `AGENT_HOOK_SKIP_FINAL=1`, `AGENT_HOOK_SKIP_NOTIFY=1`, `AGENT_HOOK_SKIP_PROMPT_ENRICH=1`). These are intentional opt-outs.
- Cursor not enforcing a hook — cursor only supports Rules (soft constraint), as documented in `adapters/cursor/README.md`.
- codex showing `n/a` for all hooks — codex has no native hook concept yet.
- A hook's matcher being too narrow / too broad in a user's specific scenario — file a regular issue.

## Hook source code review checklist

Before merging any new hook:

- [ ] **Zero third-party imports** in `source/hook.py` (asserted by `tests/test_hooks.py::test_all_hooks_zero_third_party_imports`)
- [ ] All inputs treated as untrusted — no `eval()`, no `shell=True`, no string formatting into shell commands
- [ ] Path comparisons use `pathlib.Path` semantics, not raw `str.startswith()` (which can be tricked by `..`)
- [ ] Regex patterns are **conservative** — prefer false positives (block) over false negatives (allow). Example: `guard-bash` blocks `echo "rm -rf in a string"` because LLM could route it through `eval`.
- [ ] Override env-var documented in manifest description and README

## Update policy

Critical / High issues:
- Patch released within **7 business days** of confirmation
- CVE filed if the bypass is exploitable in user environments
- Fix coordinated across companion repos if `manifest.py` schema is involved

## Companion repos

- [Agent_skills](https://github.com/zjgulai/Agent_skills) (methodology layer)
- [Agent_mcp](https://github.com/zjgulai/Agent_mcp) (context layer)

The shared `agent/lib/manifest.py` (md5 `b46c2f55980b9aa2ea93b87941c833e2`) is the spine of all three. Issues touching it require coordinated patches.
