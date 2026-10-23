# T-139 / T-143 同批验证（attempt a1）

状态：**INCOMPLETE**。RUN-OUTSIDE-01 已取得 T-139 真实入口红态、候选通过及两个变异的业务拒绝；
后续 T-143 候选和普通终端投影修复必须由 RUN-OUTSIDE-02 再次联合验证。WebGL 与保留窗格尚未取得性能数字，不能最终验收或集成。

## T-139

项目视图每个任务一格；任务视图只含该任务 agent；单 agent 只显示自己。项目普通终端有单独入口。
单 agent 重命名和关闭保留兄弟的树与名称；项目终端保存只包含 task=null 的终端。
项目行菜单、三份受保护 oracle、地图与 ticket 未改。

第一批沙箱外结果在 `outside-cZpQfO1X/`（主控运行 RUN-OUTSIDE-01，代码为 feea09ebc）：

| 检查 | 结果与证据 |
| --- | --- |
| 修前 ebbae7bd0 | NO_GO，baseline.json 的五项业务失败：任务混项目终端、worker 混其他窗格、项目无两格任务、项目混终端、普通终端不可达 |
| T-139 候选 | PASS，t139-candidate.json；项目、任务、worker、主控、普通终端五步 PNG 同目录。已查看项目截图，两任务同屏两格 |
| 任务重新混入项目终端变异 | NO_GO，mutant-task-includes-project-terminal.json，task_A_only_its_agents、worker_only_itself 失败 |
| 重复回放变异 | NO_GO，mutant-duplicate-replay.json，编号输出切换前/后以及隐藏输出的唯一性检查失败 |
| selection、真实 store/原布局校验 | PASS，selection.json、layout-store.json |
| T-107 | PASS，t107.json |
| T-133/T-107 | INCOMPLETE，t133-t107.json，在“身份已放弃”处超时；原投影会把放弃角色的终端继续放进 agents，足以导致此等待不满足。已修复，待原 oracle 重跑 |
| T-091 | INCOMPLETE，t091.json，旧 IPC handler 枚举失败。用户消息“主控 #7”已把验收改为与起点同样失败、不更差；未修改 oracle。RUN-OUTSIDE-02 用同一 oracle 比较修前和候选 |

投影修复将未认领/已放弃角色的普通终端放到 `sidebar_snapshot.terminals`，经批准的角色继续进入 agents；
侧栏单独显示普通终端。因此放弃角色后它从 agents 消失，普通终端入口仍在。真实 SQLite 的 catalog-red-01.json
准确复现旧投影违反该合同；catalog-shape-red-01.json 还检出了终端行缺少下属摘要的夹具遗漏；catalog-green-02.json 通过对应检查。
当前源码的 T-107 投影检查 sidebar-projection-02.json 通过，原真实 T-133/T-107 必须再跑。

此前布局缺陷及修复记录保留：selection-red-03.json、layout-red-01.json、store-layout-red-02.json 逐步检出任务混终端、
单 agent 编辑覆盖兄弟布局、项目终端保存包含任务 agent；后续对应绿态均保留。独立检查报告 REVIEW-01.md 为 INCOMPLETE，
REVIEW-02.md 对旧候选为 FAIL；修复后的真实 store/原布局校验 store-layout-retention-01.json 有 10 项通过，不将旧审查改称通过。

## T-143

RUN-OUTSIDE-01 的同一夹具：两个真实 Claude CLI worker，模型请求 claude-haiku-5-5，使用本地脚本化 Messages 接口；
经角色申请批准的项目主控终端；真实 PTY 输出 5000 行编号，三次滚动、八次交替切换。
它证明 CLI/后台/界面调用及偏移、输出、焦点与输入合同，不证明供应商模型推理能力或长期性能。

| 项目 | 对照 → 单项实验（RUN-OUTSIDE-01） | 处置 |
| --- | --- | --- |
| screenReaderMode 关闭 | 切换中位数 78.05 → 64.30 ms；滚动 121.37 → 121.22 FPS，p95 9.0 → 8.9 ms | 观察到切换约 17.6% 缩短，候选默认关闭；设置可手动开启，作用于本窗口所有终端。RUN-OUTSIDE-02 在 T-139 控制版本再测 |
| 100 → 16 ms 轮询 | 切换中位数 78.05 → 81.70 ms；滚动 121.37 → 121.25 FPS，p95 均 9.0 ms | 无改善，不保留；生产仍用 100 ms，未增加输出推送路径 |
| WebGL | 未测。主控已安装 MIT 的 @xterm/addon-webgl 0.19.0，授权本 worker 提交 package.json/lock 改动 | 仅用于测试副本；模块导入与标准构建通过，未启用到生产终端。RUN-OUTSIDE-02 与同一 T-139 控制版本只差 WebGL；不改善则移除依赖 |
| 切换保留连接 | 未测。当前加入候选，未宣布保留 | RUN-OUTSIDE-02 对比当前代码 retainedPaneLimit=0 与 =4，其他代码/读屏设置相同；不改善则撤掉 |

旧 FPS 采样的首个时间差来自 performance.now() 到首个 rAF，原始数据中出现负值，不能据此声称超过屏幕刷新率或滚动改善。
原始数据未改写。测量版本 2 先用首个 rAF 建立基点，再采 120 个正帧间隔；RUN-OUTSIDE-02 所有对照、实验与候选均用它，
并重新运行 ebbae7bd0 与 T-139 控制版本。切换计时现在还要求目标窗格 input_enabled=true 才算完成。

保留窗格的待测实现：每个窗口最多保留四个未显示终端，保留 xterm、UTF-8 解码器与字节偏移；隐藏期间暂停轮询，
恢复时立即唤醒并追平输出后显示和聚焦。主进程把保留集与当前选择分开，隐藏 key 仅可读，输入/缩放等写命令拒绝；
身份变为历史或只读时旧绑定不复用；超出上限撤销凭据并销毁 renderer，后台完整输出仍可回放；关窗撤销两集合的凭据。

| 本地当前候选检查 | 证据 |
| --- | --- |
| 缺少连接复用的红态 | retention-red-01.json，切回得到不同 pane key |
| 选择与权限检查 | retention-green-03.json，16 项：复用绑定/输入凭据、隐藏快照绑定原任务且不可输入、跨窗口拒绝读取保留 key、关窗撤销全部凭据等 |
| 真实 SQLite / 后台原布局校验 | store-layout-retention-01.json，10 项通过 |
| 普通终端投影 | catalog-green-02.json，两项合同及行结构检查通过 |
| 构建 | t143-build-candidate-01.json、t143-build-webgl-control-01.json 均通过，临时构建目录已清理；不代表 GPU 实际渲染已验证 |
| 测试脚本语法 | Python py_compile、zsh -n RUN-OUTSIDE-02.sh 通过 |

新 e2e 在原联合夹具中额外核对：真实 xterm 对象与输入凭据在切换后相同、隐藏窗格不能输入、设置可手动开读屏、
WebGL2 canvas 确实启用且未报告 context loss。增加 inactive-input 变异，不能用只读快照代替输入拒绝。
retention-harness-failure-01.txt 保留了关闭窗口检查初次遇到的测试边界缺方法错误；它不是业务红态。

下一步：主控在沙箱外运行，回传新目录与 COMPARISON.json。

```sh
zsh evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-02.sh
```

脚本逐项跑新基线、T-139 控制、读屏关闭、WebGL、无保留/有保留候选，三个变异和指定回归。
worker 读取数字后决定 WebGL 与保留窗格的最终处置，再更新本报告；本次是供测量的候选，不是最终 PASS。
新依赖来自主控“主控 #7”的明确授权；没有改 node_modules，没有写用户全局 CLI 配置，没有 push 或合并。

原始临时夹具继续保留：RUN-OUTSIDE-01 的各 summary 中有 fixture 路径，本地新 SQLite 夹具也在各 summary 中记录。
大块原始目录未入 Git，归档交主控按 T-088 处理。最初 Electron 无 CDP 的 baseline-01/02.json 等探索失败全部保留。
