# T-042 第 3 项：人工介入桌面复验

**PASS。** 2026-10-08，在本次启动的隔离 Electron 桌面版中，经界面“任务窗口”进入 `/#/a2a`，在门禁 dispatch 创建、membership 绑定的 worker 中发送人工消息。任务窗口出现“人工介入 · 1”，真实 observer 为 healthy；门禁 events 与原生消息读回对应。普通非受管会话成功发送后没有新增门禁事件。共完成两次真实 Codex 短 turn，均回复 OK。

本结论只覆盖任务书指定的第 3 项及其反例、隔离和收尾，不代替用户的外观判断，不宣布完整 M1 或生产发布通过。

## 正例与反例

| 核对项 | 结果与证据 |
| --- | --- |
| 真实桌面入口 | Computer Use 点击“任务窗口”；`03-managed-expanded.jpg`、同名完整 AX 文本记录 `/#/a2a`、worker、claimed、healthy、人工介入标记和展开记录 |
| 受管身份 | task `t042-0d20433bded4`；attempt `2d1e6f60-bf75-4ffe-96a0-7587e5293c9e`；session `477773ac-ad08-47af-9428-d033e1616087`；fence/spec_rev 均为 1；见 `dispatch.json`、`membership.json` |
| thread/message | thread `7f00160f-ef8d-45da-81c4-247e56b05e6a`；message `d711ed42-dda6-43c6-b3b8-3e5fb1680522`；门禁事件与原生消息逐项相等 |
| 事件原文 | `events-managed-complete.json`：seq 21、type `human_intervention`、`dispatch_origin=user`、source_sequence 8；事件 ID `9c9d1f1f-e1b7-4ad8-8901-8374aa1b1ce7`；text 为“人工介入复验 T042-人-81：请只回复 OK，不要调用工具或修改文件，不要提交或交付。” |
| 业务状态 | dispatch 后、人工回复完成后及反例后，整个门禁 task 对象相等，保持 claimed，无 candidate、verification 或 integration_intent；人工输入没有提交、验收或集成 |
| 非受管反例 | 普通 thread `t042-0d20433bded4-reviewer`，message `398f90b0-7a44-474d-ae6b-abef648b5ec5`，原生消息 origin=user；输入“普通会话反例 T042-非-29：请只回复 OK，不要调用工具或修改文件。”后回复 OK。该 thread 虽沿用脚本 reviewer ID 后缀，但没有绑定任何 membership 或受管 task |
| 反例的权威读回 | `unmanaged-binding-before/after.json` 均 task=null；`membership-before-negative.json` 只有受管 worker；`native-unmanaged-complete.json` 证明消息实际发出且 turn 完成；`04-unmanaged.jpg` 为真实 UI |
| 事件计数与前缀 | 发送前 20 条；受管消息后 21 条；普通消息完成后仍为完全相同的 21 条。human_intervention 从 0 变为 1，反例后仍为 1。不是用未发送的草稿证明反例 |

`check-evidence.py` 只读上述真实产物，断言来自任务书中的关联身份、原文、状态不推进与非受管不记事件要求。执行 `python3 evidence/2026-10-07-synara-batch2/T-042/intervention/check-evidence.py` 可重新核对，已保存退出成功的输出 `check-evidence.json`。正例区分始终不记录，反例区分所有用户消息都记录；本轮没有修改产品或运行旧产品/变异产品，不把它称为新修复的红绿回归证明。没有额外调用审查模型，执行观察也不冒称独立 monitor 或独立审查。

## 两次模型调用与准备边界

候选为 Synara 分支 `a2a`、完整提交 `3566ef4eb34b18c480c7a49e4b5d741681b72426`。沿用 recovery-01 的标准构建和启动方式：dev:web offset 2038、renderer 7771，Electron 43.4.1 主进程 59059，自启 backend 59142、端口 60885。启动 argv、环境与进程组见 `vite-start.json`、`electron-start.json`、`isolation.json`；没有重建、修改产品代码、移动或链接 dist/node_modules。

dispatch 必须创建并投递 worker。为不占用人工正例和普通反例的两次额度，准备时保持 Codex disabled，经实际门禁 dispatch 创建受管 attempt。原生 reactor 明确以 disabled 拒绝启动；保留 `electron.log` 和 `01-before.jpg`，不伪装为成功模型 turn。之后才用原生 `server.updateSettings` 启用隔离 Codex，未重新 dispatch、未重发准备消息。UI 曾显示“session restarted without its previous history”，原始快照保留该提示；本轮正例仍从真实人工输入开始，有新原生 turn 与对应回复。

两条模型 turn 分别为 `01a11b73-5bf4-7531-856e-2b45e938c1d3` 与 `01a11b74-bdeb-7fb1-8608-bd60de00d128`。`model-turns.json` 从两个隔离 rollout 提取 task_started、task_complete、turn_context 与用户/助手消息，共两次开始、两次完成；两个原生快照各一项 checkpoint、session ready、无 pending interactions。没有第三条发送或其他 provider。

两次均为 gpt-6.1-sol、xhigh、fastMode=true、runtimeMode=full-access。Codex CLI 固定 0.161.0，wrapper 显式带 `-c 'service_tier="fast"' -c check_for_update_on_startup=false`。这是请求配置证据，不证明供应商实际服务 tier 或计费。没有工具调用完成工作的要求，两个助手可见答复均为 OK。

## 隔离、回收与用户数据

新隔离根为 `/Volumes/WD-Elements/dev-cache/synara/instances/t042-intervention-01`。HOME、XDG、应用数据、profile 和临时文件均在此根。认证 home 为 `/private/tmp/a2a-t042-codex-7gxuw55x`，只从用户配置复制一次 auth.json；新配置只信任本次夹具仓库及门禁为它创建的 worktree，只包含 git add、git commit 两条 allow 规则，无 hook。`codex-isolation.json` 保存非秘密配置与固定启动输入，认证副本从未入证据或 Git。

Computer Use 只绑定本次 Electron.app。启动初期两次绑定失败，待进程初始化后成功；仅关闭自启 DevTools、跳过应用内 Safari 导入、项目导入、AppSnap 公告与功能导览。没有进入系统设置、实际登录、密码或付款界面，没有授予权限或导入用户数据。保存的截图为 Computer Use 原始字节，未裁切、修图。

`reclaim.json` 通过唯一门禁入口指定原 attempt 回收；`native-reclaimed.json` 显示 stopped 且 archivedAt 非空，`events-reclaimed.json` 保留回收事件。回收使 task 返回 ready/current_attempt=null，这是收尾动作的结果，不是人工消息推动业务状态。

`cleanup.json` 与 `processes-before-stop.txt` 记录本次 Electron/Vite 进程组，停止后组内无残留。删除整个认证 home、Synara 自动生成的 codex-home-overlay，以及启动时的空 CODEX_HOME；隔离根内已无 auth.json。`user-before.json`、`user-after.json`、`user-comparison.json` 确认用户 config.toml、rules 目录及规则文件的大小/mtime 和只读 herdr status 输出全部相等。该核对只覆盖指定范围，不外推全机逐文件审计。

`product-final-status.txt` 仅原有 `.grok/` 未跟踪，受控产品文件无差异。夹具、worktree、门禁状态保留在外置盘，另打包为 `retained-fixture.tar.gz`；未打包认证、profile 或 desktop secrets，也未登记嵌套 gitlink。项目 status 为 Problems 0 / stale 0；MAP、ticket、AGENTS 均未改动。

## 操作复现索引

所有脚本位于本目录。真实复验须换用新的证据目录、隔离根和空闲端口，不可覆盖本轮文件；再次真实发送需要新的调用额度。

1. `start-ui.py` / `launch-electron.cjs`：隔离 dev:web 与 Electron；初始化目录与 disabled settings 见 `isolation.json`、`settings-disabled.json`。
2. `prepare-fixture.py`：独立测试 Git repo，命令保存在 `fixture.json`；`prepare-managed.py`：create、dispatch、membership、初始 events。
3. `enable-provider.py`：只复制 auth、固定 CLI、设置隔离 provider；输入及回执见 enable 系列文件。
4. Computer Use：任务窗口 → worker 输入框 → 粘贴正例文本 → Send message 一次 → 查看介入记录；普通会话 → 粘贴反例文本 → Send message 一次。完整输入以原生消息与门禁原文为准。
5. `readbacks.py managed`、`readbacks.py managed-complete`、`prepare-unmanaged.py`、`read-negative.py`：门禁及原生读取。普通 turn 完成后另读 `native-unmanaged-complete`、`events-negative-complete`；RPC 精确请求见各 input/command JSON。
6. 门禁 reclaim 请求见 `reclaim.json`，随后原生及 events 读回。`cleanup.py`：保存两次 turn 证据、停止自启进程、删除 home、归档夹具、用户前后核对。

仅提交本目录的证据和中文报告，不 push。

交付检查：中文报告 UTF-8 无 BOM、无替换字符。`git diff --cached --check` 对原始 AX/日志中的尾部空格与空行返回 2，详见 `diff-check.json`；保留原始证据，不为格式检查改写运行输出。
