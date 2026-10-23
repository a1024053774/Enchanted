# T-141 执行主控裁定

- 2026-10-23T13:58Z：T-141 去掉 Codex `projects=untrusted` 后，受保护验收文件 `workbench/tests/test_t140_extra_dirs_e2e.py` 的隔离 CODEX_HOME 未配置信任，Codex worker 停在 Folder access（`codex_folder_trust_requested`，见 T-141 worktree `outside02-FMG476aF/t140.json`，fixture `/private/tmp/t140-fe2uko1b`），产品行为符合用户裁定（20261023T125315Z-ideation-answer-001 问题 2）。
- 裁定：允许 T-141 worker 只改该文件的夹具配置，在其隔离 CODEX_HOME 里把该测试创建并核对过的 demo 仓库标为 trusted；不得改断言、检查名、期望值或超时。
- 依据：AGENTS.md“真实 Codex 验收……只信任已核对的夹具根目录”；先例 T-146-1 中 T-137 只改夹具不改断言。属缺陷级夹具对齐，不改变验收条件。
