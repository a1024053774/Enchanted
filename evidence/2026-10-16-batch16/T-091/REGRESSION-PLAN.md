# T-091 回归命令与材料问题

状态：**INCOMPLETE，以下尚未执行**。当前先交单格 Tracer bullet，真实读回后再扩三格；这些命令留给执行主控核对、在对应冻结候选上运行，不构成已通过结果。

CLI 核心回归使用现有 daemon acceptance adapter：Python／Node／Git、隔离后台与测试运行器；没有 Electron、真 Claude／Codex 或供应商模型回合。recovery 和反例包含隔离夹具自建进程的受控故障／终止，不操作用户 Herdr 或其他应用。所有路径与标签须是全新目录，原始输出直接放外置盘。主控需同时核对原运行器的收尾／原件归档记录，不能把顶层 rc 当成唯一通过证明。

## 四套现有正例

```sh
python3 -B workbench/tests/run_daemon_acceptance.py --suite coop --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label coop-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite recovery --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label recovery-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite run --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label run-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite cas --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label cas-01
```

预期分别为 8／9／18／1 方法，0 failures、errors、skipped，且 source revision、runtime_layers、命令和原始结果可核对。run 的 5 个 default-production-daemon 与 13 个 isolated-orchestration 来源不能混称真实 agent／GUI 证据。

## 原有 fence／CAS／lock 反例

先在测试副本中制作三个单处变异，不改本仓库 workbench/src/gates 或验收文件：

```sh
python3 -B -c 'import sys; from pathlib import Path; sys.path.insert(0,"workbench/tests"); from prepare_daemon_mutants import prepare; print(prepare(Path("/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-mutants-01"), task="T-091"))'
python3 -B workbench/tests/run_daemon_acceptance.py --suite coop --test test_identity_gates_and_revocation_reject_old_verified_attempt --mutant fence --mutant-manifest /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-mutants-01/manifest.json --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label fence-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite cas --test test_external_write_between_read_and_cas_is_preserved --mutant cas --mutant-manifest /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-mutants-01/manifest.json --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label cas-mutant-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite recovery --test test_live_verify_excludes_verify_and_integrate --mutant lock --mutant-manifest /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-mutants-01/manifest.json --output-root /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-01 --label lock-01
```

反例必须在各自的业务断言失败，不能把启动、导入、权限、超时、夹具或 JSON 错误算作成功反例。沿用原 business_mutant 复核条件，逐项保留原始 trace 与变异 patch；本次尚未运行，不能宣称这些条件成立。

## 非阻塞材料问题，交主控处理

1. 旧 `test_electron_e2e.py:170` 要求 bridge 恰为 output／snapshot，与 T-078 已有六方法和 T-091 的只读 paneKeys 不符。未改这条验收断言；主控须确认受保护文件身份和正确契约，才能运行其 window 阶段并计入回归。
2. 旧 `test_t078_window_binding.mjs` 需要的 `p1-materials-09/continue-esc/electron/snapshots.ndjson` 在本稀疏 worktree 缺失。更新了新生产片段定位和定向调用，但未运行该旧测试；不能伪造或用模拟值替代这份指定真实输入。
3. 不直接用 `run_daemon_acceptance.py --probe all --output-root <新根>`：它的旧 entry-red 子运行器仍按 `evidence/2026-10-10-batch12/T-075/run-acceptance.py` 的 BASE 写旧批次路径，新根收据查询因此不一致。用户禁止改该旧 evidence／acceptance 范围，本 worker 未改。上面的独立 suite／mutant 命令避免启动这个旧 entry-red 包装，但完整回归仍须按新批次规则核对原件。

T-078 GUI 正反例还需审阅旧 ElectronClient 的故障收尾：它在失败路径会 kill_owned 进程组。当前 T-091 新实跑采用已确认的“ready 未确认就停等主控、不自动对 Electron 发信号”策略，因此不悄悄执行旧 GUI 包装器，也不把其未跑结果写成通过。单格 run_tracer 已直接覆盖六条 keyed IPC 和模拟输入介入；三格实现后还须补完整同窗／角色／输入隔离与旧 GUI 场景。
