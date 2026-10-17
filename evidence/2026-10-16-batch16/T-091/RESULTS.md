# T-091 结果记录

日期：2026-10-17。task `T-091`，attempt `a1`，worker `s16-t091`，启动记录 `launch-a818e11600754e8b8ad79aab63a17f83`，ticket ready_rev 1。整票状态：**INCOMPLETE**。单窗口三窗格的基线红态已取得；产品实现、绿态、反例、回归与独立交付审查尚未完成。

## red 与 close 系列

| 运行 | 原状态／退出码 | 事实与结论 |
| --- | --- | --- |
| red-01 | INCOMPLETE／rc 1 | observer_response_deadline；三个 observer 输出为零，未取得产品红态。后台三个窗格读回已生成，但 Electron 6599 未退出，cleanup_complete=false。原失败不改判 |
| close-01 | BLOCKED／rc 2 | 6599 卡在 ready 前，正常退出请求被拒：electron_normal_quit_request_refused |
| 主控人工处置 | 主控报告 | 执行主控核对 6599 的完整 argv、06:30:34 启动时间与 ppid 1 后，亲自发一次 SIGTERM，报告 2 秒后退出且无残留。不是 worker 或脚本动作；2 秒未经 worker 独立测量，不补造具体命令 argv 或精确时间戳 |
| close-02 | BLOCKED／rc 2 | already_absent，未发退出请求；复制前 inventory 拒绝符号链接，fixture_archive_contains_symlink |
| close-03 | PASS／rc 0 | 已核对 6599 和原 writer 不存在；仅复制已停止夹具，链接按自身保存，原件保留。71 个文件条目、2,482,692 字节、2 条链接，comparison=true。PASS 只指收尾与归档，不上调 red-01 |
| red-02 | INCOMPLETE／rc 1，**有效红态已取得** | red_observed=true，expected=3、observed=1；实际一个窗口只有 worker 终端。ready／退出均确认、cleanup_complete=true，error／archive_error 缺省为空，cleanup_errors=[]。该轮产品仍未实现三窗格，rc 1 是要求的合同失败 |

执行与原图检查来源为执行主控 #9／本对话主控 #36。worker 本轮只读核对外置 JSON、日志、原始单帧，没有重启或操作该场景。场景供应商模型回合 0、假 Messages POST 0、keys=[]、没有粘贴或放行；受管 worker 是现有受控 C receiver，不能把其 Codex 形状版本号／原生日志当成真实 Codex 模型回合。

close-03 与 red-02 都以 `6974c2aad1233133264b7448e1277cd19fa0b6ba` 的脚本运行；red-02 的产品源码与起点 `44bbb7828459d81fab0d46069a19d3dd515a7732` 相同。Node v26.5.0，Electron 43.4.1；两个 Claude CLI 固定 2.1.296，停在隔离首屏，不走真登录。完整 argv、输出、快照和进程事实见外置原件。

## red-02 的独立输入与真实读回

任务：`t091-red-c6e65649`，任务标题“T-091 同任务三窗格基线”。三个预先登记的启动身份为：

| 角色／preset（来自启动记录） | launch | 外置读回 |
| --- | --- | --- |
| controller／ideation | `295b635c-42dc-491c-a356-38359b24c1df` | ideation.snapshot.json、ideation.process.json、ideation.launch.json |
| controller／executor | `d0f2b1e2-f2cc-4269-8cb2-8c6d0c89e848` | executor.snapshot.json、executor.process.json、executor.launch.json |
| 受管 worker | `e7145a5d-ae59-457c-accb-3a6fe71fc22e` | worker.snapshot.json、worker.process.json |

基线 snapshot 尚未投影 preset；不能仅凭两个 controller 字样区分构思／执行角色，须核对对应启动记录。单帧也不代替这些身份读回。

`view.json` 和原图都显示一个 BrowserWindow 内仅一个终端格，绑定上述 worker；屏幕含 `T078_DETERMINISTIC_RECEIVER_READY`，没有两个主控格，底部保留任务门禁栏。主控已看原图；worker 本轮只读查看同一张原图，所见一致。未拼图、未把顺次切换截图当同时显示，未覆盖标签。

原始单帧只留外置盘：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-02/baseline-original.png`。指针为 [red-02.single-frame.pointer.json](red-02.single-frame.pointer.json)，原件 213,422 字节，2880×1800；对应逻辑窗口 1440×900、Electron PID 64741、CoreGraphics 窗口号 10448。实际捕获命令是 `/usr/sbin/screencapture -x -o -l 10448 <外置原图路径>`；完整 argv 保存在 capture.json。仓库不复制 PNG、原始二进制、SQLite 或整个 fixtures。

## 原件位置与重放条件

统一外置根：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/`。

- `red-01/`、`red-01-close-01/`、`red-01-close-02/`：失败原件不覆盖。
- `red-01-close-03/fixture/`：原 red-01 夹具的停止后副本；清单 [red-01-close-03.archive.json](red-01-close-03.archive.json)，原目录 `/private/tmp/t078-2-t091-red-05cht89k` 保留。
- `red-02/fixture/`：172 个文件条目、5,222,955 字节、2 条链接，comparison=true；清单 [red-02.archive.json](red-02.archive.json)，原目录 `/private/tmp/t078-2-t091-red-bh38vd4j` 保留。
- `red-02/`：三份 snapshot、process、first-screen，expected.json、view.json、capture.json、observer 日志与完整命令原始输出。链接清单同时标记原夹具／归档目录外目标，链接不跟随、绝对目标不重写。

主控日志位于 `/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/` 下的 `t091-close03.log`、`t091-red-02.log`，早期失败另见相应 red／close 日志。

本轮执行入口及参数为：

```sh
python3 -B evidence/2026-10-16-batch16/T-091/close_red01.py --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-01-close-03 --label red-01-close-03 --approval-ref '<本轮主控批准，逐字值见 run.json>'
python3 -B evidence/2026-10-16-batch16/T-091/run_red.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/red-02 --label red-02 --approval-ref '<本轮主控批准，逐字值见 run.json>'
```

这是已执行命令的可读形式，输出标签均已使用。重放须使用冻结版本和新标签／新批准；后续产品实现会使当前 worktree 不再满足 red 脚本的基线检查，不能直接把修改后的源码冒作基线重放。完整原始脚本 argv 与批准引用保留在各 run.json。

## 实现顺序与当前边界

下一步为单格 **Tracer bullet**：同一生产入口经 sender 窗口及 pane key 查询快照、读输出、发输入和放行；不保留旧单格 IPC 实现。单格真实读回交执行主控跑通后，再扩到已确认的上方双主控／下方全宽 worker；窗宽小于 1000px 时三行，160×45 网格与独立滚动保持不变。

绿态、错 task／旧 launch 反例、T-074／T-075 正反例及 T-078 输入回归均为 **INCOMPLETE**，不得用本轮红态或旧候选通过结论替代。仍只在隔离场景验证，所有 Electron／daemon／PTY／ps／截图实跑交执行主控，不在 worker 沙箱外执行。

## 单格实现候选（待实跑）

单格已迁到 sender 窗口／pane key 的唯一生产通路，六条 IPC 进程内单次注册；preset 是 daemon 唯一新增投影。完整身份、实际焦点标识、原输入序号／放行声明与 160×45 网格保留；未扩三格。

本地 `pane-ipc-unit-01.json` 的八项 main／preload 边界检查为 PASS；未知 key 的旧 API 被已知坏版本反例拒绝。`driver-selection-unit-01.json` 在给定观察值上验证显式选择、角色／快照绑定、未知／歧义拒绝，旧驱动不拒绝歧义而失败。这些是 VM／给定边界证据，不是 GUI 或后台实跑。脚本语法、TS／TSX 内存转换通过；没有在 worker 中完整构建、启动 Electron 或后台。

待主控核对并运行 [TRACER-RUN.md](TRACER-RUN.md) 的 tracer-01；原图仍只留外置盘。按已确认顺序，取得真实单格读回后再扩三格并重跑新候选的绿态、反例和回归。[REGRESSION-PLAN.md](REGRESSION-PLAN.md) 给出现有 CLI 全命令，并列出旧验收材料／包装器问题，不把它们隐去或记为通过。
