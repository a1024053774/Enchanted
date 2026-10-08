# T-042 恢复与合并后复验（2026-10-08）

**环境恢复 PASS；本次任务总体 INCOMPLETE。** 我在首轮构建准备中造成的源码与依赖损坏已处理：受控文件恢复到 `3566ef4`，依赖按锁文件重新安装，标准桌面构建、typecheck、lint 与 35 项门禁场景全部通过。真实 Electron 任务窗口显示 observer `healthy`。人工介入发送被关闭的 provider 拦截，未启用 provider，也未调用模型；受管事件与非受管发送反例仍未完成。

首轮是执行 agent 的操作错误，不是用户的责任，也不能归为产品回归。首次日志、4 项模块缺失失败、误删清单与恢复记录均保留在上级 verify 目录；没有用本轮绿态覆盖它们。

## 本轮结果

| 项目 | 结论 | 证据 |
| --- | --- | --- |
| 依赖恢复 | PASS | `install-result.json` / `install.log`，frozen lockfile 安装退出 0，1,635 packages，约 37 分钟；`dependencies-after-install.json` 中全部工作区声明的依赖 manifest 均可找到 |
| lint | PASS | `lint-result.json` / `lint.log`，退出 0；保留既有 warnings，没有 errors |
| 18 项编排 | PASS | `orchestration-result.json` / `orchestration-trace.json` / `orchestration.log`，18 项、0 失败、0 错误，78.662 秒；仍为隔离原生线程边界，不证明真实模型 |
| 17 项交付/恢复 | PASS | `delivery-result.json` / `delivery-trace.json` / `delivery.log`，17 项、0 失败、0 错误，99.769 秒 |
| typecheck | PASS | `typecheck-result.json` / `typecheck.log`，8/8 successful、0 cached，退出 0 |
| 标准桌面构建 | PASS | `build:desktop-result.json` / `build:desktop.log`，退出 0；保留 chunk-size 等构建警告 |
| membership HTTP | PASS | `desktop/membership-command.json` / `membership.jsonl`，原 T-038 主场景的 8 个真实请求通过；`cross-project-member.json`、`cross-project-gate.json` 分别返回预期 400 与错误码；`preflight.json` 的 4 项 OPTIONS 检查通过 |
| 真实 observer 桌面显示 | PASS | `desktop/02-observer-healthy.jpg` 与同名 txt，实际点击“任务窗口”后位于 `/#/a2a`；真实 GET 回读 `observer-before.json` 也是 healthy。03 截图中的受管 worker 内也显示 healthy |
| 受管消息与人工介入标记 | INCOMPLETE | 门禁 dispatch 创建了受管 worker；Computer Use 输入完整消息并点击发送，界面提示 provider disabled，消息仍为草稿。`desktop/03-managed-send-blocked.jpg` / 同名 txt；`managed-events-after-ui.json` 与 `events-cli.json` 均无 human_intervention |
| 非受管发送反例 | INCOMPLETE | 未执行。到达任务书规定的 provider-disabled 停止边界后，不继续发送实验；没有用“消息没发出去，所以没有事件”冒充反例通过 |
| 进程清理 | PASS | `desktop/cleanup.json`，本轮 Electron/Vite 进程组无残留，54877、5811、7771 无监听 |

## 恢复范围与候选绑定

产品 checkout 为 `/Users/luckye/Documents/Code/synara`，分支 `a2a`，完整提交 `3566ef4eb34b18c480c7a49e4b5d741681b72426`。最终 `final-product-status.txt` 仅原有 `.grok/` 未跟踪；源码、锁文件无差异。未接触 synara-t038 checkout，未 push，没有修改 MAP、ticket 或 AGENTS。

首轮误删的 6,186 个受控文件已按删除清单恢复；本轮将各工作区原 node_modules 完整移到外置盘 `t042-verify-recovery-01/damaged-dependencies`，移送起止记录见 `dependency-moves.jsonl`。随后执行 `./a2a/scripts/bun install --frozen-lockfile --backend=copyfile --no-progress`，依赖补丁与安装正常完成，没有修改版本或锁文件。原损坏树继续保留。本轮还移除了事故输出目录中由我引入、仍指向工作区的两个危险链接，见 `hazardous-links-removed.json`。

旧构建目录移存为 `generated-before-rebuild`，不在输出目录里放依赖链接；新构建使用产品的标准目录和 `./a2a/scripts/bun run build:desktop`。缓存、Electron 下载与临时目录均由指定 wrapper 路由到外置盘。安装、测试、typecheck、构建串行执行；完整 argv、cwd、环境、时间、退出码见各 command/result JSON。恢复依据是锁文件重装和实际运行验证，不声称逐字节还原所有此前未登记的忽略文件。

新隔离根目录是 `/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify-recovery-01`，HOME、XDG、CODEX_HOME、CLAUDE_CONFIG_DIR、desktop-home 与 profile 均在其中。没有复制用户 auth，也没有写用户 ~/.codex、Synara 或浏览器 profile；没有操作 Herdr。一次检查 Bun install 帮助的 wrapper 调用使用默认外置 slot，仅显示帮助及建立 wrapper 管理目录；实际安装、验证、应用启动均显式使用本轮新 slot。

## 真实桌面与发送边界

本轮按 T-042/desktop 启动方式运行：offset 2038 的 dev:web，Electron 43.4.1 主进程 PID 52055，Electron 自行启动 backend（端口 54877）；renderer 为 7771。桌面主进程、web 与 server 都来自本轮恢复后的合并候选构建/源码。数据目录初始没有数据库，仅复制旧隔离实例的 settings 并确认全部 providers/providerInstances disabled；不是复制旧任务或旧事件。

通过真实门禁 create、原生 feature socket 的 thread.create 和 membership HTTP 创建新输入；未注入响应、未改 SQLite。membership 测试之后，通过实际 dispatch 创建受管 worker，再用 membership save 将该 thread 绑定到任务的 worker 栏。全部输入与响应在 desktop 目录，测试仓库、worktree 和门禁状态在新外置目录。

Computer Use 只绑定上述自启 Electron。第一次 getApp 在启动期间超时，没有输入；第二次绑定成功，关闭自开的 Developer Tools。点击 Not now 跳过应用内 Safari 导入、项目导入、AppSnap 公告，并跳过导览；没有打开系统设置、授权或导入账号。通过界面的“任务窗口”链接进入 `/#/a2a`。

门禁 task 为 `t042-78ae72ed974e`，attempt 为 `92efb808-9192-4530-b13a-2a469d6f3704`，session 为 `f4bbb1ae-f4a1-4f71-b7e3-865267dc2178`，fence/spec_rev 均为 1。受管 thread 为 `9e523288-7849-4be9-a5fd-a3da89e37283`。dispatch 返回 ok 与 claimed；之后 provider turn start 被 disabled 检查拒绝。agent-origin 的分派消息在桌面显示 Sent by agent，它不是人工介入，也不是模型回复。

我在该受管 worker 输入框中发送尝试的文本为“人工介入复验 T-042 2026-10-08”。最初 native typeText 未送入中文字符，随后通过受控文本粘贴补全，AX 已确认完整文本后才点击 Send message。点击后 AX 出现“Provider is disabled in Synara settings.”提示；03 截图和完整 AX 保存了仍在输入框中的消息、Unsent draft、人工介入 —、provider disabled 和 observer healthy。

HTTP 门禁 events 与原生 CLI `events` 都回读成功，但 human_intervention 数量为 0，没有对应 message_id 或 dispatch_origin=user 可核对。没有创建伪事件。由于发送未成功，不能把这一结果作为正例或非受管反例的成功证据。provider 保持关闭，没有实际模型调用；也没有供应商实际 tier 的证明。

`ui-actions.json` 记录操作过程。所有截图来自 `cua app.getAXStateAndScreenshot` 的原始字节，未裁切或修改；02 为 dispatch 前 ready 状态，03 为 dispatch 后 claimed 状态和发送阻挡。画面中的其他阶段标签不表示那些阶段已通过。

## 复现与证据保存

`restore-dependencies.py`、`verify-recovery.py` 和 `run-check.py` 保存本轮恢复与串行检查流程。不要在现有记录目录上直接重跑；复验应使用新的目录与记录名，保留本轮产物。桌面准备与接口检查使用 `desktop/start-ui.py`、`prepare-server.py`、复制自 T-038 的 `http-scenario.py` 和 `native-rpc.mjs`；HTTP 脚本仅新增当前自启 backend 的认证接入，原主场景断言保持不变。临时 backend token 仅在内存中使用，未保存到证据。

`retained-fixtures.tar.gz` 包含本轮 35 项测试夹具、桌面测试仓库/worktree 和门禁状态；不包含 auth、server secrets、profile、原生 state.sqlite 或依赖树。原外置目录保留，没有嵌套 gitlink。`project-map-status.txt` 为 Problems 0 / stale 0。首轮事故与本轮恢复、复验属于不同记录，不以新结果改写旧失败。

剩余决定仅涉及原任务的模型调用限制：若继续证明人工介入与非受管反例，需要另行允许在隔离环境启用 provider 并允许其真实调用；本轮没有跨越该边界。环境恢复本身已经完成，不再要求用户为我的失误承担恢复决策。
