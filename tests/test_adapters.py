import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from agent.lib import (
    adapter_codex,
    adapter_cursor,
    adapter_dispatch,
    adapter_kimi,
    adapter_opencode,
)
from agent.lib.manifest import load_manifest


def _load(name: str):
    return load_manifest(REPO / "registry" / name / "manifest.yaml", expected_kind="hook")


@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    plugins = tmp_path / "opencode-plugins"
    cursor_rules = tmp_path / "cursor-rules"
    kimi_cfg = tmp_path / "kimi-config.toml"
    kimi_reg = tmp_path / "kimi-registry.json"
    monkeypatch.setattr(adapter_opencode, "PLUGINS_DIR", plugins)
    monkeypatch.setattr(adapter_cursor, "RULES_DIR", cursor_rules)
    monkeypatch.setattr(adapter_kimi, "CONFIG_PATH", kimi_cfg)
    monkeypatch.setattr(adapter_kimi, "MANAGED_REGISTRY", kimi_reg)
    return {"plugins": plugins, "cursor_rules": cursor_rules, "kimi_cfg": kimi_cfg, "kimi_reg": kimi_reg}


def test_opencode_install_creates_plugin(isolated_paths):
    m = _load("protect-sensitive-files")
    res = adapter_opencode.install(m)
    plugin = Path(res["plugin"])
    assert plugin.exists()
    text = plugin.read_text()
    assert "managed-by: agent-hook · protect-sensitive-files" in text
    assert "spawnSync" in text
    assert "PreToolUse" in text
    assert "Write" in text


def test_opencode_uninstall_removes_plugin(isolated_paths):
    m = _load("protect-sensitive-files")
    adapter_opencode.install(m)
    res = adapter_opencode.uninstall("protect-sensitive-files")
    assert res["removed"] is True


def test_opencode_uninstall_refuses_unmanaged(isolated_paths):
    isolated_paths["plugins"].mkdir(parents=True, exist_ok=True)
    p = isolated_paths["plugins"] / "agent-hook-foreign.js"
    p.write_text("// some user-written plugin\n")
    res = adapter_opencode.uninstall("foreign")
    assert res["removed"] is False
    assert "not-managed" in res["reason"]


def test_codex_always_skips():
    m = _load("protect-sensitive-files")
    res = adapter_codex.install(m)
    assert res["skipped"] is True
    assert res["client"] == "codex"


def test_cursor_install_degrades_protect_files(isolated_paths):
    m = _load("protect-sensitive-files")
    res = adapter_cursor.install(m)
    assert "rule" in res
    rule = Path(res["rule"])
    assert rule.exists()
    text = rule.read_text()
    assert "alwaysApply: true" in text
    assert "agent-hook-protect-sensitive-files" in text


def test_cursor_install_skips_post_format(isolated_paths):
    m = _load("post-edit-format")
    res = adapter_cursor.install(m)
    assert res["skipped"] is True


def test_cursor_install_skips_when_unsupported(isolated_paths):
    m = _load("final-verify")
    res = adapter_cursor.install(m)
    assert res["skipped"] is True


def test_cursor_uninstall_removes_rule(isolated_paths):
    m = _load("guard-bash")
    adapter_cursor.install(m)
    res = adapter_cursor.uninstall("guard-bash")
    assert res["removed"] is True


def test_kimi_install_appends_to_hooks_array(isolated_paths):
    m = _load("protect-sensitive-files")
    res = adapter_kimi.install(m)
    assert "config" in res
    import tomli
    with isolated_paths["kimi_cfg"].open("rb") as f:
        data = tomli.load(f)
    hooks = data.get("hooks", [])
    assert any(h.get("name") == "protect-sensitive-files" for h in hooks)


def test_kimi_install_does_not_duplicate(isolated_paths):
    m = _load("protect-sensitive-files")
    adapter_kimi.install(m)
    adapter_kimi.install(m)
    import tomli
    with isolated_paths["kimi_cfg"].open("rb") as f:
        data = tomli.load(f)
    matching = [h for h in data.get("hooks", []) if h.get("name") == "protect-sensitive-files"]
    assert len(matching) == 1


def test_kimi_uninstall(isolated_paths):
    m = _load("protect-sensitive-files")
    adapter_kimi.install(m)
    res = adapter_kimi.uninstall("protect-sensitive-files")
    assert res["removed"] is True
    import tomli
    with isolated_paths["kimi_cfg"].open("rb") as f:
        data = tomli.load(f)
    assert not any(h.get("name") == "protect-sensitive-files" for h in (data.get("hooks") or []))


def test_dispatch_install_all_clients(isolated_paths):
    m = _load("protect-sensitive-files")
    results = adapter_dispatch.install_all_clients(m)
    by_client = {r["client"]: r for r in results}
    assert "opencode" in by_client and "plugin" in by_client["opencode"]
    assert by_client["codex"]["skipped"] is True
    assert "rule" in by_client["cursor"]
    assert "config" in by_client["kimi"]


def test_dispatch_install_all_for_post_format_skips_codex_and_cursor(isolated_paths):
    m = _load("post-edit-format")
    results = adapter_dispatch.install_all_clients(m)
    by_client = {r["client"]: r for r in results}
    assert "plugin" in by_client["opencode"]
    assert by_client["codex"]["skipped"] is True
    assert by_client["cursor"]["skipped"] is True
    assert "config" in by_client["kimi"]


def test_dispatch_unknown_client():
    m = _load("protect-sensitive-files")
    with pytest.raises(ValueError):
        adapter_dispatch.install(m, "vim")
