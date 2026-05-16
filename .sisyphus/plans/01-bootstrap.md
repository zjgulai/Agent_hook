# Phase 0 · Agent_hook Bootstrap

> 创建时间：2026-05-16
> 决策来源：与 user 讨论确认的 8 项决策（见 aim-memory `agent-kit` context）

## 目标

让 `Agent_hook/` 拥有与 `Agent_skills/` 同形的"管理面板"骨架，但**不立即写 portal**（按决策 7，Phase 0-5 走 CLI-only）。

## 必须落地的目录

```
Agent_hook/
├── AGENTS.md                ✅ 项目级 AI 协作规则
├── README.md                ✅ 人类入口
├── opencode.json            ✅ 最小 opencode 配置
├── .opencode/
│   ├── agent/hook-manager.md            ✅
│   └── commands/{list,install,uninstall,doctor,sync}.md  ✅
├── .sisyphus/plans/
│   ├── 01-bootstrap.md      ← 本文件
│   └── 02-execution-todo.md ← 与全局 TODO list 同步
├── agent/
│   ├── lib/                 manifest.py + 4 个 adapter_*.py（P0.4 阶段）
│   └── docs/
├── registry/                空（P2.1 开始填）
├── adapters/{opencode,codex,cursor,kimi}/  空目录
├── docs/                    空（Phase 6 portal 时填）
└── tests/
    ├── conftest.py
    ├── fixtures/
    └── test_manifest_schema.py  （P0.4 阶段）
```

## 验收标准

- [ ] `tree -L 3 Agent_hook/` 与上面骨架一致
- [ ] `cat Agent_hook/AGENTS.md` 可读，UTF-8 NO BOM（修复 Agent_skills 的 UTF-16 历史问题不会重演）
- [ ] `python3 -c "import yaml; yaml.safe_load(open('registry/.gitkeep'))"` 不报错（即 registry 目录就绪）
- [ ] 后续 P0.4 写完 manifest.py 后，`pytest tests/` 至少有一个 passing test

## 不做的事

- ❌ 不写 portal/ —— Phase 6 才合并
- ❌ 不创建任何具体 hook —— P2 才开始
- ❌ 不动 `~/.config/opencode/plugins/` 等客户端目录

## 协作纪律

- 任何对 Agent_hook 的修改必须先读本文件 + AGENTS.md
- 任何对客户端配置的写入操作 **必须**走 adapter（即使是 P0 调试也不破例）
