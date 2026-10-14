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
