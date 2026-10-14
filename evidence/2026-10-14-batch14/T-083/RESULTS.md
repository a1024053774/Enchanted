# T-083 本地交付证据（2026-10-14）

本地验证：PASS。交付流程：INCOMPLETE，等待执行主控运行提交脚本、独立审查并经门禁交付；本会话未提交、未 submit、未集成。

## 变更与依据

只修改 `acceptance/test_herdr_traceability_e2e.py:117` 的两行固定期望：加入 `--no-daemon`，把 `service_tier="fast"` 改为 `service_tier="default"`。完整 argv 相等断言和所有尾注断言保留。

独立依据是 T-083（`ready_rev: 1`）引用的用户原话：“以后只用 gpt6.1sol xhigh,不用 astra 了，那个消耗额度太快了，也不用 fast。”及速度覆盖决定 B（`20261013T142903Z-ideation-answer-001`，每会话显式 default）；`--no-daemon` 依据是任务指定的 `scripts/launch-worker` 固定启动参数。期望直接写在测试里，不读取实现输出生成答案。

起点与候选基线均为 `10ada0328ad6f522de4612724b5802bc2e8a0efd`（`exec/t083`）。运行时 main 已前进至 `cfbd8d0cb3d16edbdf38595baf33a6dbb5bdb9c4`；两版的受影响测试和启动器完全相同，比较命令为 `git diff 10ada0328ad6f522de4612724b5802bc2e8a0efd cfbd8d0cb3d16edbdf38595baf33a6dbb5bdb9c4 -- acceptance/test_herdr_traceability_e2e.py scripts/launch-worker`，空输出见 `baseline-main-equivalence.diff`。未切换或写入共享 main。

## 红态、绿态与反例

| 运行 | 退出码 | 测试结果 | 业务信号 |
| --- | --- | --- | --- |
| `red-01` | 1 | 7 项，3 failures，0 errors | 修改前，旧 argv 期望同时拒绝 default 和 --no-daemon |
| `green-01` | 0 | 7 项全过 | 同一整套测试，仅证据输出目录不同 |
| `mutant-fast-01` | 1 | 7 项，3 failures，0 errors | 副本默认 tier 改为 fast，固定 argv 断言拒绝 |
| `mutant-no-daemon-01` | 1 | 7 项，3 failures，0 errors | 副本去掉 --no-daemon，固定 argv 断言拒绝 |

三个失败用例均为 `test_amend_rebase_merge_and_native_replacement`、`test_commit_no_verify_and_plain_counterexample`、`test_duplicate_trailers_keep_body_and_project_trailer`，都在 `Contract.assert_trailers` 的 argv 相等断言失败。四个其余用例在红态和两个反例中均通过。绿态继续覆盖 amend、rebase、merge、--no-verify、原生会话替换、重复尾注、原钩子失败和打分反例。

每个运行目录保存 `command.json`（完整 argv、工作目录、代码版本、时间和身份）、原始 `stdout.txt` / `stderr.txt`、`exit-code.txt`、测试的 `commands.jsonl`、`summary.json` 与七份 Git 夹具归档。测试夹具保留在各自 `/tmp/t073-contract-*`，完整路径见 `artifacts/*/location.txt`；未在顶层登记 gitlink。两份变异源码与各自唯一变更见 `mutants-01/` 下的 `mutation.diff`；生产 `scripts/` 未改。

原始运行命令（在仓库根目录执行）：

```sh
python3 -B evidence/2026-10-14-batch14/T-083/run-contract.py red-01
python3 -B evidence/2026-10-14-batch14/T-083/run-contract.py green-01
python3 -B evidence/2026-10-14-batch14/T-083/prepare-mutants.py mutants-01
python3 -B evidence/2026-10-14-batch14/T-083/run-contract.py mutant-fast-01 --scripts-root evidence/2026-10-14-batch14/T-083/mutants-01/fast/scripts
python3 -B evidence/2026-10-14-batch14/T-083/run-contract.py mutant-no-daemon-01 --scripts-root evidence/2026-10-14-batch14/T-083/mutants-01/without-no-daemon/scripts
```

重放须换新的目录标签，脚本拒绝覆盖旧运行。红态必须使用起点版本的测试；候选重放会得到绿态。各次底层测试均为 `python3 -B acceptance/test_herdr_traceability_e2e.py --artifacts <新目录>`；反例另加 `--scripts-root <副本/scripts>`，精确 Python 可执行路径见 `command.json`。

## 边界与交接

全部检查在沙箱内完成。Herdr 使用测试已有的显式 fake，实际启动器、Git 提交及钩子在隔离 Git 夹具内运行；Codex 仅执行 `--version`，未调用真实模型，也未操作用户 Herdr server。环境为 Python 3.9.6、Git 2.52.0、Codex CLI 0.162.1；worker 的完整启动记录、角色卡及规格版本见 `context.json`。没有供应商实际服务档位的证明或相应主张。

`project-map-status.txt` 保存收尾检查；`checks.json` 保存路径、编码与差异检查。测试与辅助脚本使用 UTF-8、无 BOM，测试保留 LF；未修改地图、ticket、角色卡和术语表。

按当前指令不开子代理。`behavioral-acceptance-review` 要求新只读上下文，此处不把作者验证称为独立审查；主控须对冻结候选另开 reviewer。需要审查的 claim 是“固定 argv 断言接受当前普通速度启动并拒绝 fast 回退或缺少 --no-daemon”，已有两个业务反例可供复核。

提交脚本：`sh evidence/2026-10-14-batch14/T-083/commit-worker.sh`。脚本核对分支、起点及暂存路径，沿用本 worker 的受管身份和现有 Git 钩子生成尾注，不手写 `A2A-*`。脚本未执行，因此无候选提交号；提交后由主控按原 task/attempt 完成显式 submit 与验收，不能复用旧通过结论。

范围外发现见 `out-of-scope-issue.md`；`report-issue.sh` 供主控把报告写入共享收件箱。该共享路径不在本票写入范围，本会话未调用。
