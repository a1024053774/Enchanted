# T-144-1 / attempt a1：INCOMPLETE

首轮真实 Electron 绿态、业务红态、两个变异和 T-146/T-137 回归已由主控在沙箱外跑出预期结果。用户裁定 A 后，只调整指定三处合同断言；新断言在起点失败、在候选通过。当前等待 RUN-OUTSIDE-02 的新候选复验与独立审查，整体保持 INCOMPLETE。

## 修改

- 卡片标题显示角色与任务名；launch 和 attempt 的 UUID 放到悬停提示。
- 执行主控按侧栏已核实的父 launch 与当前 worker 的派发关系进入任务泳道，不用主控终端的 task 字段推断。不同任务分别计算；未关联的会话逐项说明原因。
- 泳道逐行显示项目主目录与 T-140 当前设置的额外目录。沿用侧栏状态及已结束会话列出规则。
- 产品代码只改流程投影、流程页、样式、README 流程段；未改 sidebar.ts、panes.ts、daemon.ts、门禁。测试仅新增 T-144 文件及按下文裁定修改三处旧断言，受保护的 T-146/T-137 e2e 未改。任务卡是派发前已有的脏改动，按原样保留。

## 已运行证据

| 检查 | 结果与证据 |
| --- | --- |
| 聚焦投影红态 | `node workbench/tests/test_t144_flow_projection.mjs evidence/2026-10-23-batch23/T-144/projection-red-01.json`，修前缺少派发主控，断言拒绝。仅证明投影缺陷，不代替真实入口红态。 |
| 同一投影检查绿态 | `projection-green-01.json`、`projection-green-02.json`：PASS；检查派发关系、同项目跨任务隔离、旧 attempt 与跨项目排除、多路径、未归属原因和输入未变。 |
| 标准前端构建 | `build-01.json`、最终候选 `build-02.json`：PASS；使用标准 `node workbench/app/build.mjs --slot ...`，临时输出已清理。Vite 的 >500 kB chunk 提示保留。 |
| 新 Python / zsh 语法 | `PYTHONPYCACHEPREFIX=/tmp/a2a-t144-pycache python3 -m py_compile workbench/tests/test_t144_flow_page_e2e.py`、`zsh -n evidence/2026-10-23-batch23/T-144/RUN-OUTSIDE-01.sh`：PASS。首次未设置 pycache 路径时写用户缓存目录被拒，改用 /tmp 后通过。 |
| 真实入口修前运行 | `e2e-sandbox-01.json`：夹具错误（同项目重复执行主控，角色独占），不算红态；已改成两个独立项目各一个任务，加第三个无关项目的主控。 |
| 修正夹具后修前运行 | `e2e-sandbox-02.json`：INCOMPLETE。真实 Claude 写文件与提交成功，但 submit 被嵌套沙箱拒绝，退出码 71。`sandbox-diagnostic-01.json` 从原生归档提取错误。未到 Electron，不算业务红态。 |
| 项目状态 | `project-map-status-01.txt`：Problems 0、Stale living docs 0。 |

原始探索现场保留 `/private/tmp/t144-1tpnqh45`、`/private/tmp/t144-pmv09lnl`；未归档或删除。依据 T-088，主控负责外置盘归档。

## 首轮旧合同冲突与用户裁定 A

`test_t111_flow.mjs:36` 仍要求泳道只有 worker，第 41 行要求 controller 在未归属；`test_t146_ended_projection.mjs:65` 同样要求已结束主控在未归属。T-144 的派发归属正好改变这些期望。两项实际运行均失败，见 `t111-01.json`、`t146-ended-projection-01.json`。后者运行时误将 `--help` 用作输出名，完整产物已移到上述证据路径，没有丢弃。

已通过 `scripts/inbox send` 上报 `20261023T140459Z-worker:b23-t144-issue-001`，正文在 worktree 的 `.project-map/inbox/`。此自动生成的上报文件不列入候选代码提交，主控可直接读取。

用户 2026-10-23 选择“A 授权改这两处 (Recommended)”。依据为主控本轮派发与 `/Users/luckye/Documents/Code/a2a/.project-map/inbox/20261023T142024Z-ideation-answer-001.md`；原件标记 `certainty: relayed`，转述用户答复 A，原样副本为 `decision-A.txt`：

> 用户答复：A。授权只把“执行主控在未归属”改为“执行主控按派发关系在其任务泳道；确实无关联的才在未归属”，其余断言、检查名、期望值不动；改动逐条写入 RESULTS 与 report。可以合入 T-144。

只修改以下三行，行号未变：

| 文件与行 | 旧期望 | 新期望 | 依据 |
| --- | --- | --- | --- |
| `workbench/tests/test_t111_flow.mjs:36` | T-A 泳道成员为 `['w1','w2','ended']` | `['controller','w1','w2','ended']` | 裁定 A：controller 是该泳道当前 worker 的派发父会话，应进入该泳道。 |
| `workbench/tests/test_t111_flow.mjs:41` | 未归属为 `['controller','old','orphan']` | `['old','orphan']` | 裁定 A：已按派发归属的 controller 不再进入未归属；旧 attempt 与缺父关系仍保留。 |
| `workbench/tests/test_t146_ended_projection.mjs:65` | 在 `flow.unassigned` 找 terminal，状态为 `ended` | 在 `flow.lanes[0].agents` 找同一 terminal，状态仍为 `ended` | 裁定 A：已结束主控仍按其派发 worker 归属泳道，只改查找位置，状态期望不变。 |

其他断言、检查名、期望值全部保留，产品代码没有新增修改。修改后的两份测试使用相同的新断言分别加载起点源码与候选源码：`contract-local-76cfr4j2/SUMMARY.json` 记录命令、源码路径、退出码及错误。起点 `6af6e3028cbca2d1868e32eda85eeb932b91ef17` 两项均退出 1，分别命中第 36、65 行；候选两项均 PASS、退出 0。T-111 在起点的首个失败是第 36 行，第 41 行未执行；候选上两行均执行并通过。起点源码副本保留在 `/private/tmp/t144-contract-baseline-ydrtkp71/source`，没有回退或改写工作区。

## 沙箱外复跑

运行：`zsh evidence/2026-10-23-batch23/T-144/RUN-OUTSIDE-01.sh`。

脚本每次新建输出目录，记录候选号、脏状态、Node/Claude 版本、每条命令的退出码和日志。包含：

1. 新 e2e 在起点 `6af6e3028cbca2d1868e32eda85eeb932b91ef17` 上的红态与当前候选绿态。
2. `uuid-title`、`terminal-task` 两个变异；汇总要求命中具体标题或归属断言，不把环境失败算成抓住变异。
3. T-146 真实会话状态 e2e、T-137 Reflect e2e、投影检查，以及上述两个旧合同的原样运行结果。

新 e2e 使用真实后台、角色申请、门禁、Claude Code `claude-haiku-5-5` 与本地脚本化 Messages 接口、真实 Electron/CDP。随机任务名防止写死标题；两个项目各有任务与派发主控，第三个主控无任务，其中第一个项目带额外目录。DOM 检查标题、悬停 UUID、逐条泳道成员、未归属原因及路径，并把截图写到摘要旁。

## 首轮沙箱外结果与第二轮交接

主控提供并已核对 `outside-20261023T141754Z-U3kdek/`（候选 `52af15174c25f5fbdeb3f74b470e5fa66335d77d`，Node/Claude 版本、各命令日志和退出码在同目录）：

- `green.json`：PASS，11 条检查通过；截图 `green.png`。真实标题、两条泳道归属、无关联主控原因、主目录与额外目录全部通过。
- `red.json`：退出 1，命中标题、派发归属、路径及未归属原因等具体业务断言；截图 `red.png`。
- `uuid-title.json`：退出 1，命中两条任务泳道的 worker/主控标题及 UUID 可见性断言；截图 `uuid-title.png`。
- `terminal-task.json`：退出 1，命中两条泳道的成员、主控标题与未归属断言；截图 `terminal-task.png`。
- `projection.json`、`t146.json`（47 条检查）、`t137.json`（10 条检查）：PASS。只有两份旧合同因上述已获授权修正的断言退出 1，首轮汇总的 INCOMPLETE 原样保留。

第二轮命令：`zsh evidence/2026-10-23-batch23/T-144/RUN-OUTSIDE-02.sh`。每次新建证据目录，使用改后的两份测试分别加载起点与候选源码，要求旧源码在指定归属断言失败、候选通过，并重跑真实 Electron green。源码副本与真实夹具均保留供主控按 T-088 归档。

合同对照目前为 PASS；第二轮真实 Electron 绿态及新候选独立审查未运行，整体保持 INCOMPLETE。`RUN-OUTSIDE-02 请主控运行`。
