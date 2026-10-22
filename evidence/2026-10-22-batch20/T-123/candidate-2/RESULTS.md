# T-123 候选 2：处理审查 01 的发现

日期：2026-10-22。基线：候选 1 `f0188d772`（其父提交 `4116c8b44`）。候选：本目录随附提交。执行与验收：执行主控（Claude Code）。

结论：**PASS**（候选级：端到端绿态，修前版本与 9 个已知坏实现的端到端红态，迁移单元测试的修前版本与 2 个坏实现红态都已取得；独立复审另行进行，结论见同目录审查文件）。

## 相对候选 1 的改动

逐条处置见 `review-01-disposition.md`，摘要：

- 任务 id 的格式规则（`taskIdPattern`）移到 `contracts/a2aMembership.ts`，契约、门禁、中继、审查协议共用这一条。
- 迁移：成员资格里尚未迁移的 id 也进入改名集合，两库之间中断后，下次启动接着做完；`relay_requests.input` 的 JSON 一并改写。
- CLI：带 task 的命令都允许 `--project`。
- `workbench_snapshot` 改为与解析后的完整 id 比较。
- ticket 计划原文改清楚：删除的是 `card_draft_owned` 机制，已有的历史事件原样保留。
- README 补充迁移的上述行为。

## 端到端证据（`e2e/`）

命令：`e2e/commands.sh`，从 `workbench/` 运行。

| 运行 | 结果 | 停在 |
| --- | --- | --- |
| green-01（T-123 全场景） | PASS，22 项 | — |
| red-01-parent（`--revision 4116c8b44 --scenario same-name`） | 失败 | `same_name_created_in_both_projects`：beta 的同名任务被拒 |
| red-02-global-task-id（`--scenario same-name`） | 失败 | `same_name_created_in_both_projects`：`card_version_conflict` |
| red-03-ambiguous-name-picks-first | 失败 | `bare_name_ambiguous_for_operator` |
| red-05-migration-skips-events | 失败 | `legacy_task_in_its_project`：事件仍挂在 `T-0`、`T-D` |
| red-06-gone-only-first-restart（T-128） | 失败 | `migrated_attempt_reclaimed`：`unknown_pane` |
| red-07-full-id-ignores-project | 失败 | `other_project_refused_and_recorded`：四条跨项目请求全部通过 |
| red-08-migration-ignores-drafts | 失败 | `legacy_draft_in_its_project`：`unknown_card_version` |
| red-09-cli-refuses-project | 失败 | `cli_bare_name_with_project`：CLI 报 `invalid command arguments` |
| red-10-snapshot-raw-name | 失败 | `snapshot_by_bare_name`：`launch_task_mismatch` |
| t121-green | PASS，49 项 | — |
| t121-red-foreign-key-unchecked | 失败 | `other_project_task_and_repo_refused` |
| t122-green | PASS，23 项 | — |
| t124-gui-green（真实 Electron 窗口） | PASS，28 项 | — |
| t124-restart-working | PASS，19 项 | — |
| t124-restart-verified | PASS，26 项 | — |
| t127-green（真实 Codex，用户的 `~/.codex`） | PASS，19 项 | — |

green-01 在候选 1 的场景上新增了以下检查（候选 1 的场景见 `../candidate-1/RESULTS.md`）：
- 修前版本的终端保存一个未建任务的草稿 `T-D`，旧库里确有一条 `card_draft_owned`（`legacy_library_has_owned_draft`）。
- 迁移后草稿归入 `legacy+T-D`，可读（`legacy_draft_in_its_project`）。事件改挂 `legacy+T-0`、`legacy+T-D`；`card_draft_owned` 历史条数不变，最后也没有新写入（`no_new_draft_ownership_records`）。
- 迁移后用裸名 `T-0` 取窗口快照，得到完整 id 与对应 launch（`snapshot_by_bare_name`）。
- 管理凭据经真实 CLI 用 `status --task T-1-1 --project beta` 取到 `beta+T-1-1`（`cli_bare_name_with_project`）。

## 单元证据（`unit/`）

命令：`unit/commands.sh`。

- test_relay_core、test_t078_controller_relay、test_t078_relay_role、test_t096_restore、test_t124_quota_notice、test_t109_hierarchy 全部退出 0。
- `tests/test_t123_migration_resume.ts`：只用门禁库，不经后台。三种情形：修前写出的库整体迁移（含 `relay_requests.input`）；任务库已迁移而成员资格未迁移的中断状态，下次启动做完；再启动一次什么都不变。
  - 绿态 PASS（3 项）。
  - 修前版本（`4116c8b44`）失败在第一种情形。
  - 去掉成员资格续迁的坏实现，第一种情形通过，失败在中断情形。
  - 去掉 `input` 列改写的坏实现，失败在第一种情形。

## 验收条目

T-123 与 T-128 各条的依据同候选 1，在本候选上全部重跑，结果见上表。另外两点：
- “已有库迁移”一条现在也覆盖了未建任务的草稿，以及两库之间中断后的续迁。
- “`card_draft_owned` 与相关检查删除”：删除的是机制；历史事件按追加式记录保留。见 ticket 计划原文的修订。

`project_map.py status`：提交前运行，0 问题、0 过期文档。

## 未覆盖与已知限制

- 后台同一时间只跑一个 worker（`single_worker_slice`），两个项目的同名任务依次派发。
- `test_task_cards_e2e.py` / `test_daemon_gates_e2e.py` 在 HEAD 上就失败，`test_relay_scope.ts` 在 HEAD 上就失败，`test_t107_sidebar.mjs` 因 git 中文输出失败。这几项都未作为证据（详见候选 1）。
- 没有做 TypeScript 类型检查（本机未装）。
- `pane_layout` 的布局键按调用者给的 task 字符串；界面只传完整 id，未改。
- 迁移留下的旧 `locks/<旧 id>.sqlite3` 不清理：操作锁保留 inode、从不 unlink。
- T-129（Claude reviewer 协议失败记不下）仍开着，不在本候选范围。

## 夹具

端到端夹具已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-22-batch20/T-123/candidate-2/fixtures/`。清单见 `fixtures.archive.json`：17 项，15 项已归档，其余 2 项是 T-121 测试结束时自行删除的。归档时逐个核对了文件数与字节数。迁移单元测试的临时库在 `/tmp/t123-migration-*` 下，很小，已删除。
