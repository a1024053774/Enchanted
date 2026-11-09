# T-249 v9 恢复交付

INCOMPLETE（整票）。worker 的三方恢复和三项机械条件通过；限定独立审查、绑定本次后台的新 Test 包与 Terra 验收尚未完成。交付候选是包含本报告的最终 Git 提交，完整提交号由本次 submit 请求绑定；不把旧包或旧独立结论视作本候选验收。

## 恢复与身份

- 本次 base：`62faa87b9424e48a4739920b53920d111a057486`。
- 原 B：`3577086056eb33e4a0c3bd2d16bbc3b30862778c`，已从当前 base 的 `evidence/2026-11-09-batch35/T-249/controller-package/verify-v7.json` 中 `result.task.current_attempt.base_commit` 独立核对，原 attempt 为 `f8b6b251-7ad4-4eb8-98da-3c91ca4a581f`。
- 原 C：`d8f55c958d901d052e79eda1a04dbf0a8fbf5ed5`。B→C 共 229 路径，15 份 README/产品/开发测试及 214 份原证据，恢复后共 1,740,201 字节。
- 本次 task `a2a+T-249-1`，attempt `ccae173b-72ec-46dd-ba4c-21c1d090e14e`，session `e9e12125-59e6-454a-8951-c6716bd29d10`，fence `8`，spec_rev `9`；完整上下文见 `run-context.json`。

`restore.py` 先读 B、C、当前 base，预检所有路径后才应用。当前等于 B 的路径采用 C；相同路径保持；README 通过 `/usr/bin/diff3 -m current base candidate` 无冲突合并。没有 Git reset/restore/checkout，没有覆盖整个 workbench，没有更改 sparse 配置。预检、应用与临时文件清理见 `preflight.json`、`application.json`。

恢复后直接读取原始字节和执行位，14 个产品/测试文件、214 份旧证据与 C 全部相同。README 的 Git 图段落逐字沿用 C，删掉该新增段落后恰等于当前 base；与 C 的唯一区别是保留 T-265 材料文件说明，见 `readme-vs-C.diff`。未重新实现或修改产品、测试与原驱动。

`equivalence.json` 核对 87 个现存保护路径与当前 base 相同，覆盖后台、冻结 acceptance、REVIEW.md、RecordsPage.tsx、records.css、依赖清单；这些范围的 Git diff 为空。后台 `panes.ts` 与旧 C 不同，保留的是当前 base 的 T-265 修复。不存在用旧 d8f55 包对应当前新后台的结论。

## 本次检查

精确命令、环境、时间、版本、退出码和清理记录在 `checks-01/summary.json`；重跑入口：

```sh
python3 evidence/2026-11-08-batch34/T-249/worker-untracked/recovery-v9/run_checks.py --output evidence/2026-11-08-batch34/T-249/worker-untracked/recovery-v9/checks-02
```

输出目录须全新，环境需保留本 attempt 的 `A2A_REQUEST_DIR`。脚本只运行卡内原 argv，设置 TMPDIR 到本 attempt 的请求目录子目录、Node 26.5.0 的 PATH 与禁止 Python 字节码；验收文件内容未改。

| 检查 | 本次结果 | 证明范围 |
| --- | --- | --- |
| `/usr/bin/python3 acceptance/T-249/check_git_graph.py` | PASS，exit 0 | 图 CLI 的顺序、父提交、引用、泳道、未提交行、分支操作与非法名称 |
| `/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t249_git_host.mjs` | PASS，27/27 | 实际 Git 与原始文件 oracle；有 HEAD/unborn 内容、特殊路径、空/二进制、只读边界和元数据原始字节 |
| `/usr/bin/python3 workbench/tests/test_t249_outside_safety.py` | PASS，6/6 | 指定业务红态与启动/CDP 失败分开，清理保留历史与链接目标 |

Node v26.5.0，Git 2.52.0。本次未构建、未调用 ps、未启动 Electron/后台/hc/额外 agent。测试自身清理夹具；结束时本次临时根剩余 0 文件、0 字节，随后移除。没有全套测试或新窗口通过结论。

## 旧证据的来源与边界

原 C 的失败、人工介入、错误基线、README 冲突、修正前空文件预期、导入失败、窗口前 INCOMPLETE 和最终红绿文本均按原字节恢复。原报告中的 C 等标识沿用当时语境，不能误作本次恢复的 C。尤其 `host-green-01.txt` 实为修正预期前失败，不能因名称判 PASS。

原 `controller-window-01/` 的 27 份文本逐份与当前 base 保存的主控来源比较，全部相同，见 `equivalence.json`。来源由主控沙箱外执行，worker 此次只读核对：candidate 200 项、deferred-candidate 49 项；old-C 与九个变异命中各自业务断言，列宽正例为 128→192→128 px。这些是原输入的历史证据，不能单独证明当前后台组合的窗口已验收；窗口原记录未内嵌提交号的限制仍保留。

v8 `99910bd1` 的文稿权限等待后 UserPromptSubmit 记账超时来自主控 #136 任务说明；worker 没有把该故障当作产品红态。任务首段指定 `recovery-v9`，正文继承的 v8 目录名没有被用作新证据目录。

## 限定自查与后续

结构扫描 13 个定位项全部位于原 C 恢复的产品文件，执行位和内容均未变；原逐项来源与职责在上级 `stop-hook-check.md`。不删除合法处理来消除扫描提示。当前限定自查见 `design-integrity-review.md`、`behavioral-acceptance-review.md`；不是干净会话的独立审查。

project-map 开始时 Problems 0 / Stale 0；恢复后 Problems 0 / Stale 1（REVIEW.md 覆盖 RUN-OUTSIDE-T249.sh）。脚本与 C 相同；REVIEW.md 冻结，MAP.md 不在写入范围。已排队非阻塞 issue `5d266908-1d60-42b8-aa64-395d5fca1aa1`，请主控限定审查后维护 Verified 并重跑 status；queued 不代表已处理。提交后状态以最终读取为准，不冒称治理已清零。

后续限定审查只核对未跟踪文件读取、只读边界、相关反例、列宽检测能力与版本/证据一致性。审查员在唯一候选副本独立构造 2–5 个小变异并给出预期、补丁、命令，由主控外部执行后原样回传；不把主控执行记成审查员执行。新 Test 包、Terra Computer Use 与常规测试、正式应用前后状态及治理收尾由主控负责。集中外部命令见 `HANDOFF.md`。

暂存路径、字节和 UTF-8 核对见 `staged-check.json`。`git diff --cached --check` 退出 2：定位到原始日志的行尾空白、原 patch 的空白上下文行，以及本次 `readme-vs-C.diff` 的一条空白上下文行；原文保留，不为消除提示改写证据。定位原输出保存在 `staged-diff-check.txt`。产品与本次撰写的报告/脚本单独检查见 `authored-diff-check.json`。

额外可写目录 `[]`，额外目录改动 `[]`。请求文件仅在专用请求目录，不进入 Git；worker 不 verify、集成、回收、安装或 push。

**Works**：229 路径无冲突恢复；除 README 保留 T-265 段落外，与 C 逐字节及执行位相同；本次三条完成条件退出 0。

**No regression**：27 个宿主场景、6 个脚本安全场景和冻结入口检查通过；87 个保护路径与当前 base 相同。未运行全套与新窗口验收。

**Risk / undo**：整票仍 INCOMPLETE；独立审查、新包与 Terra、治理 Verified 待主控。需要撤回时由主控按门禁撤回本次候选，保留 C、失败与人工介入记录，不回退当前后台或共享引用。
