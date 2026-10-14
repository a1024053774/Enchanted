# T-077 final-04 交接

**READY：脚本与夹具修复已准备；全量业务结论仍为 INCOMPLETE，待主控沙箱外运行。**

## 本次修复与冻结范围

夹具修复提交：`30ebf967573be231daa142f1b09f98d18e508295`。其中产品、hook、README 与 acceptance 均未改，产品仍冻结为 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`。两处夹具变化是 daemon adapter 的 overlap_reason 传递，以及回归 runner 完整执行与名单记录。原因、原始失败路径及局部修前/修后命令见 `DIAGNOSIS-rebase-final-03.md`。

18 项都在 final-03 的原始名单里；failfast 令其在第 11 项 ERROR 后停止。final-04 的 runner 不提前停止，实际方法名单必须与原始名单逐项相同，run 必须为 18/18，错误仍导致 INCOMPLETE。主控运行时可直接检查 `run/run.json` 的 tests_run、expected_tests、executed_methods、unexecuted_methods、failures、errors、skipped 和 failfast。

阶段 guard 分别锁定产品和夹具：src/hooks/README/acceptance 必须与产品冻结版本相同，tests 必须与夹具修复提交相同；产品到夹具提交的非证据变化只允许上述两个 fixture 文件。此后只允许本卡证据提交。准备时归档逐文件字节，阶段执行前后复核；运行期间 HEAD 不得改变。没有放宽任何业务断言。

## 由主控运行

在沙箱外执行，工作目录为本 worker worktree：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-final-04
```

固定新输出目录：`evidence/2026-10-11-batch13/T-077/outside-rebase-final-04/`。已存在则拒绝运行，不覆盖 final-01/02/03，也不自动重试。无需 auth、模型、真实 Codex、Electron 或正式工作台；新增真实模型回合 0。依赖外置盘未挂载则报错。需要沙箱外的部分仍是测试创建的 Unix socket、受控 PTY、进程身份检查和自建服务清理。

全量保持 **39 个子阶段**：driver-readiness；审查清理 4 条 preimage 红态与候选；3 条 joint 变体红态；7 条冲突红态；joint 候选；S3 全量 25；coop 8、recovery 9、run 18、CAS 1、cards 15；relay-conflict；两条 controlled-trailer 候选证明；identity、shutdown；T-076 最终入口 tracer/wide/review-faults/controls/provenance；relay core/cli/scope/global-mutant；native-final、dispatch-state、panes。三条 joint 路径仍包括同 C 的 R8 重验沿用有效审查、新 C 重审、冲突重交后质量打回再提交。

review preimage 仍为 `7b3463c4a55381d0fb97f782e69cc0029522f6da`，只在隔离副本重建旧产品；保留 final-03 严格符号链接规则。变体仅在 /tmp 修改，门禁/CLI/Git 为真实入口，外部模型由受控夹具提供。

## 结果读回

- 顶层：`outside-rebase-final-04/run.json`，应为 PASS、39 steps、real_codex_turns=0。
- run 套件：`outside-rebase-final-04/run/run.json`，应为 18/18、0 failures/errors/skipped、unexecuted_methods=[]、failfast=false；原始输出在同目录 unittest.txt。
- 各红态须命中规定业务断言，setup/import/收证据错误不算红态。所有原始输出与命令见各子目录、receipt 和 commands.jsonl。
- 任一文件超过 5 MB 停下交主控归档；不删原结果或继续推进。独立审查仍等待主控明确指令。

本次准备检查已通过，命令如下（当前归档为 `rebase-final-04-preparation-01/`；重放前须另存 runner 并指定新 PREP 目录，不能覆盖已有目录）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/run-rebase-final-04.py --prepare-only
python3 -B evidence/2026-10-11-batch13/T-077/check-rebase-final-04-preparation.py
```

runner 的 `--prepare-only` 创建计划和输入归档，第二条命令做语法、冻结文件、T-076 断言不变与项目地图检查。准备检查 PASS 仅表示可交运行，不表示 39 阶段通过。
