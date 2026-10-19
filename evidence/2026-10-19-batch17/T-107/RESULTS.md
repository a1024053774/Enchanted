# T-107 / attempt a1：INCOMPLETE

本次为本地候选交接，尚未提交、未独立审查、未运行真实 Electron。基线为
`0967cd465ce20c01b0a6ee29b2931ecbf4032caf`（exec/t107 起点）。未调用模型工具、
未启动模型回合、未操作 Herdr、未 push。没有生成截图或复制认证文件。

## 已实现

- 上方项目目录列表，使用真实 Git 分支与本地上游引用的领先／落后数；无上游保留缺口。
- 选项目后显示任务栏与已有启动记录；中文角色、任务、完整 attempt、CLI、状态与图例。
- 已核对的 relay 发送 launch → 成功 assign → 接收 launch 可以构成父子关系。
  角色地址、普通回复、关系歧义不会建立层级；未归属的 worker 等按任务分组。
- 点击聚焦已有窗格，其他历史记录用临时只读视图打开；不发输入凭据，不改保存布局。
- 七种状态的文字和图标、项目汇总、等待用户回答的单次转换通知及可保存的通知开关。
  缺少真实信号的两种等待状态保持未知，通知真实触发未验收。
- 扩充窗口 IPC 名称合同及拒绝检查。原门禁、操作锁、原多窗格准入规则未修改。

## 验收逐项

| 任务票验收 | 状态 | 当前证据或缺口 |
| --- | --- | --- |
| 真实 Electron 红态／绿态，两个项目与完整层级，逐个聚焦 | INCOMPLETE | IPC 已知坏基线被拒；真实 Electron 脚本待主控运行。现有 worker 派发无具体父 launch，不能把完整层级记为通过。 |
| 七状态真实信号／真实原件回放，缺失信号与未归属反例 | INCOMPLETE | 受控投影检查通过；两种等待信号缺口保留。受控输入不充当真实模型证据。 |
| 项目汇总、等待高亮、回答后恢复、一次通知及关闭 | INCOMPLETE | 受控汇总与通知转换、关闭、再进入均通过；真实等待与系统通知未验收。 |
| Git 与 git status -sb 一致；注册复用 T-106 | INCOMPLETE | 真实 Git 的领先 1／落后 1、无上游通过；T-106 注册 IPC 回归通过。真实界面待运行。 |
| 截图／命令／模型回合／地图检查 | INCOMPLETE | 按主控转述的用户裁定不交截图；复现命令已写；模型调用 0。稀疏检出造成的 8 个既有地图问题未改。 |

## 本地检查

摘要 JSON 保存本次命令和观察；测试输出不替代真实界面或真实模型验收。

- `node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /tmp/t107-ipc-green-04.json`：PASS。
  20 个显式 IPC、21 个显式 bridge 名称；保留旧 key、跨窗口、iframe、旧 attempt、错误任务、
  关闭时序与保存布局拒绝检查。T-107 起点被缺少侧栏合同的断言拒绝；通知不触发、历史
  主控获得输入凭据两处单变异分别被对应断言拒绝。另保留原有历史反例。
- `node workbench/tests/test_t107_sidebar.mjs /tmp/t107-projection-02.json`：PASS。
  使用真实 Git 与 SQLite；运行中、空闲等状态输入为受控对象，非真实模型原件。
- `python3 workbench/tests/test_t107_counterexamples.py /tmp/t107-counterexamples-01.json`：PASS。
  缺失信号被上调、按角色猜父会话、Git 领先数写死为零，均被对应断言拒绝。
  变异源码及失败现场按 JSON 中路径保留在 `/private/tmp`，未删除；归档尚待主控处理。
- `node --experimental-vm-modules workbench/tests/test_t106_creation.mjs /tmp/t107-t106-regression-01.json`：PASS。
- `node --experimental-vm-modules workbench/tests/test_t105_panes.mjs`：PASS。
- 标准 Vite 构建：PASS；依赖从内置盘已有安装只读引用，源码副本与中间构建目录已清理。
  构建仍有既有的大 chunk 提示；不把构建通过写成 Electron 验收。
- Python 新脚本与扩充的验收脚本按 Python 3.9 语法解析：PASS；`git diff --check`：PASS。

## 主控运行

```sh
bash evidence/2026-10-19-batch17/T-107/RUN-OUTSIDE-01-ELECTRON.sh electron-01
```

脚本在内置盘创建独立源码副本和隔离库，用固定 Electron 43.4.1 执行基线与候选。
无原生目录对话框、不调用模型、不写用户全局配置、不截图；只留下摘要。
通过已实现切片时退出 0，但摘要总状态仍为 INCOMPLETE，因为两种等待与完整 worker
父子关系尚无真实来源。失败时保留现场和构建路径，禁止覆盖同名摘要。
这次运行只覆盖可实现切片，不能关闭整张票。

## 交付身份冲突

当前进程缺少 `A2A_*` 和会话级 `GIT_CONFIG_*`，仓库默认 hook 路径没有提交钩子。
只读核对当前原生记录：会话 `01a15497-758a-7f22-945f-f2bbf27eb46e`，
`source=vscode`，CLI 版本 `0.163.0`，目录是本 worktree，当前模型／强度为
`gpt-6.1-sol/high`。

主 checkout 的 T-107/a1 启动记录为 `launch-2ae69905c1054464bc356597daf5364c`，
session `dc063ce6-97f7-411b-a03a-cc040c66b66c`，agent `s17-t107`；该记录要求 CLI
worker／xhigh，`native_session` 仍为 unknown。没有把当前 Desktop 会话写成它的原生身份，
没有安装钩子或手写尾注。主控须核对交付身份后，在合法会话环境中提交。

独立 behavioral-acceptance-review／design-integrity-review 均未运行：本次禁止调用模型，
worker 不能自行替代新的只读 reviewer。主控须对冻结候选另开审查。
