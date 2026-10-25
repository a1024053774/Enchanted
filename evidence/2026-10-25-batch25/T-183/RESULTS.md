# T-183 结果：被门禁拒绝的 create 不再留下后台新建的工作分支

## 状态：INCOMPLETE（e2e 全过；待 agy 审查、合并）

## 依据

T-183（执行主控按 T-004 边界自建的缺陷票，`ready_by: executor`），来源 T-181 真实 haiku 复跑：主控第一条 `card_save; create` 里卡保存被拒，create 随之以卡版本不存在被门禁拒绝，但后台已在门禁之前新建了 `enchanted/demo`；第二次 create 回执 `reason: existing`，主控如实转述为“沿用已有分支（没有新建）”，与事实不符。

## 根因

T-180 的 `createGate` 先建分支、再交门禁（门禁要求分支已存在），门禁拒绝时没有撤销本次新建的分支，create 不是原子的。

## 改动

- `src/workBranch.ts`：新建分支时记下起点提交，返回 `made: { ref, sha }`；新函数 `dropWorkBranch` 用 `git update-ref -d <ref> <sha>` 删除，只在分支仍指向该提交时生效。分支已被移动时不删，改为拒绝 `work_branch_cleanup_failed`，并带上门禁原来的拒绝原因。
- `src/daemon.ts`：`createGate` 在门禁返回失败或抛出拒绝时，删掉本次新建的分支，再原样返回或抛出门禁的结果。沿用已有分支（`existing`、`repo_tasks`）时什么都不删。

## 验收（真实 Electron、后台、门禁、终端主控；脚本化模型，不耗额度）

在 `workbench/tests/test_t180_default_work_branch_e2e.py` 里加场景 8：新项目 atom，主控不写 branch、卡没保存就 create（门禁拒 `unknown_card_version`），核对没有留下 `team/atom`；再正常保存卡后 create，回执应为 `created: true, reason: default`。

| 运行 | 结果 |
| --- | --- |
| 修前 main（`red-main-01`） | 2 项失败：被拒后 `team/atom` 留在仓库（指向 217aebf），下一次 create 回执 `created: false, reason: existing`，与真实复跑一致 |
| 修后 `green-01` | PASS 15/15（含 T-180 原有 13 项） |
| 变异 `keep-branch-on-refusal`（门禁拒绝时不删） | 被拒：同样 2 项 |

## 没做 / 未验证

- 分支被别人移动后的 `work_branch_cleanup_failed` 分支没有覆盖。
- 没有用真实模型复跑。
