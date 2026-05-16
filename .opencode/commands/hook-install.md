---
description: 安装一个 hook 到指定客户端（或全部支持的客户端）。
agent: hook-manager
---

# /hook-install <name> [--client opencode|cursor|kimi|all]

调用 `agent/lib/adapter_<client>.py` 的 install 方法。

工作流：

1. 读 `registry/<name>/manifest.yaml`，校验 schema
2. 检查 `compatibility.<client>` 字段：
   - `native` 或 `adapter` → 继续
   - `unsupported` → 报错退出
3. **备份** 目标客户端配置文件 `cp <target> <target>.bak.{timestamp}`
4. 调用对应 adapter 写入配置（带 `# managed-by: agent-hook · <name>` 锚点）
5. 输出: 安装路径 + 备份路径 + 验证命令
