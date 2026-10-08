STATUS: FAIL
TARGET: Synara 冻结候选 `fc9e36c75af3bbcf701551abbb911883b94217c2`（父版 `fa3fc3352805d00e41c454fa6f810807528de3a9`）
EVIDENCE:
- 合同要求一次真实 run 经完整入口 accepted，集成引用读回为 worker 提交。
- 候选仅修改 `apps/server/src/a2a/orchestration.ts` 并新增 `apps/server/src/a2a/service.test.ts`；冻结候选与源码绑定一致。
- `seam-red-02` 失败、`seam-green-02` 6/6 通过、`seam-final-parent-red`/counterfactual 失败，证明两类修复能拒绝父版已知坏实现。
- `orchestration-18` 18/18、`delivery-recovery-17` 17/17 通过，共 35 项。
- 真实 run 使用一次 Codex turn，模型为 `gpt-6.1-sol`、`xhigh`、`full-access`、`fastMode=true`；`a2a_submit`、独立 oracle、CAS 集成都成功。
- `real-01/run.json` exit=1，结果为 `run_external_unknown`，run outcome 为 `integrated_reclaim_failed`。事件显示已集成后，自动回收仍失败。
- 后续同 attempt 人工 reclaim 先失败、再成功完成 stopped+archived；独立读回明确 `original_run_remains_failed=true`，不能改判原自动 run 成功。
- 隔离 home 已删除；用户 Codex 配置、Synara 数据与 Herdr status 前后一致。
FINDINGS:
- [P1] `apps/server/src/a2a/orchestration.ts:29-39` — provider turn 已完成并 session 已关闭，但 shell projection 仍短暂为 running；自动 run 在集成后的回收读回被判为 `run_external_unknown`，未满足完整真实 run accepted。应增加绑定原 attempt 的有界 native-close/projection-settlement 读回，再确认 stop/archive 后完成 run。
COUNTEREXAMPLE:
- 父版 `fa3fc3352805d00e41c454fa6f810807528de3a9` 的 seam 反事实 exit=1；候选测试能拒绝该已知坏实现。
- 候选真实输入 `t039-pagination-r02` 在 submit、oracle、CAS 集成都成功后仍返回 `run_external_unknown`；后续人工 reclaim 通过，但原 run 保持失败。
LIMITATIONS:
- seam 修复使用受控 thread/provider boundary，证明门禁逻辑与 service 入口，未证明真实 provider 在 interrupted 且运行时退出的完全相同时序。
- native settings 显示 `serviceTier=priority`，而请求/config 记录 `fast`；没有独立 oracle 判定该映射是否合法。
- 全仓 fmt 已失败（既有 `.grok`）；全仓 test 未运行。
