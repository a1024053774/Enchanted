codex
结论：**NO_GO**。审查对象为 `t118-02.diff`；结束时受审文件仍与该 diff 一致。全程未修改文件、未提交。

发现按严重程度排列：

1. **P2：第一轮第 6 条仍未完整解决，恢复后界面继续显示旧版本。**  
   [panes.ts:394](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:394) 更新了运行时副本，但 [daemon.ts:415](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:415) 的 `workbench_snapshot` 仍通过 `launchRecord()` 读取不可变历史记录；界面使用其中的 `cli_version`。  
   场景：记录为 `2.1.304`，安装版本更新后恢复为 `9.9.9`，界面仍显示旧版本。实际 snapshot 分支的内存探针确认了该结果。应保留历史记录，同时让当前运行状态返回观测版本。

2. **P2：第一轮第 3 条只修复了大积压；小积压重连仍可回放中间画面。**  
   [renderer.tsx:252](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:252) 仅在 `next_offset < total` 时隐藏。因此积压不超过单次读取的 65,536 字节时，整个补读过程保持可见。  
   实际读取循环、生产 writer 和实际 xterm 解析器的探针中，**3,846 字节**的重绘序列产生了 **179 个未隐藏的中间画面**。writer 会拆分模式切换序列，不能把“一次 socket 读取”视为“一次画面更新”。应在重连补读期间隐藏，待写入完成再显示。

3. **P2：崩溃重载没有等待正在创建的终端，新界面可能漏掉窗格。**  
   [main.ts:614](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:614) 等待 `context.switching`，没有等待 `context.creating`。  
   场景：用户新建或拆分终端，`shell_start` 尚未返回时 renderer 崩溃；重载先读取旧 selection，随后后台才登记新窗格。旧 renderer 的回执已丢失，新 renderer 的定时刷新只更新侧栏，因此新窗格不会自动出现。时序探针确认重载时窗格集为空、随后新增窗格。应等待正在进行的创建操作完成后读取最终布局。

4. **P2：审计字段格式改变后，既有真实验收必然失败。**  
   [claudeLogin.ts:155](/Users/luckye/Documents/Code/a2a/workbench/src/claudeLogin.ts:155) 现在记录完整输出，如 `2.1.304 (Claude Code)`；[run_t108_real.py:104](/Users/luckye/Documents/Code/a2a/workbench/tests/run_t108_real.py:104) 仍断言它等于 manifest 的裸版本 `2.1.304`。  
   即使没有更新版本，正常输出也会使该断言失败。本轮证据没有覆盖最终审计的新格式，也没有对应的修前／变异失败证明。应将实际版本与独立观测值比较，将配置版本单独核对。

5. **P2：GUI 证据仍不足以验收本轮边界，提供的复现入口也缺文件。**  
   [t118drive.mjs:41](/Users/luckye/Documents/Code/a2a/evidence/2026-10-21-batch19/T-118/t118drive.mjs:41) 覆盖首次恢复及单次 `Page.crash`，没有覆盖重连、错误、无 launch、切换期间崩溃、关窗及 10 秒内再次崩溃。  
   [t118run.sh:11](/Users/luckye/Documents/Code/a2a/evidence/2026-10-21-batch19/T-118/t118run.sh:11) 引用的同目录 `register.mts` 不存在；GUI JSON 也没有可核对的候选构建身份。不能据此确认本轮完整候选通过真实 GUI 验收。

第一轮 7 条逐项核对：

| 第一轮问题 | 本轮结果 |
|---|---|
| 1. 环境过滤过头 | **PASS**：改为精确名单；真实 daemon＋zsh 证据确认保留 OAuth、Bedrock 配置。 |
| 2. 项目切换期间崩溃 | 实现已修；实际 handler 的局部时序检查通过，真实 GUI 证据 **INCOMPLETE**。 |
| 3. 重连显示补读过程 | **NO_GO**：小于等于 64 KiB 的积压仍有缺口，见发现 2。 |
| 4. 无 launch／错误永久隐藏 | 局部检查 **PASS**：空 trace、无 launch、snapshot/output 错误均结束恢复状态。真实 GUI 未覆盖。 |
| 5. 无限重载 | 局部检查 **PASS**：10 秒内第二次退出不重载；关窗期间不重载。真实 GUI 未覆盖。 |
| 6. 版本记录旧值 | **NO_GO**：审计赋值已改，运行时副本已改，但 snapshot／界面仍旧；审计验收还存在格式回归。 |
| 7. 过期版本比较文案 | **PASS**：指出的 README 文案已修；未发现生产路径残留的 CLI 版本相等比较。 |

测试独立性方面，环境、Claude 启动、Codex 启动及恢复测试使用外部夹具与独立断言，已有有效反事实：修前版本拒绝更新、泄漏标记，以及前缀过滤变异误删配置、运行时版本变异保留旧值，均因目标行为失败。**red 文件虽然标为 `INCOMPLETE`，其具体断言失败可作为红态证据。**

GUI 旧版同脚本对照也已补齐：旧版观察到 6 个可见中间帧且崩溃后未恢复；新版首次恢复采样通过。但它不能覆盖上述遗漏。恢复测试只断言内部 `panes.get(...).record`，所以未检出发现 1 的真实读取路径。

本次额外验证仅使用只读内存探针；未重跑会创建夹具或证据文件的端到端测试。
