# T-258 a4：补齐已绑定 leader 失配反例

**PASS（本次 worker repair）；INCOMPLETE（整票门禁，待范围复审）**。新增两个进程身份反例后，候选完成条件 119/119 通过；删除对应生产守卫的同一 M5 变异被这两个业务断言检出。生产实现及真实 CLI E2E 驱动未改。

task `a2a+T-258-1`，attempt `7043f6b6-95a1-403d-a487-4587e2c02d62`，session `a5b9c655-b08c-4fda-84e2-9fbbcfca0280`，fence `4`，spec_rev `4`，repair `b4a5ce47-0612-4047-9c81-fbbc2803dddb`。原候选为 `9d6883239d2757e8899d1894999837c1e0b61617`，此次验证为 `2026-11-09T01:23Z`。请求的 worker 配置沿用 Codex gpt-6-astra、xhigh、普通速度；没有启动辅助 CLI 或 reviewer。

## 范围与变更

门禁 #87 报告：当前生产守卫正确，现有 117 案完成条件漏检已绑定非空 `runtime_identity.leader_pid` 被替换的错误实现。上一轮已复现并保存 [诊断报告](../a4-review1/RESULTS.md)及[逐案证据](../a4-review1/reproduction-01.json)，原报告与原始反例没有改写。

主控 #88 在当前会话明确了 repair 范围：“允许这次仅修改新增 test_t258_codex_late_start.ts 与本票 worker 证据，补 worker/reviewer 已绑定非空 leader PID 失配反例并保留 null 合法正例。”该消息同时明确同一 attempt 正常提交、只复审本修复范围一次，生产与 E2E 保持原字节，README/地图和安装由主控负责。此前等待范围澄清的 BLOCKED 停点由该消息解除，未改卡或重派。

`workbench/tests/test_t258_codex_late_start.ts` 新增 16 行，生成两个场景：

- `bound-leader-mismatch worker`：current_attempt.runtime_identity 的已绑定 leader=4099，pane/live leader 保持 4101。
- `bound-leader-mismatch reviewer`：review.runtime_identity 的已绑定 leader=4099，pane/live leader 保持 4101。

两案均要求 UPS 拒绝 `identity_conflict`，原启动失败、active 对象和 unknown 状态保留，写入次数仍为原始 paste/Enter 两次。现有 `leader-first-observed-late` 的 null 合法晚观察正例未修改。预期来自已定进程身份契约与审查反例，不由生产输出推导；没有扩展其他身份或时序检查。

## 反事实与完成条件

| 阶段 | 结果 | 证据 |
| --- | --- | --- |
| 修改前：M5 运行原 117 案 | 117 PASS，exit 0；错误实现存活 | `a4-review1/reproduction-01.json` 的 `m5-original-tests`。 |
| 修改前：两案诊断运行原候选 / M5 | 原候选 2 PASS、exit 0；M5 两案 FAIL、exit 1 | 同文件的 `sentinel-candidate` / `sentinel-m5`；失配输入拒绝缺失，实际 failed=null、state=busy。 |
| 修改后：候选完成条件 | 119 PASS，exit 0 | [checks-01.json](checks-01.json) 的 `candidate`；新增两案均记录 `identity_conflict`，null 正例 PASS。 |
| 修改后：同一 M5 运行相同完成条件 | 117 PASS、2 FAIL，exit 1 | 同文件的 `m5`；只有新增两案报 `Missing expected rejection: bound leader mismatch must refuse recovery`。null 正例仍 PASS。 |

M5 仅在自身源码副本把 `(bound.leader_pid === null || bound.leader_pid === pane.leader)` 替换为 `true`。候选与变异都执行 `/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t258_codex_late_start.ts`，用 `T258_SOURCE_ROOT` 选择产品副本，用 `T258_SUMMARY` 选择新的摘要。Node 为 v26.5.0，外层 cwd 始终是本 attempt worktree；依赖沿现有父目录 node_modules 只读解析。

重放命令：`python3 evidence/2026-11-08-batch34/T-258/worker/a4-repair1/run-checks.py`。再次运行时先将该小运行器复制到新的卡内证据目录；现有摘要存在时脚本拒绝覆盖。摘要保留每案名称、顺序、实际拒绝/失败断言、退出码、完整 node argv、源码版本、环境和清理状态，不保留重复 pane/数据库全文。

本轮没有重跑 T-257、原生来源或真实 CLI：本次只有测试补充，原 117 案在候选中均通过，产品源码、配置、冻结 oracle 与 E2E 驱动均未变化。原候选 T-257 104 案、原生来源 13 案及主控真实入口证据属于它们各自的运行记录；最终产品输入等价性和真实入口证据的适用范围由主控核对，不以本测试报告替代。

## 自查、清理与交付

本次 evidence-first-testing 自查确认顺序为“先复现缺口、再补测试、同一错误实现失败、候选通过”。未新增产品异常处理、fallback、兼容或平行 API；没有触及 design-integrity-review 的新结构风险。behavioral-acceptance-review 的独立复审由主控对本修复范围安排一次，本报告不自称已通过复审。

全部自有 SQLite/rollout 及源码副本均在记录目录、时间、文件数、字节数与结果后清理。未写额外目录、依赖、全局配置、正式后台或用户 hc。旧 a4 报告和小运行器继续对应原冻结快照，不改写为新 119 案证据。

[最终核对](final-readback.json) 保存产品与 E2E 逐字节不变、冻结文件无差异、仅允许路径变化和清理读回。[项目地图状态](map-status.json) 的唯一 stale 为 workbench/README.md，仍由主控按 #88 接续；不自行修改地图或 Verified。

本 repair 按原身份提交并显式 submit 新完整 SHA 一次，最终 SHA 由该提交和请求绑定。queued 仅表示请求排队，受理以门禁回执为准；worker 不运行 verify/integrate/自动 run/push。

**Works**：本轮候选 119 案通过，同一 M5 只有两个新增身份反例在业务断言上失败；原覆盖缺口已补齐。

**No regression**：原 117 案及 null 合法正例保持通过；产品实现、E2E 和冻结文件未改。未重跑无变化的真实 CLI 或无关全套。

**Risk / undo**：整票仍待本范围独立复审及主控后续门禁。撤回新增 16 行即可回到原完成条件，但会重新漏检 M5；生产无需回退，全部历史证据保留。
