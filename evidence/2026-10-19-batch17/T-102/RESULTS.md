# T-102 / a1 打包前置核对

状态：**BLOCKED**。2026-10-19；未实现产品变更，未产出或安装 `.app`。

## 绑定与范围

- task / attempt：T-102 / a1；ticket ready_rev：1。
- 代码起点：`803e6cf69abbd7727c3694a446a52eb5940ddf2e`；分支：`exec/t102`。
- worker：`s17-t102`；session：`b39683a9-f281-4941-aa23-d4479d9a917d`；原生会话：`01a15278-4b82-7963-8301-50cf9e0de9cd`。
- launch：`launch-60574dbe21504c0594fc02ef9a2475e3`；Herdr pane：`wF:p6Y`。本次派发未提供门禁 fence、状态目录或结构化任务卡；未猜测这些字段。
- 用户授权引用：2026-10-19 派发消息逐字引用用户“打包吧,打完包我在体验”，并要求安装到 `/Applications`。
- 目标：按 **Tracer bullet** 打通双击 → 编排后台 → 界面 → 选择项目/任务 → 打开可用 zsh 窗格，再验证关界面后后台保持运行。
- 非目标：新增项目/任务领域设计、扩展门禁语义、调用模型、自动更新、公证、安装器、跨平台。
- 验收条件：本票 Acceptance 的真实打包入口、红态/绿态、反例、截图、体积、命令、签名与地图检查全部有证据。

## REALITY GATE: BLOCKED

本轮决策是现有功能能否仅补打包与启动层。源码核对发现项目/任务选择与普通 shell 窗格缺少生产通路；派发第 4 条及 ticket 第 5 项明确要求遇到此类缺口停止上报，因此停止产品实现。

| 缺口 | observed：源码位置 | inferred：为什么超出打包层 | 最小选项，待主控裁定 |
| --- | --- | --- | --- |
| 项目/任务选择 | `workbench/app/renderer.tsx:211` 的 Workbench 只从固定 paneKeys 取得快照，`:228`～`:230` 仅显示当前项目和任务；`workbench/app/preload.ts:9` 无列举或切换项目/任务的 IPC；`workbench/src/gates/cli.ts:15` 命令表无项目/任务列表入口，`workbench/src/gates/core.ts:3188` 在分支前要求具体 task，`:3191` 的 status 只返回一项 | 需要确定项目来源、任务枚举、空数据时的入口、切换窗口绑定等跨 UI/IPC/后台行为；不能把静态侧栏改成可点就宣称具备选择能力 | A：先单独补齐选择现有项目/任务的最小切片，再继续打包；B：用户明确收窄为预先配置单个任务的本机包装应用 |
| 不调用模型的 zsh 窗格 | `workbench/app/main.ts:27` 仅接受主控或当前 worker 的 launch；`workbench/src/panes.ts:116` 启动 Claude 主控；`:383` 起的 worker/reviewer 通路在 `:405` 要求 Codex 配置，`:430` 构造 Codex argv，`:451` 再用 zsh 执行；renderer 只有进入/关闭已有窗格，没有新建入口 | 现有 node-pty 能启动 zsh，但产品没有普通 shell 的 launch 类型、创建命令、身份绑定与输入路径。以启动模型再退回 shell 替代验证会违反本次“不调用模型”的约束 | A：另立普通 shell 窗格切片，明确会话与输入记录语义；B：由用户改变本票 tracer 的窗格条件。worker 不选设计 |
| GUI 不会自启后台 | `workbench/app/start.mjs:9` 要求 build/task 后只启动 Electron；`workbench/app/main.ts:159` 先校验 task，再直接查询后台；`workbench/src/transport.ts:73` 已有 detached 后台启动器，GUI 未调用它；`workbench/src/credentials.ts:6` 仍要求绝对凭据路径 | detached 与常驻基础已有，GUI 接线可能较薄，但要先确定打包后台的运行时、入口文件和凭据持有方式；它不是本轮最先触发的停止原因 | 在前两项裁定后沿用现有启动器；不另造门禁入口 |

**Deep modules**：保留现有 transport/daemon 的职责边界；不为打包增加第二套门禁或浅包装 API。**Ubiquitous language**：全文沿用项目、任务、窗格、编排后台、launch 与 attempt 的既有含义。

## 红态、反例与复现

运行：

```sh
python3 evidence/2026-10-19-batch17/T-102/PROBE-BASELINE.py /绝对路径/尚不存在的结果.json
```

本次产物为 `baseline-01.json`；按原样保留 argv、退出码及 stdout/stderr。探针只做本地只读检查，构建反例在挂载检查处终止；没有启动 Electron、后台或模型，没有装依赖或写外置盘。

| 检查 | 独立预期 | 实际证据 | 结论 |
| --- | --- | --- | --- |
| 当前无已安装应用 | 本票红态要求确认无 `/Applications/a2a.app` | `installed_app.exists = false` | 已取得要求的应用缺失红态；不代表 GUI 实测 |
| 缺 `--task` | 本票要求后续能进入选择页；当前应暴露尚未实现 | `node workbench/app/start.mjs --build …` 退出 1，错误为 `--build DIST --task ID are required`；发生在读 build.json 与加载 Electron 之前 | 已取得当前真实开发入口的合同红态；打包入口尚不存在 |
| 普通目录不能伪装外置盘 | 构建必须拒绝未挂载目录且不创建输出 | 将 `A2A_BUILD_VOLUME` 指向当前 checkout，退出 1，错误为“构建要求真实挂载的外置盘；不回退到内置盘。” | 当前构建挂载守卫反例通过；没有物理卸载用户外置盘，也没有验证将来的打包命令 |
| 地图检查 | ticket 要求 status 0 问题 | 当前稀疏 worktree：退出 1、8 个问题、0 stale；见 JSON 与结束检查 | INCOMPLETE；缺失的 findings/ 与 `.grilling/a2a-gui-client.md` 不在稀疏检出范围。不改地图或扩展本票范围掩盖此结果 |

以上预期来自派发、ticket 和构建约束；未依据实现输出编写绿态答案。缺口核对为源码证据，未冒称真实 GUI 反例。没有产品修复候选，未做已知坏候选/修复候选对照。

## 依赖与文档预查（2026-10-19）

`workbench/package.json` 已有 Electron 43.4.1、node-pty 1.1.0、Vite 8.1.5、React 19.2.4、xterm 6.0.0；只有 preinstall/build/start 脚本，没有 main、打包配置或 packager/builder 依赖。Node engine 为 `>=26.5.0 <27`，本机探针为 Node 26.5.0。

- [Electron 43.4.1 官方版本记录](https://releases.electronjs.org/release/v43.4.1)：内含 Node 24.18.1。它与现有后台要求的 Node 26.5 不同；不能未经验证便把后台直接换到 Electron runtime。
- [Electron 官方原生模块说明](https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules)：原生模块须针对 Electron ABI 重建，官方给出 `@electron/rebuild`。本轮未重建 node-pty。
- [@electron/packager 官方 API](https://packages.electronjs.org/packager/v19.0.1/functions/packager.html)：职责是生成应用目录并定制 Electron 可执行文件。
- [electron-builder 官方说明](https://www.electron.build/docs/)：覆盖打包、原生依赖构建、安装器、签名与更新；该网页当前标注 next/v27，不能直接当作 stable 配置依据。

据任务只要本机 `.app` 的范围，packager 的职责较接近所需；这是文档层的初步判断。因前置功能缺口触发停止，本轮未选定工具、版本或安装依赖；不把文档预查当成兼容性验证。

## 验收逐项状态

| ticket Acceptance | 状态 | 剩余证据 |
| --- | --- | --- |
| 红态无应用；绿态双击、zsh、退出界面后台仍在 | INCOMPLETE | 只有红态；缺产品通路、打包产物与全部绿态 |
| 打包产物开项目、开任务、开窗格、关界面再开 | BLOCKED | 先裁定项目/任务选择与 shell 窗格缺口；无截图、无真实 `.app` 启动命令 |
| 缺外置盘构建报错；缺 task 不崩溃 | INCOMPLETE | 现有构建守卫拒绝普通目录；缺 task 当前仍退出；尚无打包反例 |
| 体积、构建命令、签名、限制 | INCOMPLETE | 无产物，因此体积与构建命令未知；ad-hoc 只是用户允许的目标方式，尚未签名 |
| project_map status 0 问题 | INCOMPLETE | 稀疏 worktree 8 个缺失项、0 stale，未改治理文件 |

已知限制就是上述生产缺口；尚不能让用户双击体验。本轮无任何可靠性、性能或成本改善主张，也无独立验收或发布通过结论。

## 另行报告与交接

真实启动记录的 `service_tier_requested` 和 argv 都是 `fast`，与当前 AGENTS“普通速度／不用 Fast”不符；配置记录不证明供应商实际 tier。该记录位于主仓库 `records/launches.jsonl` 的本 launch 条目。worker 未修改记录、重启会话或调用模型工具；请执行主控在下次启动时纠正配置，不把本轮记成 default。

只新增本目录的中文报告、小型探针与文本证据。未改产品、门禁、操作锁、用户全局配置、地图、术语表或 ticket；未用问题面板，未 push。

按派发第 6 条，Git 元数据与既有尾注钩子记录位于沙箱外，提交交给执行主控：

```sh
bash evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-01-COMMIT-REPORT.sh
```

该脚本只暂存列明的证据文件，要求干净暂存区和原起点，由现有 hook 追加尾注；不手写尾注，不覆盖历史，不 push。T-101 已改写历史时会停下，须先核对映射。脚本尚未由 worker 运行，提交号待主控回传。

本次是阻塞报告，不是满足完成条件的候选交付；未调用 submit，未伪造缺失的 fence/spec_rev。执行主控需先裁定最小选项并提供后续合同；不得据此验收、集成或将 ticket 记为 PASS。项目功能范围的裁定来自派发停止条件，不是 skill 自行增加的审批。
