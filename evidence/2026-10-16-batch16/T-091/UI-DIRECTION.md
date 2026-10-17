# T-091-1 界面方向

日期：2026-10-17。状态：**INCOMPLETE**（方向稿待执行主控确认；尚未实现、构建或运行验收）。

归属：worker `s16-t091`，task `T-091`，attempt `a1`，启动记录 `launch-a818e11600754e8b8ad79aab63a17f83`。读回起点为 `44bbb7828459d81fab0d46069a19d3dd515a7732`；依据 T-091 `ready_rev: 1`、任务卡 T-091-1，以及 native-cli-orchestration spec 的第 5、9、12 节。

本步只交界面方向。目标是让同一任务中的构思主控、执行主控和一个受管 worker 在一个 Electron 窗口内同时可辨，并让用户看清键盘输入归属。方向确认后的验收仍须取得三份真实快照、进程身份、输入与输出证据和原始单帧截图。

范围沿用任务卡：复用现有终端与输入输出通路；不改门禁、紧急停止、收件箱语义，不增加项目／任务导航、系统 IME 或真登录功能。本步仅新增本文件，保留进场时已有的 `task-card-T-091-1.md`。

## 现状与方向依据

以下是 2026-10-17 的源码读回，不是运行时验收。

| 已读事实 | 来源 | 对方向的影响 |
| --- | --- | --- |
| `run()` 创建一个 BrowserWindow，闭包只有一组 launch、identity、sequence、inputQueue 和 pendingRelease | `workbench/app/main.ts:15` 起 | 一个系统窗口需要容纳多组窗格绑定；不能让三个终端共用这一组输入状态 |
| `Workbench` 只创建一个 Terminal，渲染一个终端 section | `workbench/app/renderer.tsx:32` 起、`:57`、`:157` | 保留任务外壳，把终端及其状态改为按窗格实例持有 |
| preload 的六条 IPC 通道都没有窗格选择参数；handler 在每次 `run()` 中全局注册 | `workbench/app/preload.ts`、`main.ts` | 调整既有 IPC 的路由和生命周期，不新增后台业务接口 |
| `workbench_snapshot` 校验 launch 所属 task，返回 role，但未返回主控 preset | `workbench/src/daemon.ts:237` 起 | 在同一快照中补出已有启动记录的 preset，以真实字段区分两个主控 |
| controller 启动记录保存 `role: controller` 和 `preset: ideation/executor`；worker 另有 attempt | `workbench/src/panes.ts:78` 起、`:112` 起 | 角色文案来自后台记录；不能按显示顺序或窗口标题猜角色 |
| 后台已有独立的窗口凭据、输入序号、请求去重和写前身份检查 | `workbench/src/daemon.ts:58` 起、`:109` 起 | 每个窗格各领取一份现有窗口凭据，沿用原输入合同 |
| xterm 与 PTY 均固定 160×45；当前终端挂载区最小宽度 1153px | `renderer.tsx`、`style.css`、`src/panes.ts` | 本票先保留终端网格，用各窗格自己的滚动区显示；不加入 PTY resize 接口 |
| T-078 rev 2 已将同窗三窗格移到 T-091；真登录和系统 IME 不在其通过范围 | T-078 Resolution | 旧结论只作回归入口线索，不能替代本票的重新证明 |

技能依据：已读 `frontend-production/SKILL.md` 及其 `references/look-and-copy.md`、`references/visual-family.md`。在指定技能目录搜索后未发现独立的 `same-visual-family` 或 `frontend-less-ai-tone` 入口；现有 `frontend-production/SOURCE.md` 明确记录这两者的规则已原样迁入上述参考文件，本稿据此执行。另按 `document-writing` 检查中文表达、事实保真和 UTF-8 交付；按 `project-map` 运行 session status，不改地图或 ticket。

## 布局：上方两个主控，下方全宽 worker

主行动是“选择一个窗格并输入”。沿用现有工作台的侧栏、任务标题和底部门禁栏；任务下的会话区域用细分隔线组成终端工作区。视觉重点只有当前输入窗格的蓝色边线及文字标识。

默认 1440×900，保留 224px 侧栏。两个主控各占上半区一半宽度，受管 worker 横跨下半区；上下初始各占一半可用高度。不做三张等宽卡片，不增加装饰性外边距或阴影。

```text
┌───────────┬─────────────────────────────────────────────────┐
│ a2a 工作台│ 任务编号 · 任务标题                后台连接状态 │
│           ├────────────────────────┬────────────────────────┤
│ 项目      │ 构思主控               │ 执行主控               │
│ 当前任务  │ task / launch / 状态   │ task / launch / 状态   │
│           │ 独立终端与滚动区       │ 独立终端与滚动区       │
│           ├────────────────────────┴────────────────────────┤
│           │ 受管 worker · 输入目标标识                      │
│           │ task / launch / attempt / 状态                   │
│           │ 独立终端与滚动区                                │
│           ├─────────────────────────────────────────────────┤
│           │ 当前任务门禁 · 当前 attempt · 候选 · 验收 · 集成 │
└───────────┴─────────────────────────────────────────────────┘
```

这是结构草图，不是产品截图或验收证据。图中的身份字段都是占位说明。

一个任务标题、一个任务门禁栏服务整个窗口。门禁栏只显示 task 当前状态及当前 attempt，不因点击主控窗格或历史窗格而切换门禁对象。每个窗格自己的 attempt 单独显示，主控显示“无 worker attempt”；执行状态与门禁状态分开，避免把“空闲”看成验收通过。

本票用启动时明确指定的多个 launch 装入同一任务；现有 `--launch` 参数可重复提供。单窗格也走同一套窗格实例路径，保留既有不指定 launch 时首次解析当前 worker 的行为，解析后固定绑定。此处只扩展启动选取，不做新增会话、拖拽编排、布局持久化、单格最大化或任务切换界面。

## 窗格标识、焦点与输入归属

每个窗格头部保留两层信息，不依赖终端内的标题文本：

- 第一行：角色名称、CLI、交互状态、输入能力。角色分别由 `role + preset` 映射为“构思主控”“执行主控”，由 `role: worker` 映射为“受管 worker”。缺失或未知 preset 显示“主控 · 角色未确认”，不猜成两个已确认角色。
- 第二行：完整 task id 和 launch id；worker 再显示 attempt。标识使用现有等宽字栈，可选取复制、允许换行。当前 `.slice(0, 8)` 不足以作为三窗格身份展示，改为可读的完整值；不把完整值只藏在 hover 中。
- 窗口身份 `window_id` 和 thread 随该窗格的真实快照提供给读回工具，不展示凭据 token。界面保留按窗格查找的身份属性，便于核对它与后台数据的对应关系。

输入能力和焦点分别表达。“可输入”只表示后台允许该窗格输入；实际 xterm textarea 获得键盘焦点时，该格另显示“正在输入：构思主控／执行主控／受管 worker”并加蓝色内边线。失去键盘焦点就移除“正在输入”，不保留误导性高亮。初次打开不自动向任一窗格送键，也不自动聚焦到 worker。

用户点击终端正文或用键盘聚焦该窗格的“进入终端”控件后，焦点进入对应 xterm。点击身份文字允许选取，不抢焦点。页面不设置把按键转发给“最近一次活动窗格”的全局监听器；输入、粘贴和合成 composition 事件均来自该格的 xterm。按钮获得焦点时保留按钮自己的可见焦点，不把它宣称为终端正在接收输入。只读窗格允许选取与滚动，输入状态明确为“只读”。

每格保留自己的“输入框已空，放行”、错误提示和“回到底部”。放行声明绑定该格的 launch、window_id、interruption、input_generation；切换焦点不替用户声明空框。worker 底部说明“在此窗格输入会记录为人工介入”；主控使用对应的用户输入说明，不在主控格显示 worker 提示。错误发生在本格就显示在本格；输入结果未知时该格停止发送，不自动重投。

焦点变化只用于本地显示，继续复用 `createFocusSafeWriter` 对 DECSET/DECRST 1004 的拦截和观察；不能因多窗格切换把 focus 序列送进 CLI。系统输入法不在本票验收范围，合成 composition 回归不写成系统 IME 通过。

## 复用组件与样式

已只读查看本地 Synara fork 在固定提交 `49cae984f22924de006e0f8358cb447eb881aaf6` 的来源片段：`apps/web/src/components/TerminalScrollToBottom.tsx`、`apps/web/src/index.css` 的字体／分隔线规则、`apps/web/src/theme/theme.seed.generated.ts` 的 Codex dark seed。以当前工作台已经适配的版本为实现基准，不搬入 Synara 的 provider、MCP 网关、整套导航或另一套主题。

继承当前 `workbench/app/style.css` 的六项族卡：

| 角色 | 当前值与沿用方式 |
| --- | --- |
| 底 | `#111111`；按钮底 `#262626`，hover `#333` |
| 字 | `#fcfcfc`；次要字 `rgba(252,252,252,.55)` |
| 强调 | `#0169cc`；用于焦点、当前输入标识；警告沿用 `#e6b450` |
| 边线 | `rgba(252,252,252,.12)`，1px 分隔 |
| 字体栈 | UI：`-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`；终端／身份：`"SF Mono", "SFMono-Regular", Menlo, monospace`；UI 基准 13px，终端 11px |
| 圆角 | 保留 `--radius: 10px`；按钮／任务行 6px，状态标识 4px；相邻终端以直线分隔，不逐格新增圆角容器 |

复用 `TerminalScrollToBottom`，每个实例接自己的 Terminal；复用 `terminalOutput.mjs` 的查询接管与顺序写入；复用现有连接、只读、活动、生命周期及门禁状态文案。新分栏只增加布局和焦点规则，不引入字体、图标包、渐变、玻璃材质或进场动画。按钮写具体动作：“进入终端”“重新连接”“输入框已空，放行”。长中文、完整 id、错误文案均须可换行；焦点同时用文字和边线表达。

## 窗口尺寸变化

保留现有默认 1440×900 和最小 900×650。以会话区域的实际宽度决定布局：

- 宽度至少 1000px：上方两格并排、worker 下方全宽；三格保持挂载和可见。
- 宽度不足 1000px：按构思主控、执行主控、worker 的顺序变为三行，等分会话区域剩余高度。三份身份头部和终端区域仍同时可见，不降为标签页或只显示焦点格。
- 窗格头部和动作允许换行；最小窗口下用紧凑间距，门禁明细可换行。各格 `min-width/min-height: 0`，终端独立横向／纵向滚动，页面不被固定宽终端撑破。尺寸变化保留已有输出游标、滚动位置与输入绑定。

终端仍是 160×45，不缩小字号把三格硬塞进去，不调用前端 fit 造成与 PTY 网格不一致。默认尺寸下全宽 worker 能获得现有终端所需宽度，两个主控需要各自横向滚动；最小窗口只能同时看见较少的终端行。这是本方向的明确取舍，不宣称所有列和所有行都同时可见。确认后用真实窗口检验 1440×900、1200×800、900×650，尤其检查最小尺寸的角色、输入标识、放行控件与终端是否均可到达；被标题或错误挤到没有终端区域则判失败，先调整布局再交付。

## 与 IPC、窗口身份的对应

**Ubiquitous language**：BrowserWindow 是一个系统窗口；pane 是任务内的一个 agent 终端区域；现有 `window_id` 是后台给输入视图签发的身份。同一个 BrowserWindow 中三个 pane 各有一个不同的 `window_id`，沿用既有字段和命令，不另起术语或认证机制。

| 层 | 方向确认后的最小改动 |
| --- | --- |
| main／启动参数 | 同一 task 接受多个明确 launch；先通过现有快照核对 task、launch、角色、版本及生命周期，再建立各格绑定。不能将未提供或失效的第三格默认为当前 worker。每格持有自己的 identity、sequence、inputQueue、pendingRelease 和关闭状态 |
| 全局 IPC | 六条现有 handler 每进程注册一次，以已登记的 sender BrowserWindow 和局部 pane key 定位绑定；继续校验 mainFrame。不存在或属于其他窗口的 key 拒绝。renderer 不能传任意 launch 或窗口凭据替换绑定 |
| preload | 原 snapshot／output／input／composition／release／focus-observation 方法带局部 pane key；凭据和后台路径仍由 main 持有，不暴露给 renderer |
| renderer | 一个任务外壳加多个终端实例。各格独立持有 Terminal、decoder、输出 offset、已绑定 launch、输入占用与放行声明、连接和错误状态。React key 固定为已核对身份，重排布局不重新创建终端 |
| daemon | 只在既有 `workbench_snapshot` 的 launch 投影补出记录中已有的 preset；优先保持现有 `window_open/input/close`、`pane_output` 和写前检查。若实现发现必须改变门禁或输入语义，停止并向主控报告 |
| 关闭 | 关闭 BrowserWindow 时分别结算三格已发出的输入／放行结果并撤销各自窗口凭据，再移除该窗口的路由登记；不停止 daemon 或 agent，不因清理一个窗口而移除其他窗口仍使用的全局 handler |

**Deep modules**：输入权限和真实进程判断继续由现有后台入口负责；前端只负责显示与选择输入目标。终端组件封装其实际状态和生命周期，不为六条 IPC 各写一层透传包装，不保留旧单窗格 renderer 作为第二条实现路径。

**Tracer bullet**：获确认后，先把现有一个窗格完整迁到按 pane key 路由的生产路径，跑通真实 snapshot→输出→输入→读回，再扩到三格。同一通路支持一个或多个实例，不先造三块静态终端外壳再补身份。

## 红态、绿态、反例与截图计划

本步仅取得源码层现状：起点的单个 Terminal、单个终端 section 和单组 main 输入绑定已读回。**完整红态尚未运行**。后续在第一次代码变更前保存起点源码摘录、完整代码版本和命令，并交执行主控运行隔离红态脚本。

1. 红态：主控运行脚本，在隔离夹具的同一 task 中建立已登记的两个主控与一个受管 worker，保存其真实启动与进程事实。使用起点标准构建与现有启动入口读回一个真实 Electron 窗口；记录该窗口实际只有一个终端区域，不能同时呈现预先列明的三份 launch。保存原始单帧、DOM 可见区域和后台快照。参数不支持多 launch 的解析错误只能作为补充，不能代替这个产品现状读回。
2. 绿态：在同一个隔离 BrowserWindow 中装入三份明确 launch。期待的 task、角色／preset、launch、thread、attempt 从启动前冻结的夹具记录取得，不从 UI 输出反推。分别保存现有 `workbench_snapshot --task … --launch …` 的三份原始结果，并以 `launch_show`、`pane_process_info` 和系统进程事实核对 shell、CLI leader、原生会话与 launch。三格必须同时有非零可见区域，并属于同一个 BrowserWindow；截图只提供同时可见的证据，身份由这些独立读回共同支持。
3. 输入／输出：逐格聚焦并发送不同的已批准测试文本，核对各自 `window_id`、从 1 开始独立推进的 sequence、用户输入目标和 PTY 写入收据；worker 输入应派生人工介入，主控输入不伪造 worker attempt。并行输出从各自 offset 推进，用各格独有输出及原 trace 读回检查串流；切换焦点不应新增 CLI focus 输入。发送动作与送达收据分开记录。
4. 反例：保持前两格不变，仅给第三格提供另一 task 的 launch，要求拒绝绑定且不向它写入；再给第三格提供已失效 worker attempt 的旧 launch，要求拒绝本次三格运行视图的第三格绑定，不领取其输入凭据，不把历史只读输出算成第三个当前运行窗格。既有单格历史只读查询仍须回归。另核对未知 pane key、重复输入序号、错误窗口／放行声明均拒绝。若第三格拒绝，不能静默换成新 current_attempt；证据中保留拒绝和零误投递事实。
5. 截图：三格全部完成身份读回后，在该隔离窗口一次捕获原始单帧。画面包含共同任务标题、三份角色／task／launch 标识、终端内容、当前输入标识和共同门禁栏。保留窗口边界，仅捕获目标窗口，不含其他应用；不拼接、不裁成多个区域重组、不覆盖标签或输出。不把顺次聚焦的三张图冒充同时显示。必要时附不剪辑短视频，记录三格各自输入；单帧不能单独证明交互正确。
6. 回归：用新候选重新跑 T-074/T-075 的交付、恢复、编排正反例，以及 T-078 的主控可输入／历史 worker 只读、输入来源与收据、空框声明、设备查询与 focus 拦截。沿用 `run_daemon_acceptance.py` 的 suite／probe／mutant 入口和现有 Electron 真实入口测试；现有驱动中对首个终端的全局 `querySelector` 及单份 latestSnapshot 假设须改为明确选定窗格，不能因驱动一直读第一格而误报三格通过。最终列出实际命令、退出码、断言结果、代码版本与证据位置，未跑项保持 INCOMPLETE。

执行边界：上述 Electron、受控 daemon／PTY、系统进程查询及截图操作都由后续脚本交执行主控运行，本 worker 不执行沙箱外命令、不请求升级。新后台服务必须脱离调用者进程组，结束只处理脚本登记且已核对身份的实例。运行脚本使用显式隔离 state、user-data、HOME 与当前获准的启动材料；真实 CLI 启动／hook／按键预算须在脚本中列清，不能把 T-078 的旧批准搬来当本次批准，且不执行 T-093 真登录。截图缺屏幕录制或辅助功能权限时停下报告，不打开系统设置。

构建使用产品标准命令和外置盘上的全新槽位，缺盘报错，不移动、链接或替换输出目录。每轮输出使用新目录，不覆盖失败结果。仓库仅留命令脚本、文本摘要、小型验收输入与允许保留的小原始单帧；完整 run／fixtures、原始二进制、SQLite、监视日志和视频由主控按 T-088 归档到外置盘并留 `*.archive.json`（original、archive、bytes、replay，无校验值），删除原目录前核对文件数与总字节数。

## 本步检查与交接

session 起始和交接前均运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`：均退出 0，Problems 0，Stale living docs 0。本步未运行产品测试、未启动 Electron／daemon／PTY、未查询系统进程、未截图，也未改变任何源码或验收文件。完整运行红态、三格可用性、最小窗口可读性、真实输入输出隔离和回归结果均待方向确认后取得。

待确认的方向是：上方双主控、下方全宽 worker；每格完整身份与实际键盘焦点标识；同一 task、独立窗口凭据与 IPC 路由；保持 160×45、各格独立滚动。到此停止，确认前不开始实现。
