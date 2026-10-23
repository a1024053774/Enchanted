# T-139 / T-143 同批验证（attempt a1）

状态：**INCOMPLETE**。RUN-OUTSIDE-01 已取得 T-139 真实入口红态、候选通过及两个变异的业务拒绝；
RUN-OUTSIDE-02 的 selection、layout-store、terminal-catalog、T-107、T-133/T-107 均通过，T-091 与起点同样失败。
但九项联合 Electron 运行全部在 CDP 返回对象时中止，没有性能数字。RUN-OUTSIDE-03 已产出滚动数字，但切换因焦点条件超时；候选焦点修复及 RUN-OUTSIDE-04 仍待真实验证，不能最终验收或集成。

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
准确复现旧投影违反该合同；catalog-shape-red-01.json 还检出了终端行缺少下属摘要的投影字段遗漏；catalog-green-02.json 通过对应检查。
当前源码的 T-107 投影检查 sidebar-projection-02.json 通过；RUN-OUTSIDE-02 的原真实 T-133/T-107 也为 PASS（outside-02-fXauAYx2/t133-t107.json）。

此前布局缺陷及修复记录保留：selection-red-03.json、layout-red-01.json、store-layout-red-02.json 逐步检出任务混终端、
单 agent 编辑覆盖兄弟布局、项目终端保存包含任务 agent；后续对应绿态均保留。独立检查报告 REVIEW-01.md 为 INCOMPLETE，
REVIEW-02.md 对旧候选为 FAIL；修复后的真实 store/原布局校验 store-layout-retention-01.json 有 10 项通过，不将旧审查改称通过。

## T-143

RUN-OUTSIDE-01 的同一夹具：两个真实 Claude CLI worker，模型请求 claude-haiku-5-5，使用本地脚本化 Messages 接口；
经角色申请批准的项目主控终端；真实 PTY 输出 5000 行编号，三次滚动、八次交替切换。
它证明 CLI/后台/界面调用及偏移、输出、焦点与输入合同，不证明供应商模型推理能力或长期性能。

| 项目 | 对照 → 单项实验（RUN-OUTSIDE-01） | 处置 |
| --- | --- | --- |
| screenReaderMode 关闭 | 切换中位数 78.05 → 64.30 ms；滚动 121.37 → 121.22 FPS，p95 9.0 → 8.9 ms | 观察到切换约 17.6% 缩短，候选默认关闭；设置可手动开启，作用于本窗口所有终端。RUN-OUTSIDE-04 在 T-139 控制版本再测 |
| 100 → 16 ms 轮询 | 切换中位数 78.05 → 81.70 ms；滚动 121.37 → 121.25 FPS，p95 均 9.0 ms | 无改善，不保留；生产仍用 100 ms，未增加输出推送路径 |
| WebGL | 未测。主控已安装 MIT 的 @xterm/addon-webgl 0.19.0，授权本 worker 提交 package.json/lock 改动 | 仅用于测试副本；模块导入与标准构建通过，未启用到生产终端。RUN-OUTSIDE-04 与同一 T-139 控制版本只差 WebGL；不改善则移除依赖 |
| 切换保留连接 | 未测。当前加入候选，未宣布保留 | RUN-OUTSIDE-04 对比当前代码 retainedPaneLimit=0 与 =4，其他代码/读屏设置相同；不改善则撤掉 |

旧 FPS 采样的首个时间差来自 performance.now() 到首个 rAF，原始数据中出现负值，不能据此声称超过屏幕刷新率或滚动改善。
原始数据未改写。测量版本 2 先用首个 rAF 建立基点，再采 120 个正帧间隔；RUN-OUTSIDE-04 所有对照、实验与候选均用它，
并重新运行 ebbae7bd0 与 T-139 控制版本。切换计时现在还要求目标窗格 input_enabled=true 才算完成。

保留窗格的待测实现：每个窗口最多保留四个未显示终端，保留 xterm、UTF-8 解码器与字节偏移；隐藏期间暂停轮询，
恢复时立即唤醒并追平输出后显示和聚焦。主进程把保留集与当前选择分开，隐藏 key 仅可读，输入/缩放等写命令拒绝；
身份变为历史或只读时旧绑定不复用；超出上限撤销凭据并销毁 renderer，后台完整输出仍可回放；关窗撤销两集合的凭据。

| 本地当前候选检查 | 证据 |
| --- | --- |
| 缺少连接复用的红态 | retention-red-01.json，切回得到不同 pane key |
| 选择与权限检查 | retention-boundaries-01.json，25 项：复用绑定/输入凭据、隐藏快照绑定原任务且不可输入、跨窗口拒绝读取保留 key、上限前/上限处保留、超限淘汰并撤销凭据、关窗撤销全部凭据等 |
| 真实 SQLite / 后台原布局校验 | store-layout-retention-01.json，10 项通过 |
| 普通终端投影 | catalog-green-02.json，两项合同及行结构检查通过 |
| 构建 | t143-build-candidate-01.json、t143-build-webgl-control-01.json 均通过，临时构建目录已清理；不代表 GPU 实际渲染已验证 |
| 测试脚本语法 | Python py_compile、zsh -n RUN-OUTSIDE-02.sh 通过 |

新 e2e 在原联合夹具中额外核对：真实 xterm 对象与输入凭据在切换后相同、隐藏窗格不能输入、设置可手动开读屏、
WebGL2 canvas 确实启用且未报告 context loss。增加 inactive-input 变异，不能用只读快照代替输入拒绝。
retention-harness-failure-01.txt 保留了关闭窗口检查初次遇到的测试边界缺方法错误；它不是业务红态。

独立只读审查 T143-REVIEW-01.md 对冻结候选 8faf2a646 为 INCOMPLETE：检出读屏开关选择器指向标题、无法匹配复选框。已改为选择整个设置 section 下的 input；原报告保留。另补上保留集上限边界检查，并把 WebGL context loss 计数保存在窗口上，避免切换销毁节点后遗漏已发生的丢失。独立有界复核 T143-REVIEW-02.md 确认选择器唯一匹配 checkbox，25 项 selection 再跑通过，P1 已解除。真实 Electron/GPU 检查仍待 RUN-OUTSIDE-04。

## 测试工具修正（主控 #10）

RUN-OUTSIDE-02 的 70 个小文件/截图保留在 outside-02-fXauAYx2/。九项联合运行均为 INCOMPLETE，
共同错误为 `Object reference chain is too long`，指标为空；这不能用于判定 WebGL 或保留窗格的性能。
定位到 `window.__initialShellTerminal = mount.__testTerminal`：赋值表达式返回整个 xterm 对象，
CDP 的 returnByValue 会尝试序列化其循环/深引用。修正为 `void (...)`，只在页面保留引用而不返回对象。
滚动采样显式 JSON.stringify 数字/帧间隔数组，Python 再 json.loads。测量方法仍为 v2，另记 harness_version=3。

隔离 CDP 序列化检查为 PASS：serialization-inspector-01.json。CHECK-CDP-SERIALIZATION.mjs 读取实际 e2e 的捕获表达式，
通过 Node V8 inspector 的 Runtime.evaluate 复现旧表达式对循环对象报同错，新表达式返回 undefined 且保留引用身份。
这只证明序列化边界，不是 Electron/GPU 或性能指标。
独立只读审查 T143-SERIALIZATION-REVIEW-01.md 为 INCOMPLETE：复核上述边界、实际滚动 JS 语法与空指标停止哨兵均通过；真实指标仍缺失。

修正后尝试单项真实命令：

```sh
python3 workbench/tests/test_t139_t143_views_perf_e2e.py --summary evidence/2026-10-23-batch23/T-139-T-143/serialization-selftest-01.json
```

结果 INCOMPLETE：沙箱内 Electron CDP 连接 ECONNREFUSED（127.0.0.1:59328），未取得指标，现场保留在 summary 的 fixture 路径。
按公共约定不申请越权；RUN-OUTSIDE-03 先只跑一次候选，核对 PASS、harness_version=3、三项有效正数指标、
3×120 正帧间隔与 8 次切换，再写 PREFLIGHT.json。该单项未满足时立即停止，不批量重跑；
通过后复用这份候选结果继续对照/变异/回归。真实非空指标自测尚待主控沙箱外执行。

## 保留窗格焦点修复（主控 #11）

outside-03-qCZMwEld/ 完整保留。候选滚动中位数为 59.998980 FPS、p95 17.600000 ms；切换中位数缺失，
单项为 INCOMPLETE，前置检查正确停止批量。没有基线对照，不能据此评价优化收益。

已查看 candidate-failure.png：第一轮目标 T-A 已显示完整终端，未显示“只读”或“正在恢复”，
但窗格没有“正在输入”焦点标记。实际 renderer 的 data-input-enabled、data-restoring 与测试选择器相符。
原始 Electron 日志另有一条 a2a:output 的 Task view is changing，不能单凭该条认定为超时原因（关闭阶段也会拒绝输出）。

代码中发现保留窗格重新激活时的焦点竞态：旧显示周期留下 restoring=false；active 变化时 layout effect 先请求隐藏回放，
同次提交的焦点 effect 仍可读到旧 false 并把 focusRequest 标为已服务。隐藏/重新显示后，它不再执行聚焦。
这是可复现的候选焦点处理缺陷；但旧报告缺逐项条件，不能完整证明历史 timeout 就由它触发。已把聚焦条件绑定到本次 visibility version 完成回放，且只有 document.activeElement
确实成为 terminal.textarea 才记录请求已服务。未放宽目标可见、可输入、恢复完成、textarea 聚焦这四项条件，也未延长 12 秒期限。

新隔离检查 test_t143_retained_focus.mjs 执行实际 focus effect 回调：
旧版本 6c44695ff 在 activation_does_not_consume_focus_before_its_replay 失败（retained-focus-red-02.json）；
修正后四项通过（retained-focus-green-01.json），包括恢复后聚焦和后续快照不抢回用户焦点。
该检查提供回调边界证据，未证明真实 React 调度或 Electron 焦点；真正超时是否解除必须由 RUN-OUTSIDE-04 再证。
标准构建 focus-build-01.json 通过，临时构建目录已清理；25 项选择/权限检查 retention-after-focus-01.json 通过。
独立只读审查 T143-FOCUS-REVIEW-01.md 为 INCOMPLETE：新跑父版本红态/候选绿态、1/37/126 请求边界、实际切换 JS 语法及缺指标停止门禁均通过；保留真实焦点/历史超时归因的局限。

联合 e2e 现在保存已完成的切换样本；若超时，记录目标是否存在/可见、输入标记、恢复标记、焦点与告警字符串，
不返回 DOM 对象。测量方法仍 v2，harness_version=4。RUN-OUTSIDE-04 仍先跑单项候选，指标完整且通过后才继续其余批次。
沙箱运行 Electron 的限制未变，本轮没有重复运行已知会 ECONNREFUSED 的本地真实夹具。

下一步：主控在沙箱外运行，回传新目录、PREFLIGHT.json 与 COMPARISON.json。

```sh
zsh evidence/2026-10-23-batch23/T-139-T-143/RUN-OUTSIDE-04.sh
```

脚本逐项跑新基线、T-139 控制、读屏关闭、WebGL、无保留/有保留候选，三个变异和指定回归。
worker 读取数字后决定 WebGL 与保留窗格的最终处置，再更新本报告；本次是供测量的候选，不是最终 PASS。
新依赖来自主控“主控 #7”的明确授权；没有改 node_modules，没有写用户全局 CLI 配置，没有 push 或合并。

原始临时夹具继续保留：RUN-OUTSIDE-01 的各 summary 中有 fixture 路径，本地新 SQLite 夹具也在各 summary 中记录。
大块原始目录未入 Git，归档交主控按 T-088 处理。最初 Electron 无 CDP 的 baseline-01/02.json 等探索失败全部保留。
