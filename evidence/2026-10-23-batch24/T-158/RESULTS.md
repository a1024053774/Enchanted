# T-158-1 / a1 交付结果

**PASS（本票交付检查）**。worker `b24-t158`，分支 `exec/t158`；修前基线 `c01742804961214ed025b6c9fb9924a1ea49ee2d`，通过完整验证的候选 `1c34ad29cd206eda21c07d902cb5e87f39b7f467`。此后仅补交证据与本文，不改产品或测试；执行主控的独立门禁审查、集成另行进行。

**产品门禁在修前已支持 reclaim 后一次派发；本票红态是 `a2a help` 与角色说明的五项可发现性检查。** 本票补齐完整步骤，没有修订门禁语义，也没有取消路径检查。

目标：按任务卡证明修订后正常重试成功，同时保留旧 attempt 活跃时的路径拒绝。不扩展到其他 ticket，不更改路径安全边界。

此前的决定阻塞见 [NEEDS-DECISION-01.md](NEEDS-DECISION-01.md)。主控 #36 已传回用户选择显式 reclaim 后释放；当前执行依据与文件范围见 [DECISION-01.md](DECISION-01.md)。

新增本票测试 `workbench/tests/test_t158_revise_retry_e2e.py`，含真实流程、帮助/角色说明检查、`--revision` 与三个 `--mutant`。产品改动仅为 `a2a help`、应用内主控说明、worker 角色说明与 README 的操作步骤，没有修改门禁。完整说明保存旧 attempt ID、保存 v2、显式采用、回收旧 attempt 和正常重派；写明未回收仍拒绝、未知处置不上调为成功、脏现场保留与路径占用分开。

验收状态：

| 验收 | 状态与证据 |
| --- | --- |
| 真实 Electron：打回 → v2 → revise → 对旧 attempt reclaim → 正常 dispatch 一次成功 | PASS；RUN-OUTSIDE-03 修前 flow 12 项、候选 18 项通过，原 attempt 被回收，新 attempt 的 task/spec/card/fence 及可见 pane 身份均核对 |
| 旧 attempt 未 reclaim 时继续拒绝 | PASS；实际 path_overlap 绑定原 attempt；提前释放变异在对应业务断言失败 |
| 角色说明与 a2a help 写明步骤 | PASS；修前五项失败、当前说明通过、删除 reclaim 步骤的文本变异被拒绝 |
| 回收后保留脏现场且释放路径 | PASS；sentinel 内容保留，正常重派一次成功；回收后继续占用路径的变异被拒绝 |
| 既有 T-121 终端、角色与插件回归 | PASS；49 项检查通过 |

## RUN-OUTSIDE-03 最终证据

执行主控 #43 回传脚本 rc=0；worker 核对五份摘要的候选、目标检查和 errors，结果如下。所有摘要原样提交，不把变异自身的 INCOMPLETE 状态改写成 PASS。

| 运行 | 结果与文本证据 |
| --- | --- |
| 修前 flow，`--check flow --revision c01742804961214ed025b6c9fb9924a1ea49ee2d` | exit 0，12 项通过、errors=[]；[flow-baseline.json](t158-outside-03.r3PP19-flow-baseline.json) |
| 当前完整候选 | exit 0，18 项通过、errors=[]；[candidate.json](t158-outside-03.r3PP19-candidate.json) |
| `--check flow --mutant release-before-reclaim` | exit 1，前置齐全，`unreclaimed_attempt_still_reserves_paths` 失败、errors=[]；[提前释放反例](t158-outside-03.r3PP19-release-before-reclaim.json) |
| `--check flow --mutant retain-after-reclaim` | exit 1，显式回收及 sentinel 保留已通过，`one_dispatch_after_reclaim_without_overlap_reason` 失败、errors=[]；[继续占用反例](t158-outside-03.r3PP19-retain-after-reclaim.json) |
| 既有 `test_t121_role_request_e2e.py` | exit 0，49 项通过；[T-121 摘要](t158-outside-03.r3PP19-t121.json) |

精确重放命令：`zsh evidence/2026-10-23-batch24/T-158/RUN-OUTSIDE-03.sh`。每次创建新摘要前缀和日志目录，不覆盖现有证据。主控本轮运行目录 `/private/tmp/t158-outside-03.r3PP19`。

本地辅助只读证据审查对冻结候选 `1c34ad29cd206eda21c07d902cb5e87f39b7f467` 返回 PASS、无范围内阻断发现，见 [acceptance-review-01.md](acceptance-review-01.md)。此审查不替代执行主控安排的受管独立审查或集成。

证据边界：真实 daemon、Git、PTY、Electron 与交互 Claude CLI；模型接口为本地脚本化 Messages，供应商模型回合 0。主控命令通过真实后台 socket，未逐条在用户终端手工输入全部 JSON；真实 `a2a help` 入口已运行。说明内容和资源绑定经过检查，但不证明模型将自行遵循说明；新 attempt 的 verify/integrate、崩溃恢复、其他权限边界和生产发布不在本票结论内。

只提交小文本。两张 PNG 已目视核对，保留在原 `t158-outside-03.r3PP19-{candidate,flow-baseline}-retry.png` 路径，未加入此提交，交执行主控归档。原始夹具、数据库、原生日志与 Electron 数据均留在摘要记录的 `/private/tmp/t158-*` 目录，由执行主控按 T-088 归档；worker 未删除或迁移现场。最初两轮夹具失败与下面的诊断原样保留。

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

静态检查：Python AST、RUN-OUTSIDE-02/03 的 zsh 语法、`git diff --check` 通过；改动的产品说明保持 UTF-8 无 BOM、LF、无替换字符。产品内容为 `2ca1204b3`，最终测试内容为 `1c34ad29c`；未修改全局配置或其他任务，没有改动项目额外目录。供应商模型回合数 0。

每轮启动及交付前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。本轮末次输出保存到 `status-final-05.txt`；此前记录原样保留。

原阻塞问题条目为 `20261024T003159Z-worker:b24-t158-issue-001`；主控 #36 已传回上述裁定，worker 不自行关闭 blocking issue。

RUN-OUTSIDE-03 已由主控完成，不再请求外部复跑。本票没有改门禁，未增跑完整 S3、8/9/18 或真实供应商模型场景，不引用这些旧候选的结论为本次变更背书。没有请求提权，没有 push 或集成。
