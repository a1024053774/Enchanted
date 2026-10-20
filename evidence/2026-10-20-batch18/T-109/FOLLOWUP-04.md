# T-109 / a1：修复独立审查 F1 的正式验收缺口

状态 **INCOMPLETE**。本地已补足并证明标题推断变异会失败；新候选的真实入口、Tab 补验与独立复审待执行。上一份独立审查的 NO_GO 结论保留，不提前上调。

本次只修改三份正式验收文件，没有修改产品归属算法、侧栏、状态识别、门禁或原键盘驱动。

## 正式合同补强与红绿顺序

`test_t109_hierarchy.mjs` 不再把 `listTasks` 固定为空。夹具实际保存 tasks 表，目录适配器读取这些记录；它仍是投影合同，不冒充真实门禁入口。真实入口由下述 Electron 场景覆盖。

先用独立给定值核对三级关系、旧 worker 和缺失父项必须未归属、执行主控后代为 3、构思主控后代为 4。再仅修改已保存任务的 title，依次使用：

- “执行主控派发的 worker”；
- “构思主控与审查员的任务，与派发无关”。

每次都要求旧 worker 和缺失父项仍未归属，全部 agent 的父项与完整后代汇总保持不变。同时比较持久化值：仅排除任务 JSON 的 title 值，其他任务字段、所有其他表、schema、trace 均不变；每次 sidebar 读取仍执行原完整零写入检查。

先运行独立审查原来的错误分支：

```sh
env -u GIT_DIR -u GIT_WORK_TREE LC_ALL=C node workbench/tests/test_t109_hierarchy.mjs \
  /private/tmp/t109-title-mutant-red-04.json \
  /private/tmp/t109-review01-l8gy_g04/candidate/workbench/review-mutant-task-title02/sidebar.ts
```

结果 **rc 1**，明确业务失败：`Task titles must not supply parent launch facts for legacy sessions`，实际父项 `exec`，预期 null；不是依赖或设置错误。随后对未修改的候选归属算法运行同一合同，**rc 0 / PASS**。

`test_t109_counterfactuals.py` 也已永久纳入 F1 的同一个错误分支，放在一次性副本中。重新运行后五项均取得预期拒绝：起点启动丢父字段、起点投影忽略父字段、侧栏偷写事件、忽略父项冲突、按任务标题推断父项。摘要与确切命令见 [title-proof-04.json](title-proof-04.json)。

## 真实场景补强

`run_t109_hierarchy.py` 在既有 `create` CLI 中给 task-0 提供真实标题“执行主控派发的 worker”。旧 worker `legacy` 和缺失父项 `missing` 原样保留；原三级缩进、折叠、状态计数、键盘、聚焦、窄窗及零写入断言均保留。

候选窗口加载后，再仅修改本次隔离 SQLite 夹具的任务 title，分别改成无角色名称的标题与另一份诱导标题。通过真实 `sidebar` IPC 确认返回的是新保存标题，父项与完整后代汇总保持不变，旧会话和缺失父项仍未归属。除 title 外的持久化值必须不变；不改任何 launch、派发或 relay 事实，也不替换产品响应。

这部分尚未在本次新候选上运行，不能用上一候选 `outside-03.json` 的通过代替。新脚本把该项结果另记为 `title_invariance`，保持既有四组整体检查结构。

## 提交与复跑

1. 执行 [RUN-OUTSIDE-COMMIT-04.sh](RUN-OUTSIDE-COMMIT-04.sh)，将三份验收修改与摘要提交到 `exec/t109`。要求 HEAD 为 `0034e35ada8242c857156794c1f4996c44b9225c` 且没有其他已暂存改动；使用本 worker 既有启动绑定和原自动尾注钩子，`git add --sparse`，不 push。
2. 执行 [RUN-OUTSIDE-04.sh](RUN-OUTSIDE-04.sh)，对干净的新提交运行正式真实入口，输出 `outside-04.json`。
3. 执行 [RUN-OUTSIDE-TAB-04.sh](RUN-OUTSIDE-TAB-04.sh)，沿审查脚本的真实 Tab 路径复跑新提交，输出 `outside-tab-04.json`。该脚本从当前已提交 HEAD 建私有 archive 与普通依赖副本，只在副本内给测试驱动加入审查原有的 Tab 遍历；产品源码及所有正式断言保持新提交原文。摘要核对产品差异为空、唯一额外改动为私有测试驱动，并要求新的标题不变性与真实 Electron 检查同时通过。它是作者复跑，不是新的独立审查结论。

原 `REVIEW-OUTSIDE-01.sh` 与独立报告均未修改：该脚本固定旧 `0034e35ad`，还把旧合同的假绿作为预期现象，所以不能直接作为新候选的通过检查。新 Tab 包装脚本只复用其 Tab 输入步骤，不复用旧候选的结论。

Node、zsh 和 Python 3.9 语法与 diff 检查通过。地图 status 仍为稀疏 checkout 的原 8 条缺失链接、0 stale living doc，见 [project-map-status-04.txt](project-map-status-04.txt)；未改地图、票据或治理规则。真实模型回合 0；没有截图。
