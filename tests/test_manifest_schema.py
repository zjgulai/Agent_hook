import copy
from pathlib import Path

import pytest

from agent.lib.manifest import (
    CLIENTS,
    HOOK_EVENTS,
    Manifest,
    iter_registry,
    load_manifest,
    validate_manifest,
)

REPO_ROOT = Path(__file__).parent.parent


VALID_SKILL = {
    "kind": "skill",
    "name": "frontend-design",
    "version": "0.1.0",
    "description": "Generate beautiful UI with strong visual direction. Trigger on landing/marketing pages.",
    "domain": "frontend",
    "priority": "P0",
    "compatibility": {"opencode": "native", "codex": "native", "cursor": "native", "kimi": "native"},
    "source": {"type": "external", "path": "~/.config/opencode/skills/frontend-design"},
    "triggers": ["landing page", "marketing site"],
    "links": {"upstream": "https://github.com/anthropics/skills"},
}

VALID_HOOK = {
    "kind": "hook",
    "name": "protect-sensitive-files",
    "version": "0.1.0",
    "description": "Block writes to .env, secrets, migrations on PreToolUse(Write|Edit) events.",
    "domain": "code-quality",
    "priority": "P0",
    "compatibility": {"opencode": "native", "codex": "unsupported", "cursor": "adapter", "kimi": "adapter"},
    "source": {"type": "local", "path": "registry/protect-sensitive-files/source/"},
    "hook_events": ["PreToolUse"],
    "matchers": ["Write|Edit|MultiEdit"],
    "requires": {"binaries": ["python3"]},
}

VALID_MCP = {
    "kind": "mcp",
    "name": "github",
    "version": "0.1.0",
    "description": "GitHub MCP server for repo/issue/PR/CI access. Use when working with github.com workflows.",
    "domain": "ops",
    "priority": "P0",
    "compatibility": {"opencode": "native", "codex": "native", "cursor": "native", "kimi": "native"},
    "source": {"type": "npm", "package": "@modelcontextprotocol/server-github"},
    "mcp_command": ["npx", "-y", "@modelcontextprotocol/server-github"],
    "requires": {"binaries": ["npx"], "env": ["GITHUB_TOKEN"]},
}


def test_valid_skill_passes():
    assert validate_manifest(VALID_SKILL) == []


def test_valid_hook_passes():
    assert validate_manifest(VALID_HOOK) == []


def test_valid_mcp_passes():
    assert validate_manifest(VALID_MCP) == []


def test_kind_mismatch_caught():
    errs = validate_manifest(VALID_HOOK, expected_kind="mcp")
    assert any("expected kind=mcp" in e for e in errs)


@pytest.mark.parametrize("missing_field", [
    "kind", "name", "version", "description", "domain", "priority", "compatibility", "source",
])
def test_missing_required_field_caught(missing_field):
    bad = copy.deepcopy(VALID_HOOK)
    del bad[missing_field]
    errs = validate_manifest(bad)
    assert any(missing_field in e for e in errs), f"missing {missing_field} not detected: {errs}"


def test_bad_name_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    bad["name"] = "Bad_Name_With_UPPERCASE"
    errs = validate_manifest(bad)
    assert any("kebab-case" in e for e in errs)


def test_bad_version_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    bad["version"] = "v1"
    errs = validate_manifest(bad)
    assert any("semver" in e for e in errs)


def test_short_description_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    bad["description"] = "too short"
    errs = validate_manifest(bad)
    assert any("description" in e for e in errs)


def test_unknown_domain_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    bad["domain"] = "frontend-stuff"
    errs = validate_manifest(bad)
    assert any("domain" in e for e in errs)


def test_compatibility_missing_client_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    del bad["compatibility"]["kimi"]
    errs = validate_manifest(bad)
    assert any("kimi" in e for e in errs)


def test_compatibility_bad_value_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    bad["compatibility"]["opencode"] = "yes"
    errs = validate_manifest(bad)
    assert any("compatibility.opencode" in e for e in errs)


def test_hook_without_events_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    del bad["hook_events"]
    errs = validate_manifest(bad)
    assert any("hook_events" in e for e in errs)


def test_hook_with_bad_event_rejected():
    bad = copy.deepcopy(VALID_HOOK)
    bad["hook_events"] = ["RandomEvent"]
    errs = validate_manifest(bad)
    assert any("RandomEvent" in e for e in errs)


def test_mcp_without_command_rejected():
    bad = copy.deepcopy(VALID_MCP)
    del bad["mcp_command"]
    errs = validate_manifest(bad)
    assert any("mcp_command" in e for e in errs)


def test_secret_literal_rejected():
    bad = copy.deepcopy(VALID_MCP)
    bad["requires"]["env"] = ["GITHUB_TOKEN"]
    bad["description"] = bad["description"] + " ghp_abcdefghijklmnopqrstuvwxyz012345678901"
    errs = validate_manifest(bad)
    assert any("secret" in e.lower() for e in errs)


def test_load_manifest_from_disk(tmp_path):
    import yaml as _y
    p = tmp_path / "registry" / "demo-hook" / "manifest.yaml"
    p.parent.mkdir(parents=True)
    p.write_text(_y.safe_dump(VALID_HOOK), encoding="utf-8")
    m = load_manifest(p)
    assert isinstance(m, Manifest)
    assert m.name == "protect-sensitive-files"
    assert m.kind == "hook"
    assert "PreToolUse" in m.hook_events


def test_load_manifest_raises_on_invalid(tmp_path):
    import yaml as _y
    bad = copy.deepcopy(VALID_HOOK)
    bad["name"] = "BAD"
    p = tmp_path / "manifest.yaml"
    p.write_text(_y.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="kebab-case"):
        load_manifest(p)


def test_iter_registry_empty(tmp_path):
    assert list(iter_registry(tmp_path)) == []


def test_iter_registry_finds_multiple(tmp_path):
    import yaml as _y
    for n in ("alpha-hook", "beta-hook"):
        d = tmp_path / "registry" / n
        d.mkdir(parents=True)
        m = copy.deepcopy(VALID_HOOK)
        m["name"] = n
        (d / "manifest.yaml").write_text(_y.safe_dump(m), encoding="utf-8")
    names = sorted(m.name for m in iter_registry(tmp_path))
    assert names == ["alpha-hook", "beta-hook"]


def test_clients_constant_matches_decisions():
    assert CLIENTS == {"opencode", "codex", "cursor", "kimi"}


def test_hook_events_constant_covers_claude_code_spec():
    expected = {"PreToolUse", "PostToolUse", "UserPromptSubmit", "SessionStart",
                "Stop", "SubagentStop", "Notification", "PreCompact"}
    assert HOOK_EVENTS == expected
