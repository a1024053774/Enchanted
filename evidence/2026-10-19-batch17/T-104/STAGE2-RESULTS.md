# T-104 / a1 第二段

状态：**INCOMPLETE（运行验收范围 PASS，待提交与独立审查）**。主控 #22 回传 06/ui-01 退出 0；worker 已核对原始结果、归档库和五张截图。后台套件、两处基线／候选合同及真实 Electron 红／绿旅程均通过。提交号、独立审查和完整 checkout 地图核对仍待主控完成。

## 绑定与边界

沿用第一段 worker、launch、session 和 Herdr 交付绑定，见 `RESULTS.md`。主控 #19 授权 T-103 合入后继续第二段；主控 #20 要求解决冲突并完成合并。主控回传：第一段提交 `c6dd956f0`，合并提交 `edd469f6b9d2d34bedb3a9479159fbb917dc43d5`，第二父提交为 `ea206484b8bcdae19fa4edd91b7553af22ff757b`。

**Tracer bullet**：窗格栏按钮 → 当前窗口的 IPC → 后台 shell_start → 项目 zsh → xterm 输入 → 界面关闭 → 后台重启后的只读终端。**Deep modules**：继续复用窗口身份、PTY 和唯一事件流；不新增门禁或输入记录器。**Ubiquitous language**：普通终端为项目对象，task／attempt 为空，和受管 worker 分开显示。

不调用供应商 CLI 或模型，不写全局配置，不 push，不用问题面板。交付继续由主控在沙箱外提交、独立审查、合入，worker 不调用 submit。

## 合并证据

`merge-resolution-20.json` 保存冲突处理检查。两边命令、目录查询不写请求事件的行为，以及窗口载荷脱敏均保留。主控执行 04B 退出 0，现有 hook 生成尾注；没有改写历史。

`merge-01-summary.json` 为 PASS；主控在沙箱外实际运行了第一段后台套件、T-103 的 `test_t091_pane_ipc.mjs` 和真实 `window_contract`，以及 T-104 的真实 UI 红态。原件与红态截图位于 `/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/merge-01/`。该结论只覆盖合并后的未加按钮候选，不替新界面背书。

## 界面与合同改动

- 在窗格栏加入“新建终端”。须先选择任务，由主进程重新核对任务对应的项目与目录，再创建项目终端；渲染层不能传入任意 cwd。未选择、正在切换或正在创建时拒绝创建，界面禁用重复操作。
- 终端显示“普通终端”、zsh、项目目录；不显示 worker 的人工介入提示、attempt 或队列放行按钮。与 agent 并存时采用现有样式和单列窗格布局。
- 项目终端可随同项目的任务切换；切换到其他项目只断开视图。后台重启后从保存的项目打开集读取，终端显示“已结束”，输入禁用。显式关闭仍经后台停止与进程核对。
- 控制序列的 focus observation 对 shell 只确认观察，不记录原始序列，不写输入；agent 的观察和专用输入记录路径保留。
- 新 IPC 名为 `a2a:new-terminal`，公开桥接名为 `newTerminal`。两处合同新增显式 shell 版本（12 个 handler、13 个桥接名），旧 legacy／picker 集合保留。原有 iframe、未知窗口、跨窗口 key、历史第三窗格、重复 launch、关闭和空布局反例仍执行；shell 合同只额外允许确切的项目布局只读查询。

本地 `ipc-picker-baseline-01.json` 与 `ipc-shell-02.json` 为 PASS；它们执行真实 main/preload 模块，但 Electron／transport 边界由夹具供应，不能证明真实窗口。`window_contract` 只扩充名称集合，保留只读输入不写 user_inputs、不改变门禁状态等断言。

## 按票核对

| 验收 | 当前证据 | 状态 |
| --- | --- | --- |
| 红态无入口、主进程未注册；绿态点击后 echo/pwd/cwd 正确 | ui-01/ui 的同一内置盘 Electron 红／绿旅程通过；green-terminal.png 可见普通终端、独立 nonce、中文与空格 cwd、LOGIN=on,RC=loaded | PASS（本次运行） |
| 输入不进 agent 记录；关闭子进程；重启显示已结束 | UI 关闭后独立 ps 确认 shell 71335、前台 sleep 71556、后台 sleep 71555 消失；第二个 shell 71675 随后台停止退出，重开显示 ended／只读。旧 key 拒绝输入 | PASS（本次运行） |
| 创建／关闭事件存在，无输入内容 | 两个 launch 各有一次 shell_created／shell_closed；独立 nonce 不在事件流中；归档库 user_inputs、user_input_ingress、dispatch_records 均为 0。ui-01-backend 的隐私坏版本被预期拒绝 | PASS（本次运行） |
| 门禁与受管输入不变；地图 0 问题 | ui-01 两处基线／候选合同与后台四项旧回归退出 0，原有反例被拒。稀疏 worktree 仍有 8 个缺失项、0 stale | 相关回归 PASS；地图要求 INCOMPLETE |

## ui-01 原件与截图核对

`ui-01-summary.json` 的 baseline-ipc、baseline-window、candidate-ipc、candidate-window、ui 五项均为 PASS／exit 0；`ui-01-backend/suite.json` 的候选、已知坏版本与隐私变异对照、worker-dispatch、controller-window、conflict-panes、restore 七项均符合预期。后台套件摘要中的 `part: 1` 与 `electron: 第二段尚未授权` 是被复用脚本的旧静态标签，不是本次权限或窗口证据；本次授权来自主控 #21，窗口证据以 06/ui-01 原件为准，未改写旧摘要。

原件：`/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/ui-01/`。窗口旅程的 `ui/run.json` 六项均 PASS，`cleanup_complete: true`，夹具 7,421,010 字节已归档。主控 #22 另确认没有残留 Electron。worker 只读核对以下五张原图：

| 截图（相对 ui/） | 可见事实 |
| --- | --- |
| `red/red-no-terminal.png` | 同一任务和历史 agent 视图没有“新建终端”入口 |
| `green/green-terminal.png` | 普通终端／zsh 与只读 worker 标识分开；输入 nonce、pwd 和登录配置读回正确 |
| `green/green-closed.png` | 普通终端窗格已移除，worker 视图与任务门禁仍在 |
| `green/green-project-shell.png` | 跨项目往返后原项目终端仍在，保持运行和可输入 |
| `reopened/green-ended.png` | 同一旧终端显示“已结束”、只读，进入按钮禁用 |

worker 的黄色“未恢复”提示是独立历史夹具按原恢复合同被拒，不属于 shell 故障，也未被隐藏。视觉核对在这五张桌面截图范围内完成，不据此声明窄窗口、输入法或任意 shell 配置已经验证。交互和进程结论由日志、库与实际进程核对支持，截图只支持显示结论。

UI 普通终端 launch 为 `e352c175-6bc1-4957-aa3f-06c4bce7c308` 和 `55f311af-68e1-4062-ae0e-e224af68f0ea`；二者 task／attempt 均为空。归档中 before-close-processes.json、events.json、fixture/state/state.sqlite3 与各窗口 driver 记录保留了本次追溯。所有产品、测试及 README 文件与通过的 source-snapshot 将由 07 再次逐字节比较；本次核对后未修改它们。

## 主控运行命令

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-06-UI.sh ui-01
```

顺序为后台套件、冻结基线 picker 合同与真实窗口、候选 shell 合同与真实窗口、同一内置盘 Electron 上的 UI 红／绿旅程。绿态通过 DOM 点击按钮和 xterm 粘贴／原生 Enter 输入；不以直接调用输入 IPC 替代成功路径。场景包括中文与空格 cwd、只读 agent 并存、两个 sleep、旧 key 拒绝、项目内外切换、关界面后台仍活、重启后结束和输入隐私。运行保存源码快照，结束时逐字节核对，保留失败现场。截图、原始日志和夹具只放外置盘；仓库保存摘要和 archive 清单。

全部通过并检查截图后提交：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-07-COMMIT-UI.sh evidence/2026-10-19-batch17/T-104/ui-01-summary.json
```

07 要求 PASS 与退出确认、至少五张截图，并核对当前源码与通过快照相同；使用 `git add --sparse` 和真实 worker 钩子环境。不手写尾注，不 push。提交号尚未知，不能先记为已提交。

## 环境与限制

主控 #21 明确保留 T-103 worktree 到本票结束。继续共用其已显式安装在内置盘的 Electron 43.4.1，红／绿使用同一个可执行文件；脚本核对版本、执行位和磁盘位置。测试通过 Electron 直接加载观察驱动，再调用实际构建的 main.run；不声称该旅程覆盖 start.mjs 或打包入口。T-104 未再装一份 Electron，第二段未增加内置盘依赖；构建输出、下载缓存及原始证据仍只写外置盘，缺盘报错。该共享路径是开发验证的已知依赖，不是产品依赖。

真实绿态和五张截图核对已完成。提交、主控独立审查及完整 checkout 地图核对仍待完成；不把本次运行 PASS 上调为整票已关闭或已集成。
