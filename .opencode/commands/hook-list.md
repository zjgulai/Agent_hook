---
description: 列出所有已注册的 Hook（registry/ 下）以及它们在 4 个客户端的安装状态。
agent: hook-manager
---

# /hook-list

读取 `registry/*/manifest.yaml` 列出所有 hook，并对每一个 hook 检查 4 个客户端是否已安装：

- opencode: `~/.config/opencode/plugins/<name>.js` 是否存在
- codex: 永远 `n/a`（unsupported）
- cursor: `~/.cursor/rules/<name>.mdc` 是否存在
- kimi: `~/.kimi/config.toml` 中 `hooks=[]` 是否包含本 hook 的引用

输出表格：name | event | priority | opencode | codex | cursor | kimi
