# T-257 worker 环境阻塞记录

状态：BLOCKED。2026-11-08，本 attempt 尚未取得 T-257 修前真实红态，未改生产行为，未形成可交付候选。

## 版本与范围

- 基线：`5c7df3a93019cea1a690194773d967bebb69a4ef`，开始时工作区干净。
- 任务：`a2a+T-257-1`；attempt：`42b3cd31-9194-45ba-85ea-4744b051cfe5`；session：`8563938f-d5bf-4ab7-b1ce-157ee39503ab`；fence：1；spec_rev：1。
- 当前 worker：Codex，任务卡指定 `gpt-6-astra` / `xhigh`。只记录请求配置，不据此证明供应商实际层级。
- 本机输出：`codex-cli 0.167.0`；Node `v26.5.0`。`codex --version` 另报 `WARNING: proceeding, even though we could not create PATH aliases: Operation not permitted (os error 1)`。
- 额外可写目录：`[]`；未修改任何额外目录。请求目录只用于本 attempt 的门禁请求，不入 Git。
- 使用本机 `project-map`、`reality-first-engineering`、`evidence-first-testing`、`document-writing` 技能；各 SKILL.md 未声明语义版本。未修改技能、权限、冻结验收、T-252 测试或项目地图。

## 已核对的行为与尚未证明的原因

REALITY GATE: BLOCKED。

目标是同一原生 turn 接收 Stop 期间的回执后能正确结束，后续队列继续投递，结束后允许回收；真实工作中仍须拒绝回收。非目标为其他票、界面、权限和门禁契约变更。

observed（源码）：`workbench/src/panes.ts` 的 `signal` 处理 Codex `UserPromptSubmit` 和 `Stop`。`noteSubmission` 认领已贴入的回执正文；`scan` 在原生 rollout 的 `task_started` 事件中把 `pane.turn` 绑定给当时的 `active.nativeTurn`。已认领正文的 UPS 分支只记录 `turn_start_signal`。Stop 匹配依赖 `active.nativeTurn`；匹配后才清除 active、转为空闲。`observeThread` 把窗格状态交给门禁用于判断是否在运行。

observed（调用者）：`workbench/src/daemon.ts` 的 `signal` 分支调用 `panes.signal` 并转交显式请求。socket 请求处理器在回执前调用 `settleInboxFeedback`，signal socket 关闭后调用 `panes.drain`。`panes.sendGateFeedback` 经 `dispatch` 排队并尝试投递。

inferred：同 turn 续跑不一定产生新的 `task_started`；若回执对应的新 active 未绑定原生 turn，第二个 Stop 可能无法匹配。这是待复现的解释，未据此修改代码。

unknown：真实 CLI 的回执贴入、Stop hook 返回、同 turn UPS/Stop、`task_complete` 的确切顺序；这一顺序是否导致本票要求的 busy 与 `reclaim=worker_working`。

下一步探针：在有权限的隔离环境中运行真实后台、门禁、Codex 交互 CLI 与本地 scripted Responses 模型；保留上述时间顺序、原生 turn、窗格和回收结果。不得调用供应商模型、启动 Claude、改库或强制 idle。负责人仍是本票 worker；沙箱外执行安排交执行主控。

顺序验证须保持的不变式（尚未执行搜索）：

1. 回执被同一原生 turn 吸收后，匹配的后续 Stop 必须结束该提交，后续队列能发送。
2. 正在工作、身份未核实、attempt/fence 不符或中断未解除时，不能以回执或模型自报放行回收。
3. 延迟或重复的旧 Stop 不能结束更新的提交，旧请求不能借续跑重复执行。
4. 顺序搜索需记录事件序列或种子；隔离模块搜索不能替代真实 CLI 红绿证据。

## 已执行的环境探针

本轮先确认本地 TCP 监听前提：Python `socket.bind(('127.0.0.1', 0))` 与 `listen(1)` 于 `2026-11-08T10:50:46.455800+00:00` 成功，退出码 0。该检查没有启动后台或 CLI，不证明完整环境可用。

随后从任务 worktree 执行现有 T-252 Codex 真实入口作为环境探针：

```sh
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py --cli codex --summary evidence/2026-11-08-batch34/T-257/worker/preflight-t252-codex-01.json
```

退出码：1。stdout：

```text
FAIL PermissionError: [Errno 1] Operation not permitted: '/private/tmp/t252-4e70r9ew'
```

完整 traceback 保存在 [preflight-t252-codex-01.json](preflight-t252-codex-01.json)。异常位于 `scripted_claude.py:259` 的 `tempfile.mkdtemp(..., dir='/private/tmp')`，在隔离夹具创建时即失败。原测试把异常标成 FAIL，本文按实际原因归为环境 BLOCKED；这不是 T-257 缺陷红态，也不证明 T-252 回归失败。`checks` 和 `preconditions` 均为空，模型请求数为 0，后台、hc 和原生 Codex 均未启动。没有请求真实供应商、没有启动 Claude。

没有换路径、修改公共夹具、修改权限或改用其他工具重试被拒操作。失败目录核对为不存在；未产生需要清理的夹具、数据库、hc 私有目录或构建缓存，没有删除旧现场。

复现环境阻塞时须把 `--summary` 换成新的文件名，避免覆盖上述证据。解除阻塞后需新增任务卡指定的 `test_t257_codex_stop_continuation_e2e.py`，取得 T-257 专属红态再修改生产行为；本次尚未创建该测试。

## 验证与交接

session 开始及停止前的 project-map status 均退出 0：Problems 0、Stale living docs 0。停止前输出见 [project-map-status-01.txt](project-map-status-01.txt)。不变式搜索、T-257 真实红绿、回收正反例、相关回归、候选审查均未执行；不以旧通过替代本票证据。

需经 `issue --blocking true` 上报执行主控，安排授权范围内的隔离实测。若需要扩大本会话权限，由主控交用户决定；答复不自动改变沙箱。当前仅保存阻塞证据，不发送完成 submit，不请求验收或集成。

**Works**：已定位需核对的生产入口与调用者，保留真实环境拒绝的命令、退出码和 traceback；尚无修复有效性证据。

**No regression**：未改生产代码或既有测试；未运行产品回归，环境拒绝不能算回归通过。

**Risk / undo**：T-257 仍未修复，因果关系待真实入口证明。本次仅新增文本证据，保留即可，无生产行为需要回退。

## 2026-11-08 v2 候选交付（以上 v1 记录原样保留）

当前状态：INCOMPLETE。最小实现、开发红绿、静态检查与自查已完成；候选真实入口红绿、相关完整回归、门禁 verify、独立审查及集成批准由主控接续，尚未宣称业务 PASS。

任务身份：task `a2a+T-257-1`，attempt `bd5eb7a7-618f-4cef-b096-b76f14280b17`，session `26392ed1-cc92-4bcf-a2c1-71cd2e289e05`，fence 2，spec_rev 2。基线 `ebd155141668da18cb2dc09238c5312e1804223a`；复现基线提交 `6b2fd3ec88de9b11d618fa16dc34535144d58abb`；实现与模块红绿提交 `a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c`。本报告之后的交付提交只补文本证据，不变更实现或测试。两次提交均核对有自动当前身份 A2A 尾注，没有手写旧身份。

代码修复仅在 `panes.ts` 的已认领 Codex UPS 分支绑定 `active.nativeTurn`，让同一原生 turn 吸收的回执能被后续 Stop 匹配。不改 daemon、hook、门禁、权限、冻结验收、全局配置或其他票。真实根因与修前主控证据出处见 [recovery-v2.md](recovery-v2.md)。没有启动 Claude、正式 Enchanted、用户 Herdr 或供应商模型。未触碰主控准备的 hc 缓存。

开发验证的命令与结果：

```sh
python3 evidence/2026-11-08-batch34/T-257/worker/run-module-check.py --dependencies /Users/luckye/Documents/Code/a2a/workbench/node_modules --summary evidence/2026-11-08-batch34/T-257/worker/module-red-02.json
python3 evidence/2026-11-08-batch34/T-257/worker/run-module-check.py --dependencies /Users/luckye/Documents/Code/a2a/workbench/node_modules --summary evidence/2026-11-08-batch34/T-257/worker/module-green-01.json
```

第一条在未改生产行为的 `6b2fd3ec8` 工作区运行，退出 1：104 场景、30 项失败；第二条在同一工作区加上当前唯一生产差异后运行，退出 0：104 场景全过。两次用同一份 TS 测试，源版本与完整生产 diff 均写入 JSON。重复运行须使用新的摘要名；还原红态应在独立副本使用 `6b2fd3ec8` 产品源码和 `a2d6dbcbb` 的 TS 测试，不在现有脏工作区撤销修复。检查使用真实 Panes 方法、SQLite 与 rollout 文件，仅排除 hc 构造和终端 I/O。TS 不能替代 Python 真实入口。

`module-red-01.json` 原始 status=FAIL 是 runner 初版将 hc 构造期间 EPERM 误标为测试失败；实际分类为 INCOMPLETE，见 `module-red-01-cleanup.json`。保留原文件和初始 schedules，未把环境失败计入红态；修正 runner 后对未完成场景保留 INCOMPLETE。没有绕过权限启动 hc；模块测试使用真实原型而不初始化不需要的终端边界。所有本轮模块数据库和源码副本已先写文件数/字节/路径状态再清理，只留下文本证据和命令脚本；只读依赖目标未改动，工作区没有 node_modules 链接。

静态与相关检查见 [static-and-regression-v2.json](static-and-regression-v2.json)：Node `--check`（panes.ts、TS 测试）、Python AST/compile（Python 真实入口、模块 runner）、`git diff --check` 均退出 0；现有 `test_t207_interrupted_turn_hooks.ts` 7 项通过，退出 0。该回归使用当前源码的隔离副本与只读依赖；通常已有依赖的候选可复跑 `node workbench/tests/test_t207_interrupted_turn_hooks.ts "$PWD" <新的摘要.json>`。它未启动 CLI，不能证明真实中断回收。未运行全套、T-252/T-229 真实 CLI 回归；按 v2 卡由主控安排。

主控真实入口复跑（每次使用新的摘要名；默认不加参数也运行完整场景并打印唯一路径）：

```sh
ENCHANTED_HC_CACHE_DIR=/private/tmp/t257-hc-cache-20261108 python3 workbench/tests/test_t257_codex_stop_continuation_e2e.py --revision 5c7df3a93019cea1a690194773d967bebb69a4ef --summary /private/tmp/t257-red-NEW.json
ENCHANTED_HC_CACHE_DIR=/private/tmp/t257-hc-cache-20261108 python3 workbench/tests/test_t257_codex_stop_continuation_e2e.py --summary /private/tmp/t257-green-NEW.json
```

已知坏生产版本的真实红态由主控取得：10 个前提成立、5 个业务行为失败、两次工作中 reclaim 均拒绝，退出 1。本 worker 未重新尝试已知不可写的 /private/tmp 真实入口。Python 只依赖既有测试辅助文件，不依赖新增 TS 或 worker 脚本；门禁红态只移植该 Python 文件即可。

已完成 `design-integrity-review` 自查（[报告](design-review-v2.md)）：结构 PASS，无发现；`behavioral-acceptance-review` 自查（[报告](behavioral-review-v2.md)）：INCOMPLETE，缺候选真实入口证据与独立审查。不把自查称为门禁独立审查。

结束前 `project_map.py status` 退出 1，Problems 0、Stale living docs 1：`workbench/README.md` 因 panes.ts 变化须主控核对。地图与 README 不在本 worker 范围；issue 请求 `245e8e02-4d71-4289-b2b6-9a0f91345aba` 已写入请求目录，CLI 返回 queued=true、delivered=false。这是排队回执，不是主控已处理。没有重复查询 status，也不以 stale 为理由绕过门禁或扩大写入范围。

额外可写目录为 `[]`，没有额外目录改动。请求目录只保存当前 attempt 的请求与移植补丁，未纳入提交。最终候选需通过指定 submit 命令显式交付；queued 仅表示等待本轮 Stop hook 转交，不能写成验收通过。

**Works**：主控真实修前红态可追溯；当前最小绑定修复在同一 104 场景中从 30 项失败变为全部通过。候选真实业务绿态未测，整体 INCOMPLETE。

**No regression**：现有 T-207 的 7 项中断/身份检查及静态检查通过；既有验收文件未改。真实运行时相关回归和完整门禁验证待主控执行。

**Risk / undo**：正式运行时尚未安装本候选，submit 回执仍可能触发旧 busy 缺陷；不伪造 idle。主控先验证并处理 README stale，再安排独立审查与集成批准。候选尚未集成；撤销 panes.ts 的 4 行新增即可回退生产改动，保留所有红态与历史记录。

## 2026-11-08 v3 候选转入（以上历史记录原样保留）

状态：INCOMPLETE。本 attempt `6ca3622b-b0e7-41ad-a21f-7ff810441994`、session `df429446-05ca-46a3-8106-2d0f1eec943b`、fence 3、spec_rev 3；基线 `ec68e0539f886bdbe37df79d085ba85946e3870e`。按卡转入 `ebd155141668da18cb2dc09238c5312e1804223a..5484315a5e318bce557dcc32e429f5d251453e84` 的 25 个卡内文件，未重新设计或更改测试断言。

暂存后整个 workbench 与主控实测 `a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c` 差异为空。原交付之后的主控真实绿态、同测试坏父版本红态与 T-252 回归，引用于 [v3 中文交接](handoff-v3.md)；它们不是本 worker 本轮运行结果。完整静态命令、退出码和原始输出见 [static-checks-v3.json](static-checks-v3.json)。本轮语法、格式、冻结文件与内容一致性检查通过；project-map 结束检查退出 1，已知 README stale 留给主控处理。未跑真实 CLI、模块场景、回归或全套测试，未创建依赖链接、缓存或夹具；额外目录改动为无。

**Works**：已转入相同候选并准备以新身份提交、显式 submit；本 attempt 门禁完成条件、红态与独立审查仍待执行。

**No regression**：冻结验收文件未改，静态检查通过；历史实测与当前检查分开记录，不将旧通过当成本 attempt 门禁通过。

**Risk / undo**：正式后台仍可能卡 busy，提交后由主控跟进；保留全部历史和本轮文本证据，需要回退时撤销 panes.ts 的 4 行生产新增。
