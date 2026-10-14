# T-081 执行主控决策记录

## 开工（2026-10-14 UTC 19:1x）

T-080 已关闭（main 391d70b0），T-081 的 blocked_by 解除。依据 assign 20261014T055042Z-ideation-assign-001（用户原话见条目"## 授权"）。worktree /Users/luckye/Documents/Code/a2a-wt-t081（exec/t081，起点 391d70b0），npm ci 按 README、spawn-helper 755。worker s14-t081（wF:p3T，launch-517c7570…，gpt-6.1-sol xhigh、service_tier="default"、--no-daemon、workspace-write、on-request）。存活 a2a Codex 2/3（s13-t078m、s14-t081）。第 7 项真实 worker 能力检查（≤3 回合）逐次批准。

## 计划审阅（2026-10-14 UTC 19:3x）

同意 1–5、6b–6d、7 与正例设计。6a 完全缺尾注：T-081 写拒收，而 spec 第 8 节、T-072 Resolution、core.ts 与现有测试允许并记人工介入——验收条件冲突，转构思主控请用户定，未答复前不实施、不编造拒收码。6e 伪造 launch/model：core.ts 仅要求非空、未与启动记录比对，先最小复现，放过则停下上报不修。第 7 项准备材料逐次批准。

## full-01：6e 探针 NO_GO（2026-10-14 UTC 19:3x）

run_t081_bad_worker_suite.py --output full-01：rc=3，NO_GO。probe_launch：同一输入下，提交尾注 A2A-Launch 伪造为 00000000-0000-4000-8000-000000000081（实际 worker launch 1e3dc0fc…），原产品 cdf8fe9b 与当前 main 均 verify ok、集成 accepted。model 探针未运行（脚本按设计停）。核对 T-072 规则："带本 attempt 尾注的正常；没有尾注的记人工介入；带别的任务尾注的打回"——未规定 Launch/Model 须与启动记录一致；用户原话"每一次代码提交都应该能追溯到"。判为规格缺口（验收/设计层），连同 6a 转构思主控请用户定；T-081 不修产品。其余矩阵继续运行，6e 记为发现。

## 供应商内容过滤（2026-10-14 UTC 19:4x）

s14-t081 在规划"伪造尾注"探针时，回复被模型服务过滤（"This content can't be shown … cybersecurity requests"），worker 空闲。执行主控重发一次，如实说明这是本项目门禁在 /tmp 隔离夹具上的验收测试（追溯字段一致性），任务内容不变。若再被拦，停下报用户，不换说法规避。

## full-02 读回（2026-10-14 UTC 19:5x）

rc=2。11 个坏行为案候选拒收码均符合预期、对应变异体均为业务 contract_failure；3 个正例集成、误拒绝 0。6e 发现：Launch/Model/Effort/Tool 四个追溯字段与启动记录不一致的提交在原产品与当前 main 均被接受并集成（已转构思主控请用户定，选项 A 补核对 / B 记已知局限）。run.json 顶层 FileExistsError(17)（收尾），交 worker 修 runner 后跑 full-03。第 7 项材料交审。

## 第 7 项第一回合审批（2026-10-14 UTC 20:0x）

审阅 CAPABILITY-REVIEW.md 与所列材料：隔离 CODEX_HOME=/private/tmp/t081-capability-01/codex-home，仅复制 auth.json、仅信任夹具根、仅 git add/commit 两条 allow；CLI hooks（UserPromptSubmit/Stop/PermissionRequest→夹具产品 signal，timeout 10，含产品自带 --dangerously-bypass-hook-trust）与 Git hooksPath 仅经本会话环境；gpt-6.1-sol xhigh、service_tier="default"、-a never、workspace-write、无网络；两条尝试命令仅作用于 /tmp 夹具 repo 与本地裸仓库，不提交、不 submit；首回合上限 1。批准：home prepare、上述 hooks 本次启用、第一回合一次。批准引用：`T-081 controller-decision-01 capability-turn-1`。尚缺启动/等待/停止/收集的运行脚本，交 worker 准备后由执行主控运行；清理另批。

## full-04 与第 7 项第一回合（2026-10-14 UTC 20:3x）

full-04：受控部分 PASS（11 个坏行为拒收、变异体业务红、3 个正例集成、误拒绝 0，23 套回归全过；wide 修正以 main 对照）。第 7 项：执行主控运行 home prepare（PASS，内容与审批一致：auth.json 0600、仅信任夹具根、两条 allow），随后运行 run_t081_capability_turn.py：INCOMPLETE，rc=2，real_turns_completed=0——dispatch 调用以 exit 1、空 stdout/stderr 失败；窗格前台仅 spawn-helper，未见 Codex 领导进程；脚本正常 daemon_stop，进程已停，夹具 main 仍 G、裸仓库无 refs，home 保留。未消耗真实回合（全票上限 3 仍余 3）。交 worker 诊断，不重试本次批准。
