# 最终输入版本的首次冻结审查

STATUS: INCOMPLETE

TARGET:
- fork `a9cc30c395af9ffd51476a1841d80bca66568993`；a2a `f81c0079bb785ad8c9b4fc86597f0b5ac444a92f`。
- fresh context，模型配置 `gpt-6.1-sol / xhigh`，供应商实际 tier 未核实。范围为 T-036 四项及输入、作用域逻辑。

EVIDENCE:
- 原验收和 oracle 相对任务基线未改；最终组合结果 17/17、failures=0、errors=0、exit=0，真实 CLI/Git/SQLite/detached worktree/独立 oracle。
- 实际恢复副本 diff 与 complete.diff 精确一致，仅入口路径核对两行；业务断言、预期、九个场景、活跃 PID、CLI 路径、state/task、-9 退出检查保留。批准观察记录与主控文件一致。
- 最终绿态和两个 mutant 共 22 次 SIGKILL，全部对应夹具 CLI 的 PID/argv、身份和完成记录；退出 -9、alive_after=false。原拒绝注入的结果保留。
- 三行新增保护与 HTTP GET 的实际直接调用边界已核对。审查者在冻结 fork 最小重跑聚焦检查 1/1 PASS，真实 Git/SQLite 现场在外置盘 `a2a-history-contract-T5SguL`；此为 thread 替身的作用域逻辑证据。

FINDINGS:
- [P2] `evidence/2026-10-07-synara-batch1/controller-poll.log:317`：本次过宽的“所有已跟踪文件不变”声明包含了持续主控日志。审查初末 diff 从 82 新增行变为 85 新增行，故本次不能给 PASS。fork、T-036、ticket、acceptance 未变。最小处理是在新委派明确排除持续主控日志，或停止日志后重新冻结。
- 已完成的行为核对未见 T-036 范围内可达产品违约。

COUNTEREXAMPLE:
- 空身份红态保存旧实现错误：空 thread 返回本地 task，空 attempt 推进 verify/integrate 到 accepted；当前保护检查拒绝且状态不变。
- 最终 fence mutant 只删除 fence 校验，在错 fence 被接受的 `0 != 1` 业务断言失败；另有 busy 时限失败，未用于证明 fence。
- 最终 readback mutant 只有两处归档变异，在 CAS 前、外部 X、删除引用场景产生 BUSINESS_RED。实际运行与保留源码一致，且用同一副本组合入口。

LIMITATIONS:
- 本次因委派冻结条件失效为 INCOMPLETE，行为核对不构成最终验收授权。
- 未重跑 17 项或 33 分钟全仓；全仓 7/7 只绑定 `26cb210a9`。最终类型/lint/聚焦和17项通过，fmt 因既有 .grok 失败。
- 未验证实际 HTTP 请求、真实 provider 生命周期、模型闭环、run/M1 切换。

RULE:
- 审查初末比对声明冻结清单，任一声明冻结文件改变则 INCOMPLETE；持续主控日志须明确处理。本记录原样保留，后续限定复核不覆盖它。
