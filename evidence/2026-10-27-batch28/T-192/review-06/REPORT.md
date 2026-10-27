T-192 独立审查第 6 轮（只读）

**STATUS: PASS（本轮指定复核范围）**

TARGET：`/private/tmp/t192-review6/change.diff`，基于仓库 HEAD `c76e2ab2a7dfd5fe0692ff9f1150ef586354a4d0` 的候选。开始与结束均逐字核对补丁涉及的 14 个文件：受控文件比较实际 diff 正文，两个新增文件比较全文；全部一致。比较只忽略 Git `index` 元数据行，没有计算摘要或指纹。源码位置以下均相对于 `/Users/luckye/Documents/Code/a2a`。

验收依据为 BRIEF、T-192、T-189；前五轮报告用于选择反例，现有检查不作为唯一预期来源。本轮核对 S1、编号与无 attempt 步骤，抽查旧修复；不修改实现、任务、地图或测试原件，不 checkout、切分支，不操作 `/private/tmp/t190` 的后台或应用。所有运行产物只写入本审查目录。

EVIDENCE：

1. **S1 两条路径已修复，组件输出通过。**

重放生产 `A2AGates.call()` → `verifyCandidate()` → `writeConflict()` → `save/event()` → `task_history`，数据库为内存 SQLite。沿用第 5 轮脚本，隔离运行目录改为本目录；Git、worker 创建、清理和操作锁等外部边界仍使用受控替代。另转换执行当前 `TaskRecord.tsx`，调用真实 React 与 `react-dom/server` 生成组件树和 HTML；仅替代 hooks 的加载状态及 effect 宿主，实际使用生产 `attemptStarts()`。

预期独立于实现：事件从 A 切到 B 再回到 A 时，返回步骤前必须重新标 A；A 始终编号 1，B 始终编号 2。

| 输入/状态 | 生产事件及实际组件输出 | 结果 |
| --- | --- | --- |
| A 验收冲突，旧 worker 已结束，替换成功 | B 的认领、启动之后，`core.ts:1729` 显式写入属于 A 的 `conflict_worker_replaced`。组件在该步前显示“第 1 次执行尝试 · original”，随后显示“合并冲突后更换 worker · 新执行尝试 replacem” | PASS |
| 替换已建立 B，随后因 `run_blocked` 失败 | `core.ts:1747` 的 `conflict_rework_unknown` 和 `:1748` 随后的问题上报均归 A。unknown 本身不投影为独立可见步骤；“上报问题 · worktree：run_blocked”前重新显示 A 的第 1 次标题 | PASS |
| 替换在建立 B 前因 `path_overlap` 失败 | 没有凭空出现 B；问题仍显示在 A 下，只有第 1 次标题 | PASS |

上述三种情况均分别检查整页与底部记录组件。前两种标题顺序为 **A=1 → B=2 → A=1**；没有第 3 次执行尝试，没有丢失可见步骤。原 verify 的重复 `merge_conflict` 拒绝仍正确折叠，未落到 B 下。

关键代码为 `workbench/src/gates/taskHistory.ts:108`、`workbench/app/TaskRecord.tsx:30`、`:31`、`:74`、`:76`。编号继续按首次出现生成；`attemptStarts` 只决定哪里重新展示标题。

2. **无 attempt 步骤的位置与编号通过局部检查。**

使用额外哨兵序列检查创建任务、认领前无 attempt 的拒绝、执行步骤之间无 attempt 的拒绝和末尾关闭。组件保持输入时间顺序：创建与认领前拒绝在第一个执行标题之前；中间无 attempt 步骤不生成执行标题、不占编号，也不使同一个 attempt 被重复编号；末尾关闭仍在末尾。返回旧 attempt 时仍重新标明其原编号。

无 attempt 步骤沿用上方的时间线区段，没有被改写成有 attempt 的事件。依据本轮“无 attempt 步骤不拆分所在 attempt”的约定，未发现确定的位置错误。这组是投影/组件哨兵输入，不声称整组事件是一次真实合法门禁旅程。

3. **旧问题抽查未发现回退。**

| 已修项 | 本轮实际检查与结果 |
| --- | --- |
| F1：closed 被重新打开 | 内存库经生产 call 对 closed 分别执行 revoke、revise、claim、dispatch，均拒 `task_closed`，任务保持 closed；对应 `core.ts:1565`、`:3948`。未测锁竞争。 |
| F3、R4、N1、Q1：verify 拒绝过滤与归属 | 重放同 attempt 冲突夹反馈/清理、替换成功/失败、打回后重复 verify；另检查不同错误、不同 attempt、新交付、新验收清除折叠资格。独有错误保留，重复拒绝仅折叠一次。A 冲突后 B 自身的早期 Git、路径、完成条件失败仍归 B。路径探针调用生产 checkPaths，未把自定义错误码当作真实错误。 |
| F4：红态、规则检查 | 当前映射与 history_check 的成功红态/失败规则输入通过；删除规则映射的变异被业务断言检出。未实际执行一整串外部检查命令。 |
| F5：历史审查、建议与报告 | 真实导出 T-2 夹具仍有两次审查、第一次的问题和建议、各次报告；组件树及 HTML 保留两份报告和建议，也显示集成提交。只保留最后一份审查的变异被检出。 |
| F2、R1～R3：零窗格与打开 worker | 源码核对：记录页轮询；零窗格不渲染旧静态门禁栏；按钮传具体 launch，经 selectAgent → select-agent → changeView({task,launch})，避开无显式 launch 的空布局恢复。firstAttempt/onAttemptStarted 机制未恢复，effect 不执行导航。此项未重跑完整 IPC 时序。 |
| N3：busy 按钮 | 实际组件 busy=true 时 disabled=true；false 时恢复，点击调用当前回调一次；底部记录没有此按钮。不是原生 UI 忙碌场景复验。 |
| F6、N2、R5：文案 | `docs/index.html:55` 按“是否打开窗格”区分整页/底部记录，并说明打开 worker；`workbench/README.md:1092` 仍限定同次、同码、一次性折叠及原验收 attempt 归属。与已查分支一致。 |
| N4：补充证据完整性 | 副本中十份 green4 JSON 全部可解析；verify 明确失败为 oracle_failed，撤销、回收回执成功，回收后 history 为 ready/current_attempt=null，末 11 步包含交付、检查、打回、上报、撤销与回收。旧 green2/green3 两份截断回执仍解析失败，保留原样，不用于证明通过。本轮未查看截图或重跑真实旅程。 |

本轮沿用 Ubiquitous language：任务、执行尝试、验收、会话、窗格分别指不同对象。按 Deep modules 检查，新增标题辅助函数只计算展示边界，未引入第二套状态或可变门禁。既有 green4 作为 Tracer bullet 仅覆盖交付、验收打回、撤销、回收的一条切片，不替代真实审查与集成全流程。

FINDINGS：

**已查范围内没有确定的新问题。第 5 轮 S1 的成功与失败两条路径均通过。**

COUNTEREXAMPLE：

环境 Node `v26.5.0`。先将 `evidence/2026-10-27-batch28/T-192/` 完整复制为本目录 `copy/`，再运行会写结果的检查，仓库原证据未改动。

| 命令（工作目录见下） | 实际退出码与结果 |
| --- | --- |
| `node history_check.ts` | 0；PASS，failures=[] |
| `bash mutants.sh` | 包装脚本 0；11 个内部 node 均退出 1，JSON 均为 FAIL 且包含业务断言失败，不是导入/启动错误 |
| `node core-path-final-review6.mjs` | 0；生产控制流局部重放 PASS |
| `node own-verification-real-path-review6.mjs` | 0；B 自身完成条件/路径失败 PASS |
| `node entry-review6.mjs` | 0；closed 四个入口及重复 verify PASS |
| `node fold-review6.mjs` | 0；独立折叠反例 PASS |
| `node render-review6.mjs` | 0；组件标题、编号、无 attempt、按钮、历史报告 PASS |
| `node render-review6.mjs --mutant` | 1；恢复组件旧的“只在首次出现时标题”规则后，两条 S1 路径在整页/底部模式均因标题业务断言失败；stderr 为空 |

11 个已有变异分别为 integration-c、no-quiet、no-reclaim、last-review-only、drop-all-verify、any-previous-failure、feedback-breaks-fold、fold-not-consumed、row-attempt、first-appearance-header、no-rule-check。`first-appearance-header` 只在“A→B→A 每次切换都要标题”的断言失败；这证明新增断言能拒绝第 5 轮的坏规则。组件级反事实进一步证明当前调用方确实展示了重新出现的标题。

可重放命令：

```sh
cd /private/tmp/t192-review6/copy
node history_check.ts
bash mutants.sh

cd /private/tmp/t192-review6
node core-path-final-review6.mjs
node own-verification-real-path-review6.mjs
node entry-review6.mjs
node fold-review6.mjs
node render-review6.mjs
node render-review6.mjs --mutant
python3 candidate-check.py
```

本轮 stdout/stderr 分别保存在同名 JSON/stderr 文件，变异日志为 `mutants-review6.txt`；11 个变异 JSON 位于 `copy/`。组件 HTML 为 `render-review6.html`，坏规则输出为 `render-mutant-review6.html`。汇总在 `checks-summary.json`。重放时另选输出文件名，保留已有结果。

LIMITATIONS：

- 本轮证据为源码、内存库中的生产控制流及组件输出。没有启动 Electron、浏览器或后台，没有验证 CSS 实际布局、滚动、读屏及真实 IPC/轮询乱序。
- 未重新构建，未派发真实 worker/reviewer，未运行真实 Git 冲突、反馈送达、进程回收、并发关闭或崩溃恢复。局部替代边界不作为这些能力的通过证据。
- 未操作用户 a2a+T-138。真实审查、打分、集成的整条任务页旅程没有在本轮重跑；既有报告/提交展示检查使用真实导出事件夹具。本文 PASS 限于 BRIEF 指定复核，不宣称 T-192 全部端到端验收或生产发布通过。
- project-map status 在开始、结束均退出 0，Problems(0)、Stale living docs(0)；没有改票或关闭验收框。

RULE：同类“投影归属正确但组件标题错误”已有独立反事实覆盖：history_check 的 A→B→A 断言拒绝坏 helper，本轮组件探针拒绝旧调用方规则。未修改仓库规则或测试。

**结论：可合并。**
