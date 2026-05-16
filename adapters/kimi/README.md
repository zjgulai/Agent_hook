# Adapters · kimi

kimi CLI 在 `~/.kimi/config.toml` 中支持 `hooks=[]` 字段。具体协议待 P2 阶段做"echo hook"探针验证。

如果 kimi 的 hook 协议兼容 Claude Code 风格（Python 脚本 stdin/stdout）：直接引用 `registry/<name>/source/hook.py`。

如果不兼容：参考 cursor 降级策略，翻译到 kimi 支持的形态（如 system prompt 注入）。

实现脚本：[`../../agent/lib/adapter_kimi.py`](../../agent/lib/adapter_kimi.py)（P2 阶段实现）
