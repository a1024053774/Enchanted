# 独立代码审查报告：T-126 候选 1（提交 `35cadc44b`）

- **审查对象**：提交 [`35cadc44b`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t126-jkbX/candidate-1.diff)（父提交 `04d632694`）
- **需求依据**：[.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md)（来源 [T-125](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-125-operator-credential-storage.md) 用户决议 A）
- **证据比对**：[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-1/RESULTS.md)、[t126drive.mjs](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/packaged/t126drive.mjs) 与归档清单
- **审查模式**：只读独立审查，未运行任何 shell 命令或文件写入。

---

## 重点审查逐项核实

### 1. 专用 Socket（[`workbench/src/daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L645-L735)）

- **是否有路径让终端在专用 socket 上以操作员或窗口身份行事**：**否**。
  - 在 [`daemon.ts#L679`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L679)：`if (terminalOnly && envelope?.identity?.kind !== "terminal") throw new Refusal("terminal_socket_terminal_only");`。
  - 即使调用方传入 `{ kind: "terminal", launch, token }`，请求进入 [`daemon.ts#L276`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L276) 后直接分流至 `terminalCommand`，绝不会穿透到后方的操作员分支（如 `role_request_decide`、`project_open`、`daemon_stop`）或窗口分支（如 `window_*`）。
  - 若终端试图调用 `role_request_decide`，由于该命令不在门禁任务命令集（`taskCommands`）中，在未批准角色时抛出 `approved_role_required`，在已有角色时抛出 `role_command_not_scoped`，均被拒绝并持久化拒绝事件。
- **拒绝是否在认证之前**：**是**。
  - 第 679 行在第 680 行 `authenticate(envelope.identity)` 之前执行。非终端身份直接抛出 `terminal_socket_terminal_only`，不会执行身份校验，攻击者无法借此探测操作员凭据或窗口令牌的存在性。
- **启动、关闭、异常退出时 socket 与目录的创建和清理**：
  - **正常停机（`daemon_stop`）**：在 [`shutdown()`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L146-L150) 中关闭 `terminalServer`、删除 `terminalSocket` 并 `rmdirSync(terminalDirectory)`，清理路径完整。
  - **启动失败与异常退出**：**存在资源泄漏边界**（详见发现项 1 与发现项 2）。
- **`panes.terminalSocket` 未就绪时启动终端**：
  - [`workbench/src/panes.ts#L219`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L219) 执行 `check(this.terminalSocket, "terminal_socket_unavailable");`，未设置或为空时立即阻断，不会产生缺少安全环境变量的裸终端。
- **后台重启后已有终端的 `A2A_TERMINAL_SOCKET` 是否失效、恢复路径是否受影响**：
  - **失效性**：旧终端的 `A2A_TERMINAL_SOCKET` 必定失效（指向已被旧后台删除的临时路径）。
  - **恢复路径**：**不受影响，符合既有设计合同**。根据 [`panes.ts#L426-L441`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L426-L441) 与 [README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L19)，普通终端（`role: "shell"`）设计上就不跨后台重启恢复交互。后台重启时，`panes.recover` 会将旧 shell 登记为 `shell_closed`（未退出则记 `shell_exit_unconfirmed`），前端以只读显示已结束，符合原始合同。

### 2. 终端环境（[`workbench/src/panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L216-L248) `startShell`）

- **是否还有变量泄漏数据目录或凭据路径**：**否**。
  - 第 221-224 行先拷贝 `process.env`，并强制删除所有以 `A2A_` 开头的变量（彻底抹除后台进程可能携带的 `A2A_STATE` 与 `A2A_OPERATOR_CREDENTIAL`），同时抹除 `GIT_CONFIG_`、`ELECTRON_RUN_AS_NODE` 与代理会话标记。
  - 后续显式加入的变量：`ZDOTDIR`、`A2A_TERMINAL_BIN`、`A2A_TERMINAL_PLUGIN`、`A2A_TERMINAL_CLI`、`A2A_NODE` 均指向应用安装或源码目录，`A2A_TERMINAL_SOCKET` 指向隔离的 `/tmp/enchanted-XXXXXX/terminal.sock`，未混入后台 `state` 或凭据目录。
  - 端到端测试与打包驱动中针对环境变量的扫描验证均确认泄漏项列表为空。

### 3. 凭据位置与迁移（[`workbench/src/desktopCredentials.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/desktopCredentials.ts)、[`workbench/app/desktop.mjs`](file:///Users/luckye/Documents/Code/a2a/workbench/app/desktop.mjs)）

- **迁移顺序是否可能丢掉正在使用的凭据**：**否**。
  - 先复制凭据内容到新文件并写入新描述文件，再清理旧文件。运行中的后台在启动时已将 token/epoch 读入内存，不依赖磁盘原文件；新应用连上后提交相同 token/epoch，保持无缝认证。
- **中断后能否续做**：**能**。
  - 若在写入新描述文件前中断，下次启动检测到新描述文件不存在，重新执行复制与迁移；
  - 若在新描述文件写入后、旧文件删除前中断，下次启动检测到新描述文件已就绪，跳过复制直接执行旧凭据文件的兜底清理，具有完整的幂等性。
- **描述文件校验**：
  - [`desktopCredentials.ts#L21`](file:///Users/luckye/Documents/Code/a2a/workbench/src/desktopCredentials.ts#L21) 校验 `dirname(credential) === directory` 并用正则严格校验文件名格式 `/^desktop-operator-[0-9a-f-]{36}\.json$/`，杜绝目录穿越或指向外来文件。
- **文件与目录权限**：
  - 凭据目录显式通过 `mkdirSync(0o700)` + `chmodSync(0o700)` 设定，规避进程 umask 影响；
  - 凭据文件与描述文件均以 `0o600` 模式写入，且由 [`credentials.ts#L27`](file:///Users/luckye/Documents/Code/a2a/workbench/src/credentials.ts#L27) 进行 `(mode & 0o077) === 0` 严格校验。
- **`desktopConnection` 抛错时应用的行为**：
  - 在 [`desktop.mjs#L76-L80`](file:///Users/luckye/Documents/Code/a2a/workbench/app/desktop.mjs#L76-L80)，未捕获的描述文件异常直接进入 `start().catch(...)`，触发 `dialog.showErrorBox` 并 `app.exit(1)` 退出。未出现异常吞噬或静默降级，符合 fail-closed 原则。

### 4. 测试独立性与 RESULTS.md 真实性

- **独立性**：单元测试 [`test_t126_desktop_credentials.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t126_desktop_credentials.ts) 独立构造旧安装布局，测试期望来自规格；源码端到端 [`test_t126_terminal_socket_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t126_terminal_socket_e2e.py) 走真实 zsh、CLI、node-pty 与独立攻击脚本；打包测试 [`t126drive.mjs`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/packaged/t126drive.mjs) 经 CDP 黑盒模拟用户操作。
- **变异能行性**：
  - 单元测试跑 5 个变异体全部退出 1 并在目标断言精准失败；
  - 源码端到端跑父版本（`04d632694`）与 3 个变异体（`socket-accepts-all`、`state-exported`、`refusal-unmarked`）均退出 1 并命中指定检查；
  - 打包驱动第 1 阶段真实证明修前版本会暴露 `A2A_STATE`。
- **RESULTS.md 真实性**：
  - 回核 [`evidence/2026-10-22-batch20/T-126/candidate-1/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-1/) 下的 `unit/exits.txt`、`e2e/exits.txt`、`e2e/*.json` 与 `packaged/packaged-01.run.json`，数据与通过项数完全一致，已知未验证边界表述客观，无夸大或矛盾。

---

## 审查发现项

### [P2] [`workbench/src/daemon.ts#L726-L734`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L726-L734)：后台启动失败时临时 socket 目录泄漏

- **具体失败场景**：
  在 `daemon.ts` 的 `serve()` 函数中：
  ```ts
  const terminalDirectory = mkdtempSync(join(tmpdir(), "enchanted-"));
  const terminalSocket = join(terminalDirectory, "terminal.sock");
  if (Buffer.byteLength(terminalSocket) > 103) throw new Error("terminal socket path exceeds 103 bytes");
  await new Promise<void>((resolve, reject) => { terminalServer.once("error", reject); terminalServer.listen(terminalSocket, resolve); });
  chmodSync(terminalSocket, 0o600);
  panes.terminalSocket = terminalSocket;
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(socket, resolve); });
  chmodSync(socket, 0o600);
  writeFileSync(join(root, "daemon.pid"), String(process.pid) + "\n", { flag: "wx", mode: 0o600 });
  ```
  如果步骤在第 726 行之后失败（例如：路径超长检查抛错、`server.listen(socket)` 因旧 `control.sock` 占用失败、或 `daemon.pid` 因已有 PID 锁以 `wx` 写入抛错），`serve()` 没有 `try...finally` 结构清理已创建的 `terminalDirectory`。
  由于 `terminalDirectory` 位于系统临时目录且随机命名，其路径未持久化到数据目录中，后续的 `startDaemon()` 只能检测并清理 `control.sock` 和 `daemon.pid`，无法感知也无法清理遗留在 `/tmp/` 下的 `enchanted-XXXXXX` 目录与套接字，造成孤立文件残留。
- **建议**：
  在 `serve()` 的套接字绑定与 PID 写入阶段包裹 `try...catch`，若未能完全就绪，在抛出错误前执行清理：
  ```ts
  try {
    // 监听与 PID 写入
  } catch (error) {
    if (existsSync(terminalSocket)) unlinkSync(terminalSocket);
    try { rmdirSync(terminalDirectory); } catch {}
    throw error;
  }
  ```

### [P3] [`workbench/src/desktopCredentials.ts#L26-L36`](file:///Users/luckye/Documents/Code/a2a/workbench/src/desktopCredentials.ts#L26-L36)：新凭据目录中历史操作员凭据持续累积不清理

- **具体失败场景**：
  每次后台停机后再由桌面应用启动新后台时，[`desktop.mjs#L68`](file:///Users/luckye/Documents/Code/a2a/workbench/app/desktop.mjs#L68) 会调用 `newDesktopCredential(credentials)` 生成一个新的 `desktop-operator-<UUID>.json`，并通过 `saveDesktopConnection` 覆盖更新 `desktop-connection.json`。
  [`migrateDesktopCredential`](file:///Users/luckye/Documents/Code/a2a/workbench/src/desktopCredentials.ts#L49) 仅负责清理了旧数据目录（`state`）中的历史凭据，但没有清理新凭据目录（`~/Library/Application Support/Enchanted/`）中的失效旧凭据。虽然这些文件权限为 0600 且位于 0700 目录中，但长期使用和多次重启会导致该目录下残留大量无用的历史凭据文件。
- **建议**：
  在 `saveDesktopConnection` 写入新描述文件后，清理 `credentials` 目录下所有名称匹配 `credentialName` 但不等于当前生效文件的历史凭据文件。

### [P3] [`workbench/src/daemon.ts#L146-L153`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L146-L153)：`shutdown` 过程中 server close 异常可能阻断后续文件删除

- **具体失败场景**：
  在 `shutdown()` 中：
  ```ts
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  await new Promise<void>((resolve, reject) => terminalServer.close((error) => error ? reject(error) : resolve()));
  gates.close(); store.close();
  if (existsSync(terminalSocket)) unlinkSync(terminalSocket);
  rmdirSync(terminalDirectory);
  if (existsSync(socket)) unlinkSync(socket);
  unlinkSync(join(root, "daemon.pid"));
  ```
  如果 `server.close` 或 `terminalServer.close` 出现异常导致 Promise reject，后续的套接字删除（`unlinkSync`）和 `rmdirSync` 以及 `daemon.pid` 的删除将被短路跳过。
- **建议**：
  将套接字与 PID 文件的物理清理放入 `try...finally` 块中，确保即使网络层 close 出现异常，本地文件系统端点仍能尽力清除。

---

## 总体结论

### **PASS**

**判定理由**：
1. 提交 `35cadc44b` 完整且严谨地达成了 [T-126](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md) 规定的全部验收条件：项目终端与专用 socket 完全隔离于后台数据目录和操作员凭据之外；非终端身份在认证前即被阻断；拒绝事件带 socket 标识且审计完整；旧版本平滑迁移且具有幂等中断续做能力。
2. 单元测试、隔离源码端到端、CDP 驱动的打包真实运行证据链条闭合完备，且经变异体与修前基线充分证伪；[RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-1/RESULTS.md) 记录真实严谨。
3. 发现的 P2/P3 问题属于极端启动异常及长期历史文件垃圾回收的稳健性优化项，不破坏主干功能与安全隔离边界，无需阻断候选采纳。
