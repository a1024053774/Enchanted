# T-151-1 / a1：Claude 信号测试迁移

状态：PASS（worker 本地迁移与红绿态）；执行主控复跑、独立审查及门禁验收尚未执行。起点 `32ffb4e6d`，分支 `exec/t151`，task `T-151-1`，attempt `a1`。最终交付提交由包含本报告的 Git 提交确定。

## 目标与范围

按 T-151 与任务卡迁移 `workbench/tests/test_t078_claude_signals.ts`，保留所有有效检查，不改产品代码、其他测试或历史索引。只新增本目录的证据与重放脚本，无测试专用辅助源码。

Ubiquitous language：登记派发记录、active submission、原生会话、`pane_idle` 沿用 ticket 与项目术语。此次是单个领域状态测试的夹具修复，不跨产品层，不新增 Tracer bullet 或 Deep modules。

## 修改前的逐条检查清单与独立来源

| 原检查 | 分类与现行依据 | 迁移后期望 |
| --- | --- | --- |
| `typeof panes.startController === "function"` | 有效。T-149 DISPOSITION 的 R12 行明确入口仍存在；没有删除 API 的决定。 | 原样保留。此项只证明入口存在，不证明终端启动。 |
| 登记派发后 `UserPromptSubmit` 使状态保持 `busy` | 有效。T-151 明确保留登记提交与 UserPromptSubmit/Stop 关联；T-071 D14 只认结构化信号。 | 保留 busy，并显式核对 prompt id 已绑定当前提交。 |
| 匹配 `Stop(stop_hook_active: false)` 后状态为 `idle` | 有效。T-151；T-078 Resolution 的 08e 记录 busy→idle。 | 原样保留。 |
| 匹配 Stop 后 `pane.active === null` | 有效。T-151 明确保留“有 active 的匹配 Stop 清空”。 | 原样保留。 |
| 首次匹配 Stop 后 `pane_idle` 总数为 1 | 有效。T-151 的一次完成语义。 | 保留数量，并核对事件的 submission 是原 active id。 |
| 重复 Stop 后 `pane_idle` 总数仍为 1 | 有效。T-151 的显式去重要求。 | 原样保留；变异必须在这类保留检查上失败。 |
| 外来 `session_id` 的 Stop 抛 `hook_native_session_mismatch` | 有效。T-151 明确保留异会话拒收；T-108 的 hook 身份边界。 | 原样保留。 |
| 夹具未声明角色、只给出不存在的 transcript 路径 | 过时夹具，不是应删除的断言。T-151 明确要求补 transcript/模型事实；T-076 要记录实际模型，T-130 区分请求配置与原生回复事实。现行读取位置 `workbench/src/panes.ts:889` 的 `claudeTurnFacts`，匹配 Stop 在非 controller 角色下调用它。 | 明确使用 worker 角色；写入本测试提供的 user/assistant JSONL 与 Stop effort。期望状态仍来自上述 ticket，不按产品输出改答案。 |

## 修改前证据

命令：`node workbench/tests/test_t078_claude_signals.ts evidence/2026-10-23-batch23/T-151/baseline-01/output`

Node `v26.5.0`。退出码 1。入口存在性与异会话拒收通过；登记提交场景在 Stop 读取 `native-session.jsonl` 时 ENOENT。摘要见 `baseline-01.json`；完整结果与事件从原路径整体移到其 `raw_artifacts`，没有丢弃。这是测试夹具缺口，不能称为产品缺陷红态，也不能替代迁移后的变异红态。

## 实际变更

1. 在文件头列出失败方式。明确测试只覆盖领域状态，不声称运行真实 Claude CLI。
2. 将 launch 的角色明确为 `worker`，保持原测试实际走过的非 controller 分支；没有通过改成 controller 绕过 transcript 读取。
3. 在隔离临时目录写入合成的 user/assistant JSONL（指定 prompt id、`claude-haiku-5-5` 回复模型）；首次 Stop 提供 `effort.level: high`，满足 T-151 指出的当前夹具前提。没有新增模型提取或尾注的验收主张。
4. 原七处断言均保留，期望没有反转、删除或跳过。新增两处断言核对 prompt id 已绑定、`pane_idle.data.submission` 指向原 active id，依据仍为 T-151 的登记提交关联。
5. 新增本目录的 `RUN-CHECKS-01.py`，只在临时副本注入变异，仓库 `workbench/src/**` 无修改；复跑拒绝覆盖已有 summary。

## 绿态与有效检查上的红态

以下命令从仓库根目录运行。再次复跑须给 `--summary` 新文件名。

| 证据 | 命令 | 观察与判定 |
| --- | --- | --- |
| `green-01.json` | `python3 evidence/2026-10-23-batch23/T-151/RUN-CHECKS-01.py --summary evidence/2026-10-23-batch23/T-151/green-01.json` | PASS。未改动的当前产品源码副本，测试进程退出 0，三个检查组全部 PASS，`pane_idle` 总数 1。另一次直接调用改后测试也退出 0，原始产物 `/tmp/t151-green-01`。 |
| `mutant-duplicate-stop-idle-01.json` | `python3 evidence/2026-10-23-batch23/T-151/RUN-CHECKS-01.py --mutant duplicate-stop-idle --summary evidence/2026-10-23-batch23/T-151/mutant-duplicate-stop-idle-01.json` | PASS（反例被拒收）。变异在 Claude 未匹配 Stop 分支错误追加 `pane_idle`。测试进程退出 1，仅登记提交检查组失败：原有重复 Stop 断言报 `2 !== 1`，事件总数也是 2；入口存在性和异会话拒收仍 PASS。不是 ENOENT、导入错误或夹具错误。 |

变异脚本第一次准备运行退出 1，尚未启动被测测试：最初锚点同时匹配 Claude 和 Codex 分支，触发 `RuntimeError: Claude unmatched-Stop mutation anchor is not unique`。该失败不计红态。随后锚点加入 Claude 的 `stop_hook_active` 条件，唯一匹配后才取得上表的有效红态。第一次准备失败的命令与变异行相同；当时没有创建 summary，也没有覆盖绿态或其他证据。

全部运行使用 Node `v26.5.0`、Python `3.9.6`；未启动 CLI、Electron、PTY、daemon 或 socket，无模型回合。无需 RUN-OUTSIDE 脚本。摘要里的 `raw_artifacts` 保留临时源码副本、完整事件和结果，未入 Git；如主控需要长期原件，按 T-088 归档。

## 相关回归与限制

- 本次只修一个现有测试的局部夹具，其他测试不导入本文件，产品行为未改；`regenerate_t078_p1.py` 的旧归档清单引用它，原来的“输出目录”位置参数保持不变。未运行其完整历史 P1/真实 CLI 流程，不能据此声称这些历史套件通过。
- 这份测试使用真实 `Panes.signal` 与 SQLite store，但 pane、hook 和 transcript 是合成夹具。它不证明真实 CLI 的 hook 格式、终端启动、门禁、GUI 或模型行为；这些不在 T-151 的迁移验收范围。
- 按 behavioral-acceptance-review 的边界核对了期望来源、保留断言和已知坏实现。worker 不把自查称为独立审查；新上下文的独立审查由执行主控在候选交付后安排。
- 没有发现必须扩大范围的问题；未修改产品代码、历史索引、其他测试或 `.project-map/**`。
- 收尾 `project_map.py status --root .` 退出 0，0 problems、0 stale，证据 `project-status-01.json`；`git diff --check` 通过。交付文本已回读，UTF-8 无 BOM、LF、无替换字符；未改动原文件换行方式。
