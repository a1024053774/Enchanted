# T-144-1 / attempt a1：INCOMPLETE

实现已提交候选，真实 Electron 验收、业务红态和变异证据待主控在沙箱外运行。没有把本地构建或模型自报当作验收通过。

## 修改

- 卡片标题显示角色与任务名；launch 和 attempt 的 UUID 放到悬停提示。
- 执行主控按侧栏已核实的父 launch 与当前 worker 的派发关系进入任务泳道，不用主控终端的 task 字段推断。不同任务分别计算；未关联的会话逐项说明原因。
- 泳道逐行显示项目主目录与 T-140 当前设置的额外目录。沿用侧栏状态及已结束会话列出规则。
- 只改流程投影、流程页、样式、README 流程段；未改 sidebar.ts、panes.ts、daemon.ts、门禁或验收文件。任务卡是派发前已有的脏改动，按原样保留。

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

## 旧合同冲突，未修改

`test_t111_flow.mjs:36` 仍要求泳道只有 worker，第 41 行要求 controller 在未归属；`test_t146_ended_projection.mjs:65` 同样要求已结束主控在未归属。T-144 的派发归属正好改变这些期望。两项实际运行均失败，见 `t111-01.json`、`t146-ended-projection-01.json`。后者运行时误将 `--help` 用作输出名，完整产物已移到上述证据路径，没有丢弃。

已通过 `scripts/inbox send` 上报 `20261023T140459Z-worker:b23-t144-issue-001`，正文在 worktree 的 `.project-map/inbox/`。此自动生成的上报文件不列入候选代码提交，主控可直接读取；等待主控裁定旧合同的授权更新，不自行改验收。

## 沙箱外复跑

运行：`zsh evidence/2026-10-23-batch23/T-144/RUN-OUTSIDE-01.sh`。

脚本每次新建输出目录，记录候选号、脏状态、Node/Claude 版本、每条命令的退出码和日志。包含：

1. 新 e2e 在起点 `6af6e3028cbca2d1868e32eda85eeb932b91ef17` 上的红态与当前候选绿态。
2. `uuid-title`、`terminal-task` 两个变异；汇总要求命中具体标题或归属断言，不把环境失败算成抓住变异。
3. T-146 真实会话状态 e2e、T-137 Reflect e2e、投影检查，以及上述两个旧合同的原样运行结果。

新 e2e 使用真实后台、角色申请、门禁、Claude Code `claude-haiku-5-5` 与本地脚本化 Messages 接口、真实 Electron/CDP。随机任务名防止写死标题；两个项目各有任务与派发主控，第三个主控无任务，其中第一个项目带额外目录。DOM 检查标题、悬停 UUID、逐条泳道成员、未归属原因及路径，并把截图写到摘要旁。

当前未验证：真实 Electron 展示与截图、完整业务红/绿、两个变异是否实际被拒绝、T-146 与 T-137 的 e2e 回归、独立审查。旧合同冲突未裁定，整体保持 INCOMPLETE。`RUN-OUTSIDE-01 请主控运行`。
