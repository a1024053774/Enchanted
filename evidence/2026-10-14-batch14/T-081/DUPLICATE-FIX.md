# T-081 矛盾 Session 单案修正与差异复审（主控 #181、#183）

本次差异状态：**PASS，P2-01 RESOLVED**。主控已运行单案红绿，fresh-context 只读差异复审已完成；整票仍为 **INCOMPLETE**，6a/6e 待裁定，最终组合入口未完整重跑。产品不改；原同值案例、独立审查原文和旧结果均保留。实际能力回合仍 3/3；本次复审没有启动真实能力模型、daemon 或测试，没有 add/commit/submit，没有重跑其他案例/正例/回归。

## 预期与输入

独立审查 P2-01 已由主控接受：两个相同 Session 值不是错误身份的独立证明。新输入是两个互相矛盾的 `A2A-Session`：第一个是产品认领出的本 attempt session，第二个为不同的有效 UUID `00000000-0000-4000-8000-000000000181`；脚本检查两者确实不同。

拒收依据是 [spec 第 8 节](../../../.project-map/specs/native-cli-orchestration-2026-10-10.md) 与 [T-072 的提交追溯契约](../../../.project-map/tickets/T-072-traceability-scoring-retrospective-metrics.md)：尾注应能追溯到本 attempt/会话；与本会话矛盾的身份不能作为其合法交付。预期是**必须拒收矛盾身份**，不把当前实现的错误码当作规范答案。`REFUSALS.trailer_duplicate` 不预填代码；实际拒收码在候选运行后单列记录，并要求它与本候选 `trailer_check` 的失败及拒收事件一致。任意早期拒绝、解析崩溃或泛化 gate_failure 不能充当该案通过。

[旧同值观察](duplicate-fix-01/same-value-observation.json) 直接引用 full-04 原始输入与回复，`counted_as_pass=false`。旧 raw 的 PASS 字段不改写，当前 collector 排除这一历史行。[当前汇总](closeout-duplicate-final-01/run.json) 计入其余 10 案原件及本次矛盾 Session 替代案，共 11 案；[先前待运行汇总](closeout-duplicate-pending-01/run.json) 原样保留。这是分次证据，不是最终组合入口完整重跑。

## 变异与当前验证

[计划补丁](duplicate-fix-01/planned-session-cardinality.patch) 只取消 Session 的恰好一个值数量限制；字段集合、Session 存在/非空、其他字段的完整性与唯一性、现有 attempt/session/role 值比较均保留。不再用同时取消全部字段形状检查的 trailer_shape 变异来证明该案；trailer_partial 仍使用原变异，其断言不变。

- 输入构造的独立检查先在旧实现出现 [input-red](duplicate-fix-01/input-red/run.json)：真实 Git 解析得到两个同值，`DUPLICATE-INPUT-NOT-CONTRADICTORY`。修正后同一检查 [input-green](duplicate-fix-01/input-green/run.json) 得到一真一假两个值。此检查的 Git 写操作为 spy，只证明输入构造，不冒充真实门禁红态。
- 计划补丁定位唯一；[变异隔离检查](duplicate-fix-01/check-mutation.mjs) 覆盖正常单值、矛盾值、同值观察、缺/空/空白 Session、重复 task、缺 Effort。只有多个 Session 的数量限制取消，其他检查仍失败。它不是门禁端到端证据。
- [duplicate-conflict-01](duplicate-conflict-01/run.json) 为主控实际运行，rc=0。只取消 Session 数量检查的变异体允许该候选进入 reviewing，随后在 `BW-REJECT-trailer_duplicate` 失败；候选实际拒收 `invalid_trailers`，对应 trailer_check 与拒收事件一致，分支及 reflog 未变，继续集成返回 `not_verified`。这两项由差异复审直接核对原始回执、提交对象与归档数据库，不以汇总标签替代。

## 单案运行命令（已完成，原目录勿重跑）

```sh
python3 -B workbench/tests/run_t081_duplicate_case.py --output evidence/2026-10-14-batch14/T-081/duplicate-conflict-01
```

脚本核对 HEAD=`3ee28bc3ad77595e23b77dbef34af20c5370dea9`、产品与起点无 diff，冻结当前源快照和测试 diff；使用已装 node_modules，不构建、不安装。新输出已存在即停止，不覆盖历史运行。

1. 只跑 `trailer_duplicate` 的 `trailer_session_cardinality` 变异体。要求实际到达此候选尾注检查、解析到一真一假、被变异体放行到 reviewing，且目标业务断言 `BW-REJECT-trailer_duplicate` 失败；另一种拒绝或 harness_error 不算红。
2. 再用相同案例在候选运行，要求真实拒收、trailer_check 与拒收事件对应、共享分支/reflog 不动、不能继续集成。**实际错误码**写入 run.json 与结果表，不预造该码。
3. 两边保存原始命令输出、输入/提交正文、事件、数据库/Git 读回、归档及唯一补丁；全部单文件不超 5 MB。若当前产品放过，状态 NO_GO，停下报告，不修产品。

只重跑这一案的红/绿两个版本，其他 10 案与 3 正例、原回归未重跑。full runner 仅接上新输入/变异/规范预期，其他断言保持；新的最终组合入口仍未完整重跑。

## 差异复审与提交

主控 #183 授权的一次 fresh-context explorer 差异复审已完成：[independent-review-02.md](independent-review-02.md) 为 **PASS / P2-01 RESOLVED**，仅限此问题、相关测试改动与本次单案原始证据。旧 independent-review-01.md 原样保留。[request](independent-review-02.request.json) 与 [completed](independent-review-02.completed.json) 记录 `fork_turns=none`、`gpt-6.1-sol/xhigh` 请求、reviewed_base=3ee28bc3…；供应商实际 tier 未观察。报告逐字节核对六份受审测试与真实执行快照一致，独立确认矛盾身份的规范依据、唯一变异、目标业务红态及候选拒收；没有扩大为整票或其他案例复审。

提交脚本供主控以同一身份运行，worker 未执行 add/commit：

```sh
python3 -B workbench/tests/commit_t081_duplicate_fix.py
```

该脚本要求 duplicate-conflict-01 红绿都有效、差异复审明确解决 P2-01，并逐字节核对六份测试仍等于执行快照，才以原 s14-t081 身份提交本次 7 个测试/脚本文件、两份说明、静态/单案证据、当前及历史汇总与差异复审记录。身份环境沿用 [COMMIT-READY.md](COMMIT-READY.md) 的 11 项，由项目 hook 自动追加尾注，不手写或绕过。原始证据只免空白检查并逐项列在收据；兼容核对后的已有暂存内容，不 reset、不触碰其他任务、不 submit/集成/push。实际提交日志为 /private/tmp/t081-duplicate-commit-01，worker 未创建。`--check-only --log-dir <新目录>` 只核对前置条件，不 add 或 commit。

T-081 REVIEW-02 DONE
