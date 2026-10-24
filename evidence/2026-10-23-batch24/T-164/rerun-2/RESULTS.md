# T-164-2 / a1 运行记录

状态：INCOMPLETE（额度停线）。09:02:52.348Z会话日志5h已用90%、周已用14%，停止新的应用操作与模型回合，只整理证据并提交。随后执行主控也明确叫停，并通知将停止UI与daemon、保留状态文件；测试者之后不连socket。没有可合并审查或集成，C未派发。

- worktree：`/Users/luckye/Documents/Code/a2a-wt-t164b`；分支 `exec/t164b`；起点 `44ee947cfd337592242381d0dfb6d3d4fcc136d8`。
- 产品基线：实例 `instance.json` 记录 `5380ebb28ad53f0efec5447f7b0fcda8cc3bf727`。
- 实例：`/private/tmp/t164-dogfood-x339g6dx`；repo 为其下 `demo-repo`；Electron PID 60016、daemon PID 60015（主控 #84 提供）。启动记录中的 Electron 路径和 PID 与主控提供一致，窗口 renderer URL 对应该实例。实时进程表读取被沙箱拒绝，未提权或绕过。
- 启动由执行主控完成；测试者没有运行生命周期脚本，没有读取凭据文件。Computer Use 固定使用 `/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist/Electron.app`。
- 方式：Computer Use（`@oai/sky`，经 node_repl）；仅操作指定 Electron。业务流程不使用 CDP、DOM 注入、外部门禁命令或数据库驱动。

## 额度与回合

主控 #84 提供的开跑前读数：5h、周窗口均 100% left（已用 0%），原件位于主仓库 `rerun-2/quota-start.md`，本 worktree 没有复制或重建。当前工具没有外层会话 `/status` 入口；已通过异步问题请主控执行并回传。随后测试者只读本会话日志 `rollout-2026-10-24T04-10-13-01a16cf5-d7ec-71f0-bd1e-51db9a0df665.jsonl` 中的 `token_count.rate_limits`，08:13:53Z 的读数为 5h 已用 5%、周窗口已用 1%，据此继续。这是日志额度读数，不冒称 `/status` UI 操作。

截至 readback-01.json 的 orchestration event #1294：Claude 共 11 个根提示（主控 C1～C5 五个、A worker 四个、A 两次独审各一个）；应用内 Codex worker 六回合、独审一个，共七回合。没有 C worker、Reflect 或 monitor。真实回合口径：Claude 原生 JSONL 的非 isMeta user 记录，排除 tool_result，不把同一工作回合中的排队说明另算根回合；Codex 取每个实际 turn_context，并与 turn_start_signal 对照。所有记录仅限本实例；没有把模型自报或指标表当全局计数。尚无集成提交。

08:20:52.337Z 日志读数：5h 已用 17%、周已用 3%，见 `quota-observed.jsonl`。截至 C5 已提交 5 条主控根提示，A 另有两条测试输入；最终根回合按原生日志终核，不能用 UI 指标直接当全局总量。

## 步骤与证据

| 步骤 | 证据 | 观察 |
| --- | --- | --- |
| 核对初始实例 | `screenshots/01-initial.jpeg` | renderer URL 对应本轮 root，后台已连接，无项目 |
| 打开一次性项目 | `screenshots/02-project-opened.jpeg` | 主目录为本轮 demo-repo；main，无上游 |
| 新建项目终端 | `screenshots/03-project-terminal.jpeg` | 终端属于本轮项目；未输入 CLI 命令 |
| 启动 Claude 与信任 | `screenshots/40-cli-ready.jpeg`、`41-trust-before-selection.jpeg` | 自己输入 `claude --model claude-haiku-5-5`，只信任屏幕明确显示的本轮 repo；CLI v2.1.310 / Haiku 5.5 |
| 申请与批准角色 | `screenshots/06-controller-role-prompt.jpeg`～`09-role-confirmed.jpeg` | C1 申请执行主控；界面批准后已确认，侧栏与窗格头均标角色 |
| 三票需求 | `screenshots/10-three-task-prompt.jpeg` | C2 全文经 AX 核对后提交；包含混合 CLI、并行、打回与等待顺序，原文见 prompts.txt |
| 记录与指标 | `screenshots/11-approval-in-records.jpeg`、`12-metrics-coverage.jpeg` | 角色批准关联事件 #34；指标明确主控未覆盖、汇总未知、非全局总回合 |
| 任务卡与并行 | `screenshots/13-cards-preflight.jpeg`、`14-parallel-dispatch.jpeg` | A Haiku、B Codex；主控核对首轮漏总计和先提问等待顺序，披露语义检查局限 |
| Codex 问题回执 | `screenshots/16-codex-issue-ack.jpeg` | 门禁 #3 已被自动确认，底部 GPT-6.1-Sol high，无测试者 Enter |
| 面板答复与唤醒 | `screenshots/17-answer-draft.jpeg`～`19-codex-answer-started.jpeg` | 答“不分组”；约几秒内已 Working 4s，模型仍 high，无测试者 Enter |
| 流程与 A 真实打回 | `screenshots/20-flow-parallel.jpeg`、`21-a-repair-working-before-input.jpeg` | A 首候选 f9458781447e83418d9d2399df3c1f86a61d62e1，真实 oracle_failed：global total 6 missing；修复回合仍显示 Razzmatazzing |
| A 工作中人工介入 | `screenshots/22-input-during-a-repair.jpeg`、`23-a-intervention-progress.jpeg` | 输入时修复回合仍在运行；CLI 收到说明并在原 attempt 重交 0ac73a86e4fd4d97a486dc1aa262b12a1bacf0fb，门禁候选已更新 |
| A 交付阶段再次输入 | `screenshots/24-input-at-delivery.jpeg`、`25-a-after-second-input.jpeg` | 交付后/回执阶段输入，CLI回复；侧栏未知。第二次并未独立证明恰落 Stop hook 内，须按日志核对，不夸大 T-157 覆盖 |
| 任务分屏 | `screenshots/26-task-split.jpeg` | 左侧保留 B Codex，右侧普通项目终端，未向普通终端输入命令 |
| 只读审查与滚动 | `screenshots/27-codex-reviewer-readonly.jpeg`～`31-codex-review-progress.jpeg` | 两种 CLI 独审可读；未见 focus-observation 横幅、重叠黑块；Codex reviewer 底部仍 high |
| A 协议拒绝与重开 | `screenshots/32-review-paused-issue.jpeg`～`34-review-restart.jpeg` | JSON 前出现说明文本，被门禁拒绝并保留原文；经问题页为同次交付新开干净审查 |
| B 独审打回及回执 | `screenshots/35-codex-review-rejection-started.jpeg`～`37-codex-review-rejected.jpeg` | 额外鸡蛋、香蕉“禁止采购”仍过核心检查。B收到打回并复验后正确issue，门禁 #13 已自行进入 Working 1s，模型仍high |

有效 AX 输出与时间已从本测试者原始工具返回恢复到 `ax-tool-outputs.json`；旧保存器输出仅作为采集错误保存在 `capture-error/ui-observations.txt`，不作为业务证明。目录选择器初次快捷键/粘贴连发后仍显示旧路径，测试者在确认前用 AX set_value 改为本轮路径并逐屏核对，未打开旧项目；这是测试操作时序问题，不据此判产品缺陷。

测试者在本隔离窗口的设置中开启“启用屏幕阅读器支持”，用于经可访问性树读取终端文本；没有改系统设置或全局配置。申请批准按钮在设置关闭后的首帧不可用，点击申请所在终端取得焦点后可用，随后正常批准；未改后台状态。

主控 C2 曾把服务档位 default 当作 run_mode；C3 已澄清是 Codex 服务档位（不使用 Fast），运行权限仍 workspace-write。主控自述 A effort medium，产品默认映射事实未据此判缺陷。A/B 独审副本没有 Git 元数据，而主控写的检查器使用 `git show main:pantry.json`，原命令因此失败；reviewer 分别披露环境限制，并额外运行同一核心检查做反例，没有把核心检查替代完整命令的绿态。

B 修订需要新 attempt，测试者已异步询问外层主控：“恰好 1 个 Codex worker”是否允许回收旧 B 后同票重派（始终一个活跃）。口径未确认前不推动 B 修订/回收/重派；A/C 按已有授权继续。

## 事后核对与 T-167

实际观察暂停后，测试者用只读 SQLite 连接和本实例 Claude 原生日志核对已见现象，未用查询结果驱动业务。可重放选定事实的命令（必须使用新的输出文件名，不覆盖旧结果）：

```sh
python3 evidence/2026-10-23-batch24/T-164/rerun-2/readback.py /private/tmp/t164-dogfood-x339g6dx /private/tmp/t164-readback-next.json
```

脚本不读认证、operator.json 或 launch env；只输出选定身份字段、回合上下文、时间与事件引用。完整启动 argv、原始 PTY 和模型会话仍在隔离实例内，由执行主控按卡处理生命周期和归档。本报告没有复制认证，也没有清理任何目录。

B 的后续五条消息（门禁 #3、用户 #5、门禁 #7、#11、#13）均有 turn_submitted→turn_start_signal，延迟为 0.118、0.120、0.120、0.142、0.098 秒。没有人工 Enter；屏幕与 native turn_context 的 model/effort 一致，worker 六个、reviewer 一个均为 gpt-6.1-sol/high。启动冷路径另列：worker 9.202 秒、reviewer 6.396 秒，不混入回执统计。服务档位请求 default，实际 tier 无独立证明。单轮观察不能证明稳定可靠或更省额度。

A 的工作中输入：#674 claude_prompt_queued，#728 Stop，#732 重交受理；第二次输入：#760 user_prompt_unregistered，#763 新 UserPromptSubmit，#767 Stop。第二输入在 08:20:33，晚于 08:20:22 的 Stop，不冒称落在 Stop 内。状态未知与无法回收有屏幕证据；未读产品实现确定根因。

## 第一阶段暂停时的现场（后续继续运行见下节）

截至图39（主控 C5 结束）：A 卡 v2、spec_rev 2，current_attempt 为空；旧 A worker 侧栏未知，reclaim worker_working，没有新 A attempt。B 仍是原 attempt，独审需修复后正确上报验收文件问题，等待答复，没有新 B worker。A 首次审查协议被拒后，经界面新开同次交付审查，该审查有效结论为需修复。C5 主控未派 C，理由是产物未集成不应宣称存在；C 尚未建立，测试者没有代为写文档或绕过它派发。

| 对象 | 身份 | 最后确定事实 |
| --- | --- | --- |
| 执行主控 | launch 682c9ffb-f842-48d7-b5a4-4a6d76d37d1c | Haiku，C5 结束空闲；本地 dogfood 检查器修订提交 4959aa9 |
| A worker | launch c55be686-692e-4059-bf8e-031e1e66c9a1；attempt 76b562a0-a845-4ef5-8e0f-2cc4ad3078cf | 原 spec_rev 1，已被 revise 撤销；曾交付 f945878144…、0ac73a86e4…；最后侧栏未知，回收被拒 |
| A 首次 reviewer | launch 007dafb2-5a45-4828-b751-408314a5d22d；review 5c4d583b-2e79-4fca-8345-be32e3d50834 | JSON 前说明导致协议拒绝，原文保留，已结束 |
| A 第二 reviewer | launch cff7848c-64e2-40fa-9126-9dad40115bea；review f8a695f6-7d6a-4602-960a-c1160b46ec9e | 需修复检查器，已结束 |
| B worker | launch 04fe0c28-d9ba-4a52-8536-f4e739c419a6；attempt a4eed566-5878-424d-bc59-e026b15ba747；session 525ad58f-b674-4dfb-a18e-8b0b18eb5d03 | fence 1 / spec_rev 1；候选 bc4e1813b8a58bc53e592d9bebfa52d33c737e88；独审后 issue #2，等待答复 |
| B reviewer | launch 3ba01bf9-73d0-4e09-974b-6defeabfc0df；review 180b9eeb-97f0-48c8-b34d-ebbf1480a68b | 原候选需修复，已结束；纯 JSON 结论被门禁受理 |

当时REOPEN请求已发出，尚未收到新PID。这段为原暂停时点记录，不代表最终未完成清单。原始实例归档与隔离CODEX_HOME清理由执行主控处理，测试者不清理或归档沙箱外目录。报告未做独立验收审查。

阶段末外层额度日志 08:30:04.343Z：5h 已用 32%、周已用 5%，未触发任一窗口 ≥90% 停止线。停止推进依赖的是明确口径、新 PID 和已观察到的 A 回收拒绝，不是额度耗尽。

执行主控随后回复：08:35:58Z 本会话 rate_limits 为 5h 已用39%、周已用6%，来源是会话日志而非 /status；开跑前两窗口100% left。另明确允许同票回收后重派，始终仅一个活跃 Codex worker。B 重派口径已解决；REOPEN 新 PID 仍待回复，尚未恢复 Computer Use。

## 口径答复后的继续运行

执行主控随后确认 REOPEN：新 Electron PID 77811，旧60016退出，daemon60015未动，实例不变。测试者重新核对窗口URL后只操作新窗口。主控会话、worker与审查历史仍在；B任务的左右分屏保留（图42～45）。本窗口屏幕阅读器设置需重新开启，未改系统设置。

外层对B的明确答复原文：“允许同票回收后重派，活跃仅 1 个”；REOPEN答复还要求“重派前确认旧 B 会话已回收”。C6转述后，应用内主控修订v2并经门禁回收a1，再派a2（eff3c4aa-79eb-4a97-98b4-54dd6fbecca3），基底71bf027bcfe472bfb4b7a6f6d19c165ab6a90b97；a2交付ebac0371ef05b523bd39ce65f606de937e9f9eee。独审07d382ba-ae61-46ab-af55-8ff92fe89744发现分类标题分组仍过，需修复；完整命令仍因Git依赖无法在副本运行（图47～53）。

C8要求在原目标内同时处理分组和副本执行条件。主控将原始数据副本及pantry.json列入保护、去掉Git读取依赖；在无Git副本原样运行正式命令及变异，再经门禁修订v3、回收a2后派a3（8b907e04-654a-4228-8071-1276d6615da9），基底b2c0cf5。a3交付9e7ac7ec9d583cddd586e4fe6025b6a3cdeb96f2，自动确认回执；C9触发verify，机械通过，独审f485544c-a68b-43b1-8b80-61cfd905b8fc进行中（图56、57）。每次都先回收旧B，没有并存两个活跃Codex worker。A没有再次回收或强制。

手动Reflect明确选择Claude Code/claude-haiku-5-5/medium，已完成一次，范围最早记录至08:41:51.504Z（图51、54、58），不是最终运行全量复盘；8条建议均未批准或拒绝，定期复盘保持关闭。报告路径为实例state/retrospectives/bfeafc7a-2bb4-4cc3-9094-2ec40093fe51/report.md。复盘建议引用测试者关于pane_status的指令，但实际角色调用此命令被拒，不能把建议当该能力存在的独立证明。

08:42:35.669Z测试者日志额度：5h已用52%、周已用8%，见quota-observed.jsonl。后续终核会另存新readback文件，不覆盖第一阶段证据。

## 检查

开始时 `project_map.py status --root .`：Problems 0、Stale living docs 0。工作树开始时干净。未改产品或验收文件，未运行产品测试套件。

阶段交接前再次运行status：Problems 0、Stale living docs 0。第一阶段暂存差异检查退出0（staged-check.json）；最终加入新窗口原始AX后，完整检查退出2，70处均为ui-observations-current.txt原样尾随空格，保留而不清洗证据。报告、索引、RESULTS与只读脚本的限定差异检查退出0。实际回读文档为UTF-8、无BOM、无替换字符。截图引用首次校验误把文档中的glob当文件，修正校验后没有缺失引用，见final-validation.json。未用整理检查替产品验收背书。提交号见交付消息。

## 采集错误与恢复

提交前按文件体量检查并实际打开图19，发现跨 node_repl cell 的保存函数捕获了旧变量：02～38命名截图误存同一目录选择器，旧 AX 文件也重复保存旧树。这是测试者的采集错误。原始错误文件完整移入 `capture-error/`，没有删除、覆盖或当成通过证据。

Computer Use 服务保留了每次真实 get_app_state 的原始 JPEG。按保存调用时间与原始文件时间恢复为 `screenshots/*.jpeg`，映射及时间差在 `screenshot-recovery.json`；追加图39为C5结束、图40为CLI就绪、图41为信任前目录屏。图29/30的原始文件同秒复用，只支持最后一张画面；图05的选项选择瞬间未独立保留，不用它证明选择。旧 `.png` 扩展名也是保存器错误，恢复文件沿用真实JPEG格式。已实际打开并核对恢复图09、19、21、26、33、39。

有效AX文字从外层原始session日志的62条相关工具返回中选取（按call_id关联包含get_app_state的调用，仅取AX文本，排除图像编码与其他工具输出），保存在 `ax-tool-outputs.json`。它与屏幕观察、原始服务截图、隔离后台readback分开标明来源。恢复没有操作Electron或重跑业务。

## 最终交付现场

B后续继续：v3独审检出Markdown加粗类别标题；v4独审检出HTML实体类别标题与Setext多标题；v5独审检出嵌套列表和HTML h2标题。五次有效独审均为需修复，未以本地自检通过替代接受。v4候选805b3b7…，attempt edcf7f5a-c37c-4b7f-b7f4-7f495001a456，基底e9e32bb；v5候选b5d4b0e4d9c1f66a3d067d1b9ad25d44f4246b93，attempt 383fed7e-a0ee-4098-906c-ebf868e8fb0d，session 6b0dde03-05a3-4c94-a754-647581ce545a，fence/spec_rev均5，基底27107c6bdf83279c6832d1063af74f57be888274。B每次都先回收旧attempt再重派，累计5个worker会话，任何时刻只1个活跃。重派口径由外层明确授权，不冒称累计仅启动1个。

最终只读摘要readback-03-final.json截止orchestration event #3478：Claude根回合20个（主控C1～C13共13、A worker4、A两次独审2、Reflect1）；Codex回合27个，来自B五个worker及五个独审。17次后续门禁回执/打回与用户答复均自动开始，提交至开始0.098～0.188秒。27个原生turn_context均gpt-6.1-sol/high。新会话初始化公告回放含default强度文字，不能宣称初始化所有帧也为high；工作回合没有模型切换证据。

最终任务事实见final-task-state.json：A为ready/spec_rev2，无current_attempt，旧worker未知且未回收；B为submitted/spec_rev5，当前候选为上面的v5；integration_intent为空。门禁events表中包含integrat字样的事件数为0，没有集成提交。该JSON只挑选少量字段，其中verification所选键的null不表示此前没有机械通过，机械通过与随后独审拒绝的证据见实际UI和原始事件。

最终Codex读数：09:01:46.395Z为5h89%/周14%；09:02:52.348Z为5h90%/周14%，触发硬停止线。自看到90%起未再操作应用、发起应用内回合或连接socket。随后执行主控明确要求仅完成文档与提交，并通知停掉UI/daemon、保留状态文件；测试者未声称独立确认进程退出。当前只读状态文件不作运行实例仍存活的证明。

未完成：任何可合并独审/集成/打分、C派发、A安全回收重派、第二新实例复现和运行归档。REOPEN、B四次完整修订回收重派、一次真实Haiku Reflect已完成。原始运行及隔离home的归档/清理由执行主控负责。没有本轮外部独立验收，最终状态INCOMPLETE。

新增截图42～63与AX保存在ui-observations-current.txt，保存函数改为显式传入当前state，避免旧闭包；已核对新图片大小随画面变化。图49可能仍处于切换首帧，B a2交付与模型以图50及readback为准。图52是独审首次载入，具体拒绝用图53。最后应用观察为图63（B第五次独审反例），停线后没有补截。
