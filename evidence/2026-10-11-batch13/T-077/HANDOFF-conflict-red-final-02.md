# T-077 conflict-red-final-02 交接

**INCOMPLETE：新入口已准备，七红/七绿仍待主控沙箱外运行。** 本次范围为主控 #127；用户重跑决定引用 answer `20261014T121326Z-ideation-answer-001`。产品冻结 `5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`，夹具冻结 `178d15f3ddb13f06a00eac19d7655225519f98e2`。

`outside-conflict-red-final-01/` 和 `conflict-red-final-01.console.txt` **被系统低内存回收、不计**；原因来自主控派发。原始文件未修改：完整收据只到 red-03，red-04 只有未完成现场，没有顶层 run.json。此次提交保留这些文件，既不续跑也不借用前三项计入 -02。

新阶段仍调用 `run-conflict-red-final-01.py`，增加输出目录参数 `--output`；参数同时选择同名 `-preparation` 目录，避免改动入口后误用冻结旧字节的归档。执行函数、七案名单、顺序、四个变体、逐目标前置、断言与红绿判定均保持不变。原阶段及准备目录保留。

主控在沙箱外执行并保存独立 console（新运行目录和 console 均须不存在）：

```sh
(set -o noclobber; bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh conflict-red-final-02 > /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/conflict-red-final-02.console.txt 2>&1)
```

输出为 `evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02/`。同名目录已存在即拒绝，新增真实模型回合 0。所有结果必须绑定此次运行 HEAD；运行中不得变更 HEAD 或冻结输入。

准备命令（本次已执行；同名准备目录存在即拒绝，不能覆盖）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/run-conflict-red-final-01.py --prepare-only --output evidence/2026-10-11-batch13/T-077/outside-conflict-red-final-02
```

准备归档和 plan.json 保存于 `outside-conflict-red-final-02-preparation/`。局部检查仅确认语法、参数与入口路径、冻结输入及未变的执行函数/契约；不作为冲突业务红绿或独立复审结论。七红/七绿仍按 [原交接](HANDOFF-conflict-red-final-01.md) 的目标与前置逐项读回：八个子阶段全部完成，七红命中各自目标且前置齐全，候选七案通过，无 errors/skipped/cleanup_failures，顶层才可 PASS。

准备检查 **PASS**：四个变体语法通过；CLI 参数同时选中新 OUT/PREP，归档逐字节核对通过，七目标/前置与冻结夹具相同，run() 及其余执行函数与 `fba6ebb5` 相同，shell 语法通过，project-map 为 0 problems/0 stale。原始命令与输出见 `conflict-red-final-02-readiness-01/commands.jsonl` 和 `checks.json`。这里仅报告重跑准备，不上调冲突业务结论。

本 worker 未运行沙箱外阶段、未请求提权、未启动真实 Codex；整票与 F1 仍 INCOMPLETE，验收、针对性独立复审、集成和关票由主控处理。
