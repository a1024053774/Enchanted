# T-164-1 / a1 运行记录

状态：INCOMPLETE（额度停点）。执行主控 #83 确认本测试者 Codex 会话日志周额度已用97%、剩余3%，下令叫停。收到后没有再做 Computer Use，也没有再向应用内主控或worker输入；只整理本报告、findings和提交。没有完成可合并审查或集成，不报告PASS。

- worktree：`/Users/luckye/Documents/Code/a2a-wt-t164`，分支 `exec/t164`。
- checkout：`cbd3d4cf35ddba56fdf521360169bf5a91421c07`。
- 产品基线：`7d7cb8342b8642defda827f26a44c018e981948e`；`git diff --quiet 7d7cb8342b8642defda827f26a44c018e981948e -- workbench` 退出 0。
- 实例：`/private/tmp/t164-dogfood-xn9_oslt`；Electron 41077、daemon 41076（执行主控提供，启动记录与应用 URL 对应，未独立读取实时进程表）。
- repo：该实例下 `demo-repo`；UI 项目名 `demo-repo-2`。
- 启动由执行主控执行 `bash evidence/2026-10-23-batch24/T-164/START-APP.sh`。worker 未运行生命周期脚本。
- Computer Use 绑定专用 app 路径，renderer URL 属于本实例；未操作其他应用。

## 已走步骤

| 步骤 | 证据 | 结论 |
| --- | --- | --- |
| 打开本轮项目并启动指定 CLI | `screenshots/01-claude-start.png` | Claude Code v2.1.310，Haiku 5.5；只信任屏幕明确显示的本轮一次性 repo |
| 申请执行主控 | `screenshots/02-role-request.png` | 第 1 窗格、项目 demo-repo-2、申请 executor |
| 界面批准并确认 | `screenshots/03-role-confirmed.png` | 侧栏执行主控空闲；窗格头普通终端 · 执行主控 |
| 看记录 | `screenshots/04-role-approval-record.png`、`role-record.ax.txt` | 1 条批准，关联角色事件 #37 |
| 主控验收脚本自检 | `screenshots/05-controller-checker-selftest.png` | 有正确/错误样本，仍报告否定改述漏检 |
| 指标 | `screenshots/06-metrics-coverage.png` | 主控未覆盖、汇总未知，明确非全局总回合 |
| 混合CLI并行派发 | `screenshots/07-workers-dispatched.png` | A Haiku、B唯一Codex，独立worktree |
| 忙碌人工介入 | `screenshots/08-worker-busy-before-input.png`、`11-after-intervention-unknown.png` | A收到并回复；候选未交付，侧栏未知/窗格忙 |
| Codex上报与面板答复 | `screenshots/09-codex-worker-issue.png`、`10-issue-answer.png` | 先issue等待；面板答复平铺显示已送达 |
| 任务视图分屏 | `screenshots/12-task-split-keeps-worker.png` | 原worker保留，右侧普通终端 |
| 主控有界诊断 | `screenshots/13-bounded-diagnosis.png` | 两票not_submitted，不长轮询 |
| C正常交付 | `screenshots/14-c-submitted.png` | 门禁接受8749aa0d113fdb5f3f672d8c5c8abd26fcdd2ed4 |
| Codex收据人工恢复 | `screenshots/15-codex-pending-ack.png`、`16-codex-ack-after-enter.png` | 完整ACK停在输入区，一次Return后恢复，后续B交付 |
| 只读查看 | `screenshots/17-reviewer-readonly-no-focus-error.png` | 无focus-observation横幅；有文字重叠 |
| Reflect会话树 | `screenshots/18-reflect-models.png` | 两种CLI及角色配置；请求配置不当实际模型证明 |
| C真实独审打回 | `screenshots/19-c-review-rejected-b-review-started.png` | 弱验收/错误存在性断言，未集成 |
| B Codex独审 | `screenshots/20-codex-review-mutations.png` | 非清单鸡蛋和反向补货语义仍通过，结论需修复 |
| 未完成完整回收流程时重派 | `screenshots/21-revise-path-overlap.png` | A未reclaim即dispatch，path_overlap为有效拒绝，不能判F05回归 |
| 手动复盘 | `screenshots/22-haiku-reflect-started.png` | 确认Claude/Haiku/medium，状态进行中；定期复盘未开启 |

实际操作与原始提示见 `SESSION-NOTES.md`。首次目录选择误落上轮 T-155 夹具，未在旧项目启动终端或 agent，随后核对并切回本轮；旧项目条目仍保留。C1 的 typeText 丢失中文，仅发送英文词，Claude 未执行推送，等待任务；C2 改用 paste 并先截图确认全部中文约束后提交。这两项属于测试操作问题，不据此判产品缺陷。

## 当前预算与停点

应用内 Claude：已提交8个主控根提示（C1～C8），另有A/C worker、C独审、一次Haiku Reflect；原生日志终核未做，不给出伪精确总数，也不声称已独立证明总回合≤60。应用内 Codex：已观察恰好1个worker、1个对应reviewer，实际根回合数未能终核（额度停点）。外层Codex额度：#81报告7% left，#83依据会话日志确认剩3%，触发硬停止线。

派发前发现模型组合歧义，已获主控 #82 澄清，原文：“允许。用户原话限制的是 worker（‘应用内只用 1 个 Codex worker’），同时要求走到集成；产品规定 reviewer 与 worker 同 CLI 同模型，所以那个 Codex worker 的独立审查用产品自动给的 Codex reviewer，其余 worker 与 reviewer 都用 claude-haiku-5-5。这是执行主控的解释，我会在报告里列给构思主控；你在 RESULTS 里引用本条。继续推进到集成。”按该解释继续，不修改产品的审查模型契约。

最后已核对的任务停点：A人工介入后交付未知，修订v2后重派被旧路径挡住，reclaim曾worker_working；B人工回车后真实交付611ca29623…，机械通过但独审需修复；C初版8749aa0d11…机械通过但独审需修复，主控报告已按原目标强化README检查器至本地提交09dabd1，修订v2后未完成旧会话回收。旧C退回worker后上报受保护验收文件，未擅改。

## 留给执行主控的现场

应用和后台按#83保持运行，由执行主控处理；本测试者没有停止进程、重开UI、回收会话或清理目录。实例仍为 `/private/tmp/t164-dogfood-xn9_oslt`，repo为其下 `demo-repo`，state为其下 `state`。已知启动PID为Electron 41077、daemon 41076；收到#83后未再次核验进程或数据库。

下面是最后一次UI观测（C8输入前）的状态，不能冒充#83到达时的实时快照。最后输入C8已经提交，但它可能在后台继续执行，结果未观察，执行主控接手时须重新核对。

| 对象 | 身份 | 最后观测状态与确定事实 |
| --- | --- | --- |
| 执行主控 | Claude项目终端，launch ecfc3bb9-df4d-4959-bced-48b49d0b7bf0 | C7结束时侧栏空闲；之后收到C8，执行结果未知 |
| A worker | Haiku，attempt dbc83884-ebca-404d-948a-628d87e47ed9 | 侧栏未知、窗格忙；CLI完成回复且提交a3452b88…，门禁未接受交付；旧attempt已被revise撤销，任务v2待认领 |
| A reviewer | 未启动 | 没有独审记录可用 |
| B worker | 唯一Codex，attempt e53f84fe-a5e8-48e5-94eb-ef99ce5419c9 | 等待主控回答；候选611ca29623…机械通过，独审需修复；未集成、未另派Codex worker |
| B reviewer | Codex，review 674481ae-5c26-40e3-ab76-f9172f8f04fa | 侧栏已结束；需修复结论被门禁接受并回到worker |
| C worker | Haiku，attempt 8b58b55a-68a8-4a16-957e-f1c8483734af | 等待主控回答；初版已交付并独审打回；任务v2待认领，旧会话回收尚未观察成功 |
| C reviewer | Haiku，review 97ce2790-024d-4709-ae46-a850759ec7a1 | 侧栏已结束；需修复结论有效，保留失败 |
| Reflect | 手动Claude/Haiku/medium | 最后看见进行中，完成结果未核对 |
| 普通终端 | T-B任务分屏终端、Reflect项目终端 | 侧栏运行中；未手动输入业务命令 |

C8已纠正测试者跳过reclaim的操作，要求按README395～405的完整流程先确认pane_status idle/writing=false/active=null/queued=[]、门禁归档回收后再正常重派C；该结果未能复验（额度停点）。A旧会话未知不强制回收，B不新派第二个Codex worker。

未完成步骤：修复后可合并独审、集成/打分、完整修订回收复验、Reflect完成核对、REOPEN后的恢复、历史worker查看、最终原生日志回合/实际模型统计与原始证据归档。原因均为额度停点；此前的REOPEN请求不由测试者继续推进。无集成提交。原始现场在上述实例及本票对应的原生会话，未归档、未删除；仓库只交文本和22张小截图。

## 本 session 检查

`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`：开工与本次暂停前均 Problems 0 / Stale living docs 0。`git diff --check` 通过。没有改产品，没有运行产品测试套件；未做独立验收审查，不声明完整验收通过。

额度叫停后的提交检查：`git diff --cached --check` 退出2，唯一提示为原始 `role-record.ax.txt:28` 的尾随空格（AX文本“ · ”）。按保留原始证据要求不清洗该文件；此前未暂存新文件时的diff检查不替代这次结果。未新增产品测试或界面核验。
