# T-126 候选 2 结果

- 候选：`87453d496`。候选 1 `35cadc44b` 加上审查 01 的 P2 修复；README 随后在 `ce05e1b4` 补了一句说明。证据运行期间源码未改动。
- 结论：**PASS**（待复审）。
- 审查 01 的逐条处置见 `review-01-disposition.md`；候选 1 的完整证据见 `../candidate-1/RESULTS.md`。

## 相对候选 1 的改动

`workbench/src/daemon.ts`：后台启动时，监听两个 socket 或写 `daemon.pid` 失败，会先删掉专用 socket 的临时目录，再原样抛出错误。成功路径不变。

## 单元（`unit/commands.sh`）

| 运行 | 结果 |
| --- | --- |
| cleanup-green（`tests/test_t126_failed_start_cleanup.ts`） | PASS：旧 PID 记录（失败于 `EEXIST`）、过长临时路径（失败于超长检查）两例都没有残留 |
| cleanup-red-candidate-1（同一测试跑在 `35cadc44b` 上） | 失败：`EEXIST` 一例留下 `enchanted-*` |
| credentials-green | PASS，9 项 |

## 端到端，源码入口（`e2e/commands.sh`）

| 运行 | 结果 |
| --- | --- |
| green-01 | PASS，10 项 |
| red-01-parent（`--revision 04d632694`） | 失败于 `terminal_env_has_no_data_directory_or_credential`：`['A2A_STATE']` |
| t121-green | PASS，49 项 |
| t122-green | PASS，23 项 |
| t124-restart-verified | PASS，26 项 |

候选 2 只改了启动失败路径，所以候选 1 的三个变异、t124-gui、t124-restart-working 与 t127 没有重跑；它们在候选 1 上的结果见 `../candidate-1/RESULTS.md`。

## 端到端，打包测试版（`packaged/commands.sh`）

- 新版本从 `87453d496` 重新打包（`a2a.revision` 与之对应）；修前版本仍是 `04d632694` 的那一份。
- 驱动与候选 1 相同，三个阶段一样：修前红态 → 迁移并重连正在运行的旧后台 → 新后台的终端环境、终端命令、界面批准、攻击被拒并有记录、关掉再开界面后重连。
- `packaged-01`：PASS，23 项（`packaged-01.run.json`）。截图与日志在归档盘，见 `packaged/packaged-01.archive.json`；夹具运行后删除。

## 没有验证的、已知边界

与候选 1 相同，见 `../candidate-1/RESULTS.md` 的同名一节。另外：

- 审查 01 的两条 P3 不改，理由见处置文件。
