---
session_id: grilling-a2a-gui-client-20261006
status: confirmed
topic: a2a-gui-client
destination_artifact: intent.md
created_at: 2026-10-06T10:21:42-04:00
updated_at: 2026-10-06T11:03:23-04:00
last_round: 4
---

## Destination

接受一份修订后的 `intent.md`（Plan / intent 阶段），把"a2a 图形客户端"写成第二阶段目的地，并在交接时同步项目地图。首轮协作运行层的验收结果作为既有事实保留。

> 目的地（D0）："D0：确定。"——针对评估中的提议"把'a2a 图形客户端'作为新目的地写入 intent 和项目地图"。
>
> 本次起点："目前想给这个 herdr 做个 gpui，在 Zed 上二开是不是一个好的选择？然后前端样式我想设计成这种的，前端框架需要重构，先做这个 a2a 的，然后 enchanted 那边先搁置，打算把 enchanted 的功能做到现在这个 a2a 的客户端里"
>
> 产品形态（D1）："就做成本身还是依赖于各个 agent 的 cli 的，但是给他们做一个类似 herdr 的这种，但不要 herdr cli,构建一个 gpui,然后要有 herdr 这样的，每个项目是一个窗口，这个项目窗口里又可以给不同的任务再加各个窗口，然后每个任务的窗口里有各个 pane，用于不同 agent 分工。"
>
> 界面（D10）："主要就是想要一个现代化的界面，像 codex、synara 这样，不要像是 enchanted 那样老气横秋的，看着还跟浏览器一样，初版也做像 synara 这样的果冻，可以选择不同色彩集作为强调色。"

## Out of scope

- 实现、原型编译、探针执行、仓库改造和发布 | reason: grilling 只做决定并交接。
- 基于 Zed 二次开发 | reason: 评估判为 NO_GO（许可、构建条件、体量、线程模型冲突），见 [评估记录](../findings/gui-client-assessment-2026-10-06.zh-CN.md)；用户把底座交给 agent 挑选后选定方案 A，并在漂移检查中确认。
- M1 不含：对话视图、Enchanted 其他功能、远程机器（SSH）、插件、Windows 与 Linux、元素级背景模糊、从上游同步检测清单与修复 | reason: D12 接受的 M1 范围；D14 "以后再单独同步"。这些属于以后的阶段，不是本 intent 里的待定事项。

## Confirmed constraints

- C1 | state: confirmed | source: D1, user | agent 仍以各自的 CLI 运行在终端 pane 中，不改用 provider 原生协议驱动。
- C2 | state: confirmed | source: D1, user | 不使用 Herdr CLI；用户界面是自建的 GPUI 应用。
- C3 | state: confirmed | source: D1, user | 层级：每个项目一个窗口；项目窗口内按任务再分"窗口"；任务窗口内有多个 pane，供不同 agent 分工。
- C4 | state: confirmed | source: D2, user | 至少支持 Herdr 支持的全部 CLI；可以参考 Herdr 的实现。
- C5 | state: confirmed | source: D3, user | a2a 与 Enchanted 的构建缓存默认放在外置硬盘；用户接受机械硬盘较慢。
- C6 | state: confirmed | source: D4, user | 能复用代码就复用，但不能因此改变方向；多 CLI 支持这类关键代码优先参考他人设计，Synara 开源可参考。
- C7 | state: confirmed | source: 首条消息, user | 界面风格参考 Synara 截图。
- C8 | state: confirmed | source: 首条消息与 D0, user | 先做 a2a 客户端；Enchanted 搁置，功能日后并入这个客户端。
- C9 | state: confirmed | source: round 2 answers, user"允许" | 外置硬盘未挂载时构建直接报错，不回退到内置盘。
- C10 | state: confirmed | source: D10, user | 现代界面，参照 Codex 与 Synara，不要浏览器式的旧界面；初版就要有 Synara 式"果冻"玻璃质感；强调色可从多套配色中选择。
- C11 | state: confirmed | source: D11, user | 永不闭源；自用并会开源；允许直接复用 GPL 代码。
- C12 | state: confirmed | source: D7 与 R5 推导，漂移检查确认 | 新引擎使用独立命名空间（可执行文件名、环境变量、socket 目录、集成 hook），与已安装的 Herdr 并存到切换完成。
- C13 | state: confirmed | source: C11 的推论，漂移检查确认 | 若并入 GPL 代码，开源许可证必须为 GPL-3.0；Herdr 的 Apache-2.0 代码可以并入。
- C14 | state: confirmed | source: D14 与 F10 推导，漂移检查确认 | fork 中不自动从 herdr.dev 拉取在线检测清单；清单与上游修复以后单独同步。
- C15 | state: confirmed | source: D16 | 门禁优先：界面上对受管任务的验收、集成、回收只调用 `coop.py` 同一入口；在受管 worker pane 里直接输入记为人工介入。
- C16 | state: confirmed | source: D12 | M1 只面向 macOS。

## Decisions so far

- D0 | state: confirmed | type: decide | origin: recommended | source: 评估 D0 → 用户"确定" | 把 a2a 图形客户端写成第二阶段目的地，写入 intent 与项目地图。 | assumes: 首轮协作运行层保留为既有成果。
- D1 | state: confirmed | type: decide | origin: user | source: round 1 answers | 自建类 Herdr 的 GPUI 应用，agent 仍为各自 CLI，见 C1～C3。 | rejected: 评估路线 B（GPUI 作为已安装 Herdr 的客户端）与形态 b（对话投影为主）。
- D2 | state: confirmed | type: compare | origin: delegated | source: round 1 answers | 技术底座交给 agent 挑选，约束见 C2、C4、C6；结果见 D8。
- D3 | state: confirmed | type: decide | origin: user | source: round 1 answers | 构建缓存默认放外置硬盘，见 C5、C9；具体机制留给 spec。
- D4 | state: confirmed | type: decide | origin: user | source: round 1 answers | 复用原则见 C6；GPL 结论见 D11。
- D5 | state: confirmed | type: decide | origin: recommended | source: round 1 answers | Enchanted 先纳入 git 做快照，再冻结；在交接后执行。 | assumes: 快照范围（上游子目录、`plans/`）在执行前由用户确认。
- D6 | state: confirmed | type: decide | origin: delegated | source: round 1 answers | 命名交给 agent 提议；结果见 D9。
- D7 | state: confirmed | type: decide | origin: recommended | source: round 2 answers（Q7"取代"） | 新应用取代 Herdr 成为 a2a 运行时；`coop.py` 保留门禁，只替换 F2 的 9 个 Herdr 命令；新运行时通过同样的验收后删除 Herdr 路径；旧 intent 中"保留 Herdr"被取代。 | basis: C2 | assumes: 门禁语义与运行时无关。
- D8 | state: confirmed | type: compare | origin: recommended | source: round 2 answers（Q8"A"） | 以 Herdr 的 Apache-2.0 引擎为底座、换上 GPUI 界面。 | assumes: "不要 herdr cli"允许并入 Herdr 引擎代码。 | rejected: B fork muxel（GPL、依赖 tmux、约 10 个预设、无 agent 控制接口）；C 从头新建（基本重写 Herdr）。
- D9 | state: confirmed | type: decide | origin: recommended | source: round 2 answers（Q9"很好"） | 项目=一个 OS 窗口，对应一个仓库目录；任务=项目窗口里的标签页（以后可弹出成独立窗口），就是 a2a 的 Task，验收合同可选；Pane=任务里的终端区域；角色沿用 CONTEXT.md；"原生会话"专指 CLI 自己的会话记录，不单用"会话""session"，不用"线程"。 | 写入 CONTEXT.md 的时机：交接时与 intent、AGENTS.md、地图一起改，避免中途让 living doc 互相矛盾。
- D10 | state: confirmed | type: decide | origin: user | source: round 2 answers（Q10"a"并补充原因） | 只借截图的外观与导航，任务页主体是终端 pane；对话视图随 Enchanted 并入再做；界面要求见 C10。
- D11 | state: confirmed | type: decide | origin: user | source: round 2 answers（Q11） | 永不闭源，自用并开源，允许直接复用 GPL 代码，见 C11。 | rejected: agent 推荐的"只复用 Apache/MIT 代码"。
- D12 | state: confirmed | type: decide | origin: recommended | source: round 3 answers（Q12"按上面这版"） | M1 = 新应用接替 Herdr 承担 a2a 日常工作：引擎后台持久与恢复；项目窗口、任务页、pane 与四种状态；Codex、Claude Code 端到端实测，已装 CLI 冒烟、未装 CLI 标未验证；`coop.py` 改用新控制接口，三套验收与一次真实 `run` 通过后删除 Herdr 路径；Codex/Synara 式外观、窗口级玻璃、可选强调色、中文输入与复制。 | basis: D7、D8、C3、C4、C10 | assumes: 未安装的 CLI 只沿用检测清单、标为未验证即可。
- D14 | state: confirmed | type: decide | origin: recommended | source: round 3 answers（Q14"B，以后再单独同步"） | 硬分叉，从 Herdr 0.9.3（`c4653a4`）自主演进；检测清单与上游修复以后单独同步。 | basis: D7、C2、F10 | assumes: 新 CLI 支持主要来自检测清单，硬分叉不妨碍 C4。
- D16 | state: confirmed | type: decide | origin: recommended | source: round 3 answers（Q16"a"） | 门禁优先，见 C15。 | basis: 首轮核心目标、旧 C5、AGENTS.md 操作锁规则。

## Facts

- F1 | state: observed | source: herdrdev/herdr@c4653a4 `docs/.../agents.mdx`，2026-10-06 | Herdr 列出 23 个自身支持的 agent（Claude Code、Codex、Copilot CLI、Cursor Agent CLI、OpenCode、Pi、OMP、Droid、Devin CLI、Kimi、Kilo、Hermes、Qoder、Qwen、Letta、MastraCode、Grok、Antigravity、Amp、Kiro、Maki、Gemini CLI、Cline）和 5 个自报状态的 agent。识别方式：找到 pane 中的 agent 进程，按检测清单读屏得到 idle/working/blocked；集成 hook 负责会话恢复和状态上报。
- F2 | state: observed | source: `coop.py`，2026-10-06 | a2a 运行时依赖 9 个 Herdr 命令：`pane list`、`pane process-info`、`pane split`、`pane close`、`agent get`、`agent read`、`agent list`、`agent start`、`agent prompt`。
- F3 | state: measured | source: `diskutil info`、`df -h`，2026-10-06 | 外置盘 `/Volumes/WD-Elements`：APFS、USB、931 GiB，约 839 GiB 可用；内置盘约 23 GiB 可用。
- F4 | state: observed | source: herdr `crates/ghostty-vt/build.rs`、`rust-toolchain.toml`；`which zig` | Herdr 引擎编译 libghostty-vt 需要 Zig，本机未安装 Zig；Herdr 锁定 Rust 1.96.1，本机已有。
- F5 | state: observed | source: herdr 文档与 `src/protocol/*` | Herdr 为 Apache-2.0；服务端持有终端，客户端断开后 agent 继续运行；为客户端自绘界面提供 endpoint generation 1 协议（快照、单元格画面、语义输入）。
- F6 | state: inferred | source: herdr `src/server/headless/client_views.rs` | 服务端按客户端区分聚焦的标签页，多个窗口各看不同项目可能可行；需在 spec 阶段核实。
- F7 | state: observed | source: ProjectHax/muxel `Cargo.toml`、`FEATURES.md`，2026-10-06 | muxel：GPL-3.0-only；gpui + gpui-component + alacritty_terminal；pane 跑在 tmux 会话里以便重启后保留；内置约 10 个预设，另支持 Codex 会话恢复；本机未安装 tmux。
- F8 | state: observed | source: Emanuele-web04/synara | Synara：MIT；Electron + React + TypeScript；通过各家原生接口接入 Codex、Claude Code、Cursor、Antigravity、Grok、Droid、OpenCode、Pi、Devin。
- F9 | state: observed | source: [评估记录](../findings/gui-client-assessment-2026-10-06.zh-CN.md) | gpui-kit 0.7.1 为 Apache-2.0，只需 Command Line Tools；Zed 二开判 NO_GO 的依据。
- F10 | state: observed | source: herdr `src/detect/manifests/`、`src/detect/manifest_update.rs` | 检测清单是 22 个 TOML 数据文件；Herdr 还会从 `https://herdr.dev/agent-detection/index.toml` 拉取远程清单目录（可用环境变量改地址）。
- F11 | state: observed | source: zed-industries/zed `crates/gpui/src/platform.rs`、`crates/gpui_macos/src/window.rs`，2026-10-06 | GPUI 的窗口背景有 Opaque、Transparent、Blurred（以及 Windows 的 Mica）；macOS 的 Blurred 在内容下方放一个系统 NSVisualEffectView，模糊强度由系统材质决定。未找到元素级背景模糊的实现。
- F12 | state: observed | source: synara `apps/desktop/src/windowMaterial.ts`、`CHANGELOG.md`、`customization.mdx` | Synara 的玻璃质感：整窗或仅侧栏半透明，模糊度与透明度可调（可调模糊用私有接口的原生插件，失败时退回系统 vibrancy）；有主题颜色编辑器，选中行带强调色。

## Frontier

- 无。Q13 因方案 A 继承检测清单而取消。

## Blocked

- 无。

## Not yet specified

- 无。原有雾区已分两类处理：属于 spec 的问题列入交接；属于以后阶段的事项列入 Out of scope。

## Risks and conflicts

- R1 | state: resolved | owner: user | affects: D1, C2, D7 | 原冲突：D1"不要 herdr cli"与已接受 intent、旧 ledger C6/D7/D15 及 `coop.py` 的 Herdr 调用。用户选择取代（D7）与方案 A（D8），旧 intent 中"保留 Herdr"将在新 intent 中标为被取代。
- R2 | state: resolved | owner: user | affects: C3, C7, D10 | 原张力：终端 pane 为主与截图对话为主。用户选择只借外观与导航（D10）。
- R3 | state: accepted | owner: user | affects: C5 | 机械硬盘使构建变慢；多个 worker 并发编译的争用留给 spec。
- R4 | state: resolved | owner: user | affects: D5 | Enchanted 已建 git 仓库并提交快照 `3e2ad91`，冻结说明 `b0094c4`；详见 T-021。
- R5 | state: open | owner: spec session（T-018 的切换条件） | affects: D7, Q12 | T-006～T-008 的验收证据只对 Herdr 运行时成立，切换后要在新运行时上重跑同样的验收。
- R6 | state: accepted | owner: user | affects: D8, D14 | Herdr 引擎 fork（约 27.6 万行）选择硬分叉：改动自由，但上游的大改动不会自动进来；修复与检测清单以后单独同步。
- R8 | state: open | owner: T-024 | affects: C3, D12 | 多个窗口各看不同项目依赖服务端按客户端区分聚焦（F6，inferred），spec 阶段核实。
- R9 | state: open | owner: T-026 | affects: D8, C5 | 引擎编译需要 Zig（F4），本机未安装；工具链与缓存位置在 spec 中按 C5、C9 处理。
- R7 | state: open | owner: T-025 | affects: C10 | GPUI 只有窗口级玻璃，模糊强度可调需要私有 macOS 接口，元素级背景模糊未实现（F11、F12）。

## Handoff

已确认（用户："都很不错，符合我的想法，做之后的事，然后更新 Git，如果没仓库的话，也帮我创建一个。"）。

- canonical artifact：根目录 [`intent.md`](../intent.md)（2026-10-06 accepted）。草案已并入，草案文件删除。产品称呼统一为"工作台"，含义不变。
- 术语：[`CONTEXT.md`](../CONTEXT.md) 新增工作台、引擎、项目、Pane、原生会话，更新 Task 与 Herdr。
- 治理：[`AGENTS.md`](../AGENTS.md) 增加"第二阶段：工作台约束"；项目地图的目的地改为第二阶段。
- 决策 ticket：T-016～T-021 已关闭；交给下一步的 ticket：T-022 代码位置与名称、T-023 主控层级、T-024 多窗口焦点、T-025 中文输入与玻璃质感（依赖 T-026）、T-026 外置盘构建缓存。
- Enchanted：已建 git 仓库并冻结，见 T-021。
- 限制：F6 仍为推断，由 T-024 核实；元素级背景模糊与上游同步不在 M1。

下一步：按 project-map 流程关闭 T-022～T-026，再写工作台 spec、切 tracer-bullet build ticket。本 ledger 不记录实现进度。

## Changelog

- Round 0: 只读评估，见 [评估记录](../findings/gui-client-assessment-2026-10-06.zh-CN.md)，提出 D0～D6。
- Round 1: 用户回答 D0～D6。D1 否决"Herdr 客户端"路线，改为自建类 Herdr 的 GPUI 应用；D2、D6 交由 agent 提议。核实 F1～F9 后提出 Q7～Q11；Q12、Q13 等待 Q7、Q8。
- Round 2: 用户选择 Q7 取代、Q8 方案 A、Q9 按提议命名、Q10 (a) 并补充界面要求、Q11 开源且允许 GPL，确认 C9。核实 F10～F12。Q13 因方案 A 继承检测清单而取消。提出 Q12、Q14、Q16；C12、C13 待漂移检查确认。D9 的术语推迟到交接时写入 CONTEXT.md。
- Round 3: 用户接受 Q12（M1 范围）、Q14（硬分叉，以后单独同步）、Q16（门禁优先）。frontier 清空；雾区分别转入交接和 Out of scope。新增推断 C14。起草 intent 草案并做漂移检查，等待用户确认。
- Round 4: 用户确认漂移检查与 intent 草案，C12～C14 一并确认。写入 intent、CONTEXT、AGENTS、项目地图与 T-016～T-026；Enchanted 建库并冻结；ledger 标为 confirmed。
