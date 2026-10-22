作为独立审查者，已完成对提交 `28a0550cc`（父提交 `b25d44045`）及对应代码差异、需求契约 [`T-124-terminal-controller-answers-attach-run.md`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-124-terminal-controller-answers-attach-run.md) 与验收结果 [`RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-124/RESULTS.md) 的逐项审查。审查过程仅使用只读工具，未执行任何命令或修改任何文件。

---

### 一、重点审查项分析

#### 1. 正确性核对
- **终端主控回答记为主控而非用户输入**：
  在 [`core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L597-L647) 中，门禁通过 `actor?.controller` 识别调用者为终端主控；若是主控回答，写入的记录标记 `from: controller.role`，关联 `controller-launch` 与 `role-request`，并发出 `controller_answer` 事件；显式跳过了 `recordUserInput` 与 `human_intervention` 事件；下发给 worker 的消息被显式标注为“主控答复”，在 [`panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L973) 中派发来源记为 `executor`，在 [`store.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/store.ts#L1190) 中格式化为 `⟦主控 #n⟧`。界面（管理凭据）回答仍走原用户输入路径，记录为 `⟦用户 #n⟧` 并触发 `human_intervention`。变异测试 `mutant-01-answer-as-user` 准确捕获了走用户路径的坏实现。
- **run 在主控身份结束或额度用完后经门禁未评分集成，主控在时仍等主控打分**：
  在 [`core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2759-L2772) 中，任务进入 `verified` 且无 `repair` 时核对 `initiatorState = controller?.state()`。主控处于 `active` 时，状态维持在 `waiting_executor`，等待主控带分打分；一旦主控身份 `ended` 或 `quota_exhausted`，run 登记 `run_initiator_ended` 并经门禁发起集成；在 [`core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3828) 中，无评分文件时生成 `{ result: "未评分", reason: "主控身份已结束" | "主控额度用完" }`，并在 [`qualityProtocol.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/qualityProtocol.ts#L102-L105) 中严格校验此格式。变异测试 `mutant-02-run-waits-for-score`、`mutant-03-run-ignores-active`、`mutant-04-unscored-without-reason` 均证明该逻辑能区分坏实现。
- **身份结束后新派发/run/attach 被拒**：
  终端释放身份或关闭后，[`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L238-L239) 的 `roleRequests.approved(terminal.id)` 返回空，对后续请求直接拒绝并抛出 `approved_role_required`，记录入 `request_rejected` 事件。
- **monitor 只读**：
  在 [`panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L927-L945) 中，Codex monitor 启用 `--sandbox read-only`，工作目录设为独立空目录 `monitors/<thread>`；Claude Code monitor 启用 `--permission-mode dontAsk`，且 `permissions.allow` 中不注入任何 `Edit(...)` 权限，`sandbox.filesystem.allowWrite` 设为空数组，且 `allowUnsandboxedCommands: false`。测试在 `monitor_reads_but_cannot_write` 中通过真实的写入尝试（退出码 1 且目标文件未生成）验证了只读屏障。
- **门禁锁、attempt 绑定、fence 不被绕过**：
  自动 run 在各阶段（dispatch、verify、integrate、reclaim）均走统一的 `request()` 入口，执行前获取 SQLite 排他操作锁 [`operationLock`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3357)，核对 `current_attempt`、`attempt.fence` 与评审基线。

#### 2. 安全边界审查：`processSnapshot.py` 对 `PROC_PIDT_SHORTBSDINFO` 的回落
- 在 [`processSnapshot.py`](file:///Users/luckye/Documents/Code/a2a/workbench/src/processSnapshot.py#L48-L65) 中：
  1. 仅当 `size == 0 and number == errno.EPERM` 时进入 `privileged(pid)`。
  2. 若 `info.uid == os.geteuid()`（属于本用户的进程被拒），仍立即抛出 `QueryError('proc_pidinfo_denied_same_user', errno.EPERM, pid)`，**同用户进程绝不回落放行**。
  3. 只有当进程属于其他用户（如 Claude Code 在其进程树中以 setuid-root 启动的 `/bin/ps`，其有效 UID 为 0）时，才回落至 `ShortInfo`。
  4. 对于 `ShortInfo` 进程，第 86 行强制硬编码其前台进程组 `'tpgid': -1`。
  5. 在 [`panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L871) 中，前台 leader 判定条件为 `row.pid === row.pgid && row.pgid === row.tpgid && row.command === pane.record.executable_path`。由于 PID 必大于 0，而 privileged 进程的 `tpgid` 为 -1，**该类进程在数学上永远不可能被判定为 CLI leader**。
  6. 进程树仍由内核 `proc_listpids` 的 `ppid` 严格串联，任意伪造父子关系或进程身份在前后两次快照中变更（包含 `identity` 字段比对）均会抛出 `process_identity_changed_during_query`。
  **结论**：`PROC_PIDT_SHORTBSDINFO` 回落不会导致被伪造或替换的进程通过身份核对或冒充 leader。

#### 3. 测试独立性核对
- [`test_t124_controller_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t124_controller_e2e.py) 中的断言不是用实现自报的输出充当预期：
  - monitor 只读性检查通过实际执行 shell 写操作并断言退出码为 1，且直接用 Python `pathlib.Path.exists()` 检查磁盘上未产生文件。
  - run 集成检查直接通过外部 `git ls-tree refs/heads/main` 命令断言分支中落入的目标文件。
  - 用户与主控回答区分断言分别检查了 `user_inputs` 计数是否保持不变、`human_intervention` 事件是否未发出、实际下发给模型的输入是否出现“主控答复”而非“用户答复”。
  - 构造了 9 个代码变异体与父提交基线，各个变异体分别在预期的判定点红态中断，证明了测试套件对错误实现的敏感性与区分度。

#### 4. RESULTS.md 真实性与客观性核对
- 检查了 `evidence/2026-10-22-batch20/T-124/e2e/` 与 `unit/` 下的所有运行结果 JSON 清单及 `exits.txt`。
- `green-01-release`（22 项）、`green-02-quota`（20 项）、`green-03-codex-monitor`（22 项）的断言项数与退出码全部与证据文件吻合。
- 报告如实说明了父提交 `red-01-parent` 因没有额度监听在首步退出、因而需由 `mutant-01` 单独证明回答记录的客观事实。
- 报告没有掩饰缺陷或未完成项，明确将原生提问在现有 CLI 权限配置下不可达的情况列为未完成，并将整体结论定为 `INCOMPLETE`。

---

### 二、审查发现列表

#### 发现 1【P1 严重】
- **文件与行号**：[`workbench/src/gates/core.ts#L3532`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3532)、[`workbench/src/gates/core.ts#L3541`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3541)
- **具体失败场景**：
  在本次提交中，为避免 monitor 共享仓库目录导致会话记录冲突，attachment 的工作目录被改为独立空目录 `attachment.workspace = join(this.root, "monitors", thread)`。在 [`core.ts#L3518`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3518) 的 reclaim 初检中，代码已正确修改为：
  ```typescript
  live.workspace === (attachment.workspace ?? task.repo) && ...
  ```
  但在随后的回收终止与归档核对代码中，第 3532 行与第 3541 行被遗漏更新，仍写死为：
  ```typescript
  stopped.workspace === task.repo && ... // L3532
  archived.workspace === task.repo && ... // L3541
  ```
  由于 monitor 线程的真实工作目录是 `monitors/<thread>` 而非 `task.repo`，当主控或外部调用 `reclaim` 回收已结束的 monitor 附加会话时，门禁必定会抛出 `Refusal("stop_unconfirmed")` 或 `Refusal("reclaim_unconfirmed")`，导致**所有 monitor 附加会话均无法通过门禁接口被正常 reclaim 回收**。该问题在测试中未暴露，是因为测试只验证了 monitor 在终端关闭后存活，未执行针对 monitor 的 `reclaim` 流程。
- **建议**：
  将第 3532 行与第 3541 行的 `stopped.workspace === task.repo` 和 `archived.workspace === task.repo` 修改为：
  `stopped.workspace === (attachment.workspace ?? task.repo)` 与 `archived.workspace === (attachment.workspace ?? task.repo)`。并在端到端测试中追加回收 monitor 的断言步骤。

#### 发现 2【P2 中等】
- **文件与行号**：[`workbench/src/controllerQuota.ts#L63-L65`](file:///Users/luckye/Documents/Code/a2a/workbench/src/controllerQuota.ts#L63-L65)
- **具体失败场景**：
  在增量读取 CLI 的 jsonl 日志解析额度记录时：
  ```typescript
  for (const line of bytes.subarray(0, end).toString("utf8").split("\n")) {
    const record = JSON.parse(line);
  ```
  如果日志中包含空行（例如某些异常刷盘或空换行分隔），`split("\n")` 会切出空字符串 `""`，调用 `JSON.parse("")` 将直接抛出 `SyntaxError: Unexpected end of JSON input`。而在外层 `tick()` 中：
  ```typescript
  catch (error) {
    if (!reading.failed) this.store.event("controller_quota_unreadable", ...);
    reading.failed = true;
  }
  ```
  一旦抛出异常，`reading.failed` 会被永久置为 `true`，导致该主控会话后续即使写入了有效的额度用完或额度恢复日志，也再也不会被解析处理。
- **建议**：
  在第 64 行循环内增加空行过滤：
  ```typescript
  for (const line of bytes.subarray(0, end).toString("utf8").split("\n")) {
    if (!line.trim()) continue;
    const record = JSON.parse(line);
  ```

#### 发现 3【P3 轻微】
- **文件与行号**：[`workbench/src/gates/cli.ts#L178`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts#L178)
- **具体失败场景**：
  参数校验逻辑中：
  ```typescript
  else if (key === "blocking" || key === "fast") {
    if (value !== "true" && value !== "false") throw new Error("boolean required: blocking");
    request[key] = value === "true";
  }
  ```
  当用户给 `--fast` 传入非法布尔值（如 `--fast 1`）时，错误提示固定输出 `"boolean required: blocking"`，提示信息与传入的参数名不符。
- **建议**：
  修改为 `throw new Error(`boolean required: ${key}`);`。

#### 发现 4【P3 轻微】
- **文件与行号**：[`workbench/tests/test_t124_controller_e2e.py#L1413-L1417`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t124_controller_e2e.py#L1413-L1417)
- **具体失败场景**：
  在 `MUTANTS` 映射定义上方，两个变异体的注释位置颠倒：
  ```python
  # A process of another user in the worker's tree fails the snapshot, as before this ticket.
  # A Codex monitor's session cannot be bound (the resume argv refused its role), as before this ticket's fix.
  'codex-monitor-unbound': ...
  'snapshot-denies-privileged': ...
  ```
  使得快照异常注释出现在了 monitor 变异项上方。
- **建议**：
  调换两行注释顺序以匹配实际变异项。

---

### 三、总体审查结论

**结论**：**INCOMPLETE**

**依据**：
1. 本票验收条件中明确规定的“终端主控回答 worker CLI 自己弹出的提问”在现有原生 CLI 配置模式（Claude Code 的 `dontAsk` 及 Codex 默认模式）下客观发不出来，代码中已按事实撤回相关接口并如实标明待用户裁定，因此本票在需求范围上属于明确的未完成（INCOMPLETE）状态。
2. 发现 1（P1）指出了附加 monitor 会话由于门禁中工作区路径比较遗漏而完全无法执行 `reclaim` 回收的问题，需在集成前予以修复。
3. 除未完成的原生提问与上述回收缺陷外，其余关于主控回答不进用户输入、主控身份结束/额度用完后自动集成未评分、新工作拒绝隔离、monitor 只读沙箱屏障以及独立测试反例等均已得到严密验证且与证据完全吻合。待用户就提问方式裁定并修复回收路径后，方可推进合并。
