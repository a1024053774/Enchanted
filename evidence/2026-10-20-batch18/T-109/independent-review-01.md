# T-109 第一轮独立审查

状态：**NO_GO，需修复验收缺口 F1**。未复现候选产品的归属、追加记录或只读缺陷；当前层级合同却放过了 ticket 明确禁止的“按标题猜父项”实现。不能据其绿态关闭本票。

- 审查日期：2026-10-20；任务 T-109，作者交付 attempt a1。
- 冻结候选：`0034e35ada8242c857156794c1f4996c44b9225c`；起点：`6411bdff8482ba47da207efa6a295a12666222aa`。
- 作者提交尾注：session `05933b4f-66d7-4f57-a916-a02584790934`，launch `launch-c756fd73ed4547a2971081b4dda29a41`。本次审查没有收到自身门禁 fence/session，不虚构该绑定；按派发指令只交报告，不 submit。
- 独立性：新会话，按指定顺序读角色卡、AGENTS、T-109、T-107 进展及三份交付记录；以 `git show`、`git diff` 核对原文，没有读取作者会话历史。
- 范围：仅父 launch 记录和侧栏竖向缩进列表。用户本轮逐字指令取代旧视觉假设；横向流程页属于 T-111。截图不是验收条件。
- 写入：仅新建的 `/tmp` 现场及本报告、`REVIEW-OUTSIDE-01.sh`。没有改候选、commit、checkout、reset、stash、push、调用模型、开子 agent、申请升级或使用问题面板。既有未跟踪的 `outside-03.json` 和参考图保留。

## 确认的发现

### F1 / P2：验收未拒绝从真实任务标题推断父项

位置：`workbench/tests/test_t109_hierarchy.mjs:41`。该合同把 `listTasks` 固定为空，旧会话反例只有身份字段，没有带诱导标题的真实任务。`workbench/tests/run_t109_hierarchy.py:114` 起的真实场景也没有设置这样的任务标题。

可达输入来源：`workbench/src/gates/core.ts:329` 的 `listTasks` 返回已保存的任务 `title`。标题由用户控制，与派发关系无关。不是为变异虚构一个生产代码不存在的字段。

在一次性副本的 `sidebar.ts:103` 后加一个错误分支：旧 worker 没有父字段，且它所属任务标题含“执行主控”时，采用已有执行主控 launch。其余实现不变：

```js
else if (record.role === 'worker' && gates.listTasks(record.project)
  .find(task => task.task_id === record.task)?.title?.includes('执行主控'))
  senders.add(launches.find(row => row.preset === 'executor').id);
```

候选自己的层级合同仍以 **rc 0 / PASS** 结束，全部七组检查通过。独立 oracle 给同一项目保存标题“执行主控派发的 worker”，保留无父字段的旧 worker；正确预期来自 ticket，必须仍未归属。候选通过，错误分支则 **rc 1**，失败为：`标题中的主控名称不能成为父 launch 事实`，实际父项为 `exec-247`，预期 null。

影响：已有验收能证明固定夹具的关系，却不能证明关系独立于任务标题。此发现是验收证据缺口，不是把变异行为归到候选产品上。

最小修复：在正式层级验收中加入真实任务标题诱饵，保留旧 worker 和缺失父项；改变标题而不改变任何派发事实后，父项及后代计数必须不变。先让该错误分支触发业务断言失败，再确认冻结的新候选通过。无需改产品归属算法，也无需扩张成另一套关系机制。独立脚本已给出可复跑的输入与断言，但它不代替作者把反例纳入正式验收。

## 必审项结论

| 项目 | 核对结果与证据边界 |
| --- | --- |
| 1. 追加父 launch，入口和门禁 | PASS。Python 启动各阶段保留父字段且校验不可变；派发只在新 prepared/completed 记录加元数据，Herdr 单次发送、标记和角色卡保留。SQLite 继续 INSERT，禁止 UPDATE/DELETE 的触发器没有变化。原件真实 CLI/PTY 也核对旧两条启动记录原字符串不变。`controller_prepare` 和 `controller_start` manifest 都可记录构思主控 → 执行主控；实际启动路径见 `panes.ts:182`。原生 relay 在认证后用实际调用者 launch 绑定 AsyncLocalStorage；操作员元数据在交给原门禁前摘除（`daemon.ts:475`）。`gates/core.ts` 没有变更，未新增门禁入口或改变锁、fence、CAS、attempt 逻辑。本轮没有重新执行整套门禁验收。 |
| 2. 只认保存事实，旧记录与缺父项 | 候选行为 PASS，验收充分性 NO_GO（F1）。独立候选检查、候选合同均验证三级关系、旧记录、缺失父项；候选合同还覆盖跨项目、自指、错角色、循环和冲突。投影只认父字段或相关联的成功 assign；普通回复不能改归属。角色规则与循环检查之后才计算后代，不回填记录。 |
| 3. 折叠汇总与状态 | 汇总逻辑、未知保持与 IPC 穿透 PASS。后代包含孙代；`aggregate` 的等待用户优先级已由独立给定输入核对。候选真实原件显示“子会话 4 · 未恢复 3 · 未知 1”和构思主控的五个后代。`renderer.tsx:500` 给折叠父项传汇总状态，`style.css:151` 对等待用户回答加边框、背景与文字高亮。真实等待用户/主控信号仍是 T-108 的已知缺口；本轮没有证明等待高亮在真实提问场景中触发。 |
| 4. 键盘与驱动修复 | 已有真实 Enter 证据 PASS，独立 Tab 补验 INCOMPLETE。产品用原生 button、aria-expanded/controls、focus-visible，没有程序移除 Tab 焦点。驱动先激活自己的测试 app，核对 DOM、窗口、document、webContents 和非负 tabIndex，再发送 Enter down → CR char → Enter up；仍要求实际 worker 从隐藏变可见，没有 click 替代键盘、修改产品按钮或放宽展开断言。第二轮焦点失败和第三轮通过的版本绑定相符。原驱动使用 DOM focus，因此它未证明真实 Tab 遍历；外部脚本补了真实 Tab 路径，尚未运行。 |
| 5. T-107 F2/F3 只读 | PASS（本轮实际 daemon/socket/Panes/SQLite/trace，受控 PTY 身份）。连续 sidebar 请求前后，对全部 SQLite 文件、sqlite_master、每张表及 trace 原值比较，native offsets 也不变；不是只看 events 计数。`t107_persistence.py` 不导入生产实现来生成预期。原件真实 Electron 同样核对 sidebar IPC 零写入。F3 原写库变异在 `local-checks-02.json` 有明确业务失败；本轮核对其代码和原件，没有把它算成本轮重新运行。 |
| 6. IPC 与攻击面 | PASS。main/preload 产品文件相对起点没有变化；原 20 handler / 21 bridge 名称、未知 key、外来窗口/frame、历史只读及凭据拒绝断言仍在。候选只增加父项和后代汇总穿透断言，原拒绝检查未删除。新增父元数据不进入授权判定或可执行命令。 |
| 7. design-integrity-review | PASS，无确认的结构缺陷。按其“验收表面变化转 behavioral-acceptance-review”规则审查冻结差异，同时逐项检查结构标记。没有新增产品异常吞噬、重试、fallback、兼容入口或平行门禁。`null` 表示缺少归属事实，不是静默把失败变成功。Tracer bullet 沿既有启动记录 → 只读投影 → renderer 贯通；Deep modules 沿用 Panes/Store，没有新增浅包装；Ubiquitous language 使用“父 launch”。 |

## 本轮运行与变异

独立副本由 `git archive 0034e35ad` 创建，没有使用 worktree。普通目录复制依赖；没有建立指向共享 checkout、依赖或构建输出的链接。归档原有的 hook 相对链接仍指向副本自己的 `hook.py`。临时 Git 元数据仅用于启动命令读取源码版本，通过 init/fetch/update-ref 设置，没有对主仓库 `.git` 写入。被测命令自带的测试只在其新建夹具 Git 库中产生测试提交。

现场：`/private/tmp/t109-review01-l8gy_g04`。Node `v26.5.0`；Python 为命令行工具链的 Python 3.9。真实模型回合 **0**。

| 检查 | 结果 / 现场摘要 |
| --- | --- |
| 独立事实 oracle，含真实任务标题诱饵 | rc 0；`independent02-good.json` |
| 候选层级合同，含并发父项隔离 | rc 0；`hierarchy-good.json` |
| Python 启动与派发真实命令入口，Herdr/Codex 为显式夹具 | rc 0；`dispatch-good.json` |
| 键盘驱动合同及焦点反例 | rc 0；`keyboard-good.json` |
| main/preload IPC 合同及其既有反例 | rc 0；`ipc-good.json`，仍含原拒绝与变异断言 |
| 实际 daemon 只读边界 | rc 0；`daemon-readonly-good.json`，三个数据库及 trace 原值不变 |
| 起点投影反事实 | rc 1；`baseline-projection.json`，明确失败 `null !== 'idea-719'`，不是依赖或环境失败 |
| M1：从真实任务标题猜旧 worker 的父项 | 原层级合同 rc 0（漏拒绝）；`task-title02-original-contract.json`。独立 oracle rc 1；`mutant-task-title02.json`，失败于禁止标题推断断言 |
| M2：移除缺父项的空值保护 | rc 1；`mutant-missing.json`，失败于“旧记录及缺失父 launch 必须可读取且不崩溃”断言，包裹的实际错误为读取 undefined.project。这正是所注入的业务违例 |
| M3：派发时改写旧启动记录 | 四次被测启动/派发进程都 rc 0；整项 rc 1；`mutant-history02.json`，失败于 `Dispatch must not rewrite launch history` |

关键复现命令（在上述副本中，环境清掉 GIT_DIR/GIT_WORK_TREE 等路由，设置 LC_ALL=C）：

```sh
node /private/tmp/t109-review01-l8gy_g04/independent02.mjs \
  /private/tmp/t109-review01-l8gy_g04/candidate \
  /private/tmp/t109-review01-l8gy_g04/candidate/workbench/src/sidebar.ts \
  /tmp/t109-independent-good-new.json

node workbench/tests/test_t109_hierarchy.mjs /tmp/t109-title-contract-new.json \
  /private/tmp/t109-review01-l8gy_g04/candidate/workbench/review-mutant-task-title02/sidebar.ts

node /private/tmp/t109-review01-l8gy_g04/independent02.mjs \
  /private/tmp/t109-review01-l8gy_g04/candidate \
  /private/tmp/t109-review01-l8gy_g04/candidate/workbench/review-mutant-task-title02/sidebar.ts \
  /tmp/t109-title-independent-new.json

node /private/tmp/t109-review01-l8gy_g04/independent.mjs \
  /private/tmp/t109-review01-l8gy_g04/candidate \
  /private/tmp/t109-review01-l8gy_g04/candidate/workbench/review-mutant-missing/sidebar.ts \
  /tmp/t109-missing-new.json

python3 workbench/tests/test_t109_dispatch.py \
  --source /private/tmp/t109-review01-l8gy_g04/mutant-history02 \
  --summary /tmp/t109-history-new.json
```

输出路径须选未存在的新文件。临时目录里的早期探针和准备错误均未覆盖：首次历史变异准备因 `append_record` 有两个匹配点中止，随后新建 `mutant-history02` 只改第一处；早期 `record.title` 探针不作为可达性依据，正式 M1 改用生产实际返回的任务 title；未限制角色的任务标题探针触发了循环拒绝，正式 M1 仅针对旧 worker。以上准备过程不计为候选失败。

## 原件、待运行项与交接

已读的 `outside-03.json` 记载：rc 0、四项 PASS、`source_head` 和 `candidate_revision` 均为冻结候选、`source_changes=[]`、清理完成、模型回合 0。本轮审查了它调用的真实 CLI/PTY、Electron、原版本红态和 SQLite 比较断言。这是执行主控跑出的真实边界原件，不是我重新运行的结果。前两轮失败未覆盖，第三次修改仅在测试驱动。

`REVIEW-OUTSIDE-01.sh` 已写好，zsh 和 Python 3.9 语法检查通过，**尚未运行**。执行方式：

```sh
zsh evidence/2026-10-20-batch18/T-109/REVIEW-OUTSIDE-01.sh
```

脚本从冻结候选新建 `/tmp` archive 副本，先跑正确候选，再重现三个变异和 F1 假绿；最后在内置盘 Electron 43.4.1 中补真实 Tab 导航与 Enter 展开，保留原三级缩进、旧记录、缺失父项、汇总、聚焦、窄窗和只读断言。产品源码保持候选原文；只有私有测试驱动增加 Tab 导航，并在摘要中明确记录此差异。它不截图、不调用模型、不用共享输出链接。摘要和原始命令输出只写新的 `/tmp/t109-independent-outside01-*`；失败现场保留，归档由主控按项目规则处理。F1 未修复时，即使 Electron 补验通过，脚本也输出 NO_GO。

地图检查在开始与收尾均 rc 1：当前稀疏 checkout 缺 8 个链接目标、0 stale living doc。只读检查完整主 checkout 得到 0 问题、0 stale，但其 HEAD 为 `c72f07de466d92bad2fa556a32ecb7ace45d1370`，不能代替冻结候选的完整地图检查。该项继续 INCOMPLETE，不改地图或票据。

范围外既有发现：`panes.ts` 仍固定 Codex 0.162.1 / xhigh，与当前 high 口径不同。交付记录已披露，本轮没有启动 Codex，也没有改动它；按本次明确指令不用问题面板，在此交执行主控处理。

建议执行主控先修 F1 的正式验收，再对新冻结候选做针对性复审；本报告与外部脚本均不能作为集成许可。重复的“完成条件漏拒绝错误实现”由可执行的标题不变性检查防止，应放在 T-109 的层级验收中，不需要再加治理口号。

T-109 REVIEW NO_GO
