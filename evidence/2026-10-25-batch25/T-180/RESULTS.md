# T-180 结果：不指定工作分支时自动新建 enchanted/<项目>，前缀可在设置里改

## 状态：PASS

## 依据

ticket T-180（ready_rev 1），来源 `findings/2026-10-25-lcu-real-use.md` 的 L07。用户 2026-10-25 原话：“新建 enchanted/xxx,这个分支前缀在设置里也要能改”。

## 根因

- 门禁 `create` 必须带已存在的 `branch`（不写就 `invalid_text`），后台不替主控选分支；主控说明（a2a skill）又写着“工作分支按用户说的来……不要另建分支”，所以用户没说时主控只能停下来问。
- 门禁还要求同一仓库的任务共用一个工作分支（`project_branch_conflict`），所以默认名不能按任务起，只能按项目起。

## 名称规则（本票写明）

`refs/heads/<前缀><项目名>`，前缀默认 `enchanted/`，例如 `enchanted/demo`：
- 本仓库已有任务：沿用它们的工作分支（门禁本来就只允许一个）。所以改前缀只影响之后还没有任务的项目。
- 同名分支已存在：直接用，不重建。
- 否则从仓库当前 HEAD 新建，只建分支，不切换、不动 main/master，不 push。
- 用户指定了 `branch`：照用，门禁照旧校验（必须是已存在的 `refs/heads/*`）。

## 改动

- `src/workBranch.ts`（新）：默认分支的选取与新建；前缀合法性（`git check-ref-format --branch <前缀>name`）。
- `src/gates/core.ts`：只读方法 `repoWorkBranch(repo)`，返回该仓库已有任务的工作分支。门禁的 `create` 校验不变。
- `src/daemon.ts`：三条 create 入口（终端主控、后台启动的主控经中继、操作员）都经 `createGate`：不带 `branch` 时先定分支再交门禁，回执加 `work_branch`（`ref`、`created`、`reason`、`from`），主控据此告诉用户。新命令 `work_branch_prefix`（只读）与 `work_branch_prefix_save`（仅操作员，存为追加事件 `work_branch_prefix_saved`）。
- `src/store.ts`：读当前前缀，默认 `enchanted/`。
- `app/main.ts`、`app/preload.ts`、`app/renderer.tsx`、`app/execution-settings.css`：设置页新增“工作分支前缀”一节；非法前缀显示“这个前缀不能用作 Git 分支名的开头”，不保存。
- `terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md`：用户指定了就用；没说就不要停下来问，`create` 不写 `branch`，把回执的 `work_branch` 告诉用户。

## 验收（真实 Electron，真实后台、门禁、经角色申请批准的终端主控，真实 Claude Code worker 与审查员；模型是本地脚本化接口，不耗额度）

`workbench/tests/test_t180_default_work_branch_e2e.py`。场景：项目 demo 建 T-1 不写 branch，派发、交付、验收、审查、集成；再建 T-2；在设置页先存一个非法前缀，再存 `team/`；demo 建 T-3；新项目 other 建 T-9；项目 spec 用用户指定的 `feature/x` 建 T-5，另试一个不存在的分支。

| 运行 | 结果 |
| --- | --- |
| 修前 main（`red-main-02`） | 不写 branch 的 create 被拒 `invalid_text`（L07 原样），4 项失败，设置页没有前缀一节（超时） |
| 修后 `green-03`、`green-04` | 两次 PASS 13/13 |
| 变异 `prefix-ignored`（设置的前缀不生效） | 被拒：`new_prefix_used_for_new_project` |
| 变异 `no-reuse`（不沿用项目已有的工作分支） | 被拒：`project_with_tasks_keeps_branch_after_prefix_change` |
| 回归 `test_t131_parallel_workers_e2e.py`（同项目两个 worker 并行、各自集成） | PASS |

`green-03` 实测：T-1 回执 `work_branch = {ref: refs/heads/enchanted/demo, created: true, reason: default, from: main}`，新分支起点等于 main 头；派发、审查、集成都一次成功，集成后 `enchanted/demo` 前进、含 `done.txt`，main 头不变。T-2、T-3 沿用 `enchanted/demo`（`reason: repo_tasks`），改前缀后也没有建 `team/demo`。other 的 T-9 得到 `refs/heads/team/other`。spec 用 `feature/x` 照用，没有建 `team/`、`enchanted/` 分支；不存在的 `feature/missing` 被门禁拒绝。

截图：`shots/green-04-01-settings-prefix.jpg`（设置页“工作分支前缀”，已存为 `team/`）。

## 测试第一版的运行（保留在 `test-v1-runs/`）

第一版测试没有覆盖“改前缀后已有任务的项目沿用原分支”，变异 `no-reuse` 在第一版下通过（第二个任务用默认名也恰好落在同一分支上），说明那一版测不出沿用逻辑。补上 T-3 检查后，红态、绿态、两个变异全部重跑，上表是第二版的结果。

## 没做 / 未验证

- 没有用真实模型跑：主控读了新说明后会不会不再停下来问、会不会把分支名告诉用户，本票没有新增证据；T-181 的真实 haiku 复跑会一并观察。
- Codex 主控用同一份 skill 说明；本票没有单独用 Codex 跑。
- `test_t178_flow_project_scope_e2e.py` 在本分支不存在（T-178 未合并），没有作为回归运行。

## 独立审查

agy（gemini-3.8-flash-high，只读）审查候选 74724cfa0：`T-180 REVIEW PASS`。
- P1：候选从 T-177 合并前的 main 切出，diff 里看起来像删除了 T-177。处置：用 `git merge` 三方合并，合并后重跑 T-177 与 T-180 的 e2e（结果见合并后的记录）。
- P2：同名分支已存在时直接沿用，若是很久以前的旧分支，任务会从旧代码起步。回执里 `created: false, reason: existing` 会告诉主控，skill 要求主控转告用户；属已知取舍，本票不改。
- P3：审查员认为 `regression-t131-01` 没有 summary。实际已提交：`regression-t131-01/summary.json`（status PASS）。审查员误读。
全文 `review-agy-01.md`，启动参数 `review-agy-01-argv.txt`。
