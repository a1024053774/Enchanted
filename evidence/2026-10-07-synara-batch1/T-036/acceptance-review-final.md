# 唯一一次针对性独立复核

STATUS: PASS

TARGET:
- fork `26cb210a99fc74a43ef341278c6ef4e19ab0565e`；上一候选 `5cae1072db94ccd1af20ef161481163484aecfe5`。
- a2a 冻结证据 `977867bf59b8a2426bcbbd3ee0e646775b43d699`。
- 审查模型配置 `gpt-6.1-sol / xhigh`；实际供应商 service tier 未验证。PASS 只限 T-036 四项验收及上次 P1 的历史 reclaim 作用域逻辑。

EVIDENCE:
- 历史 reclaim 选择所指定历史记录并核对 task；只在它仍拥有 task 时改变业务状态。仍核对 thread/worktree、拒绝 working，并读回停止与归档。
- `history-contract-idle-red.log` 明确保存修复前合法回收被 `stale_attempt` 拒绝。`core.test.ts` 覆盖首次回收、当前绑定不变、精确停止/归档对象、重放、跨 task 与 working 拒绝。审查者独立最小复验 1/1 PASS：[原始命令及输出](review-final-command.json)。
- 主控 `controller-decision-01.md` 明确批准入口身份核对。逐行比较实际副本与原文件，完整 diff 完全一致，只有副本 202–203 行新增 `identity_entry` 并替换路径条件。PID 活跃、CLI 路径、state/task、全部业务断言及九个场景保留；原 acceptance 和 oracle 没有修改。
- `native-suite.py` 只组合原交付 8 项与同一恢复副本 9 项。绿态和两个 mutant 的 trace 含相同的 17 个场景与来源；组合绿态 17/17、exit 0，恢复单独 9/9。
- 组合绿态及两个 mutant 各 7 次 SIGKILL，逐一匹配夹具 `.launch.json` 的 PID/argv、完成记录和 ps 身份。CLI 路径、state、task 匹配，退出均为 -9；未发现向非夹具进程发信号的证据。
- 两份实际运行 mutant 与保留源码一致，对新候选只含指定变异；baseline core/CLI 与 `7cb0ac0` 一致。
- 审查结束两仓 HEAD 未变，fork 已跟踪文件干净；T-036、规格、原验收与冻结提交相同。地图为 0 problems、0 stale。

FINDINGS:
- 限定复核范围无未关闭发现。上次历史 reclaim P1 有修复前红态、候选绿态与独立预期支持，按作用域逻辑关闭。

COUNTEREXAMPLE:
- fence：17 项，2 个业务断言失败、0 error；错误接受 fence 触发 `0 != 1`，继而触发状态不变断言。
- readback：17 项，3 个 BUSINESS_RED、0 error；CAS 前恢复未推进引用却宣布完成，外部 X 与删除引用错误变成 accepted。
- baseline：17 项、18 个失败、0 error；缺失 `--state … create` 功能而 exit 2，只证明缺功能红态，不作为恢复业务反例。

LIMITATIONS:
- 历史回收使用真实 Git/SQLite、thread 边界替身，只证明作用域逻辑，不证明真实原生会话、provider 或认证。
- 未重复全套 17 项或全仓检查，未采用还在写入的未跟踪 workspace 日志。
- 主控批准是本次明确提供的未跟踪补充材料，不在 worker 的冻结提交。
- 不覆盖真实模型闭环、run 编排、M1 切换或全仓通过。

RULE:
- 保留历史回收作用域检查及同版本 fence/readback 业务反例。缺依赖、setup 与夹具失败继续与业务红态分开记录。
