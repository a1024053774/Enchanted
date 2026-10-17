# T-091 回归命令与材料问题

状态：**INCOMPLETE，以下尚未执行**。tracer-01 单格真实读回已通过，三格候选已实现、待实跑。当前统一执行入口和逐场预算见 [THREE-PANES-RUN.md](THREE-PANES-RUN.md)；下面保留 core wrapper 所调用的完整 suite／method 参数，不能重复使用同一输出标签。

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

## 材料问题的当前处置

1. 主控 #11／本对话 #40 已确认旧 bridge 断言过时且不受 T-080 保护，允许在保存起点结果后修正。baseline-bridge-assertion-01 记录起点原模块／原断言单独执行的失败，不冒称完整 GUI 起点运行。新断言精确列出六方法及 paneKeys；真实 window case 尚待主控执行。
2. 主控已恢复原始 `p1-materials-09/continue-esc/electron/snapshots.ndjson`，原件未改。`node workbench/tests/test_t078_window_binding.mjs evidence/2026-10-16-batch16/T-091/t078-window-binding-01` rc 0、13 项 PASS；其范围为原 snapshot 支持的生产谓词及定向驱动逻辑，外部边界由测试提供，不是 GUI 实跑。
3. 不直接用 `run_daemon_acceptance.py --probe all --output-root <新根>`：它的旧 entry-red 子运行器仍按 `evidence/2026-10-10-batch12/T-075/run-acceptance.py` 的 BASE 写旧批次路径，新根收据查询因此不一致。用户禁止改该旧 evidence／acceptance 范围，本 worker 未改。上面的独立 suite／mutant 命令避免启动这个旧 entry-red 包装，但完整回归仍须按新批次规则核对原件。

旧 ElectronClient 的自动强杀已删除；未确认 ready／退出时，现有 window 与 T-078 入口同时暂缓后台停机和归档。client-cleanup-unit-01 在纯给定边界上通过，旧实现违反“unready 不操作”断言而失败。真实 GUI 生命周期仍须以新入口实跑证明。

复核还发现旧 test_electron_e2e 清除 A2A 环境后未设置现行后台要求的 bootstrap 凭据路径。本次仅为该测试补隔离 fixture 凭据，并在确认停机后删除，不改业务预期；不读取登录凭据。原 GUI 业务断言（除已获准修正的 bridge 精确列表）继续原样使用。

重启后接手又核对到 core runner 的四份固定源材料在当前稀疏 checkout 缺失，记录见 `core-materials-takeover-01.json`。主控需先按 THREE-PANES-RUN 的 `prepare_core_materials.py --restore` 恢复 HEAD 原件；worker 只读检查过，未在边界外写文件。所有 GUI case 逐场运行；驱动请求、读屏上界、输出阈值及实际数量记录见同一执行清单。当前仍没有新的真实回归通过结果。
