# T-158-1 / a1 阶段结果

**INCOMPLETE，待主控运行 RUN-OUTSIDE-03**。worker `b24-t158`，分支 `exec/t158`；产品基线 `c01742804961214ed025b6c9fb9924a1ea49ee2d`。

目标：按任务卡证明修订后正常重试成功，同时保留旧 attempt 活跃时的路径拒绝。不扩展到其他 ticket，不更改路径安全边界。

此前的决定阻塞见 [NEEDS-DECISION-01.md](NEEDS-DECISION-01.md)。主控 #36 已传回用户选择显式 reclaim 后释放；当前执行依据与文件范围见 [DECISION-01.md](DECISION-01.md)。

新增本票测试 `workbench/tests/test_t158_revise_retry_e2e.py`，含真实流程、帮助/角色说明检查、`--revision` 与三个 `--mutant`。产品改动仅为 `a2a help`、应用内主控说明、worker 角色说明与 README 的操作步骤，没有修改门禁。完整说明保存旧 attempt ID、保存 v2、显式采用、回收旧 attempt 和正常重派；写明未回收仍拒绝、未知处置不上调为成功、脏现场保留与路径占用分开。

验收状态：

| 验收 | 状态与证据 |
| --- | --- |
| 真实 Electron：打回 → v2 → revise → 对旧 attempt reclaim → 正常 dispatch 一次成功 | RUN-OUTSIDE-02 的后端十项检查全部通过；随后夹具 UI 选择等待错误，整体 INCOMPLETE，待 RUN-OUTSIDE-03 |
| 旧 attempt 未 reclaim 时继续拒绝 | 前两轮实际返回 path_overlap，冲突绑定原 attempt；两个路径变异待运行 |
| 角色说明与 a2a help 写明步骤 | 本地 PASS；红态、绿态与删除 reclaim 步骤的反例均已保存 |
| 完整真实流程、两个路径变异与既有 T-121 回归 | INCOMPLETE；RUN-OUTSIDE-03 待主控运行 |

文本检查（最新版测试，三项 errors 均为空）：

- `python3 workbench/tests/test_t158_revise_retry_e2e.py --check instructions --revision c01742804961214ed025b6c9fb9924a1ea49ee2d --summary evidence/2026-10-23-batch24/T-158/instructions-red-02.json`：exit 1；真实帮助入口 exit 0、五项可发现性失败。见 [红态](instructions-red-02.json)。
- 同命令去掉 `--revision`，summary 改为 `instructions-green-02.json`：exit 0、六项通过。见 [绿态](instructions-green-02.json)。
- 同命令加 `--mutant help-no-reclaim`，summary 改为 `instructions-mutant-02.json`：exit 1，只在帮助缺完整顺序的目标检查失败。见 [文本变异](instructions-mutant-02.json)。

这些检查验证帮助入口及说明内容可发现，不证明模型能自发照做，也不替代回收/重派的运行证据。之前的 `instructions-*-01.json` 原样保留。

## RUN-OUTSIDE-01 失败分类

主控 #38 回传目录 `/private/tmp/t158-outside-01.YXVx70`。原 [flow 摘要](t158-outside-01.YXVx70-flow-baseline.json) 与 [instructions 摘要](t158-outside-01.YXVx70-instructions-red.json) 原样保留。flow 不是有效产品红态：测试把输入正在发送时误判为空闲，门禁正确返回 `worker_working`。

从已停止夹具 `/private/tmp/t158-retry-kpfofdul` 的 SQLite 只读抽取原始时间线，见 [diagnosis-01.json](diagnosis-01.json)：

- orchestration #137/#138：`01:01:18.293Z` 开始并写入打回消息的 paste。
- gate #90：`01:01:18.393Z` 拒绝 reclaim，`worker_working`。
- orchestration #153/#154：`01:01:18.594Z` 才提交同一条打回消息。

因此该 reclaim 位于真实输入发送区间内。`panes.ts` 的 drain 在这段时间 `writing=true`，而夹具仅检查 `state=idle`、active/queue 为空。夹具现增加 `writing is False`，并在交付后、打回后、reclaim 前和新交付后保存实际 quiescence 状态；不增加 reclaim 重试，不接受 `worker_working` 作为成功，不修改产品判断。

重放诊断：`python3 evidence/2026-10-23-batch24/T-158/DIAGNOSE-01.py --fixture /private/tmp/t158-retry-kpfofdul --output <新 JSON 路径>`。脚本只读取已停止的夹具，数据库不入仓库；由主控按 T-088 归档。

## RUN-OUTSIDE-02 失败分类

主控 #41 回传目录 `/private/tmp/t158-outside-02.xbsX8S`，原 [flow 摘要](t158-outside-02.xbsX8S-flow-baseline.json) 原样保留。修正 writing 等待后的修前基线中，十项后端检查全部通过：旧 attempt 未回收时拒绝；显式 reclaim 成功；脏现场内容保留；不带交叠参数的一次 dispatch 成功，新 attempt 使用 v2，旧回收事件保留。

随后 `revised task selected` 等待超时，errors 有 traceback、没有失败业务断言。原测试把 SessionPane 的 `data-task-id` 当作任务选择标志；这是夹具错误，不能算产品红态。

定位证据见 [diagnosis-02.json](diagnosis-02.json)。已停止夹具 `/private/tmp/t158-retry-ze1cl8rx` 的任务布局事件只有 orchestration #197 的 `pane_layout_closed`（旧 launch），没有新 launch 的 `pane_layout_opened`。`store.ts:77`～95 据此得到 saved=true、openPanes=[]；`app/main.ts:668` 起的任务选择保留已保存的空布局；`renderer.tsx:366` 的 data-task-id 只在 SessionPane 上，而任务按钮本身用 `data-task-option` 与 `aria-current=page` 表示选中。因此任务切换正确时也不必渲染该终端选择器，增加超时不能修复这条错误等待。

原失败没有在清理前保存 DOM 或截图，不能补称已直接观察到按钮切换成功。新夹具先检查按钮可点，点击后核对 `aria-current=page` 与主进程 selection 的完整 task id；再明确点击新 worker 的 `data-agent-launch`，核对可见终端的 task、attempt、launch 三个身份并截图。后端十项断言不变，没有放宽成任意 pane 或跳过 UI。若再有环境/UI异常，清理前另保存 DOM 状态和失败截图。

本地 `zsh -n evidence/2026-10-23-batch24/T-158/RUN-OUTSIDE-01.sh` 与 Python AST 语法检查通过。一次 `python3 -m py_compile` 因系统 Python 想写沙箱外的 `/Users/luckye/Library/Caches/com.apple.python/...` 返回 PermissionError，未提权；语法检查改用不写缓存的 AST 解析，未把该环境错误算红态。

静态检查：Python AST、RUN-OUTSIDE-02/03 的 zsh 语法、`git diff --check` 通过；改动的产品说明保持 UTF-8 无 BOM、LF、无替换字符。本轮只改夹具、复跑脚本与证据记录，产品内容仍为 `2ca1204b3`；未修改全局配置或其他任务。临时夹具仅位于 `/private/tmp/t158-*`，不是项目额外目录；供应商模型回合数 0。

每轮启动及阶段记录完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。本轮末次输出保存到 `status-final-04.txt`；此前记录原样保留。

原阻塞问题条目为 `20261024T003159Z-worker:b24-t158-issue-001`；主控 #36 已传回上述裁定，worker 不自行关闭 blocking issue。

沙箱外请求：[RUN-OUTSIDE-03.sh](RUN-OUTSIDE-03.sh)。运行 `zsh evidence/2026-10-23-batch24/T-158/RUN-OUTSIDE-03.sh`；先跑修正两处夹具等待条件后的修前流程，再跑完整候选、release-before-reclaim 与 retain-after-reclaim 两个变异、既有 T-121。基线或候选异常立即停，不自动重试；摘要与日志每次新建，两个变异要求前置检查齐全且在各自业务断言失败。请主控回传生成的摘要前缀；夹具按 T-088 由主控归档。未请求提权，未在此启动后台或 Electron。

说明修复后的相关既有回归为 `workbench/tests/test_t121_role_request_e2e.py`（终端命令、主控身份与插件挂载）。若需要改门禁，再增跑 S3 的路径交集、clean revise、dirty revoke 与 historical cleanup 场景；不会把历史候选的通过结论当作本票证据。
