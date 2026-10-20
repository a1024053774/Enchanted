# T-111 第一轮独立审查（2026-10-20）

STATUS: NO_GO
TARGET: `43717b803a6f3db84cf3420921fd277aa7d13c1a`，起点 `b1ecd6e9cba23c1bbddb331822b6500a1488e2e9`，T-111 / a1 / ready_rev 1。

结论：**需修复验收缺口 F1**。在已查产品代码中没有确认到实现缺陷；候选通过独立双打回输入。但现有交付合同接受“最多保留一条打回记录”的单处错误实现，不能证明“折回次数等于门禁事件里的打回次数”。依 reviewer 角色卡及 T-082，本轮不能给 PASS。真实 Electron 的本轮独立重跑未执行，已交付沙箱外脚本；这一限制不改变已经复现的 NO_GO。

只写本报告与 `REVIEW-OUTSIDE-01.sh`；产品、测试、地图、术语表和原有证据均未改动。没有 commit、checkout、reset、stash、push、模型调用、子 agent、全局配置写入或权限升级申请。开始时已有三份未跟踪的 `*-outside-02.json`，原样保留。

## EVIDENCE：依据和重建的答案

先读指定 reviewer 角色卡、AGENTS.md、T-111、T-109 Resolution、RESULTS.md 和用户参考图；另读 MAP.md、CONTEXT.md、intent.md。用 `git show` 与 `git diff b1ecd6e9c 43717b803` 检查候选原文和全部产品／测试改动。判定依据是票据及本次派发中的七项要求，不以作者输出作答案。用户取消截图要求有效，因此截图缺失不作为拒绝理由。

预期：一票一横向泳道，五个门禁阶段；阶段只取当前 attempt 的门禁事件；打回次数按该票真实 `delivery_rejected` 事实累计，不重复累计附属审查／检查结果。agent 只按经 T-109 校验的父 launch、项目、任务、非空当前 attempt 绑定；缺失、过期或不明归属进入未归属。角色决定阶段，monitor 在泳道上方。页面只读；超过四个可展开、集成票默认折叠、空状态和窄窗横滚成立。保留原 IPC 拒绝检查与侧栏零写入合同。

Tracer bullet：检查只读投影 → daemon → main/preload → 流程页这一生产链路，没有另建门禁入口。Deep modules：`flow.ts` 集中事件与归属投影，`FlowPage.tsx` 承担展示；既有接线层没有增加另一套状态机。Ubiquitous language：沿用任务、attempt、启动记录、门禁阶段和 T-107 状态。

独立运行环境：Node `v26.5.0`，Python `3.9.6`；所有运行副本由 `git archive` 创建于 `/private/tmp`，没有 worktree、符号链接或原仓库 Git 元数据写入。

已运行命令：

```sh
zsh evidence/2026-10-20-batch18/T-111/REVIEW-OUTSIDE-01.sh --local
```

完成的第二次运行 rc 0，脚本输出的审查状态为 NO_GO；rc 0 表示证据采集按预期完成。完整命令、stdout、stderr、JSON、探针和变异源码保留在 `/private/tmp/t111-review-01-jgb5w4pg/`，入口为 `summary.json`。

| 独立检查 | 结果 | 证据 |
| --- | --- | --- |
| 冻结候选的现有流程合同 | PASS，rc 0 | `candidate-contract.json` |
| 冻结候选的 main/preload IPC 合同 | PASS，rc 0 | `candidate-ipc.json`；21 handler、22 bridge 名称，保留原拒绝与变异断言 |
| 独立双打回输入 | PASS，rc 0 | `candidate-two-returns.stdout`；不同 attempt 各一条，另有附属 `review_result`；应计 2，不重复计数；去掉打回事件后应计 0 |
| 计数变异跑现有合同 | **错误实现被接受**，rc 0 | `count-mutant-existing-contract.json` |
| 同一计数变异跑独立输入 | 正确拒绝，rc 1 | `count-mutant-independent-probe.stderr`，实际 1、预期 2 |
| 缺失 attempt 变异跑现有合同 | 正确拒绝，rc 1 | `missing-attempt-mutant.json`，实际 1、预期 0，断言 `Missing attempt binding must stay unassigned` |

首次运行 `/private/tmp/t111-review-01-dynxy438/` 中，候选合同、IPC、双打回输入通过，但计数变异缺少依赖，报 `ERR_MODULE_NOT_FOUND: effect`。这是审查脚本准备失败，不是成功拒绝错误实现。现场保留；脚本补为普通依赖副本后重新创建全新目录运行，没有覆写首次结果。

## FINDINGS

### F1 · P1 · 完成条件漏检非零打回次数恒为 1 的实现

位置：`workbench/tests/test_t111_flow.mjs:43`、`:47`；真实 Electron 夹具 `workbench/tests/run_t111_flow.py:128` 和断言 `:179`。

现有领域合同分别测零条和一条打回，包括一次旧 attempt 打回，但没有在同一张票的同一次输入中提供两条打回。真实 Electron 夹具也只有一次打回，并固定期望 `count: 1`。因此无法区分真实累计和“非零永远为 1”。这属于关键事实的验收缺口，不是对当前正确计数实现的指控。

单处变异位于副本的 `workbench/src/flow.ts:16`：

```ts
const returns = events.filter(event => event.task === task.task_id && event.type === 'delivery_rejected').slice(0, 1)
```

其余实现完全不变。现有 `test_t111_flow.mjs` 对该变异返回 PASS。独立输入给同一票一条旧 attempt 的机械检查打回、一条当前 attempt 的审查打回，要求两条；候选通过，变异以 `1 !== 2` 失败。该错误会令页面和折回线遗漏后续打回事实，违反票据第 2、4 项及本次必审 (2)。

最小修复方向：只补验收，无需据此改产品。为同一票加入至少两条真实语义的打回事实，独立断言总数、来源与跨 attempt 累计，附属 `review_result` 不重复计数；真实 Electron 也检查非 1 次的展示与折回线。让上述单处变异在完成条件中因业务断言失败。复验时先确认候选通过，再确认变异被拒；依赖错误或启动失败不算拒绝。

## 七项必审结果

1. **只读与门禁语义：静态 PASS；已有真实入口证据核对通过。** `flowSnapshot` 仅调用现有侧栏事实读取、SELECT tasks/events、纯投影；未调用 scan、save、event、dispatch 或其他写入口。`FlowPage` 只有读取、折叠和页面切换，未发输入凭据或门禁操作。候选未改 `src/gates/`。`daemon.ts` 把新命令纳入现有 catalog/readOnly 集合，沿用读取不记录请求的路径。完整 SQLite/schema/trace 零写入的本轮独立运行仍待沙箱外脚本。
2. **阶段与次数：候选逻辑及独立输入 PASS；完成条件 NO_GO（F1）。** 阶段按 seq 遍历当前 attempt 的门禁事件；任务行只供身份与当前 attempt，不从标题、task.state 或窗格文字猜。`delivery_rejected` 独立累计整票历史；core.ts 的 `rejectDelivery` 确认为单次打回事实，`review_result` 不额外计数。未知或冲突事件路径不伪造成功。独立双打回探针证明候选能处理超过一次；现有交付测试漏检。
3. **agent 归属：静态与合同 PASS。** 先经未修改的 `sidebarSnapshot` 校验父 launch 存在、角色／项目关系、冲突与环，再匹配项目、任务、当前 attempt；不会从 pane 文本归属。`flow.ts:37` 明确要求非空字符串，故两个 undefined 不会匹配；删除此前提的变异被当前合同拒绝。缺父记录、缺失父项、过期 attempt 归未归属的真实 UI 结果来自主控证据，本轮未另开 Electron 验证。
4. **折叠与窄窗：源码及主控实际入口证据支持；本轮独立 GUI 未运行。** `Agents` 默认 slice 4，原生 button 带 aria-expanded 可展开／收起；集成票初次挂载默认折叠；五列固定 230px，1150px 泳道置于 overflow-x:auto 容器。主控 `electron-outside-02.json` 在 900px 窗口检查列宽、无 body 横溢、内部 scrollLeft 改变及展开。
5. **参考图：已直接查看原图，RESULTS 的结构对照属实。** 源码具有空心节点、细线、`›››`、阶段下竖排圆角胶囊、左侧色点和“还有 N 个 ↗”，并把重复来源折回合并成带次数的线。深色主题、五个实际门禁阶段、按票上下排、记录号／角色／状态／attempt、monitor 上置，均如其“有意不同”所述。原图左侧是彩色圆角图标，候选是小圆点，且文字由单行名称增为多行记录元数据，所以不能称像素或密度等同。RESULTS 自己把这段限定为设计／源码对照，并未声称真实渲染审美已通过；本轮也只确认到此层，不作截图验收要求。
6. **IPC 与侧栏：独立 main/preload 合同 PASS；F2/F3 边界已核对，独立真实 socket 复跑待执行。** 新接口无参数，先走已有 `windowTarget` 拒绝未知 window 和 iframe，再发固定 `flow_snapshot`；不接受客户端 task/command 注入，不颁发 pane 输入凭据。它增加所有任务流程摘要这一只读视图，既有 sidebar/catalog 本来已提供跨任务本地目录；没增加写权限或绕过既有认证。逐段 diff 确认旧断言和反例未删，原来的 sidebar 分支扩到 flow 后仍执行。F2 的只读查询没有重新引入 scan 或事件写入；F3 的实际值比较及写入变异在候选测试中保留并扩展到 flow。主控 daemon／写入变异证据支持这一点，但不能称本轮已独立重跑。
7. **design-integrity-review：在已查结构范围内 PASS。** 扫描器无发现；另手工检查新增 catch、轮询、映射及入口。页面 catch 负责展示读取错误，明确标注保留上次记录，不把失败换成成功／空状态；定时读取有卸载清理，没有重建门禁语义、兼容双路径、异常吞噬或未经事实支持的回退。纯投影与展示边界明确，没有为单个调用增设浅接口体系。扫描器只作定位依据，不替代上述检查。

## COUNTEREXAMPLE：变异与沙箱外脚本

已经在 /tmp 完成两处单点错误实现：截断打回记录、去掉非空 attempt 前提，结果见上表。第三处“读取时 `store.event` 写库”及真实 Electron 重跑写进 `REVIEW-OUTSIDE-01.sh`，本轮未执行第三处。

交执行主控在沙箱外运行：

```sh
zsh /Users/luckye/Documents/Code/a2a-wt-t111/evidence/2026-10-20-batch18/T-111/REVIEW-OUTSIDE-01.sh
```

默认使用内置盘 Electron 43.4.1，也接受 `T111_ELECTRON_DIST`。顺序为候选合同／IPC／独立双打回 → 两处变异 → 实际 flow 与 sidebar 零写入 → 第三处写库变异必须以 persisted-value 断言被拒 → 候选真实 Electron → 计数变异跑同一现有 Electron 完成条件，核对它是否仍被接受。所有结果保存在新 `/private/tmp/t111-review-01-*` 目录，不写回现有主控结果。

脚本清理 Git 路由变量，设 LC_ALL=C；Python 3.9 语法；普通 `git archive` 副本与依赖文件副本，不建 worktree／链接／提交。node-pty helper 执行位仅由既有测试在其私有 runtime 修改。服务沿用 start_new_session 生命周期。归档副本无 .git，因此只在私有驱动中把 baseline 的 `git archive` 定向原仓库只读，并明确记录归档版本；计数变异不冒称干净候选。没有改产品、响应或 IPC 数据。运行会创建私有测试窗口，保留结果，不调用任何模型。

## LIMITATIONS

- 本轮没有启动真实 Electron／socket，也未申请升级；这部分按派发要求交脚本执行。主控提供的 `electron-outside-02.json`、`daemon-outside-02.json`、`counterfactuals-outside-02.json` 均已读原件，前者绑定完整候选号且 workbench 无修改，检查项和 rc 与派发说明一致；它们是主控运行来源，不冒称 reviewer 独立运行。
- 仅审此流程页旅程及新增接口，不宣称已审全站。模型输出、原生 hook 采集质量、真实模型工作能力和生产运行可靠性不在本票证明范围；夹具不证明这些能力。
- session 开始和结束各运行一次 `project_map.py status --root .`，均有相同 8 项缺失 findings／grilling 路径问题，stale living docs 为 0。没有修改地图。票据“status 0 问题”在此稀疏检出中仍为 INCOMPLETE，不写成 PASS。
- `RESULTS.md` 与 README 对沙箱外运行仍写“待运行”，与另附主控新结果属于不同证据截止点；本报告明确分别引用，没有改写它们。
- 脚本已经以 --local 实跑；完整默认分支只完成 shell／Python 3.9 语法检查，不能视作 Electron 重跑结果。首轮脚本准备失败现场及第二次运行原件均保留。

## RULE：关闭同类验收漏检

T-109 Resolution 已记录“产品正确，但完成条件拦不住明显错误归属”的 NO_GO。本轮 F1 同属验收分辨力缺口。可机械捕获：在 T-111 完成条件加入同票两次以上打回的事实输入，并固定拒绝上述 `.slice(0, 1)` 变异；执行位置应为领域合同及真实 Electron 完成条件。无需新增泛化规则或修改 AGENTS.md；由执行主控在本票修复与后续审查中追踪。

T-111 REVIEW NO_GO
