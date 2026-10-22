# T-126 候选 1 结果

- 候选：`35cadc44b`（代码、两个新测试与 README）。证据运行期间源码未改动。
- 修前版本：`04d632694`（T-123 收尾）。
- 结论：**PASS**（待独立审查）。

## 改了什么

- 项目终端经后台另开的专用 socket 连接。socket 在系统临时目录下随机命名的 0700 目录里，环境变量为 `A2A_TERMINAL_SOCKET`。终端环境不再导出 `A2A_STATE`。
- 专用 socket 在核对身份之前，拒绝一切非终端身份（`terminal_socket_terminal_only`）。拒绝记为 `request_rejected`，带 `socket: "terminal"`。原 `control.sock` 不变。
- 桌面应用的操作员凭据与连接描述文件移出数据目录：
  - 正式版、测试版放在按产品名命名的 Application Support 目录；
  - 显式 `--state` 时放在 `<数据目录>-credentials/`。
- 已有安装在启动时迁移：当前凭据复制到新位置，然后删除数据目录里的旧凭据与旧描述文件。迁移中断后，下次启动接着做完。

## 单元（`unit/commands.sh`）

`tests/test_t126_desktop_credentials.ts` 只做文件层检查，期望值来自 ticket：凭据是数据目录外的 0600 文件，迁移后旧文件不存在。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| credentials-green | PASS，9 项 | — |
| credentials-in-data-dir（隔离目录放进数据目录） | 失败 | `directory_outside_data_directory` |
| old-credentials-kept（不删旧凭据） | 失败 | `no_old_credential_left` |
| cleanup-only-on-first-move（只在搬迁那次清理） | 失败 | `interrupted_migration_finished` |
| moved-world-readable（新文件 0644） | 失败 | `current_credential_moved_private` |
| descriptor-any-directory（描述文件可指向任意目录） | 失败 | `descriptor_outside_directory_refused` |

回归：test_relay_core、test_t078_controller_relay、test_t078_relay_role 均退出 0。

## 端到端，源码入口（`e2e/commands.sh`）

`tests/test_t126_terminal_socket_e2e.py` 走真实 CLI、后台、两个 socket、zsh 与 `a2a` 命令。攻击脚本在终端里运行，只用终端看得到的信息：环境、令牌和申请 id。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green-01 | PASS，10 项 | — |
| red-01-parent（`--revision 04d632694`） | 失败 | `terminal_env_has_no_data_directory_or_credential`：`['A2A_STATE']` |
| red-02-socket-accepts-all（去掉终端专用检查） | 失败 | `terminal_visible_identities_cannot_decide` |
| red-03-state-exported（终端环境加回 `A2A_STATE`） | 失败 | `terminal_env_has_no_data_directory_or_credential` |
| red-04-refusal-unmarked（拒绝记录不带 socket） | 失败 | `terminal_socket_refusals_recorded` |

回归，均为 PASS：

| 运行 | 项数 |
| --- | --- |
| t121-green | 49 |
| t122-green | 23 |
| t124-gui-green（真实 Electron 窗口） | 28 |
| t124-restart-working | 19 |
| t124-restart-verified | 26 |
| t127-green | 19 |

## 端到端，打包测试版（`packaged/commands.sh`）

两个 `Enchanted Test.app` 分别从 `35cadc44b` 与 `04d632694` 打包，`package.json` 里的 `a2a.revision` 与之对应。驱动 `packaged/t126drive.mjs` 经 CDP 扮演用户：点击打开项目和新建终端，经 xterm 粘贴输入命令，点击“批准”，关闭并重开界面。驱动只以桌面应用的操作员身份调用后台，用于登记项目、读取状态和最后停止后台。三个阶段共用同一个隔离数据目录：

1. **修前版本**：终端环境导出 `A2A_STATE`，泄漏数据目录。这是本 ticket 检查的红态，与第 3 阶段用的是同一个检查函数。
2. **新版本，修前的后台仍在运行**：
   - 数据目录里的 `desktop-*` 文件全部删除；
   - 新凭据、描述文件为 0600，目录为 0700；
   - 新凭据与正在运行的后台使用的是同一份；
   - 界面重新连上同一个后台 PID。
3. **新版本，自己的后台**：
   - 终端环境中没有数据目录和凭据路径；
   - 终端里 `a2a whoami`、`a2a request executor` 照常工作，界面点“批准”后角色生效；
   - 终端用不带身份、自己的终端身份、伪造的操作员身份、伪造的窗口身份调用 `role_request_decide`，全部被拒，留下 4 条带 `socket: "terminal"` 的记录；
   - 关闭界面后后台与终端仍在；重开后用持久化的凭据连上同一个后台，接回同一个终端，`whoami` 仍为执行主控；
   - 后台停止后，专用 socket 被删除。

`packaged-01`：PASS，23 项（`packaged-01.run.json`）。截图与应用日志在归档盘，清单见 `packaged/packaged-01.archive.json`。夹具含操作员凭据与用户自己的环境变量，运行后删除，不归档。驱动的三次开发运行见 `../dev-runs.archive.json`：

- dev-01、dev-02 失败于驱动自身的缺陷：首次启动时等待了还没登记的项目，第 3 阶段取错了窗格。
- dev-03 在修好驱动后通过。

## 没有验证的、已知边界

- 不带 `--state` 时，凭据放进 `~/Library/Application Support/Enchanted Test`（正式版为 `Enchanted`）。这一点只由单元测试 `directory_outside_data_directory` 检查目录计算；打包运行使用显式 `--state`，没有写用户真实的测试版目录。
- 凭据仍是本用户可读的文件。有意搜索磁盘的 agent 仍可能读到它；同一用户的其他进程也可能从后台进程的环境里读到凭据路径。已写进 README。
- 受管 worker 与 controller 的环境仍有 `A2A_STATE`，它们经能力令牌调用，不在本 ticket 范围；数据目录里已经没有操作员凭据。
- shell 按键（`window_input` 等）被拒时，按原有规则不记录（避免泄漏按键时序）。所以端到端测试用 `window_resize` 检查窗口身份在专用 socket 上的拒绝记录。
- 已知在 HEAD 上就失败的套件，不作证据：
  - `tests/test_t102_desktop.mjs`：桩里的启动参数早已过时，在 `04d632694` 的 `desktop.mjs` 上同样失败；
  - 以及 T-123 记录过的 test_task_cards_e2e、daemon_gates、relay_scope、t107。
- `tests/run_t102_packaged.mjs` 与 batch19、batch20 里旧的打包辅助脚本仍从数据目录读描述文件。它们是有日期的旧运行记录，没有改；以后在新版本上重跑需要改成读 `<数据目录>-credentials/`。
