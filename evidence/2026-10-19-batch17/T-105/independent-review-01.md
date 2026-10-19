STATUS: INCOMPLETE
TARGET: T-105 / a1；候选 `395492c8fea315c3f2419699d890fd8292e3fed4`，功能提交 `ba23a605d`；基线 `37c8a9e77c7c0a0e7426accbec077f0e33946bf4`；分支 `exec/t105`。

EVIDENCE:

- **范围与结论**：第一轮干净上下文、只读独立审查。按角色卡、AGENTS、T-105 用户逐字选项、T-104 Resolution 重建预期，再以 RESULTS 定位证据。审查中候选 HEAD 保持不变；只新增本报告及 REVIEW-OUTSIDE-01.sh。没有实现、修复、子 agent、模型调用、提权、门禁 submit、Git 提交或全局配置写入。未发现已确认的候选缺陷；原生目录选择还缺真实操作证据，因此不宣布整票 PASS。
- **规范解释**：T-105 只取代 T-104 的“必须属于项目、先选任务”限制，仍保留普通终端不经门禁、不采集输入正文和逐次输入元数据的要求。T-096 按用户裁定 B：主控仅按受认可启动记录恢复，worker/reviewer 不续接或重绑定受管 attempt。关闭 agent 视图与回收 attempt 是两件事，后者仍须门禁。
- **真实 Electron 原件（执行主控来源）**：已读 `electron-02.json`，候选完整版本与本次冻结版本一致，candidate_diff 为空，Electron 43.4.1 从内置盘运行，10 项检查通过，模型调用 0，cleanup_complete=true。该原件证明真实空库创建 zsh、家目录 cwd、右/下分屏、放大/还原、中文改名、缩窗、菜单方向键/Escape、真实 SGR 右键字节、关闭子进程、只重开界面及重启后台的区别、普通终端输入隐私、恢复失败的 agent 窗格和关闭 worker 不改 task/attempt。没有把它记成本 reviewer 亲自执行的 GUI 运行；它也没有覆盖原生目录对话框或活跃真实 worker 输入。
- **本轮可复现命令**：在仓库根运行 `bash evidence/2026-10-19-batch17/T-105/REVIEW-OUTSIDE-01.sh --isolated-only`。最终版本已运行，退出 0；Node 26.5.0、Python 3.9.6。摘要和每条完整 argv、退出码、stdout、stderr 在 `/private/tmp/t105-independent-r01-nmwcft19/review-summary.json` 及同目录文本中。所有被测源码与变异均由冻结候选的 git archive 提取，未建 worktree。脚本自带探针，可在新的 /tmp 目录重放，不依赖本轮临时文件。
- **(1) 随意开终端：部分 PASS，目录真实操作 INCOMPLETE**。`app/main.ts:135` 的来源白名单不要求任务；`main.ts:293` 在无任务时取 homedir；`src/panes.ts:118` 接受 project=null，检查已有绝对目录，启动 `/bin/zsh -l -i`，没有调用 claim。候选 main IPC 测试通过；真实无项目终端/家目录 cwd 由 electron-02 证明。目录对话框的安全与取消逻辑由下面的独立 IPC 探针证明；没有真实点选目录的证据。
- **(2) 六项菜单：PASS（源码加当前候选真实 Electron 原件）**。`app/renderer.tsx:264` 明确提供“重命名窗格、向右分屏、向下分屏、放大/还原、把右键发给窗格、关闭窗格”；按钮可 Tab 到达，菜单使用原生按钮并处理方向键、Home、End、Escape，改名有输入框与取消。分屏树按百分比递归二等分（`renderer.tsx:290`），现有 FitAddon 配合 ResizeObserver 更新终端尺寸；放大只隐藏其他视图。electron-02 核对三格相对位置、缩窗后正宽高、焦点与 Escape，以及真实 PTY 程序收到 SGR 右键按下字节；关闭转发时不产生鼠标字节且恢复菜单。Home/End 和每个菜单项的 Enter 未逐项单独跑 GUI，用源码与原生按钮语义核对，不声称做过完整辅助技术审计。
- **(3) 布局、名字及恢复：PASS（本票改动范围）**。`src/store.ts:79` 从唯一 SQLite 的追加事件读取 arrangement；`src/daemon.ts:184` 校验 launch 归属、打开集、重复叶子、深度和名字；`main.ts:280` 才把持久 launch id 转为本窗口 pane key，不持久化输入凭据。候选的 main IPC 重开合同通过，electron-02 证明名字/排列保持；只关界面连接原后台进程，后台也重启后普通终端显示已结束、只读且 launch 数不增加。`src/panes.ts:312` 的普通终端不重跑与既有 agent 恢复分支未改，T-096 的受管 attempt 拒绝恢复仍在。没有借用旧 T-096 七场结论宣称本轮又跑过那些场景。
- **(4) 不可削弱语义：PASS**。`renderer.tsx:220` 的菜单和标题栏共用 closePane，走 `main.ts:251` 的既有 pane_layout_close；`daemon.ts:190` 要求 operator 并核对 scope，普通终端才调用 closeShell，agent 只 forgetOpen，不杀进程、不回收 attempt。独立探针注入活跃 current_attempt 和 PTY 边界替身，执行真实 daemon 的认证与请求处理、真实 Panes 写入排序及真实 A2AGates/SQLite：带新 nonce 的 worker 输入实际写入 PTY，并在 user_inputs 与 human_intervention 中各形成绑定原 attempt/session/fence 的记录；替换 current_attempt 后旧输入拒绝为 stale_attempt，PTY 不再收到字节。worker 关闭时 kill 次数为 0，task/attempt 原文逐字段不变，只移除打开集。普通终端输入实际到达 PTY，前后 orchestration_events 增量为 0，user_inputs 不增加，user_input_ingress 为 0。真实 socket 与真实 worker/供应商进程不在此隔离证据范围内，按派发要求用源码与隔离测试核实；未冒称真实活跃 Codex GUI 证据。
- **门禁与锁：PASS（差异审查）**。`git diff 37c8a9e77 395492c8f -- workbench/src/gates` 只有 cli.ts 的 shell_start 项目参数从必需改为可选；core.ts、锁、fence、CAS、submit、验收、集成与回收逻辑没有修改。新的布局保存命令只有 operator 能用，renderer 没有受管生命周期控制入口。
- **(5) IPC 安全与合同：PASS**。本轮重跑 test_t091_pane_ipc.mjs，通过明确的 14 个 handler / 15 个 bridge 名称与全 handler 的 iframe/未知 sender 拒绝，以及跨窗口 pane key、历史 worker、凭据/序号分离、关闭/恢复和既有已知坏实现反例。`main.ts:80` 核对 sender 对象及 mainFrame；paneAction、resize 都先经 target 的本窗口 key 检查。resize 还限整数范围并复用窗口凭据、序号和输入队列。对合同 diff 的检查没有发现删除旧安全断言；原“无任务必拒绝”仅按新需求改成允许独立终端，其余变化是新 handler、reviewer 只读及新终端范围的断言/夹具扩展。
- **(6) 目录由谁选：IPC 安全 PASS；原生交互 INCOMPLETE**。`main.ts:135` 只收 default/home/project/choose 四个枚举，路径由主进程的 homedir、任务记录或 `dialog.showOpenDialog(context.window, {properties:['openDirectory']})` 得到（`main.ts:299`），renderer 不能传 cwd。`src/panes.ts:120` 再校验目录并 realpath。独立目录探针验证任意路径字符串、对象、数组和 null 均被拒绝，且没有创建终端或调用对话框；取消不创建；对话框返回的中文含空格目录才传给 shell_start，父窗口为请求所属窗口。这是对话框边界替身，不能据此宣称 macOS 原生面板已经实际选过目录。受信 operator CLI 本来就能传 cwd，T-104 Resolution 已明确保留，未把它混成 renderer 权限。
- **(7) design-integrity-review：已查范围 PASS**。本候选触及验收表面，按该 skill 的路由，以 behavioral-acceptance-review 为主并核对结构风险。新增 catch 是名字保存失败时恢复本地名字并重新抛出，属于 UI 操作所有者；没有新增吞异常、策略重试、双写门禁、平行生命周期 API 或未证明需要的兼容层。沿用现有 Panes 与唯一 SQLite，符合 Deep modules；分屏树的持久 launch id 与显示 pane key 分工明确。Tracer bullet 的无项目终端→分屏→重开合同能运行；Ubiquitous language 沿用窗格、普通终端和人工介入。

FINDINGS:

- 没有已确认、可复现的候选产品缺陷。当前结论 INCOMPLETE 的原因是原生目录选择的真实边界证据缺失，不把未运行记成产品失败或 PASS。

COUNTEREXAMPLE:

- 先跑好候选的相同探针，再在三份独立 git archive 副本中各改一处；退出码 1 还必须命中指定业务断言，设置/依赖/启动错误不算拒绝。以下结果均已实际获得。
- **变异一：关闭 worker 直接杀进程**。`src/daemon.ts:198` 的 `else panes.forgetOpen(input.launch)` 改为先 `panes.byLaunch(input.launch).pty.kill()` 再移除视图。运行 `node --experimental-vm-modules <原件目录>/isolated-review.mjs <原件目录>/worker-kill <原件目录>/reject-worker-kill all`。候选退出 0；变异退出 1，断言“关闭worker视图不得直接杀进程”，实际 kill=1、预期=0；前置的活跃输入/普通输入断言已通过。**被拒绝**。
- **变异二：普通终端输入写事件流**。`src/daemon.ts:494` 的 shellInput 分类之后，仅新增 `if (shellInput) store.event("review_bad_input", envelope.input)`。运行相同探针，source 换为 shell-log、输出换为 reject-shell-log。候选退出 0；变异退出 1，断言“普通终端逐次输入不得写入事件或元数据”，增量实际=1、预期=0。**被拒绝**。
- **变异三：重启普通终端自动重跑**。`src/panes.ts:315` 的 shell 恢复分支新增一次 `this.startShell(record.project, record.worktree)`。运行 `node --experimental-vm-modules <原件目录>/isolated-review.mjs <原件目录>/shell-restart <原件目录>/reject-shell-restart restart`。候选退出 0；变异退出 1，断言“普通终端重启不得调用startShell”，实际调用=1、预期=0。**被拒绝**。
- 上述 `<原件目录>` 为 `/private/tmp/t105-independent-r01-nmwcft19`；摘要保留具体绝对命令。另重跑的既有 IPC 合同也拒绝其内置旧版本、单窗格、关闭不移除和空布局回填等反例。没有用三个只改后端的变异去要求纯 main IPC 测试证明后端正确。
- 早期探针设置错误均保留在 `/private/tmp/t105-review01-3bxkjuhi`：首次误读 events.data（真实列为 details）；目录探针首次误把原窗口当成重开后的父窗口。修正的只是 /tmp 审查探针，未改候选；这些设置错误不计作产品红态或变异拒绝。另一次未传 restart 参数只跑了默认输入场景，也没有当成恢复证据；随后显式 restart 的候选与变异才计入上面结果。

LIMITATIONS:

- **待补的必要证据**：真实工具栏选择“选择目录…”→macOS 原生对话框选择与家目录不同、中文含空格的隔离目录→真实 zsh 的 pwd 正确。本轮未运行 GUI、不申请升级；按派发交给执行主控在沙箱外完成。复验脚本已经加入该入口，不替换 dialog 返回值。按 behavioral-acceptance-review 的原文要求：“require evidence from that boundary (or clearly mark the result INCOMPLETE)”，目前保持 INCOMPLETE。
- 执行主控只需运行 `bash evidence/2026-10-19-batch17/T-105/REVIEW-OUTSIDE-01.sh --chooser`。脚本先重跑本轮全部隔离检查及变异，然后用内置盘 Electron 43.4.1、自建 HOME/数据库/目录启动新窗口；打印“目录选择待操作”和窗口 PID 后，执行主控仅在这个隔离窗口的原生目录对话框里选打印的目录。脚本等待 180 秒，核对启动记录与 PTY pwd，关闭自建终端/窗口/后台，写新的 /tmp/review-summary.json。取消、无人操作或退出未确认均记 INCOMPLETE；不会修改系统设置、登录、全局配置或保存截图。
- 不带参数或传 `--electron` 会额外重跑现有真实 Electron 红绿场景，并把“输入写事件流”“自动重跑 shell”两个变异放到该真实入口验证，再做原生目录选择。此分支仅做了 Bash、Python 3.9 和生成 driver 的 Node 语法检查，尚未执行，不能算通过证据。其异常或未知进程状态保留临时目录；已确认退出后清理依赖副本和构建中间产物。
- **project-map**：本稀疏 checkout 在审查开始与结束均为相同的 8 个缺文件/断链问题，stale=0，退出 1；没有写成 0 问题。另在完整主 checkout 只读运行同一 status：Problems=0、Stale=0、退出 0。该结果只证明完整主 checkout 的地图健康，不冒称稀疏候选 status 通过。本候选没有修改地图、术语或这些缺文件。
- 这是本候选的有界审查，不是全站前端/辅助技术、长期稳定性或性能审计；未运行真实供应商 worker 或调用模型。也没有重跑整个 T-096 历史恢复矩阵、认领到集成的全门禁流程。
- UTF-8 无 BOM、中文报告；保留会话开始时已存在的未跟踪 electron-02.json。报告和脚本之外的仓库内容未写入。

RULE:

- T-104 已出现过普通输入元数据与 shell 自动重跑漏测。本轮独立探针及三变异已补可执行拒绝证据，入口保存在本次复验脚本；建议执行主控把“活跃 worker 输入/关闭”的隔离场景纳入后续例行验收，避免只用历史只读 worker 夹具。这是建议，没有在只读审查中修改测试或治理规则。
- 本报告不能替执行主控的门禁验收、集成决定或用户切换工作台的“可用”裁定。

T-105 REVIEW INCOMPLETE
