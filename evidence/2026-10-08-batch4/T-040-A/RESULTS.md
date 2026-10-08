# T-040 A 交付记录（2026-10-08）

**INCOMPLETE：实现与指定复验已完成，等待一次 fresh-context 只读独立审查。T-040 整体保持 open。** 本记录只覆盖 A 部分的旧运行路径删除、验收迁移和 README；不宣布工作台启动器、真实模型或首次日常派发完成。未 push，未修改 fork、用户 Codex 配置、Herdr 或共享构建输出。

## 删除与验收迁移

动手前的 [删除清单](删除清单.md)、[完整文件列表](deletion-files.json) 已保存。实际删除 2,966 个受控文件：`coop.py`、`muster/`、只服务旧方向的 `scripts/build`、两个 Muster live 入口、`probes/t025-gpui/`。根 `Cargo.toml` / `Cargo.lock` 在 session 开始时已不存在，未伪称本次删除。

完整退役目录在 [源码归档](retired-source.tar.gz)，归档没有跟随符号链接。外置盘 Zig 缓存仍在；旧 `.runtime/`、`.upstream/` 历史夹具、主控批次日志及 B 部分工作均保留。当前受控运行文件扫描未发现旧入口引用，见 [扫描](runtime-reference-scan.json)。历史记录中的引用按简报保留。

交付默认入口改为 `acceptance/entry/a2a_gates.py`；恢复只采用 T-036 批准的入口身份两行 diff；编排提升 T-037 的原生 18 项及线程服务替身。全部业务方法、输入、oracle、断言和场景数保持批准版本，见 [完整 diff](acceptance-migration.diff)、[提升差异](native-suite-promotion.diff)、[逐项说明](验收迁移说明.md) 和 [静态核对](assertion-preservation.json)。

默认入口由无 `COOP_SCRIPT` 覆盖的 fresh Python 进程核对，见 [记录](default-entry-check.json)。编排 main 复制转接器时现在一并保存 TS 与线程替身；复制后的 Python → TS → 原生 CLI 和含空格目录的外部边界路径取得实际结果，见 [转接检查](relocated-boundary-check.json)。没有将转接器快照冒称为冻结产品源码。

## 新运行结果

所有运行的 fork 开始和结束提交均为 `d3b5bcc61cc212572f38e01139e1b9af2196b820`，分支 `a2a`。共享 checkout 中 B 部分的桌面启动文件有独立修改，相关门禁源码无 diff；实际源码保存于 `fork-gate-sources/`。a2a 起点 `1fa81e32dad035a08bdc4116a7327cfbbe6b5cd2`。每轮 `command.json` 保存精确 argv、环境、开始/结束版本、输出、退出码和原现场路径；`trace.json` 保存 CLI、Git、SQLite 回读和注入身份。

| 运行 | 结果 | 证据 |
| --- | --- | --- |
| 删除前交付 | PASS，8/8 | `baseline-delivery/command.json`、`trace.json` |
| 删除前恢复 | PASS，9/9 | `baseline-recovery/command.json`、`trace.json` |
| 删除前编排 | PASS，18/18 | `baseline-run/command.json`、`trace.json` |
| 删除后交付 | PASS，8/8 | `after-delivery/command.json`、`trace.json` |
| 删除后恢复首轮 | NO_GO，8 项通过、1 项失败；不能作为通过结论 | `after-recovery/command.json`、`trace.json`、`process-load.txt` |
| 删除后恢复同代码重跑 | PASS，9/9 | `after-recovery-02/command.json`、`trace.json` |
| 删除后编排 | PASS，18/18 | `after-run/command.json`、`trace.json` |
| 将入口指回已删除文件 | PASS（预期反例被拒绝）：exit 1，明确 `CLI entry point does not exist`；setUpClass 即拒绝，0 个业务场景启动 | `deleted-entry-negative/command.json`、`trace.json` |

恢复首轮的失败是两个忙调用仍在既定 2 秒时限后存活。夹具核对活跃 Popen PID、原生 CLI 路径、state/task 后，分别向本次创建的两个并发 CLI 注入 SIGKILL；原验收执行者仍完成，无第二 oracle。没有放宽时限或修改实现。相同源文件随后 9/9；超时根因尚未确定，不能由一次重跑宣称环境原因、稳定性或性能改善。

上述“不存在旧入口”反例只证明验收不会继续走已经删除的路径，不冒充产品逻辑 mutant。交付和编排仍使用真实错误分页候选、独立输入、Git 引用/reflog 和 oracle 拒绝场景。编排的 provider/thread 边界为替身，不证明真实模型、实际 tier 或长期收益；T-039 的真实闭环证据没有被本次新候选借用。

复现命令从 a2a 根目录执行，label 必须全新：

```sh
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_BEFORE_DELIVERY baseline delivery
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_BEFORE_RECOVERY baseline recovery
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_BEFORE_RUN baseline run
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_AFTER_DELIVERY candidate delivery
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_AFTER_RECOVERY candidate recovery
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_AFTER_RUN candidate run
python3 -B evidence/2026-10-08-batch4/T-040-A/run-check.py NEW_MISSING_ENTRY deleted-entry delivery
```

baseline 是删除前使用的原生验收版本：交付 helper 不含业务改动，恢复为 T-036 身份副本，编排为 T-037 原生副本。删除后重跑 baseline 只能复现该验收版本，不能重建删除前磁盘状态；删除前状态须使用起点 Git 版本与源码归档。

本次全部 8 轮现场在 [完整归档](retained-fixtures.tar.gz) 与 [原路径清单](retained-fixtures.json)。原 /tmp 目录仍保留，内嵌 Git/worktree 未登记 gitlink。模型及受管 attempt/fence 未从主控获得可核对身份，不编造；版本与实际 skill 字节见 [版本记录](versions.json) 和 `skill-sources/`。

## 检查与交接

README 已改为原生本地 CLI、服务端 HTTP/MCP 用法与新验收命令。`git diff --check` 通过，保存后的中文文档按 UTF-8、无 BOM、LF 回读；不改历史记录。

项目地图开始为 0 problems / 0 stale。删除后 `CONTEXT.md` 因其覆盖的 `coop.py` 被删除而 stale；简报明确由主控更新 AGENTS.md、CONTEXT.md 和地图，worker 不越过写入归属。该治理更新及 B 部分、首次日常派发仍是主控待办，不将全局地图状态写为 PASS。T-040 只在 Resolution 追加 A 部分交付，不关闭 ticket。
