# T-106 / a1：提交后失败响应的分类修复

2026-10-19。**INCOMPLETE**：P1 已修复，实际 daemon/门禁/SQLite 触发器红绿与原检查通过；新候选真实 Electron 按钮检查、提交和独立定向复审仍需主控完成。本轮不调用模型、不操作原生目录对话框、不交截图、不 push、不申请升级。

绑定 task `T-106`、attempt `a1`，session `46c7c0a5-076f-48e7-adc0-4aea62a637a9`，launch `launch-d83c474a34f148c19f8e35e9bd60ff71`。起点与已知坏候选为 `24cacef60f9e88103213c0bb93eecb0cb5c41cf3`。派发未提供 fence/spec_rev，不推断其值；本次范围取主控 #42 与独立审查 01 的 P1。原审查报告、主控的 `form-electron-01.json` 和原复验脚本保持原样、未替主控纳入本 worker 暂存范围。

## 根因与修复

原 main 将所有 `card_save ok:false` 归为未保存。然而业务事务 COMMIT 后，daemon 仍可能因结果事件写入失败返回 `orchestration_failed` 或 `event_write_failed`。create 同样存在任务已注册、结果事件失败的情况。

修复只在原表单 main/renderer，不改 daemon、门禁、校验规则或 IPC 名称集合：

| 阶段与结果 | 处理 |
| --- | --- |
| 格式校验拒收 | 尚未调用保存，保留可编辑/取消的草稿。 |
| card_save 的 `invalid_task_card`、`invalid_card_version`、`card_version_conflict` | 这些错误在卡版本提交前拒绝，按本次未保存处理。 |
| create 的 `project_branch_conflict`、`invalid_work_branch`、`invalid_repo`、`invalid_title` | 这些错误在任务提交前拒绝；已成功保存的卡片仍保留，不允许重试写命令。 |
| card_save 的其他失败或通信异常 | 只读调用一次 `card_show`，核对第 1 版及门禁规范化后的整份卡片。匹配时说明卡片已保存，停止自动流程，不自动进入 create；可关闭表单并保留记录。 |
| create 的其他失败或通信异常 | 只读调用一次 `status`，核对 task、project、repo、title、branch、card_version、整份卡片和 ready 状态。匹配时按实际已注册结果刷新列表。 |
| 只读请求失败、记录不匹配或未读到记录 | 保持 `persisted: "unknown"`，不猜成未保存。main 拒绝取消、再次提交和重新选仓库；renderer 显示未知，禁用取消、确认、字段与 Escape 取消。 |

`persisted` 现有布尔结果扩展为 false/true/"unknown"，分别对应本次明确未保存、已知保留记录、无法核实；没有增加第二条写入 API。IPC 本身异常且已经尝试提交时，renderer 也进入未知，不能因收不到结果重新启用提交。失败详情与只读核对结果都保留，未静默吞掉原错误。

**Tracer bullet**：沿实际 main → daemon 认证/解码/处理 → 原门禁 → SQLite 取得提交后故障红绿，再核对 UI。**Deep modules**：事务与错误合同仍由原门禁/daemon 拥有；表单只根据可核对事实分类，不增加回滚、重放或后台补偿。**Ubiquitous language**：未保存、已保存、未知分别表达，不用一个失败布尔值代替持久化事实。

## 已执行的红绿与回归

新 `test_t106_postcommit.mjs` 沿用审查 `probe-postsave-02.mjs` 的方法：实际 main、daemon、operator 认证、门禁和 SQLite；只提供 Electron、PTY 与 socket 监听边界。SQLite 触发器仅阻断指定请求事件，不把实际保存替换成模拟结果。独立 SQL 计数确定故障发生在业务提交前还是提交后。

```sh
node --experimental-vm-modules workbench/tests/test_t106_postcommit.mjs evidence/2026-10-19-batch17/T-106/postcommit-green-final-03.json
node --experimental-vm-modules workbench/tests/test_t106_postcommit.mjs evidence/2026-10-19-batch17/T-106/postcommit-red-final-03.json /private/tmp/t106-knownbad-k3e738g_
```

第一条退出 0，七场 PASS；第二条退出 1，七场在缺少只读核对的业务断言处拒绝旧候选。该旧目录由 `git archive 24cacef60 workbench` 解包，未修改旧实现；不是故意破坏导入或设置的红态。

七场分别覆盖：保存提交后结果事件失败；进一步触发 event_write_failed；保存后的只读核对也失败；请求事件在保存前失败且没有卡版本；同编号已有内容不匹配的旧卡片；任务已注册后结果事件失败；任务注册后 status 也无法核实。最后两场真实 task 行与快照均已落库；失败没有被误判成没有任务。未知场景中，实际 main 的取消/重试/重新选目录均被拒；每次被测写命令只调用一次。

早先五场、六场的探索红绿摘要保持原件，不覆盖。红态临时 SQL 夹具和旧源码目录保留在摘要所列 `/private/tmp/t106-postcommit-*` 与 `/private/tmp/t106-knownbad-k3e738g_`，依赖副本已清理；原始夹具后续归档由主控按 T-088 处理。仓库只放文本摘要，不放 sqlite 或完整 run 目录。绿色运行在关闭实际门禁/存储后清理自有夹具。

原检查均未改断言，重跑 PASS：

```sh
node --experimental-vm-modules workbench/tests/test_t106_creation.mjs evidence/2026-10-19-batch17/T-106/postcommit-creation-regression-01.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-19-batch17/T-106/postcommit-pane-regression-01.json
node --experimental-vm-modules workbench/tests/test_t105_panes.mjs
```

原来的格式拒收、版本冲突、目录信任边界和保存前失败后可取消仍有效；17/18 名称集合、旧反例及三个已有窗口变异检查保持。没有修改这些测试源文件。

在内置盘临时源码与依赖副本中运行标准 `node app/build.mjs --slot postcommit-final`：PASS，见 `postcommit-build-01.json`；完成后该副本、缓存和输出均清理。Vite 仍提示 chunk 超过 500 kB，本轮不扩大优化范围。新 runner/脚本检查 Python 3.9 语法，shell/node 语法、UTF-8 回读、JSON 解析与 diff 检查均完成；外部实际 Python 3.9 执行尚未完成。

## 主控提交与重跑

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t106
bash evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-04-COMMIT.sh
bash evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-03-POSTCOMMIT.sh 01
```

第一条核对 exec/t106、固定起点、暂存范围和未暂存产品变化，用本 worker 非秘密身份让既有钩子添加尾注；共享 Git 元数据写入交主控在沙箱外执行。

第二条**无需人手操作目录对话框**。它使用实际内置盘 Electron 43.4.1、daemon、门禁、SQLite；只有观察 driver 的 `dialog.showOpenDialog` 返回固定夹具路径，明确不作为新的原生目录选择证明。它先在固定旧候选重现“卡已保存但仍允许取消与重试”的真实 GUI 红态，再在当前候选运行五场提交后故障：检查已保存提示、未知时禁用取消/确认、实际已注册后列表出现、SQL 记录及无写命令自动重放。完成条件不会被执行，没有模型或截图。

默认只读复制本机已有依赖，可用 `T106_DEPENDENCIES` 指定；Electron dist 可用 `T106_ELECTRON_DIST` 指定同版本内置盘路径。源码、依赖、缓存与输出都在新的内置盘临时目录，不改共享 checkout 的输出/依赖。所有自有进程退出经核对后清理依赖与构建；通过时清理夹具，仅保留 `postcommit-electron-01.json` 摘要。失败或退出未知保留现场位置，旧编号不覆盖。

本候选真实 Electron 尚未运行；原 `form-electron-01.json` 只证明旧候选健康路径，不能替本修复背书。独立审查 01 的 NO_GO 也保持原结论；请主控冻结新候选后按 [behavioral-acceptance-review](/Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md) 的 “Review one frozen candidate snapshot in a fresh, read-only context.” 做一次针对 P1 的复核，本 worker 的自检不能代替独立审查。

`project_map.py status` 仍退出 1：稀疏 checkout 的 8 个既有缺文件诊断，stale living docs 0；未改地图、术语或其他 ticket。真实模型根回合 0。
