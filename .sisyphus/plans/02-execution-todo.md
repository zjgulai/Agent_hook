# Phase 0~6 · 执行 TODO List

> 与 OpenCode 主会话的全局 TODO list 同源。每完成一项，本文件 + 主会话 todowrite 同步勾选。

## Phase 0 · 骨架（半天）

- [x] P0.1 创建 Agent_hook 骨架
- [ ] P0.2 创建 Agent_mcp 骨架
- [ ] P0.3 Agent_skills 补加 registry/ adapters/
- [ ] P0.4 manifest.py 统一 schema 验证库 + pytest
- [ ] P0.5 三仓 pytest 验证全绿

## Phase 1 · MCP 先行（1 天）

- [ ] P1.1 写 6 个 P0 MCP 的 manifest（github/filesystem/context7/playwright/sequential-thinking/git）
- [ ] P1.2 写 4 客户端 MCP 适配器
- [ ] P1.3 实现 `agent-mcp` CLI（install/uninstall/list/doctor）
- [ ] P1.4 验证：4 客户端 install 后都能 list 到这 6 个

## Phase 2 · Hook P0（1 天）

- [ ] P2.1 写 5 个 P0 Hook 的 Python 脚本
- [ ] P2.2 写 4 客户端 Hook 适配器（opencode JS plugin / codex skip / cursor Rule / kimi config.toml）
- [ ] P2.3 实现 `agent-hook` CLI
- [ ] P2.4 验证：opencode 改 .env 被拦 / Stop 跳 final-verify

## Phase 3 · Skills P0 + 老 8 个注册（半天）

- [ ] P3.1 写 4 个 P0 Skill 的 manifest 并源口拉取
- [ ] P3.2 补齐现有 8 个老 skill 的 manifest 注册（不动文件）
- [ ] P3.3 写 4 客户端 Skill 适配器（符号链接为主）
- [ ] P3.4 验证：4 客户端都能识别这 12 个 skill

## Phase 4 · 元工具（半天）

- [ ] P4.1 写 hook-creator / mcp-registrator
- [ ] P4.2 跨仓脚手架 `agent-kit new <skill|hook|mcp> <name>`

## Phase 5 · P1 补强（1 天）

- [ ] P5.1 4 个 P1 Skill
- [ ] P5.2 4 个 P1 Hook
- [ ] P5.3 4 个 P1 MCP

## Phase 6 · 端到端 + Portal 合一（1-2 天）

- [ ] P6.1 端到端 demo：idea → PR
- [ ] P6.2 三仓 portal 合并到 5174 全局唯一 portal
- [ ] P6.3 全局交付验收：4 客户端 × 三类组件 × install/uninstall/doctor 矩阵全绿
