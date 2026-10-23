T-141-1 / a1：已按本轮执行主控裁定，仅在 T-140 隔离 config.toml 加 demo 仓库 trusted，不改断言、检查名、期望或超时。

继续核对发现后续还有两个独立信任入口：workbench/tests/test_t140_extra_dirs_e2e.py:225-230 会新开 Codex reviewer，生产目录在 workbench/src/gates/core.ts 的 review-copies；同一测试 :233-240 又启动 Codex monitor，目录由 core.ts:3717 创建在 <state>/monitors/<thread>。这两处均非 demo 仓库后代，也没有隔离 trust 条目。根据主控已提供的三变体原生探针，demo 仓库信任不会覆盖这两个非 Git 目录，因此 demo 修复后仍可能在 reviewer/monitor 正确暂停。这是推断，尚未跑到两处，不报成已观察失败。

范围限制：本轮明确只授权 demo 仓库配置；我没有顺手信任整个 fixture、state 或另外两目录。
最小选项：执行主控可授权同一隔离 config.toml 额外信任已创建核对的 <state>/review-copies 与 <state>/monitors 两个夹具专用父目录，仍不改任何断言/超时；或先跑 RUN-OUTSIDE-03 取得实际后续失败后再裁定。当前不是阻塞项，其余 MCP 修复和交付脚本继续。
