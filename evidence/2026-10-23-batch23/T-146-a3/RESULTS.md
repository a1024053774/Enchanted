# T-146-3 / a3 交付记录

状态：**INCOMPLETE**。实现、本地红绿、投影变异与构建已完成；真实 Electron、CLI 和指定 e2e 回归等待主控在沙箱外运行 `RUN-OUTSIDE-01.sh`，没有把它们写成 PASS。独立审查与集成由执行主控进行。

身份：worker `b23-t146c`，task `T-146-3`，attempt `a3`，分支 `exec/t146-a3`，起点 `bf932d49940104ec099023aa957d06fe95116e92`。完整候选版本以本分支提交为准；未手写 A2A 尾注。任务卡见同目录 `card.md`，公共约定见上级 `COMMON.md`。

## 改动与边界

- `sidebar.ts` 保留每个项目终端最近一次确认生效的主控角色，包括已结束角色；结束优先于历史 `terminal_turn`。关闭后仍在项目层以原来的构思／执行主控身份展示，task 为 null，不重列成普通终端。理由：launch 没变，结束不抹掉曾确认的角色与子会话关系；显示历史不会让 `RoleRequests.approved()` 返回已结束身份。
- 同终端多次确认角色时，侧栏与流程仍按 launch 列一行，采用最近一次确认角色，避免重复 key。Reflect 沿用按角色申请区分历次角色的设计。未确认或只有批准而没确认的请求，不产生历史主控。
- `flow.ts` 去掉两处 ended 过滤；当前 attempt 且父归属有效的结束 worker／reviewer／monitor 留原位置，其他会话沿用“未归属”规则。阶段与归属算法没有改动。
- Reflect 和流程继续使用侧栏投影提供的状态，没有新增状态算法。renderer 将 ended 的“已结束”标签变成可见文字，沿用现有样式变量；保留读屏文字和状态图标。
- README 更新已结束会话的展示规则。未改 `panes.ts`、门禁、地图、术语表或 T-144 的标题与归属。

Ubiquitous language 沿用“Agent 会话”“角色申请”“启动记录”。本票在现有投影路径修复，没有新增跨层接口；Deep modules 的接口保持原状。真实入口的 Tracer bullet 沿用 T-146 e2e，等待沙箱外验证。

## 本地证据

运行环境：macOS，Node v26.5.0；模型无需调用。所有 JSON 用新路径写入，初次失败未覆盖。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 修前关闭已确认主控 | 预期红态：主控从 agents 消失，作为普通终端出现 | `projection-red-01.json` |
| 修后历史身份、状态、父子关系、无权限、只读查询、重复角色 | PASS（隔离 SQLite；pane 存活输入由测试提供，不证明真实 CLI） | `projection-green-01.json` |
| B 合同在起点实现 | 预期红态：缺 ended worker | `t111-b-baseline-red-02.json`；另保留首次同起点工作区红态 `t111-b-red-01.json` |
| 修改后 T-111 合同在候选 | PASS | `t111-b-green-01.json` |
| 原 T-111 合同在候选 | 预期失败：实际多出 ended worker，证明变更就是展示规则 | `t111-old-on-candidate-01.json` |
| 主控结束后回退普通终端变异 | 被拒绝：Closed confirmed controller must remain an agent | `controller-becomes-shell-02.json` |
| 流程过滤结束 worker 变异 | 被拒绝：实际 undefined，期望 ended | `flow-hide-ended-02.json` |
| 现有 T-107 侧栏投影 | PASS | `t107-projection-green-01.json` |
| 现有 T-146 SessionEnd 校验与回收 | PASS | `t146-session-end-green-01.json` |
| T-091，使用所需 VM modules 参数 | 起点与候选均失败，error、checks、known_bad_result 相同；只证明不更差 | `t091-baseline-02.json`、`t091-candidate-02.json`、`t091-comparison.json` |
| 最终标准构建（含可见 ended 标签与样式） | PASS，Vite 有既存大 chunk 警告；成功 slot 已清理 | `build-final.json` |
| `git diff --check`、Python AST、`zsh -n RUN-OUTSIDE-01.sh` | PASS | 本次命令检查；不证明运行时 |

异常保留：`t091-*-01.json` 是未传 `--experimental-vm-modules` 时的环境错误，不能当产品红态；`*-02.json` 才是正确参数下的对照。两个 `*-01.json` 变异运行因隔离副本缺 effect 依赖而失败，不算有效变异；补接已有 node_modules 后的新 `*-02.json` 才在目标断言失败。`build-01.json` 是新增 ended 标签样式前的成功构建，最终证据用 `build-final.json`。

主要重放命令（输出路径必须换新）：

```zsh
node workbench/tests/test_t146_ended_projection.mjs /private/tmp/NEW-projection.json
node workbench/tests/test_t111_flow.mjs /private/tmp/NEW-t111.json
node workbench/tests/test_t107_sidebar.mjs /private/tmp/NEW-sidebar.json
node workbench/tests/test_t146_session_end.mjs /private/tmp/NEW-session-end.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /private/tmp/NEW-ipc.json
zsh evidence/2026-10-23-batch23/T-146-a3/RUN-OUTSIDE-01.sh
```

本地变异是隔离副本中的单点更改：`sidebar.ts` 的 `current.filter(row => row.confirmed_at)` 改回 `current.filter(row => row.state === 'approved')`；或 `flow.ts` 的 worker/reviewer/monitor 绑定条件加回 `agent.state !== 'ended'`。其运行目录在各 JSON 的 argv 中。初次红态、隔离副本与 SQLite 保留在 `/private/tmp`，未放进 Git，未删除失败现场；需要归档时由主控按 T-088 处理。

## 受保护测试的逐条变更

依据均为用户 2026-10-23 裁定“B 侧栏和流程也列已结束”，授权记录 `.project-map/inbox/20261023T125315Z-ideation-answer-001.md` 问题 3，以及本 attempt 任务卡。

| 文件与候选行 | 旧期望 | 新期望／补充检查 |
| --- | --- | --- |
| `test_t111_flow.mjs:36` | 实现阶段 agents 只有 `w1,w2` | 增加 `ended`；该会话的 task、attempt、parent 本来均有效 |
| `test_t111_flow.mjs:37` | 没有对应断言 | 保留的 ended 会话状态必须为 `ended`；其他既有断言、检查名与期望值不改；unassigned 原期望不变，因为 ended 仍绑定原泳道 |
| `test_t146_session_state_e2e.py:171` | 自然退出后，侧栏／流程可缺失或 ended | 三处均必须存在且为 ended，沿用原检查名 |
| `test_t146_session_state_e2e.py:187` | 回收 worker／关闭主控后，侧栏／流程可缺失或 ended | 两种结束会话三处均必须为 ended，沿用原检查名 |
| `test_t146_session_state_e2e.py:167,190–198` | 无对应身份／可见性断言 | ended 标签可见、主控保留 executor／project／task=null／terminal 身份，且不重复进普通终端 |
| `test_t146_cli_exit_probe.py:56` | sidebar 可为 MISSING 或 ended | sidebar 必须 ended；Reflect 的 ended 期望不改 |

T-146 e2e 的配套改动：头部从暂行规则改为 B；增加两个 ended 变异入口；保存各阶段分步观察与 Reflect 截图，在侧栏同步超时时也保留后台快照与同步前 DOM。其他旧断言期望未放宽。未改其他 oracle_paths。

## 待沙箱外验证

`RUN-OUTSIDE-01.sh` 每次生成独立 outside 目录，运行 T-146 起点红态、候选绿态、两个变异，以及任务卡列出的 T-139/T-143、T-140、T-137、T-107、T-145 e2e。同时复跑 T-111 新旧合同和 T-091 起点对照。预期失败必须到达目标场景，启动错误不能算红态。

每次 e2e 都经真实后台、门禁、Electron 与真实 Claude Code CLI，模型来自本地脚本化 Messages 接口；T-140 的 Codex 按原测试执行。脚本复制截图到证据目录；完整 fixtures 与原始日志按 T-088 由主控归档。当前尚无本候选的真实 UI 截图、CLI 自然退出结论或五项 e2e 回归结论。
