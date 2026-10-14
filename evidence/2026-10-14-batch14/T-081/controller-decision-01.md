# T-081 执行主控决策记录

## 开工（2026-10-14 UTC 19:1x）

T-080 已关闭（main 391d70b0），T-081 的 blocked_by 解除。依据 assign 20261014T055042Z-ideation-assign-001（用户原话见条目"## 授权"）。worktree /Users/luckye/Documents/Code/a2a-wt-t081（exec/t081，起点 391d70b0），npm ci 按 README、spawn-helper 755。worker s14-t081（wF:p3T，launch-517c7570…，gpt-6.1-sol xhigh、service_tier="default"、--no-daemon、workspace-write、on-request）。存活 a2a Codex 2/3（s13-t078m、s14-t081）。第 7 项真实 worker 能力检查（≤3 回合）逐次批准。

## 计划审阅（2026-10-14 UTC 19:3x）

同意 1–5、6b–6d、7 与正例设计。6a 完全缺尾注：T-081 写拒收，而 spec 第 8 节、T-072 Resolution、core.ts 与现有测试允许并记人工介入——验收条件冲突，转构思主控请用户定，未答复前不实施、不编造拒收码。6e 伪造 launch/model：core.ts 仅要求非空、未与启动记录比对，先最小复现，放过则停下上报不修。第 7 项准备材料逐次批准。

## full-01：6e 探针 NO_GO（2026-10-14 UTC 19:3x）

run_t081_bad_worker_suite.py --output full-01：rc=3，NO_GO。probe_launch：同一输入下，提交尾注 A2A-Launch 伪造为 00000000-0000-4000-8000-000000000081（实际 worker launch 1e3dc0fc…），原产品 cdf8fe9b 与当前 main 均 verify ok、集成 accepted。model 探针未运行（脚本按设计停）。核对 T-072 规则："带本 attempt 尾注的正常；没有尾注的记人工介入；带别的任务尾注的打回"——未规定 Launch/Model 须与启动记录一致；用户原话"每一次代码提交都应该能追溯到"。判为规格缺口（验收/设计层），连同 6a 转构思主控请用户定；T-081 不修产品。其余矩阵继续运行，6e 记为发现。
