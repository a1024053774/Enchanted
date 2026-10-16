# T-076 / T-082 D3 断言对应表

当前状态：按主控 #39，以下 D3 断言替换已直接进入本 worktree，随检查点 `0dd00d09` 冻结；报告协议输入随后更新于 `7f2bd406`。旧 `t076-assertion-changes.patch` 和 OUTSIDE-05 是失败探索的历史材料，不是当前执行方式，也不代表那批运行通过。

2026-10-16 返工：独立审查 01 指出 default tier 负例不是 D3 只读断言，原来的观测点替换不成立。已按主控 #54 恢复原断言 id，负例改从当前 D3 候选仅移除对应角色的 default override。OUTSIDE-11 已确认两个 default 负例在原断言失败，正例通过；只读变异已实际生效，但门禁在 verify 阶段提前拒收，原 runner 错等后续断言。本次改为严格要求 `TRACER-REVIEW-START`、原始 `review_launch_boundary` 和实际 read-only argv 三者一致，待 OUTSIDE-12 重跑。源码审计及 a7f4cc30 锚点不变。

| 父修订断言/夹具 | D3 替换依据 | 候选中的替换 | 结果/证据 |
| --- | --- | --- | --- |
| `test_quality_tracer_e2e.py` 的 `TRACER-READONLY-ARGV`：`details['sandbox'] == 'read-only'`，实际 argv 也须 read-only | D3 要求一次性候选副本内 workspace-write、断网、排除 tmp | `TRACER-REVIEW-COPY-ARGV` 检查新 sandbox、network/proxy/tmp 参数；保留独立 session/thread/home、无 Git hook 环境条件；新增 `TRACER-REVIEW-CANDIDATE-COPY` 检查无 `.git`、独立路径及实际 `-C` | OUTSIDE-07 的三性质及 OUTSIDE-09 的三性质/严格 JSON PASS；T-082 的 `T082-REVIEW-ARGV`、`T082-COPY-CREATED` 亦 PASS |
| `run_t076_quality_green.py` 的 `reviewer-writable` 变异：把旧 read-only 分支改成 workspace-write，期望 `TRACER-READONLY-ARGV` 失败 | D3 反转正确的 reviewer sandbox 边界；新门禁会在启动处拒收 | 变为 `reviewer-readonly`：只在临时源码把实际 reviewer sandbox 改回 read-only；要求 `TRACER-REVIEW-START` 失败，并核对原始错误是 `review_launch_boundary`、实际 argv 是 read-only | 质量 runner 仍被原审计拦下，未执行此分支，不标 PASS；按 OUTSIDE-11 同一 start_review 入口的原始读回同步预期，未改审计 |
| `run_t076_launch_policy.py` 的 `TRACER-REVIEWER-DEFAULT-ARGV` default tier 负例 | 该要求没有被 D3 取代，必须保留观测点；旧快照缺少其他新边界不能用作隔离负例 | worker/reviewer 两个负例分别从当前候选只移除该角色的显式 default override，其余 D3 边界和身份均有效；仍要求 `TRACER-WORKER-DEFAULT-ARGV` / `TRACER-REVIEWER-DEFAULT-ARGV` 失败。独立 read-only 变异另在启动拒收处失败，不改变 default tier 观测点 | OUTSIDE-11 的两个 default 负例及 default-tier-green 均通过对应检查；reviewer 负例先通过四项 D3 断言，再在原 default tier id 失败。只读预期修正后的整串待 OUTSIDE-12 |
| `test_quality_tracer_e2e.py` 的受控 review_submit 输入只含旧字段 | T-082 请求/解析契约增加 review_requirements 和独立报告节 | 受控输入增加精确 review_requirements 与含“完成条件与变异检查”键的 report；说明这是受控输入，不是模型判断证明 | OUTSIDE-09 report-roundtrip 与真实 round-2 分别验证协议全路径和真实报告 |

审计逻辑和 `a7f4cc3033c16d5888de50d8352da516c941f8e9` 锚点保持原样。OUTSIDE-06 实际拒收来自原 acceptance 文件对该锚点的非空 diff，不能直接归因为上表 tracer 断言变化，也不是当前源码 dirty diff 非空就拒收。主控 #40 指定以冻结候选的三项性质 tracer 作为本票 T-076 回归，锚点整体迁移交上游待决。

旧断言未在 OUTSIDE-05 得到有效父修订业务红态：临时 Git 副本首先遇到审计/夹具错误，记录为 INCOMPLETE；不把这些错误称为断言检出了 D3 行为。当前绿态、历史失败和剩余证据缺口均见 [RESULTS.md](RESULTS.md)。
