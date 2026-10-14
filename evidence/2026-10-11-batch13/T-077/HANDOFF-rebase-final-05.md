# T-077 final-05 交接

**READY：无后台预检和夹具修复完成；全量业务结果仍为 INCOMPLETE。**

夹具提交为 `be91b3c047195e23fff0e1d6fd68e82ab63bf72f`。新增产品差异 0，acceptance 业务语义不变；产品仍冻结在 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`。本轮只补 RelayConflict.managed_trailers，没有更改测试断言或 gate 行为。原 final-04 的 run 18、CAS 1、cards 15 均通过；relay 的 AttributeError 及之后未运行的阶段仍保持原结论。

## 预检读回

| 范围 | 结果与证据 |
| --- | --- |
| Python 继承、helper、关键字、字段 | 8 类 / 52 场景，完整 1,170 处显式调用绑定无缺口；`final05-preflight-complete/run.json`。初次缺口保留在 `final05-preflight-before/` |
| 新 helper 和动态转发 | 修前 3 项中 1 error，修后 3 项通过；`final05-helpers-before/`、`final05-helpers-after/`。只验证 Python 客户端构造，不冒充真实 Git/门禁 |
| 后续入口 | 9 个 Python CLI --help 与 11 份 TS 语法通过 |
| 无后台边界 | relay core/CLI/scope/global-mutant、native-final、panes 共 6 组通过；`final05-boundaries-before/`、`final05-boundaries-completion/` |
| dispatch-state | 语法通过；执行时 readThread 调真实 ps，沙箱 spawn EPERM，保留 INCOMPLETE，无重试；全量阶段由主控在沙箱外执行 |

预检覆盖受控尾注候选、identity、shutdown、T-076 tracer/wide/reviewer 故障/controls/provenance 的实际场景名单，并追踪 super、显式父类和 cleanup 回调。QualityDriver/CommandLog 构造器与调用参数也已核对。展开参数、动态记录和启动后时序的边界见 `DIAGNOSIS-rebase-final-04.md`，不把静态可解析称为业务通过。

## 沙箱外运行

工作目录为 `/Users/luckye/Documents/Code/a2a-wt-t077`：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh rebase-final-05
```

输出固定到全新 `evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/`；存在则拒绝运行。保留全部 **39 子阶段**，不从 relay 中途续跑：driver；审查清理四红一绿；joint 三红、冲突七红、joint 候选；S3 25；coop 8/recovery 9/run 18/CAS 1/cards 15；relay-conflict、controlled-trailer 两候选、identity、shutdown；T-076 tracer/wide/reviewer 故障/controls/provenance；relay core/CLI/scope/global-mutant；native-final、dispatch-state、panes。

三条 joint 组合路径仍为同 C 的 R8 重验复用有效审查、新 C 重新审查、冲突重交后质量打回再提交。run 不启用 failfast，必须实际执行全部 18 项且全部通过，保存实际与未执行名单。所有业务断言原样保留。

guard 分别核对产品版本与夹具版本；产品到夹具提交只允许本卡证据及已批准的三个 fixture 文件，之后只允许本卡证据提交。准备归档包含源码、测试、阶段脚本和预检输入，逐文件比对字节；运行期间 HEAD 不得改变。旧 review preimage 与严格 hook.py 符号链接重建规则不变。

真实模型回合 0，不读 auth、不创建新的真实 CODEX_HOME、不启动正式工作台。Unix socket、真实 ps 和测试自建进程的清理由主控的沙箱外阶段运行。变体仅放 /tmp。单文件超过 5 MB 则停下交主控归档；不自动重试或开始独立审查。

## 结果与准备命令

读回 `outside-rebase-final-05/run.json` 和各子阶段 run.json/results.json；顶层须 PASS、39 steps、real_codex_turns=0。任何 setup、方法缺口或收证据错误都不能算业务红态或通过。

本次准备命令如下，产物在 `rebase-final-05-preparation-01/`。重放必须另存阶段脚本并改为新 PREP/OUT，不覆盖已有结果：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/run-rebase-final-05.py --prepare-only
python3 -B evidence/2026-10-11-batch13/T-077/check-rebase-final-05-preparation.py
```

局部预检及 helper 的完整再生成命令见 `DIAGNOSIS-rebase-final-04.md`；逐条离线命令和 stdout/stderr 在两个 boundaries 目录的 commands.jsonl 与 command-output/。准备检查通过仅表示可交运行，全量仍待主控执行。
