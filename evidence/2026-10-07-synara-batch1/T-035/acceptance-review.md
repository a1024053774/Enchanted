# T-035 独立只读验收审查（2026-10-07）

审查请求模型：gpt-6.1-sol / xhigh；实际供应商 service tier 未核对。fresh-context agent：`/root/t035_acceptance_review`。审查期间源码及已跟踪文件保持冻结；审查者没有改文件、分支、提交或外部状态。下文为审查者最终结论。

STATUS: PASS

TARGET: `/Users/luckye/Documents/Code/synara`，冻结提交 `7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73`；仅验收 T-035 五项。

EVIDENCE:

- 独立 package 持有门禁状态；CLI、HTTP、MCP 调用同一核心。已核对操作锁、身份校验、CAS 路径及上游改动清单。
- 准确冻结产物的新任务 `pagination-frozen` 完成真实 Codex 闭环。原生 rollout 记录错误 session 被拒绝，正确 `a2a_submit` 才进入 submitted。
- `verify-3.json` 在独立 detached worktree 运行冻结 oracle；审查者重新运行，12/12 PASS。集成引用、worker HEAD、验收候选均为 `fd0b69579c5c8f8f2d0f97c33f51a3783226aca1`。
- 审查者重跑 `check-frozen-live.py`：17/17 PASS；独立比较保存的加载产物与冻结源码重建产物，7,034,921 字节完全相同。
- 已目视核对五张 `frozen-*.png`：claimed → submitted → verified → accepted，回收后仍显示 accepted 与“worker 已回收”。原生读回 stopped、archived=true。
- 已核对 `runtime-cleanup-frozen.json`；隔离 home 和临时副本均不存在。完成时源码仍冻结，项目 status 无 problem 或 stale living doc。

FINDINGS:

- 当前 T-035 范围内无未解决验收发现。原运行产物缺少最终工具注册行的版本绑定缺口，已通过准确产物的新闭环补证；旧记录完整保留。

COUNTEREXAMPLE:

- starter 被冻结 oracle 拒绝：10 项业务断言失败，程序正常退出，排除了环境故障造成的假红态。
- 新运行 wrong-session 返回 `stale_session`，拒绝事件先于合法 submitted。
- `no-submit-frozen` 已 completed/idle，门禁仍 claimed；verify/integrate 返回 `not_submitted`/`not_verified`，集成引用不变。
- 原加载 bundle 与冻结候选不同，被拒绝作为当前候选的通过证据。

LIMITATIONS:

- **完整 M1：INCOMPLETE。** 本次不证明恢复、竞争、完整编排、多 agent 层级或切换通过；操作锁等未取得完整故障场景证据。
- 能力轴适用：编排状态、异步、身份范围、交互、文件、外部副作用、运行运维；检索/记忆 N/A，本切片没有该能力。
- 全仓 test 仍为 FAIL：`ProviderCommandReactor.test.ts:7200` 一个失败；单例复核 PASS，未证明根因或已修复。typecheck、lint PASS；全仓 fmt 因范围外 `.grok/settings.json` 失败。
- Worker 原生配置读回模型、xhigh、priority；供应商实际计费 tier、性能与成本未验证。审查请求配置为 gpt-6.1-sol/xhigh，实际供应商 tier 未核对。

RULE:

- 在真实闭环验收入口绑定冻结提交与实际加载产物；产物不一致时拒绝沿用旧通过结论，保留差异并对准确产物重新取得边界证据。
