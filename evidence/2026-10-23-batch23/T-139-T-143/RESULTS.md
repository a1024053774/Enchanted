# T-139 / T-143 同批验证（attempt a1）

状态：**INCOMPLETE**。RUN-OUTSIDE-04 的联合候选与全部指定回归已通过；本次撤掉未经验证的 WebGL，
新增大量输出到可见的耗时测量，最终源码须经 RUN-OUTSIDE-05 重新联合验证。**滚动改善尚未证明。**

## T-139

项目视图每任务一格；任务视图仅含该任务 agent；单 agent 视图仅显示自己；项目普通终端有单独入口。
单 agent 重命名/关闭保留兄弟布局与名称；项目终端布局保存只包含 task=null 的终端。
普通终端在 sidebar_snapshot.terminals，经批准角色在 agents，放弃角色后仍可从普通终端入口访问。
项目行菜单、三份受保护 oracle、地图和 ticket 未修改。

最新真实证据：`outside-04-kDtDFKqW/`，测量 v2、工具 v4，代码 `117045d00e74bc317c95e4f2bd14a7426e5b9bc3`。
每次夹具含两个任务各一位真实 Claude CLI worker（请求 claude-haiku-5-5，本地脚本化 Messages 接口），
另有经角色申请批准的项目主控终端；同一 Electron 运行覆盖视图和性能。它不证明供应商模型推理能力。

| 验收项 | 结果与证据 |
| --- | --- |
| 修前红态 ebbae7bd0 | NO_GO，baseline-v2.json 准确落在五项：task_A_only_its_agents、worker_only_itself、project_two_task_tiles、project_does_not_mix_terminals、ordinary_terminal_reachable |
| 候选真实联合入口 | PASS，candidate.json；输出完整、焦点/输入正确、凭据复用、隐藏/ended 输入拒绝、名称持久化均通过 |
| 五步截图 | candidate-01-project.png、02-task-A.png、03-worker.png、04-controller.png、05-ordinary-terminal.png；已查看项目截图，T-A/T-B 同屏两格 |
| 任务混项目终端变异 | NO_GO，mutant-task-includes-project-terminal.json，任务/单 worker 隔离检查失败 |
| 重复回放变异 | NO_GO，mutant-duplicate-replay.json，切换前/后编号唯一性与隐藏输出唯一性失败 |
| 隐藏输入放行变异 | NO_GO，mutant-inactive-input.json，inactive_input_rejected 失败 |
| 选择/布局/普通终端投影/焦点回调 | PASS，selection.json、layout-store.json、terminal-catalog.json、retained-focus.json |
| 原真实 T-107 与 T-133/T-107 | PASS，t107.json、t133-t107.json；普通终端投影造成的旧回归已解除 |
| T-091 修订合同 | PASS（仅指与起点同样失败），t091-baseline.json、t091-candidate.json：同一 handler 枚举错误、同一 checks。按用户“主控 #7”，不改原 oracle、不把它写成原测试绿态 |

旧红态、审查失败与测试工具故障全部保留：outside-cZpQfO1X/、outside-02-fXauAYx2/、outside-03-qCZMwEld/，
以及 REVIEW-01/02、T143-REVIEW-01/02、T143-SERIALIZATION-REVIEW-01、T143-FOCUS-REVIEW-01.md。
其中前者揭示并修复兄弟布局/项目布局集合问题；工具修复分别处理 CDP 返回循环对象和保留窗格聚焦竞态。
历史 timeout 缺逐项状态，不能完全归因焦点；后续 RUN-OUTSIDE-04 已真实通过切换及输入。

## T-143

已定保留项：默认关闭屏幕阅读器支持（可在本窗口设置手动开启）、切换保留最多四个未显示终端。
隐藏期间暂停读取；回来时追平输出并完成本次显示后聚焦；隐藏 key 不可输入，超限/关窗撤销凭据。
生产轮询仍为 100 ms。WebGL 从生产候选和当前测试实验中移除，package.json / package-lock.json 的相关变更已全部撤回，
两份依赖文件与起点一致；不改 node_modules。没有新依赖、输出推送并行路径或降级渲染分支。

| 项目 | 前 → 后数字 | 判定 |
| --- | --- | --- |
| 读屏关闭（RUN-OUTSIDE-04，T-139 控制版本单变量） | 切换中位数 99.45 → 89.30 ms（本次约缩短 10.2%）；滚动 60.005 → 60.003 FPS，p95 17.5 → 17.2 ms | 保留默认关闭及手动开关。FPS 无可辨别改善 |
| 保留连接（RUN-OUTSIDE-04，当前源码仅 retainedPaneLimit=0/4 不同） | 切换中位数 83.90 → 75.00 ms（本次约缩短 10.6%）；滚动 60.002 → 60.024 FPS，p95 17.1 → 17.5 ms | 保留；没有因此宣称滚动改善 |
| 100 → 16 ms 轮询（RUN-OUTSIDE-01） | 切换中位数 78.05 → 81.70 ms；旧滚动 121.37 → 121.25 FPS，p95 均 9.0 ms | 切换无改善，未保留；旧采帧方法首间隔有缺陷，FPS 不作收益依据。该轮切换完成条件也早于 v2，不与新数字混算 |
| WebGL（RUN-OUTSIDE-04） | 控制切换 99.45 ms；实验有 105.25 ms 部分采样，但 webgl2_renderer_active 失败，后续 isContextLost 调用遇 null，整体 INCOMPLETE | 配置未获有效启用证明，部分数字不构成 WebGL 对照；不推断有效 WebGL 的优劣，直接撤掉及依赖 |
| 起点 → 联合候选（RUN-OUTSIDE-04） | 切换中位数 108.40 → 75.00 ms；滚动 60.002 → 60.024 FPS，p95 17.6 → 17.5 ms | 本轮切换约缩短 30.8%，含视图和两个保留项的整体差异；不全归因任一项。滚动未证明改善 |

以上是单批探索对照，不证明长期可靠性或稳定收益。原始八次切换样本、三组各 120 帧间隔及版本/显示参数均在各 json 中。
所有当前配置约 60 FPS，p95 约 17 ms，被显示刷新率封顶，不能用于区分滚动性能。

新增测量 v3（工具 v5）：在同一真实主控 PTY 执行相同的 5000 行编号命令，计时起点在页面调用输入之前，
终点要求输入已确认、xterm onRender 覆盖最后一行 BENCH_04999、终端可见且恢复完成，再经过两次 rAF。
记录 `output_to_visible_ms` 和完成条件，随后仍核对全部 5000 行顺序/唯一性、输出偏移和真实输入。
它测的是输入→PTY→轮询/解码→最后一行绘制的端到端耗时，含传输和 Python 启动成本，不是纯滚动渲染耗时。
不使用平均 FPS 代替它，也不预设候选必须更快；无改善就报告“未证明改善”。基线/候选数字目前均待 RUN-OUTSIDE-05。

| 新测量检查 | 证据与局限 |
| --- | --- |
| 原报告缺新指标 | output-metric-contract-red-01.json，基线/候选均无 output_to_visible_ms；不把旧 PASS 当成新测量通过 |
| 实际计时表达式的完成边界 | output-meter-boundaries-01.json，七项 PASS：缓冲区有文本但没渲染、仍隐藏、输入未确认/失败、无关行渲染均不能成功；有效可见渲染等绘制帧后才完成；监听器被清理 |
| 脚本语法 | 实际 JS 表达式 node --check、Python 编译、zsh -n RUN-OUTSIDE-05.sh 通过 |
| 撤依赖后的标准构建 | final-without-webgl-build-01.json PASS；临时构建目录已清理 |

隔离边界检查使用可控 DOM/xterm/input/rAF，未产生或冒充真实性能数据；真实新指标仍为 INCOMPLETE。
沙箱 Electron CDP 的 ECONNREFUSED 限制未变，按公共约定由主控运行：

```sh
zsh evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-05.sh
```

脚本写新的 outside-05 目录，先校验计时表达式，再跑单项候选。仅当候选 PASS 且新旧指标完整有效才继续：
同一夹具/同一命令的 ebbae7bd0 基线、三个变异、原指定回归及 T-091 起点比较。
不重跑已撤掉的 WebGL；各单变量试验的数字以 RUN-OUTSIDE-04 及前述旧轮询证据为准。
回传 PREFLIGHT.json、COMPARISON.json 后，worker 将补上新的基线/候选耗时与最终判定，不能提前宣称最终 PASS。

大块原始夹具路径保留在各 json，未入 Git，归档仍交主控按 T-088 处理；所有失败现场与截图保留。
无 push、合并、用户全局 CLI 配置改动。交付绑定 T-139-1 / T-143-1、attempt a1；真实夹具 session/fence 与代码版本见各 summary。
