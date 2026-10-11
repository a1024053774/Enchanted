# T-075-2 验收差异白名单核对（沙箱外交接前）

状态：PASS，仅指差异范围核对；不替代测试结果。比较起点 `e5e7dbb841131935aac0bd061649a55e7a1e7d20`，命令：

```sh
git diff e5e7dbb841131935aac0bd061649a55e7a1e7d20 -- acceptance/
```

完整差异保存为 `acceptance-before-outside-01.patch`。当前 acceptance 仅三个文件有变化：

| 文件 / hunk | PLAN 白名单 | 核对 |
| --- | --- | --- |
| test_coop_e2e：INTEGRATION_REF、git init、create helper | A1（同时实现 A6 的 oracle/barrier 全文封入 argv） | 目标改为 main；卡字段来自独立夹具；原分页 oracle 内容与预期不改。 |
| test_coop_e2e：重复 create | A2 | 只替换注册输入；拒绝、业务状态与事件断言不改。 |
| test_coop_e2e：oracle snapshot 正例 | A3 | 源文件修改后另存 V2，当前任务仍用 V1；一次集成和重放断言保留。 |
| test_coop_e2e：baseline change | A4 | 外部 commit 已推进工作分支，删除多余 update-ref；原拒绝断言保留。 |
| test_run_e2e：正常 run 后主分支 | A5 | HEAD 到 M，检查目录与索引；辅助进程正例复用同一修改，其他编排断言保留。 |
| test_recovery_e2e：GIT_BARRIER | A8 | 记录/转发 stdin 事务；before 在真实事务前，after 在实际 commit 成功后；只包装真实 Git。捕获 BrokenPipeError 仅处理已被 SIGKILL 的调用者不能再读取这一既有注入场景，原始 Git 结果仍落盘。 |
| test_recovery_e2e：frozen_keys | A7 | oracle 路径键替换为卡快照/卡版本/命令数组；原身份/G/C/M/worktree/command_intent 保留。 |
| test_recovery_e2e：unknown_reference | A9 | 删除工作分支时保留一个夹具引用供 show-ref；外部 X 的 commit 已改分支，删除多余 update-ref。原恢复拒绝及历史断言不变。 |

A10 位于 `workbench/tests/test_cas_race.py`，同样仅删除外部 commit 后多余的 update-ref，保留外部 X 不被覆盖的全部断言。

新增任务卡与目录快进恢复测试都在 `workbench/tests/`，没有改写其他 acceptance 断言，没有删除或跳过原 8/9/18 场景。实际三套运行结果待沙箱外收据。
