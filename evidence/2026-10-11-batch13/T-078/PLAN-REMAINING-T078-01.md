# T-078 剩余三项验证计划（主控 #333，2026-10-16）

**计划待审；三项运行均 INCOMPLETE，launch NO_GO。** 本轮只读源码/既有回执、写计划，不建实例、不启动 daemon/API/Claude/Codex/Electron、不输入或切换系统设置。A-15 已回收，不能复用其 PID、root 或旧身份批准。

目标是补三项明确证据：真实时钟的 09C、同任务三窗格联合视图、真实系统 IME。非目标是模型判断质量、真登录、真实 Codex 行为、日常派发切换、扩大 Computer Use 权限或凭计划直接修改 UI。原 ticket、[09BC 计划](PLAN-09BC-01.md)、[全票状态](RESULTS.md) 的其他缺口与独立审查仍保留。

**Tracer bullet**：每项先通过真实入口取得一个可证伪样本，再加对应反例；不先建完整模拟层。**Deep modules**：沿用 window IPC、Panes、原生 hooks、relay 和唯一门禁，不另造工具批准、输入或收件箱接口。**Ubiquitous language**：严格区分 queued、pending、delivered、工具排队回执、门禁执行结果、用户本人和 test-simulated-user。

## 预算及执行前提

下表都是拟议硬上限，须经主控审定后冻结各阶段，不是启动授权。每次实际 POST 都计数，含等待中的 POST、409 和 CLI 自身重试；发生额外请求即 INCOMPLETE、停止，不补预算。

| 项目 | 真实供应商模型回合 | 真实交互 Claude / Codex 会话 | 确定性目标 | roots / 主 Messages POST | Electron |
|---|---:|---|---|---|---|
| 09C 主场 | 0 | Claude 2（ideation/executor）；Codex 0 | 1 个经真实 claim 的 worker 接收器 | ideation ≤4/7；executor ≤1/1；总计 ≤5 roots/8 POST | 许可/读屏窗口一次只开一个；启动角色串行 |
| 三窗格独立场 | 0 | Claude 2；Codex 0 | 1 个受管 worker 接收器 | 两个主控业务 roots/POST 都为 0 | 现 UI 方案需 3 个隔离进程/窗口；若要求单窗三 pane，先安排实现 |
| 系统 IME 独立场 | 0 | Claude 0；Codex 0 | 1 个受管 worker 接收器 | 原生模型 roots/POST 为 0；仅两次 IME 样本 | 1 个隔离窗口 |

三窗格若在 09C 两角色首启完成、stop 创建之前拍摄，可复用这两会话和一个目标，不额外增加 CLI/POST；仍须先明确窗口布局和内存门槛，不能为省会话而污染真实时钟段。否则三项顺序独立建场/回收，累计 Claude 4、真实 Codex 0、真实模型 0；不并开第二套后台。接收器均明确是测试替身，非真实 Codex。

新的标准 prepare 必须先补 reader 源闭包 issue `20261016T120838Z`，冻结完整分页 helper 与三个 caller；不得把 A15 专用包的通过结论当新包证明。运行前核对最新源码/合并状态、oracle_paths、固定 Claude 2.1.296、实际 dispatch/claim 身份、独立 HOME、逐屏计划与所有批准字段。先做 file/check-only 和真实 daemon/relay/HTTP 的无 Claude 排练，覆盖 queued tool_result、Stop 后执行与各自动根；只有主控审定完整包后才起真实 CLI。权限 Enter 继续使用同一产品窗口/awaited 回执、完整分页原屏校验、每次唯一 slot/output。

本机内存受限：串行启动，一次只做一角色引导；启动前由主控审定可用内存上限、每步保存整个进程树的实际 RSS/内存压力。没有现成测量，不承诺固定 MB 数。超过上限或身份/源码改变就停止，不增加额外代理，不用分拍冒充同时显示。

## 一、09C：真实时间超过两分钟，无 ack 后 ideation 只中断

**已知事实**：当前 [core.emergencyStop](../../../workbench/src/gates/core.ts) 仅对 ideation 要求 `now - stop.created_at > 120000`，之后核对无 executor ack、stop.refs 与目标、实际运行身份，最后经 runtime.interruptThread。A15 已证明工具仅返回 queued、实际业务要到真实 Stop 才转交；新协议必须沿用这个时序。A15 不能证明这条真实时钟分支。

**最小做法**：一个全新 scratch root、同任务两个真实 Claude 角色、一个受管确定性目标。两个角色先完成 B1/onboarding/初始 readiness，权限均 manual；executor 先进入可接收状态。主控批准一条 `test-simulated-user` 窗口 stop 请求，明确持续要求在本次 150 秒观察期内停止该唯一目标；取消要求立即终止试验，不让 fixture 编造用户继续要求。

| 阶段 | 根的真实来源与动作 | 预算（roots/POST） | 可证伪条件 |
|---|---|---:|---|
| C-I1 | 批准的模拟窗口输入经 pane_dispatch/release；API 下发 Bash command，实际 inbox send；工具 queued，真实 Stop 生成 stop | I 1/2，一次许可 | stop.from 必须 ideation；refs/实际调用者、created_at 齐全，不用 operator 代 send |
| C-E1 | 原 stop 的实际 inbox wake；executor UPS/HTTP 收到正文后保持 SSE 回合，不给工具、不 ack | E 1/1，无许可 | 必须实际 delivered/有接收证据；未送达或 API 错误不能算“已收到但不 ack” |
| C-I2 | 原 send 的真实执行反馈触发根；在 stop 年龄仍 <120 秒时，真实 ideation CLI 调相同 stop 命令 | I 1/2，一次许可 | 匹配 Stop 后门禁必须 stop_too_early，target 新字节 0，无中断事件 |
| C-I3 | 原 too-early 执行反馈触发根；该根的单次 HTTP 请求保持连接，至真实年龄 >120.1 秒才下发相同目标/stop 的 tool_use | I 1/2，一次许可 | 真实 Bash→queued→Stop 后 actor=ideation，恰一次 Esc；不得 executor/operator 代执行 |
| C-I4 | 原成功执行反馈，只确认并 Stop/idle | I 1/1，无许可 | 不调用其他工具、不 ack、不产生额外 Esc |

合计 ideation 4 roots/7 POST、executor 1/1、三次一次性工具许可。**不照搬 09B 的 I=4/6**：新增的提前拒绝和晚到工具结算需要 7 POST；仍低于既定每角色 6 roots/12 POST、合计24上限，但须作为 09C 新 manifest 明确批准。原 09B protocol/预算原样保留。

时钟与保持屏障的实现方案待准备阶段排练：C-E1 连接维持到整场结论/收尾；C-I3 用 SSE 心跳保持单个 POST，不能沿用旧90秒超时、不返回409诱发重试、不多开轮询 Messages。时间从真实 stop.created_at 算，同时在观察到实际条目时记录 UTC/monotonic；每≤20秒只读采样 no-ack、目标/角色身份、要求有效和 target 字节。至少保留 <120 秒拒绝点、>120000ms 的真实执行点、墙钟/单调时钟对应原件。时钟跳变/休眠导致解释不清即停，禁止改 created_at、快进时钟或用 sleep 时长充当门禁执行时间。

**120～150秒窗口是硬约束**：总观察从真实 stop 创建起算 ≤150秒，晚到门禁调用必须在其中完成。C-I3 的许可必须预先得到“符合实际命令/stop/目标/原屏条件后自动单 Enter”的明确授权，或有人能在余下窗口审签；未能及时批准就 INCOMPLETE，不延长150秒、不略过许可。driver 在按键前完整读屏，核对实际命令、❯ 1. Yes、真实 PermissionRequest 与预批准模板，再经原 Electron 单键通路。最晚时间到即停自动化、保存现场，后续 owner-bound 回收另批；停止观察不等于擅自杀会话。

**独立 oracle**：真实 UPS/Stop 原件、每个实际 HTTP POST、异步请求/relay 回执、同一个 stop/目标/attempt/fence；created_at 不变且无 ack；早期 target 0，晚到后恰 `1b`；emergency_interrupt_intent/requested.actor=ideation；目标 PID/lstart、workspace、task/attempt/fence 仍原值，没有 kill/reclaim/archive。阈值守卫删除的坏实现应在提前拒绝点失败；不执行中断的坏实现应在实际字节/事件点失败。先在真实 daemon/relay/HTTP 排练里证明这些 oracle 能失败，排练不替代真实 Claude 时钟场。

**权限/待决定**：新两角色 CLI/假 API/后台/目标、隔离 Electron 启动与逐屏/工具单键、外置构建/归档/实例回收须逐项批准。Computer Use 如采用，只限 worker 自己启动的隔离 Electron，沿用已有代批边界，不操作系统设置或其他应用。用户给执行主控的逐字授权是“授权你代签 T-078 09B 各阶段批准”，仅限09B，**不据此代签09C**；需用户决定09C由谁签，以及能否批准上述条件式模拟用户持续要求/晚到单 Enter。批准前只准备材料。不能在150秒内完成完整许可与收据时，结果就是 INCOMPLETE，不能放宽时限。

## 二、同任务两个主控＋一个 worker 的三窗格联合视图

**observed**：当前 [renderer](../../../workbench/app/renderer.tsx) 只有一个 Terminal、一份 Snapshot 和一个 `<section className="pane">`；[main](../../../workbench/app/main.ts) 一个 Electron 进程只创建一个 BrowserWindow，绑定单一 launch，窗口 minWidth=900/minHeight=650。当前没有现成的同窗口三 pane 布局，不能写一条不存在的“打开三窗格”命令。

**最小可证伪做法及决策分支**：

- 若原 ticket 的“同时在一个任务下”允许三个现有产品窗口：用同一 daemon/task 的三个真实 launch 分别开独立 user-data 的 Electron，串行打开，保持同时存活；在一个真实屏幕帧里展示三窗口的任务标识、角色/launch 和可辨终端输出，拍前拍后核对三份真实 workbench_snapshot 与 PID/窗口绑定，期间零输入/POST。禁止三张图后拼接或顺次切换冒称同时显示。屏幕必须容纳三份可读区域；可用显示面积及系统截图权限尚未知，不能以遮挡/缩到不可读掩盖。
- 若要求**同一个 Electron 工作台内的三窗格**：先由主控安排本票的 UI 实现/审查子任务，复用原输出/输入通路、每 pane 独立窗口身份与序号，不另建业务门禁；原方案的一次进程/全局 IPC handler 也须同时调整。完成真实 UI 入口反例后才能 capturePage 或录制该窗口。当前仅计划，不顺手改产品。

通过条件为同一时间、同 task 的两名 controller 与当前受管 worker 可辨且绑定正确；失败条件为错 task、历史 attempt、重复同 launch 冒充另一角色、截图与实际绑定不符，或三者不能同时显示。拍摄前给三个 PTY 各一个仅输出的独立只读标记，不向 Claude 发提示；用真实 snapshot 与实际进程身份核对，不能只看标题。以“给第三视图绑定错 task/旧 launch”的受控反例证明检查会拒绝，保留原始单帧 PNG（可加短视频但不剪辑）。

**权限/待决定**：主控/用户需先裁定三原生窗口同屏是否满足原验收，还是必须补单窗布局；worker 不自行降低验收。Computer Use 仅用于这些新建隔离窗口的摆放/焦点/截图，不碰用户窗口或业务输入。系统 Screen Recording/辅助功能权限是否已有尚未知；缺失时由用户处理，主控不能代批系统隐私授权。可用窗口 capturePage 无需拍用户桌面；若采用三独立窗口联合原帧，必须限定截图区域只含这三个隔离窗口。产品所支持的真实三窗格与仅截图方案不可混称。预算见前表；如允许与09C共场，先拍完并关闭多余观察窗口，再开始真实时钟。

## 三、系统 IME：真实候选/组合输入到后台/PTY

**已知边界**：当前 renderer 监听原生 compositionstart，现有失败方式验收用合成事件证明了代码路径。`isTrusted=true`、直接 sendInputEvent/typeText 或最终“中文出现了”本身，均不足以证明系统输入法真的参与。

**最小做法**：新建一个受管 worker 确定性接收器与单一隔离 Electron，无 Claude/Codex/模型。先确认本机已经启用的具体中文 IME、macOS/Electron/xterm 版本、原生按键来源及可拍候选窗；不安装输入法、不写全局输入设置。推荐由用户在场亲手只对该测试窗口输入固定期望短语“中文”，独立期望 UTF-8 文件由试验说明给出，不从产品输出生成答案。

两个样本足够回答当前缺口：

1. **提交样本**：先输入拼音并在候选尚未确认时暂停，保存真实候选窗和原生 composition/beforeinput/input 事件（测试侧只读监听，不派发合成事件）；此时不得把未确认拼音/候选写进 PTY。选择“中文”提交，确认文字后再单独一次 Enter。raw PTY 最终 UTF-8 恰为期望短语加实际提交控制字节，无重字/丢字/候选残留；后台用户输入串联与其一致，受管 worker 的 human_intervention 指向同一真实输入记录，CR 仍记 action。
2. **取消样本**：新一轮 preedit 显示候选后取消；未提交的汉字/拼音不得进入 PTY。若实际取消控制键穿过 IME 到 PTY，必须独立记录其原字节与 action，不预设系统一定吞掉 Esc，也不把该控制键误报成中文输入。取消后再输入一个 ASCII 检查窗格仍可用。

独立证据为真实候选/组合过程的窗口视频或逐帧图、原生事件顺序、后台窗口/输入代次、PTY 原字节与用户输入/人工介入引用。已知坏实现（compositionstart 后直接转发 preedit，或把提交文字再发送一次）须被样本1的“确认前0字节/确认后恰一次”检出；合成红态只验证 oracle，不替代两份真实 IME 绿态。真实输入法事件次序不同于合成时如实保留失败，不放宽为“最后看起来差不多”。

**权限/待决定**：需用户指定/确认已启用的中文 IME，并决定安排人在场，还是另批原生按键自动化的探针。若自动化只能直接插入文本/模拟 DOM 事件，就仍 INCOMPLETE；只有真实输入源、候选窗与 native composition 链路实证后才可用。Computer Use 限隔离 Electron/其 IME 候选，不查看剪贴板、不读取用户输入历史，不由 worker 自动改输入源菜单、系统设置或隐私授权；需要这些额外动作须单列给用户决定。没有人在场/无可靠原生驱动时，先做其他项，保留此项 INCOMPLETE，不能代签“用户已亲手输入”。

## 顺序与交接

先审冻结候选 `92874fe7f320a9a4a47e61adacedd26fc58078c7`，再由主控汇集三窗格口径、09C签字/限时单 Enter、IME执行方式三项决定。可独立完成的准备是 reader闭包修正与09C真实HTTP/relay无模型排练；需另派实际实现/运行任务，本轮不做。三窗格可在09C的时钟前共场；系统IME独立场最后做，避免输入源/候选状态污染主控CLI实验。

每份后续运行包必须列完整路径、未签批准、独立停止条件、owner-bound回收和外置脱敏清单；提交前用同一归属函数检查所有 git add 路径（含自生预检）并模拟最终干净。临时目录/服务用后按真实身份回收；停止后的验证只读归档，不读 SQLite。任何新增产品改动另冻候选并重新审查；本计划未给这些动作执行授权。
