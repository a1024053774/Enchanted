> 审查员：agy 1.4.8，`gemini-3.8-flash-high`，`--mode auto`，审查目录 `/private/tmp/t194-review8` 设为只读，只用文件工具。原文取自 agy 本次会话记录的最终回复；账号邮箱已删。审查对象 `6a42b22`。

# T-194 独立只读审查报告（第 8 轮）

## STATUS

**PASS**。

第 7 轮指出的判据缺陷 **R7-F1**（`leaves` 允许任意相异字符串建立别名映射）已在 [test_t194_mcp_entry_e2e.py](file:///private/tmp/t194-review8/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L264-L283) 中彻底修复并闭环。新判据引入局部模板掩码函数 `masked`，仅放行重新验收中合法的四类外生差异（UUID、40 位 Commit 哈希、ISO UTC 时间戳、验证临时工作区序号 `-verify-N`），且保留全局双射约束；反例 `recheck_other_check` 经同一夹具离线重放实证确认：旧判据确实误放（漏报），新判据可靠拒绝。

整票复核确认：生产代码自第 3 轮定向修复后保持零修改，第 7 轮关于统一入口门禁、角色生命周期闭环（EOF / EPIPE / AbortSignal）、各 CLI 零全局配置污染以及无静默吞异常的架构结论依然完全成立；三项 Acceptance 证据链完整闭环，涵盖 25 项全量反例拒绝及多项已知坏实现的变异与红态验证。

*(注：依据 BRIEF.md 指令，本轮为纯只读审查，未执行 shell 命令，现场动态执行边界详见 [LIMITATIONS](#limitations)。)*

---

## FINDINGS

### 前轮遗留项复核

#### R7-F1 · `leaves` 允许任意相异字符串建立别名映射 · [已关闭 / PASS]

- **问题位置**：[test_t194_mcp_entry_e2e.py:264-283](file:///private/tmp/t194-review8/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L264-L283)。
- **机制与反例复核**：
  - **第 7 轮缺陷机理**：原 `leaves` 在递归遍历字符串叶子节点时，只要 `first != second` 便直接加入 `pairs.append((second, first))` 并无条件返回 `True`。虽然有 `len(aliases) != len(set(pairs))` 检查双射，但若重验链中被篡改的字符串在整个区间仅出现一次（孤立语义字符串），该相异文本便会被作为合法别名吸收，导致重验链被误判一致并予以剥离。
  - **候选修复实现**（提交 `6a42b22`，见 [T-194-since-review7.diff](file:///private/tmp/t194-review8/T-194-since-review7.diff#L9-L31)）：
    ```python
    def masked(value):
        value = time_form.sub('<time>', commit_form.sub('<commit>', uuid_form.sub('<id>', value)))
        return re.sub(r'-verify-\d+(?=/|$)', '-verify-<n>', value)  # the verification workspace carries the run's ordinal

    def leaves(first, second, ignore, pairs):
        ...
        if isinstance(first, str) and isinstance(second, str):
            if first == second:
                return True
            pairs.append((second, first))
            return masked(first) == masked(second)
        return first == second
    ```
    当两个字符串相异时，必须满足 `masked(first) == masked(second)`，否则直接返回 `False` 拒绝匹配。
  - **`masked` 宽严边界评估**：
    - **未见“过宽”**：`uuid_form`、`commit_form`、`time_form` 均为标准格式正则（8-4-4-4-12 UUID、40 位 SHA-1 哈希、以 `Z` 结尾的 ISO 时间戳），`-verify-\d+` 仅匹配带序号的临时验证工作区后缀。字符串中除这四类标识外的所有语义文本（如命令名、参数、脚本名、错误原因、断言文字、工作区根目录相对结构等）完全保留，必须字面完全一致；且收集到的 `pairs` 依然受到后续的一对一双射与跨记录还原校验。
    - **未见“过严”**：在因工作分支前移而合法触发的二次重新验收中，天然发生变化的正是新验收 ID（UUID）、二次运行时间戳（ISO 时间）、主分支前移后的合并候选提交 SHA（40 位 Commit）以及验证临时目录序号（`-verify-1` → `-verify-2`）。基线端到端测试 [green-20-v7test.json](file:///private/tmp/t194-review8/evidence/green-20-v7test.json#L2) 中真实发生的二次重验完整通过，证明未对正常重验产生任何误拒。
  - **反例 `recheck_other_check` 验证**：
    - 反例代码位于 [test_t194_mcp_entry_e2e.py:469](file:///private/tmp/t194-review8/candidate/workbench/tests/test_t194_mcp_entry_e2e.py#L469)：
      ```python
      recheck_other_check=compare(edited(base_rows, 'completion_check', ['result', 'argv'], lambda argv: argv[:-1] + ['check_other.py'], 1))
      ```
      该反例仅篡改重新验收（occurrence 1）中的 `completion_check` 执行脚本为 `check_other.py`。
    - 在 [r7f1-replay.txt](file:///private/tmp/t194-review8/evidence/r7f1-replay.txt#L1-L9) 的同一夹具离线重放中：
      - **旧判据**：输出 `'recheck_other_check': True`（`same_records` 判定两入口一致，即**放过了篡改**，存在漏判漏洞）。
      - **新判据**：输出 `'recheck_other_check': False`（`same_records` 判定不一致，即**成功拒绝篡改**）。
      - 其余 24 个反例在新旧判据下均保持为 `False`。
    - **结论**：事实证明 `recheck_other_check` 确实只有旧判据会放过，新判据已可靠拦截，R7-F1 彻底关闭。

---

### 本轮新发现

本轮静态审查未发现新的生产代码或测试代码缺陷。

---

## EVIDENCE

### 一、 三项 Acceptance 证据复核

| Acceptance 验收项 | 判定 | 依据与证据边界 |
| --- | --- | --- |
| 1. 四家 CLI 的 MCP 支持实测记录 | **PASS** | 候选事实文档 [findings/2026-10-27-mcp-per-session.zh-CN.md](file:///private/tmp/t194-review8/candidate/findings/2026-10-27-mcp-per-session.zh-CN.md#L1-L52) 详尽记录了 Claude Code 2.1.311、Codex 0.164.0、opencode v2.1.4、agy 1.4.8 四家的会话级挂载方式、会话号提取机制及交互模式实测结果；[real-05-cand3.json](file:///private/tmp/t194-review8/evidence/summaries.json#L874) 记录了 Codex 与 opencode 真实 CLI 在隔离目录下的测试全通；[real-03-opencode-agy.json](file:///private/tmp/t194-review8/evidence/summaries.json#L841) 复现了 agy 交互模式无法调用工作区 MCP 工具的现象；[real-red-b6c2600.json](file:///private/tmp/t194-review8/evidence/summaries.json#L892) 证明了无包装时 CLI 角色申请超时的红态。 |
| 2. 至少一家经 MCP 走通完整链（申请主控 → 建卡 → 派发 → 交付 → 审查 → 集成） | **PASS**（历史运行全绿；本轮只读未复跑） | [green-20-v7test.json](file:///private/tmp/t194-review8/evidence/green-20-v7test.json#L1-L21) 记录了最新候选提交 `6a42b22` 在真实后台、真实 PTY、真实 Unix socket、SQLite 数据库及本地脚本化 Claude Code 环境下的端到端运行：9 项 checks 全部通过，主控通过 MCP 工具依次完成 `card_template`、`card_save`、`create`、`dispatch`、`verify`、`integrate`，主分支成功合入提交并生成目标文件 `a.txt`，任务达成 `accepted`。本轮只读审查未做现场重跑，见 LIMITATIONS。 |
| 3. 同一操作经 MCP 与经 a2a 命令，门禁记录一致 | **PASS** | T-1（全走 MCP 工具）与 T-2（全走 `a2a call` 命令）落库的事件序列（7 类核心事件）、主控终端归属（`parent_launch` 均指向主控终端）及打分记录 `data`（6 字段）与 `facts` 经规范化比对完全一致；在 [green-20-v7test.json](file:///private/tmp/t194-review8/evidence/green-20-v7test.json#L434-L460) 中，**25 项差异反例全部被拒**（`refusals` 全部为 `false`），且新反例 `recheck_other_check` 经离线重放实证证明了判据强度的有效提升。 |

---

### 二、 整票架构与系统设计复核

生产代码自第 3 轮审查后未再做任何变更（详见 [T-194.diff](file:///private/tmp/t194-review8/T-194.diff#L1-L1254) 与 [T-194-since-review7.diff](file:///private/tmp/t194-review8/T-194-since-review7.diff#L1-L42)）：

1. **统一门禁与浅层协议转接（Deep modules）**：
   - [`terminalCli.ts:115`](file:///private/tmp/t194-review8/candidate/workbench/src/terminalCli.ts#L115) 将 `send` 统一定义为 `requestAt(socket, input, identity, undefined, signal)`。
   - [`terminalMcp.ts:87-91`](file:///private/tmp/t194-review8/candidate/workbench/src/terminalMcp.ts#L87-L91) 将各 MCP 工具参数映射为 `{ ...args, command: tool.command }` 并直接透传给 `send`；`request_role` 直接调用与命令行一致的 `requestRole`（完成 `role_request` 与 `role_request_confirm`）。MCP 层无任何权限状态机或平行业务校验。
2. **生命周期与传输闭环**：
   - **输入 EOF**：[`terminalMcp.ts:96`](file:///private/tmp/t194-review8/candidate/workbench/src/terminalMcp.ts#L96) 在 `input.on("close")` 时置 `open = false`，对所有在途请求执行 `AbortController.abort()`，并触发后台 `asker.gone` 撤回待批申请。
   - **输出异常（EPIPE）**：[`terminalMcp.ts:99-102`](file:///private/tmp/t194-review8/candidate/workbench/src/terminalMcp.ts#L99-L102) 严格只捕获 stdout 的 `EPIPE` 错误并正常结束会话，非 `EPIPE` 错误原样 `throw error`，杜绝异常吞没。
   - **连接层销毁**：[`transport.ts:29-31`](file:///private/tmp/t194-review8/candidate/workbench/src/transport.ts#L29-L31) 拦截已中止信号不予建连，并在收到 `abort` 事件时立即 `socket.destroy(...)`。
3. **零全局配置污染**：
   - Claude Code 经插件 [`plugin.json`](file:///private/tmp/t194-review8/candidate/workbench/terminal/plugin/enchanted-a2a/.claude-plugin/plugin.json#L1) 的 `--plugin-dir` 临时加载，不写 `~/.claude`。
   - Codex 经包装脚本 [`bin/codex`](file:///private/tmp/t194-review8/candidate/workbench/terminal/bin/codex#L16-L21) 传入 `-c mcp_servers.enchanted...` 参数，不写 `~/.codex/config.toml`。
   - opencode 经包装脚本 [`bin/opencode`](file:///private/tmp/t194-review8/candidate/workbench/terminal/bin/opencode#L18-L21) 注入 `OPENCODE_CONFIG_CONTENT` 配合 `--standalone` 启动，不修改用户配置。
   - agy 包装脚本 [`bin/agy`](file:///private/tmp/t194-review8/candidate/workbench/terminal/bin/agy#L6-L13) 明确不挂载 MCP，继续保持使用 `a2a` 命令，不向 `~/.gemini` 产生缓存写入。
4. **异常流与防御设计**：
   - [`terminalMcp.ts:125`](file:///private/tmp/t194-review8/candidate/workbench/src/terminalMcp.ts#L125) 捕获工具调用异常后返回 `outcome_unknown` 与 `isError: true`，无自动重试、无兜底逻辑。

---

### 三、 测试充分性、红态与变异验证

1. **测试预期来源独立性**：
   - 门禁事件序列、评分契约与状态机流转直接以 [T-194](file:///private/tmp/t194-review8/T-194-mcp-dispatch-entry.md) 与 [T-189](file:///private/tmp/t194-review8/T-189-real-use-fixes-decisions.md) 的预定契约为依据，直接核验底层 SQLite 事件表与 Git 提交树，而非来自实现自身的输出镜像。
2. **红态测试验证**：
   - `red-bf16c21-v6test.json`：父提交上运行，精准失败在第 488 行断言 `主控没有 Enchanted 的 MCP 工具`。
   - `lifecycle-red-494d859.json`：第 1 轮候选上运行，精准失败在 `超时：关闭输入后申请撤回`。
   - `lifecycle-red-a6c65f7.json`：第 2 轮候选上运行，精准失败在 `eof_ends_quietly`（stdout 触发未处理 EPIPE）。
   - `real-red-b6c2600.json`：无 MCP 包装脚本的真实 CLI 运行，精准在等待 MCP 角色申请处超时。
3. **变异测试验证**：
   - `mutant-grant-not-confirmed-v6test.json`（未确认角色）：精准失败在断言 `mcp_role_takes_effect`。
   - `mutant-session-not-reported-v6test.json`（未上报原生会话）：精准失败在断言 `mcp_role_carries_cli_and_session`。
   - `lifecycle-mutant-close-keeps-calls-02.json`（关闭输入未中止在途调用）：精准失败在断言 `eof_withdraws_pending_request`。
   - `lifecycle-mutant-aborted-still-sent-03.json`（已取消仍发 socket 连接）：精准失败在断言 `aborted_request_not_sent`。
   - `lifecycle-mutant-writes-after-close.json`（关闭后仍写输出）：精准失败在断言 `eof_ends_quietly`。
   - `lifecycle-mutant-stdout-error-unhandled.json`（未处理 stdout 错误）：精准失败在断言 `output_closed_ends_quietly`。

---

## LIMITATIONS

1. **只读审查与动态执行边界**：依据 BRIEF.md 指令，本轮审查为纯只读模式，未执行任何 shell 命令。全流程端到端通过结论依据静态源码审查、diff 分析及归档运行产物（[green-20-v7test.json](file:///private/tmp/t194-review8/evidence/green-20-v7test.json)、[r7f1-replay.txt](file:///private/tmp/t194-review8/evidence/r7f1-replay.txt)、[summaries.json](file:///private/tmp/t194-review8/evidence/summaries.json)），本报告未把“当前环境现场端到端复跑”推断为通过。
2. **脚本化模型仿真边界**：端到端测试中使用本地脚本化 Messages 接口模拟模型行为，证明了真实 CLI、MCP 管道、Unix socket、门禁状态机与 SQLite 的联动编排正确性，不构成对真实 LLM 语义理解、自然语言指令遵循或生产推理稳定性的证明。
3. **CLI 版本覆盖范围**：实测记录与包装脚本验证严格限定于 Claude Code 2.1.311、Codex 0.164.0、opencode v2.1.4、agy 1.4.8，不推断未测试版本或其他第三方 CLI 的行为。
