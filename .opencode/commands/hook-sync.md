---
description: 把 registry/ 中所有 hook 的最新源同步到 4 个客户端（已安装的会被覆盖更新，未安装的不变）。
agent: hook-manager
---

# /hook-sync

对每一个 `registry/<name>/`：

- 如果该 hook 在某客户端已安装（按锚点检测）→ 用最新 source 重新生成 adapter 产物覆盖
- 如果未安装 → 跳过

用于"我改了 hook.py，把改动推到所有已装的客户端"。
