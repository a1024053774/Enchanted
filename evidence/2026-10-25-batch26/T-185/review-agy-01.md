   T-185 独立审查报告：Codex 终端装上开局钩子（SessionStart）

  作为 Enchanted（a2a）项目的独立 reviewer，我对候选提交 1ec0ab9ec（T-185）进行了只读独立审查。审查范围覆盖 workbench/ 源码改动、ticket
  验收标准、测试用例实现、红态与变异证据、真实 Codex 运行与重评记录、凭据安全性以及回归测试结果。
  ──────
  ## 一、审查核对详情

  ### 1. 包装脚本实现与“用户 -c 优先”（codex:11-15）

  • 参数位置与优先级：
  在 codex:13-14 中，Enchanted 的钩子参数通过 set -- -c "hooks.SessionStart=[{hooks=[$start]}]" ... "$@" 注入，位于用户传入参数 "$@" 之前。在 Codex 的 CLI
  参数解析规则中，后出现的 -c 会覆盖同名键的先入设置，因此用户自身传入的 -c hooks.SessionStart=... 能够可靠覆盖 Enchanted 的开局钩子。
  • 引号与变量展开：
  start='{type="command",command="\"$A2A_TERMINAL_BIN/a2a\" session-context",timeout=10}' 中单引号安全包含内部双引号，展开后作为 TOML 数组元素传入 -c，由
  Codex 交互执行时交给 shell 展开 $A2A_TERMINAL_BIN，且双引号有效保护了包含空格的路径。此模式与自 T-133 起稳定运行的 $hook 完全一致。
  • 变异拒绝证明：
  在变异 ours-after-user（将 Enchanted 的 -c 移至 "$@" 之后）测试中，summary.json:52-55 明确断言失败于 user_flag_session_start_runs 与
  user_flag_replaces_enchanted_session_start，证明优先级机制具有真实的测试保护。

  ### 2. 协议升级与 Claude 侧回归（terminalCli.ts:76-79）

  • JSON 协议统一：
  a2a session-context 从纯文本输出改造为：
  print({ hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: orientation } });
  输出结构完全符合 Codex 的 SessionStartHookSpecificOutputWire 规范与 Claude Code 的 SessionStart 钩子协议。
  • Claude 侧回归验证：
  查阅 summary.json:99-105，test_t181_question_text_e2e.py 实测输出显示 orientation_in_model_context: [true, true] 顺利通过，证明改成结构化 JSON 后，Claude
  Code 插件依然准确提取 additionalContext 并带入模型上下文，无回归风险。

  ### 3. 开局说明新措辞的准确性（terminalCli.ts:50-53）

  • CLI 中立性：
  原说明中针对 Claude Code 的专用表述（如 用 Bash 运行、Bash 超时设 600000 毫秒）调整为中立且准确的 直接在 shell 里运行 与 命令超时设 600 秒以上（Codex
  使用 exec_command，不称 Bash 工具）；
  • 指引清晰度：
  将“先读 enchanted-a2a 插件的 a2a skill”明确划分为“Claude Code 里是 enchanted-a2a 插件的 a2a skill，其他 CLI 看 a2a help”。措辞客观精确，消除了 Codex 等非
  Claude CLI 因寻找不存在的插件 skill 而困惑的隐患，无误导性内容。

  ### 4. 机械测试合规性与红态验证（test_t185_codex_session_start_e2e.py）

  • 期望来源：
  测试期望 ORIENTATION = ('a2a help', 'a2a request executor', 'Enchanted 工作台的项目终端') 直接源自 ticket 与 T-181 规格，非抄录产品实际输出。
  • 红态断言精准：
  在修前 main 运行记录 summary.json:14-21 中，测试准确失败在缺陷断言 orientation_in_codex_context（a2a request executor: false、Enchanted 工作台的项目终端:
  false），其余既有配置项全部通过。
  • 信任框交互合规性：
  Codex 0.164.0 在首次遇到新钩子时，TUI 菜单第 1 项为 1. Review hooks，第 2 项为 2. Trust all and continue，第 3 项为 3. Continue without
  trusting。默认光标停留在第 1 项。若直接回车，将进入检查 pager 而无法进入会话。AGENTS.md 第 77 行明确要求：“禁止把下一条任务或 Enter
  当作默认批准”。测试脚本通过 PTY 模拟真实用户键入 '2' 并按回车选择信任，完全合规且符合真实使用场景。
  • 异常现场保留：
  在前期测试脚本调试中的三轮错误均被完整保留在 setup-error-01/（包含 green-01、green-02、green-03、mutant-ours-after-user-
  01），无任何掩盖或丢弃失败现场的行为。

  ### 5. 真实复跑评分与重评（--rescore）正当性

  • 初评失败根因：
  查阅 summary.json:29-46 与 tool-calls.json:8-11：Codex 0.164.0 采用 code-mode 执行命令（tools.exec_command({cmd:"a2a request
  executor"})），前置字符包含引号 "，旧评分脚本正则只匹配空白前导符；同时旧脚本按不存在的 user_message 事件统计根提示导致计数为 0。
  • 真实行为核验：
  tool-calls.json 显示 Codex 的第 1 次工具调用为 a2a help，第 2 次直接执行 a2a request executor，期间完全没有调用任何问答工具（如
  request_user_input），亦未在文件系统搜索 a2a。
  • 重评与负例防护：
  在修正计数逻辑（改看 task_started）和命令正则后，使用 --rescore 在原 rollout 产物上重评为
  PASS（summary.json）。重评并未降低业务要求。执行主控进一步构造了 3 份注入缺陷的 rollout 负例并记录于
  real-codex-01-scorer-negatives.txt，分别验证了“先用问答工具”、“搜索入口路径”、“缺少开局说明”均会被准确拒绝，证明新评分器并非无条件放行。

  ### 6. 凭证隔离与安全性核查

  • 隔离 CODEX_HOME 销毁：
  test_t185_real_codex_controller_e2e.py:455-457 在 finally 中执行 shutil.rmtree(codex_home)，运行记录证实 "codex_home_removed": true。
  • 无凭证外泄：
  检查了所有提交的 summary、tool-calls、文本日志及截图 real-codex-01-finished.jpg，没有包含任何 API token、密钥或用户个人凭据。大文件 rollout
  已按规定归档至外置盘清单 codex-rollout.archive.json。

  ### 7. 架构与改动范围

  • 架构纯洁性：
  改动严格限制在最小根因层（仅 3 处源码位置：workbench/README.md、workbench/src/terminalCli.ts、workbench/terminal/bin/codex，以及 2
  套端到端测试）。没有增加任何吞异常代码、兼容后门、重试机制、平行 API 或冗余 shim。
  • 文案风格：
  README 与终端开局说明文字技术描述准确客观，没有任何夸大或营销用语。
  ──────
  ## 二、审查发现项清单（Findings）

  ### [F-01] Codex 主控在获批后连调多次 card_template 参数（观察项）

  • 文件与行号：RESULTS.md:54-57、tool-calls.json:22-36
  • 严重度：P3（低 / 范围外观察项）
  • 场景与分析：真实 Codex 主控在角色获批后，调用 card_template 尝试了 4 种不同入参形式才命中符合预期的参数结构。这表明 a2a help 中对 card_template
  命令的参数示例描述还可以更直观。执行主控已在 RESULTS 中如实记录并作为范围外问题上报，未私自扩大本票范围，处置符合项目规则。
  ──────
  ## 三、审查结论

  T-185 交付物根因定位准确，改动范围最小且干净，红态与变异反例充分，真实复跑与重评证据坚实且经负例验证，凭证管理安全无泄漏，回归检查全部通过。

  T-185 REVIEW PASS
