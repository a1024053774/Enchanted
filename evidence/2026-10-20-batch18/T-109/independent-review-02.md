# T-109 第二轮独立审查

状态：**PASS**。第一轮 F1 已修好：同一个“按任务标题猜父项”错误分支，现在被正式层级合同的业务断言拒绝。未确认本轮范围内的新产品缺陷或结构缺陷。

本结论只审查冻结候选的父 launch 记录与侧栏竖向缩进列表，不代表提交、集成、切换工作台或 T-108／T-110／T-111 验收。真实 Electron 证据采用执行主控提供的本候选原件；本 reviewer 没有亲自重跑 GUI，不把待运行脚本称为已通过。

- 日期：2026-10-20；任务 T-109，交付 attempt a1。
- 候选：`a13908c04dd5f3a73c456cb173caefab0d5ef3f6`；起点：`6411bdff8482ba47da207efa6a295a12666222aa`；第一轮审查候选：`0034e35ada8242c857156794c1f4996c44b9225c`。
- 作者尾注绑定：session `05933b4f-66d7-4f57-a916-a02584790934`，launch `launch-c756fd73ed4547a2971081b4dda29a41`。未收到本 reviewer 的门禁 session／fence，不虚构；按派发方式只交报告，不 submit。
- 独立性：新开的只读会话，按指定顺序读角色卡、AGENTS、T-109、T-107 进展与交付记录；用 `git show`、`git diff` 核对候选及差异，没有读取作者会话历史。
- 授权范围按用户逐字要求：“我们做缩进列表,然后在侧栏的话,竖着展示,然后这个横着的流程视图做一个单独的展示页面,展示现在系统流程.” 横向流程页不在本轮；截图不是验收必需。
- 写入仅为自己新建的 `/tmp` 现场、本报告和 `REVIEW-OUTSIDE-02.sh`。没有改候选、主仓库 Git 元数据、地图、票据、全局配置；没有提交产品、checkout、reset、stash、push、调用模型、开子 agent、申请升级或使用问题面板。测试自身的 Git 提交／分支操作仅发生在它们新建的隔离夹具中。既有未跟踪原件与参考图保留。

## 验收依据与 F1 关闭证据

依据任务卡和 T-107 的既有约束，答案预先确定为：父关系只能来自保存的事实；无父项、缺失父项与冲突关系不能猜；启动历史不可改；折叠汇总包含全部后代，等待用户回答优先，缺少可信状态保持未知；键盘能够聚焦折叠按钮并用 Enter 展开；侧栏不得写入表、schema、trace；原门禁和 IPC 拒绝边界保留。

F1 的修复只改变三份正式验收文件，产品算法和键盘驱动相对第一轮候选没有变化。

1. `workbench/tests/test_t109_hierarchy.mjs:20` 新建真实 SQLite tasks 表，`49` 行起读取已保存任务，替代原先恒空的 listTasks。`83` 行起仅改变 title，使用“执行主控派发的 worker”等诱导标题；`89` 行直接要求旧 worker 的 parent 为 null，随后核对缺失父项、所有父关系与完整后代汇总。除 title 外的所有持久化值仍受约束，每次读取仍执行原全表/schema/trace 零写入比较。
2. `workbench/tests/run_t109_hierarchy.py:122` 通过真实 create CLI 保存诱导标题；`189` 行核实 IPC 读到了该标题；`190` 行起只改变隔离数据库中的 title，再要求真实 sidebar IPC 返回新标题，父关系与汇总不变。`183` 行旧记录／缺失父项断言、`214` 行零写入、折叠、Enter、聚焦及窄窗检查均保留。
3. `workbench/tests/test_t109_counterfactuals.py:65` 永久加入第一轮同一个标题推断变异，并要求它失败于 `Task titles must not supply parent launch facts for legacy sessions`。本轮未重新执行整个 counterfactuals 包装器；亲自重建了相同变异，直接运行正式合同验证。

本轮顺序为：候选正式合同 **rc 0 / PASS**；再给一次性副本 `sidebar.ts:103` 后加入第一轮原错误分支，其余生产代码不变，正式合同 **rc 1**，实际 `exec`、预期 null，明确失败于上述断言。独立给定另一组身份、任务号和保存标题的 oracle 也拒绝该分支。不是依赖缺失、空集合、设置失败或语法错误。

差异核对显示本次没有删除原父项、跨项目、错角色、自指、循环、冲突、普通回复不改归属、并发上下文隔离或 IPC 拒绝检查。标题变更后的新快照用于零写入基线，范围只覆盖夹具主动改变 title 的操作，没有把产品读取造成的变动排除掉。

## 必审项结论

| 项目 | 结论与依据 |
| --- | --- |
| 0. F1 | PASS。正式验收含已保存任务标题诱饵；原变异在业务断言上失败；既有检查保留。见上节与本轮 `mutant-title-formal.json`。 |
| 1. 父 launch 追加、入口和门禁 | PASS。Python 启动／派发只给新记录加字段，各启动阶段校验父字段不变。Panes／Store 保持 INSERT，launch_records 的禁止 UPDATE／DELETE 触发器没有变化。构思主控 → 执行主控由 controller_prepare 参数或 controller_start manifest 保存（`panes.ts:182,254`）；worker／reviewer 共用 createPane 的父字段（`535` 行）。认证后的 relay 请求使用真实调用者 launch 绑定 AsyncLocalStorage；operator 元数据在进入原门禁前摘除（`daemon.ts:441,475`）。本轮真实 Python 命令检查通过，主控真实 CLI／PTY 原件还证明旧两条启动记录原字符串不变。门禁 core 和 relay 相对起点没有变化；未重跑整套门禁恢复验收。 |
| 2. 保存事实、未归属 | PASS。`sidebar.ts:103–130` 只合并父字段与可关联的成功 assign，冲突则未归属；同项目／合法角色与循环检查后才计算后代。无父字段、缺失父项、跨项目、错角色、自指和循环均不猜、不回填。正式合同和独立输入通过；普通后续回复不改父项。 |
| 3. 折叠汇总、状态 | PASS（本票汇总／展示范围）。独立给定输入核对构思主控四个后代、执行主控三个后代及空闲 1／未知 2；未知没有被改成空闲。aggregate 对等待用户回答给予最高优先级。renderer `500–506` 行将后代状态用于折叠父项，style.css `151` 行提供边框／背景／文字高亮；主控真实 Electron 原件核对了四个子会话和含孙代的五个后代汇总。真实提问信号仍缺失，不能把逻辑和样式检查说成已验证真实等待问题高亮；该联动属于 T-108。 |
| 4. 键盘与三次驱动修复 | PASS，采用本候选真实 Enter／Tab 原件。产品是原生 button，保留 aria-expanded、aria-controls 和 focus-visible。驱动修复只激活测试自己的应用／窗口，核对 DOM、document、窗口、webContents、目标 launch、非负 tabIndex，再发 Enter down → CR char → Enter up；没有改按钮、强设 tabIndex、用 click 冒充 Enter、增加重试或取消展开断言。前两次焦点失败原件仍保留。候选自己的驱动合同通过；outside-tab-04 的私有驱动先以真实 Tab 到达按钮，再沿 Enter 路径展开。原驱动的 DOM focus 本身不证明 Tab 可达，因此单独采用该 Tab 证据。 |
| 5. T-107 F2／F3 | PASS。本轮实际 daemon/socket/Panes/SQLite/trace 检查连续读取后核对三个数据库（locks/t.sqlite3、membership.sqlite3、state.sqlite3）、sqlite_master、每张表和 trace 原值，结果不变，清理完成。独立 oracle 和正式层级合同也比较全部持久化值，未删掉零写入断言。主控本候选真实 Electron sidebar IPC 原件同样通过。 |
| 6. IPC 合同与攻击面 | PASS。main/preload 产品文件相对起点没有改变。合同只增加父关系和后代汇总穿透断言；原 20 个 handler／21 个 bridge 名称、未知 key、外来窗口／frame、历史只读、错误凭据与越界目标拒绝保留，并由本轮 IPC 合同通过。新 CLI 父字段只作为元数据，未进入权限、锁、fence、CAS 或 attempt 判断；未新增 renderer 可调用的命令。 |
| 7. design-integrity-review | PASS，无确认结构缺陷。按技能的验收表面路由执行 behavioral-acceptance-review，并核对产品差异的结构风险。没有新增产品异常吞噬、重试、fallback、兼容入口或平行门禁；null 是关系未知的显式领域值。Tracer bullet 沿既有启动记录 → 只读投影 → 侧栏贯通；Deep modules 沿用 Panes／Store，没有新增浅包装；Ubiquitous language 使用“父 launch”。 |

## 本轮亲自运行的检查与变异

主要现场：`/private/tmp/t109-review02-had30whx`。Node `v26.5.0`，Python `3.9.6`，真实模型回合 **0**。

副本通过 `git archive` 从冻结候选提取；依赖复制为普通目录，没有建 worktree 或指向其他目录的符号链接。归档自带的 hook 相对链接只解析到副本内部。私有 Git refs/index 位于新建目录；只读对象 alternate 用于读取完整历史，主仓库对象库不写入。另一个历史变异副本使用本地 fetch，只写其私有 Git 元数据。

| 检查／错误实现 | 实际结果与摘要 |
| --- | --- |
| 冻结候选地图及 living docs | rc 0，0 问题、0 stale；`map-status.stdout`。提取全部地图链接目标和 covers 所需文件，并读取完整历史，未改 Verified 值。 |
| 独立事实 oracle | rc 0，`independent-good.json`；不同身份／任务号、真实保存标题、三级关系、未归属、汇总和零写入。 |
| 正式层级合同 | rc 0，`hierarchy-good.json`；含标题不变性、关系反例、并发父字段隔离。 |
| Python 启动／派发命令 | rc 0，`dispatch-good.json`；Herdr／Codex 为明确的进程夹具，不连接用户服务。 |
| 键盘驱动合同 | rc 0，`keyboard-good.json`；含应用激活、CR、焦点和负 tabIndex 反例；不冒充 GUI 证据。 |
| main/preload IPC 合同 | rc 0，`ipc-good.json`；原拒绝检查及原合同内部反例保留。 |
| T-107 原投影回归 | rc 0，`t107-projection-good.json`；12 组原检查通过。 |
| 实际 daemon 只读 | rc 0，`readonly-good-local.json`；三个数据库与 trace 原值不变，cleanup_complete=true；PTY 身份为受控输入。 |
| M1：任务标题含“执行主控”时给旧 worker 猜父项 | 正式合同 rc 1，`mutant-title-formal.json`，失败于 `Task titles must not supply parent launch facts for legacy sessions`；实际 exec、预期 null。独立 oracle 同样 rc 1，`mutant-title-independent.json`。 |
| M2：把 `parent?.project` 改为 `parent.project` | 独立 oracle rc 1，`mutant-missing.json`，失败于显式的“缺失父 launch 和旧会话不得导致读取崩溃”断言；包裹原因是读取 undefined.project，正是注入的业务违例。 |
| M3：派发 prepared 追加后改写旧 launches.jsonl 的父 launch | rc 1，`mutant-history.json`，失败于 `Dispatch must not rewrite launch history`。被测启动及三次派发进程均 rc 0；最终字节比较拒绝了历史篡改。 |

确切 argv、cwd 和退出码保存在 `review-outside-02.json`；每个命令的 stdout／stderr 单独保留。T-107 投影与实际 daemon 是同一候选副本上的追加检查，摘要分别为上表所列文件，不冒称已写入较早的总摘要。

主要复现命令（在上述 candidate 目录、清除继承 Git 路由并设置 LC_ALL=C 后）：

```sh
node workbench/tests/test_t109_hierarchy.mjs /tmp/t109-review02-good-new.json
node workbench/tests/test_t109_hierarchy.mjs /tmp/t109-review02-title-new.json \
  /private/tmp/t109-review02-had30whx/candidate/workbench/review02-mutant-title/sidebar.ts
node /private/tmp/t109-review02-had30whx/independent.mjs \
  /private/tmp/t109-review02-had30whx/candidate \
  /private/tmp/t109-review02-had30whx/candidate/workbench/review02-mutant-missing/sidebar.ts \
  /tmp/t109-review02-missing-new.json
python3 workbench/tests/test_t109_dispatch.py \
  --source /private/tmp/t109-review02-had30whx/mutant-history \
  --summary /tmp/t109-review02-history-new.json
```

三个变异只在一次性副本改变一个位置。输出路径须为新文件。它们的测试摘要把错误实现标作 INCOMPLETE 并退出 1；表中的拒绝 PASS 指本轮核对了预期的业务失败，不将错误实现称为通过。

两次准备失败也保留：`/private/tmp/t109-review02-763eo77n` 因 shallow 历史缺 Verified 提交而中止；`/private/tmp/t109-review02-0odsblly` 因 archive 未提取 acceptance/entry/a2a_gates.py，被地图误视为删除而中止。随后改为只读完整对象历史并补齐该受检文件，另建现场得到地图通过。这两次不计作候选失败或反事实红态，没有覆盖原摘要。

## 真实原件、待运行脚本与限制

已读取执行主控运行的 `outside-04.json` 和 `outside-tab-04.json`，并审查对应的 RUN-OUTSIDE-04／RUN-OUTSIDE-TAB-04 及正式 runner 原文：

- 两者状态 PASS，均有四组检查、title_invariance=PASS、cleanup_complete=true，模型回合 0。
- 正式原件 source_head／candidate_revision 均为本轮完整候选，source_changes=[]。
- Tab 原件 candidate／source_head 为同一候选；唯一差异是私有测试驱动增加 Tab 遍历，脚本另用 git diff 要求产品代码保持候选原文。candidate_revision=null 如实表示测试驱动不同，不能解读为干净候选整树；产品绑定仍成立。
- 四组真实检查包含 CLI 派发／PTY、旧记录字节不变、原版本忽略父字段的红态、三级缩进、未归属、标题不变性、折叠计数、键盘展开、聚焦、窄窗、sidebar IPC 零写入。

以上是执行主控的真实入口证据，不是本 reviewer 重新运行的 GUI 记录。结合本轮独立 oracle、正式合同的原变异拒绝、实际 daemon 只读检查，以及产品相对首轮未变，足以关闭 F1 并给出本范围审查 PASS。

新增 `REVIEW-OUTSIDE-02.sh` 已通过 zsh 与 Python 3.9 语法检查、UTF-8 检查。其完整沙箱外模式**尚未运行**：

```sh
zsh evidence/2026-10-20-batch18/T-109/REVIEW-OUTSIDE-02.sh
```

脚本固定本轮候选，重建 archive 副本，先跑好候选、再拒绝三个变异，并跑实际 daemon 只读。最后使用内置盘 Electron 43.4.1，给私有驱动增加有界真实 Tab 导航，保留正式全部 UI／标题／零写入断言；输出只写新的 `/tmp/t109-review02-*`。不截图、不调用模型、不动用户 Herdr、不对主仓库 .git 写操作。LOCAL_ONLY 模式将未运行 GUI 记为 INCOMPLETE，不能以脚本的可执行性代替已发生的真实验证。本轮 local-only 总摘要中的 daemon 未运行项已由上述单独追加检查完成；GUI 未重跑仍然成立。

收尾在原稀疏 checkout 的 status 仍有既有 8 条缺失链接、0 stale；其运行条件并非完整候选。冻结候选在本轮独立副本已取得 0 问题、0 stale，不借用另一个 main HEAD 的结论。

范围外既有发现照实交主控：Panes 的真实 worker 路径仍固定 Codex 0.162.1／xhigh，与当前 high 口径不一致；此前交付已披露，本候选未引入或修复。本轮没有启动真实 Codex，也没有把 C 接收器字段当作模型配置验收。不使用问题面板。

重复缺陷类 F1 的防回归检查已经落在正式层级合同的“保存标题变化不改变父事实”及 counterfactuals 原变异中；无需再增加一条不可执行的治理口号。执行主控仍须自行完成门禁、集成和票据处置，本报告不替代这些步骤。

T-109 REVIEW PASS
