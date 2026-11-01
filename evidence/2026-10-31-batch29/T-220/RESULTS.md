# T-220 结果：私有 core 被杀后谁把它拉起来，新 core 继承谁的环境

2026-11-01，执行主控（Claude Code）在本机实测。状态：事实部分 **PASS**；第 4 点的处理方式和界面两点 **待用户定**，见文末。

## 怎么测的

两个探针都走真实入口：门禁命令行起编排后台、开项目终端；hc 只用后台按固定版本装好的 0.1.15。每次用 `/private/tmp` 下的一次性夹具，夹具有自己的 HOME。所以“用户默认 XDG 目录”在这里落在夹具 HOME 下，不是真实的 `~/.local/state`。不启动供应商 CLI，不调用模型。两次运行前后用户自己的 hc core 与状态目录都没有变化（`user_core.unchanged: true`），证据边界检查通过，记录里没有终端令牌。

- 探针一 [t220_core_restart_probe.py](t220_core_restart_probe.py)，结果 [run-01/run.json](run-01/run.json)：
  ```
  python3 t220_core_restart_probe.py --output <新目录>
  ```
- 探针二 [t220_restart_owner_probe.py](t220_restart_owner_probe.py)，结果 [run-02/run.json](run-02/run.json)：
  ```
  python3 t220_restart_owner_probe.py --output <新目录>
  ```

“终端里的 agent 调 hc”的做法：夹具 HOME 的 `.zshrc` 在每个项目终端里挂一个后台子进程，测试写下触发文件后，它以该终端的环境运行 `herdr-core --json ls`，并带一个只有它才有的标记 `T220_STARTER=terminal-agent`。新 core 的环境，从它新开的一个终端里读出（`hc run --bg`）。

探针一的第一阶段（逐条命令测谁会拉起 core）被 holder 的自动重拉干扰，那一段结论作废，以探针二为准。

## 事实

### 1. 哪些情况会拉起新 core

- **holder 会自己重拉。** holder（`herdr-core hold`，终端进程的父进程）发现 core 不在后，约 3.1 秒后自己起一个 `herdr-core serve`，作为它的子进程。
  - 原 core 是 holder 的父进程时，量到 3.12 秒；
  - 死的是 holder 自己拉起的那个子进程时，量到 3.10 秒。
  - 证据：run-02 `daemon_stopped`、`holder_child_core_killed`。
- holder 拉起的 core 继承 holder 的环境，也就是原 core 的受控环境：私有 `XDG_STATE_HOME`，没有终端身份变量。状态继续写在私有目录，原来的终端照常在。
- **运行中的编排后台不会重拉，也不重连。** 断开后各窗格记 `hc_connection_lost`；在这个后台上再开终端，返回 `orchestration_failed: hc connection closed`。要等后台重启。证据：run-01 `daemon_after_agent_core.shell_start_on_running_daemon`。
- **没有 holder 时，测过的 hc 命令都会拉起 core。** `server status`、`ls`、`get`、`read`、`send`、`wait`、`exec`、`events`、`server start` 九条，都在调用后留下一个新 core。没有 holder、也没有人调用时，3 秒内不会自己出现。证据：run-02 `calls_without_holder`。

### 2. 终端里的客户端能不能抢先

能。后台运行时杀掉 core，并立刻让项目终端里的子进程调 `hc ls`，新 core 由这次调用拉起。新 core 的父进程是 1，带着 `T220_STARTER=terminal-agent`。证据：run-02 `race`；run-01 `agent_first` 是同一结论。

holder 要等约 3 秒，终端里的调用是即时的。所以只要 core 死后的 3 秒内终端里有任何 hc 调用，就是终端先拉起。

### 3. 由终端拉起时，实际拿到的是什么

- **环境是那个终端的。** 新 core 下开的终端里有：
  - 该窗格的 `A2A_TERMINAL`；
  - 该窗格的 `A2A_TERMINAL_TOKEN`：探针核对过，与那个窗格登记的令牌相同，只记了是否相同，没有记令牌本身；
  - agent 自己的标记；
  - 没有私有 XDG。
  证据：run-01 `agent_first.probe_env`，run-02 `race.identity`。
- 后台之后在这个 core 上新开的项目终端，也带着 agent 的标记和启动它时的旧环境标记（`T220_MARKER=initial-daemon`，虽然后台已经以 `restarted-daemon` 重启）。`A2A_TERMINAL` 和令牌被后台显式传入的值覆盖。证据：run-01 `daemon_after_agent_core.new_pane_env`。
- **状态写进用户默认的 XDG 目录。** 终端里还原的是用户自己的 XDG（T-212 的做法），所以这个 core 在 `$HOME/.local/state/herdr-core/enchanted-<uuid>/` 下建了 `core.json`、`terminals.json`、`screens/`。在真实环境里，这就是用户的 `~/.local/state/herdr-core/`。证据：run-01 `agent_first.fixture_home_state`。
- **原来的终端丢了。**
  - 新 core 的登记表是空的，只认识之后新开的终端；
  - 发起调用的那个窗格的 shell 进程随即消失，那次 hc 调用以 129 退出（SIGHUP）；
  - 后台重启后，两个原窗格都记为 `shell_exit_unconfirmed`（`recorded hc terminal identity missing`），再关也关不掉，`shell_close` 返回 `shell_exit_unconfirmed`。
  - 证据：run-02 `race.after_5s`，run-01 `daemon_after_agent_core`。
  - shell 被结束的具体机制没有查到。已知的对照是：同样的杀法，若由 holder 或后台以私有状态目录重拉，终端都还在（run-02 `daemon_stopped`；T-212 第三轮 `round3-crash-green-01` 的 `same_shell_pids`）。

### 4. 编排后台现在怎么判断 core 是不是自己的

`workbench/src/hc.ts` 的 `HcRuntime.start()` 用 `server start` 拿到 core 的 pid，要求它的父进程是 1，且不在后台的进程组里。实测这个判断正好放反了：

- holder 拉起的 core（受控环境，父进程是 holder）被拒，报 `private hc core did not detach`，后台直接退出、起不来。core 崩溃后超过约 3 秒才启动后台，就会这样。证据：run-02 `daemon_start_on_holder_core`。
- 终端拉起的 core（外来环境，父进程是 1）被接受，后台在它上面照常开终端。证据：run-01 `daemon_after_agent_core.restart`。

T-212 第三轮的崩溃绿态之所以通过，是因为后台在 holder 重拉之前就重启并自己拉起了 core。

### 5. 崩溃后屏幕标为 inexact

这一点核对的是 T-212 已有的行为，没有新增实测：后台能接回的窗格记 `shell_screen_inexact`，状态里 `screen: inexact`，照常复位并接回；界面没有“历史不完整”的提示。终端由外来 core 拉起时，原窗格接不回，连 inexact 都到不了，见上面第 3 点。

## 待用户定（执行主控建议）

1. **终端里不带私有 core 的地址。** 项目终端启动时，像现在处理 XDG 那样，去掉 `HC_SOCKET`、`HC_SESSION`、`HC_TERMINAL_ID`。这样终端里的任何 hc 调用都碰不到私有 core，上面第 2、3 点的抢先、令牌外泄、状态写进用户目录、原终端丢失就都不会发生。
   - 依据：产品代码里只有 `hc.ts` 用这些变量，没有功能需要终端连到私有 core。
   - 代价：用户或 agent 在 Enchanted 终端里敲 `hc`，用的是用户自己的 hc 设置，和在别的终端里一样，看不到 Enchanted 的终端。
2. **后台按身份认 core，并在断开后自己接回。**
   - 后台起来时，以及断开后，先等 holder 重拉，或用受控环境自己拉起；认的依据从“父进程是 1”改为“是这个私有会话、写在私有状态目录里的 core”，具体判据在建造票里实测后定。
   - 接回后窗格标 inexact，照常复位。
   - 认不出的 core 不接受，停下并显示原因，不在上面开终端。
   - 这同时修掉“崩溃 3 秒后后台起不来”的缺陷。
3. **界面。** 标 inexact 的窗格显示“历史不完整”的提示；后台对 inexact 的屏幕照常复位并接回，不改。

第 1、2 条可以各开一张建造票，第 2 条先做，因为它是后台起不来的缺陷。
