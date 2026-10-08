# T-043 交付记录（2026-10-08）

结论 **PASS（可核对部分）**，待主控关闭。验收第 4 项“外观由用户判断”未勾选，由用户看截图决定。没有模型调用；没有 push。

候选为 Synara fork `a2a` 分支 `d3b5bcc61cc212572f38e01139e1b9af2196b820`（基线 `3566ef4eb`）。只改 `apps/web/src/a2a/**`，没有碰上游组件、`ChatView.tsx`、构建输出或依赖目录。

## 改了什么，为什么这样做

| 问题（用户意见） | 根因 | 改法 |
| --- | --- | --- |
| 状态行和“人工输入记录器”在任务顶部和每个栏里各出现一次 | 上游 `ChatView` 为每个 thread 渲染一份 `<GateStatus threadId>`；任务窗口里的栏就是 `ChatView`，所以每栏多一份。这份还每秒各自轮询一次 | `GateStatus` 读一个 React context；任务窗口在最外层声明“门禁已在顶部显示”，栏内的 `GateStatus` 直接返回 `null`（也不再发请求）。不用改 `ChatView`。任务窗口之外的单个会话页行为不变 |
| “查看人工介入记录”展开块像邮件 | 独立的 `<details>` 记录块 | 删除。人工介入改为对话流里对应那条人类消息上的小标记；栏标题只留“人工介入 N”，为 0 时不显示 |
| 门禁区占三行（状态、动作、记录器） | 各组件各占一个带边线的整行 | 合成一个 `GateBar`：步骤（点 + 连线，当前步骤 `aria-current="step"`）、当前允许的那一个动作、记录器状态芯片。失败原因折叠在下方一行，展开才看完整输出 |
| 记录器 failed 说明刺眼 | 红色徽章加两段红字 | 状态芯片只改一个红点；说明写成一行灰底、灰字的备注，说清原因和后果（门禁拒绝改变任务状态的操作，保留错误码 `human_input_observer_failed`） |
| 3 个以上会话 | 栏最小宽度 20rem、无吸附 | 栏最小 22rem、`flex-1 basis-0`，容器横向滚动并吸附到栏首；栏标题固定高 `h-9`，聚焦栏用淡底和前景色标明 |

沿用的 Synara 原件：`Badge`、`Button`、`Collapsible`、`DisclosureChevron`、`StatusChip`（含 `bg-status-*`/`bg-warning` 令牌）、`text-ui-*` 字号。没有新增依赖。没有从零写的通用组件；唯一新文件 `InterventionMarks.tsx` 见下。

**人工介入标记的做法与限制。** 对话流是上游标记，不能传 prop。标记是限定在该栏（`data-a2a-pane`）内、以事件里的 `message_id` 为键的一条 `::before` 规则，外观对齐 `Badge warning`（小号）。它跟随上游行的重渲染与滚动，不改 DOM。限制：只能显示固定文字，不能带悬停提示；事件时间仍放在栏标题计数的 `title` 上。读取层 `humanInterventions` 新增 `messageId`（T-037 已发布的 `details.message_id`，缺失或为空则报错，与其他字段一致）。

**文案。** 观察器状态改中文：未安装 / 启动中 / 正常 / 已停止 / 已失败。步骤名 `ready/claimed/submitted/verified/accepted` 仍用门禁原词。失败原因标题：验收未通过 / 集成冲突 / 验收结果未知 / 验收中断，原始 `verification.state` 在悬停提示里。

## 夹具与口径（务必读）

- 真实：项目、3 个 thread、membership、4 条用户消息（真实 `thread.turn.start`，provider 全部禁用、`CODEX_HOME` 为空，turn 随即失败，所以栏里有 “Provider turn start failed” 的红色提示，这是夹具环境的噪声，不是界面问题）、门禁任务经 `coop` 同一入口 create → claim → submit → verify，**独立 oracle 真实失败**（`oracle_failed`，`unordered-ties`），页面里的“失败原因”就是它的真实输出。
- **FIXTURE（读响应拦截，见 `shoot.mjs` 头注）：**① `GET /api/a2a?thread=…`（ChatView 自带门禁行读的那个）用真实 `status` 结果回应，代替“thread 已被真实 run 绑定”；改前截图靠它复现重复行，改后用同一个拦截证明重复消失；② 一条 `human_intervention` 事件（T-037 已发布形状，`message_id` 指向 worker 栏里那条真实消息）与 `human_input_observer` 块（healthy/failed）追加到读响应。没有真实人工输入记录器，也没有自造字段。
- 观察器 failed 的原因文字标明“协议夹具……非真实故障”。
- 环境：slot `t043`，端口 5816/7776，空 home（只从 T-038 实例复制 settings.json 并禁用全部 provider），外置盘；Playwright 与 Chrome 为 fork 现有，未下载浏览器；有窗口 Chrome、独立 context、`reducedMotion`、`colorScheme` 分别取 light/dark。

## 截图（本目录）

| 内容 | 文件 |
| --- | --- |
| 改前（浅色；复现重复状态行/记录器） | `before-light.png` |
| 改前，展开旧“查看人工介入记录”块（浅色/深色） | `before-light-expanded.png`、`before-dark-expanded.png` |
| **改后，3 个会话 + 1 条人工介入标记 + 真实失败原因（浅色/深色）** | `after-light-main.png`、`after-dark-main.png` |
| 改后，记录器 failed 的备注（浅色/深色） | `after-observer-failed-light.png`、`after-observer-failed-dark.png` |
| 改后，展开失败原因 | `after-failure-open-dark.png` |
| 改后，打开“会话归属”（MembershipEditor 未改，仍可用） | `after-editor-light.png` |
| 改后，5 个会话横向滚动（浅色/深色） | `after-wide-light.png`、`after-wide-dark.png` |

`after-light-main.json`/`after-dark-main.json` 的 `structure` 字段是 DOM 计数：`gateSections: 1`、`observerIndicators: 1`、`legacyRecordBlocks: 0`、`markedRows` 恰为夹具里那条消息 id、三个栏标题只在 worker 栏有“人工介入 1”。改前没有同样的计数（当时脚本还没有这一项），改前只有截图。带 `-01/-02/-03`、`after-light-01`、`after-light-02`、`after-wide-dark-01/02/03` 的是迭代中的中间截图，保留，不作为通过依据。

复现：`./a2a/scripts/bun` 经 `A2A_SYNARA_SLOT=t043` 运行 `shoot.mjs <label> <light|dark> <missing|healthy|failed> <yes|no>`（环境变量 `TASK`、`COLUMNS`、`OPEN_FAILURE`、`OPEN_EDITOR`、`EXPAND`）；实例由 `start.py <label>` 启动（`./a2a/scripts/bun run dev`），夹具由 `fixture.py`、`seed.py`、`messages.py`、`seed2.py` 建立。

## 检查

| 项 | 结果 | 记录 |
| --- | --- | --- |
| `fmt:check` | PASS | `check-fmt.log`；中途一次 FAIL 在 `check-fmt-01-fail-after-summary-edit.log`（改完失败摘要后未格式化），随后 `fmt` 应用并复查通过 |
| `lint` | PASS（0 error；868 条既有 warning） | `check-lint.log` |
| `typecheck` | PASS | `check-typecheck.log` |
| T-038 相关 web 测试（`humanIntervention`、`threadDetailSubscriptionRetention`、`-threadDetailOwnership`、`uiFontSize`） | PASS，4 文件 27 测试 | `check-web-tests.log` |
| 新断言的坏实现检验 | PASS | 去掉 `message_id` 校验后 `humanIntervention.test.ts` 失败（`mutant-no-message-id-check.log`），恢复后通过（`restored-test.log`）；期望值来自 T-037 的字段合同，不是实现输出 |

membership 服务端与合同文件（`membershipRoute.ts`、`membership.ts`、`a2aMembership.ts`）本次未改；它们没有独立的单元测试文件，T-038 的验证是 HTTP/GUI 场景。本次只用截图确认 `MembershipEditor` 仍能打开，没有重跑 T-038 的 HTTP 场景。未运行完整 workspace suite（T-038 记录里它已是 NO_GO，且本次不涉及 desktop）。界面逻辑只有视觉与 DOM 计数证据，没有新增交互测试。

## 改动文件

fork `d3b5bcc61`：`apps/web/src/a2a/` 下 `GateStatus.tsx`、`HumanObserverStatus.tsx`、`GateActions.tsx`、`TaskWindow.tsx`、`humanIntervention.ts`、`humanIntervention.test.ts` 修改，`InterventionMarks.tsx` 新增。

## 未解决与过程中的失败（如实保留）

1. **上游空会话页脚在窄栏会重叠**：空 thread 的输入框上方一行（项目名 / 分支 / Temporary / Worktree）在 22rem 栏宽下文字叠在一起（见 `after-wide-light.png`）。这是上游 `ChatEmptyStateHero`/页脚的布局，不在 a2a 文件里，没改；有消息的会话不出现。要修需主控批准改上游。
2. 夹具里 provider 禁用，所以每个栏都有 turn 失败的红色提示；改后截图前脚本点掉了 toast 和部分横幅，仍有残留。这与 T-043 的界面无关。
3. “栏里已有消息条数很多时标记是否仍可见”未测；标记依赖上游行属性 `data-message-id`/`data-message-role`，上游改名会使标记静默消失（没有对应的运行时检测）。
4. 首次追加消息的命令缺 `runtimeMode`，服务端返回 `Missing key ["runtimeMode"]`；我随后清理了那三份失败的输出（`msg-*.json`）后才补字段重试，没有保留。命令与脚本已修正保留。
5. 两次先启动了只含 Vite 的 `dev:web`（服务端没起，`start-01/02-webonly-stopped.json`，`vite-01/02.log` 保留），改用 `dev` 后正常。另有两次 `shoot.mjs` 因 zsh 对 `$a` 不分词而用法报错、未产出截图。
6. 栏最小宽度试过 20/22/24rem；22rem 时 1600px 宽窗口里 3 栏刚好不滚动，24rem 会出现滚动条，所以取 22rem。

## 清理

只停了我启动的进程（pgid 72752 及先前两次 Vite），5816/7776 已无监听。实例与夹具保留在 `/Volumes/WD-Elements/dev-cache/synara/instances/t043`（外置盘，未归档进 Git）。没有读写用户 Synara 数据、`~/.codex`、Herdr；没有动 `synara-t038`。`evidence/2026-10-08-batch3/launch-argv.txt` 是主控的未跟踪文件，原样保留未提交。
