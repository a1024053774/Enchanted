# T-077 变基冲突处理（主控 #53）

状态：**INCOMPLETE**。执行主控已在沙箱外将 `beaeab3c` 重放到 main `457e02a8`，当前只完成两个文件的冲突整理与静态核对，等待主控 `git rebase --continue`。未 abort、未重复申请提权、未运行行为测试；真实用量 0/4。

- `core.ts`：保留 T-077 的共享 claim/dispatch 实现，迁入 main 的 `runtime_identity: null`、创建后身份绑定、启动后 `bindObservedIdentity`。稳定身份检查、submit/reclaim 身份门槛及 run 的停机边界均保留；T-077 的命名、路径交集、冲突新 attempt 与重交基线不变。
- `panes.ts`：`readThread` 同时返回 main 的 runtime_identity 和 T-077 的 session_ended，保留已结束会话不算 running 的判定。归档释放名额、rollout 工作目录归属、gate 队列回写保留；main 的请求模型/强度环境字段保留。
- 自动合并的 README 与 `a2aGates.ts`：main 的所有原行按顺序保留，新增 T-077 文档与字段。daemon、transport、提交尾注 hook、stateConsistency、原受控 host 与 main 逐字节一致。

`checks-02.json` 保存 18 项静态保留核对和 Node 语法、差异格式检查，均通过；它不表示变基候选通过业务验收。首份 `checks.json` 保留一次检查脚本错误：读取 hook 符号链接时跟随到了文件内容，却与 Git 保存的链接目标名比较，误报一项不等。修正后分别核对 `readlink` 的目标名和 `hook.py` 文件，未改产品或 Git 链接。两份 `.conflicted.ts` 保存处理前现场，stage1/2/3 分别来自起点、main 与本卡候选。重建各来源文件的命令为：

```sh
git show 14b57d22:workbench/src/gates/core.ts
git show 457e02a8:workbench/src/gates/core.ts
git show beaeab3c:workbench/src/gates/core.ts
git show 14b57d22:workbench/src/panes.ts
git show 457e02a8:workbench/src/panes.ts
git show beaeab3c:workbench/src/panes.ts
```

语法与格式检查可重放：

```sh
node --check workbench/src/gates/core.ts
node --check workbench/src/panes.ts
node --check workbench/src/contracts/a2aGates.ts
git diff --check -- workbench/src workbench/README.md
```

主控继续变基后，下一阶段在同一候选上合并运行完成条件、8/9/18、CAS、cards 和七项冲突检查，再准备真实场景与一次独立审查。真实场景还须覆盖同一隔离 home 内历史根 CLI 记录保留与新 attempt 身份归属（主控 #51）。
