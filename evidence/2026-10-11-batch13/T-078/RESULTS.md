# T-078-1 运行记录

2026-10-14 主控 #106～107：08 启动后是首次主题选择，未发送 Digit1／Enter，cleanup PASS。08b 的产品改动单独提交，改为每个原字节快照独立批准的按键；用途限 onboarding-theme／workspace-trust，同屏不可重放、信任仍限一次。没有主题数字键依据，不猜数字；采用文档化方向导航，再单独批准确认明确所选 Dark 的 Enter，不自动补键。新实例、参数与静态红绿见 [P1-APPROVAL-08b](P1-APPROVAL-08b.md)，实际 UI 效果仍未知／待 launch 审批，本轮未启动 CLI／API或按键。真登录用户 HOME 中任何引导屏一律停下交主控、不按键，已同步 PLAN-2；整票仍 INCOMPLETE。

2026-10-14 主控 #97～99：用户允许假服务／真登录阶段各确认一次隔离目录信任，主控已外置 cleanup-06 超限原件并字节读回。旧改动按逻辑提交并取得干净工作树；材料 08 的静态构造、原始 hook 留证与一次 Digit1 后台通路具红绿，见 [P1-APPROVAL-08](P1-APPROVAL-08.md)。移除 IS_DEMO、禁标题、增加 debug，保持假 Bearer／theme／3 秒 hooks；不预置内部状态、不自动补 Enter。按 #99，08 只做一个回合，Esc／二次送达／紧急停止仍由 09 承接，不缩减整票验收。08 实际启动、信任和 hooks 尚未运行，当前准备局部 PASS／整票 INCOMPLETE；变基改变源码后必须重新绑定材料。

2026-10-13 主控 #95：Bearer 生效，nonce 提交后 API 收到一条标题侧请求，未得到主回合／hook 证据；continue-06 因缺 turn_start_signal 停下，cleanup-06 PASS。只读归档显示信任状态 false、无 hook_received／signal 请求、无 debug 或 hook stdin／退出数据，因此不能归因于 timeout 或字段不符。标题请求占住串行 handler，原 runner 在写 release 前失败，未发送 SSE。材料 07 为 BLOCKED 诊断／提案，见 [P1-APPROVAL-07](P1-APPROVAL-07.md)；已报 blocking issue `20261013T182412Z-worker:s13-t078s-issue-001` 请求目录信任决定。建议假服务禁用文档化标题请求并加 debug／hook 留证，不改身份检查或盲目增加 timeout。本轮未改产品候选、未发新输入、未启动 CLI／API／模型，不预置信任状态或穿过提示。

2026-10-13 主控 #94：continue-05b 的已登记 nonce 真实送达并提交，但 CLI 报 `Not logged in · Please run /login`，假 API 无请求，期限到即停；不能把到提示符等同认证可用。原协议失败及 traceback 保留。cleanup-05b 核对记录 CLI PID 50901 已退出后才 PASS，主控确认无残留；该退出修复获得真实复验。本轮按官方文档选择只在假服务阶段用 `ANTHROPIC_AUTH_TOKEN`，移除 API_KEY，假 API 仅接受公开 Bearer token；不用 helper、内部批准状态或自动按键。新实例材料 06、依据与纯检查见 [P1-APPROVAL-06](P1-APPROVAL-06.md)。profile／handler 红绿、材料构造与语法检查通过，完整静态检查仍 INCOMPLETE：旧 cleanup 归档 8,028,610 字节，待外置。新阶段先归档并读回，再取得完整静态 PASS 才启动 API／CLI；旧失败报告与未运行草稿均保留。真实登录阶段不变，本轮未启动 CLI／API／模型，实际新认证、hooks 与完整主控链路仍 INCOMPLETE／待审批。

2026-10-13 主控 #93：p1-launch-05 仅用文档化 theme／IS_DEMO 直接到主提示符，无 key／目录信任提示；没有写未文档化状态。continue-05 在第一次后台命令前失败，实际缺失的是 `<实例根>/initial-ready.json`，不是 API 或 CLI 文件；原失败 result 保留，commands.jsonl 实际未生成，假 API 无请求。只读诊断见 [p1-continue-diagnosis-05b](p1-continue-diagnosis-05b.json)。runner 改为显式传入主控确认的就绪材料，记录 traceback／文件路径，用新输出标签保存续跑；产品与 CLI 参数不变，实例未重启、未 cleanup。新阶段及审批材料见 [P1-CONTINUE-05b](P1-CONTINUE-05b.md)，当前仍 INCOMPLETE／待续跑审批。

2026-10-13 主控 #91：批准先仅用文档化的隔离 `theme: dark` 和 `IS_DEMO=1` 观察固定 CLI；API key 批准与目录信任仍不预置，出现即停并保存终端原文。决定原样留档为 [controller-decision-04-update-91](controller-decision-04-update-91.md)，blocking issue 未自行关闭。材料 05 和新阶段已准备，静态红绿及完整审批说明见 [P1-APPROVAL-05](P1-APPROVAL-05.md)。本次没有启动 CLI、API、PTY 或模型，真实运行仍 INCOMPLETE／待 p1-launch-05 审批；cleanup 退出核对仍待真实复验。

2026-10-13 主控 #89：真实 CLI 03 在隔离 HOME 启动并停在主题引导，无模型请求；cleanup 曾在 CLI PID 16681 仍活着时报 PASS，几秒后其自行退出。新 cleanup 增加关联 manifest 的 CLI 退出确认，纯检查通过，尚待真实复验。文档仅确认 theme／IS_DEMO；未找到假 key 和 repo trust 的公开预置契约，已报 blocking issue `20261013T154915Z-worker:s13-t078s-issue-001`。材料 04 已生成但启动明确 BLOCKED，见 [P1-APPROVAL-04](P1-APPROVAL-04.md)；未写未文档化状态、未操作引导界面或启动新 CLI。

2026-10-13 主控 #88：p1-launch-02 退出 1，停于 Required CLI options missing；API 曾绑定 61040，交互 CLI 未启动、模型回合 0；随后 cleanup PASS。读回官方帮助与文档后，不能把未列完整文件参数视作已删除／改名。本轮仅改为公开列出的 `--append-system-prompt` 传角色文本及其预检，生成材料 03，见 [P1-APPROVAL-03](P1-APPROVAL-03.md)。其他参数经实例身份正规化比较保持一致；当前 INCOMPLETE／待审批，没有再启动 CLI 或 API，旧失败原件未覆盖。

2026-10-13 主控 #84 恢复：s13-t078s 续接原生会话，按主控日志读回为 gpt-6.1-sol/xhigh/default。旧 P1 实例根消失，材料 01 过期并保留；已生成新根、launch/session 的材料 02。API 改为启动时分配端口、核对 PID/身份并保存实际 manifest 后才启动 CLI。端口 0 的产品入口纯红绿与绑定检查见 [P1-APPROVAL-02](P1-APPROVAL-02.md)。当前仍 INCOMPLETE／待审批，没有运行 CLI、API、socket 或真实模型。

2026-10-12 续卡记录：用户已选择假服务为主、真登录复核 2～3 回合，决定 04 批准 T-078-2 的 P0。P1 实现与静态材料已准备，**INCOMPLETE，等待首次真实 CLI／假 API 启动审批**，尚未运行。详见 [P1-APPROVAL](P1-APPROVAL.md)。以下 T-078-1 的已验收结果只绑定其原候选，不替新增主控运行路径背书；旧“等待认证方式决定”是当时记录。

2026-10-11。总状态：**INCOMPLETE，待主控关闭**。T-078-1 非 Claude 范围的最终验收与一次新上下文只读独立审查均为局部 PASS，绑定代码提交 `b3fb998cf48574821c39440ece3f9ff897f26cf9`（父提交 `532c51f4cc12352bb7cf545ce1e5f824d68bdc4a`）。最终阶段包括领域 11、管理客户端 8、窗格状态 11、静态启动骨架 2、运行时入口 12、输入失败方式 11、worker 收件箱入口 14；原回归 8/9/18 与 CAS 1 全过，四项权限及三项原业务变异反例均成立。详见文末最终验收表、[最终原始检查点](outside-final-01/checkpoint.json) 和 [独立审查](independent-review-01.md)。真实 Claude 启动、主控角色凭据及 hook 接线、真实主控互相唤醒和三窗格验收未完成，等待 needs-decision `20261011T101958Z`；本卡未启动 Claude 或其夹具，仍待真实 Claude 复核。

任务：T-078-1，T-078 `ready_rev: 1`；worker `s13-t078`；分支 `exec/t078`；产品起点 `14b57d22a84bcaebfa91c5051b9909b53a570fac`。授权和范围见 [PLAN](PLAN.md)、[主控决定 01](controller-decision-01.md)、[主控决定 02](controller-decision-02.md)。

## outside-red-01：P1 未通过，未进入产品红态

由执行主控在沙箱外运行，原始产物位于 [outside-red-01/checkpoint.json](outside-red-01/checkpoint.json)。P1 运行 Electron 43.4.1 与已安装的 xterm 6.0.0；退出 1。未重写此目录及其中的失败输出、源快照或截图。

通过的局部检查：裸 onData 包含设备应答；公开 parser 接管六个查询；初次键盘输入；中文多行粘贴；合成组合输入；大段粘贴。交错场景失败，因此 P1 不是 PASS，focus 检查与产品红态未运行。

### 空串调查：实际没有空 onData 回调

| 分类 | 结论 | 证据 |
| --- | --- | --- |
| observed | 原始 `events` 共 20,023 条，`kind=data` 且 `data=""` 的事件为 0 条 | [逐条核对结果](empty-input-investigation-01.json)、原始 `p1/results.json` |
| observed | `interleaved-output-input` 阶段没有任何 onData 回调，只有 `input(data="y", isTrusted=true)` 的 DOM 事件 | 原始事件 seq 20023；同一核对结果 |
| observed | 报错 `unexpected onData ""` 打印的是该阶段全部 data 事件的 `map(...).join('')`，空数组也得到空字符串 | 原失败运行保存的 `sources.tar.gz` 中 `probe_t078_input_origin.mjs`；不是一条原始回调 |
| observed | 失败探针在初次 Enter 之后，仅向交错场景发了 `sendInputEvent({type:'char', keyCode:'y'})`，没有该字符的 keyDown | 同一源快照；初次 Enter 与之后各场景的调用顺序 |
| observed（源码） | xterm 在 `_keyDown` 开始清除 `_keyDownHandled`；screenReaderMode 下处理 Enter 后将它设为 true；`_keyUp` 不清除它；`_keyPress` 见 true 就返回，且 screenReaderMode 下 `_inputEvent` 不代发文本 | 本地 `src/browser/CoreBrowserTerminal.ts:1022、1102、1119、1145、1196` |
| inferred，待新运行验证 | 前一个 Enter 留下的按键处理状态，使缺 keyDown 的 char 事件不产生 onData；“并发输出产生空回调”没有原始证据支持 | 与实际 DOM input 有 y、onKey/onData 均没有 y 的记录相符。新增无输出的对照探针检验，不能仅凭源码算实测通过 |

以上修正的是主控决定 02“核对结果”对错误文本的解释；决定 02 对空事件的处理授权仍照办。调查只读取已核对的本地源码与公开类型定义，没有接触 xterm 私有运行时接口、修改依赖或联网查询。

复核原始记录的命令（输出必须是尚不存在的新文件）：

```sh
python3 /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/inspect_t078_p1.py --input /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-red-01/p1/results.json --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/empty-input-investigation-02.json
```

### 哪些条件可能确实产生空回调

**observed（源码）**：`CompositionHelper.ts:95–107、135–136` 中，组合输入尚未结束而遇到普通按键时，会立即结束组合输入，把 textarea 的对应 substring 直接交给 `triggerDataEvent`；这条即时分支没有长度判断。`CoreService.triggerDataEvent` 也没有空串过滤。公开 `Terminal.input` 同样接受字符串并触发 onData，不能假定所有回调都非空。

**inferred，待复现**：令组合输入的 textarea 内容为空，再按 Enter，应先有空串回调，随后有独立的 CR 回调。新 P1 通过公共 DOM compositionstart 和 Electron 按键事件构造此条件；不会直接调用私有方法。这个合成场景不等于真实 macOS 输入法验证。

## 决定 02 的处理与 outside-red-02

- 修正探针驱动：交错场景使用完整 keyDown → char → keyUp；保留原期望“恰好收到 y”。另加前一个 Enter 后只发 char 的反例和完整按键的正例，判定依据为真实公开 DOM/onKey/onData 事件，不读取内部标志。
- 错误输出分别写回调数、空回调数与拼接数据，避免把“无回调”误报为“空回调”。
- 长度为 0 的回调只保存 `empty-data` 观察，带窗口、序号、时刻，不进入非空输入集合。后续产品处理须在后台追加 `terminal_input_empty`，包含 `window_id`、`sequence`、`received_at`、`request_id` 和 `byte_length: 0`；不写 PTY，不写 user_inputs，不派生 human_intervention。此时产品尚未改动，这不是已实现声明。
- P1 单独触发空组合输入，仍要求后续 CR 完整出现；产品入口增加同一情形的合同检查：空事件有观察、对应 request_id 没有用户输入，PTY 新增字节仅是随后 Enter 的 CR。原来的中文输入、人工介入与匿名伪造角色三条断言保持不变。
- 产品新增空事件行为尚未取得红态；新检查点要求四项合同红态，不能把探针里的观察处理当产品通过。没有回调、丢失非空数据及非预期失败仍停止。

交给执行主控的新命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-red-02
```

当前未运行。先验证 P1，再执行产品红态；任何非预期失败立即停下。`outside-red-01` 保留，目录存在不覆盖。更新后的静态检查见 `preparation-check-02.json`，静态通过不代表上述推断已被运行证实。

## outside-red-02：11 项通过，焦点来源检查失败

执行主控已运行本节之前给出的 `outside-red-02` 命令；[checkpoint](outside-red-02/checkpoint.json) 与 [P1 原始记录](outside-red-02/p1/results.json) 保留。共 12 项，11 项 PASS，P1 整体 INCOMPLETE，未进入产品红态。

- **observed**：Enter 后只发 char，不伴随新 keyDown，即使没有并发输出也不产生 onKey/onData；完整按键序列得到 `q`，交错场景得到 `y`。决定 02 调查中的探针原因已有正反例支持。
- **observed**：人为开始空组合输入后按 Enter，确实先出现一条空回调（seq 27），带窗口、序号与时刻；随后独立 CR 正常送出。这与原 outside-red-01 的“没有回调”是两种情况。
- **observed**：开启焦点上报时出现 `ESC [ I`（seq 20046），其来源未被 DOM 焦点回调标明；之后 blur/focus 的两条才带原探针的 DOM 来源标记。原来的按 DOM 事件时间关联方法不能覆盖全部焦点应答。
- **observed（源码）**：`InputHandler.ts:1935` 在 DECSET 1004 设置 sendFocus 后立即发 `_onRequestSendFocus`；`CoreBrowserTerminal.ts:1293` 按当前元素状态直接生成焦点报告，因此首条应答不需要发生一次新的 DOM focus。此处只是读取源码，不使用这些私有接口。

## 决定 03：接管 1004，保留混合模式顺序

[主控决定 03](controller-decision-03.md) 已原样留档。修改目前限 P1 与运行标签；生产输入功能仍未实现，后续接入须采用同一决定，不能把本节当产品绿态。

1. 用公开 `registerCsiHandler({prefix:'?', final:'h'/'l'})` 接管含 1004 的 DECSET/DECRST，返回 true，避免 xterm 开启焦点上报。移除原探针按 DOM focus/blur 时序标来源的路径；不按 onData 文本去删除焦点字节。
2. handler 的数字参数已经丢失前导零，且不能修改内置 handler 的参数。因此输出写入器保留原始控制序列，并在模式序列结束处划分写入边界。xterm 的实际 parser 确认 1004 后才过滤该模式；剩余模式仍由 xterm 解析。普通输出只因分段而改变调用批次，字节不被改写。
3. 混合模式剩余部分在当前分段完成后、下一段之前等待处理完成。不能简单地把它追加到整块输出末尾，否则 `1004;2004h` 后紧接 `2004l` 会错序。不会在 parser 的异步 callback 中等待重入的 write，避免堵住同一个解析队列。
4. 每次实际拦截都追加观察事件，含窗口、递增序号、时刻及真实原始序列；分片与带前导零的序列也按原始字符记录，不用标准化后的参数冒充原文。

P1 原有 11 个通过项不放宽；原焦点检查改为两项：无焦点 onData 且其他模式保持效果与顺序；每次拦截都有完整观察记录。两项共同覆盖独立 set/reset、混合 1004/2004、同一块中相反的后续模式、跨写入分片及前导零；通过实际粘贴字节与公开 modes 读回核对 2004，而非只看 handler 自报。

**已知限制**：按此决定，CLI 在工作台窗口里收不到焦点变化。P1 当前只验证本地公开接口与列出的控制序列；还未证明生产窗口的后台记录、全部 VT 控制序列、真实输入法或真实 Claude。

下一次运行命令（未运行，须执行主控在沙箱外执行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-red-03
```

仍先 P1、后四项产品合同红态；非预期失败停下。`outside-red-01`、`outside-red-02` 全部保留。静态准备检查见 `preparation-check-03.json`；产品源代码仍与起点一致。

## outside-red-03：P1 与四项产品红态确认

执行主控运行后，worker 从 [checkpoint](outside-red-03/checkpoint.json)、[P1](outside-red-03/p1/results.json)、[产品入口](outside-red-03/entry-red/results.json) 独立读回。`checkpoint_status=PASS`、`red_evidence_confirmed=true`；P1 13 项 PASS。产品入口有四项预先约定的合同失败：窗口输入未到 PTY，缺用户输入及介入，缺空事件观察，匿名请求能冒充 ideation 将 assign 追加进库。四项是原来的三类再加决定 02 的空事件合同；没有设置／探针／清理错误，没有模型回合。

这使输入 Tracer bullet 可以进入候选实现，不代表整张 T-078 的其他行为已有红态。所有旧结果保持不变。

## 首个输入候选：待 outside-green-01

本轮写入的生产路径：

- 管理 CLI 显式携带启动者凭据；后台不再把无凭据调用或角色参数当主控身份。凭据文件由启动者排他创建，0600，绑定后台代次与 state；后台 socket 不签发管理凭据。worker 的会话 token／Stop 转交路径保留。
- Electron main 领取绑定固定 task/launch 的窗口凭据，校验 IPC 来源并串行发送；renderer 只有输入与焦点观察两个窄接口。输出按原字节偏移继续读回，关闭窗口先等待已发请求、撤销该窗口凭据，再结束视图。
- 输入由 Panes 串行写入；用户输入先入库，人工介入沿既有同事务方法派生，CR 写出前即记忙。字节长度为零只追加观察。输入异常不自动重投，过期 attempt 不接管。
- 已验证的焦点接管与设备查询处理移入 `workbench/app/terminalOutput.mjs`，P1 改为调用这一份生产模块，删除原测试专用副本。按决定 03，CLI 不接收窗口焦点变化。

验证命令（执行主控在沙箱外运行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-green-01
```

运行器重跑 P1 和同一组四项合同，绿态要求四项全部 PASS。测试断言未因实现改写；适配器只显式传递新启动者凭据，夹具归档排除凭据，确认后台关闭后删除本次创建的凭据。测试仍只使用确定性字节接收器，启动记录里的夹具版本字符串不是真实 Codex 验收。

**尚未完成**：二进制输入、完整的同时输入／注入反例与幂等检查、Esc 后用户放行、主控 attach／Claude 参数及状态适配、库客户端与 ready、紧急停止、独立审查及最终回归。现有 8/9/18 测试适配器的凭据接线也还要完成；本轮没有运行或宣称这些检查通过。没有据本候选更新 ticket Resolution 或宣称交付完成。

## outside-green-01：首个输入候选通过

执行主控已运行，exit 0。worker 读回 [checkpoint](outside-green-01/checkpoint.json)、[四项合同](outside-green-01/entry-green/results.json) 与原始 SQL／PTY 数据，结果一致：`checkpoint_status=PASS`、`green_evidence_confirmed=true`，P1 13 项及输入入口四项全部 PASS。确认后台关闭，启动凭据已删除且未进入夹具归档。

另用不导入产品代码的读回器检查固定中文字节、唯一消息／介入引用、空事件的记录与排除、匿名请求没有新增条目及归档中没有凭据。它在旧红态产物上退出 1，在绿态产物上退出 0：[红态读回](red-03-independent-readback.json)、[绿态读回](green-01-independent-readback.json)。初次交互读回记录 `green-01-readback-check.json` 也保留。worker 已查看 `window/after-input.png`：该阶段展示一个 worker 窗格；不是三窗格验收。

重放读回（输出使用新文件名）：

```sh
python3 workbench/tests/verify_t078_input_readback.py --input evidence/2026-10-11-batch13/T-078/outside-red-03/entry-red --output /tmp/t078-red-readback.json
python3 workbench/tests/verify_t078_input_readback.py --input evidence/2026-10-11-batch13/T-078/outside-green-01/entry-green --output /tmp/t078-green-readback.json
```

若重跑完整输入检查点，显式运行 `python3 workbench/tests/run_t078_checkpoint.py --phase green --label <新标签>`；`outside-sandbox.sh` 的当前目标已进入下一阶段。历史版本及实际 argv 仍在各检查点源快照与记录中。

## 收件箱领域逻辑：先红后绿，无 CLI 运行

隔离理由：真实 Claude 及 Claude 夹具仍未获运行授权。这组测试直接调用已有门禁领域入口，以逻辑收件人、控制时钟和可观察的投递队列作为外部边界；没有启动进程、终端、socket、hook 或模型，不冒充后台凭据验收。失败方式在测试文件开头先列出。

`domain-red-01` 退出 1：5 项预定缺口失败（排队误报已送达、ack 的排队状态、就绪查询及未知项目、执行主控立即中断），6 项已有约束通过。修改后 `domain-green-01` 与最终的 `domain-green-02` 都是 11/11 PASS。代码和数据库现场随每次结果保存。

```sh
node workbench/tests/test_t078_inbox_domain.ts /tmp/t078-domain-check-新目录
```

变更为：queued 投递收据与后续读回分开，重复 ack 不重发；ready 只查已绑定项目，使用项目的平面 front matter 语法，错误显式返回；角色只取 caller，执行主控可立即处理 stop，构思主控仍受超过 120,000 ms 且无 ack 的约束，记录实际 actor。上述中断仅由逻辑运行时记录调用，不证明真实进程已中断。

## 库客户端与 8/9/18：待 outside-inbox-01

新增 `workbench/bin/inbox`，send/list/ack/ready 都调用同一个后台。它不读写文件版 inbox；`ready` 不接任意目录、不替主控标就绪。CLI 的角色字段不覆盖凭据角色。

回归适配器为每次启动显式指定新的管理凭据；受控线程测试在已认证的管理请求外层下仍使用原有独立线程身份边界。没有改 `acceptance/test_*.py` 断言、业务方法、输入或预期。凭据在确认退出后删除，异常留下的本地文件也从归档排除；运行器新增显式输出和任务身份参数，证据不写入 T-075 目录，也不借用其 session。

当前交给执行主控的命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-inbox-01
```

顺序：领域测试 → 实际库客户端 → 原 8/9/18。任何非预期失败停下。库客户端用一个预先持久化的逻辑 handoff 验证读取和 ack，并明确记录该条不是 Claude 的发送；不存在接收者时保留未送达结果，不能用它证明主控唤醒。整个阶段真实模型回合为 0，不启动 Claude 或 Claude 夹具。

后续仍要补窗格唤醒／中断、主控凭据与启动参数、输入反例、独立审查及变基后全量复验。当前不提交、不更新 ticket 为完成。

## outside-inbox-01：产品回归，已修正待复验

执行主控运行 exit 1：domain 11/11 PASS，库客户端 8/8 PASS；coop 跑了 8 项，7 FAIL、0 error，均在 submit 收到 `stale_thread`。recovery、run 没有运行。保留 `outside-inbox-01/coop/` 全部结果以及 `/tmp/a5-aadqxws1` 现场。这不是预期红态，不能改写为通过。

**根因归类：本卡引入的产品回归，不是回归适配器夹具错误。** [逐项诊断](identity-regression-diagnosis-01.json) 显示，7 个失败测试走的都是默认产品 daemon，`test_host=false`；对应 attempt 的 thread_id 都是空字符串，launch_records 为 0，提交的 attempt/session/fence/spec_rev 与存储记录相符。测试通过 claim 创建的是未绑定原生窗格的 attempt。

本卡的 daemon 却把管理凭据合成为 `thread=operator:<epoch>`、`turn=""` 的 SubmitCaller，再传给全部门禁调用。这不是原生会话身份。submit 的既有合同对无 thread 的 attempt 要求不提供原生 caller，因此正确拒绝了这个虚构身份。panes 没有参与这些失败；只改测试 host 或绕过默认产品路径不能解决根因。

**修复**：管理身份 GateActor 与原生 SubmitCaller 分开传递。daemon 只传实际角色，不制造 thread/turn；真实 worker 仍从其原生会话生成 SubmitCaller。收件箱、停止和问题处置继续使用实际 actor，不能因为分开身份而默认成 user。受控线程适配器只透传管理 actor，并在原来的独立线程边界提供原生 caller。

submit 的 attempt、session、fence、spec_rev、thread、turn 检查区段与失败快照逐字相同，包括无绑定线程时的 `!caller` 限制。没有修改业务断言或放宽原生身份检查。[本次修复 diff](identity-regression-fix.diff) 只比较失败候选之后的三个相关文件，供执行主控审阅。

重生该差异（输出换新文件名）：

```sh
python3 evidence/2026-10-11-batch13/T-078/identity-regression-diff.py --output /tmp/t078-identity-repair.diff
```

修复后，无 CLI 的领域测试仍是 11/11 PASS，结果见 `domain-after-identity-fix-01/`。这不能替代 submit 的真实后台复验。新标签命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-inbox-02
```

脚本重跑领域测试、库客户端、原 8/9/18，任何非预期失败即停。原失败目录不覆盖；真实模型回合仍为 0，不启动 Claude。准备检查见 `preparation-check-06.json`。

## outside-inbox-02：身份修复与回归通过

主控 #37 已审阅 `identity-regression-fix.diff`，认可管理 GateActor 与原生 SubmitCaller 分开，未放松 submit 检查。worker 重新读取原始结果，见 [读回摘要](outside-inbox-02-readback.json)：domain 11/11、inbox-entry 8/8、coop 8、recovery 9、run 18 全部 PASS，failures/errors/skipped 均为 0。本结论只绑定该次源快照，不替后续窗格变更或变基候选背书。

主控 #37 要求单个原始文件超过 5 MiB 时归档到外置盘，压缩不免除此要求。只读核对：outside-inbox-01 无超限文件；outside-inbox-02 的 coop/recovery/run 各有 run.json、test-result.json，共六个。下一份沙箱外脚本先执行归档：原字节复制到 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/outside-inbox-02/` 对应子目录；逐字节读回成功、写出本地摘要和重放信息后，才删除本地原件。失败保留现场，不覆盖归档。当前尚未执行外置盘写入。

```sh
python3 workbench/tests/archive_t078_evidence.py --dry-run --labels outside-inbox-01 outside-inbox-02
```

实际归档命令与上述命令相同，移除 `--dry-run`；仅由执行主控经 `outside-sandbox.sh` 运行。原运行源快照、较小原始文件和失败结果仍留在原目录。

## 窗格运行时：状态层红绿

本阶段的 **Tracer bullet** 继续沿原 Panes／收件箱／PTY 路径推进；没有增加另一套运行时。**Deep modules**：输入顺序、唤醒收据、Esc 和初次放行归 Panes 管，角色权限与实际调用者仍归门禁管。**Ubiquitous language**：queued 只表示排队，写出 paste 和 CR 后才称 delivered；unknown 不重发。

`pane-runtime-red-01` 有四项预期合同失败，`pane-runtime-green-01` 五项通过：补了 wakeThread/readWakeDelivery、用户放行的运行时方法、只写 Esc 的 interruptThread，并把 Esc 后迟到 Stop 的审计改为保持中断；启动表迁移允许主控 attempt 为 null，保留旧行和追加式约束。窗口放行 IPC／按钮尚未接入。

随后用明确屏障暂停第一个输入的登记，复现了三项顺序缺陷：登记期间注入能越过人工草稿，后续 Enter 能越过尚未登记完成的字符，另一窗格的提交能耗尽当前窗格额度。`pane-order-red-01` 三项失败；修正后 `pane-order-green-01` 11/11 PASS。修正为同步登记输入占用，再把身份校验、用户记录和字节写入放入同一串行队列；额度按 launch 计算。Esc 仍可在 paste 与 CR 的间隔取消尚未写出的 CR。

**测试夹具修正**：静态核对发现原状态测试预置的 worker issue 指向 executor，不符合 issue 只能发 triage 的方向。已改成有效 issue → triage、executor disposition → worker；重复唤醒直接重放同一已持久化 entry 给 Panes，测试范围明确为运行时去重。ack 幂等仍由此前领域测试覆盖。没有改产品权限或 `acceptance/test_*.py` 的业务断言。

为避免仅有修改测试后的绿态，使用修正后的同一个测试重新跑已保留的坏版本：

| 产物 | 使用代码 | 结果 |
| --- | --- | --- |
| [runtime-corrected-red-01](runtime-corrected-red-01/results.json) | pane-runtime-red-01 的 panes/store | 8 FAIL、3 PASS；包括未实现唤醒／中断、错误空闲事件、空 attempt 不可存及顺序缺陷 |
| [order-corrected-red-01](order-corrected-red-01/results.json) | pane-order-red-01 的 panes/store | 3 FAIL、8 PASS；人工输入占用、输入次序、每窗格额度 |
| [pane-corrected-green-01](pane-corrected-green-01/results.json) | 当前候选 | 11/11 PASS |

各目录的 `results.json` 保存真实 argv，各用例 JSON 保存字节 spy、事件和输入读回，`sources.tar.gz` 保存该次导入的完整 src 与测试。红态恢复目录写在同名 `*-setup.json`；没有切换或覆盖工作树代码。三组都没有 CLI、PTY、socket、ps、进程信号或 Claude 夹具，不能替代真实进程身份验收。

重跑当前候选（输出须为新目录）：

```sh
node workbench/tests/test_t078_pane_runtime.ts /tmp/t078-pane-state-new
```

重放任一冻结版本时，先把对应 `sources.tar.gz` 解到新的 `/tmp` 目录，在其中的 `workbench/node_modules` 链接本 worktree 已安装的依赖，再运行该副本的 `workbench/tests/test_t078_pane_runtime.ts <新的输出目录>`。不要向共享构建输出建链接。环境依赖版本仍由 workbench/package-lock.json 固定。

## 下一检查点：outside-runtime-red-01

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-runtime-red-01
```

脚本已写好，**尚未运行**。顺序：旧超限文件归档 → 领域测试 → 窗格状态测试 → 扩展后的真实输入入口 → 当前产物超限检查／归档。

运行时测试沿用生产 Electron、daemon、SQLite、node-pty 和进程身份核对，只把供应商进程换成编译到隔离 `/tmp` 的原生字节接收器。先前 Python shebang 接收器不能提供与启动 argv 相同的前台可执行文件身份，因此这里采用原生程序，不放松产品 ps 检查。接收器仅产生最小 Codex 形状的 session/turn 日志；显式 Stop 由它的子进程调用真实 hook CLI，launch token 只留在继承环境中。它不运行 Codex、Claude、Claude 夹具、认证或模型。

入站 issue／stop 是明确标注的持久化夹具输入；实际处置、唤醒与停止调用经过生产凭据和门禁。此阶段在 worker 目标上证明运行时路径，不声称已验证 report → ideation、构思主控凭据或真实两分钟流程。stop 后的 executor ack 会入库；因没有 ideation 接收者，其未送达结果必须保留。

入口检查包含原四项，再加前台进程身份、注入不记用户输入、忙时排队、Stop 后固定唤醒字节、Esc 后迟到 Stop 不放出、窗口用户放行、停止只写 Esc 并记录 executor、关闭窗口期间大段中文粘贴完整写出，共 12 项。**唯一预期红态是 `window_user_release_available`**，因为 UI 入口尚未实现；另 11 项必须通过。非预期失败、设置错误、hook 错误或清理错误即停，不改成红态通过。主控回传后才实现窗口放行并换标签取绿态。

静态准备检查：Python AST、Electron 驱动语法、C 接收器只做 `-fsyntax-only`、shell 语法、diff 空白检查均通过。没有执行新接收器。当前失败方式覆盖情况：同时输入已有屏障反例；IME 只有 P1 合成组合事件；大段输入和关闭期间输入待本次入口运行；重启 unknown 与同 entry 重复唤醒只有状态层证据。二进制输入、请求序号竞争、主控启动参数和三窗格仍待下一阶段，不据此宣称全票完成。

## 主控 #41：运行时红态已确认，窗口放行候选待绿态

[独立读回](outside-runtime-red-01-readback.json) 与主控报告一致：outside-runtime-red-01 退出 0，checkpoint_status=PASS、phase=red；入口 11 PASS，唯一 INCOMPLETE 是 `window_user_release_available`，观察为无按钮、无放行 action。domain 与 pane-state 各 11 项 PASS；启动和清理完成，没有模型回合。

旧超限原件已按主控 #37 要求归档。[六文件归档清单](external-archive-2d13793e60824d17a22dd8fd8d78e22c.json) 逐项记录外置盘路径和字节读回 PASS；本轮产物无超限文件，见 [本轮归档清单](external-archive-585382f5afb04984af859a7f8ecc7aed.json)。仓库保留原运行目录中的摘要、源快照、重放 argv 与外置路径。

窗口放行的候选变更见 [相对红态的差异](window-release.diff)：

- preload 提供无目标参数的 releaseQueue，main 校验原窗口 IPC 来源，沿现有串行队列发送，使用同一窗口凭据、序号与 request_id。
- daemon 只允许窗口凭据调用 window_release，目标取凭据绑定的 launch。核对当前 attempt/session/fence/spec_rev、记录器和中断状态，先追加 `content.action=queue-release` 的用户 action，再调用已有 Panes 放行方法。受管 worker 的人工介入沿原事务派生。
- 按钮只在可输入且中断时启用；请求期间防重复点击，错误沿原输入失败处理，不自动重投。管理 CLI 的初次 release 仍不能解除 Esc 占用。

真实入口断言保持不变。驱动仅增加读取按钮状态的有界等待：产品每秒刷新状态，等按钮启用后点击一次；缺按钮仍立即返回 clicked=false，2.5 秒仍禁用也返回 false。没有模拟成功、直调 Panes 或重复放行。

下一命令（尚未运行，按任务卡交主控在沙箱外执行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-runtime-green-01
```

使用同一运行器的 green 模式，要求原 12 项全部 PASS；任何异常停止保留现场。为节约额度，本轮不重复已通过且无相关改动的 8/9/18，也不启动额外模型审查；最终候选和变基后复验要求仍保留。Claude／Claude 夹具继续不运行。

准备检查见 `preparation-check-08.json` 与 `preparation-check-09.json`。08 的额外 TSX 探针误引用未安装的 esbuild，原失败保留；09 根据本地 Vite 公开类型定义，改用实际构建依赖的 transformWithOxc，仅在内存中转换 TSX，不写构建产物。其结果为 PASS。其余 Node／shell／Python 语法与 diff 检查通过，project-map status 为 0 problems／0 stale，仓库证据无 >5 MiB 文件；真正 Electron 构建与绿态仍待主控运行。

## 主控 #42：窗口放行绿态通过，补输入失败方式

[读回记录](outside-runtime-green-01-readback.json) 确认入口 12/12、pane-state 11/11、domain 11/11 PASS；窗口放行有且只有一次用户 action，实际接收器收到随后提交。启动和清理完成，真实模型回合为 0，没有超限文件。这仍是一个 worker 窗格及确定性接收器，不是三窗格或 Claude 验收。

下一命令（尚未运行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-input-red-01
```

同一运行器新增 input-failures 范围，只跑原四项输入合同和七项失败方式检查，不重复 domain、pane-state 或 8/9/18。总共 11 项，预期只有下列三项失败；任何其他失败、设置或清理错误均停止：

- `composition_holds_injection`：组合输入已开始而尚未产生 onData 时，上一回合 Stop 不能导致后台提示混入。使用公开 composition 事件和同一窗口队列的空观察作为屏障，空观察本身不写字节或用户输入。当前前端尚未向后台报告组合输入占用。
- `request_id_reuse_is_not_written`：同一窗口重用 request_id、换序号和正文，必须拒绝第二次写入；不能只让用户输入表去重，却仍写 PTY。
- `binary_mouse_bytes_and_action`：真实 Electron 鼠标事件经 xterm 的公开 onBinary，送入固定网格第 131 列第 7 行；左键按下／抬起的独立预期字节为 `1b5b4d20a3271b5b4d23a327`，其中 0xa3 不得按 UTF-8 扩展。记录为两个二进制用户 action，保存原始字节。当前 renderer 明确拒绝该输入通路，产品尚未修改。

另四项检查为：组合输入完成后中文只记录一次；关闭窗口后旧凭据不能输入；人为使夹具库的输入 INSERT 失败时，记录器必须报失败且不写 PTY；显式冷重启后历史窗格为 unknown，旧窗口／旧管理凭据被拒，不接管或重放旧 PTY。故障触发器只写入本次创建的隔离 SQLite，之后删除该触发器；重启是指定场景，不是异常后自动重试。

组合输入使用合成 DOM 事件，不能据此宣称已验证 macOS 系统输入法。鼠标协议根据安装的 xterm 公开编码实现核对，不读私有字段，也不手工触发 onBinary。原生接收器只按测试文件请求输出 DECSET 1000，不调用供应商 CLI 或模型。

[准备检查 10](preparation-check-10.json) 保存 Python AST、驱动语法、C 语法、shell、diff 与 project-map status 结果。产品 src/app 与 outside-runtime-green-01 源快照逐字节一致；本轮只准备新红态，没有提前修复这三项行为。脚本回传后再修产品并用同一合同取绿态。

其余未完成项明确保留：worker 的库客户端还须接上已有 Stop 文件转交通路并证明角色权限；主控 Claude 参数／启动记录骨架尚未完成；主控凭据、三窗格及 Claude hook 的运行验证受用户决定约束，仍待真实 Claude 复核。非 Claude 候选完成后才做最终 8/9/18、变基后复验及一次干净上下文只读审查，不复用旧候选通过结论。

## 主控 #45：三项输入红态已确认，修复待绿态

[读回记录](outside-input-red-01-readback.json) 与主控报告一致：11 项中恰好三项预期失败，其余 8 项通过；启动和清理完成、模型回合为 0。原始观察分别是：组合输入期间队列已取出且 writing=true；重用请求号后的 FIRST_ONLY 与 MUST_NOT_WRITE 都到达 PTY；二进制鼠标字节和对应 action 均缺失。原失败目录保持不变。

候选的五文件产品差异见 [input-failure-fixes.diff](input-failure-fixes.diff)：

1. renderer 在 xterm 公开 textarea 的 compositionstart 上通知 main；通知沿原窗口凭据和串行发送队列进入后台。Panes 同步保留用户草稿占用，再记录 terminal_composition_started；没有已提交文本，因此不生成用户输入或介入。组合结束／取消不猜测 CLI 行已清空，仍须用户提交或 Esc 后明确放行。
2. 每个有效窗口保存已接纳 request_id。后台在第一个 await 前占用序号和请求号并追加接纳事件；重复请求拒绝，后完成的请求不再回写旧序号。用户输入去重键同时带 window_id，避免不同窗口的相同请求号互相掩盖记录。重启后旧窗口凭据失效，不能重放旧请求。
3. 现有 input 接口明确区分 utf8 与 binary，前后台都校验字节范围与大小。binary 在同一 Panes 写入队列中转换为 Buffer 后交给 node-pty，记录保存 base64 原字节的 action。鼠标协议里的控制字节不当作 Enter／Esc，也不制造文字草稿。node-pty 的公开类型和已安装实现均支持 Buffer，没有新增依赖或另起传输路径。

相关状态回归 [pane-input-fixes-green-01](pane-input-fixes-green-01/results.json) 11/11 PASS。这只是状态／存储层检查，没有真实进程身份验证。静态检查见 [preparation-check-11.json](preparation-check-11.json)：Node、Vite TSX、Python AST、shell、diff 均通过，project-map 0 problems／0 stale，证据无 >5 MiB 文件。入口断言未改，不把这些检查称为真实入口绿态。

下一命令（尚未运行，按任务卡交主控执行后停下）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-input-green-01
```

green 模式要求同一组 11 项全部 PASS。没有重跑无关回归或启动 Claude／Claude 夹具；系统输入法、主控和剩余交付项的限制继续保留。最终候选 8/9/18、变基后复验及一次独立审查尚未执行。

## 主控 #46 后：输入绿态已读回，冻结边界待明确

[输入绿态读回](outside-input-green-01-readback.json) 确认 11/11 PASS、清理完成、模型回合为 0。主控提及的 #44 经只读派发记录核对属于 T-077；当前仍有 worker 库客户端认证入口和 Claude 参数／记录静态骨架两项非 Claude 缺口。已提出范围澄清，详见 [收尾问题](scope-closeout-question.md)。不把这两项转写成仅等待真实 Claude 验证。

最终验证运行器已准备 --final 和 --identity-file 参数，尚未运行。冻结、Git 提交、变基及独立审查均未执行；待明确本轮是补齐原卡还是按 INCOMPLETE 切出当前部分。最终运行先要求候选已提交并基于 main，再跑每组一次，避免先验收后因变基重复执行 8/9/18。prepare_daemon_mutants 新增 task 参数，避免新证据借用旧 T-075 身份；原断言未变。

## 主控 #49：按原卡补齐，静态骨架红绿与 worker 入口红态准备

[范围答复](controller-scope-answer-49.md) 已留档：不收缩范围，先补齐两个非 Claude 缺口，再提交 → 变基 → 最终验证 → 一次独立审查。当前已恢复实施；blocking issue 本身仍留给构思主控处置，没有自行关闭。

**静态启动骨架**：`controller-plan-red-01` 两项失败，原因是准备入口不存在；新增 `Panes.prepareControllerLaunch` 与同一管理 CLI 的 `controller_prepare` 后，`controller-plan-green-01` 两项通过。两个角色分别构造 `--session-id`、`--model`、`--effort`、`--settings`，连同角色卡、版本引用、项目／任务和代码版本追加入库。记录为 prepared、attempt=null、CLI 版本 unknown，生命周期 not_started，标注“待真实 Claude 复核”；重启不把准备记录冒充已运行窗格。非法 preset 和认证环境混入 settings 被拒，旧记录不变。

静态检查没有启动 Claude、假 Claude 服务、hook、PTY 或子进程，不读写全局配置，也不签发主控运行凭据。相同代码在下一轮还会从真实后台的 controller_prepare 入口构造两条记录；对应的 CLI 路径故意不存在，不会执行。此骨架不是可运行的主控 attach，也不是三窗格验收。

```sh
node workbench/tests/test_t078_controller_plan.ts /tmp/t078-controller-plan-new
```

红绿目录均保存结果、argv、源文件及库读回；既有失败结果不覆盖。

**worker 收件箱红态**：扩展已有原生字节接收器，让它的 Node 子进程调用真实 `workbench/bin/inbox`。子进程继承由产品后台签发的 worker launch/token/request_dir，断言没有 operator 凭据；token 值不进入证据。只有任务创建、预置入站数据与静态准备由测试管理端完成，worker 的 send/list/ack/ready 不借用该管理身份。

七次初始调用覆盖 issue 的实际 sender、伪造 from 的 assign、伪造 role 的 list、本人条目两次 ack、worker ready、他人条目的 ack；随后撤销 attempt，再由同一 worker 凭据提交新 issue，要求 Stop 转交时拒绝。列表断言保留一个始终未确认的本人条目，避免空列表蒙混；重复 ack 必须有非空且相同的 id、库里只有一条；Stop 的实际回执字节到达 worker，旧 Stop 不重复送达。入站处置是明确标注的持久化夹具输入，不声称由真实主控发送。

下一命令（尚未运行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-worker-inbox-red-01
```

共 14 项：原四项输入和一项静态准备必须 PASS；九项 worker 入口合同预期为 INCOMPLETE，因为 worker CLI 目前仍禁止 inbox_*，本轮没有提前改这条业务路径。任何其他失败、客户端驱动异常、Stop 异常或清理错误均停下。这里“真实 worker 入口”指应用实际签发的 worker 身份、实际客户端／后台／PTY；接收器只模拟原生会话日志，不是真实 Codex 模型回合。

[准备检查 12](preparation-check-12.json) 中 Python AST、JS／TS、C 语法、Vite TSX、shell 和 diff 检查均通过；project-map 0 problems／0 stale，证据无 >5 MiB 文件。只运行了静态构造／存储测试；worker 入口待主控沙箱外执行。之后仍按先红后绿修复，最终 --final 路径已包含这个入口与静态构造检查。

夹具元数据修正：共用启动配置此前沿用 Python 接收器的“receiver invokes no hooks”说明，但原生接收器会按测试文件显式调用 Stop 的 hook CLI。现在按接收器种类分别记录；不修改历史原件，也不改变断言或授权边界。这些始终是合成 Stop，经本卡沙箱外脚本执行，不是供应商 CLI 的 hook 回合。

## 主控 #55：更正红态分类，worker 转交通路修复待绿态

[分类核对](worker-red-classification-01.json) 显示：初始七次客户端调用和撤销后的调用都在 CLI 返回 `worker_command_forbidden`，没有进入后台角色规则。只有“worker 客户端可转交命令”取得真实入口的合同红态；其他八项是下游不可达。特别是 assign、ready、他人 ack、撤销后的请求，没有证明对应业务规则曾被违反。此前将九个 INCOMPLETE 统称“合同红态”的表述在此更正；原始输出保持不变。

修复见 [worker-inbox-fix.diff](worker-inbox-fix.diff)：cli.ts 让 inbox_send/list/ack/ready 使用原来的 worker 请求文件；relay.ts 保留完整身份字段核对，只增加四种命令的字段白名单。后台用本次 Stop 的已认证 native caller 执行；对 inbox caller 的每次原生身份检查，再核对当前 attempt/session/fence/spec_rev 和回收状态。submit 的身份检查未改，原有角色规则未放宽。用户参数 from/role 不能选择实际调用者。

绿态必须同时证明真实 worker 的允许行为和以下具体拒绝：

| 规则 | 候选必须返回 | 单处变异体必须造成的可观察违反 |
| --- | --- | --- |
| worker 不能写 assign | invalid_direction，库无 assign | 绕过发送者角色条件后，库里实际出现 from=worker 的 assign |
| worker 不能查 ready | controller_required | 绕过 ready 的角色条件后，实际返回夹具 W-READY |
| 不能 ack 他人条目 | recipient_required，无该 ack | 绕过收件人条件后，库里实际出现 worker 对 foreign-message 的 ack |
| 撤销后不能继续写入 | stale_attempt，无新 issue | 绕过当前 attempt 条件后，库里实际出现撤销后的 issue |

为避免 ready 变异体只是换了另一种拒绝错误，测试在独立传入的夹具仓库里增加有效 W-READY 文件，不从后台返回值推导种子目录。四个变异体分别复制完整后台源码，只改一个检查点，复用已通过候选的前端构建；实际从变异体 CLI 启动该后台，并从启动 argv 核对加载路径。评判同时要求：恰好对应一项断言失败、其余 13 项通过、无设置／清理错误，并读回实际越权结果或库行。缺行、缺数据、另一个错误码或进程崩溃都不能算反例通过。

一次静态准备错误已记录在 `mutation-preparation-error-01.json`：ready 的角色检查文本在另一个历史处置分支也出现，初次匹配数为 2。准备阶段在任何变异运行前拒绝了这个模式，随后把精确匹配限定到 inbox_ready 分支；现在四个位置都恰好匹配一次。没有改产品权限来迎合探针，也没有放宽业务断言。

下一命令（尚未运行）：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-worker-inbox-green-01
```

顺序为候选 14/14 → assign 变异体 → ready 变异体 → foreign-ack 变异体 → revoked 变异体 → 超限证据归档；任何非预期失败停止。四项反例结果单列 `worker-rule-verdicts.json`，原变异测试的 INCOMPLETE 与退出 1 原样保存。源码在整个检查点前后逐字节核对；前端只构建一次。最终 --final 路径也已接入这四个反例。

[准备检查 13](preparation-check-13.json) 仅证明 Python／Node／shell 语法、单处变异位置、diff 和项目状态检查通过；没有在沙箱内运行这些进程检查，也没有重跑 8/9/18、启动 Claude 或 Claude 夹具。当前仍为 INCOMPLETE。

## 主控 #63：worker 绿态与反例通过，冻结提交和变基待执行

本节的代提交方案未执行，已被主控 #64 否决；更正及当前命令见下一节。

[读回记录](worker-green-readback-01.json) 确认候选 14/14 PASS；assign、ready、foreign-ack、revoked 四个单规则变异体均只触发对应检查失败，启动 argv 确认加载了变异后台，独立读回确认被禁止的结果真实发生。不是以错误码变化、空结果或设置失败冒充反例。本轮没有真实模型回合。

执行顺序按 #49：冻结提交 → 变基到最新 main → 一次最终完成条件与 8/9/18、CAS、三项原业务变异反例（另保留四项权限反例）→ 一次只读独立审查。当前 main 包含 T-076-1 的原生身份、run 超时、后台收尾和状态一致性修复；不会用本卡旧实现覆盖它们。

Git 公共元数据位于 `/Users/luckye/Documents/Code/a2a/.git`，当前 worker 沙箱只读。下一份脚本因此只交给主控执行 Git 写入：git add 与 git commit 是分别执行的独立命令，沿用派发时的会话 Git 钩子生成并核对全部尾注，不修改全局或仓库 Git 配置。只暂存 workbench、本卡证据和本 ticket 的 Resolution；两个未跟踪的收件箱条目保持原样，不纳入本次提交。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-freeze-rebase-01
```

脚本尚未执行。它先核对分支、起点、空暂存区、证据大小和 worker 启动身份，提交冻结候选，随后只执行 `git -C /Users/luckye/Documents/Code/a2a-wt-t078 rebase main`。冲突时保留 Git 现场与 stdout/stderr，不 abort、不自动选一方、不跑最终测试；由 worker 解决、主控 continue。成功后也先回读变基结果，再运行已经准备的 --final 路径，避免用变基前的测试替变基后候选背书。

`freeze-plan.json` 和 `worker-evidence-identity.json` 保存本 worker 的 task/attempt/session/launch/native session 来源。此前部分历史运行将未核对的外层身份写为 null，原记录不重写；最终运行使用现在已从会话环境与派发启动记录核对的身份。Herdr 分发没有提供工作台门禁 fence，仍为 null，不借用测试夹具的 fence。

真实 Claude 的运行与主控接线仍未完成：静态 argv/settings/角色卡记录不等于运行过 CLI，也不等于获得主控凭据或三窗格验收。全部等待 needs-decision 20261011T101958Z 的答复，保持“待真实 Claude 复核”。当前结论仍为 INCOMPLETE，ticket open，待主控关闭。

## 主控 #64：提交来源更正，worker 自行冻结

主控没有执行 outside-freeze-rebase-01：在执行主控的会话中恢复 worker 身份再提交，会把实际提交者错记成 worker。该反馈是对未执行方案的否决，没有产生提交或测试结果。身份恢复代码及 `freeze-plan.json` 的环境导出包已删除；没有生成过 `freeze-env-*.sh`，也不将此类文件纳入提交。

当前由 worker 在自己的会话中执行以下独立命令，提交消息文件只写正文，尾注交给现有会话 hook 生成。`freeze_candidate.py` 只读取当前环境与启动记录核对身份，保存暂存范围及提交尾注检查；不设置环境、不写 Git 配置。原始失败输出和历史源码快照保持原字节，空白检查只针对 workbench 和 ticket。

```sh
python3 evidence/2026-10-11-batch13/T-078/freeze_candidate.py prepare outside-rebase-01
git add -- workbench evidence/2026-10-11-batch13/T-078 .project-map/tickets/T-078-controllers-in-workbench.md
python3 evidence/2026-10-11-batch13/T-078/freeze_candidate.py staged outside-rebase-01
git commit -F /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/candidate-commit-message.txt
python3 evidence/2026-10-11-batch13/T-078/freeze_candidate.py committed outside-rebase-01
```

主控下一步只执行变基及结果检查，不包含 add、commit、source 或身份恢复：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-rebase-01
```

变基冲突保留现场，由 worker 解决后交主控 continue；成功时核对 main 已在候选历史内、尾注仍保持原 worker 来源。最终完成条件、8/9/18、CAS、原业务反例和独立审查仍待变基后执行。整体保持 INCOMPLETE；本次更正没有运行模型或 Claude 夹具。

## 主控 #67、#68：变基完成，最终检查待沙箱外执行

worker 原提交 `b5ed880b8ad0461786a8aee7f4e0a18ea42752a3` 已由主控变基到 main `532c51f4cc12352bb7cf545ce1e5f824d68bdc4a`。两个冲突由 worker 解决并独立暂存，再由主控 continue；新提交为 `b3fb998cf48574821c39440ece3f9ff897f26cf9`。尾注保持原 worker 会话、模型与 launch，没有转交或恢复身份环境。原变基失败输出仍在 outside-rebase-01。

[冲突处理记录](rebase-resolution-01/RESOLUTION.md) 列出 README 和 runner 双方行为的保留方式，及 T-076-1 的稳定身份、原生 submit、beginShutdown、在途请求收尾核对。48 项静态／参数检查通过；首轮检查器误判 `/tmp` 别名的结果及更正分别保留，不当作产品红态。

[最终阶段说明](FINAL-STAGE.md) 固定上述提交，一次运行领域 11、管理客户端 8、窗格状态 11、静态骨架 2、运行时入口 12、输入失败方式 11、worker 入口 14 与四项权限反例，随后原 8/9/18、CAS 1 和 fence／CAS／lock 三项原业务反例，最后按单文件大小外置归档。前端只构建一次。原业务断言及 workbench 源码不再修改。

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-final-01
```

本阶段尚未执行。非预期失败停止、原件保留、不自动重跑；通过后先读回，随后进行一次新上下文只读独立审查。真实 Claude 及其夹具仍不运行。整票状态继续为 INCOMPLETE，不能把静态启动记录或逻辑主控夹具写成真实主控验收。

## 最终验收与独立审查（主控 #70）

执行主控已完成 outside-final-01，exit 0、checkpoint_status=PASS，候选为 `b3fb998cf48574821c39440ece3f9ff897f26cf9`。worker 的 [27 项读回检查](final-readback-01.json) 确认原始结果、外置回归原件、权限变异体的持久化行及归档状态；不是只读取顶层 PASS。所有原 `acceptance/test_*.py` 业务断言未改。测试中真实供应商模型回合为 0。

| 完成条件／检查组 | 最终结果与边界 |
| --- | --- |
| Electron 输入、来源与人工介入 | runtime-entry 12/12、input-entry 11/11；实际窗口、后台、SQLite、node-pty 与字节接收器。中文到达 PTY，注入不记用户输入，worker 的人工输入产生介入 |
| 忙闲、唤醒与 Esc 放行 | pane-state 11/11，加 runtime-entry 的排队、送达及窗口放行；匹配 Stop 才结束回合，Esc 后不自动放行，用户放行有 action。逻辑主控／合成原生日志不证明真实 Claude 主控 |
| 收件箱与角色权限 | domain 11/11、inbox-entry 8/8、worker-inbox 14/14；worker 使用实际 launch 身份，不用 operator 代替。assign、ready、他人 ack、撤销分别由对应规则拒绝；无接收者保留 undelivered |
| 紧急停止 | domain 覆盖 stop/ack、120 秒前拒绝及超时后只中断；runtime-entry 实际凭据调用只写 Esc，调用者来自认证身份。两分钟与构思主控仍为受控时钟／逻辑角色证据，未宣称实际 Claude 链路通过 |
| Claude 启动静态骨架 | controller-plan 2/2，入口另验证 controller_prepare；四项参数、角色卡与记录持久化，状态 prepared，无进程／主控凭据。待真实 Claude 复核 |
| 原回归与 CAS | coop 8、recovery 9、run 18、cas 1；failures/errors/skipped 均 0 |
| 权限业务反例 | 四个单规则变异体各自只让对应检查失败，并实际产生禁止的结果。旧 worker_command_forbidden 不作为这些规则的红态 |
| 原业务反例 | fence、CAS、lock 指定原测试均退出 1，errors/skipped 为 0；实际出现错 fence 被接受、外部引用被覆盖、并发 verify 进入。反例成立，原失败结果保持 INCOMPLETE |
| 独立审查 | 一次 fresh-context 只读审查：本卡非 Claude 范围局部 PASS，未确认阻断问题；整票 INCOMPLETE。审查未写候选、submit 或集成 |

失败方式逐条对应：

| 失败方式 | 处理与证据 |
| --- | --- |
| 用户输入与注入同时发生 | 输入接纳先占用窗格，串行写入；待记录输入和草稿阻止注入，pane-state 的屏障反例覆盖按键不可重排；runtime-entry 读回实际注入字节 |
| 中文组合输入 | compositionstart 经窗口凭据登记占用，已提交文本只记录／写入一次；input-entry 通过。使用合成事件，真实系统输入法未验证 |
| 大段粘贴 | runtime-entry 的原始 PTY 记录含完整 51,612 字节长粘贴后缀，关闭窗口先等已接纳输入收尾 |
| 窗口关闭期间输入 | 已接纳请求按序收尾，关闭后凭据失效；runtime-entry 与 input-entry 分别覆盖 |
| 后台重启忙闲未知 | 保留历史、标 unknown，不重放注入、不接管旧进程，旧窗口凭据拒绝；pane-state 与 input-entry 覆盖 |
| 同一唤醒重复送达 | inbox entry 与派发绑定，重复 Stop／ack 不增加已送字节或新 ack；pane-state 和 worker-inbox 覆盖 |
| 空输入、重复请求号、二进制鼠标输入 | 空事件仅观察；复用请求号拒绝；二进制字节不经 UTF-8 扩展，也不当普通文字草稿；input-entry 与原始字节读回覆盖 |
| 记录器失败 | 先记录再写 PTY；失败关闭写入，不重试或重放；pane-state 与 input-entry 覆盖 |

完整重放命令见 [FINAL-STAGE](FINAL-STAGE.md)；需新的 label，且脚本核对冻结代码提交，不能把修改后源码沿用为同一候选。仅重新读回已有证据：

```sh
python3 -B evidence/2026-10-11-batch13/T-078/read_final_checkpoint.py --output evidence/2026-10-11-batch13/T-078/final-readback-replay-01.json
```

6 个超过 5 MiB 的原件已归档至 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/outside-final-01/`，逐字节读回后移出仓库。库内各 run/test-result 摘要保留重放 argv 和原件路径；[归档清单](external-archive-26fbebf6628b47c99f307a1fd2f480f1.json) 完整列出，历史失败未覆盖。

独立审查由会话内独立 agent `/root/t078_independent_review` 执行，`fork_turns=none`，未继承聊天，输入为冻结候选、任务契约与原始证据；[请求配置](independent-review-request-01.json) 指定 explorer、gpt-6-astra、xhigh。工具没有 Fast 参数，审查上下文也无法核验具体模型编号／强度／实际服务档位，故这些只记录为请求值。审查逐字比对源码快照、读取 SQLite 内存副本与外置原件，没有新运行供应商 CLI 或运行时测试。完整返回原文保存在 [审查报告](independent-review-01.md)。没有确认的修复项，因此未追加产品修复或第二次审查。

本次收尾提交只纳入本卡证据和 ticket Resolution；workbench 仍与已验收、已审查的代码提交一致。ticket 保持 open、待主控关闭；不 push，不切换日常文件版 inbox。真实 Claude、主控接线、实际互相唤醒及三窗格未完成，继续等待 needs-decision `20261011T101958Z`。

## T-078-2 材料 08c（主控 #109）

上节为 T-078-1 收尾时点；用户随后选择“假服务为主，真登录复核 2～3 回合”，T-078-2 已进入逐次审批的协议探针。当前由 s13-t078s 续接原生会话，gpt-6.1-sol／xhigh／default；未把旧通过结论外推到新代码。完整阶段约束见 [PLAN-2](PLAN-2.md) 与 [P1-APPROVAL-08C](P1-APPROVAL-08C.md)。真登录尚未启动。

08b 的实际 CLI 已由主控启动并清理，无真实模型回合。ArrowUp 到 Auto、ArrowDown 到 Dark 的批准与后台事件一致，Enter 却被拒；拒绝前后 PTY 输出均为 3,906 字节，原始失败保留。根因是 `selected_label` 的目标项语义与门禁、旧域测试的按键前光标语义不一致。[只读诊断](theme-diagnosis-08c.json) 保存字段、原文字节与退出读回；cleanup PASS 仅证明该实例的记录进程已退出。

修复单独提交 `95b69e04aac6f20d3a18e1e42a5c2494e35f46c3`。新域探针从真实批准文件与屏幕原字节重放：起点拒绝正确序列，同时接受颠倒标签；[红态](theme-confirmation-red-08c/results.json) 原样保留。修复后要求连续登记目标 Auto → Dark，再单独批准 Enter 确认 Dark；[绿态](theme-confirmation-green-08c/results.json) 4/4，默认 Enter、颠倒标签与缺少 Auto 导航仍拒绝；[原门禁检查](screen-key-green-08c/results.json) 4/4，同屏去重与一次信任限制保留。此为域夹具，合成 PTY／进程身份，没有实际选择菜单或证明真实 hooks。

08b launch 的 13 字节即时截取没有形成首屏。08c 改为只记录进程启动；首屏由另批的 screen 阶段读回，不加读屏规则、重试或自动按键。新实例为 `/private/tmp/t078-2-p1-08c-1uy5wegk`；launch/session/thread、准确 argv/env、端口启动时分配、隔离 HOME 与 hooks 等绑定见材料。每屏目标项与批准均入证据，真登录在用户 HOME 出现任何引导屏一律停下交主控、不按键。

08c 静态准备 PASS，实际 launch 未执行；一回合主请求、真实 UserPromptSubmit／Stop、busy／完成仍 INCOMPLETE。Esc 放行、二次送达、紧急停止继续留材料 09，不缩减整票验收。审批／域探针／静态检查重放命令见 P1-APPROVAL-08C；整体保持 INCOMPLETE、open、待主控关闭。本轮 worker 启动 CLI／API／模型均为 0。

## T-078-2 材料 08d（主控 #111～112）

上段为 08c 交审批时点。主控之后实跑证明主题确认修复生效，三步写 PTY，停在 Security notes，未确认提示；cleanup PASS，无残留、真实模型 0。原件保留在 p1-materials-08c。构思主控批准隔离实例中确认这一逐字相同的固定安全提示，真登录引导的停止条件不变。

新用途 onboarding-notice 仅允许 Enter，仍使用后台凭据与逐屏原字节批准。自已登记的主题确认快照后取全部提示段，按 [固定规则](NOTICE-COMPARISON-08D.md) 去终端控制序列，与 08c 固定文字全串相等；不同即拒。不是语义分类，不自动通过其他提示；同屏去重、本 notice 在 launch 限一次，原文／按键／批准留证。产品独立提交 `f14d63df7f6f5131ea143ab37a5878ec7ecb28e8`。

[红态](notice-red-08d/results.json) 是起点整用途不可达，拒绝 `invalid_screen_key`，没有额外 CR；没有把不可达的下游规则算业务红态。[最终域绿态](notice-green-final-08d/results.json) 12/12，原主题／屏幕域检查各 4/4。[单规则变异体](notice-text-mutant-08d/counterexample.json) 去掉文字比较，改字、追加提示、可打印空格变化与不完整控制序列各自实际写出额外 CR；四项失败，其余通过。全部为合成 PTY／进程身份，未发送真实菜单键。

08d 新实例 `/private/tmp/t078-2-p1-08d-ohyh5win`，51 文件源码绑定、准确 argv/env 与逐阶段审批见 [P1-APPROVAL-08D](P1-APPROVAL-08D.md)；本轮仅静态生成，CLI／API／模型启动均为 0，launch 尚未批准运行。官方文档支持后续可能的目录信任／认证／MCP 类别，不能保证 2.1.296 的完整逐屏顺序；[官方依据与未知](ONBOARDING-AHEAD-08D.md) 供审批比对。

整票仍 INCOMPLETE、open、待主控关闭。实际 notice、单回合主请求及真实 hooks 仍待 08d；完整 Esc／二次唤醒／紧急停止保留 09，真登录尚未启动。所有重放命令与原件路径见本节链接，旧结果不替当前候选背书。

## T-078-2 材料 08e（主控 #113）

上段是 08d 交审批时点。主控随后实跑通过主题及固定 Security notes Enter；下一屏为默认 No 的目录信任，没有数字标签，未发 Digit1，cleanup PASS，无残留、真实模型 0。实际原件和逐屏批准已保留，不能将旧 Digit1 域正例当作这份菜单的真实依据。

workspace-trust 改为单独批准 ArrowDown 到 `Yes, I trust this folder` → 新原文读回 → 单独批准 Enter。Enter 要求前一条意图为同窗格／launch 的该用途 ArrowDown 到 Yes；确认快照须延续该导航原文，当前原字节仍须与主控批准相等。整个 launch 只允许一次信任确认；默认 Enter、Digit1、其他目标及重复确认拒绝。产品按键映射与 runner 已删除 Digit1，没有并行路径；其他用途与真登录停止条件不变。修复单独提交 `ab997f4d2ea8f4719e6989409c1bebb5835099c1`。

[红态](trust-selection-red-02-08e/results.json) 使用 08d 实际默认屏与前置主题／notice 事件：正确 ArrowDown 不可达，旧 Digit1 却真实写出 `1`。首次未重放前置事件的红态也保留；下游 Enter／次数等不可达结果不冒充业务红态。[信任域绿态](trust-selection-green-08e/results.json) 10/10，原屏幕／主题／notice 检查 4/4、4/4、12/12。Yes 的读回帧为合成输入，真实选择仍待运行。[三项变异反例](P1-APPROVAL-08E.md) 分别真实写出默认 No 屏 CR、两次确认 CR 和不延续导航原文的 CR，按对应业务规则失败。

新实例 `/private/tmp/t078-2-p1-08e-8k1yyjw5`，52 文件源码绑定及准确 argv/env 见 [P1-APPROVAL-08E](P1-APPROVAL-08E.md)。静态准备 PASS，worker CLI／API／模型启动和真实按键均为 0，实际 launch 未执行。整票仍 INCOMPLETE、open、待主控关闭；实际信任、主回合、真实 hooks、09 的完整链路与真登录均未完成。材料交 launch 审批后停止，工作树整理提交，不 push。

## 08e 单回合可行性实测（主控 #116）

上节是交审批时点。执行主控随后完成 08e：主题三键、固定 Security notes、信任 ArrowDown→Yes→新屏读回→单独 Enter 均生效，实际 CLI 进入主提示符。continue 与 cleanup PASS；CLI PID 11046 已确认退出，无残留。实际供应商模型回合为 0，使用固定 Claude Code 2.1.296 和本地脚本化 Messages API。

worker 的 [原件读回](p1-readback-08e.json) 验证了顶层状态之外的具体证据：executor 凭据登记 dispatch `c6c8f8ae-718b-47fe-b9e0-f3dc3753fa00`，paste＋独立 CR 提交；提交中为 busy、active 绑定该 dispatch；完成后 idle、active=null。实际 UserPromptSubmit／Stop hook 原始 stdin 与后台 hook_received 原字节一致、均 exit 0，session 一致，两者 `prompt_id=fe9a0b3a-87c7-4377-a420-c4ebb453c497` 相同。实际事件顺序 turn_start_signal → turn_end_signal → pane_idle 各一次；假 API 仅一个主 Messages 请求，stream=true、model=claude-haiku-5-5，user text 包含完整登记输入；Stop 的回复为 P1_ACK 加本次 nonce。已知会话 transcript 中有一次 stop_hook_summary，hookCount=1。

原始 hook 的小份副本留在 [hook-payloads-08e](hook-payloads-08e/UserPromptSubmit.stdin.bin)；副本仅来自本隔离夹具归档，不读或复制用户认证。UserPromptSubmit 与 Stop 的 finished.json 及原始 Stop stdin 同目录保存，供 09 按实际字段建立跨回合关联，不能把同一 session 或时间戳自行当作第二回合身份。

cleanup/fixture.tar.gz 原始单文件 8,103,787 字节，执行主控已外置到 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-08e/cleanup/fixture.tar.gz`；[归档清单](external-archive-73249ada8f364b0d8abea0bad2fcf29a.json) 记录字节读回 PASS、移出本地原件和重放摘要路径。worker 核对尺寸及明确成员的一致性，没有在原件已移出的情况下冒称再次独立比对整个归档。仓库无 >5 MiB 文件，保留全部运行命令、批准、原文、summary 和归档 manifest。

**结论仅为单回合可行性 PASS**，绑定变基前产品 `ab997f4d2ea8f4719e6989409c1bebb5835099c1`／材料提交 `e5768e54d25a1fbc85d4dfd91b0bc5017c4ec054`。不证明 Esc／第二回合／紧急停止、双主控协作或真模型判断。T-077 合入后再变基，材料重新生成并完整重跑，旧 PASS 不替新 main 上的候选背书；T-078 仍 INCOMPLETE、open、待主控关闭。

用户处置条目 `20261014T035805Z-user-disposition-001` 已按主控 #117 单独提交 `f3b33316`，提交仅含构思主控抄录的该条目，certainty=relayed；关闭 blocking issue 来自用户，不是 worker 决定。真登录阶段真实 hook 触发仍在本票验收内。

只重新读回原件，不启动服务：

```sh
python3 -B evidence/2026-10-11-batch13/T-078/read_p1_08e.py --output /绝对路径/新读回报告.json --raw-dir /绝对路径/新小份hook目录
```

原件生成命令仍在 08e 各阶段 commands.jsonl 和 P1-APPROVAL-08E；重新运行需新实例／绑定／批准，不覆盖这些已完成结果。

## 材料 09 的准备（未运行）

按已说明的分场景顺序准备 [PLAN-09](PLAN-09.md)：09A 为一个真实 CLI 的 Esc 释放／第二 nonce，09B 为两个实际角色 stop→执行→ack，09C 为真实 120 秒无 ack 后只中断。分阶段偏好暂未收到补充回复，使用推荐顺序；不是启动批准，不缩减双主控／紧急停止验收。本次仅冻结 09A，B/C 的 Claude inbox 转交与实际角色工具调用仍未启用，不冒称已完成材料或运行。

产品候选 `5510ee72134fc7a8c08d37d03773adc96605debf`：按 08e 实际 prompt_id 关联 Claude 当前提交，Esc 写出后登记退休并释放 active；仍 busy／interrupted，队列只在窗口用户放行后送出。旧 Stop 不能结束第二回合，异步 transfer 返回也核对当前关联。窗口 nullable 主控按任务版本、当前 launch／native session 和真实 leader 检查，worker attempt 边界保留；显式 2 回合预算，默认 1，其他值拒绝。fake API 两个声明请求并发，第一个观察 peer 取消、第二个独立响应，不伪造 hook、CLI 历史或后台状态。

[回合红态](claude-epochs-red-09/results.json) 保存 Esc 已写却 active 不清、旧 Stop 清掉当前关联及单回合限制的具体失败；[窗口红态](controller-window-red-09/results.json) 由生产 assertCurrent 原闭包复现有效 nullable 主控被拒 stale_attempt；[第二请求红态](fake-two-requests-red-09/results.json) 生产 Handler 内存 IO 返回 200／400；[预算红态](two-turn-profile-red-09/results.json) 用起点模块证明忽略显式预算。均为域／参数／内存 IO，不是实际窗口或网络实测。

最新域／参数／内存 IO 7＋5＋3＋1 项通过；原单回合 signal/profile 3＋3 通过；原菜单／主题／notice／信任 30 项通过。四项有效坏变异见 [09 审批材料](P2-APPROVAL-09.md)，均触发对应违约。首次只删入口 Stop 匹配的变异仍被后续检查挡住，原件保留、标 INCOMPLETE／无效变异，不计反例；编辑工具两次未应用的 patch 也不算产品红态，已按实际内容修正。

09A 新实例 `/private/tmp/t078-2-p1-09-c_gw0g87`，新 launch/session/thread，67 文件冻结，完整 argv/env、API 场景、构建／Electron／驱动 argv、逐屏及 Escape／queue-release 两动作的未批准模板见 [P2-APPROVAL-09](P2-APPROVAL-09.md)。[静态准备](p1-preparation-check-09.json) PASS；本轮实际 CLI/API/UI/模型均未启动，未构建、未 rebase、不 push。真实 09A 与 B/C 仍 INCOMPLETE，整票 open／待主控关闭。T-077 合入后再变基、全部材料重新生成并完整重跑，当前 PASS 不替新 main 背书。


## 09A 失败读回与材料 09A-2（主控 #122）

上节是 09A 交审批时点。执行主控实际完成 launch 和逐屏引导／信任；continue-esc INCOMPLETE：nonce1/UPS1/主请求1/busy 与 nonce2 排队成立，但 Esc 后 active 未释放。cleanup PASS，无残留；8,208,905 字节原件已由主控外置、字节读回，manifest [578c9fe0…](external-archive-578c9fe0799847c19ce5020b5ec503d0.json)，全部失败证据保持不动。

[只读诊断](readback-09a-complete.json) 核对归档 SQLite/pty.raw 与 Electron 原件：用户动作为空、无 Esc 写入意图／收据／提交退休；31 个快照 input_enabled 全为 false，30 个已 busy 且绑定 dispatch1。问题不仅是驱动截屏／发键过早：main 的 nullable 主控 attempt=null 与 optional current_attempt 取得的 undefined 比较，永久禁输入。PTY 输出与窗口收到的 20,591 字节前缀一致，只证明输出通路；API 关闭发生在 cleanup 期间，不能算 Esc 成功。

修复独立提交 `7cd19b586fe757268384d99f243f5d0a583a5ad3`，[diff](binding-fix-final-09a2.diff) 供主控审：允许 running nullable controller 输入，保留 worker attempt 与后台凭据／版本／native leader 校验；窗口渲染身份、busy、active、输入可用状态；runner 等它们匹配且驱动发键前再核对。发键仅返回 attempted，送达必须同窗口请求的 action／admitted／write_intent／written 与 dispatch 退休顺序完整。旧运行时夹具同步传绑定，不放松业务断言。

[红态](window-binding-red-09a2/results.json) 复现主控只读与未接通／错目标仍发键；[静态绿态](fix-static-09a2/result.json) 8/8，后台身份域 5/5，收据正反例 12/12。[缺 written 变异体](window-receipts-mutant-09a2.json) 实际产生四项假送达判断，被检查拒绝。上述为生产谓词／驱动分支和合成持久事实，不替代实际 Electron/PTY 绿态。本轮无 CLI/API/UI/模型启动，未构建。

新实例 `/private/tmp/t078-2-p1-09a2-sm_du7jo`，新 launch/session/thread，73 文件冻结；[材料 09A-2](P2-APPROVAL-09A2.md) 列完整 argv/env、逐屏审批、窗口与后台读回停点、预算和清理。冻结静态检查 PASS；实际 09A-2 未运行，仍 INCOMPLETE。旧 09 slot 明确为本 worker 夹具所有，已提供主控执行的 p1-slot-cleanup-09：确认 fixture cleanup PASS、Electron quit/PID 退出和构建来源后保留清单再删精确 slot；本轮未清理，新 slot 亦须在 cleanup 后单独清理。

各原件／域检查／反例的重放命令在材料末节及对应 argv/commands.jsonl；完整读回脚本只读外置归档明确成员。不覆盖失败、不改变真实模型预算或引导授权。T-077 合入后再变基并重跑，当前只绑定变基前版本。09B/09C 双主控、紧急停止与真登录均仍未完成；T-078 整票 INCOMPLETE、open、待主控关闭。

## 09A-2 实跑失败与草稿方案交接（主控 #124）

09A-2 实际引导／信任通过，A1/A2/A3 成立：窗口确实发出 Esc，库保存同请求 action／准入／意图／写入／退休；active=null，busy/interrupted、第二 nonce 留队列，API1 的 peer 在放行前关闭。A4 后实际 prompt 却是第一条＋第二条的精确拼接；fake API 拒收，产品仍 INCOMPLETE，没有修改独立声明或业务断言。

[本轮只读读回](draft-readback-09a2/result.json) 核对保留根／外置 pty.raw（17,573 字节）一致；Esc 前已渲染至 11,917，放行前至 13,245，其增量含第一 nonce 的输入框重绘、没有第二 nonce。实际截图已目视确认恢复的第一条位于可编辑输入框。后台只新写第二条的 bracketed paste＋单独 CR，一次，没有清空键。第二真实 UserPromptSubmit 同样携带拼接正文、exit 1；API 记录三次主请求，后两次正文相同。重复请求的内部原因未确认，不算 a2a 新登记或重派发。

`user_draft=true` 来自 userInput 处理非二进制输入（含 Esc）时设置的占用标记，并非观测 CLI 草稿。releaseByUser 清理的是这个后台状态，没有清空编辑框。结合截图、hook/API 正文和单次新注入，确认“恢复的提示仍在框内，放行追加第二条”的机理；CLI 内部实现与其他编辑上下文仍未知。

[DRAFT-OPTIONS](DRAFT-OPTIONS-09A2.md) 区分事实／推断／未知，给出 A（用户处理草稿后明确确认空框放行，建议）与 B（另批丢弃草稿、后台先清空）的最小流程及取舍；列官方按键依据、Ctrl+U 多行限制、Ctrl+C 上下文风险和输入记录语义决定点。仅拒绝 user_draft 而没有确认解除入口不构成完整修复。第二 hook exit 1 不阻断 CLI 请求的事实与提交前阻断选项也列出，不能替代草稿处理或泛化为拒绝所有用户提交。本轮没有实现任何选项、发送按键、启动 CLI/API/UI 或运行模型。

主控已确认停止自建进程，CLI 退出核对 PASS；cleanup 整体 INCOMPLETE、slot-cleanup BLOCKED 原件保留。fixture 8,124,728 字节已由主控外置、字节读回，[manifest 93611737…](external-archive-93611737c0674a7aa55d1fcf3863a0b0.json) 已保留。根与 09A-2 slot 仍在；旧 09 slot 已由主控独立清理 PASS。

独立处置阶段 `p1-draft-disposal-09a2-01` 已写入 outside-sandbox.sh，交主控审批执行：核对精确归属／已知退出与五个 PID 不存在，把根和 slot 全部直接归档到外置盘、不跟随两条链接，逐成员字节读回通过后才删除自己的两个目录；不发信号、不修改产品失败状态。归档函数本地正例及实际复制链接目标的坏变异反例 [2/2 PASS](draft-disposal-static-09a2/result.json)，没有执行真实根／slot 的进程检查、外置写入或删除。重放命令与未来外置路径见方案文档末节。

方案决定仍待主控／构思主控，用户输入记录含义有变化的项已标明；后续新 Tracer bullet 仍逐次审批。T-078 open、INCOMPLETE、待主控关闭；真实双主控／紧急停止／真登录及变基后的完整验证均未完成。

## 新 worker 与 09A-3 文件边界（主控 #128，2026-10-14）

用户决定已到：[answer 20261014T120839Z](20261014T120839Z-ideation-answer-001.md)，选 A，由用户自行处理输入框，再声明“输入框已空，放行”；声明引用对应中断，后续键入或组合输入使其过期。新增声明不是机器读取空框。提交前拦截限结构化登记的当前注入，在 UserPromptSubmit 阻断错配、留诊断，不改 Stop，不裁剪、不容忍拼接、不自动重送；手打提交不受影响。Ctrl+C/U/S 等用户手动控制字节须记 control action，不记 message；本轮尚未修改产品分类或发送这些键。

电脑重启后 `/private/tmp/t078-2-p1-09a2-sm_du7jo` 已不存在。之前外置的 8,124,728 字节 fixture 归档、小份诊断和运行材料保留；其余未归档的 /tmp 原件丢失，明确记为证据缺口，不补造。上节“根仍在”是重启前的历史时点；原根读取和旧 root+slot 处置命令现在不能重跑。本轮没有尝试恢复旧服务或续接旧 CLI。

**状态 BLOCKED：产品实现停在主控指定的文件边界。** [失败方式清单](FAILURE-MODES-09A3.md) 已先写，当前候选的新红态尚未运行。实际 `gates/cli.ts` 清掉成功 signal 的 JSON，失败 exit 1 不阻断 Claude；仅改 panes/daemon 无法把 UserPromptSubmit 阻断传出。该文件由 T-080 独占，按“必须改时先停下告诉我”已上报并停止产品实现；`core.ts` 无须修改。空框声明的中断引用／输入代次还需要 app/main.ts、app/preload.ts 转发参数，这两处不在本轮明确文件范围。最小选项是主控协调 T-080 并授权三处接线，或由其负责 CLI 接线后交新候选给本 worker。没有在受限文件中写入，也没有用替代入口绕过。

可独立完成的 [仅旧 slot 清理材料](SLOT-CLEANUP-AFTER-REBOOT-09A2.md) 已准备，交主控在沙箱外运行。前置改为原根缺失、归属、重启时间、当前进程与打开文件检查；归档完整 slot 并逐字节读回后才删精确路径，不依赖旧 cleanup PASS，不发信号、不碰其他 slot。归档 helper 本地正例和已知坏跟随链接反例 [2/2 PASS](slot-archive-static-09a3/result.json)；不把 helper 绿态当实际清理通过。

本轮 vendor CLI／API／Electron／模型启动均 0，外置写入／删除 0。09A-3 产品红绿及 launch 材料仍 INCOMPLETE，未生成或启动可执行 launch，不能宣称 MATERIALS READY。新 worker 不关闭 ticket、不验收／集成，不 push；整票仍 open、INCOMPLETE，等待主控协调文件所有权。

用户随后在当前会话明确答复“保持边界，先交阻塞报告及独立材料”。据此维持停点，交 [BLOCKED-REPORT-09A3](BLOCKED-REPORT-09A3.md)，blocking issue `20261014T122545Z-worker:t078-09a3-new-issue-001` 保留开放。材料版本 `2643895b0ad1749ca04ee23fb7114df85da39b50` 的 fresh-context 只读审查对本地 helper 与脚本静态边界给出限定 PASS；实际外盘清理仍 INCOMPLETE。审查没有执行 cleanup main／外盘写入／ps／lsof／sysctl 或启动供应商进程，不能把其结论转成清理或产品 PASS。

## 09A-3：主控 #130／#131 授权接线后的候选

2026-10-14，文件所有权调整后重新开始；原证据已先原样提交 `c80cecd6cd4cc7dfdf816022db02c0f600f253d5`。本轮实现和限制见 [IMPLEMENTATION-09A3](IMPLEMENTATION-09A3.md)。空框声明引用 Esc 实际写入与窗格输入代次，原字节保留；控制字节记 action；当前登记注入的正文错配通过真实 hook CLI 输出 JSON block，手打提交与 Stop 不套用阻断。gates/core.ts 未改。

新候选入口局部 **PASS**：[原条件红态](empty-declaration-entry-red-04-09a3/results.json)、[main 同窗竞态红态](main-concurrency-red-02-09a3/results.json)、[窗口关闭竞态红态](window-revocation-red-09a3/results.json) 都实际拒绝了已知坏行为；[最终入口 17/17](empty-declaration-entry-final-02-09a3/results.json) 转绿，保存 SQLite 与真实 hook 原始 stdin/stdout/stderr。相关状态 11、Claude 关联 7、窗口身份 5、窗口绑定 8 均局部 PASS。测试经过实际 daemon/window transport/hook CLI，PTY/vendor liveness 为 spy，main 是实际闭包，未运行 Electron；不外推实际 CLI 阻断或模型请求数。

本轮真实 vendor CLI／API／Electron／构建／模型启动均 0，未用额外代理，旧 slot 未清理，未 push。门禁 8/9/18、独立 reviewer、真实 IME 与 09A-3 两个 CLI 场景仍 **INCOMPLETE**；不把旧候选或旧审查转为本候选 PASS。主控完成代码冻结提交后，才生成新隔离 HOME 的正例与保留拼接的阻断反例；各次启动继续单独审批。本段不是 launch 或整票 submit 授权。

主控 #133 已按当前启动身份提交代码 `c1c6b53a8419e35ad0dee5a79abf6adc4c37f08c`（钩子九项尾注），并核对／停止遗留 PID 74270。随后生成两套新的 [09A-3 launch 材料](P2-APPROVAL-09A3.md)，绑定该代码提交及各自 75 个源码字节；[准备检查](preparation-check-09a3.json) **PASS**。clean 根 `/private/tmp/t078-2-p1-09a3-s86zm2yy`，block 根 `/private/tmp/t078-2-p1-09a3-block-wk7vopkk`；独立 task/launch/session/thread/nonce，模板均未批准，slot 均未创建。前者由主控自行处理草稿后声明空框；后者保留恢复草稿并作反例声明，要求真实 hook JSON block、API 仍只有一次。驱动均不代发清空键、不自动点声明。所有 vendor/API/UI/构建/模型启动仍 0；只交 launch 审批，未启动。整票及真实场景仍 **INCOMPLETE**，不关闭、不集成、不 push。

主控 #135 随后通知 T-077 已验收合入 main（`cdf8fe9b`），要求本批提交后先变基、解决双方冲突，再重新生成与静态核对。上段两套变基前材料保留为日期记录，**不用于 launch**。T-080 当前独占 gates/core.ts 与 taskCards.ts；本轮不在它们增加新实现。变基 Git 操作交主控脚本执行，未知／冲突现场保留，不自动取某一侧、不 stash/reset/clean；只有新材料完成并静态核对后才交 launch 审批。

## 变基后回归与 worker 回执诊断（主控 #143／#146）

主控执行五个 continue 脚本后完成变基：`ff3708d0b647ddf71d272e6fb87f6424c7533163`，基于含 T-077 的 main `87e954a2f4059d471e3e240872b565217e29b0b5`。各冲突双方、解决文件、静态核对与执行现场保存在 rebase-continue-01～05；后续夹具元数据修正和本地回归证据已由主控按原启动身份提交 `0f754a6dfd555568cb377affbbe52655a13d3d4d`，九项尾注。原隔离后台经认证 cleanup **PASS**，没有强制信号或删除原现场。

主控在沙箱外执行第一阶段：实际 Electron／PTY runtime 12 项与 input-failures 11 项 **PASS**；worker-inbox 七个回执断言 observed={}，整段 **INCOMPLETE**，其后 8/9/18、CAS、权限反例未运行。原输出 [rebased-outside-regression-09a3](rebased-outside-regression-09a3/result.json) 保留原状态，不重试、不改写。

[只读诊断与最小复现](WORKER-INBOX-DIAGNOSIS-02.md) 核对原库八个真实回复均存在：正常请求的真实 worker 来源、范围、权限拒绝及撤销后的 stale_attempt 齐全。缺返回来自夹具按旧 `id:<request_id>` 查内部 key，漏掉 T-077 按 launch 登记的回执；没有证据要求修改 claim 来源、受管派发或凭据的产品行为。离线最小探针 8 项红态，修复夹具按持久 launch／request_id 关联 opaque key 后，同一探针 8/8 **PASS**，原业务断言不改，src/app/hooks 不改。诊断与局部绿态不替代新真实入口回归。

同一 [阶段脚本](rebased-stage-09a3.py) 的 regression-02 模式只续跑 worker-inbox 14 → 8/9/18 → CAS 1 → 四个权限反例，独占新输出目录；原 runtime／input-failures 仍绑定 0f754a6d，只有产品文件未变化时才复用 frontend。提交和沙箱外执行均交主控脚本，真实模型预算 0；本轮未启动 CLI／API／UI，不提权、不 add／commit。**新阶段回归、独立 reviewer、新两套 09A-3 launch 材料与真实场景仍 INCOMPLETE**；T-078 open，不关闭、不集成、不 push。

## 09A-3R 材料交接（主控 #147／#148）

主控提交夹具修复 `567d7748c40ca511f170997d7fe216063fb7c4f1`，九项尾注；沙箱外 regression-02 **PASS**：worker-inbox 14/14、coop 8/8、recovery 9/9、run 18/18、CAS 1/1，四个权限变异体各在唯一目标契约失败且禁止结果实际出现。[保存结果只读核对](regression02-readback-09a3r.json) 9 项 PASS，未重跑。原 runtime 12／input-failures 11 仍绑定 0f754a6d，并保存产品源码未变的核对，不称重跑。原失败目录和状态保持不动。

主控随后以原启动身份提交回归证据 `166509267fe11f02b1591f2089a77d7480a0c1e6`，九项尾注。新两套 [09A-3R launch 材料](P2-APPROVAL-09A3R.md) 均绑定该提交，clean 根 `/private/tmp/t078-2-p1-09a3r-1t5lartp`、block 根 `/private/tmp/t078-2-p1-09a3r-block-58xp7gc_`；各自新 HOME、task、launch、session、thread、nonce，两包各 76 个冻结源码文件。生成及静态核对 **PASS**，模板全未批准，slot 未创建，CLI／API／后台／Electron／构建及真实模型启动均 0。

正例继续采用 Esc → 主控亲自处理草稿 → 看到空框后声明 → 第二回合 exact 干净送达；反例保留恢复草稿，作反例声明，要求真实 UPS2 JSON block／exit 0、API 总数 1，并保存 2 秒有界无 API2 观察。驱动不清空、不自动点声明、不裁剪、不容忍拼接、不重送；逐屏引导、信任、continue 与 cleanup 仍分别审批，两套串行。此次只申请正例 launch；材料提交不启动。产品源码未变，T-080 的 core.ts／taskCards.ts 未动。

清理读回发现旧包文案把 slot 脚本的文件清单＋删除称作归档，实际没有 slot 内容归档／逐字节读回。已非 blocking 上报 [slot 文案问题](SLOT-CLEANUP-DOC-ISSUE-09A3R.md) 并更正新包；不修改旧日期记录、不改清理工具。两个新 slot 尚未创建，删除不在 launch 授权中，清理阶段由主控另行处置。

真实两套场景、新候选独立 reviewer、09B／09C、系统 IME、真登录及整票验收仍 **INCOMPLETE**。本包不借旧材料批准，不把静态准备 PASS 或有界反例当可靠性结论。T-078 保持 open，不关闭、不集成、不 push。

## 09A-3R2 驱动修改（主控 #150）

主控提交 09a3r 材料 `6f0cfdb2c042ac27251dd979b56c792e4874f720` 后说明执行主控没有原生窗口操作工具，不能依赖用户在场，明确改为逐项预批的 test-simulated-user 清空及点击声明。该消息覆盖之前的人工步骤限制；后台仍不删字，原 Stop／拦截／API oracle 不改。旧材料保留，但当前驱动改变后不能再用于 launch。

先写 [失败方式](FAILURE-MODES-09A3R2.md)，核对 [官方 Ctrl+C 依据](KEY-BASIS-09A3R2.md)，取得旧人工 runner 与父版本窗口按键分支红态；改动及边界见 [IMPLEMENTATION-09A3R2](IMPLEMENTATION-09A3R2.md)。新局部 runner 14/14、窗口分支 13/13、原收据 12/12 **PASS**；空框无条件通过及取消批准检查两项有效坏变异均被契约拒绝。属于实际脚本分支＋合成窗口事实，不是实际 CLI／xterm 绿态。

正例在 Esc 写入／退休、API1 取消及恢复草稿可见后只经同窗口发一次 Control+C，完整 control action／准入／intent／written、新 offset、编辑区空框、截图和同 highwater PTY 原字节齐备后才点生产声明；反例不清空，只点击预批的故意不真实声明。每一步有独立批准人／引用／依据，source 明写 test-simulated-user，不能称用户亲手操作。任何不清空、残字、未知区、缺证、旧代次或额外输入均停，无第二 Ctrl+C、换键或重送。slot 删除按 #150 保留不执行，清理阶段再定。

本轮只改测试／材料工具，src/app/hooks 与 T-080 文件未动；未启动 CLI／API／后台／UI／构建或真实模型。主控冻结修改后才生成两套新 09a3r2 ID／HOME／nonce；新材料静态核对及实际场景当前 **INCOMPLETE**。新候选独立 reviewer、09B／09C、系统 IME、真登录和整票仍 **INCOMPLETE**，不关闭、不集成、不 push。

主控 #151 以原启动身份提交 `643d59bfadbf07466ee28d57f471b8ef3d10646f`，九项尾注，保存新 source freeze。本 worker 随后生成 [09A-3R2 新材料](P2-APPROVAL-09A3R2.md)：clean 根 `/private/tmp/t078-2-p1-09a3r2-hgqtpjz_`、block 根 `/private/tmp/t078-2-p1-09a3r2-block-093154n0`，新 HOME／task／launch／session／thread／四 nonce，分别冻结 79 文件。生成及静态核对 **PASS**；每个动作批准字段均为空，API／状态库／readiness／slot 尚未生成。只交 clean launch 审批，提交脚本不启动。

正例与反例均由 executor 预批的 test-simulated-user 点生产声明，来源在证据中明示。正例同窗一次 Ctrl+C、完整控制收据、新 offset 空框及 PTY／窗口证据齐备后才点；反例清空预算 0，保留草稿并作不真实声明，要求拼接 block／API1-only。当前外包只接受 09a3r2，旧材料批准不能误选新实例；slot 删除入口保留拒绝，清理到时由主控另定。本轮没有真实 CLI／API／后台／Electron／构建／模型启动，实际两场景及新候选独立审查仍 **INCOMPLETE**，整票不关闭、不集成、不 push。

## 09A-3R2 实跑、清理修复与 09BC 计划（主控 #153／#155／#157）

以上是交材料时点。随后主控逐次批准并实跑两场景，源 `643d59bfadbf07466ee28d57f471b8ef3d10646f`、材料提交 `dc67ce58b3300503bf31873d7c3c69c8d56b941f`。clean／block 均局部 **PASS**，模型 0，窗口动作如实为 executor 批准的 test-simulated-user。worker 从外置原件直接读 API/hook/PTY 和新临时 SQLite/WAL 副本，[23 项读回 PASS](closeout-readback-09a3r2/result.json)，并目视空框与拼接阻断截图，详见 [CLOSEOUT-09A3R2](CLOSEOUT-09A3R2.md)。读回不是新上下文独立 reviewer，不外推整票。

clean 的 Esc 退休／API1 取消、一次同窗 Control+C 的 control action、输入代次 2、空框观察及 highwater 13836 字节一致、引用中断 seq88 的声明／唯一释放、API2 末条精确为前缀＋nonce2（不含 nonce1）、新 prompt_id／唯一匹配 Stop／idle 均成立，三 hook exit 0，cleanup PASS。block 不清空、故意不真实声明后的实际 UPS2 拼接被 JSON decision=block／exit0 阻断，主 Messages 只有 1、无第二 turn_start/Stop/API 错误；原 2 秒观察与后续归档均无 API2。

block 初次 cleanup **BLOCKED**：真实 PID48987/lstart 未变但 comm 转成 `(2.1.296)`，旧规则立即 identity_changed，没有等实际 absence；记录缺 stat，不称括号名证明退出。先复现等待闭包红态，再修为同 PID/lstart 继续有界观察、仅实际 absence 才 PASS，PID 复用仍拒绝。第一次恢复也 **BLOCKED／无信号**：中文 ps 日期四段被按五段切列，Python 路径混入 started。使用原文本／实际 probe 红态后，固定生产端 LC_ALL=C/LANG=C、非规范消费输入直接拒绝；owns_api 规则不改。lifetime 5、locale 5、原 cleanup 6 局部及回归 PASS；两份真实 BLOCKED 原样保留。

主控 #157 执行恢复-154 **PASS**：仅对核对完整命令／根及双读 lstart 的 API PID48954 发一次 SIGTERM，确认退出；原 CLI48987／壳48986／后台48977 均确认退出。block 根直接外置归档、逐成员字节读回后删除。clean 原件 8,138,071 字节／980 成员，manifest [20323dd7](external-archive-20323dd797a64b74b90e9633065b15df.json)；block 原件 8,126,057 字节／970 成员，[recovery-154 清单](p1-materials-09a3r2-block/cleanup-recovery-154/result.json)。原 [3fc9ebfa](external-archive-3fc9ebfa7b8b4183a45aa58f2bd16dff.json) files=[] 不能证明 block 根归档；由新清单补齐，旧清单不改。两根已删除，两 slot 仍在外置盘、未删。

只读发现 Claude 角色 relay／stop 客户端／nullable 控制会话 caller／双角色 HOME 等前置缺口，按最新指示只交 [09B/C 计划审稿](PLAN-09BC-01.md)，另报 [入口前置](ISSUE-09BC-ENTRY-01.md)。当前 09B/C launch **NO_GO**，没有新材料／实例／启动，也不实现这些超出当前阶段的前置；主控先审计划并协调 T-080 文件所有权。新候选独立 reviewer、09B/C、实际 IME、真登录与整票仍 **INCOMPLETE**，不关闭、不集成、不 push。

## 第二次 main 变基与 T-080／T-083 局部回归（主控 #163／#167／#168）

主控 #163 已审 09BC 计划并分配前置产品文件，批准顺序为单角色真实 Claude 转交／工具切片红绿及边界反例 → 09B 材料／实跑 → 09C 材料／实跑。每场景每角色根提交 ≤6、主 Messages ≤12、合计 ≤24、模型 0；09C 必须真实超过 120000 ms、总观察 ≤150 秒。上节入口 NO_GO 是审计划前的历史状态；本轮按新授权先变基与回归，不据此启动未经逐次批准的新场景。

主控 #168 完成有界变基 **PASS**：`bf9bb9d75def72c7c74ef6389bcb82647a29a697`，固定目标 `490de67d05a08ccf8a453a78694a106288579b47`，含 T-080／T-083、无冲突。交接提交 be6e0195 与备份保留；原日志十个文件逐字节拷入 [rebase-main-2/execution](rebase-main-2/execution/COPY-RESULT.json)，未移动／删除原件。

本轮只迁移 T-078 自建三个卡生成器，显式补 `oracle_paths: ["value.txt"]`，其固定基线先提交到各夹具；不改本 worker 的实际任务卡或产品源码，不留旧格式分支。实际卡表达式的当前生产 schema 探针先取得 [红态 3/3 拒绝](post-rebase-2-card-red/results.json)、exit1，再取得 [绿态 3/3 PASS](post-rebase-2-card-green/results.json)。起始文件存在及实际 claim 仍需真实入口检查。

新的局部检查 **PASS**：打分 34（实际临时 schema2 写入／缺 oracle 拒绝／schema1 历史只读）、T-083 原有入口 7（0 failures/errors）、收件箱领域 11、pane runtime 11、主控窗口身份 5、Claude epochs 7、窗口绑定 13；命令与边界见 [POST-REBASE-2](POST-REBASE-2.md)。纯逻辑与 spy 不代替真实边界；T-083 使用假启动器，没有启动额外 agent。供应商 CLI／API／Electron／模型 0，无 Git 写入、无额外子代理。

[单一沙箱外阶段脚本](post-rebase-2-stage.py) 已准备，计划顺序为库 inbox 8、原任务卡 15、真实 daemon/window/hook 空框入口 17、确定性接收器的实际 Electron／PTY runtime12／input-failures11／worker-inbox14。冻结 HEAD 后才运行，外盘缺失／源码变化／异常即停，超时保留 PID 与原件，不发信号或重试；slot 不删。上述实际入口目前 **INCOMPLETE**。完整 8/9/18/CAS 未在此次变基后重跑，旧 PASS 不替本候选背书。

交 [提交脚本](commit-post-rebase-2.sh) 与阶段命令给主控运行；成功后绑定新的 source freeze，再准备单角色真实 Claude 入口红态 launch 包。该切片、新独立 reviewer、09B／09C、实际 IME、真登录及整票仍 **INCOMPLETE**，本轮不启动、不关闭、不集成、不 push。

## cards host 夹具启动凭据与第二次变基续跑（主控 #170）

主控按原身份冻结 `3d5225a9689bf04bf839967dc059e0a8e7adc300`，九项尾注；沙箱外首次阶段 **INCOMPLETE**：inbox-entry 8/8／cleanup PASS，cards15 为 0 failures、15 errors，全部 setUp 失败。前四条命令是版本／源码检查，其后空框入口、runtime、input-failures、worker-inbox 均未运行，不把命令序号当业务测试组数。原 [outside-01](post-rebase-2-outside-01/result.json) 全部保留，不重试。

[原始十五份 host 输出读回](post-rebase-2b-diagnosis/original-host-readback.json) 确认同一 `absolute_operator_credential_path_required`，发生在 credentials.ts 与 host:84 创建 bootstrap 凭据，serve／card 请求之前；无 readiness／gate CLI 请求。`DaemonCards` 父 setup 清掉继承 A2A 环境，却未像其它生命周期 adapter 一样设置本夹具绝对凭据路径；属于夹具接线缺陷，产品拒绝缺凭据符合现有边界，不是 oracle_paths 或 core 业务接口导致的这十五个错误。完整 host／业务接口仍待实际续跑。

实际 setUp 环境＋生产 credential API 的最小信号，迁移前 [red2/2](post-rebase-2b-bootstrap-red/results.json) 缺路径、同因 exit1；补每根自己的 operator 路径并在原退出确认后移除自建凭据，迁移后同探针 [green2/2 PASS](post-rebase-2b-bootstrap-green/results.json)。host spawn 被截获，真实临时 Git／凭据创建与读回，未启动 daemon／PTY／供应商／模型；该局部 PASS 不等于 host ready 或 cards15 PASS。修改仅夹具生命周期三行，原卡与业务断言、host／产品均未改。

交 [诊断与续跑说明](POST-REBASE-2B.md)、[提交脚本](commit-post-rebase-2b.sh) 和更新后的 [同一阶段脚本](post-rebase-2-stage.py)：核对原 inbox PASS／cleanup 与相关源码未变，明确复用、不重跑；只从 cards15 及之后四组续跑到新 outside-02，异常停、保留原件、不重试、不删 slot。完整续跑、新独立 reviewer、单角色真实 Claude 红态、09B／09C 与整票仍 **INCOMPLETE**。

## 第二次变基续跑 PASS 与单角色红态准备（主控 #172）

主控冻结 `ee2f7c1b7c19153ffec07abd2eb30574863d8c77`（九项尾注）并在沙箱外续跑 [outside-02](post-rebase-2-outside-02/result.json) **PASS／rc0**。worker 实际读回原结果：cards15（0 failures/errors/skipped）、空框声明入口17、runtime12、input-failures11、worker-inbox14，三 UI 场景 setup／cleanup 完整；原 inbox8 的 3d5225a9 来源与源码未变复用核对保留。outside-01 原失败不改；没有把前置命令数当业务测试数，也没有重跑未要求的完整 8/9/18/CAS。

按主控顺序只准备 [单角色工具入口红态](SLICE-1-RED.md)，产品源码未改，真实 Claude 未启动。根提交1、Bash1、主 Messages2、模型0；真实 CLI 调用库 inbox list，fake API 只发精确命令和普通 ACK，实际错误必须来自真实 tool_result；不写 requests／业务库，不伪造 attempt 或 operator 代写。startup/trust、nonce、原生工具许可均单独批，工具 Enter 走同窗口并记 control action／实际 written。

先写 [失败方式](FAILURE-MODES-SLICE1.md)。新假 API 的纯协议 [12 项 PASS](slice1-protocol-green/results.json) 和 [有效预算坏变异](slice1-protocol-mutant-budget-02/results.json) 已保留；坏变异确在第三请求契约失败、exit1。第一次带 mutant 目录名的命令漏传开关，mutant_budget=false，原件保留，不当变异证明。局部夹具证据没有 socket／CLI／API／UI／模型，不能替真实入口红态。

最早 worker 专用 writer 位于未列入分配的 relayFiles.ts，已 [非 blocking 上报](ISSUE-SLICE1-RELAY-FILE-OWNERSHIP.md)，先继续红态准备，不在其它文件复制 writer，也不写该产品文件。后面的 controller_relay_not_enabled／nullable caller／relay schema／角色归属仍等真实层次证据，不能只删拒绝就称接通。

只读还发现 [许可 Enter 提交记账](ISSUE-SLICE1-PERMISSION-ENTER.md)：当前 userInput 会将 CR 直接登记新 user intent／替换 active，工具审批可能虚记新提交；未实测，已非 blocking 上报。探针单列这个缺陷，以真正 UPS1/API2 核对原生预算，不称假 intent 为合法回合或原注册正确结算。工具键分支旧版红态后新增窄的 permission Enter：[6 项局部 PASS](slice1-permission-key-green/results.json)、原 Esc/CtrlC [13 项 PASS](slice1-window-binding-regression/results.json)，模拟 view、未开 UI，产品 input 行为不改。

交 [一次运行的冻结／生成脚本](commit-and-prepare-slice1.sh)：先冻结辅助脚本与回归证据，再生成全新实例、按 Git 提交与当前源码逐字节读回，再提交材料；不启动。材料成功后主控读实际 argv/env/root/IDs 再逐次批 launch；当前实例生成／实际红态／绿态／边界反例、新独立 reviewer、09B／09C 与整票均 **INCOMPLETE**。

## 单角色首轮真实工具红态与未闭合现场（主控 #175）

主控已运行冻结／生成脚本：source `6a59ef929bbea4b68e28e8c88db57a7e280c390e`、材料 `14e19e2bff16eacfcba7ab00bd63906aef42cced`。新 root `/private/tmp/t078-2-p1-slice1-red-z7msieml`、launch `70e18a26…` 已逐次启动／引导／信任／nonce／一次 Yes Enter。首次生成缺少 screen-key-approval-template，主控补为 executor-written；旧文件来源标注不改，生成器现已补未来实例的空批准模板。

读回 [现场原件与副本](slice1-readback/result.json)，最早库客户端的真实入口红态 **PASS**：真实 Bash command 与冻结命令一致，API2 同 ID tool_result 为 is_error=true、Exit code1＋daemon_call_failed／worker_request_directory_required；requests、relay_requests／relay_results／inbox_records／inbox_deliveries 全 0。足够支撑该客户端缺陷的对应修复，未到非空请求的 controller_relay_not_enabled，不能拿后者冒充此次红态。

许可 Enter 记账红态 **PASS**：原生 PermissionRequest seq57；同 request/window 的 seq85 准入、86 intent 0x0d、88 written、action 2b3fa040(form=action)齐全；seq87 却多记 source=user 提交 intent。实际 UPS1、intent2。虚记已实测；active 替换由实际执行路径和源码推断，没有后置 pane 快照，未声称直接读到内存。原许可截图已目视确认一次 Yes／冻结 command。

整场 **INCOMPLETE**，预算 **NO_GO（主 Messages3/2）**：API2 的结果之后有 system 元数据，原 fake validator 错判末条必须 user，抛错，未回 ACK；原 hooks 仅 UPS／PermissionRequest(exit0)，无 Stop／turn_end／idle。第三条仍同 tool_result，thinking 有变化，debug 记录两次 HTTP400及 engine turn ended in error；没有第二 UPS，不是新根，但超本包额度。发现即发主控报警，原 permission/result.json／api-error不覆盖，不补 ACK／不续跑。

以本次 api.jsonl 原样副本先取得 [实际请求 red](slice1-recorded-api-red/results.json)，再只修消息位置定位：[green12/12](slice1-recorded-api-green/results.json) PASS，ID／command／model／stream／预算／唯一结果／因果顺序不放宽，末尾仅 text system 元数据可接受。去掉 command 核对的坏变异、放宽预算的坏变异分别在对应条件失败；原合成 protocol12 仍 PASS。全部是 validator 本地重放，没有重发实际请求或启动服务。未来 screen-key template 的实际生成表达式也已核对，旧源码缺失和旧主控补写来源保留。

交 [读回与建议](SLICE-1-READBACK.md)、[固定本实例 cleanup 脚本](cleanup-slice1-red.py)：认证 daemon_stop、等待原 CLI／shell／daemon实际退出、API92591完整 argv/root＋双读 lifetime 后最多一次 SIGTERM；逐成员归档读回到外置盘，slot 不删，根删除须显式 --remove-root。worker 未执行，cleanup **INCOMPLETE**。建议先清理，再新实例／新 ID／新批准重跑一个闭合 ACK／Stop 的完整红态，不将已失败／越预算旧实例改成 PASS。当前只修假服务／模板，不改产品；新独立 reviewer、真实转交绿态／边界反例、09B／09C／真登录／整票仍 INCOMPLETE。

## controller 请求与许可记账实现候选（主控 #178）

主控按原身份提交 `5b404cb91a4415d31ff2ba2aa113de7d9bea0994`（九项尾注）；原 [cleanup-175](p1-materials-slice1-red/cleanup-175/result.json) **PASS**：仅 API92591 一次 SIGTERM，外置归档逐字节读回，根因 api-error 按规则保留，root_removed=false，slot 未动。此前 INCOMPLETE 原报告不改写。

在 #178 已分配的八个产品文件与测试中完成原通路的 schema2 controller 请求、真实 Stop 转交及 caller 核对；不伪造 worker attempt/fence，不用 operator 代理请求。launch/preset/project/task/spec_rev/session/native session/prompt/active/shell/leader 均参与核对；角色 scope 来自实际 caller，请求参数不能覆盖。PermissionRequest 绑定当前 prompt 与登记 active，工具许可 Enter 只记 control action/write，原 active 保留；普通 Enter 的提交行为保留。细节和每项证据见 [SLICE-1-GREEN](SLICE-1-GREEN.md)、[失败方式](FAILURE-MODES-SLICE1-GREEN.md)。

对应两条已取得真实红态，实际 producer 的 parent red→green、原 #175 UPS/PIRQ 的许可单元 red→3/3 green；relay/caller 边界22/22、worker writer3、scope5、controller-window5、pane-runtime11、Claude epochs7、inbox-domain11 均 PASS。taskspec/project caller 额外先取局部红态再修。worker writer 新规范路径拼写导致的临时回归原件保留，根因层修为仅 controller context 使用该检查；原 worker 三条真实 CLI 请求回归 PASS。

复核候选发现 relay 扩展漏保留原角色白名单；先保存 monitor／unknown 被执行的局部红态，补回检查后两个反例 PASS，controller22 重跑 PASS。启动 profile 预算3项及使用旧官方 help 的角色文本参数检查也 PASS；漏传 help 路径的命令错误保留，不能算产品红态。

绿态 fake API 合成契约11/11 PASS；空结果、错角色、错 request_id、重放、多工具均拒绝。首次预算变异被其它验证掩盖，不算证据；修正探针输入后，有效坏变异仅在第四 Messages 拒绝条件失败。局部 protocol／spy 不替实际 Claude 或独立审查。

交 [冻结→入口回归→生成→材料提交脚本](commit-and-prepare-slice1-green.sh)，依次 controller-entry6、空框17、runtime12、input-failures11、worker-inbox14；全部通过才生成新 `p1-materials-slice1-green`，绑定新 source commit、逐文件 tar/Git 读回，再提交材料。生成不 launch；launch／逐屏信任／nonce／一次工具 Yes 都由主控单独批准。两条预声明 incoming role sentinel 是夹具输入，不冒称另一真实角色发送。预算根2、Messages3、Bash1、供应商模型0，第二根只承载真实 Stop 处理结果；无重试。

当前上述沙箱外入口、新实例生成／静态核对、真实 Claude 绿态均 **INCOMPLETE**；新独立 reviewer、09B／09C、真登录、整票仍 INCOMPLETE。project_map status 的 README stale 已非 blocking 上报所有权问题，本轮不擅改 README／地图，不能声称 living docs 全绿。所有 Git／服务启动交主控脚本，worker 未提权、未开额外 agent、未启动 CLI/API/Electron，不删根／slot，不集成或 push。

## 首次 controller 入口阶段的反馈早读（主控 #182）

主控以原身份冻结 `455696c98e99b73a118886345ab1d83de24e0bdf`（九项尾注）。[outside-01](controller-green-outside-01/result.json) **INCOMPLETE／rc1**，controller-entry 第五项期待反馈 CR 却早读 undefined；原入口前四项通过，后续第六项、空框17、runtime12、input-failures11、worker-inbox14、实例生成均未执行。原 stage／preparation 输出和 code-freeze 留存，不覆盖、不重试。

[只读原事件](controller-green-2-diagnosis/original-database-readback.json) 明确 seq29 一次真实 ideation 执行、seq30 反馈排队、seq31 原提交 idle、seq34 paste_written、seq38 turn_submitted，最后 seq39 daemon_stopped。CR 确实稍后写出。daemon 在 Stop 响应 close 后 drain，夹具在 paste 与 CR 之间断言并清理，属于夹具等待缺陷；产品无改动。

先用生产 drain 的 [局部 red](controller-green-2-wait-red/results.json) 复现完全相同 undefined !== '\r'，再以同样生产代码等当前 dispatch 的 turn_submitted 得 [green PASS](controller-green-2-wait-green/results.json)，保持实际 CR、busy、active 和两条 intent 断言；PTY 为 spy，无 daemon／socket／CLI／API／模型。修复入口仅补有期限的特定收据等待，保存前后／超时快照，原角色、身份、字节及去重断言保留。

#182 已分配 README，本轮同步现有 controller 通路与验证边界；提交前 status 的历史 stale 留存，待 README 提交后再核对。交 [新续跑脚本](commit-and-prepare-slice1-green-2.sh)，新 outside-02 依次完整入口6及其后四组；全部通过再生成全新 slice1-green，并静态核对、材料提交。当前完整续跑、新实例／实际 Claude 绿态、独立审查、09B/09C、整票仍 **INCOMPLETE**。没有 launch、提权、额外 agent 或删除现场／slot。

## controller 入口续跑与新材料冻结（脚本执行读回）

夹具／README 提交 `7e77f8b81611dc03e7df95a95801bda3f617393d`，产品源码沿用 `455696c98e99b73a118886345ab1d83de24e0bdf`；提交后 project_map status **PASS**。新 [outside-02](controller-green-outside-02/result.json) **PASS**：controller-entry6、空框17、runtime12、input-failures11、worker-inbox14；UI 三组 setup/cleanup 均确认，原 outside-01 失败与原数据库归档保持原样。

[新实例静态核对](p1-materials-slice1-green/static-check.json) **PASS**：root `/private/tmp/t078-2-p1-slice1-green-1yhrmwad`、launch `284a5916-fd75-4c4d-bec0-9a8d49e063d9`、session `10b07cc8-bdc6-47e4-a801-c4d63dd37bb4`；绑定本次 source，逐文件 Git/tar 字节相同，批准字段空。根2、Messages3、Bash1、模型0。实际 Claude 绿态／launch 尚未执行，独立审查、09B/09C、整票仍 **INCOMPLETE**。

## 首个真实绿态场景的 API3 文本表示误判（主控 #184）

主控以材料提交 `41672c9363ce5c70689f2e3a9f71d16256e9a9a7` 实跑上述实例，逐屏／信任／nonce／一次 Yes Enter 完成。场景 **INCOMPLETE**，预算 **NO_GO（主 Messages4/3）**；原 permission／api-error 不覆盖，没有最终 ACK／第二 Stop／idle。本轮没有重送旧请求。

[原件只读快照](slice1-green-3-readback/database-readback.json) 留存数据库／WAL／SHM 两次相同字节读取的原 tar，SQL只在私有副本上读。API2 真实 tool_result queued=true/delivered=false；PermissionRequest seq57，Enter control action 与 seq88 引用第一根原 submission，没有新增 user intent。真实第一 Stop 与 UPS1 同 prompt，exit0；seq93～94 一次 schema2请求真实执行，仅返回IDEATION sentinel；seq96第一根idle。第二根 seq100～101 登记并CR，UPS2 exit0，新prompt，真实API3已收到该反馈。已证实这部分真实链路，不上调为整场绿态。

[登记／UPS2／API3 文本对照](slice1-green-3-readback/registered-feedback.json) 完全相同，API3 的 user.content 是字符串；原 validator 只遍历 block 数组，漏掉反馈，误取第一根nonce作比较。错误HTTP后CLI自身重发API4，仍同一第二根；根intent/UPS各2，但超Messages预算，不能容忍或补称通过。

用 api.jsonl 原样先取得 [red12、仅API3失败](slice1-green-3-recorded-red/results.json)，再修文本表示并要求实际登记正文精确相同，[green14/14](slice1-green-3-recorded-green-02/results.json) PASS。假服务只读自身库中绑定该launch的第二gate dispatch及queued事件作参考，不从API正文生成expected、不写业务行或请求、不代理角色。model/stream/预算/命令/tool ID/request关联/角色范围不放宽；外来launch没有登记参考。合成green11、原red协议12回归PASS；预算坏变异仍仅第四Messages条件失败。全部局部重放/SQL验证，无服务/CLI/API/UI/模型启动。

交 [固定cleanup脚本](cleanup-slice1-green-184.py)：认证daemon_stop确认原CLI/shell/daemon退出；核对API44036命令/root和两次lifetime后最多一次SIGTERM，确认退出并外置逐成员归档读回。根因api-error保留，无root删除选项，slot不动；当前仅静态PASS，实际cleanup **INCOMPLETE**。说明与新实例审批见 [SLICE-1-GREEN-3](SLICE-1-GREEN-3.md)。

cleanup PASS后交原身份 [冻结／新材料提交脚本](commit-and-prepare-slice1-green-3.sh)，新 `p1-materials-slice1-green-3` 必须新root/HOME/IDs/nonce，绑定新source、逐文件核对。明确复用outside-02的相关入口PASS，仅在产品/入口/驱动源码均未变的Git核对通过后成立，旧回归不是新运行。新原样重放单列；根2/Messages3/Bash1/模型0不增，launch与逐屏/nonce/一次许可仍单独批。当前新实例生成/真实完整绿态、独立reviewer、09B/09C、整票仍 **INCOMPLETE**。产品源码无改动，worker未执行清理或启动新实例。

## 原场景清理与新文本校验材料冻结（脚本执行读回）

[原场景cleanup](p1-materials-slice1-green/cleanup-184/result.json) **PASS**：确认四个原进程退出、最多仅API44036一次SIGTERM、外置归档字节读回；根／slot保持，原场景仍INCOMPLETE／预算NO_GO。新source `8e99d62e7892ef0468fe2b2b8dabe22387684557`，产品沿用455696c9；相关outside-02源码未变，明确复用、不称新运行。

[新实例静态核对](p1-materials-slice1-green-3/static-check.json) **PASS**：root `/private/tmp/t078-2-p1-slice1-green-3-jzfi4ju5`、launch `c4a5dc22-7d3f-430d-8e82-1b8723fac40f`、session `b733f220-534f-4411-b960-5caabd1ed73e`；新HOME/IDs/nonce，Git/tar逐文件相同、批准字段空。根2/Messages3/Bash1/模型0；未launch，真实完整绿态、独立审查、09B/09C与整票仍 **INCOMPLETE**。

## 单角色 green-3 实际闭环 PASS 与 09B 计划性材料（主控 #185）

主控逐次批准启动／逐屏／信任／nonce／一次工具Yes，`p1-materials-slice1-green-3/permission/result.json` **PASS**。worker [读回原数据库／WAL／hook/API](slice1-green-3-closeout/readback.json) 再核对：三次主Messages（实际ACK与FINAL_ACK）、relay_processed一次、两个intent／turn_end／idle，permission_control_written一次且没有user intent。`inbox_list --role executor`仍返回实际ideation的IDEATION_ONLY_SENTINEL；第一真实Stop执行一次，反馈第二根完整到达并结算。来源source8e99d62e、材料b5b8b165；供应商模型0，范围为实际单角色假服务闭环，不是09B／09C／整票。

#184 的API3字符串表示误判已由原样red→green修复，并在本次全新实例真实复验通过；没有放宽登记正文、身份、预算或工具条件。旧scene仍INCOMPLETE／主Messages4/3 NO_GO，原件与cleanup-184 PASS保留，错误根不删。

交 [本实例cleanup](cleanup-slice1-green-185.py)：认证daemon_stop、原CLI/shell/daemon确认退出、API49173命令/root与双读lifetime后最多一次SIGTERM，确认退出；外置逐成员归档读回、库存未变和四PID仍不存在后才删此成功根。slot处置另列且本轮不动。当前仅脚本就绪，实际cleanup **INCOMPLETE**，worker未执行。

按 #185 先交 [09B计划性材料审阅](09B-MATERIALS-REVIEW-01.md)，不启动、不改产品。当前profile共享六个角色路径且只允许1/2根，静态构造事实已核对／非blocking上报；新09B合同仍INCOMPLETE，launch NO_GO。拟独立HOME/请求/日志等目录、共同broker/state/repo，一项实际受管确定性C目标，真实attempt/fence必须由dispatch/claim取得；材料不伪造尝试或借operator代写业务。

完整拟序列包含真实send→错误目标拒绝→实际目标stop→执行成功后ack→重复ack幂等、ideation越权ack与已ack stop拒绝；I4根6主Messages，E6根11主Messages，合计17、供应商模型0，均在 #163 上限内。fake API只给工具／中性确认，实际反馈全文／stop/request/inbox ID与角色来源必须读回；不沿用共库固定#1/#2。card模板补oracle_paths，目标不提交候选，真实运行观察由独立oracle定义。

交 [提交与计划包冻结脚本](commit-closeout-and-09b-materials.sh)：成功cleanup后保存green-3实际读回、#184结论与前置事实，生成09b-materials-01提案profile/IDs/目录、协议、oracle、卡与空批准模板，Git/tar字节核对后材料提交。静态PASS仅计划冻结，**不能launch**；profile/回合前置与实际双角色驱动仍待审阅后实现、再冻可执行包。实际09B、09C、独立reviewer与整票 **INCOMPLETE**；本轮没有新CLI/API/目标/UI启动、没有集成或push。

## green-3成功清理与09B计划包冻结（脚本执行读回）

[cleanup-185](p1-materials-slice1-green-3/cleanup-185/result.json) **PASS**：原进程退出、最多仅API49173一次SIGTERM、外置归档字节读回后删除成功根；slot仍保留。source `c6a81742eac12736bb5fd407401d578ded58e5fd`。

[09B计划包](09b-materials-01/static-check.json) 静态 **PASS**，root `/private/tmp/t078-2-09b-plan-4mzvkbne`，source/Git/tar逐文件相同；包含独立角色目录／拟argv/env、协议、oracle、task卡和空审批模板。明确 **launch NO_GO**：当前profile与双角色阶段驱动前置未完成；未创建Git repo／broker／角色／目标，实际09B、09C、独立reviewer、整票仍INCOMPLETE。

## 09B 前置产品切片：角色隔离目录与 6 根预算

主控 #187 已审 09B 计划方向，预算 I=4/6、E=6/11、合计17、模型0。本轮只做前置，不实现双角色业务驱动，不启动 CLI/API/目标。

[修改前红态](09b-profile-red-02/results.json) 记录真实 `claudeLaunch` 构造的共享六路径（HOME、CLAUDE_CONFIG_DIR、TMPDIR、ZDOTDIR、A2A_REQUEST_DIR、A2A_HOOK_TRACE_DIR）及第三根 `invalid_controller_turn_limit`。修改后 [绿态](09b-profile-green-01/results.json) 通过真实生产构造器：同一 broker/state/repo 下由 `roles/<preset>/` 推导独立 home/config/tmp/shell/requests/hooks/user-data/debug，路径无交集；3 根接受、7 根拒绝。旧 root 级路径不再由 P1 生成器创建，不留 fallback。

`panes.ts` Claude 信号接受 1～6 根；P1 生成／续跑同步角色目录、role config/settings、hook 读回和 user-data。profile08、auth、role prompt、两回合预算构造回归以及单角色 relay22、permission3、entry6、empty-declaration17 均 PASS；无 CLI/API/UI/model。

本切片只改 claudeLaunch、panes、P1 生成／续跑和 profile tests；relay/core/daemon/caller/Stop 业务未变，根路径校验保留。交 [前置提交脚本](commit-09b-pre.sh)：提交后再实现双角色 fake API／阶段驱动／独立 oracle，绑定实际登记正文、stop/request ID 和全局 dispatch.seq；另交可执行 launch 包审阅。当前双角色仍 plan-review、launch NO_GO，09B/09C 实跑与独立 reviewer INCOMPLETE。

## 09B 前置产品切片提交冻结

代码提交 `b9b5fdd30bdfe9ddf6f7682f3033d956a52e41b3`，角色隔离目录、6根Claude信号预算、P1生成／续跑同步及红绿／slice1回归证据已冻结；未启动服务、CLI、API或目标。双角色驱动／独立oracle及可执行launch包留待下一段，当前launch NO_GO。

## 09B 双角色 driver／oracle 前置（主控 #188）

先取 [driver 红态](09b-driver-red-feedback-05/results.json)：登记 dispatch 正文与观察正文只差一个字符，独立 oracle 拒绝 `registered_feedback_text`。绿态 [PASS](09b-driver-green-05/results.json)：两角色根／Messages 为 I=4/6、E=6/11，合计17；stop/request/inbox/ack ID 由本次 scenario 生成，dispatch.seq 在共库全局连续，反馈 prompt 逐字来自实际登记 dispatch。seq-reset、identity、duplicate-esc 三个变异分别被 oracle 捕获。无 socket、进程、CLI、daemon、目标或模型。

交 [09B driver 及 oracle 说明](09B-DRIVER.md) 与 [可执行包静态生成器](prepare-09b-executable.py)。提交脚本会在首提交后运行 driver 证据核对及生成 `09b-executable-materials-01`：两个角色的独立 HOME/config/tmp/shell/requests/hooks/user-data/debug、共用 broker/state/repo、根预算、空审批、target card 的 oracle_paths、实际 target claim 绑定要求和 source tar。材料静态 PASS 仍标 launch NO_GO；不启动任何真实 CLI/API/目标，批准前不填 attempt/fence/null 占位。

## 09B role_file 单路径收紧（主控 #189）

先在双路径旧实现上保存 [红态](09b-role-file-red/results.json)：root/role.md 被接受，按新契约应拒绝。实现后 [绿态](09b-role-file-green-rejection/results.json) 以 `controller_launch_config_required` 拒绝 root/role.md；P1 generator、run_p1、profile/budget tests 已迁到 `roles/<preset>/role.md`，不再保留 root role fallback。

用新目录重跑的 role-only profile、budget、slice1 relay/permission/entry/empty 回归和 driver red/green/seq-reset/identity/duplicate-esc 均保存；driver 绿态仍 I=4/6、E=6/11，全局 dispatch.seq 与登记正文校验保持。旧目录全部保留，不覆盖。提交脚本 allowlist 已同步新 role boundary test、role-only 输出与材料文件；仍不启动真实 CLI/API/目标。

## 09B driver 首提交与可执行 launch 包静态冻结

driver／oracle source `31b45c0232eaaa79b81447040871204494e5f58d` 已冻结；纯夹具 red→green→反例通过，I=4/6、E=6/11、合计17、模型0。新 [可执行包](09b-executable-materials-01/static-check.json) 静态 PASS，双角色新 root/manifest/独立目录、target card oracle_paths、空审批与 source tar 均读回；`launch_status=NO_GO`，无目标 claim、attempt/fence、CLI/API/目标启动。

## 阶段 A runner 拒绝路径 spy（主控 #191）

[09b-run-spies-06](09b-run-spies-06/results.json) **PASS／5项**：实际 runner entry 对 approval 字段伪造和 source_revision 不符均在 spawn 前退出，`spawned=false`、无新增 run root；attempt 回执缺任一 attempt/session/fence/thread/workspace 的纯入口变异被拒，去掉该检查的变异被 oracle 放过。阶段 A 正式 runner 尚未执行，未启动 daemon、fake API、target、CLI 或模型。说明与模板见 [09B-RUN-SPY](09B-RUN-SPY.md)。

## 09B 阶段 A runner 与可执行包静态冻结

runner source `661064d70bfd264825af3e0e51936e766aef8748` 已冻结；默认无 approval 不 spawn，A 阶段批准后才创建 root、detached fake API/daemon、card/dispatch/claim target 并写 readiness。新 [executable-02](09b-executable-materials-02/static-check.json) 静态 PASS、launch NO_GO；没有执行 runner、没有真实 CLI/API/目标，阶段 B/C 未启动。

## 阶段 A 材料 revision lineage 修复与 spy 绿态

旧 [stage-a-01](09b-stage-a-01/result.json) stale 红态保留：spawned=false、无 root。runner 现要求材料 revision 是 HEAD 祖先，revision..HEAD 只允许本票证据目录，并拒绝 workbench/scripts/runner 自身变化。新 [materials-03](09b-executable-materials-03/static-check.json) 静态 PASS；[revision spy](09b-run-revision-spy-03/results.json) 绿态接受当前 lineage，workbench/src 反例拒绝，spawned=false。仍未执行阶段 A。

## 阶段 A 卡片预检修复（主控 #195）

`09b-stage-a-03/result.json` 留存本次真实入口的失败：阶段 A 已创建 root 并启动两个假 API 与 daemon，但在 `card_save` 被 `invalid_task_card` 拒绝；原因是 `paths.deny` 使用了门禁不接受的 `oracle/**` 通配路径。此失败没有 dispatch、claim、target 或 Claude CLI；原 root、日志与 approval 现场保持不动，cleanup 脚本只绑定该 root 与记录的 PID，先做两次 lstart 身份核对。`--dry-run` 只列出 daemon_stop、逐 API 一次 SIGTERM、归档和删除动作，不发信号或删除；正式归档逐个普通文件比对字节，目录核对类型、符号链接核对目标，任一身份或归档比对不符即 `BLOCKED`。

按 `taskCards.validateTaskCard` 的实际 schema，卡片现使用 `paths.deny: []`；oracle 文件由 `oracle_paths` 精确路径声明并受门禁保护，不能由 `red_commands.test_paths` 交叉覆盖。旧的 [card preflight](09b-card-preflight-green-04/results.json) 与新的 [runner card preflight](09b-card-preflight-runner-06/results.json) 均先用真实 Node 门禁验证空 deny 卡通过，再验证 `oracle/**` 被拒；两次预检都没有创建 root、daemon、API 或 target。

runner 已将卡片构造与真实 `taskCards.validateTaskCard` 预检移到 root 创建、编译 receiver、假 API／daemon／target spawn 之前；因此同一类坏卡会在 runtime spawn 前取得 `spawned=false` 红态，修正卡片后才允许继续阶段 A。材料冻结将使用 materials-04 的新 revision；本轮仍未启动阶段 A、真实 CLI、目标或模型，launch 继续 **NO_GO**。

cleanup 的归档 helper 用临时目录取含普通文件、目录和符号链接的夹具验证逐成员字节／类型／目标读回 **PASS**；#195 实例 cleanup 尚未运行，等待主控先运行 dry-run 再运行正式清理。

## 阶段 A 假 API 停止死锁与 SIGKILL 恢复（主控 #197/#198）

正式 cleanup 在认证 `daemon_stop` 后按身份核对只向 62217 发送一次 SIGTERM；15 秒未退出即 `BLOCKED`，62218 未发信号，root 保留。`09b-stage-a-03-cleanup/sample-62217.txt` 记录 Python 信号处理函数在 `serve_forever` 同线程调用 `server.shutdown()` 后停在 `__psynch_cvwait`，因此旧 cleanup 结果与 sample 原件不覆盖。

新 [recovery cleanup](cleanup-09b-stage-a-03-recovery.py) 只绑定该 root 与两个记录 PID，先 dry-run 做双读身份核对；正式阶段确认 daemon 已退出后分别各一次 SIGKILL，逐成员归档并比对普通文件字节、目录类型、符号链接目标，读回 PASS 才删除 root。dry-run 与正式输出目录已列入 run-04 allowlist；主控实际读回 **PASS**：两个 SIGKILL、归档 71 成员／25,523 字节逐个比对 PASS，root 已删。

假 API 停止路径当前实现先取得 [SIGTERM 两秒超时红态](09b-fake-api-stop-red-07/result.json)，随后修为信号处理器抛 `SystemExit(0)`，取得 [两秒内退出绿态](09b-fake-api-stop-green-08/result.json)。两次均为独立短命真实进程，测试根已删除；runner 继续引用同一修复后的 `t078_09b_fake_api.py`。工作树 38 项逐项归属预检 [PASS](09b-run-04-ownership-preflight-09.json)，materials-04 重冻待提交脚本运行，launch 仍 **NO_GO**。

## 阶段 A 卡片预检、假 API 停止修复与 materials-04 冻结

#195 的 `09b-stage-a-03` 与 #197/#198 cleanup BLOCKED 现场均保留：坏卡红态未 dispatch/claim/target；首个假 API 的 SIGTERM 死锁由 sample 证据确认，恢复脚本先 dry-run 再对 62217/62218 各一次经身份核对的 SIGKILL，归档逐成员读回 PASS 后删除 root。假 API 停止测试先取当前实现 SIGTERM 两秒超时红态，再以 signal handler 抛 `SystemExit` 取得两秒内退出绿态。runner 仍先经真实 `taskCards.validateTaskCard` 预检，空 `paths.deny` 由 `oracle_paths` 承担 oracle 保护；materials-04 静态冻结继续 `launch_status=NO_GO`，本轮不启动阶段 A、CLI、目标或供应商模型。

## 阶段 A-04 receiver 启动红态与修复（主控 #200/#201）

`09b-stage-a-04/result.json` 保留真实红态：门禁 `card_save`、`create`、`dispatch`、`claim` 全部成功，attempt `f1dd4297…`、fence `1`、thread `a7b98242…`、workspace 均由真实回执提供；失败发生在 `pane_process_info`，shell `68179` 的 `leader=null`，复查仍只有 `/bin/zsh`。只读 [readback](09b-stage-a-04-readback-01/result.json) 通过真实 CLI 读取 `daemon_status`、`launch_show`、`pane_status`、`pane_process_info`、`pane_output`、`orchestration_events`，没有向 pane 输入、没有 signal/stop。pane 原文是 `create sessions: File exists` 后回到 zsh 提示符；launch-config 的 `codex_bin` 与 launch argv 第一项均为 target receiver，路径存在，但进程列表没有 receiver。事件只有 `pane_started` 与 `dispatch_queued`，所以不是读取时序或缺 dispatch。

根因为 runner 在 `target/home/sessions` 预先创建目录，而 deterministic receiver 自己用 `mkdir(..., 0700)` 创建 `CODEX_HOME/sessions`；`mkdir` 返回 `EEXIST` 后退出，故 shell 没有 foreground leader。runner 已删除该预创建；[receiver launch 回归](09b-receiver-launch-green-10/result.json) 在空隔离 HOME 中编译并启动真实 receiver，收到 READY、自动创建 sessions 与 `receiver-started.json` 后退出，PASS。阶段 A-04 cleanup 脚本按 root/PID 绑定，先 dry-run，再认证 `daemon_stop`、确认 shell/daemon 退出、各 API 一次 SIGTERM（两秒内）和逐成员归档读回后删 root；未运行时保持 `INCOMPLETE`，launch 继续 **NO_GO**。

## 阶段 A-04 receiver 修复与 materials-05 冻结

真实 Stage-A-04 红态已读回：dispatch/claim 回执完整，但 pane 只有 zsh，屏幕 `create sessions: File exists`，launch-config receiver 路径存在而未启动；根因是 runner 预创建 CODEX_HOME/sessions。已删除该预创建并以空 HOME receiver 进程回归 PASS。A-04 cleanup dry-run/正式 PASS，两个假 API 各一次 SIGTERM 均在两秒内退出，归档逐成员读回后 root 删除。materials-05 静态 PASS，launch 继续 NO_GO；未启动新的 Stage A、供应商 CLI 或模型。

## 阶段 B 单角色审批门禁与 B1 材料（主控 #202/#203）

A-05 真实 readiness 保留：attempt `766c797e…`、fence 1、thread `c6961479…`、target leader `70839`、shell `70837`、fake API `70730/70731`、daemon `70733`，roles_started=[]、模型0，现场不清理。

新增 `run-09b-stage-b.py` 实现阶段 B 入口核对与执行委托：从 A-05 readiness 重新读 root、attempt/session/fence/thread/workspace，并对所有 PID 重新读取 lstart/command；approval 必须逐 role、逐 phase、逐屏绑定同一 binding，安全提示逐字匹配，信任只接受 `ArrowDown → Yes, I trust this folder → Enter`，工具许可只一次性 Yes。`RoleGate` 拒绝同时启动第二角色并要求 ideation→executor。`--dry-run` 只验证门禁；去掉该标志后只调用既有 `run_t078_p1.py` 的单个 `launch`/`screen`/`key` phase，不另造 CLI 或 pane 通路，每次调用后保存原件并停下。

[Stage-B spies](09b-stage-b-spies-03/results.json) **PASS**：缺 B approval、readiness/binding 不符、第一角色 active 时启动第二角色均拒绝；去掉这三项检查的变异分别接受坏 approval、陈旧 binding、并发角色。合法 ideation B1 approval 纯校验通过且 `spawned=false`。已生成绑定 A-05 root、实际 fake API URL/PID 的 [ideation P1 材料](09b-stage-b-ideation-p1-01/) 与未签字 [approval 草稿](stage-b-ideation-approval.json)；无 Claude CLI、pane 输入、daemon/API/target/model 新启动，待主控签字后再逐项执行。

## 阶段 B materials-01 静态冻结

B1 仅冻结逐角色审批门禁与 screen-key 计划，绑定 A-05 readiness；spies-02 PASS，含缺 approval/binding/并发三项变异红态，spawned=false；materials-01 静态 PASS 且 launch NO_GO。未启动 Claude、pane 输入、API、daemon、target 或模型。

## Stage-B B1 P1 prerequisite red/green correction

保留 `09b-stage-b1-ideation` 红态：run_t078_p1 在 spawn 前因 A-05 root 缺 `scenario.json` 退出，p1 exit=1、p1_stderr 含 FileNotFoundError/scenario.json；CLI 未启动这一事实以主控 #207 的 pgrep 读回为准，不从旧 result 推断。补齐 root/input、nonce、scenario 与角色隔离目录后，独立 prerequisite preflight-02 PASS，未启动任何进程。runner 现在传播 p1 非零退出，并分别记录 p1_spawned 与 cli_spawned；approval-02 重新留空签字字段，材料-02 静态 launch NO_GO。

## Stage-B existing API reuse 与首屏 Messages 证据（主控 #221/#222）

reuse resolver 的红绿与读回：旧 `reuse-red-02` 保留 `reused_api_identity_changed`；`reuse-green-07` **PASS**，`cli_spawned=false`、无第二 API。`readback-02` 对 PID 70730 的完整 argv/lstart 两次读取一致，实际脚本为 `workbench/tests/t078_09b_fake_api.py`，role root/role/port 与 A-05 readiness 逐项一致；resolver 变异单测覆盖 pid、role、stage、非法端口、readiness 不符五类拒绝。

关于首屏是否发送 Messages：现有 slice1 green-3 原始 `api.jsonl` 的首个 `/v1/messages` 记录发生在提交 `P1_NONCE_...` 之后；`p1-materials-08e/launch/result.json` 的 launch 阶段只记录 process startup，明确没有首屏抓取或输入。证据因此只能证明在已实跑链路里 Messages 出现在提交之后，不能把“首屏前绝不发送”上调为已验证结论。真实 B1 若在 onboarding/首屏阶段发送 Messages，当前 09B 假 API 的业务 endpoint 返回 409，启动将停在该协议错误；B1 approval-10 保持逐屏与首屏停止，I1 之前必须另取该时序的真实请求证据并实现对应应答。

## Stage-B bounded API reuse/readback materials-04

完整 fake API argv/lstart resolver与五类 mutation red/green PASS；readback-02 argv_match true、两次身份一致；reuse-green-07 PASS，cli_spawned=false，A-05 无新 API。approval-10 留空签字，首屏 Messages 时序未在本阶段观测，slice1 证据只证明提交后请求。materials-04 静态 PASS，launch NO_GO。

## B1 task binding/runtime path correction materials-05

保留 approval-10 签字件、dry-run 与真实 B1 NameError 红态；复用分支现绑定 A-05 task 并将 runtime-input 写入按 label 的 P1 输出目录，controller-start 参数构造测试 PASS，删 task 变异被拒。approval-11 留空，materials-05 静态 launch NO_GO，A-05 现场不清理。

## I1 offline Messages protocol red/green

离线 I1 绿色请求 1 Messages/1 root，SSE 四事件；正文、dispatch.seq、request_id、role、预算五类变异均被独立 oracle 拒绝。无 socket/API/CLI/daemon/target/model；I1 待批材料绑定实际 ideation session/target attempt，launch NO_GO。

## A-06 full protocol offline materials

最终协议假 API 离线覆盖 I1-I4/E1-E6、全局 seq/登记正文/身份/预算与 SSE；green 10 stages、I 4/6、E 6/11，四类变异拒绝。A-06 材料静态 PASS、launch NO_GO；A-05 cleanup/历史证据保持。

## A-06 final protocol HTTP red/green 与 A-05 cleanup provenance

A-05 cleanup 实跑后，脚本仅在事后补充 `archive_bytes=archive.stat().st_size` 字段（归档已存在、原 `result.json` 不改写）；原因是正式结果当时只记录 archive path/inventory/readback，缺归档字节数。原运行读回与归档保持不变。

`09b-http-protocol-red-green-01` 用真实 loopback 服务取红/绿：旧阶段 A 模式 `/v1/messages` 返回 409；`--protocol` 模式按共享 `t078_09b_protocol_core.py` 返回 SSE 200；正文、seq、身份、role、超预算五项均返回 409。未启动 Claude、daemon、target 或供应商模型。A-06 runner/prepare 将引用同一 protocol core 与 fake API 文件，材料重冻前仍 launch NO_GO。

## A-06 executable packet root gate and shared protocol freeze

保留 A-06 阶段 A 红态：旧自造材料缺 static.root，在复制静态夹具处 KeyError 并建空 root；新 runner 在建 root 前拒绝缺 root/oracle/repo 字段，gate green spawned=false。A-06 materials-06 改由 prepare-09b-executable.py 同一格式生成并以 `--protocol` 记录，包含 shared protocol fake API/core，launch NO_GO。阶段 A 运行命令固定带 `--protocol`，让实际服务和离线 oracle 共用协议入口。

## A-06 B1 ideation P1 materials

A-06 stage A readiness 已保留并绑定新 root；生成 ideation P1 材料，input 使用 `http://127.0.0.1:0` 模板，实际 API root/readiness 由 B1 approval 的 reuse 参数绑定。只读前置校验 PASS，未启动 CLI/API/daemon/target。空签字 approval 的 dry-run 被 runner 在 spawn 前拒绝，结果保留为 INCOMPLETE、spawned=false、cli_spawned=false。

## A-06 B1 ideation readback and I1 protocol driver

主控已签 B1 approval 并完成 A-06 ideation 首启、逐屏主题/安全说明/信任选择，停在 s13 idle；B1 executor approvals、环境和原始读回全部保留。I1 新 driver 先取离线/spy 绿态与正文、seq、身份、stop/request、角色、预算六类 409 反例；真实路径只登记一条 dispatch，写入实际 request/stop ID 后 release 一次，预期 1 root/1 Messages，收到响应并 idle 即停。I1 材料 launch NO_GO，未启动新东西。

## A-07 protocol matrix and A-06 cleanup handoff

I2–I4/E1–E6 离线矩阵逐阶段绿态与 409 反例 PASS，ideation 3 阶段、executor 6 阶段，均只写登记和读取共享 protocol core；未启动服务。A-06 owner-bound cleanup 脚本绑定 root、daemon、target、Claude shell/CLI 与两个 API，dry-run 后才允许 daemon_stop、API 一次 SIGTERM、归档逐成员读回和删除。A-07 09b-executable-materials-07 由同一 prepare-09b-executable.py --protocol 生成，协议标记为 a07-registered-anthropic-v1；Stage A/B1 approval 均留空，launch NO_GO。

## A-07 I1 materials

A-07 readiness、B1 P1 launch/session 与 ideation API 5436/54603 的实际绑定已读回；I1 材料预期 1 root/1 Messages，正文、dispatch.seq、request/stop ID 登记方式和停止条件均冻结，approval 留空、launch NO_GO。B1 signed approval 的冗余 api_reuse 元数据仍指向旧 A-06，已单独审计为 INCOMPLETE，签字证据未改写；I1 使用正确的 A-07 readiness/API root。

## A-07 I1 materials

A-07 readiness、B1 P1 launch/session 与 ideation API 5436/54603 的实际绑定已读回；I1 材料预期 1 root/1 Messages，正文、dispatch.seq、request/stop ID 登记方式和停止条件均冻结，approval 留空、launch NO_GO。B1 signed approval 的冗余 api_reuse 元数据仍指向旧 A-06，已单独审计为 INCOMPLETE，签字证据未改写；I1 使用正确的 A-07 readiness/API root。

## A-07 hookTrace binding red/green

真实 cli.ts signal 入口在旧布局假设下取得 invalid_hook_trace_binding 红态；修复后允许 `root/roles/<preset>/hooks`，正确 preset/launch 绿态通过，错 preset/错 launch 仍拒绝。A-07 I1 active 卡住分析保留：Stop/pane stop/emergencyStop 均不能由 operator 合法收回，只有认证窗口用户 Esc/声明路径或 A-08 重建可继续。

## A-08 static packet and parameterized generators

A-07 owner-bound cleanup script已交主控运行；A-08 materials-08 由同一 prepare-09b-executable.py --protocol 生成，协议标记 a07-registered-anthropic-v1。B1 P1 与 I1 生成器均从显式 --stage-a/--p1 读取真实 readiness/input/manifest，不写死 A-06/A-07 路径；approval 从实际输入生成并留空。A-08 launch NO_GO。

## A-08 registration newline normalization

实测 A-08 UserPromptSubmit trace 的 prompt 没有末尾换行，而旧 dispatch registration 保留 prompt 文件尾换行，导致 exact block。产品登记现在只去除末尾 CR/LF，内部正文仍逐字比较；真实 signal 红/绿与中间正文变异反例均保留。A-08 active 的合法收回仅是认证窗口用户 Esc/声明路径；本轮不操作现场，等待 A-09 裁定。

## A-09 packet and A-08 cleanup

A-08 owner-bound cleanup script dry-run/formal由主控运行后归档读回；A-09 materials-09 由同一 prepare-09b-executable.py --protocol 生成，协议标记 a07-registered-anthropic-v1。Stage A approval 与 B1 template 留空，screen approvals/tool approval 完整，launch NO_GO。

## A-09 queued I1 recovery

登记只移除末尾 CR/LF；真实 signal 红绿和 A-09 spy 通过。产品没有 queued cancel API；新增 --resume-queued 只读 pane_status/orchestration_events，核对真实 id/seq/原文后写登记并 release，不重新派发或伪造字段。A-09 execute-01 红态保留，execute-02 命令等待主控裁定。

## A-10 API role binding and raw HTTP evidence

A-09 live API 红态原件记录 name ROLE 未定义，11 次重试均只回 409；A-10 修复从 --role 赋 ROLE，并按序保存 request/response 原文。真实 Claude 2.1.296 请求原件出处为 slice1-green-3-readback/api.jsonl；A-10 loopback test 使用该结构，launch NO_GO。A-09 owner-bound cleanup 脚本绑定新现场参数，未运行。

## A-10 phase-parametric I2 driver

I1 regression and I2 spy 均 PASS；driver 现在按 I1–I4/E1–E6 阶段选择 role、Messages budget 和 ACK，I1 默认行为保留。I2 材料由 --stage-a/--p1 读取真实绑定生成，launch NO_GO。

## Protocol I1 tool/inbox stage oracle

冻结 protocol 的 I1 离线绿态实现 I_SEND_STOP tool_use、tool_result、实际 stop/wake 关联；I2/E1 材料边界按协议保留。A-10 管道回合已计入 ideation 4/6（1 root/1 Messages），Protocol I1 追加 1 root/2 Messages 后仍在预算内。未启动或发送。

## A-10 cleanup handoff and A-11 protocol budget

A-10 owner-bound cleanup 已执行 PASS：daemon_stop 关闭 Claude/目标，API 23489/23490 各一次 SIGTERM，七个进程退出；逐成员归档读回后 root 已删除。归档路径为 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a10-cleanup/fixture.tar.gz。批准引用为“主控 #281 T-078 A-10 owner-bound cleanup (executor)”。A-10 cleanup command 保留 dry-run 与正式两条实际命令。A-11 excludes the independent A-10 1-root/1-Message pipeline turn from the 09B budget. Frozen protocol budgets are ideation I1-I4 = 4 roots/6 Messages and executor E1-E6 = 6 roots/11 Messages. A-11 Stage A is prepared with protocol fake APIs and no role CLI spawn; launch remains NO_GO.

## A-11 Stage A and ideation B1 preparation

A-11 Stage A 已由主控 #282 批准并实跑 PASS：readiness READY_FOR_APPROVAL，root `/private/tmp/t078-2-09b-run-j0ogu5t7`，daemon 24112，target shell/leader 24203/24205，ideation/executor protocol API 24109/24110；本提交保留签字 approval 与全部原始输出。
ideation B1 P1 材料从本次 readiness 生成，复用 `/private/tmp/t078-2-09b-run-j0ogu5t7/roles/ideation` 的既有 API；签字批准绑定实际 attempt/session/fence/thread/workspace，逐屏 onboarding 与一次性工具许可模板完整。dry-run PASS、spawned=false、cli_spawned=false；本轮未启动角色 CLI、未发送输入。

## A-11 ideation B1 onboarding and protocol I1 materials

A-11 ideation B1 process launch PASS：实际 process manifest 保留于 `09b-a11-b1-ideation-p1-01/09b-a11-b1-ideation-01/`，真实 vendor model turns=0。onboarding 材料逐屏单键、security notice 原文、trust ArrowDown→Enter 和 0 Messages 断言已冻结；本轮未发 onboarding 按键。
Protocol I1 材料绑定本次 launch/session/target binding，登记 I_SEND_STOP tool_use、一次 PermissionRequest、tool_result 第二条 Messages、实际 Stop/relay wake 独立读回；离线 shared-core green 与工具 ID/entry/target/seq/role/text 409 反例随包保留。I1 approval 留空，executor B1 未启动，未发送 I1。

## A-11 ideation B1 onboarding and protocol I1 materials

A-11 ideation B1 process launch PASS：实际 process manifest 保留于 `09b-a11-b1-ideation-p1-01/09b-a11-b1-ideation-01/`，真实 vendor model turns=0。onboarding 材料逐屏单键、security notice 原文、trust ArrowDown→Enter 和 0 Messages 断言已冻结；本轮未发 onboarding 按键。
Protocol I1 材料绑定本次 launch/session/target binding，先由 dispatch phase 停在 PermissionRequest 并保存 screen.bin，再由独立 permission phase 通过 Electron window 入口核对完整 Bash 命令、一次性 Yes/Enter，随后完成 tool_result 第二条 Messages、实际 Stop/relay wake 独立读回；离线 shared-core green 与工具 ID/entry/target/seq/role/text、早按键/屏幕变化/错误 dispatch 反例随包保留。I1 approval 留空，executor B1 未启动，未发送 I1。

## A-11 ideation B1 onboarding and protocol I1 materials

A-11 ideation B1 process launch PASS：实际 process manifest 保留于 `09b-a11-b1-ideation-p1-01/09b-a11-b1-ideation-01/`，真实 vendor model turns=0。onboarding 材料逐屏单键、security notice 原文、trust ArrowDown→Enter 和 0 Messages 断言已冻结；本轮未发 onboarding 按键。
Protocol I1 材料绑定本次 launch/session/target binding，先由 dispatch phase 停在 PermissionRequest 并保存 screen.bin，再由独立 permission phase 通过 Electron window 入口核对完整 Bash 命令、一次性 Yes/Enter，随后完成 tool_result 第二条 Messages、实际 Stop/relay wake 独立读回；离线 shared-core green 与工具 ID/entry/target/seq/role/text、早按键/屏幕变化/错误 dispatch 反例随包保留。I1 approval 留空，executor B1 未启动，未发送 I1。
A-11 scene-01 的真实 Claude Bash schema 要求 input.command，不接受 argv；12 条请求使 I1 Messages 计数为 12/6，A-11 不再继续，修复后必须重建 A-12。

## A-11 owner-bound cleanup and A-12 rebuild packet

A-11 cleanup is prepared with root `/private/tmp/t078-2-09b-run-j0ogu5t7`, API 24109/24110, daemon 24112, target 24203/24205 and Claude 29924/29925; dry-run and formal commands are both frozen, with external archive/readback before deletion. A-11现场未在本轮操作。
A-12 materials-12 was generated from the current source revision with protocol=true, fresh root proposal and blank Stage-A approval. The prior A-11 I1 schema failure and 12/6 Messages overrun remain evidence; A-12 launch is NO_GO.

## A-11 cleanup and A-12 B1/I1 packet

A-11 owner-bound cleanup dry-run/formal PASS：两个 protocol API 各 SIGTERM 一次，七进程退出，逐成员读回后 root 删除，归档在 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a11-cleanup/fixture.tar.gz`。A-12 Stage A READY_FOR_APPROVAL，root/API/daemon/target 绑定与签字 approval 保留；ideation B1 onboarding、0 Messages 断言和 split protocol I1 材料均为 NO_GO 静态准备，本轮未启动角色、未发送输入。

## A-12 I1 Electron permission acknowledgement fix

A-12 I1 dispatch reached the bound PermissionRequest; the first permission attempt produced terminal_focus_intercepted observations but no daemon window_input/terminal_input_write_intent. Root cause was electron_driver terminal-key returning after native sendInputEvent without awaiting the product window IPC receipt. The fixed permission path awaits window.a2a.input(\r), while preserving the bound Electron window, dispatch and one control action. Original execute-01 failure remains; offline red/green oracle covers receipt absence and corrected path. No retry or real key was sent by this fix packet.

## A-12 I1 step3 unique Electron slot

The first permission attempt failed before key delivery because the build slot was already occupied. The new permission runner derives a unique slot from the output label (`execute-02`) and the launch; the signed permission-approval-03 remains blank for review. Original execute-01 logs are retained, and offline slot red/green proves collision rejection and unique naming. No input was sent by this fix packet.

## A-12 closeout and A-13 packet

A-12 redaction PASS：保留 12 requests/1 response 的 tool_use/tool_result 与错误码，未复制 raw logs、debug、system/tools/auth 或凭据。A-12 owner-bound cleanup dry-run/formal PASS；API 93826/93827 各 SIGTERM 一次，daemon_stop 关闭 Claude/target，逐成员字节读回 PASS 后删除 root，归档在 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a12-cleanup/fixture.tar.gz`。
A-13 rehearsal PASS：真实 daemon/bin-inbox/Stop/relay 链路五项检查通过，错 launch exit 2 且 stop 条目数保持 1；无 Claude/API/model，scratch 自行删除。A-13 materials-13、Stage A、B1、onboarding 和 protocol I1 三步模板均为 NO_GO 写文件准备，binding/签字栏留待实际 Stage A/B1 结果。

## 主控 #298：离线角色 pending 契约的红态与实现计划

用户已选择“条目留存，等角色上线再投递”，答复为 `20261016T012505Z-ideation-answer-001`。本轮只整理红态和计划；产品代码未修改，新契约 **INCOMPLETE**，A-14 **NO_GO**。

`09b-pending-live-red-01/readback.json` 通过真实门禁只读取得 A-13 事件 116/117：stop 已正确追加，投递为 undelivered/role_session_missing，relay 返回 wake_undelivered，发送方收到 gate 反馈派发。没有复制 raw API/Claude 日志或凭据，也没有发送输入、Stop、重试或回收现场。

复用 A-13 排练的真实 daemon/bin-inbox/UPS/Stop/relay，新增 `--recipient-offline` 场景；`09b-pending-chain-red-01` 与阶段脚本实跑 `09b-pending-chain-red-02` 均精确复现“一条 stop、错误 relay 结果、一条 gate feedback”。子检查 exit 1 是新契约的预期红态，阶段核验 **PASS** 不代表产品通过；进程约 1 秒自行退出，scratch 已删。`09b-pending-chain-online-baseline-01` 的原有会话五项基线仍 **PASS**，不当作 pending 绿态。仅 native 进程与 PTY 边界为 spy，无 Claude/API/model。

下一步方案见 `PLAN-PENDING-DELIVERY-01.md`，主控独立重跑命令见 `09B-PENDING-RED-COMMANDS-01.txt`。方案守住明确待上线 pending 与未知投递意图的区别、发送方事件可见、上线后的既有唤醒与 ack；单列冻结 I2 的反馈时点待主控核对，不采用先启动 executor 的替代方案、不增预算。A-13 脱敏/owner-bound cleanup、实现后绿态与反例、新独立审查及 A-14 材料尚待后续阶段，本轮不声称完成。

## 主控 #299：pending 投递实现与延后 I2

主控已批准计划 1–3 与验收矩阵，并确认用户原话的共同读法：pending 阶段反馈为零；原有一条 I2 只在条目实际 delivered 后登记，关联原 request_id/entry_id，不重做 send、不额外增加派发、不改成管道确认。依据为 answer `20261016T012505Z-ideation-answer-001` 的原话：“不再给发送方回灌反馈回合”与“protocol 与预算不变”；该答复的字节副本已保留在本票证据目录。

实现复用既有 inbox_records/inbox_deliveries、角色登记和 wake/dispatch。无 ideation/executor 会话时保留可见的 pending/role_session_missing，relay_processed 仍携带发送方 request_id；Stop 不生成即时反馈。真实 controller_start 仅把待上线条目放入 unknown 窗格的队列，初始 release 后只有 turn_submitted 才读回 delivered。延后 I2 先保存与原 request/entry 关联的意图再登记，避免重复或未知写出被重发；旧 relay_results 与 stop.created_at 不改写，120 秒无 ack 起点不重置。bare pending/unknown 不自动恢复，多会话歧义仍失败，executor ack 与权限校验保持真实 caller。

`09b-pending-local-03`：11 组 **PASS**（pending 链 13、在线 6、歧义 6、controller relay 22、controller entry 6、inbox domain 11、权限 3、epochs 7、空框声明 17、pane runtime 11、管理 inbox entry 8）。pending 链经真实 controller_start、inbox 客户端与 UPS/Stop/relay 证明首启零输入、delivered 后唯一 I2、created_at 不变、executor ack/重复 ack 和越权 ack 拒绝；native 进程和 PTY 为 spy，没有真实 Claude/API/model。worker 夹具按新语义明确区分两份 pending ack 与其余五份正常回执；其真实 Electron/worker 入口回归待主控执行，不把未跑部分记为 PASS。

中间失败均留存：green-01 未等异步反馈的提交收据即访问 active；local-02 扩展链在最后越权 ack 步骤耗尽 30 秒总期限，前 14 条子命令均正常返回，事件显示串行 Node 入口耗时数秒。现保留单调用 5 秒期限，扩展最多 17 次调用总期限 90 秒并记录各调用耗时；local-03 全过。local-02 的 scratch 尚待主控用 `cleanup-pending-timeout.py` 确认旧 PID 不存在后归档删除，不发信号。

A-13 只读脱敏归档 `09b-a13-i1-redacted-01` **PASS**：13 请求/2 响应，只保留计数、tool_use/tool_result、错误码，无 raw logs/凭据复制。A-13 owner-bound cleanup dry-run/正式命令在 `09B-A13-CLEANUP-COMMANDS.txt`，绑定原七个 PID、root 和真实 -02 manifest，新增原 B1 lstart 核对；本轮没有执行回收或发键。候选待主控冻结并安排全新独立审查，A-14 **NO_GO**，不宣称 09B 完整验收通过。

## 主控 #300：真实 worker 回归与残留 socket 清理修复

主控沙箱外运行 `09b-pending-runtime-01` **PASS**，worker-inbox 14 项断言通过；前节该回归的“待主控执行”已完成，新独立审查仍 **INCOMPLETE**。

`09b-pending-timeout-cleanup-01` 保留 **BLOCKED**：两个旧 PID 均已不存在，原脚本在移除临时 operator 文件后，对残留 `state/control.sock` 归档时因 unsupported filesystem member 停下，root 未删除。新版脚本仅对这一固定路径用 lstat 确认 socket，记录类型、路径、inode 和持有者检查；只有两次 `lsof -t` 均确认无人持有且 inode 未变，才单独删除该 socket。其他特殊类型仍由未修改的归档器拒绝；凭据文件已缺失会如实记录，不再次要求删除。

socket 原行为红态在 `09b-pending-socket-cleanup-red-01`；首次绿态夹具因 `lsof -F p` 还返回自动 fd 行而失败，原件保留 `09b-pending-socket-cleanup-green-01`。当前 `-t` 路径经真实 Unix socket/真实 lsof 实测三项 **PASS**，见 `09b-pending-socket-cleanup-green-02`：活跃 socket 不删、关闭后的残留 socket 记录并删除且归档字节读回通过、FIFO 继续拒绝。新版回收输出用 `09b-pending-timeout-cleanup-02`，只交主控执行；worker 本轮未回收保留的 scratch 或 A-13，未发信号。

README 已同步 1～6 根、角色 hook 路径、仅尾部 CR/LF 规范化以及 pending/延后 I2 语义。提交前 project-map status 的 stale 提示以最后已提交的 README 为基点，不读取未提交正文来消除历史差异；提交后重新核对，不改地图的 Verified 字段。

## 主控 #303：独立审查收尾与 A-14 待审材料

待投递产品候选 `7039840565754f7999b27061191b6506e61ef9d2`（冻结 `4b48664fd689aab8d52a8721098939067928847e`）的全新独立审查 **PASS**，见 `independent-review-pending-01.md`。主控已确认 A-13 现场与超时排练 scratch 清理完成；前节的待清理/待审状态已收尾，不复用其 PID。审查覆盖范围不等于整张 T-078 或完整 09B 通过。

用户答复 `20261016T012505Z-ideation-answer-001` 要求“目标角色没有会话时”留存 pending、发送方可见、不回灌反馈，同时 protocol 与预算不变。pending 零反馈、条目实际 delivered 后才登记原有 I2，是主控 #299 对这些约束的解释；独立审查确认其与用户原话一致，但不能说成用户另行逐字批准过 I2 的延后时点。

A-14 静态材料见 `09b-a14-materials-01/PLAN.md`，冻结 protocol 逐字不变：ideation 4 roots/6 Messages，executor 6/11，七次工具许可。阶段驱动只有 I1 使用批准的 test-simulated-user 模拟窗口停止请求，经正常 pane_dispatch/release 注入；随后所有 I/E 根都读取产品实际 gate feedback/inbox wake，按实际全局 seq/request/entry/Stop 关联。I1 Stop 后必须读到 pending/零反馈；executor 串行首启 unknown 时零业务输入，主控确认空提示符后初始 release，真实 turn_submitted 后的原 send 回执才可作为 I2。不会用 operator 代发 send/stop/ack，不合成业务结果。

新增 fixture phase-plan 模式只读真实门禁记录登记 API 应答，并在同一 HTTP 请求上等待本阶段独立批准，最长 180 秒，超时拒绝后整场停止，不自动重试。该夹具等待机制及真实双角色时序尚 **INCOMPLETE**，本轮未启动 API/daemon/Claude/target、未发键。完整 HTTP/窗口证明不能由纯数据检查替代，launch **NO_GO**，需主控先审新增驱动；产品 workbench/src 本轮未改。

`09b-a14-static-check-03.json` **PASS**：冻结父版本在多根历史上确实因 tool_use_id_mismatch 拒绝；当前共享 core 作用域限定为当前登记根、按实际 POST 次数核算，完整历史 6/11 结算通过，错误工具 ID/重复当前结果/正文中间差异/seq/身份/角色/超预算七类反例均拒绝。Bash command schema 读自 A11 实际 Claude tools；I2/E1/I3 解析读取既有真实 SQLite 事件正文，但 API 日志关联在该检查内为纯数据输入，不冒称新真实 relay/HTTP 排练。输出保留 01/02/03，均为逐步扩充检查，不覆盖原件。

材料检查包含实际成功 B1 label 绑定、角色本地输入、完整 screen_approvals/tool_approval、B1 plan 的 security-notice+screen_text 与实际 key 的 onboarding-notice 分开、读屏不符用新 -02、不丢签字件、awaited Electron 控制动作回执、唯一 stage/output/launch slot、嵌套输出先建父目录、tail CR/LF 规范化，以及已知/延后生成命令路径的分类。提交脚本在第一次提交前已有本段 RESULTS，并模拟所有现有与将生成文件被两次提交覆盖；ownership 报告本身也在清单中。统一 prepare 只在源码提交后生成 executable materials-14 和静态 root，第二次提交后不再追加 RESULTS/receipt/output。

project-map status **PASS**：Problems=0、Stale living docs=0。没有修改地图或审查启动代码。所有实际阶段批准签字留空；单角色 slice1 的运行回归和新增 phase-plan 的真实 HTTP/Electron 边界检查本轮 **NOT_RUN**，待主控安排，不能用旧独立审查为新夹具背书。

## 主控 #304：A-14 无模型真实边界排练待执行

新增 `test_t078_a14_rehearsal.py`、真实 daemon 测试 host 与确定性 PTY 角色替身；范围、替代边界和确切命令见 `09B-A14-REHEARSAL-PLAN.md`、`09B-A14-REHEARSAL-COMMAND.txt`。完整排练 **INCOMPLETE**，本轮只写材料，不起服务、窗口或模型，不发键。A-14 提交/Stage A **NO_GO**，须等主控沙箱外排练读回 PASS。

请求脱敏结构直接读取 A12 实际 Claude 2.1.296 的原始请求并按白名单生成，保留消息/块/Bash schema 结构；tool_result 用 A12 已脱敏的实际 queued 回执形状。未复制 system、reminder、描述、metadata、headers 或用户凭据。替身从实际 launch settings 取得原生 signal 命令，只在本 scratch 角色上下文执行冻结 I_SEND_STOP；不由 operator 代写业务。controller 的 provider spawn/liveness 是明确替代边界，其余 daemon/relay/gates/PTY/HTTP/SQLite/窗口输入均走真实代码。managed target 的 attempt/session/fence/workspace 必须由真实 dispatch/claim 产生。

正例从缺批准、HTTP 已等待且零 SSE/工具开始，批准到位才应答；复用现有 driver 的 arm/只读 observe 和真实 Electron permission helper，只送 I1 一次 CR。验收停在 I1 pending/零反馈 → executor unknown 零业务输入 → 初始 release → delivered → 原 I2 恰一次 → E1 PermissionRequest/零按键。预期实际 POST：I1=2、I2=1、E1前半=1，roots ideation=2/executor=1；不冒称完整 E1 或后续阶段已完成。独立 scratch 的反例真实等 180 秒，409 phase_approval_deadline 后场景 INCOMPLETE、自行退出、无重试/条目/relay；汇总可将该预期拒绝记为检查 PASS，不能把场景本身升为成功。

正常收尾走 daemon_stop→panes.shutdown，API 子进程各一次 SIGTERM/2 秒确认；确认所有角色、target、Electron 已退出后 checkpoint/SQLite backup 与 WAL/SHM 一并留证、integrity_check 通过再删 scratch。全场 500 秒硬超时，失败写具名步骤与命令原件；清理不确定时 BLOCKED 并保留 root。实际退出、清理、180 秒时钟与 HTTP/Electron 本轮均未运行。

本地静态预检 `09b-a14-rehearsal-preflight-03/preflight.json` **PASS**（路径、AST、脱敏请求及 queued tool_result 构造），TypeScript host 的 `node --check` exit 0，`git diff --check` exit 0。01/02 原件保留。文档生成首次因 stdin UTF-8 SyntaxError 失败，原错误保留 `09b-a14-rehearsal-doc-write-failure-01.txt`；随后改用 UTF-8 patch 写文档，未据此修改旧运行证据。提交脚本将要求完整排练结果/两场退出和清理/真实 180 秒均通过，且当前源码与实际排练副本逐字节一致后才允许提交。当前缺运行原件，其完整 --check-only 也应拒绝；没有把归属检查当成完整提交检查通过。

主控执行 A14 无模型排练：PASS；正例 POST 为 ideation=3/executor=1；超时场景按要求 INCOMPLETE、未重试，实际 HTTP 等待 180.039063708 秒；两场 owner-bound 清理 PASS、scratch 已删除。原件：09b-a14-rehearsal-01/result.json，供应商模型 0。

## 主控 #308：A-14 executor 首启被 pending 队列阻断

主控实跑 A-14 的 Stage A、ideation B1/onboarding、I1 均 PASS；I1 实际 2 POST/2 response、一次许可 Enter、stop `7d260ac3…` pending/role_session_missing、relay ok、feedback=0。executor B1 上线后正确只登记 inbox 队列，未 paste/submit、API 0 POST；首个主题键却被 screen_requires_startup 拒绝，未发键。旧无模型排练跳过了 executor onboarding，因而未覆盖这项真实交汇，不把其 PASS 外推为首启可用。

根因与范围见 `STARTUP-PENDING-308.md`。产品仅从 screenKey/assertStartup 删除 `!pane.queue.length`，其他条件及三次检查位置不变；screenKey 不 drain，drain 的 idle 前提不变。旧实现领域红态 `09b-startup-pending-red-01` 精确复现首键零写入拒绝；修复后 `09b-startup-pending-green-02` 15/15 PASS，六键期间仍 unknown/active null/队列原样/零业务提交，初始 release 才写出一次。其余启动状态、异步草稿变化、executor 权限、屏幕字节和前台身份反例仍拒绝。输入来自实际 A-14 队列与已签首启屏幕；这是 Panes/store 领域重放，PTY/身份为 spy，不冒称完整实际窗口。

另给真实 gate CLI/daemon/Stop/relay 的离线排练扩展与旧谓词反事实脚本 `run-startup-pending-entry.py`，覆盖 pending→上线队列→六个首启键→release→delivered→原 request 的 I2→ack/负例。当前入口阶段 INCOMPLETE、待主控沙箱外运行；本轮已完成路径/源码前置与 Node 语法检查。首次 Python 脚本检查的多余方括号 SyntaxError 保留为 preflight-failure-01，修复后 preflight-01 PASS。

A-14 本身续行 NO_GO：daemon 持有旧 ESM 方法，P1 批准包的 panes.ts 与修复后源码逐字不同；不改旧包、不跳核对、不热补丁、不重启接管旧 PTY。完整 s1 新 label 命令仅作为 `09b-a14-s1-retry-NO-GO.json` 的禁执行提案保留。主控需在新独立审查后裁定回收/新实例；本轮无按键、业务注入、release、Stop 或现场回收。一次 ps 探测被沙箱拒绝，没有请求升级；只读 SQLite 证据与原命令输出已保存，PID 不冒称本轮重验存活。

本差异独立审查 INCOMPLETE，见 `STARTUP-PENDING-REVIEW-REQUEST-01.md`；不沿用原 pending PASS，不宣布真实 Claude 首启恢复、完整 09B 或整票完成。

## 主控 #309：真实入口复验的副本漏拷

`09b-startup-pending-entry-01` 原样保留 INCOMPLETE。原始 command-2.stderr 明确为 Node MODULE_NOT_FOUND：副本未包含 `workbench/bin/inbox`，不是调用者身份、请求目录或会话拒绝。该命令根本没有加载 inbox；UPS 虽 PASS，失败库的 relay_requests/relay_results/inbox_records 均为 0，尚未到达首启键。这次不能算 queue 谓词的真实入口红态。

`09b-startup-layout-red-01` 用原副本布局在无服务条件下再次取得同一 MODULE_NOT_FOUND。修复只改排练副本组装：把真实 bin/inbox 与 package.json 连同 src、测试文件放进同一个包布局，不新增替代入口。预检和 red/green 正式运行共用 prepare_snapshot，并在启动服务前实际用副本入口执行无效命令，要求到达 inbox 参数合同而非缺模块。

`09b-startup-layout-green-01` 本地实跑 PASS：真实副本入口成功加载，预期退出 2/inbox_client_arguments；无 daemon/API/model，临时副本已删除。完整链仍 INCOMPLETE，主控下一次输出固定用 `09b-startup-pending-entry-02`，命令在 `STARTUP-PENDING-ENTRY-COMMAND-02.txt`。产品源码与 A-14 现场均未改动、未发键、未重试或回收。

## 主控 #312：独立审查 NO_GO 与完成条件补强

主控后续运行 entry-02，旧完成条件真实入口 14/14 PASS；但新独立审查 `independent-review-startup-01.md` 明确为 NO_GO／需修复完成条件：M5 key_receipt_is_delivery 在冻结领域 15/15、真实入口 14/14 均存活，仅独立时点探针检出。没有将它描述为候选产品缺陷，也不沿用原局部通过结论授予审查 PASS。

本轮不改任何 workbench/src 产品代码。领域两个正例在每个按键后使用真实 A2AGates.inboxDeliveryStatus→refreshInboxDelivery→Panes.readWakeDelivery 刷新同一个原 stop；新夹具保留实际记录的 entry 身份与同库 queued 收据。真实入口排练在每个 pane_screen_key 后通过真实、认证的 inbox list 查询该 entry，逐次断言 queued、无 delivered 历史、无原 I2 intent/registered/dispatch，且 thread/message 仍指向原队列；六个时点分别保存原件。仅查未刷新行的旧做法不再作为投递证明。

审查员 M5 原始 diff、probe.diff 和注入说明从外置归档选择性保留在 `startup-receipt-oracle-312/`。先实跑 `09b-startup-receipt-legacy-M5-01`，冻结旧测试确实仍放过 M5（15/15）。新测试的最终本地运行 `09b-startup-receipt-domain-03`：候选 15/15 PASS，七次 pre-release 刷新 queued/无 delivered 历史/无 I2；M5 两项正例在第一键后的新断言实际 delivered／预期 queued，exit 1、用例 INCOMPLETE，保存了 queued→delivered 历史、unknown、一条队列和仅 ArrowUp 字节。运行器 PASS 表示确实拒绝该已知坏实现，不把变异用例升为业务成功。领域仍是 PTY/进程身份 spy，没有冒称 daemon 的 I2 调度已在本地实测。

沙箱外复验命令见 `STARTUP-RECEIPT-ENTRY-COMMAND-01.txt`，使用全新输出 `09b-startup-receipt-entry-01`，同样先精确 M5 再候选；要求 M5 在 startup refreshed delivery 0 这一新断言失败。入口完整运行仍 INCOMPLETE，主控待执行。组装与真实 inbox 加载的无服务预检已 PASS，原单调用 5 秒不变；六次查询使首启场景总期限为 160 秒、外层 190 秒，不快进时钟、不重试。新独立审查仍 INCOMPLETE，见 `STARTUP-RECEIPT-REVIEW-REQUEST-02.md`。未操作或回收 A-14，launch 仍 NO_GO。

## 主控 #316：先变基 T-082，再回收 A-14／准备 A-15

主控已完成入口复验与 startup 第二轮独立审查，`independent-review-startup-02.md` 对冻结候选 `68d7749c2`／产品 `06fc9feca` 的指定差异为 **PASS**，报告提交 `cd8ca713e1ef0ef62b1bc53c4cc33fd5fcf4e246`。原先未提交的 `09b-startup-receipt-entry-01/` 在本次交接清单中保留：候选入口 14/14、六次真实 queued 刷新；M5 在首键后的新断言失败。该结论仅属变基前差异，不外推为完整 09B 通过或 A-14 可续行。

按主控 #316，暂停刚开始的 #315 文件准备，先把 exec/t078 变基到固定 main 提交 `0e6c2b833f6da64243f71d670ea45bb9116fda4d`（含 T-082）。起点 `cd8ca713e1ef0ef62b1bc53c4cc33fd5fcf4e246`，共同基点 `490de67d05a08ccf8a453a78694a106288579b47`；准备时 main 已追加一条本票决策证据，代码未越过固定目标。脚本与完整说明见 `rebase-main-3/`，先提交现有证据与两份未运行的 A-14 草稿，再备份并做有界变基；冲突保留，不自动取任一方。

`09b-a14-cleanup-owner.json` 与 `redact-a14-scene.py` 仅为 #315 已开始写的进度，尚未执行，owner-bound 清理脚本与 A-15 材料尚未完成。A-14 现场本轮没有被查询、输入、发信号或回收。本轮预检只涉及仓库、现有证据、Python 语法和项目地图；变基、冲突处理、变基后的 pending 链／startup 15 项及入口／worker 收件箱 14 项均 **INCOMPLETE／未执行**。T-082 的审查启动和结束语义须完整保留，T-078 的投递与首启语义须在新候选重证后才继续 #315。

## 主控 #319／#320：合并后回归与质量宿主引导修复

主控改用合并，提交 `859fd649765e64926c87c7eb69499854b18ae042` 已完成；本轮不再重放 121 条历史提交。唯一 relay 冲突保留 T-078 命令与 pending/反馈去重，并增加 T-082 的 review_requirements/report；core/panes 的逐段核对与本地报告转交见 `merge-main-3/RESOLUTION.md`。主控确认合并提交后地图 Problems 0／Stale 0，上一节的合并前状态已收尾。

主控沙箱外运行 `merge-main-3-outside-01`，前四段 **PASS**：pending/controller 11 组、startup 领域 15 项与精确 M5、startup 真实入口 14 项与精确 M5、worker 收件箱 14 项。T-082 启动矩阵 **INCOMPLETE**，五个用例均在宿主启动报 operator_credential_required，未到审查边界；最后六个报告/结束核对用例未运行。没有把基础设施错误当作拒收反例。

五份真实 stderr 原本已在嵌套的用例证据目录，未随 q76 scratch 丢失；原文与路径副本保存在 `merge-main-3-fix-01/`。实际质量宿主为 quality_chain_host.ts，尚未接 T-078 的私有 operator 引导；不是 daemon_acceptance_host.ts 自动合并错误，也没有发现 review 副本／pending 的产品语义冲突。本轮只改受控质量夹具：每代新路径、真实产品凭据创建、退出确认后删除；另汇总失败宿主日志至顶层并列入 run.json。产品 src/app/bin 没有变化。

`bootstrap-red-01` 先取得两代真实夹具/宿主入口均缺路径和凭据的红态；修后同一探针 `bootstrap-green-01` 四项 **PASS**（两代独立 0600/state 绑定、退出后移除、失败日志原字节复制）。只在 socket 前截断，不启动服务／PTY／模型，不当作 T-082 真正门禁验收。旧输出不改写。续跑命令 `merge-main-3-fix-01/REGRESSION-02-COMMAND.txt` 只接 T-082 两段，用新目录 `merge-main-3-outside-02`，核对先前四段 PASS 与产品源码未变，保存本次实际夹具源码副本。完整 T-082 回归仍 **INCOMPLETE／待主控执行**，A-14 回收、A-15 与完整 09B 仍待后续，不操作现场。

## 主控 #321：合并后的六段回归完成

主控沙箱外运行 `merge-main-3-outside-02` **PASS**：T-082 tracer 与四种启动边界变异共五项、六项 report/结束核对全部通过，退出码 0。连同 outside-01 的前四段，合并后的六段关键回归全部 **PASS**；outside-01 的宿主启动失败原件原样保留，不把其整体 INCOMPLETE 改写为 PASS。两轮产品源码均绑定合并提交 `859fd649765e64926c87c7eb69499854b18ae042`；第二轮另逐字保存四份实际质量夹具修复源码，凭据正常引导/回收及完整审查边界已有真实门禁运行证据。主控要求本会话直接提交本轮修复与两轮证据，然后继续只写 A-14 owner-bound 回收和 A-15 材料；本节不批准执行回收或启动 A-15，完整 09B 仍 INCOMPLETE。

## 主控 #321：A-14 回收与 A-15 静态材料

本会话已直接提交 `f2e07d077293909bd02aa19f9e0fdda85ca3e182`（质量宿主 operator 引导、日志留存、bootstrap 检查与两轮合并回归原件），钩子生成九项尾注，提交后 git status 为空。随后只准备本节文件，未访问 A-14 的当前进程、数据库、窗口或 API，未执行清理，也未启动 A-15。

A-14 固定 owner 为 root `…/t078-2-09b-run-gbxz0tyb` 与原九个 PID；两个实际 B1 manifest 均已从保存证据取值。`cleanup-09b-a14.py` 先只读双读身份/父子/前台关系，正式模式要求独立主控签字和已完成的脱敏外置归档，再经认证 daemon_stop→panes.shutdown 关闭两角色和 target；只对两个原 API 各一次 SIGTERM。原 shell 没有历史 lstart 的限制如实写进 `09B-A14-CLEANUP-PLAN.md`，不补造值。只归档计数、批准工具/排队回执、错误码、原 I1 pending 收据和状态摘要；每个保留成员按类型与字节读回，确认九进程退出后才删 raw root；不留 raw HOME/auth/debug/messages/SQLite，不删 slot。实际 dry-run、脱敏与回收仍 **INCOMPLETE／未执行**。

A-15 计划见 `09b-a15-materials-01/PLAN.md`，protocol 逐字不变，预算 I 4/6、E 6/11、模型 0。沿用已验证的 API profile `a14-approved-gate-history-v1`（协议版本名），实例 nonce/scenario/B1/按键/读屏 label 用明确的 a15 参数；提示文件也显式给出，不默认读取 A-14 材料。source_base 为当前 f2e07d077，提交脚本先冻结生成器，再由同一个 unified prepare 生成 executable materials-15 与实际 source_revision；批准字段仍空。首次提交前已有本段 RESULTS，自生预检和二次生成物都进清单，第二次提交后不追加文件。

executor onboarding 每个键后增加只读 gate inbox_list 刷新＋pane status/SQLite 观测，要求原 stop 仍 queued、没有 delivered 历史和原 I2、unknown/active=null、同一原队列，零业务写出/零 POST；初始 release 在六项通过后才允许。B1 plan 的 security-notice/screen_text 和实际键的 onboarding-notice 分开，旧屏 -02 重读、实际成功 manifest 绑定、唯一 slot/output、I1 三步与 180 秒批准期限全部沿用原路径。

`09b-a15-file-check-03` 本地纯检查 **PASS**：九进程登记字段的正例、五种身份反例、无守卫的坏 validator 拒绝；凭据哨兵被白名单剔除、额外 shell 命令拒绝、归档字节变更拒绝；六份已保存的真实首启 queued 收据通过，真实 M5 错误收据在新观测器中拒绝；两角色文件生成均为新 A15 nonce/label、正确预算、executor 六次逐键观测；旧 A14 nonce 变异被拒。测试开始前保存所用源码并在结束逐字核对，未用真实 API/daemon/角色进程或模型，不外推为 A-15 运行验收。01 是变异文本替换引发 SyntaxError 的预检失败，未算业务红态；02/03 为修正后的已知坏 nonce 拒绝，均保留。

本轮新 A-15 的完整 HTTP/Electron/Claude 时序仍 **INCOMPLETE／未运行**，launch **NO_GO**。A-14 清理批准、A-15 Stage A/B1/业务阶段批准均由主控后续逐次审签，不在本轮签字或执行。

## 主控 #322：A-14 停止已完成，归档删除余步待执行

主控运行 A-14 dry-run **PASS**、脱敏归档 **PASS**，外置 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a14-redacted-01/scene.tar.gz` 为 1,164 字节，逐成员读回通过；凭据字样扫描为 0（主控读回）。已签的 09b-a14-cleanup-approval.json 原样保留。正式清理 **BLOCKED**：认证 daemon_stop 已成功，九进程已退出，两只 API 各一次 SIGTERM；删除前再次 collect 时 SQLite 查询报 unable to open database file，root 未删。该结果不改写成 PASS，也不重发停止或信号。

本轮修复发生在上述执行之后，修改前源码与 file-check-03 副本一致并另留存于 09b-a14-cleanup-fix-01。精确变更为保留停机前现场/归档摘要比较并保存其值；停机后只验 tar 成员及摘要字节，移除第二次 collect/SQLite 访问。新增 finish 脚本只校验 #322 原回执、九 PID 缺失和原归档，再删固定 root，无 signal、daemon_stop 或 collect 调用；命令见 09B-A14-CLEANUP-FINISH-COMMAND.txt，实际余步 **INCOMPLETE／未执行**。

`09b-a15-file-check-04` **PASS**：旧后置读库表达式在数据库不可用时精确复现同一 OperationalError；新 helper 不读库而通过，归档字节变化仍拒绝；本次保存的真实停止回执及重复信号负例通过，finish 的禁用动作检查通过。该检查只用临时文件与既有证据，process_probes=0，未访问当前 root、发信号或删除现场。A-15 源码与文件包本轮按主控要求直接 Git 提交冻结，所有 launch/阶段批准仍空，不启动运行。

## 主控 #324：A-14 完成回收，A-15 Stage A 就绪

据主控 #323/#324，外置盘 I/O 曾使 finish 进程阻塞在 open()；主控在 rmtree 前结束该进程，空目录 `09b-a14-cleanup-finish-01/` 留在本机，Git 不保存空目录，本段作为其占位记录，不向旧目录写入伪造结果。恢复后 `09b-a14-cleanup-finish-01-dry-run` **PASS**，正式 `09b-a14-cleanup-finish-02` **PASS**：signals_sent=[]、root_removed=true，无 daemon 命令重发；主控确认旧 root `/private/tmp/t078-2-09b-run-gbxz0tyb` 已不存在。原 #322 BLOCKED 证据与签字不改写，A-14 回收现已完成。

主控签 A-15 stage-a-approval（#324）后运行 `09b-a15-stage-a-01`，状态 READY_FOR_APPROVAL，source_revision=`dedd4f66bc424610183cbff2d7114e991483e1c6`，新 root `/private/tmp/t078-2-09b-run-yp09xosq`，daemon=59398、target shell/leader=59550/59552；真实 dispatch/claim attempt 回执保留，roles_started=[]、供应商模型 0。后续只生成 ideation P1 的文件与未签 B1 批准，B1 dry-run/real 均由主控另批执行，不在本轮启动角色或发送输入。

## 主控 #324：A-15 ideation P1 文件已生成，B1 待审签

先以 `bcf94eaf461877325963564d1cd847954991b90b` 提交上述收尾与 Stage A 证据，九项尾注齐、工作树干净。随后只运行 ROLE-MATERIAL-COMMANDS 第一条文件生成命令，生成 `09b-a15-b1-ideation-p1-01`，实际 exit 0；未运行 executor 生成命令、B1 runner、Claude 或业务输入。生成阶段仅调用既有 TypeScript 静态构造 helper；没有启动 API、daemon 或角色进程。

本次 ideation launch=`298e0f0e-3f2c-4a76-89b5-4cd5a12053a0`、session=`be13441f-b3da-48aa-8ed4-d7f70dc3d04a`；B1 binding 与 A-15 readiness 原 attempt 对象一致，P1 input.api_url 保留动态模板，复用保存的 ideation API 59387/64830。`stage-b-approval.json` 签字字段仍空。屏幕计划与 runner 的 security-notice/screen_text 逐项一致，实际 s7 按键为 onboarding-notice；dry-run、real 的完整命令在 P1 的 B1-COMMANDS.txt。

`09b-a15-b1-preparation-01/static-check.json` **PASS**：58 个 source 文件及 root/P1 输入逐字节相同，角色独立目录和 hooks 绑定一致，批准所需字段、真实 attempt、协议预算与两条 B1 命令路径均通过；新输出目录均不存在。该检查只读文件/Git，不访问 API 或 gate、不做 ps 身份检查，也没有执行 B1 dry-run。B1 运行状态仍 **INCOMPLETE／未运行**；待主控签字后先 dry-run 读回再决定 real。实际 preflight 输出、生成 stdout/stderr 和复验脚本一并保存。

## 主控 #325：A-15 ideation B1 已启动，首屏与首键材料待执行

主控签 B1 后，dry-run 为 READY_FOR_ROLE、spawned=false；real 外层 **PASS**、cli_spawned=true、p1_exit_code=0。内层 P1 原件仍为 **INCOMPLETE**，scope 为 Process startup only，next 明确 No input has been sent；这表示只完成启动，尚无首屏或 readiness 结论。实际 manifest 保存 shell/CLI=65816/65817，launch/session 与本次 ideation input 相同。原签字件、内外层输出与 dry-run 一并以 `02afa5df7455d3afe69f66185991221dc5805e3e` 提交，九项尾注齐、当时工作树干净。

后续只运行已有 bind-launch 文件步骤，将实际成功 label `09b-a15-b1-ideation-01` 写入材料。首屏只读命令输出使用 `a15-ideation-s1-screen-01`；读回不符时只用新 -02 重读，不发键。第一键 ArrowUp 的两份可选草稿分别引用 -01/-02 原屏，签字字段均空；主控核对后只能选一份签字和执行，按键后保存 s2 快照即停。命令在 FIRST-SCREEN-COMMANDS.txt，完整说明与静态检查在 `09b-a15-first-screen-preparation-01/`。本轮未读屏、未发键、未调用 gate、未进行新的进程存活探测，未启动其他角色；首屏及首键状态仍 **INCOMPLETE／未运行**。

## 主控 #326：ideation 首启完成，readiness 与 I1 第一步待执行

主控逐屏读后分别签字完成六键（主题 ArrowUp→ArrowDown→Enter，Security notes 核对后 Enter，trust ArrowDown→Enter），每个 key_result 都 written，使用初读原件、没有 -02。s13 只读原件为 `a15-ideation-s13-screen`，主控报告空提示符、manual mode on、零业务输入。六份签字、每键前原屏与输出已先提交为 `a3c36f1ac1c7269176ff5103fcb5c4ed7ed8f07a`（九项尾注）；原 screen/key 结果仍保留 INCOMPLETE，不将其上调为整场通过。

本轮仅准备确认命令与 I1 材料。READINESS-CONFIRM-COMMAND 由主控执行时才核对原屏绑定/尾部提示符/manual、实际 POST/请求/响应计数为 0、该 launch 无提交事件，排他创建 readiness.json，不 release 或发送输入。屏幕标记核对辅助 #326 已有人工读回，不冒充独立终端渲染验收；本轮未执行此确认命令。I1 的 phase approval 补齐模拟用户输入来源、实际 synthetic_input_id、预算和只到许可屏的停止条件，approved_by/approval_ref 仍空；注入文本沿用原 i1-prompt.txt，真实驱动仅经门禁 pane_dispatch/release，API 从真实历史登记 seq、dispatch/request/prompt 关联，tool_use Bash input 使用 command。STEP1-COMMAND 输出为新 `phases/I1/dispatch-01`；父目录已存在，尚未派发、写 stage approval 或调用假 API。

I1 全回合预算 1 root / 2 Messages、一次许可；本次待批第一步只至第 1 POST 与 PermissionRequest，随后保存原屏/事件并停止。许可 Enter 与后半回合仍需另批；executor 不启动。静态语法、路径、未签字段与绑定检查的实际输出保存在 `09b-a15-i1-preparation-01`；readiness 确认、I1 第一步运行均 **INCOMPLETE／未执行**。

## 主控 #327：A-15 I1 到 pending 通过，executor 材料待批

readiness 确认 **PASS**（0 Messages、无业务提交事件）。主控签 I1 后，dispatch-01 返回 READY_FOR_PERMISSION（真实 dispatch=`c9f2322a-0526-4430-a3d6-98b376b8b140`、全局 seq=2）；核对完整 Bash command、refs 和 ❯ 1. Yes 后签 permission，一次 awaited Electron Enter。execute-02 为 **READY_FOR_EXECUTOR**：2 Messages，真实 Stop→relay 得到 ideation→executor stop `c3ab1493-5c73-4af5-947f-a0f16f19d6c7`，request=`80ef9485-80df-43f3-9791-bab43261cb5b`，relay ok、pending=true/role_session_missing、feedback_count=0、target_byte_count=0；Enter 记为 action/control。stop.created_at=`2026-10-16T10:51:40.728Z` 原样保留。这只证明 I1 阶段，不上调为完整 09B 通过。

先以 `1aded2e073d959457233a4ee06351f0b76fa8788` 提交以上原始输出与签字件，九项尾注齐、当时工作树干净。随后只执行原统一生成器的 executor 文件命令；它先核对真实 relay pending 行，再生成 `09b-a15-b1-executor-p1-01`，绑定同一 Stage A target attempt、独立 executor launch/session 和原 API 59388/64829，api_url 仍为动态模板。B1 与六键签字字段均空，dry-run/real 未运行；没有新 API、daemon 或角色进程。

executor 的 B1-COMMANDS、BIND-LAUNCH、ONBOARD-COMMANDS 与六键草稿一并冻结；实际 launch label 必须在 B1 后由 bind-launch 取得，本轮不伪造 manifest。每键后安排 expected-keys=1…6 的 observe-startup-queued，刷新本次原 stop，要求仍 queued、无 delivered 历史、无 I2、unknown/active=null、同一队列、零业务写出/POST，entry.created_at 不变；未通过不得下一键或 release。s7 实际按键 purpose=onboarding-notice，B1 screen plan 保留 security-notice + 原文；旧屏用 -02 重读，不发键。当前仅文件与命令静态核对 **PASS**；executor B1、逐屏与六项 queued 观测仍 **INCOMPLETE／未运行**，材料明细在 `09b-a15-executor-b1-preparation-01/HANDOFF.md`。

## 主控 #328：executor 首启与逐键 queued 观测通过，E1 材料待执行

主控审签 executor B1 后 dry-run READY_FOR_ROLE、real PASS/cli_spawned，实际 bind-launch PASS。六键逐屏签发且每屏初读相符，s13 空提示符/manual 为主控读回；逐键 observe-startup-queued 六次全部 **PASS**，原条目始终 queued、历史无 delivered、无 I2、unknown/active=null、零业务写出。以上原件和签字先以 `019414f9cdea56902bc668c409de65096b0b5af5` 提交（九项尾注）。原消息=`b91b5f60-62e9-4983-b48e-f73630f1f854`，原 stop/request 仍为 I1 的 c3ab1493…/80ef9485…，未重置 stop.created_at。

随后仅生成材料：executor readiness 命令再刷新一次原 queued 收据并核对 0 POST、s13 与六份原件，才创建确认；I2 空签字草稿的 arm 命令只预登记原 I2、不发输入；E1 空签字草稿的 initial-release 命令只放行原队列，到真实许可屏即停。原 I2 在 delivered 后响应的时点仍是主控 #299 对用户原话的解释，不冒称用户逐字批准。后续读回先走既有 I2 collect，再核对原 request/entry、原队列消息 turn_submitted 与 delivered 时间对应、I2 注册/提交/反馈各恰一次，预期实际 POST 为 ideation 3、executor 1；此时 E1 Enter 尚未批准。executor readiness、arm/release/collect 和读回本轮均 **INCOMPLETE／未运行**。

本轮材料检查中，直接用 mode=ro 查看历史 A-14 排练 SQLite 导致其 SHM 读标记变化；已留存变化前后两份 32,768 字节副本、来源提交与原因说明，之后逐字节恢复受控原件，未操作 A-15 现场，也未丢弃异常证据。记录在 `09b-a15-e1-preparation-01/historical-sqlite-read-side-effect-01`；后续不再直接打开历史数据库。该准备期副作用与上述真实运行结果分开记录。

## 主控 #329：原 I2 与实际投递已读回，后续阶段材料待批

executor readiness **PASS**（0 Messages）；主控签 I2 后 arm=ARMED，不发输入。签 E1 后 initial release=READY_FOR_PERMISSION：原 inbox dispatch b91b5f60…、实际 seq=3、原 entry c3ab1493…。I2 collect 和 delivery-i2-readback 均 **PASS**：turn_submitted seq 176 → feedback seq 187，delivered，关联原 request 80ef9485…/entry c3ab1493…；I2 注册/提交/反馈各一次，实际 POST ideation 3（I1 2、I2 1）、executor 1（E1）。原件及签字先以 `1010601fed408181074779263a15f495ddba924c` 提交，九项尾注齐。主控报告误重跑读回时被 output_exists; no action 拒绝、无新动作；未为该拒绝补造产物。

本轮只生成 E1 真实 PermissionRequest 的空签字草稿（permission_wait seq 195、原 command/screen/dispatch），以及 E1→E2→E3→E4→I3→I4→E5→E6 的独立逐阶段命令。七份未来 phase approval 签字字段均空；未来 permission 必须等实际 dispatch/事件后由原 prepare 生成，不预造 request/tool/ack/seq。工具阶段每次先 START 到许可屏，读屏/cmp、生成未签 permission、主控核对一次 Yes 后单 Enter，再只读 collect；I4/E6 无工具、无 Enter。自动根只消费真实 gate feedback/inbox wake，不重新 pane_dispatch、send 或代写 ack；全局 seq 按真实登记与 readback 字段核对。

预算仍 ideation 4/6、executor 6/11（共 17 实际 POST、7 工具许可、模型 0）；当前已 4 POST，E1 第二条及之后余 13 POST。E3 会同时触发 I3 与 E4，两角色可能交错；待批准而未返回 SSE 的真实 POST 也计预算，180 秒超时即整场 INCOMPLETE，不重试。所有后续运行状态仍 **INCOMPLETE／未执行**；本轮仅文件、命令路径/字段与预算静态检查，材料索引见 `09b-a15-later-stages-preparation-01/stages.json` 和 HANDOFF.md。

## 主控 #330：E1/E2/E3/I3/I4 已读回，E4 只读原屏截断需裁定

主控逐阶段签字执行，E1、E2、E3 的许可/读回 **PASS**，实际全局 seq 分别为 3、5、6；E2 的原 target 恰收到一个 Esc（1b）。E4、I3 并行 START 到许可屏，实际 seq 分别为 8、7；I3 许可及读回 **PASS**（真实越权 ack），I4 START/读回 **PASS**（seq 9、target_byte_count=1），ideation 用满 6/6 POST。主控报告 E1/E2/E3/I3 的读屏 cmp 均为 0、批准命令与原屏一致；I3 的误重复生成/读屏被已存在检查拒绝，未为该拒绝补造产物。

E4 首次单独 screen 输出 **INCOMPLETE**，报 screen_exceeds_review_limit、未写 screen.bin。只读检查已保存原返回：offset 0→65536，total_bytes=76125。进一步发现 E4 dispatch-01/permission-screen.bin 也只有 65536 字节，与该分页前缀逐字相同；因此直接补齐完整读取不能再和旧截断文件作全文件 cmp。当前 Enter 前只读校验也只取一页，AST 隔离反例用同一真实保存页证明：它接受相同前缀，却仍有 10589 字节未读。此反例没有执行 gate、Enter、CLI/API、进程或数据库操作，不能算修复绿态。

三个关联 reader 调用均在原冻结包：P1 snapshot、phase_driver 许可截图、permission Enter 前的只读比较。E5 的同一追加式累计输出也会超限；仅改一个显示函数会遇到旧参考与源码冻结检查的下一处失败。本轮不改变原文件、未签 E4 permission 草稿或运行现场；实现暂停，已上报 blocking issue `20261016T113401Z-worker:t078-e4-screen-issue-001`（工具强制 issue 送 triage，主控在当前会话同步获知）。完整事实与最小建议在 `09b-a15-e4-screen-diagnosis-01/NEEDS-DECISION.md`：建议授权同一条完整只读分页证据链、保留旧截断原件并追加引用同一实际事件的完整恢复收据、另签新 permission，以及显式新的只读 harness 源冻结；不重启角色/daemon/API，不改业务输入与预算。当前修复/续行 **INCOMPLETE／needs-decision，NO_GO**。

## 主控 #331：完整只读证据链修复，现场恢复待执行

#331 明确批准原四点建议，限测试证据链，不改业务输入、Stop/relay、protocol、预算、验收标准或产品代码。三个原 reader 调用统一为 p1_output：固定 total、连续 offset、逐页字节数、最后 EOF 再确认；变化 total、零进度、截断/缺页/越界拒绝，不重试。Enter 前必须有完整 capture，旧截断参考不能靠相同首个页继续放行。新增 check-only 在 build/窗口/按键前只验证屏幕与 active binding；原 Enter 业务段 AST 不变。

聚焦证据 **PASS（夹具范围）**：真实 P1 参数/screen 入口候选 6/6，旧 reader 的同入口红态及只读一页坏实现均被检出；permission CLI check-only 7/7，缺少完整捕获也拒绝；phase execute 许可截图原红 65536/155701、候选绿 155701/155701；恢复器 5/5，删掉前缀校验的坏实现检出；冻结范围 3/3，三个调用批准只读段以外 AST 相同。输出传输与身份均明确是隔离夹具；沙箱 /bin/ps 被拒，身份用 spy，真实身份外侧复验脚本另交，尚 **INCOMPLETE／未运行**。未用这些结果声称已经在 A-15 恢复。夹具初期的固定 node/operator.json 与 /tmp 别名错误均保留，不算产品红态。

历史审计仅查旧原件：E1/E2/E3/I3 的许可参考为 16026/32797/52533/44869 字节，均与当时保存的完整 gate total 和原屏逐字节一致，未受本次上限截断。I1 为 16322 字节，与 Enter 前 Electron offset 相同，但未保存直接 gate total；直接完整性证据仍 **INCOMPLETE**，由主控判断对旧 PASS 的影响，不改任何旧结论。E4 的 65536/76125 截断事实保留。

本次源码提交后生成新的 reader harness 冻结：原 58 文件只改三个只读 caller，其余 55 文件逐字节相同；分页 helper、恢复器、源校验入口及测试显式入包。业务源码继续标为 dedd4f66bc424610183cbff2d7114e991483e1c6，新 harness 版本从实际 Git HEAD 读取。新命令显式验证该包；P1 还传 --source-materials，不跳过原冻结检查。E4 以新 -02 完整读屏→只读追加恢复（原前缀匹配、同一 dispatch/event）→新 -03 与独立完整参考 cmp→主控签新 permission-02 后才 Enter。恢复原件与新 permission-02 由主控执行只读命令后生成，本轮不伪造现场材料。E5 从许可截图到 Enter 前都完整读取，E6 延用同一新冻结命令。

blocking issue 20261016T113401Z 的可关闭依据为 #331 范围裁定、三处统一读取、红绿及反例、追加恢复/冻结范围检查；worker 未代关，现场读屏/恢复/Enter 仍 **INCOMPLETE／未执行**，预算不变。独立 fresh review 未运行（遵守不增开 Codex/子代理），已有请求材料，不用自查替代独立 PASS。另非阻塞 issue 20261016T120838Z 提醒下一次标准 prepare 补新增 reader 闭包；本次新包完整，旧 prepare 为保持其余原包不变而未改。

源码已提交为 `c0c5caee3e70e58abadbd55efa4eade72a44370b`，九项尾注齐。随后统一生成器 --check-only **PASS**，实际生成 `09b-a15-reader-harness-01`，新包 65 文件、原包未变 55 文件、改动原 caller 3 个；source byte verifier --check-only **PASS**。harness 版本绑定该真实提交，business 仍为 dedd4f66bc424610183cbff2d7114e991483e1c6。E4 -02、追加恢复、新 -03 全文件 cmp、可选只读预检、一次 Enter、collect，以及 E5 完整流程和 E6 收尾的绝对命令均已生成；未运行任何现场命令。实际 permission-approval-02 必须在主控完成 -02 读屏且恢复器核对前缀后生成，本轮仅提供预审模板，未填假完整原件。

## 主控 #332：A-15 全阶段读回与 T-078 全票状态

主控实际完成 E4 完整读屏/恢复、签 permission-02 后 Enter、E5 全流程及 E6；新增 263 个证据文件与签字件已先提交为 `34aa4e130`（九项尾注，提交后工作树干净）。外侧 reader 复验九组 **PASS**、scene_actions=0；E4 完整屏 76,125 字节、E5 93,747 字节。旧 E4 截断原屏、screen-01 和未签 permission-01 全部保留。E4 签前 check-only 被 permission_approval_required 拒绝，签后再跑因 FileExistsError 失败、主控管道未停；该预检不算 PASS。实际 Enter 自身在 build/窗口/按键前的完整读屏及绑定校验通过，随后一次 CR 与阶段 readback 通过。BSD cmp -n 的 EOF 误报由主控用 Python 核对前缀，不据此改写旧原件。

worker 的最终只读核对 [final-check-04](09b-a15-final-check-04/result.json) **PASS**：从仍存现场的 API 文件直接计数 ideation 6 POST/6 响应、executor 11/11，17 个 HTTP meta 均 200、各完整 6 SSE，无 409；真实 hook 原件为 4/6 个 UPS 与 Stop，七个 PermissionRequest 对应七份 action/CR 回执。各 phase 的工具 command 与 protocol.commands 代入真实 ID 后逐项相等，tool_result 都是实际异步排队回执，业务成功/拒绝另由真实 Stop/relay 读回。目标基线为空、最终恰 `1b`。本轮没有调用 gate/API、窗口/按键、进程探测或 SQLite；只读脚本和完整来源在 [全场核对](09B-A15-FINAL-CHECK.md)。check-01 的 bound 字段 KeyError 原件保留；02/03 为中间核对，最终以 04 为准。

| 阶段 | 实际全局 dispatch.seq | roots / POST | 许可次数 | 门禁结果 |
|---|---:|---:|---:|---|
| I1 | 2 | 1 / 2 | 1 | 实际 ideation send；pending、零反馈 |
| E1 | 3 | 1 / 2 | 1 | worker_target_required，目标仍 0 字节 |
| I2 | 4 | 1 / 1 | 0 | 原 send 的 delivered 反馈，只确认 |
| E2 | 5 | 1 / 2 | 1 | executor 仅一次 Esc，目标为 1b |
| E3 | 6 | 1 / 2 | 1 | 实际 executor ack，伪造 --role 无效 |
| I3 | 7 | 1 / 2 | 1 | recipient_required，无新 ack |
| E4 | 8 | 1 / 2 | 1 | 重复 ack 返回同一 id，无重复唤醒/Esc |
| I4 | 9 | 1 / 1 | 0 | 实际 I3 拒绝反馈，只确认 |
| E5 | 10 | 1 / 2 | 1 | stop_already_acknowledged，无额外 Esc |
| E6 | 11 | 1 / 1 | 0 | 最终确认，Stop/idle |

预算准确为 ideation **4 roots/6 POST**、executor **6/11**、合计 **10/17**、七次工具许可、真实供应商模型 **0**。真实 CLI 两角色，确定性目标接收器；假 API 与 test-simulated-user 自动化不冒称真实模型判断或用户亲手输入。全局 seq 按事实列出，I3/E4 交错不重编号。

原 stop c3ab1493…/request 80ef9485… 在 I1 pending 时对发送方可见，feedback=0，created_at 始终 `2026-10-16T10:51:40.728Z`；executor 六个首启键后真实收据仍 queued、无 delivered/I2、unknown/active=null。初始 release 后 turn_submitted 176 才转 delivered，原 I2 反馈 187；反馈、I2 登记、提交各一次，关联原 request/entry、没有重新 send。I2 的该时点是主控 #299 对 answer `20261016T012505Z-ideation-answer-001` 原话同时要求“pending 不回灌反馈”与“protocol 与预算不变”的解释，经既有独立 pending 审查核对；不是用户逐字规定 delivered 后时点。

历史许可原屏 E1/E2/E3/I3 的直接 total 与字节一致；I1 16,322 字节虽与 Electron offset 相同，当时没有直接 gate total 原件，完整性证据仍 **INCOMPLETE**。不改旧 PASS 文件，由主控及独立审查判断其影响。用户随后选择“关闭，写明边界”，执行主控追加的 [disposition](../../../.project-map/inbox/20261016T133204Z-user-disposition-001.md) 只关闭 blocking issue 20261016T113401Z 的“原参考截断、修复范围待裁定”阻塞，不宣告 A-15/整票通过、不覆盖独立审查与 I1 历史缺口；签发原件不改，worker 未代关。非阻塞 20261016T120838Z 的标准 prepare 新 reader 闭包仍需在下一新场景前处理，本次 A-15 专门 harness 已完整。

### 全票对照验收条目

以下逐项对照原 [T-078 ticket](../../../.project-map/tickets/T-078-controllers-in-workbench.md)，不修改 ticket 的勾选或关闭状态。**整票 INCOMPLETE，未请求集成或切换日常派发。**

| 原验收项 | 已有证据与当前状态 | 仍缺／证据边界 |
|---|---|---|
| T-075 检查面；同任务两个主控＋一个 worker 的 Electron 截图/录屏 | 非 Claude T-078-1 与 A-15 真实双角色/受管目标身份已证明；各窗口/许可有原件 | **INCOMPLETE**：未将现有单窗格视图冒充三个窗格同任务联合截图验收；目标是确定性接收器，非真实 Codex |
| 用户打字、后台注入、worker 人工介入正确分类 | **PASS（已验自动化范围）**：outside-final-01、输入入口/失败方式回归；A-15 七许可 CR 均 action，注入根独立登记 | 合成组合输入、模拟用户动作不证明实际系统输入法或自然人亲手；不以本场 stop 文本当真实用户输入 |
| 空闲/忙时唤醒、回合结束送达、Esc 后用户放行 | **PASS（分场景）**：09A-3R2 clean/block；A-15 pending、六次逐键 queued、初始 release 后 delivered/原 I2；原 Esc/空框声明入口与 epochs 等回归 | 09A 绑定旧场景版本，后续局部回归与本候选整合边界由独立审查核对；不拿清理 PASS 替业务 PASS |
| 库 send/list/ack/ready 与越权拒绝 | **PASS（夹具项目）**：worker-inbox 14、四权限变异；slice1 green-3；A-15 真实角色 send/ack、实际身份、重复 ack/越权拒绝 | 日常文件 inbox 尚未退役、不双写；独立审查须覆盖合并后的 controller/worker 两种凭据边界 |
| stop→ack；无 ack 两分钟后只中断；实际调用者 | **09B PASS，整项 INCOMPLETE**：本场 stop→executor 一次 Esc→ack，伪造 from/role 无效 | **09C 未运行**：没有真实时钟 >120000ms、无 ack 且持续停止要求下 ideation 只中断的 CLI 证据。已有受控时钟测试不能替代 |
| Claude 隔离配置与真实回合授权 | **PASS（假服务阶段）**：两角色独立 HOME/config/tmp/shell/requests/hooks/user-data，实际 model 0，逐阶段主控签字 | 真登录复核 2～3 回合是原 PLAN-2 另列计划，尚未运行；不以假 API 证明供应商认证、额度或真实模型行为 |
| 8/9/18 与 T-075 正反例不退化 | 已存 8/9/18、CAS 与权限变异 **PASS**；合并后 pending/controller、startup 域/M5/入口、worker 14 与 T-082 边界/结束核对六段 **PASS**，见 merge-main-3-outside-01/02 | 完整 8/9/18 最后运行版本早于本次整合；是否需要最终冻结整组复跑交验收核对，不把局部六段表述为重新全跑 |

ticket 所列同时输入、组合输入、大粘贴、关窗、重启 unknown、重复唤醒，已有 input-failures、runtime、worker 与领域证据；实际系统 IME 未测。09B 假 API 的 180 秒批准门已经在 A-14 无模型排练由真实 HTTP/时钟验证（约180.04秒超时），它与 09C 的两分钟无 ack 规则是不同条件。

### 回收与独立审查交接

[A-15 owner-bound 回收](09B-A15-CLEANUP-PLAN.md) 与三条 [确切命令](09B-A15-CLEANUP-COMMANDS.txt) 已准备：先 dry-run 身份核对，再外置白名单脱敏归档/逐成员读回，另签后 daemon_stop→panes.shutdown，再每只原 API 一次 SIGTERM；停机后只验归档和退出，不读 SQLite。正式签字字段仍空，**dry-run、归档、停机、删除全部 INCOMPLETE／未执行**，现场与 slot 保留。

新 A15 脚本的本地 file check **PASS**，含 PID 复用/未知子进程拒绝、无守卫坏实现、凭据哨兵/原样复制坏实现、未批准命令拒绝、归档逐成员字节/变更拒绝、旧后置读库坏实现；无实际进程探测或现场清理。范围在 [file-check](09b-a15-closeout-file-check-01/result.json)。

独立审查看 [REVIEW-REQUEST-T078-FINAL](REVIEW-REQUEST-T078-FINAL.md)：业务 dedd4f66…、reader c0c5caee…、运行原件 34aa4e130；完整候选为该请求所在最终冻结提交，由主控传实际 Git 提交号。须覆盖 controller 身份/Stop 转交、pending/I2、startup/M5、输入/空框声明、只读分页证据链与三处调用、T-082 合并边界、异步 request/entry/ack 及残余验收缺口。旧三个独立审查只对原冻结差异有效，不替本次新候选背书；本轮未开子代理或自行给独立 PASS。

## 主控 #333：A-15 回收完成

主控逐命令执行：`09b-a15-cleanup-01-dry-run` **PASS**（无停止/信号/删除）；`09b-a15-redacted-01` **PASS**，外置归档 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a15-redacted-01/scene.tar.gz` **1,766 字节**、逐成员字节读回 PASS，主控扫描凭据字样 0。主控签署的 `09b-a15-cleanup-approval.json` 原样保留，不恢复为空签字模板。

正式 `09b-a15-cleanup-01` **PASS**：认证 daemon_stop 正常关闭角色/目标；API 59387/59388 各一次 SIGTERM，九进程全部退出；停机后仅核对归档、不访问 SQLite/WAL，root `/private/tmp/t078-2-09b-run-yp09xosq` 已删除；slots 未删除。worker 只读核对三个 result.json 和签字件，没有重复清理或发信号。

确认 disposition `20261016T133204Z-user-disposition-001` 由执行主控写入本 worktree 收件箱，worker 仅随 `e682a929c` 提交原件；其关闭边界仍以原文为准，不改写成 worker 代关或整票通过。独立审查候选随本次回收证据提交前进；业务/reader 的运行版本不变，审查请求随后填入实际完整 Git revision。

上述回收证据与签字以 `92874fe7f320a9a4a47e61adacedd26fc58078c7` 提交，九项尾注齐、当时工作树干净。[独立审查请求](REVIEW-REQUEST-T078-FINAL.md) 已显式固定此完整 revision；后续仅计划/说明提交不让 reviewer 自动追逐 HEAD。原 root 的完整 API headers/system/metadata 未原样归档，审查只能用停机前保存的逐项安全投影、主控读回和既有阶段原件，不能在已删除 root 重新计算原始 HTTP body；该证据边界已写入请求。

三项剩余验证的 [计划](PLAN-REMAINING-T078-01.md) **仅准备、运行 INCOMPLETE／launch NO_GO**：09C 拟用两 Claude、一个确定性目标、模型0，ideation 4 roots/7 POST、executor1/1，真实 >120000ms 且总观察≤150秒；三窗格须先裁定三现有窗口同屏或单窗三pane，独立场为两 Claude/零 POST；系统IME独立场无 Claude/Codex/模型，仅真实输入法提交与取消两个样本。每项都给实际入口、独立字节/事件/截图依据、坏实现应失败的位置、权限与待决定事项。现有“代签09B”不扩大到09C；缺人在场/可靠原生IME驱动不以合成事件补称通过。

现源码只有单 Terminal/单 pane、单 BrowserWindow，三窗格口径与权限需主控协调，已作为非阻塞 issue `20261016T135530Z-worker:t078-remaining-plan-issue-001` 上报 triage；不阻塞本轮计划交付，未修改产品或地图。原 issue 中 renderer 的54/161是附近上下文，随后精确核对为构造57、pane157，主记录 [问题正文](REMAINING-DECISIONS-ISSUE.md) 已更正定位，原收件箱条目不覆盖。该 issue 同时报告 README 的旧“单角色/09B仍未运行”描述需同步；本轮未在只写计划范围内顺手改 living doc，地图脚本未报 stale 不代表这段现状文字已正确。

## 主控 #335：独立终审 NO_GO 与 F6 源闭包红态

[独立终审01](independent-review-final-01.md) 原件入库、不改其字节。其目标92874fe7f，整票 **NO_GO／INCOMPLETE**；源码/保存回执的局部PASS不等于17 POST/七原生许可的独立证明。F1确认回收仅留汇总投影使HTTP/hook原件无法复核，没有证据推翻当时运行，但历史A15不能补造缺失原件。F1是否重跑09B由用户决定；F3由主控安排下一轮reviewer在冻结候选的隔离临时worktree做2～5个变异，不要求门禁副本。F2/F4/F5/F6/F7按报告分别保留，当前整票仍不关闭。

F6先通过真实标准prepare生成 `09b-executable-materials-f6-red-01`：旧生成器返回静态PASS/58文件，但独立的三个reader调用者局部import闭包检查 **exit 1／INCOMPLETE**，明确缺 `p1_output.py` 及command_evidence、electron_client、p1_endpoint、p1_processes、p1_reuse、p1_simulated_actions、p1_window_receipts共八个helper。红态在 `review-followup-f6-red-01`，不是socket/CLI设置失败。该包只是源边界探针、launch NO_GO；仅静态Node构造，daemon/API/原生CLI均0，已删除其临时静态root，原包与失败回执保留。

标准prepare仅补这八份reader本地依赖，保持原调用者、根/预算/协议不变；源码提交冻结后才生成新标准包取绿。F4仅给现有原断言runner增加单case/mutant-core参数，以复用原T075 fence/CAS/lock变异，不改业务测试方法或acceptance断言；整组8/9/18、CAS、卡片正反例及三变异的实际运行仍 **INCOMPLETE／未执行**。命令路径/语法/三个变异定位的check-only已PASS，无进程/模型。真登录仍受现有fake-only产品入口约束，准备材料将明确前置，不用直接原生CLI绕过门禁。

F6代码已提交 `a853ad58b91f0363fcb933c50ff15ff15e2d3caf`，九项尾注；之后真实标准prepare生成 `09b-executable-materials-f6-green-01`（66文件）。[绿态](review-followup-f6-green-01/result.json) **PASS**：三个reader调用者的14个局部import模块无缺失；在隔离Python `-I` 子进程只从解包目录导入reader，真实字节/分页/EOF通过，删除p1_output的坏包仍被拒。该包由prepare逐文件与提交字节核对，没有从当前checkout补缺失模块；无daemon/API/原生CLI。静态临时root已删除、源包和读回保留。F6闭包问题可凭上述红绿交主控关闭，不代表新09B/09C获准启动。

[F4说明](REVIEW-FOLLOWUP-F4.md) 和 [确切命令](REVIEW-FOLLOWUP-COMMANDS.txt) 指向新 `review-followup-regressions-01`；预期coop8、recovery9、run18、CAS1、cards15全组PASS，三单点变异各原测试exit1/业务失败/errors0后由协调器另判反例PASS。当前只做check-only，**运行INCOMPLETE**；不将T075非模型门禁正反例说成重跑历史真实Codex/网络沙箱。快照绑定当前最终业务与已提交runner，后续票内文档允许，源码改变即拒绝。

F7已在审查请求末尾追加#335说明，旧报告/原件不改：#333已完成A15回收，root不再存在；回收充分性和F1验收原件充分性是两件事。F3留给主控下一fresh reviewer，允许绑定候选的隔离临时worktree中做2～5个变异，不再要求Herdr期尚未提供的门禁副本；worker本轮未做reviewer变异或给独立PASS。F5仍直接total INCOMPLETE。

[P3真登录最小材料](P3-REAL-LOGIN-MINIMAL-01.md) 给出两真实回合＋第三次另批、两CLI/仅一个真实模型接收者、短基线/实际report唤醒、argv/env/hooks、仅本次会话历史的用户HOME写入许可及停止条件。**P3 launch BLOCKED**：产品尚无normal-login profile；实际CLI正常HOME写集和包含失败/重试的可靠调用计数也未验证。现有授权已确定认证路线，不重复提问；另上报非阻塞issue `20261016T142844Z-worker:t078-review-followup-issue-001` 请主控安排最小实现/前置，不能捏造可执行manifest或直接起原生CLI绕门禁。需要扩大用户HOME非历史写入时才另请用户决定。本轮未访问用户认证/历史、未启动真登录。

F1的 [逐POST/hook最小保留清单与代价](09B-MINIMAL-RAW-RETENTION-01.md) 仅供用户决定：保留每个实际请求/响应/meta、每次原生hook的脱敏stdin/stdout/finished、完整许可/单Enter回执、原事件/目标字节与身份，而非重建汇总。秘密字段定点脱敏，原始顺序/实际ID保留；外置逐成员字节读回，fresh独立重数通过后才另批删root。拟议仍两Claude、0真实Codex/模型、17 POST/七许可；未压缩估计1～5MiB、先留20MiB余量，实际大小/耗时未知。没有决定重跑09B或修改过去的redactor/cleanup；A15历史采集PASS、独立INCOMPLETE的边界不变。整票继续NO_GO/INCOMPLETE。

F4准备期的判定器文件检查首次失败，原trace在 `review-followup-final-check-01/failure.txt`：错误地在单条assertion找business-red，实际它属于原测试`TEST_RESULTS`。这是harness字段错误，不是产品红态。修正后runner额外保存原测试结果，协调器分别要求具体claim失败和原结果business-red；[02文件检查](review-followup-final-check-02/result.json) PASS，三份历史业务红态均接受，setup-error、错loaded core、fixture分类及无业务断言失败均拒绝，scene_actions=0。没有运行F4真实测试，源码冻结元数据会随本次最终harness提交更新，防止交主控的命令仍绑定修正前代码。

F4最终harness与本轮材料提交为 `4fcb60dbe`，完整revision从实际Git读取并更新于 `review-followup-source.json`；它包含上述分类修正，F6 producer/reader及最终业务未再改变。终审01原件已在a853ad58b入库，未修改。最后仅补冻结元数据与只读预检收据，不在提交后追加未跟踪文件；F4实际外侧回归和P3真登录依然未执行。

## 主控 #336：F4 coop失败的只读诊断与历史对照待执行

主控沙箱外check-only PASS；正式 `review-followup-regressions-01` **INCOMPLETE**（revision6f9fae871）。coop8方法均执行，0 failure、1 error；后续recovery9/run18/CAS/cards/三变异没有运行。输入输出原件保留，本轮不改其结论或其他旧结果。

[诊断facts](review-followup-f4-diagnosis-01/facts.json) **PASS（保存现场的根因定位）**：原review_requested=115时shared_refs已记worker HEAD=67ef506f…、候选C=3cc14063…；真实report被接受（review_result=122），审查目录HEAD=C且clean（命令131/133），worker HEAD到结束核对仍为同一个67ef506f…（135），随后review_lifecycle_failed=136，phase=reclaim、error=review_worker_workspace_changed。无review_protocol_failed、无review_reclaimed。宿主正常退出、stderr仅Node模块类型警告。legacy driver等8秒回收超时是该拒绝的后果，不是报告schema未跟上。

源头是T082新增worker HEAD必须等于C的结束guard，与原用例“提交冻结C后worker再提交later_bad，verify仍验证C”的交叉；验收文件在150ef6516和main0e6c2b833之间逐字相同。审查前后worker HEAD没变与“必须等于C”是不同条件，worker clean因HEAD短路没有执行，不补称已读到clean。业务源码是否应按审查开始时实际worker边界绑定，或本来有意收紧，须主控/契约owner裁定；已上报issue `20261016T145441Z-worker:t078-f4-diag-issue-001`。本轮**不改core、driver、acceptance或protocol**，不reset worker、不加超时、不跳过回收。

[两版本对照命令](F4-DIAG-COMMANDS-01.txt)与[语义诊断](F4-REVIEW-BOUNDARY-DIAGNOSIS-01.md)已交准备：新输出review-followup-f4-compare-01，串行在两个临时稀疏clone上跑同一原方法，产品/验收/legacy driver各保留自身历史版本，仅叠加现有单case/证据runner并保留diff；不需要改共享worktree/主仓引用。**实际两版本结果尚INCOMPLETE／未运行**，不把“main预计也失败”写成实测。只读Git对象/依赖/路径预检PASS，临时文件上的tar类型/字节校验与字节变化拒绝PASS，未起宿主/模型。

修复后完整重跑的新目录为review-followup-regressions-02，命令已作为明确标注的后续模板列出；只有语义裁定、分配修复、红绿/边界检查及源码重新冻结后才可运行，当前NO_GO。T082审查期间真实改worker/共享refs/审查目录仍须拒绝的保证不能削弱；当前只读诊断不算修复或整组通过。

## 主控 #337：历史对照确认上游缺陷，转T-090；T-078暂停

主控已在沙箱外执行 [两版本对照](review-followup-f4-compare-01/result.json)，同一个原方法 `test_submit_requires_clean_head_and_cannot_replace_frozen_candidate`，验收/产品/各版本legacy driver未修改，仅叠加已留diff的单case/证据runner：

| 版本 | 实际单用例结果 | 审查结束证据 |
|---|---|---|
| 合并前exec/t078 `150ef6516f6ef5aaa6855631b770ce262991ffbf` | **PASS**，exit0、0 failure/0 error | review_result119 → review_reclaimed135 |
| main `0e6c2b833f6da64243f71d670ea45bb9116fda4d` | **INCOMPLETE**，exit1、0 failure/1 error；legacy driver等待回收超时 | review_result122已接受；review_lifecycle_failed136，phase=reclaim、error=review_worker_workspace_changed；无reclaimed |

顶层对照脚本PASS只表示两次结果成功采集，不将main的业务失败上调。真实模型/供应商CLI均0；两个隔离fixture分别147/168个成员逐字节核对归档后删除，clone scratch也已删除；没有重跑整组、没有修改旧失败结论。

主控#337裁定：这是**T-082带入main的产品缺陷**。T-082票原文要求“候选提交号不变、审查目录与worker worktree干净、共享仓库引用未变”，未要求worker HEAD==C；采用“审查开始时绑定worker实际HEAD/分支/干净，结束核对未变”的修复方向。修复由主控在main新建的缺陷票 **T-090**、另一worker处理，**不在T-078内修改core.ts**，不通过改acceptance/protocol或driver reset绕过。

后续顺序：等待T-090合入main；由主控安排T-078再合并main、核对双方意图与实际冻结源码，再以全新 `review-followup-regressions-02` 完整重跑F4各组。当前未合并、未修改源码、未运行该回归。按主控明确要求，完成本次证据/裁定提交后 **暂停T-078工作**，等待T-090或用户对剩余四项的决定；整票仍NO_GO/INCOMPLETE，不自行启动任何后续现场。

## 主控 #338：ready_rev 2，A16／09C仅做前冻结计划

本轮按主控新指令恢复**材料写作**，不解除实际场景的NO_GO。已读取main票“修订rev 2”与revise `20261016T174154Z-ideation-revise-001`，逐字副本在 [前冻结材料](rev2-prefreeze-materials-01/README.md)；本worktree旧ticket尚未合并，worker不改地图/ticket，实际新运行按ready_rev 2重新绑定。

| 用户2026-10-16决定 | 本票当前处理与状态 |
|---|---|
| 09C“授权执行主控代签 (Recommended)” | 已授权各阶段及满足实际命令/stop/目标/原屏/预批准模板逐项一致后的自动单Enter；任一不符停并INCOMPLETE。预算I4 roots/7 POST、E1/1，假API、模型0。旧“09C代签待用户决定”是历史文字，不再重复询问路线；实际模板尚未签/绑定 |
| 三窗格“拆出去：T-078其余先收，截图项另开UI票” | 移到 **T-091**，不再作为T078本轮验收阻塞项；本票未覆盖同窗多pane，不把单窗格截图算通过 |
| 系统输入法“本轮不做”，原文“保持INCOMPLETE” | **未验证／INCOMPLETE**；本轮不采系统IME，不把已有合成composition测试上调为系统实测 |
| 09B“重跑一场09B，留最小脱敏原件” | 已决定A16重跑，沿原protocol与I4/6、E6/11、合计17 POST/七工具许可，模型0；逐POST请求/响应元数据与正文、hook stdin/finished等可独立复核原件外置保留，不含认证信息。A15历史F1缺口不补造/改判 |
| 真登录“另开一张票，T-078先不等它” | 移到 **T-092**；T078本轮按假API证据验收，明确未覆盖正常HOME登录/真实模型。已备P3真登录材料不运行任何真实模型回合，不在本票实现/启动normal-login profile |

A16与09C可同批准备、串行执行，各新root/两角色/API/target/身份；两场合计15根/25个主Messages POST、10次工具许可、供应商模型0、真实Codex0，不把两场塞入一个旧turn_limit会话。本轮仅写 [A16阶段](rev2-prefreeze-materials-01/A16-STAGES.json)、[09C阶段](rev2-prefreeze-materials-01/09C-STAGES.json)、签字字段/条件式C-I3模板、两份明确标TEMPLATE的 `*.archive.json`、[归档清单](rev2-prefreeze-materials-01/RAW-RETENTION-AND-ARCHIVE.md)、[回收脚本契约](rev2-prefreeze-materials-01/CLEANUP-SCRIPT-CONTRACT.md)与[预算/停止条件](rev2-prefreeze-materials-01/BUDGET-AND-STOPS.md)。**这些是未绑定施工材料，不是已实现/验证的raw cleanup或C driver**；当前无可执行launch命令、不伪造PID/claim/permission/screen/归档字节PASS。

C-I3在阈值前尽早停在实际PermissionRequest、完整取屏并由执行主控签实值预批准；>120000ms且monotonic观察≥120100ms时再完整读取全部页/EOF，与原屏逐字节相等，逐项核对命令、stop/target、native/window/事件/签字/无ack/持续要求，才沿原Electron通路最多一个awaited CR，保存真实action/intent/written。若等待中原屏变化或写入未知，不自动改签/重按，INCOMPLETE。自动开始截止130秒为驱动留结算余量，不改变产品>120秒门槛；整场观察/结论仍≤150秒，不快进clock或重置created_at。

归档新契约先在daemon仍活着时捕获逐条原件/一致事件行快照，结构脱敏后外置tar，成员类型/目标/普通文件字节逐一读回，实际成功才产生archive.json清单；独立方从包重数，不以summary代替原件。再单签owner-bound正常daemon_stop/panes.shutdown、两原API各一次SIGTERM；停机后只验文件/归档，**不读SQLite/WAL**。关停出现新的POST/hook/finished或原件变化则阻止root删除，不能再漏尾部。旧A15 summary-only出口不可作为A16 fallback。

按主控要求，**本轮没有生成依赖源码版本的冻结包**，没有sources.tar.gz/实际root/UUID/PID/签字/归档回执，不运行prepare、场景、测试、API、daemon、CLI、Electron或按键。新的raw保留/回收与C保持/条件Enter需按施工单在合并后实现、真实无模型排练，再纳入完整源码闭包；T090合入main、T078合并main并完整F4复验后才冻结/重新绑定两场。整票仍INCOMPLETE／NO_GO；旧独立终审原件保留，后续fresh审查按rev2范围及逐记录原件重新核对，不能由本轮计划替代。


## 主控 #339：先实现 rev2 测试工具，实际场景仍待合并后绑定

按主控新授权提前实现测试工具，替代#338施工单中“尚未实现”的当前状态；#338原记录、旧A15/F1缺口和终审结论不改。本轮未改 `workbench/src`、acceptance、冻结protocol或地图，没有启动原生Claude/Codex、Electron、daemon、真实目标或模型，也未生成任何版本依赖的launch冻结包。T090合入后再合并/重跑/冻结的顺序不变。

[工具交接与确切命令](REV2-TOOLS-01.md)、[先列的失败方式](REV2-TOOLS-FAILURE-MODES.md) 对应两项实现：`t078_raw_retention.py`全量逐HTTP/hook原件、定点脱敏、一致停机前行导出、每文件archive指针/成员字节核对、独立读回前置、owner/九进程正常停止、停机后只验文件与尾部；`t078_09c_driver.py`真实阶段判定/登记、Bash.command、原生queued结算、单held SSE、系统时钟/单调时钟、完整原屏与逐字段模板、独占fsync单Enter意图、实际Stop/relay/无ack/单Esc/不回收目标的结算。窗口发送复用原Electron terminal-key permission路径，CR记control action；中间按键成功与最终业务结算分开，晚失败保留partial-result且顶层INCOMPLETE。

同一个真实假API服务新增C profile并在校验前保存所有请求、逐块响应及method/path/status/时间/长度/complete元数据，认证头值不进入捕获接口。未来std prepare/runner/I1/角色生成器同步只认新marker `rev2-raw-c-profile-v1` / `rev2-registered-raw-v1`，不复用旧进程、不留旧marker兼容；只改生成器/测试工具，没有运行prepare。Python运行闭包补入raw与C两模块。B协议/预算维持原文；C预算I4根/7 POST、E1/1，模型0。

[本地最终契约](rev2-tools-final-check-02/result.json) **PASS 42项**，含模板每个字段不符、单页/total变化/零进度/无EOF、可见命令不符、ack/要求撤销、时钟跳变/超时、未知写入不重按、归档字节变时零stop/零删除、原件新增在停机前阻断、关停尾部在删除前阻断、dry-run零副作用。三个去检查坏实现（字节验证、模板、时钟）均在新oracle处RED。工具新增前同入口contract-red为“未实现”红态，不当旧产品缺陷；首次green相对路径错误与handler-04离线API标签缺失均原样保留，修后新目录通过，不重写失败。

[C真实Handler字节流排练](rev2-tools-local-01/C-handler-final-02/result.json) **PASS**：按既有Claude2.1.296脱敏结构走C-I1→held C-E1→C-I2→C-I3→C-I4，正例实际Handler调用7/1，正文/seq/真实launch身份/角色/预算五类反例409也全部保存。随后从tar直接重数为I11/E2（含五反例，不能混入正式场景预算）。先归档、逐字节读回，再用相同finish函数执行确定性normal_stop/API生命周期、SQLite已不可用时仅文件复核、删scratch。Bash.input变异为argv时，实际Handler的SSE在捕获Claude tools schema断言处RED；B既有core与九阶段矩阵PASS。详细原件将无损压缩保留，结果JSON不改。

边界：上述时钟为明确标注的注入单测、HTTP为实际Handler字节流、窗口/库行/normal_stop为确定性夹具。**真实loopback及实际API SIGTERM尚INCOMPLETE**；已交`run-rev2-tools-outside.py`串行六段完整命令、路径/语法预检PASS，正式由主控沙箱外运行。它只起两只假API，不起真实角色CLI/模型/Electron，C real-clock阶段210秒硬超时、外层230秒。**原生C门禁/Electron全链、实际九PID owner、独立审查和整票验收仍INCOMPLETE／NO_GO**，不以此模拟排练替代。未启额外agent；后续由主控安排fresh独立审查、合并T090及两场实值绑定。

提交前又取两条工具自身的局部红绿：HTTP meta 在truncate/write交错下暴露无效JSON，改临时文件原子replace后同探针PASS、旧writer变异RED；许可Enter回执窗口内若下一根gate反馈已到，旧adapter误把它计为CR新增intent（rev2-permission-feedback-red-01），现按同一真实request_id关联控制动作，增强后的42项PASS。晚业务结算失败保存partial原件且最终INCOMPLETE；C真实CLI参数入口以09B的E6冒充C的E1预算时，在任何动作前明确拒绝（rev2-C-budget-entry-01）。最新Handler重跑rev2-handler-post-atomic-01 PASS。全部仍是明确标注的工具/夹具证据；没有实际点击或业务Stop。

系统时钟已在本会话单独执行：[rev2-real-clock-01](rev2-real-clock-01/result.json) **PASS**，系统time.time/monotonic实等120.109656/120.108549秒；同一conditional_enter在wall age120109.138ms、观察elapsed120107.939ms时只调用一次替身CR，145秒硬超时未触发。没有注入时钟、端口、GUI、角色CLI或模型。此证明限工具时钟/条件按键，实际09C角色/门禁仍INCOMPLETE，真实HTTP组合排练仍交主控。


## 主控 #340/#341：main/T090 已合并，准备两场新冻结（不运行）

合并提交 **43d085c5d0fe3584b350d7c1420a17533be8b43e**，父为acf8b8a3f和main6d85482ff；备份由主控建立。三个冲突仅测试宿主/runner，取舍见[RESOLUTION](merge-main-4/RESOLUTION.md)：保留operator凭据引导和失败原件，两个ready统一用T090完整写入后原子发布；一个可重复的--case保留唯一原方法检查、--mutant-core/original_results和单例/多例字段。worker没有再改core.ts，自动合并的worker_boundary按review_id核对语义与T078 pending/startup共存。语法/冲突标记/引导顺序静态检查PASS，合并后实际回归仍INCOMPLETE。

主控放回的[rev2-tools-outside-01](rev2-tools-outside-01/result.json)为acf8b8a3f上的六段PASS：真实loopback+系统时钟120.688秒组合排练、两只API正常SIGTERM、先字节读回归档再停止/删除均完成；C正例7/1 POST，随后五反例原件也保留。它明确使用确定性库行/窗口/normal_stop替身，不是合并后的真实角色/门禁C验收，不上调旧A15的F1。

[新回归命令](merge-main-4/REGRESSION-COMMANDS.txt)交主控沙箱外：review-followup-regressions-02全8/9/18、CAS1、cards15及三业务变异；merge-main-4-t078-regressions-01覆盖pending/controller/input11组、startup候选15与真实入口14及M5、worker收件箱14。T090既有短期限偶发issue不授权重试、延长或跳过；首败即停保留。原F4对dedd4f66的写死源检查改按本轮business_revision/source冻结核对，原验收断言和期限不改，旧结果不重写。

A16/09C沿同一个标准prepare/StageA/API/角色工具；新增显式scene，A16预算I4/6、E6/11（17 POST七许可），C为I4/7、E1/1（八POST三许可），真实模型0。两场静态包绑定合并后的实际source提交，未签NO_GO；StageA建root/进程之前要求两份当前源码回归收据PASS，卡片仍先真实入口预检。StageA将保存原始五PID完整argv/lstart，后续owner从实际B1 manifests补四PID，不伪造attempt/null；C的role/phase/owner生成器已纳入闭包，未来只填实际数据，不在启动后再换API。所有本轮新增生成器/接口适配只做静态检查与文件生成，尚未运行合并后场景。

详细阶段顺序、C真实时钟/完整原屏条件单Enter、原件先归档逐字读回再停机/停机后不读SQLite、-02重读、唯一slot、I2时点的归属说明和停止条件见[HANDOFF](merge-main-4/HANDOFF.md)。三窗格/真登录仍移T091/T092，系统IME未验证INCOMPLETE。当前未运行StageA、B1、按键、模型或回归；冻结文件PASS只指文件/版本/预算/闭包，不是业务验收。整体仍INCOMPLETE/NO_GO，等待主控复验和逐阶段签字。

本轮文件冻结完成：source commit **1b86f2c91c781cd4867227230185fc2a2c145aeb**（含merge43d085c5d/main6d85482ff），A16 `09b-executable-materials-16` 与C `09c-executable-materials-01` 各312个源码/输入成员，均从该Git提交逐字节核对。两份SOURCE.json、StageA命令及空签字批准已生成；C预算原生turn_limit明确4/1，旧共享布局和旧marker不兼容。标准包含完整受控宿主ready_file、app/reader/API/owner/角色生成闭包。

[final-static](merge-main-4/final-static.json) **PASS，仅静态**：10条命令/入口检查、实际输入存在或明确列为StageA/B1后生成、未签字段、两组预算、源码闭包核对及两个runner的check-only均通过。静态root在/private/tmp保留供主控StageA复制，不是已运行场景。没有执行StageA、原生CLI、fakeAPI、daemon、按键或回归；两份真实回归收据仍缺，StageA机械拒绝缺收据的启动。原主控工具实跑目录已无损打包为rev2-tools-outside-01.originals.tar.gz，逐字读回后保留原样JSON摘要与originals.archive.json，原失败/反例/HTTP均在包内，非改写旧结果。

## 主控 #342：合并后整组通过；mutant-cas 分类器 claim 错误

主控在 `7f45637794b5455d46125242dae90efba4863aee` 沙箱外运行：[T078 自身](merge-main-4-t078-regressions-01/result.json) 四段全部 **PASS**（pending/controller/input、startup 领域与 M5、startup 真实入口与 M5、worker-inbox）；[F4 整组](review-followup-regressions-02/result.json) coop8/recovery9/run18/CAS1/cards15 共51方法首次在同一次运行全 **PASS**，fence 变异按预期业务失败。主控报告负载最高1分钟3.51，原日志 [regressions-load.log](merge-main-4/regressions-load.log) 留存；不据此宣称稳定性改善。

F4 顶层仍 **INCOMPLETE**：CAS 子测试已是1 failure/0 error/0 skipped、business-red，但本票 runner 期待的两条 claim 不存在于选中的原 CAS 方法，所以在分类处 AssertionError。[诊断](MUTANT-CAS-DIAGNOSIS-01.md) 列出独立原方法与原 assertions 对照：旧 G 未重绑、外部提交祖先关系丢失、oracle只运行1次。变异没有检错位置，属于 **runner 分类器缺陷**。未改 acceptance、workbench、变异 helper 或旧结果；本次把主控放回的原回归目录、签存日志一并原样入库，不重写任何原结论。

分类器按原用例 CAS 契约修复；相同保存原件重放 red→green，**11项 PASS**（1有效红态＋10误判反例），无真实门禁/API/CLI/模型。新 `--only-mutant cas` 的路径/语法/单点位置 check-only 已实测 PASS；[单段命令](MUTANT-CAS-RECHECK-COMMAND.txt) 交主控沙箱外以新 `review-followup-mutant-cas-03` 执行，尚未运行。原 lock 变异未运行，保持INCOMPLETE；本轮不扩大重跑范围、不改写整组结果，也不启动 A16/09C。现有源码冻结包未变；原 Stage A 要求全量回归 PASS 的前置仍未满足。整票仍 **INCOMPLETE／NO_GO**。

## 主控 #343：CAS 单段 PASS，准备原 lock 单段

主控沙箱外 [review-followup-mutant-cas-03](review-followup-mutant-cas-03/result.json) **PASS**，绑定 `0ea5830a6960ef1aae0b4f551e76cf6f3b266127`：只执行 mutant-cas，原子测试 exit1、分类器接受预期业务红态、顶层 exit0；原目录原样随本次提交留存。旧全量顶层 INCOMPLETE 不改写，lock 仍未实跑。

本次 runner 仅两处修改：`--only-mutant` 增加 `lock`；结果 scope 根据实际选项写为 `mutant-lock only` 或 `mutant-cas only`。不改 acceptance、workbench、单点变异、原方法、分类器或冻结包。核对 `acceptance/test_recovery_e2e.py` 的原 `busy_probe`／`test_live_verify_excludes_verify_and_integrate` 与 daemon adapter：并发 verify/integrate 应返回 `ok=false,error=operation_busy`；oracle 应始终只有1个。runner 既有三条 claim 与原用例一致，不存在 CAS 那种标签不匹配：`Live operation excludes concurrent verify`、`Live operation excludes concurrent integrate`、`Busy commands never start a second oracle`。

[重放入口](check-mutant-lock.py) 使用历史 `outside-final-01/mutant-lock` 的原 run.json 与 test-result.json 数组，仅在一次性 scratch 里压缩为当前分类器读取格式，未合成业务字段、未修改旧文件。该历史版本为 `b3fb998cf48574821c39440ece3f9ff897f26cf9`，不是当前源码的变异实跑：其 verify/integrate 实际均 `ok=true`，oracle 实际2，三条 claim 均false。重放接受该真实业务红态；无关失败、错误core、夹具error、非business-red四反例均拒绝。新单段功能先经真实 runner 的 check-only 取 [red-01](mutant-lock-checks-red-01/result.json)（argparse exit2、未创建运行目录），改两行后同入口 [green-01](mutant-lock-checks-green-01/result.json) **6/6 PASS**，lock check-only exit0、suites空、mutants仅lock、未创建运行目录。无门禁/API/角色CLI/模型进程。

[精确单段命令](MUTANT-LOCK-RECHECK-COMMAND.txt) 交主控沙箱外，使用全新 `review-followup-mutant-lock-04/`，仍核对冻结业务/原测试/helper/prepare及已提交runner。当前真实 lock 与 F4完整收尾保持 **INCOMPLETE**；不会以历史重放代替合并后复验，不启动 A16/09C，也不自动修改其全量回归前置。

## 主控 #344：合并后回归补齐，Stage A 显式绑定四份收据

主控沙箱外 [lock-04](review-followup-mutant-lock-04/result.json) **PASS**（指定原方法 BUSINESS_RED，顶层接受），原件随本轮入库。依主控裁定，F4 由 [02](review-followup-regressions-02/result.json) 的五组51方法与fence、[cas-03](review-followup-mutant-cas-03/result.json)、lock-04共同补齐为 **PASS**；[T-078自身四段](merge-main-4-t078-regressions-01/result.json) **PASS**。02 本身仍 INCOMPLETE，绝不改写原文件或冒称它整次运行已通过；完整收据组合和各补跑范围明确保留。

[四收据预检](STAGE-A-FOUR-READBACKS-01.md) 显式核对 02 只停在旧 CAS claim 分类器：阶段边界、Git中对应版本的断言/行号、原CAS业务失败均吻合，其他失败不能豁免；cas-03替代该判定、lock-04补齐未执行段。两份Stage A批准必须与包内的四路径完全一致，逐份核对测试版本祖先与业务/验收/原测试/驱动闭包无变化。仅新 Stage A 预检脚本的差异单独记录并纳入新包冻结，不以旧回归证明新场景已通过。

旧入口拒绝的红态已保留；保存原件＋12反例共 **13项 PASS**，删掉历史状态/error检查的已知坏预检被两条反例抓到。均只读Git/保存文件或一次性文件夹具，零运行服务/角色/模型。下一步仅按源码提交重新冻结新包（旧包保留）、更新未签批准和命令，不运行场景；整票仍 **INCOMPLETE／NO_GO**，回归补齐不代替09B补证和09C实际验收。

本轮文件冻结已完成，源码提交 **7a6edbff87df85077b3a05d38f3cfd5654cde9c1**。标准prepare生成 `09b-executable-materials-16-02` 与 `09c-executable-materials-02`；[逐成员核对](stage-a-readback-rebind-01/result.json) **PASS**，各312个成员与该Git提交一致，相对旧包只有 `run-09b.py` 一项不同。旧包、旧全量结果及原始回归记录保留，不改业务、原测试或protocol预算。两份当前Stage A批准仍在原目录、签字均空，四份readbacks逐项相同；Stage A／角色材料／owner命令已指向新包。

[完整真实预检函数](stage-a-four-readbacks-final-01/result.json) 两场均 **PASS，仅预检**：包含材料谱系、完整源码闭包、四份实际收据及历史异常的显式核对；实际未签批准均拒绝。正例只在内存填测试批准，没有写实际签字、运行main、创建运行root或启动daemon/API/目标/角色/模型。源码仍为合并T090后的业务，A16/09C实跑和整票结论仍 **INCOMPLETE／NO_GO**，待主控签字与串行执行。

## 主控 #345：A-16 Stage A READY，ideation B1/首启仅备材料

主控签 [Stage A批准](09b-a16-materials-01/stage-a-approval.json) 并在沙箱外运行 [09b-a16-stage-a-01](09b-a16-stage-a-01/result.json)，结果 **READY_FOR_APPROVAL**、供应商模型0；root为 `/private/tmp/t078-2-09b-run-z9ov_cco`。签字原件与完整输出随本轮提交，不改主控记录。

本轮按主包 `ROLE-MATERIAL-COMMANDS.txt` 第一条实际运行已冻结 `prepare-a14.py --mode role`，只写ideation P1/隔离角色配置和phase-plan文件，生成 [09b-a16-b1-ideation-p1-01](09b-a16-b1-ideation-p1-01/generation.json)。实际attempt/任务/root/API取本次readiness，不复用旧A15绑定；ideation API34330/64318仍用动态端点模板和既有复用身份检查，不起第二只API。

[材料静态核对](09b-a16-b1-ideation-p1-01/preparation-static.json) **PASS，仅静态**：312个冻结源码成员与当前源文件逐字一致；B1 binding/schema/首启计划完整，签字为空；六键草稿均未签，s7单键为onboarding-notice，而B1整体计划保留security-notice和原提示文本；23条B1/绑定/首启命令的入口与现有输入路径通过检查。实际B1 manifest、各屏screen.bin和launch label明确为后续产物，先实跑B1、再BIND-LAUNCH从真实结果填入；不假装它们已经存在。

[B1-HANDOFF](09b-a16-b1-ideation-p1-01/B1-HANDOFF.md) 给出 dry-run/real分步、实际launch绑定、首启逐屏六键、-02重读和停止条件。读屏沿冻结的完整分页reader，需稳定total与EOF原件，不再使用旧单页路径。rev2 API/raw collector/reader闭包与marker已核对；逐POST/hook原件继续留在隔离角色目录，回收前先脱敏归档、逐成员读回并从tar独立重数/留archive清单，再停机；停机后不读SQLite。owner待两角色真实B1 manifests齐全再生成，此时未伪造PID/owner/归档通过。

**本轮没有运行 B1 dry-run、真实B1、读屏、按键、业务输入、gate dispatch/release、服务启动、归档或清理，也未生成executor P1或启动其角色CLI。** 主控下一步从 `B1-COMMANDS.txt` 分别取 dry-run和real两行，签字后各自执行；成功后按 `BIND-LAUNCH.txt` 再用 `ONBOARD-COMMANDS.txt` 一条一条读屏/签键。ideation预算4根/6POST、全场17POST、模型0不变；A16业务补证、09C和整票仍 **INCOMPLETE／NO_GO**。

## 主控 #346：ideation 首启完成；s11 送达与采集状态分别留存

主控运行A16 ideation B1：dry-run **READY_FOR_ROLE**、real外层 **PASS/cli_spawned**、BIND-LAUNCH通过，实际Claude shell36360/CLI36361。六键逐屏核对后签发，初读均相符未用-02；本轮把两层B1、完整读屏/逐键输出、实际launch-binding与签字件一并提交，保持旧原件字节及状态。

s11 Enter的 [原result](09b-a16-b1-ideation-p1-01/a16-ideation-s11-Enter/result.json) **INCOMPLETE**，不改判。它的唯一 `pane_screen_key` 调用exit0、`key_result.written=true`，授权引用/原屏/selected Yes均吻合；随后第一次 `pane_output` offset0→7079、total7079，下一次 offset7079→8913、total8913。新增字节包含Claude欢迎页、空提示符和manual，属于信任确认后正常界面过渡输出；完整reader按契约拒绝变化的total，抛 `output_total_changed`，没有生成不完整screen.bin。

[保存收据独立比对](09b-a16-b1-ideation-p1-01/s11-readback-01/result.json) **PASS，仅读回**：支持该Enter已送达；错误发生在送达后的采集，不影响已有按键证据，不应重按。后续主控另行读取的 [s13](09b-a16-b1-ideation-p1-01/a16-ideation-s13-screen/screen.json)为8921字节，total固定、offset0到8921并有EOF零字节确认；原屏同launch/session/repo、空提示符和manual可核对。P1只读screen结果本身沿生命周期默认仍记INCOMPLETE（无error），不改其文件；本条PASS仅指完整capture/显示内容的检查，不是整票/业务验收。

判断：本次是启动界面继续输出期间的预期采集拒绝，没有按键错误证据。本场保持冻结工具不变，不自动重读/重按或吞掉错误；以后如需改善此类工具体验，可在发键回执已保存后以有界等待再独立取稳定只读快照，仍须严格total/EOF且超时保留INCOMPLETE。这个建议未实施，不作为本场通过条件的变更。

已准备 [readiness确认命令](09b-a16-b1-ideation-p1-01/READINESS-CONFIRM-COMMAND.txt) 和 [I1第一步](09b-a16-b1-ideation-p1-01/phases/I1/STEP1-HANDOFF.md)：确认命令实际运行时才查0 POST/0提交并排他写readiness；I1批准仍空，真实pane_dispatch/release后到许可屏停止，预计1根/1POST，完整I1仍2POST、一次工具许可另批。逐POST/hook原件按rev2即刻留存，回收前额外归档读回/独立重数，不以汇总代替、不停机后读SQLite。本轮未执行确认命令、I1、发键/Enter、任何服务/角色启动或清理；A16后续与09C、整票仍 **INCOMPLETE／NO_GO**。

## 主控 #347：A16 I1 pending 通过，executor B1/首启材料就绪

主控执行 [ideation readiness](09b-a16-b1-ideation-p1-01/readiness.json)，0 Messages；签I1后派发 `f2b2cd4d-a2c3-4ed9-bbbd-e1b30c700693`、全局seq2，原 [dispatch-01](09b-a16-b1-ideation-p1-01/phases/I1/dispatch-01/result.json) **READY_FOR_PERMISSION**。许可原屏完整15877字节，命令/本次thread/attempt一致；主控签 [permission批准](09b-a16-b1-ideation-p1-01/phases/I1/permission-approval-01.json) 后Electron一次Enter。原 [execute-02](09b-a16-b1-ideation-p1-01/phases/I1/execute-02/result.json) **READY_FOR_EXECUTOR**：两POST，stop `d48f9f7c-187e-4fcd-b125-58ec345710b6` 为ideation→executor、pending/role_session_missing、relay ok、feedback0、target0。业务stop没有因参数里的伪造from变成executor。

[本轮只读核对](09b-a16-b1-ideation-p1-01/phases/I1/readback-01/result.json) **PASS**：实际0001/0002 HTTP meta均200/complete，request/response文件存在、大小与meta/wire一致；请求日志顺序tool_use→tool_result且无error，UPS/PermissionRequest/Stop原件均有finished、exit0。这里没有执行HTTP请求/钩子或按键。主控关于request正文中authorization只出现在系统提示语境的扫描作为其观察保留，不要求正文清掉正常单词；rev2捕获接口不接收认证头值。本轮未采集认证信息。

原逐POST/hook文件仍在**活root**，此时尚未外置归档。已提交本轮readiness、dispatch/许可/Enter/Electron输出及签字件；上述summary不替代原件。后续收尾必须按rev2先保存脱敏逐条原件、逐成员读回并独立重数/留archive指针，全部通过才停机，不能重复A15只留汇总的问题。

按主包第二条ROLE命令，worker仅运行已冻结生成器写 [executor P1](09b-a16-b1-executor-p1-01/generation.json)，并只读核对真实pending relay。复用本次Stage A attempt/root与executor API34331/64319，不起第二只API，不重发stop，不改 `created_at=2026-10-16T21:06:39.345Z`。[静态核对](09b-a16-b1-executor-p1-01/preparation-static.json) **PASS，仅材料**：312源码成员不变，B1与六键均空签字，29条命令入口/现有输入或明确后续产物检查通过；六次observe按expected-keys1～6绑定原I1结果与条目。

[executor交接](09b-a16-b1-executor-p1-01/B1-HANDOFF.md)：B1 dry-run与real分别执行，成功后BIND-LAUNCH取实际manifest；逐屏六键每键后刷新原收据，必须仍queued、无delivered历史、无I2、unknown/active null/业务输入0，然后才能下一键。读屏沿完整分页/EOF检查，初读不符用-02新label，不自动重按。s13之后不initial release，I2 arm/E1另批。本轮没有执行executor B1 dry-run、角色启动、读屏、发键、observe、release或归档/清理；ideation当前已用1根/2POST，executor首启预期0根/0POST，预算仍4/6与6/11，模型0。A16后续、09C和整票仍 **INCOMPLETE／NO_GO**。

## 主控 #348：executor 首启 queued 六次通过；准备原 I2 与 E1 放行

主控完成executor B1：dry-run **READY_FOR_ROLE**、real外层 **PASS**、BIND-LAUNCH通过，六键均逐屏核对后签发，初读均相符未用-02；六次 [queued检查](09b-a16-b1-executor-p1-01/onboarding/s11-queued-readback.json) 全 **PASS**，累计键数1～6、业务输入0、原stop仍queued、无delivered历史、无I2。本轮把完整B1/首启输出、实际manifest、六键签字及六次收据原样提交。

executor s11与ideation同类：[原result](09b-a16-b1-executor-p1-01/a16-executor-s11-Enter/result.json) 保留 **INCOMPLETE/output_total_changed**。唯一pane_screen_key exit0、written=true，之后两页total7051→8885；这是发键后的界面过渡输出，reader按契约拒绝变化的total，不是按键未送达，不能重按。后续s13完整8893字节、有固定total与EOF，空提示符/manual；screen阶段原生命周期status仍默认INCOMPLETE（无error），不改原文件。[保存证据核对](09b-a16-e1-preparation-01/onboarding-readback.json) **PASS，仅读回**；本场没有修改或放宽冻结reader，也没有自动补键/重读。

按A15流程仅写 [readiness确认命令](09b-a16-b1-executor-p1-01/READINESS-CONFIRM-COMMAND.txt)、ideation原I2的ARM命令、executor E1的INITIAL-RELEASE，以及 [delivered/I2读回](09b-a16-e1-preparation-01/DELIVERY-I2-READBACK-COMMAND.txt)。执行顺序为：主控确认executor readiness（重新刷新仍queued/0 POST）→单签I2并arm（不发输入）→单签E1，只release原排队stop到许可屏→collect原I2并核对turn_submitted之后才delivered/反馈，原request/entry/created_at不变、feedback/登记/提交各一次。该I2时点仍如实归于主控#299的解释及既有独立审查，不冒称用户逐字指定时点。

本轮亦备好 E1许可与 E2～E6/I3～I4 的独立START、完整读屏/cmp、从真实事件生成空签字permission、只读check-only、一次Enter、只读collect命令；未来dispatch/request/permission ID不预填，自动根只观察真实gate feedback/inbox wake，实际全局seq不按阶段号推算。E3后E4/I3可交错，先分别及时START到许可屏，按A15顺序先结算I3/I4再回E4，不重发180秒批准等待中的POST。所有已有phase批准仍空；未来permission批准只能等真实dispatch/原屏后生成。

[材料静态核对](09b-a16-e1-preparation-01/static-check.json) **PASS**：43份命令文件、61条命令/比较步骤、9份空签字phase批准、现有实际B1 manifest、完整reader闭包和新输出检查通过；I2 delivered读回与A15已实跑的oracle仅实例路径不同。预算表见 [stages](09b-a16-e1-preparation-01/stages.json)，ideation4根/6POST、executor6根/11POST，合计17POST/七次许可/模型0；I1已用1根/2POST/一次许可，后续预期9根/15POST/六次许可。

本轮 **未执行 readiness、arm、initial release、任何阶段、读屏、Enter、collect、owner生成、归档或清理**。HTTP/hook逐条原件继续留在活root，结束前必须按rev2先外置归档/逐字读回/独立重数并留archive清单，再正常停机，停机后不读SQLite。当前A16后续、09C与整票保持 **INCOMPLETE／NO_GO**；本次材料PASS不代替未来真实运行。

## 主控 #349：A-16 全阶段完成；逐 POST/hook 原件核对与回收待批

主控逐阶段代签执行全部I/E阶段，每次工具许可前完整读屏、核对命令/原stop/❯ 1. Yes，check通过后一次Enter。本轮把executor readiness、I2 arm/collect、E1～E6与I3/I4的全部START/许可/Enter/Electron/读回/签字，以及原delivered-I2读回一并提交，原文件不覆盖改判。主控实跑各阶段结果均符合冻结protocol；worker本轮未执行业务或许可动作。

[全场核对](A16-FINAL-READBACK.md) 与 [最终JSON原件索引](09b-a16-final-check-03/result.json) **PASS，限worker只读核对，非新会话独立验收**：直接读取逐POST request/response/meta、hook stdin/started/finished/stdout/stderr，得到ideation6POST/4根/2许可、executor11POST/6根/5许可，合计 **17POST、10根、7许可、135个hook文件、模型0**。17次HTTP均200/complete，原件字节与meta/wire一致；Bash.command/真实tool_result同ID、7次CR action各关联唯一写出，UPS/Stop/idle/原登记逐根吻合，E578282字节原屏完整分页/EOF。模型0依据实际两角色runtime-manifest指向原loopback假API及冻结无转发SSE源码，不把CLI模型标签当供应商执行证明。

实际全局seq为 **I1=2、E1=3、I2=4、E2=5、E3=6、I3=7、E4=8、I4=9、E5=10、E6=11**，从原请求登记正文、实际dispatch_records/事件关联核对，不按阶段号推算。目标received.bin相对baseline恰增加 **1b**，唯一实际中断actor executor、thread为原target；错目标/越权ack/已ack再停的真实拒绝均符合contract，E3/E4同一ack且只有一次wake。

原stop `d48f9f7c-187e-4fcd-b125-58ec345710b6` 的created_at仍21:06:39.345Z，原request `4c754e99-a65e-450f-8381-bbb92d6114a0`；I1 Stop结果pending/role_session_missing、此前没有原I2反馈。角色上线后先queued，**E1 turn_submitted seq176** 才delivered（21:27:34.209Z），再有 **原I2 feedback seq187**；原I2反馈/登记/提交各一次。来源为原I1 HTTP tool_result及停机前活库一致只读事务，交叉核对已有DELIVERY-I2原件。该时点继续如实归于主控#299的解释，不改用户原话。

核对器自身首轮 [01](09b-a16-final-check-01/result.json) 因误读HTTP meta不存在的dispatch_seq而INCOMPLETE，失败保留；修为读取原请求登记标记和实际派发行后 [02](09b-a16-final-check-02/result.json) PASS，增加逐根idle/Stop和单ack wake后的03 PASS。缺response、截断SSE、重复UPS三种一次性副本反例被同一读取函数拒绝，副本已删，活root/原件未改。两次s11的发键后采集拒绝仍为原INCOMPLETE，不能据此重按或修改冻结reader。

[回收材料](09b-a16-closeout-materials-01/README.md) **静态准备PASS，实际回收INCOMPLETE**：只写01～07分步命令，先用原Stage A/B1绑定九PID完整argv/lstart/图、生成空签字cleanup草稿与只读dry-run，再停机前rev2结构脱敏capture。staging与tar均在外置盘，预定 `.../T-078/09b-a16-raw-01/scene.tar.gz`，逐成员字节读回、每原件archive指针、独立tar重数/原stop-I2/单Esc核对通过且readback签字后，才认证daemon_stop/panes.shutdown，两原API各一次SIGTERM，确认九进程退出、文件/归档及尾部未变后删root；停机后不读SQLite。slot不删除。归档/staging/仓内readback与cleanup输出目录已只读检查为全新。

cleanup静态记录 [02](09b-a16-closeout-materials-01/static-check-02.json) 修正首份报告把here-doc数量写成4的元数据笔误（实际3），原报告保留，已执行的语法/路径guard结论不变。**本轮没有运行owner、cleanup批准生成、dry-run、capture、tar readback、签字、停机或删除**。逐POST/hook原件仍在活root，当前不能宣称F1外置保留已完成；主控需依序实跑并保留实际bundle/pointers和cleanup收据。

A16业务阶段与原件worker核对局部 **PASS**；归档/回收与独立审查尚未完成，09C尚未执行。系统IME按用户选择仍未验证/INCOMPLETE；三窗格与真登录分别移T091/T092。本票整体仍 **INCOMPLETE／NO_GO**，不以本轮全场核对替代其余验收或宣布整票通过。

## 主控 #350：A-16 原件外置保留与回收 PASS；09C Stage A 冻结复核

以上是 #349 交接时点。本次主控已依次执行九进程 owner 核对、签署 cleanup 批准、dry-run、停机前原件采集归档、tar 独立重数并签字、归档验证、保存清单，最后正常停机回收，全部 **PASS**。实际收据及签字件随本次提交保留：[dry-run](09b-a16-cleanup-01-dry-run/result.json)、[cleanup 批准](09b-a16-closeout-materials-01/cleanup-approval.json)、[签字重数](09b-a16-raw-readback-01/readback.json)、[tar 内关联核对](09b-a16-raw-readback-01/a16-review-check.json)、[finish](09b-a16-cleanup-01/result.json)。本轮 worker 仅只读核对这些原件，未再执行采集、停机、信号或删除。

归档为 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a16-raw-01/scene.tar.gz`，**826,185 字节、929 成员**。仓内保留 [bundle 清单](09b-a16-closeout-materials-01/bundle.archive.json) 与 [逐原件指针入口](09b-a16-closeout-materials-01/raw-pointers.archive.json)，每份原件的 `*.archive.json` 留在外置盘 `09b-a16-raw-01/pointers/`。HTTP request/response/meta 与 hook stdin/started/finished/stdout/stderr 均保留脱敏原件；采集接口不接收认证头，HOME、凭据与 SQLite 不入 tar。主控报告凭据扫描为 0；这一扫描结论归于主控，不冒称 worker 另做了凭据扫描。

主控从 tar 独立重数：ideation **6 POST / 4 根 / 2 次 PermissionRequest**，executor **11 POST / 6 根 / 5 次 PermissionRequest**，合计 **17 POST / 10 根 / 7 次工具许可**。worker [本次只读复核](09c-stage-a-recheck-01/result.json) 再用冻结 reader 读取 tar，计数与签字收据一致、无未完成 HTTP/hook；并逐成员核对 staging 的类型与字节、逐原件核对 archive 指针。原 stop/request、target 恰一个 Esc、`turn_submitted 176 → delivered → 原 I2 feedback 187`、I2 反馈/登记/提交各一次的 tar 读回见上述关联核对，与 [A-16 全场记录](A16-FINAL-READBACK.md) 对照。模型 0 的依据仍为实际 loopback 启动记录与无转发的假 API，不外推为供应商账单观测。

因此，A-15 终审 **F1 所要求的可独立复核原件缺口，由替代场次 A-16 补证完成**：后续 reviewer 可以直接从 tar 重数与核对逐 POST/hook，证据不再只剩汇总投影。A-15 原件已缺失的历史事实、旧 NO_GO 报告及原结论不改；主控独立重数与 worker 复核也不冒充全新 reviewer 的终审。

finish 收据确认：认证 `daemon_stop → panes.shutdown` 正常关闭角色与目标，两只原 API（34330、34331）各收到一次 SIGTERM，九进程全部退出；归档与原件稳定性核对通过后，根 `/private/tmp/t078-2-09b-run-z9ov_cco` 已删除，**停机后 SQLite 读取为 0**。worker 只读确认根不存在；slot 未处置。

09C Stage A **静态准备 PASS，实际运行 INCOMPLETE／NO_GO**。本次通过真实 `validate_stage_a_inputs` 的静态校验路径（仅内存签字夹具；未调用 runner.main/card/root/spawn），并确认实际未签批准被拒。`09c-executable-materials-02` 的 **312 个冻结源码文件**与 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1` 及当前工作树逐字节相同，静态 root 与必要夹具仍在；该源码之后仅本票证据变化，**无需重新冻结**。四份绑定回归收据仍适用：整组 [02](review-followup-regressions-02/result.json) 的整体 INCOMPLETE 仅为旧 mutant-cas 分类断言，明确由 [cas-03](review-followup-mutant-cas-03/result.json) 替代，未运行的 lock 由 [lock-04](review-followup-mutant-lock-04/result.json) 补齐，另有 [T-078 自身回归](merge-main-4-t078-regressions-01/result.json) PASS；未静默忽略 02 的失败状态，旧原件保留。

沿用 [Stage A 命令](09c-materials-01/STAGE-A-COMMAND.txt) 与 [未签批准件](09c-materials-01/stage-a-approval.json)（`approved_by`、`approval_ref` 均仍为空），输出 `09c-stage-a-01/` 尚不存在。主控签字后由主控执行；本轮未运行 09C、未创建现场或发送输入。09C 预算仍为 ideation **4 根 / 7 POST**、executor **1 根 / 1 POST**，模型 0；后续真实时钟、完整原屏逐项核对与条件式单 Enter 的停止条件不变。系统 IME 保持未验证／INCOMPLETE，三窗格与真登录已分别移 T-091/T-092；整票仍 **INCOMPLETE／NO_GO**，待 09C 与新一轮独立审查。

## 主控 #351：09C Stage A READY；两角色首启与全部阶段材料

主控已按 rev2 授权签署 [Stage A 批准](09c-materials-01/stage-a-approval.json)，运行得到 [READY_FOR_APPROVAL](09c-stage-a-01/readiness.json)，root `/private/tmp/t078-2-09c-run-slm9wocj`，实际目标 claim/attempt/fence/thread 齐全、模型 0。本次将签字原件及 Stage A 全部输出入库；签字件不恢复为空。源码仍为 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1`，四份回归收据组成与 #350 相同。

用冻结的 `prepare-a14.py --mode role --instance c1` 仅生成文件，已备 [ideation P1/B1](09c-c1-b1-ideation-p1-01/B1-COMMANDS.txt)、[executor P1/B1](09c-c1-b1-executor-p1-01/B1-COMMANDS.txt)，各有实际 Stage A binding、独立 launch/session、模板端点 `http://127.0.0.1:0` 与原 API ready 绑定、空签 B1、六键逐屏草稿、完整分页读屏及 `-02` 重读命令、签后 readiness 核对。B1 plan 保留 `security-notice + screen_text`，实际 s7 key 使用 `onboarding-notice`。两角色启动步骤必须串行：ideation 首启结束后才启动 executor；**本场 executor 必须在 C-I1 前完成首启**，避免把两分钟无 ack 计时消耗在 onboarding 上。

[交接顺序](09c-c1-preparation-01/HANDOFF.md) 与 [静态核对](09c-c1-preparation-01/static-check.json) **PASS，限材料**：42 份命令文件、82 条命令/比较步骤、28 处明确的未来产物依赖；312 个冻结源码文件及两 P1 副本逐字节一致，两角色路径隔离，实际 B1 校验函数用内存夹具通过，现场批准仍空。所有现有入口路径存在，未来 manifest/permission/original-screen/stop 等只等前序实际运行产生，不预造 ID。独立命令在实际两 B1 bind-launch 后，再用文件专用绑定步骤填入真实 manifest 路径，不复制或写死历史场景路径。

已备 C-I1、C-E1、C-I2、C-I3、C-I4 的空签 phase 批准、独立 arm/observe/许可/collect 命令。两角色 0 POST/空提示符 readiness、owner 九进程核对与唯一 C-I3 build 均在计时前完成；五阶段预签 arm 不发送业务输入。C-I1 才经 pane_dispatch/release 输入批准的 test-simulated-user 请求；之后只读实际 inbox wake 与 gate feedback，不新派发、不硬编码 global seq。预算 ideation **4 roots / 7 POST**、executor **1 / 1**，共 **5 roots / 8 POST / 3 次工具许可、模型 0**；C-E1 单条 SSE 保持无 ack，C-I3 实际中断证据完成后才结束。

C-I3 [预批准契约](09c-c1-preparation-01/C-I3-PREAPPROVAL-CONTRACT.json) 仍未签；实际完整原屏/模板由该场 Electron 窗口生成，主控逐项核对 command/stop/目标/原屏/事件/窗口与输入代次后，才只填两个签字字段并原子发布。冻结 driver 在真实 wall age >120000ms 且 monotonic 观察 ≥120100ms 后、最迟 130000ms 开始一次 Enter，场景总截止 150000ms；按键前重读完整分页/EOF、全部原屏字节与绑定逐项一致，任一不符即 INCOMPLETE、零新键，写入未知不重按。实际 Stop/relay、无 ack、actor ideation、目标恰一个 Esc 且未回收、原 C-I4 反馈与全部 POST/hook 均须随后读回；本轮不冒称这些已验证。

本轮 **未执行 B1 dry-run/real、读屏、六键、readiness、bind/owner、build、arm、初始化、任何业务阶段、HTTP 请求或真实时钟观察**，只写文件并运行静态校验。业务源码、冻结包与 driver 均未改，09C 实际时序及整票仍 **INCOMPLETE／NO_GO**；系统 IME、T-091/T-092 的边界保持 rev2 原裁定。
