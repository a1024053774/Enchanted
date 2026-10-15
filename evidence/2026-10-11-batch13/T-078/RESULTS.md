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
