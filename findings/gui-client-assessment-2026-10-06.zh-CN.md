# a2a 图形客户端方向评估

日期：2026-10-06  
性质：日期记录（研究与评估）。只做了只读调研和本机测量；没有安装 GPUI、编译原型，也没有修改 Herdr、Enchanted、`intent.md`、项目地图或 ticket。  
输入：Codex 会话 `01a10d07-aada-76c0-9684-0ffa994af606`（a2a 规划与 T-005～T-009 执行）和 `01a102ef-c6d9-7bc1-b62b-52daf1be7135`（Enchanted R6 与 GPUI 调研）；Enchanted 的 GPUI 调研记录 `~/Documents/Code/Enchanted/plans/enchanted-r6/gpui-research-2026-10-06.md`；本仓库代码；Herdr 上游 `herdrdev/herdr@c4653a4`（0.9.3，本机克隆位于被 Git 忽略的 `.upstream/herdr`）。

**方向门：INCOMPLETE。** 基于 Zed 二次开发判为 **NO_GO**。推荐方向要成立，还需要 4 个探针（P1～P4）的结果和你的 7 项决定（D0～D6）。

## 结论

1. **不建议基于 Zed 二次开发。**
   - 许可：Zed 只有 `gpui` 等少数复用 crate 是 Apache-2.0；`ui`、`theme`、`markdown`、`terminal`、`terminal_view`、`workspace`、`editor`、`agent_ui` 都是 GPL-3.0-or-later。fork 之后，客户端整体受 GPL 约束。
   - 构建：Zed 在 macOS 上要求完整 Xcode。本机只有 Command Line Tools，系统盘约 21 GiB 可用。
   - 体量：249 个 crate，Rust 源码约 62 MB，约为 Herdr 的 5.5 倍；核验当天上游仍有推送。fork 之后要由你一个人持续跟进上游。
   - 模型冲突：Zed 的 Parallel Agents 由 Zed 自己承载线程。外部 agent 走 ACP，Terminal Threads 跑在 Zed 的终端里；文档没有提到供外部编排器或终端复用器接入线程系统的接口。接入 Herdr 意味着改写 Zed 的终端和线程后端，每次同步上游都要处理这部分冲突。
   - 想复用的部分不必 fork：这次查到的两个同类 GPUI agent 工具都没有 fork 整个 Zed。muxel 以 git 依赖引用 `gpui`，并使用 Longbridge 组件库；agentZ 把 Zed 的 GPUI、`ui`、`theme`、`markdown` 等 crate 复制进自己的工作区，同时附 Apache 与 GPL 两份许可文件。
2. **推荐：独立 GPUI 应用，作为 Herdr 和 `coop.py` 的客户端。** UI 层用锁定版本的 `gpui-kit 0.7.1`（Apache-2.0），只经公开接口连接：Herdr JSON socket API、`herdr terminal session observe` 与 `herdr agent attach`、`coop.py` 的 JSON CLI。这样不改 Herdr，符合 intent 中"先用适配层，出现可复现的公开接口缺口再决定是否改内核"的规则。这条建议要等 P1～P3 通过才成立。
3. **截图风格可以做：借信息架构，不借执行模型。** Synara 是 MIT 许可的 Electron 应用，通过各家 agent 的原生协议直接驱动 agent；a2a 的 agent 运行在 Herdr pane 里。建议中栏显示原生会话记录的实时投影，终端仍由 Herdr 持有（见"产品形态"）。
4. **先做 a2a、Enchanted 搁置后并入：同意。** 两者的接缝是原生会话记录：a2a 实时看，Enchanted 事后复盘，可以共用一套解析和渲染。Enchanted 目前没有版本控制，搁置前应先做快照。
5. **图形客户端超出了已接受的 intent。** `intent.md` 的目的地是协作运行层，不含图形客户端。按 AGENTS.md 的停止边界，本记录不改地图、intent 或 ticket，等你确认方向后再落盘。

## 现状

| 对象 | 状态 | 依据 |
| --- | --- | --- |
| a2a | `coop.py` 986 行：Python 3.9 标准库、SQLite（`tasks`、`attempts`、`verifications`、`events` 四张 JSON 表）、Git 和 Herdr CLI。成功输出 `ok=true` 的 JSON，拒绝输出 `ok=false,error`。T-006～T-008 已通过，frontier 是 T-010～T-014 的流程改进。没有图形界面。 | measured / observed |
| a2a 约束 | 验收与集成只能经过持操作锁的 CLI 入口。客户端只能调用 CLI，不能直接写 `state.sqlite3`，也不能自行实现门禁。 | [AGENTS.md](../AGENTS.md) |
| Herdr | Apache-2.0，0.9.3。Rust 源码约 11 MB（`src/` 约 27.6 万行）。服务端持有终端，客户端可以断开和重连。 | measured |
| Enchanted | 没有 `.git` 或 `.jj`。目录 2.7 GiB（含上游仓库与历史材料）。Rust core 27,029 行，React/TS 6,195 行，Tauri 2 + React。core 的命令和状态层仍耦合 Tauri；关闭调试信息后，Tauri core 的 `target` 为 1.50 GiB。 | 行数与版本控制为 measured；耦合与 1.50 GiB 引自 Codex 调研 |
| 本机 | macOS 27.0，Rust 1.96.1，只有 Command Line Tools（无完整 Xcode），系统盘约 21 GiB 可用，Herdr 客户端 0.9.3，已安装 Zed.app。 | measured |

## 关键发现：Herdr 已经给外部图形客户端留了接口

1. **控制面**：JSON socket API 附带 JSON Schema（`herdr api schema --json`），本版 schema 列出 128 个方法与事件名，覆盖 workspace、tab、pane、agent、worktree 和 `events.subscribe`。
2. **终端面**：`herdr terminal session observe <pane> --cols N --rows M` 输出 NDJSON 格式的 `terminal.frame`（base64 编码的 ANSI 字节）。文档写明它面向第三方桥接，允许多个只读观察者。`herdr agent attach <target>` 提供可写直连，同一终端只有一个可写所有者。
3. **会话映射**：`pane.get`、`pane.list`、`agent.get`、`agent.list` 在 Herdr 存有原生会话引用时返回只读的 `agent_session` 对象。本机 Herdr 安装的 Codex 集成（integration v8）在 SessionStart 时上报会话 ID；Codex 的会话文件名带同一个 ID（`~/.codex/sessions/YYYY/MM/DD/rollout-*-<id>.jsonl`）。客户端由此能从 pane 找到对应的会话记录。
4. **更深一层的协议**：Herdr 自己的客户端使用 endpoint generation 1（`shell.snapshot.v1`、`shell.surface.v1`、`shell.input.semantic.v1`、`shell.blob.v1`），服务端直接下发单元格网格和增量补丁。文档承诺这一代协议跨版本稳定，但它是 Rust 内部类型的 bincode 编码；Herdr 没有 lib target，协议类型还依赖 `raw_input`、`api::schema`、`input`、`config` 等内部模块。只有公开接口确实不够用时，才考虑复制这些类型或 fork Herdr 抽出协议 crate。

由此推断：图形客户端不需要自己持有 PTY，也不需要 Zed 的终端后端。终端面板需要的是一个 VT 解析器（`alacritty_terminal`，Apache-2.0）和一个 GPUI 绘制元素。Zed 的 `terminal_view` 和 muxel 的终端元素都是 GPL 实现，只读参考，不复制代码（见 D4）。

## 路线比较

| 路线 | 与 intent 的关系 | 许可 | 构建与磁盘 | 维护面 | 截图外观 | 判断 |
| --- | --- | --- | --- | --- | --- | --- |
| A. 基于 Zed 二次开发 | 需要用 Herdr 替换 Zed 的终端和线程后端 | 整体 GPL-3.0 | 需完整 Xcode；249 个 crate；实际占用未测 | 跟进持续更新的上游 | 要改造编辑器布局 | NO_GO |
| B. 独立 GPUI + Herdr 公开接口 | 一致：Herdr 与现有 CLI 用法不变 | 不引入 GPL 参考代码时，可全部为 Apache/MIT | 只需 CLT；依赖需优化编译，首编更慢；占用待 P3 实测 | gpui-kit 近三版各隔一周，且锁定 GPUI 快照，升级要当作一次维护任务 | 组件齐全，需要自己拼 | 推荐，待 P1～P3 |
| C. GPUI 自管终端（muxel 式） | 冲突：绕开 Herdr，`coop.py` 的 dispatch、observe、reclaim 失去依托 | 参考 muxel 代码即为 GPL | 同 B | 自己维护 PTY、持久化和状态检测 | 同 B | 不建议 |
| D. Electron，基于 Synara 二次开发 | 冲突：Synara 用各家原生协议直接驱动 agent | MIT | 没有 Rust UI 编译，但有 Node 依赖和 Electron 运行时 | 跟进活跃上游 | 现成 | 最快拿到外观；与你的 GPUI 偏好和 Herdr 模型都冲突 |
| E. 保留 Tauri + React，只重做界面 | 一致 | 现有 | core 已测 1.50 GiB | 现有 | CSS 最容易调 | 你已决定离开这套栈，只作对照 |

关于磁盘：换成 GPUI 不会自动降低编译占用。GPUI 同样需要 Rust 编译缓存，gpui-kit 安装指南还建议对框架依赖做优化编译，并说明这会让首次编译更慢；muxel 在开发配置里也对全部依赖开了 `opt-level = 3`。能降低占用的是构建配置：共享 `CARGO_TARGET_DIR`、关闭依赖的调试信息、定期清理。P3 用这些配置实测。

关于用 AI worker 开发：GPUI 的 API 随快照变化。crates.io 上的 `gpui` 停在 0.2.2（2025-10-22），gpui-kit 0.7.1 锁定 `gpui-pre =0.3.8`，Zed main 上的接口也可能不同；模型容易混用不同版本的写法。这一点是推断，没有测量。建议把锁定版本的文档和示例放进仓库供 worker 查阅，并在 P2 中记录 worker 的编译修错轮数。

## 产品形态：终端优先还是对话优先

截图是对话优先的界面：中栏是结构化对话、运行时长和改动文件卡，终端在右侧辅助。Herdr 是终端优先：agent 是 pane 里的 TUI。两种形态的数据来源不同，需要先定。

| 形态 | 中栏内容来源 | 与 a2a 的关系 |
| --- | --- | --- |
| a. 终端优先 | pane 终端本身 | 改动最小；界面接近 muxel，不像截图 |
| b. 混合（推荐） | 原生会话记录的实时投影；输入仍经 Herdr 送进 TUI | 保留 Herdr 与 CLI 用法；最接近截图；与 Enchanted 的回放共用解析 |
| c. 协议优先 | Codex app-server、Claude SDK 或 ACP 的结构化事件 | Herdr 退到旁边，dispatch 和身份校验都要重写，偏离 intent |

推荐 b 的依据：T-001 要求保留 Herdr 和现有 CLI 用法，而 Herdr 已能给出 pane 到原生会话的映射。风险在于 Codex 和 Claude 的会话记录格式不是公开契约，会随版本变化，需要记录 CLI 版本并维护能力矩阵；P4 先验证可行性。

形态 b 下，截图各区域对应的内容：

| 截图区域 | a2a 客户端内容 | 数据来源 |
| --- | --- | --- |
| 左栏线程列表 | 按 workspace 分组的 agent 与 task；第二行显示 attempt、分支和门禁状态 | Herdr `agent.list`、`events.subscribe`；`coop.py status` |
| 顶部标签 | 已打开的 agent 或 task | 客户端状态 |
| 中栏对话 | 原生会话记录投影，加上 a2a 事件时间线（claim、submit、verify、integrate） | `agent_session` 对应的会话文件；`coop.py events` |
| 改动文件卡 | 候选 C 相对集成头 G 的 diff | Git，只读 |
| 输入框 | 发给该 agent 的文字 | Herdr `agent.prompt` 或 `pane.send_text` |
| 右栏 Terminal | 该 pane 的实时终端 | `terminal session observe` / `agent attach` |
| 右栏 Explorer、Browser | 后续再做 | — |

对受管 worker 的输入属于人工介入。AGENTS.md 要求运行记录保留人工介入，而 `coop.py` 目前没有追加这类事件的命令。这是写 spec 时要补的缺口。

## 视觉方向

一句话描述：像一本值班台账，浅灰纸面上的黑色正文，只有 agent 状态和门禁结论带颜色。

记忆点是状态色。Herdr 的 working、blocked、idle、done 和 a2a 的 submitted、verified、accepted、oracle_failed 是界面上仅有的彩色元素，其他部分保持灰阶。

借鉴截图：

- 左栏两行条目：第一行是标题，第二行是项目、分支、编号等元数据；选中只用浅底色，不给每一条加卡片。
- 顶部标签栏、窄图标栏、细分隔线，系统无衬线字体加等宽字体。
- 中栏用连续的阅读排版，长时间运行的段落可以折叠（截图中的 "Worked for …"）。
- 改动文件卡显示增删行数，点开看 diff。
- 右栏用标签切换 Terminal、Explorer、Browser。

不借鉴：

- Synara 的 agent 执行方式（provider 原生会话）。
- "Want to turn on auto-fix" 这类推广横幅。
- 把模型自述和程序核验结果排成同一种样式。截图里的 "46 relevant tests pass" 是模型自述；在 a2a 中，核验结果要带 task、attempt、G/C/M 和 oracle 来源，模型自述要标明出处，两者一眼可分。

## Enchanted 并入

- 时机：形态 b 的会话投影需要解析器时，再从 Enchanted 抽出 Codex adapter 和 replay 相关代码；不提前重构整个 core。只保留一套 provider 解析器，Enchanted 的 AGENTS.md 也禁止复制第二套。
- 顺序：实时会话投影 → 历史会话回放（复用同一个渲染组件）→ Evidence → Improve 建议。用量和额度放在最后。
- 风险：
  - 没有版本控制。建议搁置前 `git init` 并提交一次快照，上游子目录和 `plans/` 是否纳入需要你决定；否则搁置期间的改动和误删都无法追溯。
  - core 耦合 Tauri（`commands`、`state`、`events`、`scheduler`、`platform`、`window_state`、`lib`）。抽取时只拆客户端实际调用的部分。
  - 术语冲突："session"在 a2a 是受管运行身份 `session_id`，在 Herdr 是服务端会话（`--session`），在 Codex 是原生会话，在 Enchanted 是解析后的会话记录；截图里还有 "thread"。写代码前先在 CONTEXT.md 定名。

## 方向门

- **REALITY GATE**：INCOMPLETE
- **GOAL**：为 a2a 选定图形客户端的技术底座和产品形态，并为日后并入 Enchanted 留出接缝。
- **NON-GOALS**：本轮不实现、不迁移 Enchanted、不修改 Herdr、不改变 `coop.py` 的门禁语义、不重启你正在使用的 Herdr server。
- **DECISION**：是否基于 Zed 二次开发（已判 NO_GO）；采用哪条路线和哪种产品形态（待 D0～D2）。
- **OBSERVED**：Zed 各 crate 的许可、构建要求、Parallel Agents 的线程模型；gpui-kit 0.7.1 的许可、GPUI 快照锁定和安装要求；Herdr 的公开 API、终端观察与直连、`agent_session`、endpoint 协议；Synara、muxel、agentZ 的许可和依赖。
- **MEASURED**：本机磁盘、工具链和系统版本；各代码库的行数或字节数。
- **INFERRED**：fork Zed 需要改写其终端和线程后端；GPUI 版本漂移会拖慢 AI worker；形态 b 可行。
- **UNKNOWN**：公开终端接口的保真度、延迟和所有权冲突（P1）；本机中文输入与复制（P2）；构建占用和你的预算（P3）；会话记录实时投影的完整性（P4）。

| 探针 | 输入与方法 | 通过 | 失败或停止 | 证据位置 |
| --- | --- | --- | --- | --- |
| P1 公开接口终端桥 | 在独立命名会话（`herdr --session a2a-gui-probe`）中开一个 shell pane 和一个 Codex pane，不碰你正在用的 server。无界面的 Rust 测试程序读取 `terminal session observe` 的帧，经 `alacritty_terminal` 还原网格，在静止时与 `herdr pane read` 比对；场景包括中英混排、宽字符、颜色、alt screen 和快速滚动输出。另在 PTY 中运行 `herdr agent attach`，写入中文 UTF-8 文本和控制键。 | 各场景静止时文本一致，宽字符对齐，输入只到达一次，延迟满足你确认的阈值（建议 p95 ≤ 100 ms） | 帧缺失、宽字符错位，或 attach 与已连接的 Herdr 客户端争夺尺寸或输入：停止，转评估 endpoint 协议路线 | `evidence/<日期>-gui-probe-p1/` |
| P2 中文输入与复制 | 最小 gpui-kit 0.7.1 应用（多行 Input 和 Markdown TextView）。用系统拼音输入"会话复盘：证据引用"，连续组词、取消候选、删除、撤销、切换输入框；跨中文、代码和 emoji 选中后粘贴到"文本编辑"。期望文本预先写好。 | 实际文本与期望完全一致，候选窗位置正确 | 丢字、候选窗错位或选区乱序：记录版本后停止，回到路线比较 | 屏幕录制、操作步骤、期望与实际文本 |
| P3 构建占用 | 在新的独立 `CARGO_TARGET_DIR` 冷编译 P2 应用（另加 `alacritty_terminal`），使用 gpui-kit 推荐的依赖优化配置；记录峰值、结束占用、一次界面改动后的增量，以及 release `.app` 体积。 | 低于你给的预算（D3） | 超出预算：先试共享 target 并关闭依赖调试信息；仍超出则回到路线比较 | 精确命令、环境、`du` 输出 |
| P4 会话实时投影 | 在探针会话中启动 Codex（`herdr agent start` 或 `coop.py dispatch`），从 `agent.get` 取会话 ID 并找到会话文件；agent 工作时增量读取 JSONL，用 Enchanted 现有的 Codex 解析逻辑还原消息与工具调用（只读引用，不改 Enchanted）。 | TUI 中出现的每条用户消息、助手消息和工具调用都出现在投影中，回合结束时无遗漏，延迟满足阈值 | 缺事件、映射错误或无法增量解析：形态 b 降为 a，或评估 c | 会话 ID、Codex 版本、逐条比对表 |

- **DECISION CONSEQUENCE**：P1～P3 通过且你选择 B，即可写 spec；P1 不通过时先评估 endpoint 协议路线（复制类型或 fork Herdr 抽出协议 crate），这一步属于内核修改决策，要再问你；P2 或 P3 不通过时，重新比较 B 与 D。
- **NEXT ACTION / OWNER**：你决定 D0～D6；之后由主控把决定和探针写进项目地图，再分派 worker 执行探针。

## 需要你决定的事

| 编号 | 问题 | 建议 | 依据 |
| --- | --- | --- | --- |
| D0 | 是否把"a2a 图形客户端"作为新目的地写入 intent 和项目地图 | 是，作为第二阶段目的地；首轮的协作运行层保持不变 | 你本次的要求；AGENTS.md 停止边界 |
| D1 | 产品形态 a、b、c | b（混合） | T-001 保留 Herdr 与 CLI；Herdr 已提供会话映射 |
| D2 | 技术底座 | B：独立 GPUI，锁定 gpui-kit 0.7.1；不采用 A | 本记录"路线比较" |
| D3 | 开发期构建占用的上限 | 需要你给出数字；本机约 21 GiB 可用 | measured |
| D4 | 是否允许引入 GPL 代码（muxel 或 Zed 的终端元素），省去自写终端绘制 | 不引入，自写终端绘制元素；GPL 代码只读参考 | 保留日后分发的选择；P1 之后再评估工作量 |
| D5 | Enchanted 如何搁置 | 先纳入 git 做快照，再冻结；按"Enchanted 并入"一节的顺序迁移 | 没有版本控制（measured） |
| D6 | 术语 | 写代码前在 CONTEXT.md 定下"会话""线程"等名称 | ubiquitous language；AGENTS.md 术语规则 |

## 确认后的下一步（尚未执行）

1. 更新 intent 和地图目的地；为 D1～D4 建决策 ticket，为 P1～P4 建研究 ticket，并用 `blocked_by` 连接到对应决策。
2. P1～P4 通过后写 spec，再切第一颗 tracer bullet：GPUI 窗口左栏列出探针会话里的 agent 及其 Herdr 状态 → 选中一个由 `coop.py run` 启动的 worker → 右栏实时显示它的终端并能输入中文 → 顶部状态条按 `coop.py status` 显示 submitted、verified、accepted。验收走真实入口：对分页夹具跑一次 `coop.py run`，界面依次显示状态变化；产物是截图序列、事件日志和复现命令。状态到视图的逻辑用 GPUI 的无头测试检查，外观由你判断。
3. 第二颗：中栏会话投影和输入框（输入记为人工介入事件）。第三颗：只调用 CLI 的 verify、integrate、reclaim 操作，以及候选 diff。之后再并入 Enchanted 的历史回放。

## 来源（2026-10-06 核验）

- Zed 许可总览：<https://zed.dev/software-overview>；各 crate 的 `license` 字段：GitHub `zed-industries/zed` 的 `crates/*/Cargo.toml`
- Zed macOS 构建要求：<https://github.com/zed-industries/zed/blob/main/docs/src/development/macos.md>
- Zed Parallel Agents 与 agent 类型：<https://zed.dev/docs/ai/parallel-agents>、<https://zed.dev/docs/ai/agents>
- Zed 仓库数据：GitHub API（`crates/` 下 249 项；languages 接口中 Rust 为 62,166,716 字节，Herdr 为 11,376,381 字节）
- `gpui` crate：<https://crates.io/crates/gpui>（0.2.2，2025-10-22，Apache-2.0）
- gpui-kit：<https://crates.io/crates/gpui-kit>（0.7.1，2026-10-05，Apache-2.0）；<https://github.com/longbridge/gpui-kit/blob/v0.7.1/Cargo.toml>（`gpui-pre =0.3.8`、`runtime_shaders`）；<https://gpui-kit.com/docs/installation/>（Command Line Tools、macOS 15+、Rust 1.92+）
- muxel：<https://github.com/ProjectHax/muxel>（GPL-3.0-only；`Cargo.toml`、`crates/muxel-terminal/Cargo.toml`、README）
- agentZ：<https://github.com/ahrorbeksoft/agentZ>（`Cargo.toml`、`LICENSE-APACHE`、`LICENSE-GPL`）
- Synara：<https://github.com/Emanuele-web04/synara>（MIT）
- Herdr：`herdrdev/herdr@c4653a4` 中的 `docs/next/website/src/content/docs/socket-api.mdx`、`persistence-remote.mdx`，`docs/next/api/herdr-api.schema.json`，`src/protocol/wire.rs`、`src/protocol/endpoint.rs`；本机 `~/.codex/herdr-agent-state.sh`（integration v8）
- 本机测量命令：`df -h /`、`rustc --version`、`xcode-select -p`、`sw_vers`、`wc -l`、`du -sh`
