# Adapters · cursor

cursor 没有原生 hook 机制（只有 Rules）。我们把 PreToolUse 类的"约束型 hook"降级翻译成 Rule（软约束，无强制力），写到 `~/.cursor/rules/agent-hook-<name>.mdc`。

实现脚本：[`../../agent/lib/adapter_cursor.py`](../../agent/lib/adapter_cursor.py)（P2 阶段实现）

## 降级原则

| 源 hook 事件 | cursor Rule 翻译策略 |
|---|---|
| PreToolUse(Write\|Edit) protect-files | Rule：用 always_apply=true 提醒"绝不修改 .env 等敏感文件" |
| PreToolUse(Bash) guard-bash | Rule：always_apply=true，列出禁止命令清单 |
| PostToolUse 格式化 | 无法降级（Rule 不能触发命令）→ 标 `unsupported` |
| SessionStart 上下文注入 | Rule：always_apply=true，描述项目上下文 |
| Stop final-verify | 无法降级 → 标 `unsupported` |

具体降级是否可行写在每个 hook 的 manifest.compatibility.cursor 里。
