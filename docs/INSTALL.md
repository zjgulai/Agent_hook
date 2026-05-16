# Agent_hook 安装指南

把 Agent_hook 从零装到 4 个 AI CLI 都跑起 hook,约 5 分钟。覆盖 macOS(首选)+ Linux(最小适配)。Windows 不在 v0.1 支持范围。

> 假设你已经有 git、Python 3.9+、curl。没有的话先装这些。

---

## 一、先决条件

| 工具 | 最低版本 | 检查 |
|---|---|---|
| git | 2.30+ | `git --version` |
| Python | 3.9+ | `python3 --version` |

**至少安装一个 AI CLI**(才能验证 hook):

| CLI | 安装 | 兼容性 |
|---|---|---|
| [opencode](https://opencode.ai/) | `npm install -g opencode-ai` | **native**(JS plugin,完整支持) |
| [cursor](https://cursor.com/) | 桌面 App | adapter(降级为 Rule,只能软约束) |
| [kimi](https://kimi.com/) | `pip install kimi-cli` 或下载二进制 | adapter(`config.toml hooks=[]`) |
| codex | n/a | unsupported(暂无 hook 概念,跳过) |

---

## 二、Clone + 装 Python 依赖

```bash
mkdir -p ~/project
cd ~/project
git clone https://github.com/zjgulai/Agent_hook.git
cd Agent_hook

python3 -m pip install --user pyyaml tomli tomli_w pytest
```

---

## 三、跑测试 + 体检

```bash
python3 -m pytest tests/   # 应输出 81 passed

./bin/agent-hook list      # 看注册的 9 个 hook
./bin/agent-hook doctor    # 验证 schema、source、二进制依赖
```

如果 doctor 报 `MISSING python3` 或类似错误,先把缺的工具装上。

---

## 四、装第一个 hook

最常用的是 `protect-sensitive-files`(拦下 `.env` / `*.pem` / credentials 写入):

```bash
./bin/agent-hook install protect-sensitive-files --client opencode

# 输出示例:
# [
#   {
#     "client": "opencode",
#     "name": "protect-sensitive-files",
#     "plugin": "/Users/you/.config/opencode/plugins/agent-hook-protect-sensitive-files.js",
#     "backup": null
#   }
# ]
```

在 opencode 启动一个新 session(已运行的 session 必须重启才会加载 plugin),让 LLM 写 `.env` 文件,你会看到 plugin throw + 工具调用失败。

## 五、装到所有支持的客户端

```bash
for h in protect-sensitive-files guard-bash post-edit-format \
         session-context-injector final-verify; do
  ./bin/agent-hook install "$h" --client all
done

./bin/agent-hook list      # 应显示每个 hook 在 4 客户端的状态
```

`codex` 列总是 `n/a`(无原生 hook 概念)是预期。

## 六、验证 hook 真生效

最直接方式 — 用 node 直接加载 plugin 模拟调用:

```bash
node --input-type=module -e '
  const mod = await import("/Users/you/.config/opencode/plugins/agent-hook-protect-sensitive-files.js");
  const hooks = await mod.AgentHook_ProtectSensitiveFiles({ directory: process.cwd() });
  try {
    await hooks["tool.execute.before"](
      { tool: "write" },
      { args: { filePath: "/tmp/test.env" } }
    );
    console.log("BUG: did not throw");
  } catch (e) {
    console.log("OK throws:", e.message.slice(0, 100));
  }
'
# 应输出: OK throws: {"block": true, "reason": "...matches exact name '.env'..."} ...
```

如果输出 "OK throws" → 全链路工作。

---

## 七、卸载

```bash
./bin/agent-hook uninstall protect-sensitive-files --client all
# 自动按锚点删除,不破坏用户其他 plugin
```

---

## 八、故障排查

| 现象 | 原因 / 解决 |
|---|---|
| `agent-hook: command not found` | `chmod +x bin/agent-hook` |
| `ModuleNotFoundError: agent` | 必须在仓根目录跑;最新版 launcher 已自动 cd,如果还失败检查 `agent/__init__.py` 是否存在 |
| `pytest` 找不到 | `python3 -m pip install --user pytest` |
| opencode 启动后没看到 hook 加载日志 | 用 `opencode serve --print-logs --log-level INFO` 看是否有 `service=plugin path=...agent-hook-... loading plugin` 行 |
| cursor 报 `agent-hook-X.mdc` 不工作 | cursor 不支持原生 hook,只能软约束(LLM 提示);要真拦截改用 opencode |
| kimi `config.toml hooks=[]` 字段不识别 | kimi 这个字段还在演进,目前装上后兼容性取决于 kimi 版本;最坏情况是 hook 不被调用,不会报错 |

---

## 九、下一步

- [Handbook](https://zjgulai.github.io/Agent_hook/handbook.html) — 9 个 hook 详细手册
- [Architecture](https://zjgulai.github.io/Agent_hook/architecture.html) — 单源码 + 4 适配器架构
- [Agent_skills](https://github.com/zjgulai/Agent_skills) — 配套的方法论层(16 skills)
- [Agent_mcp](https://github.com/zjgulai/Agent_mcp) — 配套的上下文层(10 MCPs)
