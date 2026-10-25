   Enchanted (a2a) T-184 ready_rev 2 独立审查报告

  本审查为只读审查，针对 T-184 ready_rev 2 候选交付（commit 85ddd951f，起点 main 的改动见 full.diff）。
  ──────
  ## 一、特别核对点核查结论

  ### 1. processArgs.py 读 argv 解析与数据流向

  • 解析正确性（processArgs.py:12-25）：
      • 通过 Darwin 底层 sysctl [CTL_KERN(1), KERN_PROCARGS2(49), pid] 读取进程参数缓冲区。
      • 前 4 字节按系统字节序解出 argc；随后通过查找首个 \0 跳过可执行文件路径（exec_path）并 lstrip(b'\0') 剔除内核补齐的空字节，切入实际的 argv[0]；以 \0
      切分出前 argc 个参数，并用 replace 模式解码 UTF-8。
      • 解析逻辑完全符合 macOS Darwin 内核对 KERN_PROCARGS2 的内存布局规范，实测已稳定读取主控进程的实际启动命令行。
  • 数据流向安全：
      • processArgs.py 输出仅由后台以子进程管道（execFile stdout）在内存中临时接收。
      • panes.ts:104-108 仅将 basename(argv[0]) 作为 command 名、进程 pid 及时间戳暂存于 pane.unwiredCli 对象；向前端广播的快照中仅含 { command, since }。
      • argv 原文既未入库（SQLite 中无任何字段存储），也未进入任何日志或事件记录（包括失败事件 cli_wiring_check_failed
      也仅记录错误类型），完全满足只用于机械判断、不入库不进日志的要求。


  ### 2. terminalClis.ts 判据准确性与误报/漏报分析

  • Claude 判据（terminalClis.ts:200）：
      • 包装脚本 claude:6 采用固定形式：exec "$real" --plugin-dir "$A2A_TERMINAL_PLUGIN" "$@"。
      • 判据为 argv.some((arg, index) => arg === "--plugin-dir" && (argv[index + 1] ?? "").endsWith("/plugin/enchanted-a2a"))。
      • 准确性：包装脚本注入的参数必然作为独立参数紧邻出现且以该路径结尾；正常敲 claude 必命中该判据，判定为 wired，不会误报。若使用绝对路径启动，因缺乏 --
      plugin-dir 插件参数，必判定为 unwired，不会漏报。
  • Codex 判据（terminalClis.ts:202）：
      • 包装脚本 codex:10-14 在启动前用单引号保持环境变量名字面值：hook='{type="command",command="\"$A2A_TERMINAL_BIN/a2a\" hook",timeout=10}'，并经 set --
      -c "hooks.UserPromptSubmit=..." "$@" 压入。
      • 判据为 argv.some(arg => arg.includes('$A2A_TERMINAL_BIN/a2a'))。
      • 准确性：无论用户是否覆盖 developer_instructions，包装脚本附加的 hook 参数必然带有字面量
      $A2A_TERMINAL_BIN/a2a；正常启动必命中判据。绝对路径启动时无此参数，必准确触发警告。
  • 非包装命令隔离：
      • 非包装 CLI（如 vim、node、git 等）在 shimWiring[command] 中查找为 undefined，Boolean(wired) 为 false，直接判定为非 unwired，不产生误报。


  ### 3. panes.ts 检查时机、复查撤下与异常处理

  • 检查时机（panes.ts:86-96）：
      • 用户在终端敲回车（data.includes("\r")）时触发计时 wiringCheckAt = Date.now() + 1500。1.5 秒延时给子进程 fork & exec
      充分的时间就绪，避免读取到仍在执行 shell 重定向或瞬态子进程的 argv。
  • 复查与撤下机制（panes.ts:100-109）：
      • 检出 unwired CLI 后，自动安排 5 秒周期的复查（WIRING_RECHECK_MS = 5000）。
      • 当 CLI 退出回到 shell 时，终端前台进程组组长重置为 pty shell 自身，find 结果 leader 为空，立即执行 pane.unwiredCli =
      null，撤下警告并停止复查定时器。经变异测试 never-clears 验证，该撤下逻辑必不可少且能有效工作。
  • 失败路径与异常策略（panes.ts:110-114）：
      • 在异步定时器上下文中，子进程可能在获取进程列表到调用 sysctl 的极短间隙内退出，导致 sysctl 抛出 ESRCH。
      • catch 块中执行 pane.unwiredCli = null 并记录审计事件 this.store.event("cli_wiring_check_failed", { error: String(error) }, pane.record)。
      • 不算吞异常：
          1. 依据 ticket 与 README 规范，“只依据进程 argv 这一机械事实，读进程失败时不显示提示”；在无确实 argv 证据时不应误报警告；
          2. 明确将失败写入事件存储（this.store.event），证据链完整未灭失；
          3. 避免了未捕获 Promise 异常导致后台主守护进程崩溃。



  ### 4. sidebar.ts 改动影响范围

  • 改动范围（sidebar.ts:206-207, 219）：
      • 执行主控行：
      const state: AgentState = pane?.lifecycle === 'ended' ? 'ended' : pane?.unwired_cli ? 'unknown' : last ?? (roleRequest.cli === 'claude' &&
      roleRequest.native_session ? 'running' : 'unknown');
      • 普通终端行：
      const state: AgentState = pane?.lifecycle === 'ended' ? 'ended' : pane?.unwired_cli ? 'unknown' : pane?.lifecycle === 'running' ? 'running' :
      'unknown';
  • 影响核实：
      • 仅当 pane?.unwired_cli 存在（非 null）时强制赋予 'unknown' 状态。
      • 对所有正常接入的会话（unwired_cli 为 null），三元表达式完全透传执行原逻辑。
      • 不涉及 worker、reviewer、monitor 等其他角色。改动严格局限在未接入的异常终端。


  ### 5. 测试真实度、红态与变异审查

  • 测试期望来源：
      • 期望值来自 ticket 逐字要求（绕过时有提示且状态为 unknown，修前为无提示且 fake running；正常启动无提示；退出后提示撤下），完全独立于被测代码的产出。
  • 红态落在缺陷断言：
      • 审查修前 main 运行产物 summary.json 与截图 red-main-01-bypassed-claude.jpg：
          • 4 项失败明确落在核心缺陷断言：bypassed_claude_warned（修前无提示）、bypassed_claude_state_unknown（修前假状态
          "running"）、bypassed_codex_warned、bypassed_codex_state_unknown。
          • 截图清晰显示修前界面右上角错误展示“运行中”，且窗格内无任何黄色连接警告框。

  • 两个变异的有效性：
      • 变异 name-only（模拟只看进程名不看启动参数）：必导致正常敲 claude/codex 的 N、D 终端误报，被测试拒绝。
      • 变异 never-clears（模拟进程退出后不重置警告）：导致退出后警告残留，被 warning_clears_after_exit 断言拒绝。
  • 角色申请模拟合理性：
      • 测试中终端 B 为绕过包装脚本启动的真实 Claude，因为没有挂载 a2a 插件，内部无法直接调用 a2a skill。
      • 测试以终端 B 的 token 与身份直接向 control.sock 提交 role_request 并由操作者在后台批准，这一调用序列与 terminalCli.ts:98-100 中 a2a request
      executor 的底层通信报文与权限校验完全等价。
      • 该模拟准确将系统推入“实测 L03 人工操作失误导致的假状态现场”，既免除了对外部 LLM API Token
      的不必要消耗，又严格覆盖了真实协议链路，模拟方案完全站得住脚。


  ### 6. RESULTS 如实性与 setup-error

  • RESULTS.md 如实记录了实测中发现的被测代码缺陷：在最初的实现中，Codex 判据由于对双引号转义要求过严而导致正常启动的 Codex 也误报（即 green-02
  所暴露的缺陷），随后修正为只认 $A2A_TERMINAL_BIN/a2a 并通过后续测试。
  • 截图对比（red-main-01-bypassed-claude.jpg vs green-05-bypassed-claude.jpg）直观反映了从“修前无提示 + 运行中假状态”到“修后黄色警告横幅 + 正在输入
  未知”的正确转变。
  ──────
  ## 二、标准审查五项核对

  1.
  根因与改动层级：根因找对（绝对路径启动绕过包装脚本）；按照用户明确选择“不加固，绕过时界面提示”，在后台进程监控与前端状态提示的最小根因层完成改动；无吞异
  常、无 fallback、无重试、无兼容分支或平行 API。
  2. 验收证据与期望值：测试覆盖真实 Electron、后台、node-pty、zsh、真实 Claude Code 2.1.310、真实 Codex 0.164；期望值源于 ticket 规格与 Unix 进程语义。
  3. 红态与变异：修前 red 准确落在 4 项关键缺陷断言上；两个变异设计合理，代表了真实易犯的坏实现，均能被测试拒绝。
  4. 修改边界与文案规范：改动集中在 panes.ts、sidebar.ts、terminalClis.ts、processArgs.py、renderer.tsx、README.md
  与测试文件，未越出任务卡边界；界面提示文案客观明确，无营销腔。
  5. 其他正确性与回归风险：与共用 1 秒定时器的 T-174 静默 CLI 提示完成了端到端回归验证（regression-t174-01 PASS 6/6）；合并 main（含 T-185）后验证通过。
  ──────
  ## 三、审查发现项清单

   编号 │ 位置                │ 严重度     │ 说明与失败场景
  ──────┼─────────────────────┼────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────
   F01  │ RESULTS.md:70-71    │ P3（提示） │ RESULTS.md 检查项计数与实际测试产物不一致。RESULTS.md 记录 green-04、green-05、green-06-after-main-merge 均为
        │                     │            │ PASS 9/9，但对应的 summary.json:11-68 中实际只有 8 个 check 项（Claude 侧 4 项、Codex 侧 3 项、退出清理 1
        │                     │            │ 项）。经查代码，测试在终端 D 处仅断言了 shim_codex_not_warned，未对终端 D 的状态单独执行 check（尽管 observed
        │                     │            │ 中已采集了 state: "running"）。此为文档记数偏差，不影响实际功能正确性。
   F02  │ RESULTS.md:72-78    │ P3（提示） │ 变异测试与 setup-error 的部分原始 JSON 产物未落盘归档。setup-error-01/ 目录下仅归档了 green-
        │                     │            │ 01/summary.json，而文中描述查出被测代码缺陷的 green-02 以及两个变异运行的原始 summary.json 未随 candidate
        │                     │            │ 提交在 evidence 目录下。虽有补丁定义与如实复盘记录，且逻辑推导必然被拒，但缺少物理 json
        │                     │            │ 留存。建议后续补全归档。
   F03  │ terminalClis.ts:200 │ P3（观察） │ Claude 参数解析假定参数独立且紧邻。argv.some((arg, index) => arg === "--plugin-dir" && (argv[index + 1] ??
        │                     │            │ "").endsWith("/plugin/enchanted-a2a")) 假定参数形式为 --plugin-dir <dir> 且 --plugin-dir
        │                     │            │ 作为独立元素。当前包装脚本完全按照此形式传参，判据准确；若未来包装脚本重构传参格式（例如 --plugin-
        │                     │            │ dir=...），此判据需同步维护。
  ──────
  T-184 REVIEW PASS
