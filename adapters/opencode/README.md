# Adapters · opencode

opencode 客户端的 Hook 适配器。把 `registry/<name>/source/hook.py` 翻译成 opencode JS plugin，写到 `~/.config/opencode/plugins/agent-hook-<name>.js`。

实现脚本：[`../../agent/lib/adapter_opencode.py`](../../agent/lib/adapter_opencode.py)（P2 阶段实现）

## 机制

opencode 的 hook 通过 plugin 暴露。Plugin 是 JS/TS 文件，导出对应生命周期函数（`onWrite`/`onBash`/`onSessionStart`/`onStop` 等）。

适配器做的事：

1. 读 manifest.hook_events 决定要 hook 哪些事件
2. 生成一个 thin JS wrapper，内部 spawn `python3 registry/<name>/source/hook.py < event.json`
3. 写到 `~/.config/opencode/plugins/agent-hook-<name>.js`，顶部加锚点：
   ```
   // managed-by: agent-hook · <name> · <timestamp>
   ```
4. 不删用户手写的其他 plugin
