---
name: agent-hook-rules
description: Agent_hook 项目级 AI 协作规则。定义 Hook 源仓库的硬约束、目录边界、四客户端适配协议、Manifest schema 规范。当你在 Agent_hook 目录下做任何修改时使用。
---

# Agent_hook · 项目规则

本项目级规则覆盖 `~/.config/opencode/AGENTS.md` 中冲突的部分（项目级优先），未覆盖的部分继承全局。

## 一、项目定位

**Agent_hook** —— Hook 组件的本地用户级源仓库。三仓之一（Agent_skills / Agent_hook / Agent_mcp）。

**单一真相源**：`registry/<hook-name>/source/hook.py` 是 Hook 的源代码（Claude Code 风格 Python 脚本）。

**四客户端分发**：`adapters/{opencode,codex,cursor,kimi}/` 把源脚本翻译成各客户端的原生形态：

- `opencode/` → JS/TS plugin（写到 `~/.config/opencode/plugins/`）
- `codex/` → 默认 `unsupported`（codex 暂无 hook 概念）
- `cursor/` → 降级为 Rule（写到 `~/.cursor/rules/`，软约束）
- `kimi/` → `~/.kimi/config.toml` 的 `hooks=[]` 字段注入

## 二、必读

接到任何任务前先读：

1. [本仓 README](README.md)
2. `.sisyphus/plans/01-bootstrap.md` —— Phase 0 决策与目标结构
3. [统一 manifest schema](agent/lib/manifest.py) —— 三仓共享
4. [上级目录 AGENTS.md](file:///Users/lute/project/Agent/AGENTS.md)（如存在）

## 三、硬约束（不可违反）

### 文件系统访问

| 对象 | 谁能改 | 怎么改 |
|---|---|---|
| `registry/<name>/source/hook.py` | agent 直接改 | Python 脚本，纯函数式，必须能 stdin → stdout 工作 |
| `registry/<name>/manifest.yaml` | agent 直接改 | 必须通过 `agent/lib/manifest.py` 验证 |
| `adapters/<client>/` | agent 直接改 | 写客户端配置前**必须** `cp <target> <target>.bak.{timestamp}` |
| `~/.config/opencode/plugins/` 等客户端目录 | **必须**走 adapter | 锚点注释：`# managed-by: agent-hook` |
| `INDEX.md`（如有） | agent 直接读写 | 必须先备份 |

### Hook 源代码协议

每个 `registry/<name>/source/hook.py` 必须：

1. 入口点 `def hook(event: dict) -> dict | None` —— 输入 stdin JSON，输出 stdout JSON 或 exit code
2. 退出码语义：`0`=放行 / `2`=阻止（PreToolUse）/ 其他=异常
3. **零三方依赖**或仅依赖 stdlib —— 因为它要在 4 个客户端进程里跑
4. 顶部必须有 docstring 说明 `event=`/`matcher=` 触发条件
5. 必须配套 `tests/test_<name>.py`

### Manifest 必填字段

`kind` 必须为 `hook`；`hook_events` 必须从 `[PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop, SubagentStop, Notification, PreCompact]` 取；`compatibility` 四客户端必须显式声明（`native | adapter | unsupported`）。

## 四、目录约定

```
Agent_hook/
├── AGENTS.md / README.md / opencode.json
├── .opencode/{agent,commands}/
├── .sisyphus/plans/
├── agent/{lib,docs}/
├── registry/<hook-name>/{manifest.yaml, source/hook.py, README.md, tests/}
├── adapters/{opencode,codex,cursor,kimi}/
├── docs/
└── tests/
```

## 五、协作纪律

- **不动 Agent_skills 和 Agent_mcp** —— 三仓互不交叉文件级修改。共享代码以 `agent/lib/manifest.py` 同源副本（vendored）方式存在。
- 写代码前 → 先看 `registry/` 已有哪些 hook，参考已有 manifest 的 schema。
- 改 adapter → 必须 跑 `pytest tests/` 全绿，必须先备份目标客户端配置。
- 新增 hook → 走 P4 的 `agent-hook new <name>` 脚手架（暂未实现时手动复制最近一个 hook 目录改名）。

## 六、术语

- **Source / 源** = `registry/<name>/source/hook.py`，单一真相
- **Adapter / 适配器** = `adapters/<client>/` 下的翻译脚本
- **Anchor / 锚点** = 注入到客户端配置里的 `# managed-by: agent-hook · <name>` 注释，用于按锚点删除
- **Native / Adapter / Unsupported** = 客户端兼容性三档
