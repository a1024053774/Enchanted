# T-123 候选 1：任务 id 与卡片按项目区分

日期：2026-10-22。基线：`4116c8b44`（T-124 关闭）。候选：本目录随附提交（`4116c8b44` 之后的工作区改动）。执行与验收：执行主控（Claude Code）。

结论：**PASS**（候选级：端到端绿态、修前版本与 6 个已知坏实现的红态都已取得；独立审查另行进行，结论见同目录审查文件）。

## 做了什么

- 门禁里的任务 id 改为 `<项目>+<任务名>`（`src/gates/core.ts`：`taskKey`、`resolveTask`）。终端主控只写任务名时在本项目解析；管理凭据不带项目时任务名须恰好对应一个已有任务（否则 `task_ambiguous` / `unknown_task`）；完整 id 旁另给不同项目返回 `task_project_mismatch`。
- 后台删去 `card_draft_owned` 及相关检查（`src/daemon.ts`）。跨项目的拒绝只在门禁一处做：终端的项目经 `GateActor.project` 进入解析，另一个项目的完整 id 在门禁返回 `task_project_mismatch`。
- 旧库迁移（`migrateTaskIds`）：后台启动时把各表与成员资格里的旧 id 改为 `<原项目>+<原 id>`，只改不增删行；任务数据补 `name`；触发器先删后重建；没有归属项目的卡草稿使迁移失败（`task_migration_unowned_drafts`）。
- 中继与审查协议按完整 id 校验 task（`taskIdPattern` 统一放在 `src/gates/qualityProtocol.ts`，门禁、中继、审查协议共用）。
- 界面与侧栏显示任务名：侧栏行加 `task_name`，流程页、窗格标题、任务眉题改用任务名；`A2ATask` 加 `name` 字段。worktree 与分支路径仍按项目目录加任务名，不变。
- 端到端中发现并修复 T-128：后台第二次重启后，曾被恢复过的 worker、reviewer、monitor 不再登记或恢复（`src/panes.ts`）。T-128 是本次自建的缺陷级 ticket，验收见下文。

## 端到端证据（`e2e/`）

命令：`e2e/commands.sh`（回归套件与第一轮 T-123）与 `e2e/commands-02.sh`（T-123 绿态与红态的第二轮，原因见“过程中的问题”）。均从 `workbench/` 运行。

| 运行 | 结果 | 停在 |
| --- | --- | --- |
| green-01（T-123 全场景） | PASS，18 项 | — |
| red-01-parent（`--revision 4116c8b44 --scenario same-name`） | 失败 | `same_name_created_in_both_projects`：beta 的同名任务被拒（`role_project_mismatch`） |
| red-02-global-task-id（`--scenario same-name`） | 失败 | `same_name_created_in_both_projects`：beta 的卡 `card_version_conflict` |
| red-03-ambiguous-name-picks-first | 失败 | `bare_name_ambiguous_for_operator`：裸名直接取了第一个 |
| red-05-migration-skips-events | 失败 | `legacy_task_in_its_project`：事件仍挂在旧 id `T-0` |
| red-06-gone-only-first-restart（T-128） | 失败 | `migrated_attempt_reclaimed`：`unknown_pane` |
| red-07-full-id-ignores-project | 失败 | `other_project_refused_and_recorded`：另一个项目的完整 id 四条请求全部通过 |
| t121-green | PASS，49 项 | — |
| t121-red-foreign-key-unchecked | 失败 | `other_project_task_and_repo_refused`：另一个项目的 status、card_save 不再被拒 |
| t122-green | PASS，23 项 | — |
| t124-gui-green（真实 Electron 窗口） | PASS，28 项 | — |
| t124-restart-working | PASS，19 项 | — |
| t124-restart-verified | PASS，26 项 | — |
| t127-green（真实 Codex，用户的 `~/.codex`） | PASS，19 项 | — |

green-01 的场景：
- 修前版本写出一个旧库（项目 `legacy`、任务 `T-0`，已派发并交付）。
- 新版启动时迁移：9 张表行数不变；任务、卡片、事件都归入 `legacy+T-0`。
- 旧 attempt 经门禁回收、重新派发，然后审查并集成。
- 两个项目 alpha、beta 各建同名任务 `T-1-1`，id 为 `alpha+T-1-1`、`beta+T-1-1`。两边的终端各自读到自己的卡。
- alpha 终端以完整 id 请求 beta 任务：status、card_save、card_show 与 beta 下新草稿四条请求都返回 `task_project_mismatch`，并以失败的 `request_result` 记录，来源是 alpha 终端；beta 的卡不变。
- 管理凭据只写裸名时返回 `task_ambiguous`；完整 id 旁给出不同项目时返回 `task_project_mismatch`，两边都不落卡。
- 两个任务依次派发、交付、审查、集成：提交尾注 `A2A-Task` 是完整 id，各仓库内容各自正确，两条记录相互独立。侧栏行 `task` 为完整 id，`task_name` 为 `T-1-1`。
- 最终库里没有 `card_draft_owned`。

## 单元证据（`unit/`）

命令：`unit/commands.sh`。test_relay_core、test_t078_controller_relay、test_t078_relay_role、test_t096_restore、test_t124_quota_notice、test_t109_hierarchy 全部退出 0。

## 验收条目

- 两个项目各建同名任务，各自走完整流程互不影响，后台库读回两条独立记录：green-01 `two_independent_records` 等。**满足**。
- 一个项目的终端看不到、改不了另一个项目的同名任务和卡片（门禁拒绝并留记录）：green-01 `other_project_refused_and_recorded`、`other_card_unchanged`；t121-green。**满足**。
- 已有库迁移：迁移前后任务、卡片版本、事件条数一致，旧任务归入原项目：green-01 `migration_keeps_counts`、`legacy_task_in_its_project`。**满足**。
- `card_draft_owned` 与相关检查删除；T-121 端到端改为验证新身份后全部通过：t121-green 49 项。**满足**。
- 修前版本在同名任务场景失败：red-01-parent。**满足**。
- `project_map.py status` 0 问题：提交后运行，见提交说明。

T-128：
- 后台连续重启两次后，交付过的任务仍能 verify、审查、集成：green-01 `migrated_attempt_reclaimed`、`migrated_task_continues_to_integration`。**满足**。
- 去掉修复的变异失败于 `unknown_pane`：red-06。**满足**。
- T-124 两个重启变体仍通过。**满足**。

## 过程中的问题（均保留现场）

- `e2e/aborted-01-source-edited/`：第一轮运行期间改了 `core.ts`，测试从工作区启动后台，结果混入两版候选，整轮作废。
- `e2e/superseded-01-duplicate-daemon-check/`：terminal-key-unchecked 与 T-121 foreign-key-unchecked 两个变异被门禁新加的检查拦下，只是错误码不同，不是有效红态。这说明后台的前缀检查与门禁重复，已删去后台那条。修前版本在这一轮停在迁移阶段，没走到同名场景，因此新增 `--scenario same-name`。
- `e2e/superseded-02-rejection-record-form/`：门禁的拒绝记为失败的 `request_result`，测试原来只找后台的 `request_rejected`。只改了测试的读取方式，`src` 未变；T-123 的绿态与红态重跑，同一轮的 T-121/122/124/127 结果仍有效。
- `unit/superseded-01-*`、`unit/superseded-02-*`：候选后来又改过，单元证据按最终候选重跑。
- 开发运行中还发现：Claude reviewer 的结果格式不对时，门禁记不下审查协议失败（`failReviewProtocol` 的身份缺 `prompt_id`）。这与 T-123 无关，另开 T-129，未在本候选修。

## 未覆盖与已知限制

- 后台同一时间只跑一个 worker（`single_worker_slice`），两个项目的同名任务是依次派发，不是同时派发；验收条目不要求同时派发。
- `test_task_cards_e2e.py`（及继承它的 `test_daemon_gates_e2e.py`）在 HEAD 与候选上都失败（53 处，需要 `control.sock`），属既有问题，未作为本候选的证据。`test_relay_scope.ts` 在 HEAD 上也失败，未使用。`test_t107_sidebar.mjs` 因 git 输出为中文而失败，与本改动无关。
- 本机没有装 TypeScript，没有做类型检查；类型相关的改动由上述端到端与单元运行覆盖。
- 用户的真实工作台库（`~/Library/Application Support/a2a-orchestrator`）只读复制检查过：没有任务也没有卡草稿，迁移是空操作。复制品已删除。
- T-121 测试结束时自行删除夹具，所以清单里它的 4 个夹具标为“归档前已不存在”。

## 夹具

夹具目录已归档到外置盘：`/Volumes/WD-Elements/a2a-evidence/2026-10-22-batch20/T-123/candidate-1/fixtures/`。清单见 `fixtures.archive.json`（42 项，38 项已归档）。归档时逐个核对了文件数与字节数。
