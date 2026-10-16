# T-076 / T-082 D3 断言对应表

当前状态：按主控 #39，以下 D3 断言替换已直接进入本 worktree，随检查点 `0dd00d09` 冻结；报告协议输入随后更新于 `7f2bd406`。旧 `t076-assertion-changes.patch` 和 OUTSIDE-05 是失败探索的历史材料，不是当前执行方式，也不代表那批运行通过。

| 父修订断言/夹具 | D3 替换依据 | 候选中的替换 | 结果/证据 |
| --- | --- | --- | --- |
| `test_quality_tracer_e2e.py` 的 `TRACER-READONLY-ARGV`：`details['sandbox'] == 'read-only'`，实际 argv 也须 read-only | D3 要求一次性候选副本内 workspace-write、断网、排除 tmp | `TRACER-REVIEW-COPY-ARGV` 检查新 sandbox、network/proxy/tmp 参数；保留独立 session/thread/home、无 Git hook 环境条件；新增 `TRACER-REVIEW-CANDIDATE-COPY` 检查无 `.git`、独立路径及实际 `-C` | OUTSIDE-07 的三性质及 OUTSIDE-09 的三性质/严格 JSON PASS；T-082 的 `T082-REVIEW-ARGV`、`T082-COPY-CREATED` 亦 PASS |
| `run_t076_quality_green.py` 的 `reviewer-writable` 变异：把旧 read-only 分支改成 workspace-write，期望 `TRACER-READONLY-ARGV` 失败 | D3 反转正确的 reviewer sandbox 边界 | 变为 `reviewer-readonly`：把新 workspace-write 分支改回 read-only，期望 `TRACER-REVIEW-COPY-ARGV` 失败 | 旧 runner 在源码审计阶段拒收，未执行该变异，不写为 PASS；T-082 当前 readonly 启动拒收 PASS，逐项修前红态缺口见 RESULTS 第 2 条 |
| `run_t076_launch_policy.py` 的 reviewer baseline id `TRACER-REVIEWER-DEFAULT-ARGV` 与旧 writable 变异 | 父快照不含 D3 副本策略；default tier 要求仍保留 | reviewer baseline 的预期失败 id 改为 `TRACER-REVIEW-COPY-ARGV`；变异改为 read-only。worker/default tier/priority 断言未放宽 | runner 在更早的 worker baseline `card_save` 夹具阶段失败，main 同样失败（OUTSIDE-08），没有宣称这些步骤执行通过 |
| `test_quality_tracer_e2e.py` 的受控 review_submit 输入只含旧字段 | T-082 请求/解析契约增加 review_requirements 和独立报告节 | 受控输入增加精确 review_requirements 与含“完成条件与变异检查”键的 report；说明这是受控输入，不是模型判断证明 | OUTSIDE-09 report-roundtrip 与真实 round-2 分别验证协议全路径和真实报告 |

审计逻辑和 `a7f4cc3033c16d5888de50d8352da516c941f8e9` 锚点保持原样。OUTSIDE-06 实际拒收来自原 acceptance 文件对该锚点的非空 diff，不能直接归因为上表 tracer 断言变化，也不是当前源码 dirty diff 非空就拒收。主控 #40 指定以冻结候选的三项性质 tracer 作为本票 T-076 回归，锚点整体迁移交上游待决。

旧断言未在 OUTSIDE-05 得到有效父修订业务红态：临时 Git 副本首先遇到审计/夹具错误，记录为 INCOMPLETE；不把这些错误称为断言检出了 D3 行为。当前绿态、历史失败和剩余证据缺口均见 [RESULTS.md](RESULTS.md)。
