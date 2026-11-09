# T-249 详情路径：真实窗口正反例与 Test 包

**PASS（本次窗口检查与打包）**。候选 `1243bc15f979976967cfd2d5cdd3a2acce6df635` 经真实 Electron 窗口完成 142 项正例检查；五个坏实现分别被指定业务断言拒绝；恢复原样后的正例再次 142 项通过。**INCOMPLETE（整票）**：最终门禁审查、terra Computer Use 与常规测试、用户敏感变更证据批准尚未完成，不能集成。

身份：task `a2a+T-249-1`，attempt `b33751df-0d57-4223-834d-4d467b199e22`，fence 4，spec/card 5。产品源码在修复前后未变；本轮增补开发测试、敏感编排脚本与文本证据。主控先独立复现旧 no-details 存活，再按 T-240 固定不变式、检查有界用户旅程；最终审查仅核对修复与新增测试的检测能力，不再整体盲审。

## 本次实际结果

| 输入 | 结果 | 核对点 |
| --- | --- | --- |
| 正确候选 | PASS，142 项 | 提交表、详情、文件 diff、根提交／普通提交／未提交／首次提交前；字面特殊路径；分支创建删除与非法名称；跟随固定、多仓库、受管只读 |
| no-panel | FAIL，符合预期 | 侧边面板存在 |
| no-details | FAIL，符合预期 | 点击提交后详情可见 |
| no-diff | FAIL，符合预期 | 点击文件后单文件 diff 可见 |
| parents | FAIL，符合预期 | 每行父提交与 git rev-list --parents 一致 |
| order | FAIL，符合预期 | 提交顺序与 git rev-list --date-order --all 一致 |
| 变异结束后原样正例 | PASS，142 项 | 全部旧正例和新增详情路径原样复跑 |

原始报告位于 [window-details-cache-02](window-details-cache-02/start.json)，各子目录的 `run.json` 保存独立 Git 预期、实际窗口观察、命令、退出码与清理结果；[变异汇总](window-details-cache-02/mutants-result.json)逐项绑定指定断言。期望从夹具 Git 的 rev-list、for-each-ref、show、diff、ls-files 取得，不从产品实现取得。真实界面使用可见提交行和文件按钮；没有把 IPC 直接读模型充当点击详情。

重放命令为候选根目录的 `/usr/bin/python3 workbench/tests/test_t249_git_graph_e2e.py --output <全新目录> --shots <本轮临时截图目录>`；反例另加 `--mutant no-panel|no-details|no-diff|parents|order`。环境 PATH 前置 `/opt/homebrew/bin`，TMPDIR/TMP/TEMP 指向本轮自建临时目录，ENCHANTED_HC_CACHE_DIR 指向本轮复制的固定 hc 0.1.15 包；产品仍按内置版本与校验值验证。依赖由主目录 `workbench/node_modules` 真复制，结束删除这份副本。

首轮原标准 `RUN-OUTSIDE-T249.sh` 退出 1，原始失败保留在 [outside-details-01](outside-details-01/summary.json)：五项隔离后台启动超时，均为 INCOMPLETE，不是业务红态；只有 no-panel 命中指定断言。首轮自有 hc 缓存为空，随后补入固定包，七次窗口运行完成。此对照支持启动环境影响的判断，但没有足够日志把网络下载认定为全部超时的唯一根因；没有改产品启动期限或加重试。

## 新包与清理

标准打包命令：`npm run package:mac -- --variant test --slot t249-fence4-details-20261108-01`。独立包：

`/private/tmp/t249-outside-9iitgp1b/a2a-build-t249-fence4-details-20261108-01/Enchanted Test.app`

包内 `a2a.revision` 精确等于上述候选，无 `+dirty`；bundle id 为 `org.a2a.workbench.test`。标准签名验证通过，固定 Electron 43.4.1 与 hc 0.1.15。Electron 素材来自官方发布资产，经已记录的本机临时源供标准打包器下载，版本检查未改。包及签名详情在 [保留记录](outside-details-01-preservation.json)和 `outside-details-01/package.log`。首次窗口批次失败不影响包是否构建成功，但也不能用打包成功替代窗口验收。

所有窗口夹具均报告 cleanup PASS、fixture_removed true、user_core_unchanged true。正式 Enchanted 后台始终 PID 81233，启动时间为 2026-11-08 13:56:08Z；首轮前后进程清单相同，复跑后再次核对。约 634 MB 本轮缓存、临时依赖和截图已按文件数／体量记录后清理，临时 HTTP 服务已停止，待 terra 验收的 Test 包保留；详见 [cleanup.json](window-details-cache-02/cleanup.json)。worker 工作区恢复干净，未改正式应用、正式后台或用户 core。

## 审查边界

主控补跑 design-integrity 自动扫描，退出 0、无发现、冻结验收无改动；另按四个修复文件人工核对：DOM／CDP 异常不吞掉，只有正常查询无结果才记业务 FAIL；脚本只扩展变异列表、指定断言映射与证据路径，原清理所有权不变。扫描只是辅助证据，不替代实际清理检查。behavioral-acceptance 的关键缺口已有本次真实正例与坏实现对照，但整个 Agent 产品验收仍缺独立 terra。

候选地图检查 Problems 0、Stale 1，仅 REVIEW.md 覆盖版本因敏感脚本变化而过期；主控主分支当前地图检查无问题。冻结 REVIEW.md 未改，覆盖版本要在审查、批准和集成后据实更新。Esc 分层关闭、终端焦点、重复选择、拖宽等留给 terra 的有界人工旅程，不能从自动测试未覆盖的部分推断通过。

**Works**：真实窗口正例两次各 142 项，五项变异各命中指定业务失败；新 Test 包版本与候选绑定。

**No regression**：窗口原有路径全部重跑；冻结验收、宿主 22/22、脚本安全 6/6 的当前候选证据保留。未运行全仓测试，历史或涉及未授权 CLI 的测试不作为本次通过证据。

**Risk / undo**：仍需最终门禁审查、terra 独立验收、用户阅读敏感脚本证据批准。候选未集成、不 push；保留原始失败，临时包只用于隔离验收，正式应用保持原版本。
