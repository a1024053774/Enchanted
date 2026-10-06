# Spec：Muster 工作台 M1 与初步任务书（2026-10-06）

本 spec 是日期记录，承接 [intent.md](../../intent.md) 的 M1。之后的变更走新 ticket，不改写本文。

## 问题

当前的多 agent 分工依赖另外安装的 Herdr，以及它的终端界面和 CLI；a2a 的门禁也绑定在 Herdr 的 9 个命令上。用户要一个自有的现代 GPUI 工作台：每个项目一个窗口，按任务分页，在任务里给不同 agent 分 pane。Enchanted 现有的界面观感陈旧，它的功能以后并入这个工作台。

## 方案

Muster 由三部分组成：

- **引擎**：Herdr 0.9.3 的硬分叉，作为后台服务持有终端与 agent 进程。它沿用 Herdr 的检测清单、集成 hook、会话恢复和 socket API。
- **桌面应用 Muster.app**：GPUI 窗口，是引擎的客户端。每个项目一个窗口，窗口里有任务标签页和 pane 画面。
- **控制接口**：引擎的 `muster` CLI 与 socket API，供主控、worker 和 `coop.py` 使用。`coop.py` 的门禁不变，只改接 `muster`。

从用户这边看：打开 Muster.app → 进入项目窗口 → 新建任务 → 分出 pane → 启动 Codex 或 Claude Code → 在 pane、任务标签和侧栏上看到状态 → 关掉窗口后 agent 继续运行 → 重新打开时恢复原样。主控 agent 在任意 pane 里经 `muster` 派 worker；受管任务的验收、集成和回收只走 `coop.py`。

## 决策

- [T-016 第二阶段目的地与 M1](../tickets/T-016-phase2-destination.md)
- [T-017 工作台的技术底座](../tickets/T-017-workbench-base.md)
- [T-018 运行时切换与门禁优先](../tickets/T-018-runtime-switch-and-gates.md)
- [T-019 第二阶段术语](../tickets/T-019-phase2-terms.md)
- [T-020 构建缓存、开源许可与代码复用](../tickets/T-020-build-cache-license-reuse.md)
- [T-021 Enchanted 的搁置与并入](../tickets/T-021-enchanted-freeze.md)
- [T-022 工作台的代码位置与正式名称](../tickets/T-022-workbench-location-and-name.md)
- [T-023 主控放在项目级还是任务级](../tickets/T-023-controller-placement.md)

## 设计要点

### 代码位置

- `muster/engine/`：Herdr 源码的硬分叉，保持上游的目录结构，便于以后挑拣同步。同时记录来源：上游地址 `https://github.com/herdrdev/herdr`、提交 `c4653a4`，保留 Herdr 的 LICENSE，并加 NOTICE 说明派生关系。
- `muster/app/`：GPUI 桌面应用。
- 两者组成 `muster/` 下的 Cargo workspace。`coop.py`、`acceptance/` 和文档留在原处。

### 命名空间

| 项目 | Herdr | Muster |
| --- | --- | --- |
| CLI 可执行文件 | `herdr` | `muster` |
| 桌面应用 | — | `Muster.app` |
| 环境变量 | `HERDR_*`（源码中约 80 个） | `MUSTER_*` |
| socket 与日志 | `herdr.sock`、`herdr-server.log` | `muster.sock`、`muster-server.log` |
| 配置目录 | `~/.config/herdr` | `~/.config/muster` |
| 集成 hook | `herdr-agent-state.sh`，来源 `herdr:codex` 等 | `muster-agent-state.sh`，来源 `muster:codex` 等 |
| 插件清单 | `herdr-plugin.toml` | `muster-plugin.toml`（插件不在 M1） |

已安装的 Herdr 与 Muster 要能同时运行，互不读取对方的 socket、配置和 hook。界面文字和文档中不使用 Herdr 的名称和标志；Apache-2.0 不授予商标使用权。

### 网络

引擎去掉或关闭所有访问 herdr.dev 的功能：自更新、产品公告、发布说明、预览通道、在线检测清单。检测清单和上游修复以后单独同步。

### 引擎与应用的边界

应用只通过引擎的客户端协议与它交互，即 Herdr 的 endpoint generation 1：快照、单元格画面、语义输入、控制请求。应用不直接持有 PTY 或进程，关闭应用不影响引擎和 agent。引擎要为应用提供可复用的库接口：接口小，协议细节藏在里面。

### 控制接口与名词

`muster` 沿用 Herdr 的命令结构和 JSON 输出。`coop.py` 用到的 9 个命令（`pane list`、`pane process-info`、`pane split`、`pane close`、`agent get`、`agent read`、`agent list`、`agent start`、`agent prompt`）只把可执行文件从 `herdr` 换成 `muster`。

M1 前几张切片期间，引擎内部和控制接口暂时沿用 Herdr 的 workspace、tab 两个名词，分别对应术语表中的项目、任务；界面和文档一律用项目、任务。这是有意保留的两套叫法：原因是先控制 fork 的改动量；影响是 agent 和 `coop.py` 读到的字段仍是 workspace/tab；移除条件是后续切片按 expand → migrate → contract 的顺序完成改名。该项列在项目地图的 Not yet specified 中。

### 主控

主控是一个角色，不绑定层级：它可以在任意 pane 中运行，经控制接口按 ID 操作项目级对象（窗口、任务页）和任务级对象（pane、agent），做法与 Herdr 一致。门禁和停止边界按 AGENTS.md 执行。

### 界面

参照 Codex 和 Synara 的现代界面：窄侧栏、任务标签、pane 区；窗口级玻璃质感（GPUI 的 Blurred 窗口背景，整窗或仅侧栏半透明，透明度可调）；可从多套强调色中选择，状态色要与强调色区分开；中文输入与复制正常。第一颗 tracer bullet 不要求玻璃质感和强调色。

### 构建与工具链

构建输出和缓存全部放在 `/Volumes/WD-Elements`，外置盘未挂载时构建直接报错（T-026 落地）。工具链要求：

- Rust 1.96.1（Herdr 锁定的版本，本机已有）；
- Zig 0.16（依据 Herdr 的 `flake.nix`；用于编译 libghostty-vt，本机未安装）；
- gpui-kit 0.7.1（要求 Rust 1.92 及以上、macOS 15 及以上、Command Line Tools）。

## 验证接缝（待用户确认）

1. **引擎与 a2a**：在独立命名会话中运行真实的 `muster` CLI，作为程序可以核对的接缝。a2a 沿用三套验收和 live run 入口。
2. **桌面应用**：真实的 Muster.app 连接同一个引擎。终端内容与 `muster pane read` 比对；输入用系统输入法实测；状态到视图的逻辑用 GPUI 的无头测试检查；外观以截图和录屏交给用户判断。

所有探针和验收都不修改、不重启用户正在使用的 Herdr server。

## 初步任务书

| 顺序 | Ticket | 类型 | 依赖 | 交付 | 执行方式 |
| --- | --- | --- | --- | --- | --- |
| 1 | [T-026 把构建缓存与工具链放到外置盘](../tickets/T-026-external-build-cache.md) | task | — | 构建配置、缺盘报错、机械盘耗时与并发实测 | worker 实施，主控核对 |
| 2 | [T-024 多窗口各看不同项目](../tickets/T-024-per-window-project-focus.md) | research | — | 用已安装的 Herdr 0.9.3 开独立会话，得出双客户端焦点的结论 | worker 只读研究，可与 1 并行 |
| 3 | [T-025 GPUI 的中文输入、复制与玻璃质感](../tickets/T-025-gpui-cjk-glass-probe.md) | research | T-026 | 最小 gpui-kit 应用的实测记录与录屏 | worker 实施，观感由用户判断 |
| 4 | [T-027 Muster 引擎以独立命名空间运行](../tickets/T-027-muster-engine.md) | build | T-026 | 引擎可运行，并与已安装的 Herdr 并存 | worker 实施，独立 reviewer 验收 |
| 5 | [T-029 coop.py 改接 Muster](../tickets/T-029-coop-on-muster.md) | build | T-027 | 三套验收与一次真实 `run` 在 Muster 上通过 | worker 实施，独立 reviewer 验收 |
| 6 | [T-028 Muster.app 的第一颗 tracer bullet](../tickets/T-028-app-tracer-bullet.md) | build | T-027、T-025 | 一个项目窗口、任务页和实时 pane，可中文输入，关窗后 agent 继续运行 | worker 实施，外观由用户判断 |

执行规则沿用 AGENTS.md：
- 每个 worker session 只做一张 ticket。
- build ticket 先拿到端到端的红态，再实现，最后在绿态下保存证据。
- 独立 reviewer 和 monitor 都只读。

这批关闭后，先按本 spec 复核，再从项目地图的 Not yet specified 里切下一批。

## 不在范围

- M1 之外的工作，见 [intent.md](../../intent.md) 的范围一节。
- M1 中尚未切片的部分，列在项目地图的 Not yet specified 中，等这一批 ticket 关闭后再切。
