# 独立代码审查报告：T-126 候选 2（提交 `87453d496`）

- **审查对象**：提交 [`87453d496`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts)（T-126 候选 2，父提交 `35cadc44b` 为候选 1，基线版本 `04d632694`）
- **需求依据**：[.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md)（来源 [T-125](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-125-operator-credential-storage.md) 用户选 A）
- **对比依据**：上一轮审查报告 [review-01.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-1/review-01.md)、主控处置 [review-01-disposition.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-2/review-01-disposition.md)、[candidate-2/RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-2/RESULTS.md)
- **审查模式**：只读独立审查，未运行任何 shell 命令或修改任何文件。

---

## 重点审查核查

### 1. 上一轮三条发现的处置核查

#### 1.1 P2 修复的正确性与完整性（[`workbench/src/daemon.ts#L728-L740`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L728-L740)）

**核查结论：成立，修复正确且完整。**

- **覆盖范围**：
  在 `daemon.ts` 的 `serve()` 中，临时目录创建之后、正常服务就绪之前的全部可能失败点：
  1. `Buffer.byteLength(terminalSocket) > 103` 路径超长抛错；
  2. `terminalServer.listen(terminalSocket)` 绑定失败；
  3. `chmodSync(terminalSocket, 0o600)` 权限设定失败；
  4. `server.listen(socket)` 主套接字监听失败；
  5. `chmodSync(socket, 0o600)` 设定失败；
  6. `writeFileSync(join(root, "daemon.pid"), ..., { flag: "wx" })` 写入失败（如已有 PID 文件触发 `EEXIST`）。
  以上所有步骤均已完整包裹在 `try { ... } catch (error) { rmSync(terminalDirectory, { recursive: true, force: true }); throw error; }` 中。
- **行为正确性**：
  - 使用 `rmSync(..., { recursive: true, force: true })` 保证无论 `terminalSocket` 是否已创建、目录是否为空，都能一次性递归彻底清理，且不存在因文件缺失导致清理本身二次抛错的问题；
  - 清理完成后通过 `throw error;` 原样将错误向上抛出，由外部的 `import.meta.main` 捕获并 `process.exit(1)`，没有吞噬错误，没有添加无依据的重试；
  - 审查 01 曾提及的“`control.sock` 被占用导致监听失败”场景，经回核代码，在 `serve()` 开头第 40 行（`if (existsSync(socket)) throw new Error("socket exists; refusing to replace it");`）即提前拒绝，此时根本尚未进入 `mkdtempSync`，故处置说明中指出的“实际到不了这段代码”属实。

#### 1.2 新测试的独立性与坏实现区分能力（[`workbench/tests/test_t126_failed_start_cleanup.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t126_failed_start_cleanup.ts)）

**核查结论：成立，测试入口真实、断言独立且能精准区分坏实现。**

- **测试独立性**：
  - 测试直接经 `spawnSync(process.execPath, [join(resolve(source), "daemon.ts"), state, "{}"], ...)` 调起真实的 `daemon.ts` 子进程入口，而不是在单测内存中调用桩函数；
  - 构造了两个真实诱发启动失败的独立场景：
    1. `pid_write_fails`：预先在数据目录写入 `daemon.pid`，触发写 PID 时的 `EEXIST` 失败；
    2. `socket_path_too_long`：将 `TMPDIR` 构造为 70 字符长度的子路径，直接触发真实运行时的套接字路径 103 字节超长校验；
  - 测试的判定依据独立于实现内部逻辑：同时检验了子进程非 0 退出（`run.status !== 0`）、错误信息匹配预期阶段（`run.stderr.includes(expected)`），以及物理临时目录扫描结果（`left === []`）。
- **坏实现区分能力**：
  - 回核 `evidence/2026-10-22-batch20/T-126/candidate-2/unit/cleanup-red-candidate-1.json` 与日志：同一测试运行于候选 1（`35cadc44b`）时，`pid_write_fails` 场景产生 exit 1，精确断言在 `terminal socket directory left behind`，并捕获残留的 `enchanted-hP4T4e` 目录；
  - 运行于候选 2 时，两个场景均 exit 0 通过。该测试确凿证明了候选 1 存在残留缺陷，并证明了候选 2 修复有效。

#### 1.3 两条 P3 不改理由的合理性核查

**核查结论：成立，不改理由站得住。**

1. **P3-1（历史操作员凭据在 Application Support 中持续累积）**：
   - **既有合同吻合**：README 明确记录“凭据目录里以前启动的凭据文件保留”。T-126 的核心目标是“操作员凭据移出终端可见路径”，重点是终端环境抹除 `A2A_STATE`、专用 socket 阻断越权、以及从数据目录中彻底删除旧凭据；并不包含在用户 Application Support 目录中做垃圾回收；
   - **避免非预期副作用**：旧凭据可能仍被手工启动的 CLI 或外部连接持有，未经跨进程生命周期核实盲目清理存在破坏合法会话的外部副作用。符合项目“先做根因层面的最小变更、不做超出票据授权的不可逆操作”原则。
2. **P3-2（`shutdown` 中 `server.close` 异常可能阻断后续文件删除）**：
   - **调用点核查**：在 `daemon.ts` 中，`shutdown()` 的唯一调用点位于第 719 行：
     `if (result.ok && envelope?.input.command === "daemon_stop") { connection.once("close", () => shutdown().catch(...)); }`；
   - **Node.js 网络层语义**：Node.js 原生 `net.Server.prototype.close([cb])` 仅在服务器未处于监听状态（`ERR_SERVER_NOT_RUNNING`）时才会向回调传入错误。既然 `daemon_stop` 请求已被当前 server 成功接收并处理，此时 `server` 与 `terminalServer` 必然处于正常监听状态，`close()` 回调绝不会报错；
   - 此处若增加 `try...finally` 属于无真实故障证据支持的臆想性保险分支，主控拒绝修改符合仓库设计原则。

---

### 2. 修复引入新问题核查

**核查结论：无引入新问题。**

- **成功路径行为**：`try` 块内执行的语句与顺序与候选 1 完全一致，变量绑定（`panes.terminalSocket`）与文件写入（`daemon.pid`）行为未变。
- **错误捕获与透传**：`catch` 块中仅调用 `rmSync`，随后立即 `throw error;`，原样保留原始异常调用栈与错误码，未发生异常吞噬或错误变形。
- **删除范围控制**：`terminalDirectory` 变量是紧邻前一行由 `mkdtempSync(join(tmpdir(), "enchanted-"))` 生成的唯一临时目录，`rmSync` 作用范围严格限定于该临时目录及其内部新生成的 `terminal.sock`，不存在误删其他系统文件或数据目录文件的风险。

---

### 3. RESULTS.md 真实性与重跑合理性核查

**核查结论：真实客观，无夸大或矛盾；未重跑项合理充分。**

- **证据文件与指标核对**：
  - 单元测试：`cleanup-green`（PASS）、`cleanup-red-candidate-1`（FAIL，命中 EEXIST 残留）、`credentials-green`（PASS，9 项），与 `candidate-2/unit/exits.txt` 及各 json 证据完全吻合；
  - 源码端到端：`green-01`（PASS，10 项）、`red-01-parent`（FAIL，命中 `A2A_STATE` 泄漏）、`t121-green`（PASS，49 项）、`t122-green`（PASS，23 项）、`t124-restart-verified`（PASS，26 项），与 `candidate-2/e2e/exits.txt` 及 json 记录完全吻合；
  - 打包端到端：从 `87453d496` 重新打出的 `Enchanted Test.app` 运行 `packaged-01`，经 CDP 黑盒测试 23 项检查全部通过（`candidate-2/packaged/packaged-01.run.json`），证据归档至 `/Volumes/WD-Elements/`，归档清单 `packaged-01.archive.json` 真实完整。
- **候选 2 未重跑项的合理性**：
  - 候选 2 相对候选 1 仅改动了 `daemon.ts` 启动失败分支及 README 说明，主干服务逻辑、安全边界和协议行为零变动；
  - 候选 1 已跑过的 3 个变异测试（`socket-accepts-all`、`state-exported`、`refusal-unmarked`）用于检验测试用例自身的判伪能力，测试套件代码本身未变，无需重复消耗资源变异；
  - 打包端到端真实测试、主测试场景 `green-01`、父版本红态及关联最紧密的终端/恢复回归套件（`t121`、`t122`、`t124`）均已全量重跑并绿态，跳过与启动失败无关的子套件完全符合仓库“测试是当前验收的证据，而非每次编辑后的仪式”准则。

---

### 4. 全量改动审查发现项

对 T-126 相对基线 `04d632694` 的全部改动（`workbench/` 下的 `app/desktop.mjs`、`src/daemon.ts`、`src/desktopCredentials.ts`、`src/panes.ts`、`src/terminalCli.ts`、`src/transport.ts` 及各测试与文档）进行了整体代码复审：

- **P0 发现**：无
- **P1 发现**：无
- **P2 发现**：无
- **P3 发现**：无

---

## 总体结论

### **PASS**

**判定理由**：
1. 候选 2（`87453d496`）对上一轮审查提出的 P2 临时目录残留问题修复严谨、清理边界准确、异常透传完整，且配有真实的端到端入口反例测试；
2. 对两条 P3 建议的处置理由充分，符合 Node.js 原生 API 机制及项目最小充分变更准则；
3. [candidate-2/RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-126/candidate-2/RESULTS.md) 记录真实严谨，未重跑项划分合理，全部证据链条闭合；
4. 全量改动完整达成 [T-126](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-126-operator-credential-out-of-terminal-reach.md) 的安全隔离与功能迁移目标，无遗留问题，准予集成。
