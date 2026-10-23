# T-146-4 交付记录

状态：**INCOMPLETE**。最小修复和本地投影验证已完成；本 attempt 的真实 Electron／CLI 验证等待主控在沙箱外运行 `RUN-OUTSIDE-01.sh`，不将本地通过视为整票验收通过。

任务：T-146-4；attempt：a4；worker：b23-t146d；分支：`exec/t146-a4`；起点：`6af6e3028cbca2d1868e32eda85eeb932b91ef17`。任务范围与验收文件见 `card.md`，规格依据见其中引用的 T-146 与用户裁定 B。候选版本由交付提交绑定；沙箱外脚本另保存实际 HEAD 与相关源码差异。

## 改动与边界

根因：`sidebar.ts` 将所有曾确认生效的角色都作为主控保留，并直接把角色申请的 ended 当作会话 ended。`a2a release` 只结束角色，终端仍运行，因此原 T-133/T-107 等不到主控条目消失。

修复仍在同一投影入口：取终端的 pane lifecycle；角色不再 approved 且 pane 没有 ended 时，跳过主控条目，让既有普通终端投影显示真实生命周期。pane 已 ended 时仍保留最近生效的主控身份与“已结束”状态，不恢复命令权限。没有修改门禁、角色权限或终端观测器。

流程页原本消费侧栏投影，自动得到修复；没有修改 `flow.ts` 或 `FlowPage.tsx`。Reflect 按角色申请保留历史角色，已交回的历史角色仍显示“已结束”；现有逻辑已符合该语义，无须修改。也未修改 `panes.ts` 或任何 oracle_paths。

Ubiquitous language 沿用“角色申请”“普通终端”“Agent 会话”。Deep modules 的现有投影接口不变。Tracer bullet 沿用受保护的真实 T-133/T-107 入口与 T-146 入口，当前仅本地投影层验证完成。

## 已有真实入口红态

主控提供的合并回归与单独重跑，均在交回成功之后失败“超时：身份已放弃”。`existing-e2e-red-01.json` 保存原路径、fixture、命令、前置检查和角色交回回执摘录，原件保留在主 checkout 的 `merge-1/run-20261023T134713Z/`。这是已有失败证据，不是本 worker 新运行的 e2e。

本 attempt 在修改行为前运行新增投影反例，`projection-red-01.json` 实际保存了交回后仍残留的主控条目；失败为 `Released live terminal must not remain a controller`，不是启动或依赖错误。

## 本地验证

环境：macOS；Node v26.5.0；未调用供应商模型；pane lifecycle 由夹具提供，SQLite 与三处投影使用真实代码。这些检查不证明实际 CLI、Electron 或进程观测边界。

| 检查 | 结果与证据 |
| --- | --- |
| 修前交回运行中终端的角色 | 预期红态，`projection-red-01.json` |
| 修后同一信号 | PASS，`projection-green-01.json`：恢复普通终端、未知生命周期不冒称结束、新角色替换、关闭后保留身份与历史、无权限和只读查询 |
| 已知坏起点反事实 | 预期红态，`baseline-counterfactual-01.json`：隔离导出起点源码，新测试在同一目标断言失败 |
| 已结束主控回退普通终端变异 | 被既有 ended_projection 拒绝，`closed-controller-mutant-01.json`；隔离副本将 `held` 条件改回仅 approved |
| 既有 T-146 ended_projection | PASS，`ended-projection-01.json` |
| 既有 T-111 flow | PASS，`t111-01.json` |
| 既有 T-107 sidebar 投影 | PASS，`t107-projection-01.json` |
| 脚本语法与差异检查 | `zsh -n .../RUN-OUTSIDE-01.sh` 与 `git diff --check` 通过 |
| 项目地图 | session 开始及交付检查均为 Problems 0、Stale living docs 0；未修改地图、术语表或 ticket |

重放命令（输出必须使用新路径）：

```zsh
node workbench/tests/test_t146_released_projection.mjs /private/tmp/NEW-release.json
node workbench/tests/test_t146_ended_projection.mjs /private/tmp/NEW-ended.json
node workbench/tests/test_t111_flow.mjs /private/tmp/NEW-flow.json
node workbench/tests/test_t107_sidebar.mjs /private/tmp/NEW-sidebar.json
zsh evidence/2026-10-23-batch23/T-146-a4/RUN-OUTSIDE-01.sh
```

反事实重放：将起点的 `workbench/src` 用 `git archive` 导出到新的 `/private/tmp` 目录，在其 `workbench/node_modules` 接上本 worktree 已有依赖，然后给新增投影测试传第二个参数 `<隔离源码根目录>`。变异重放：复制候选 `workbench/src`，只把 `const held = current.filter(row => row.confirmed_at);` 改成 `const held = current.filter(row => row.state === 'approved');`，给既有 ended_projection 测试传该源码根目录。原始隔离目录保留，路径见 JSON 的 argv 与 fixture；归档由主控按 T-088 处理。

## 沙箱外交接

`RUN-OUTSIDE-01.sh` 按顺序运行：起点 T-133/T-107 红态（同时作为“交回后仍保留主控”的已知坏实现）、候选同测试绿态、T-146 绿态、T-146 主控回退普通终端变异、两项投影检查、T-111、T-107、T-139/T-143、T-137。每次生成新的 outside 目录，保留失败、日志和截图。红态要求交回成功且到达目标断言；关闭终端变异沿用已有业务字段判据，不接受任意失败作为反例。

待核对：本候选真实 CLI 交回角色后仍运行的实际显示、关闭／自然退出后的三处状态、四项 Electron 回归、独立审查。没有运行 Electron，没有申请沙箱越权，没有改全局配置、push、集成或接管其他 attempt。交付提交后由主控复跑、正式审查和门禁集成。
