# T-111 / a1：系统流程页

状态：**INCOMPLETE**。尚未提交（沙箱拒绝创建共享 Git 元数据中的 index.lock）；功能已实现；本轮沙箱内合同、反事实和构建通过。真实 Electron 红／绿态、真实 daemon/socket 的零写入及写入变异检查尚未运行，不能作为最终验收通过。未调用模型，未 push。

## 候选与范围

- worktree：`/Users/luckye/Documents/Code/a2a-wt-t111`，分支 `exec/t111`。
- 起点：`b1ecd6e9cba23c1bbddb331822b6500a1488e2e9`；规格：T-111 ready_rev 1；task T-111 / attempt a1。
- worker session：`10858660-9c4e-4904-9811-feb626a89c75`；launch：`launch-c9958cdeceed4ee2a1b96ada1da39586`；native thread：`01a1580e-96ab-73d2-b5a5-c7f825736cab`。提交实际模型／强度取钩子尾注，不把请求配置当实际取值。
- Tracer bullet：先建立缺失流程投影的合同红态，再贯通只读投影 → daemon → window IPC → 单票实现阶段 worker 胶囊，并构建；随后扩展多票、折回、折叠、空状态与窄窗。
- Deep modules：领域投影集中在新 `src/flow.ts`，界面集中在新 `app/FlowPage.tsx`；原有层只接线。Ubiquitous language 沿用任务、attempt、启动记录、门禁阶段和已有七种 agent 状态。
- 不改门禁状态机、侧栏数据实现、派发与原生采集，不操作用户的 CLI 全局配置。

## 验收逐项

| 要求 | 状态与证据 |
| --- | --- |
| 当前没有流程页的红态 | PASS（合同）：`contract-red.json`；已知坏起点由 `counterfactuals-final-02.json` 再次拒绝。真实 Electron 起点红态待运行。 |
| 单独“流程”标签，一票一横向泳道 | 已实现；构建通过，真实 Electron 待运行。 |
| 两票并行：实现 2 worker、审查 1 reviewer | PASS（领域合同）`contract-final-03.json`；真实 Electron 四票夹具待运行。 |
| 阶段、胶囊与记录对应 | 阶段只由当前 attempt 的事件推进；agent 只按核实的父关系、任务和当前 attempt 放置。monitor 在泳道上方，结束会话不列为当前参与者。合同及三个变异检查 PASS；真实 IPC 数据一致性待运行。 |
| 打回线与次数 | 只累计该票的 `delivery_rejected`；附属 verification/review 结果不重复计数；保留此前 attempt 的打回次数。合同 PASS；真实 Electron 待运行。 |
| 无父记录／缺失父项／过期 attempt 进未归属 | 已实现；无父和过期 attempt 的变异被合同拒绝；缺失父项由已有侧栏事实校验负责，真实 Electron 待运行。 |
| 超过 4 个折叠、展开；已集成票默认折叠 | 已实现；真实 Electron 待运行。 |
| 空状态、窄窗横向滚动 | 已实现；真实 Electron 待运行。 |
| F2／F3 零写入及能拦住写库 | 待运行：实际 daemon/socket／SQLite／collector 检查；`flow_snapshot` 被纳入 catalog 只读路径，不记录读取请求，不调用 scan。独立比较全部 SQLite 表、schema 和 trace 原值；再注入一次 `store.event` 写入变异并要求拒绝。 |
| IPC 原拒绝检查不削弱 | PASS：`ipc-final.json`；完整保留旧拒绝与反例，扩充为 21 个 handler／22 个 bridge 名称，flow 只发送读命令、不发输入凭据，拒绝 iframe 和未知 window。 |
| 地图 status 0 问题 | INCOMPLETE：开始与结束均有 8 个既存缺失链接／文件问题，属于稀疏 checkout 未包含的 findings 与 grilling 文件；没有修改地图。结束 stale living docs 为 0，见 `project-map-status-final.txt`。 |
| 独立审查 | 未进行；交执行主控新开只读 reviewer。worker 自查不充作独立 behavioral acceptance review。 |

## 与参考图对照

已读取用户参考图。结构对齐：横向空心节点与细连接线，节点之间用 `›››`，节点下放阶段名称与竖排圆角胶囊，左侧彩色点、右侧会话标识与角色；超过四个显示“还有 N 个 ↗”；机械检查／审查有返回实现阶段的折回线；横向滚动。

有意不同：沿用现有工作台深色主题；以系统实际五个门禁阶段取代参考图的设计工作阶段；按票上下排列泳道；额外标出票号、项目、当前阶段、状态文字与 attempt，monitor 置于泳道上方。启动记录没有独立展示名，使用记录号，不根据终端文字造名字。相同阶段多次打回合并为一条带次数的折回线。颜色只区分胶囊，运行状态同时用图标和文字表达。

以上是设计／源码结构对照，**尚非真实 Electron 渲染通过结论**。按执行主控转达的用户原话“证据截图什么的都不要了,我也不会看”，本轮没有保存截图；GUI 验证脚本也不生成截图。

## 文件与并行合并提示

`renderer.tsx` 只改这些接线位置（本候选行号）：

- 9–10：导入流程组件和只读快照类型。
- 43：声明 `window.a2a.flow()`。
- 398：本地页面选择状态。
- 571–576：添加“终端／流程”标签、挂载流程页并包装现有终端区；617：闭合包装。

没有修改 `sidebar.ts`；`renderer.tsx` 的侧栏、提问状态和原终端内部逻辑均未重写。T-108 合并时核对上述接线即可。

## 复现与未完成检查

沙箱内已运行：

```sh
node workbench/tests/test_t111_flow.mjs evidence/2026-10-20-batch18/T-111/contract-final-03.json
python3 workbench/tests/test_t111_counterfactuals.py --summary evidence/2026-10-20-batch18/T-111/counterfactuals-final-02.json
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs evidence/2026-10-20-batch18/T-111/ipc-final.json
node workbench/app/build.mjs --slot t111-final-01
```

上述报告均使用新路径排他创建；重跑须改新文件名／slot。Node v26.5.0、npm 12.0.1，依赖在本 worktree 以 `npm ci --ignore-scripts --cache /private/tmp/a2a-t111-npm-cache` 安装，无跨目录依赖链接。构建在内置盘，只有现有包体积提示，没有构建错误；本次临时 cache/tmp 在交付前清理，dist 保留。Python 两个新脚本通过 3.9 语法检查，driver 通过 `node --check`；未宣称等同 Python 3.9 实跑。

首次反事实准备缺依赖，`counterfactuals-01.json` 与 `/private/tmp/t111-counterfactual-gn08909u` 保留；这是测试环境失败，不作业务红态。修正为私有普通依赖副本后，02、final 及 final-02 均 PASS。

收尾自查补充了缺失 attempt 的边界：任务和启动记录都没有 attempt 时，两个 undefined 不得视为绑定。`missing-binding-red.json` 保留该针对性红态；新增非空当前 attempt 前提后，同一合同在 `contract-final-03.json` 转绿。

执行主控应运行：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-01.sh
```

默认 Electron dist 为 `/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist`，可用 `T111_ELECTRON_DIST` 显式指定内置盘 43.4.1 dist。脚本清理 Git 路由变量、设 `LC_ALL=C`，以 Python 3.9 兼容语法运行，测试服务脱离调用者进程组。不调用 CLI 模型。GUI 起点来自上述 baseline 的普通归档副本，测试驱动读取真实 DOM／IPC，不替换产品响应。

脚本顺序：真实 daemon 的 flow 读取零写入 → 写库变异必须失败 → 起点 Electron 缺标签红态 → 新候选四泳道／折回／折叠／空态／900px 窄窗绿态 → 实际 IPC 所有表、schema、trace 原值比较。GUI 夹具中的状态保持已有规则判为未知，不凭“prepared”伪造运行中。

成功清理测试夹具与构建；失败保留进程归属、夹具及输出路径。保留的失败现场需执行主控按 T-088 归档后再处理，不能为取得通过而删除。没有更改用户提供的 ticket 验收勾选，也未进行门禁 submit。

## 提交交接

`git add --sparse` 在沙箱内被拒绝：`Unable to create '/Users/luckye/Documents/Code/a2a/.git/worktrees/a2a-wt-t111/index.lock': Operation not permitted`。没有暂存成功或部分提交；没有申请升级，也没有直接操作共享 Git 元数据。

由执行主控在沙箱外运行保留本 worker 原身份的脚本（尾注仍由原钩子自动追加）：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/RUN-OUTSIDE-COMMIT-01.sh
```

脚本核对分支、起点、空暂存区，使用明确文件清单和 `git add --sparse`。先提交当前 INCOMPLETE 候选以固定完整代码版本，再运行真实验证并交独立审查；本轮验证报告会绑定该提交。验证结果与本记录的状态更新可由主控后续提交。若候选变化或检查失败，不沿用本轮绿态。
