---
description: 体检：检查每个 hook 的 manifest 合法性、四客户端配置一致性、源脚本测试通过状态。
agent: hook-manager
---

# /hook-doctor

按顺序检查：

1. 所有 `registry/*/manifest.yaml` 通过 `agent/lib/manifest.py` 的 schema 验证
2. 每个 hook 的 `source/hook.py` 能被 Python import 不报错
3. 每个 hook 的 `tests/test_<name>.py` 跑通
4. 每个 hook 在四客户端的安装状态与 manifest.compatibility 是否一致
5. 客户端配置中是否有"孤儿锚点"（registry 已删但配置没清）
