T-153 迁移时发现，现行规格索引指向的 `.project-map/specs/native-cli-orchestration-2026-10-10.md:118` 仍要求 worker 只放行一个 socket、网络关闭；该处也未反映 T-075 最终采用请求文件与 Stop hook 的方案。

已关闭的 T-141 的 What to build / Resolution 明确记载用户“网络全开”，现行 `workbench/src/panes.ts:734` 设置 network_access=true。T-153 ticket 已授权把过时的关网络断言改到现行契约，本次以 T-141 为期望来源，不受此文档矛盾阻塞。

影响：后来者只按被索引规格读取，会恢复旧网络断言或误判现行产品。建议由有文档权限的主控核对 §5，并更新到 T-075 最终交付通道及 T-141 网络裁定。worker 不修改 spec、地图或其他 ticket。
