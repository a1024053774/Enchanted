  ### 1. 根因与最小改动层（Minimal Root-Cause Layer）

  • 根因分析：原实现将 CLI 接入硬编码为 claude/codex 且依赖钩子注入，无法支持没有每会话钩子的 agy 与 opencode。候选将 CLI 的接入判据、回合来源（hooks vs
  osc7501）与环境识别集中在单一登记表 terminalClis.ts，并统一从项目终端输出中解析原生 OSC 7501 状态报告。
  • 改动范围：直接替换原 shimWiring，没有保留兼容垫片或平行 API；没有引入重试、异常隐匿或降级 fallback。
  • 开局说明：将原硬编码在 terminalCli.ts 的文字提取至唯一事实源 orientation.md，Claude/Codex 钩子通过 a2a session-context 读取，opencode 包装脚本通过
  OPENCODE_CONFIG_CONTENT 传入，保证说明完全一致。

  ### 2. 包装脚本与参数转发（terminal/bin/agy、opencode）

  • 参数转发：
      • agy:8：使用 exec "$real" "$@" 原样转发全部命令行参数。
      • opencode:359-367：子命令（非目录首参数）、用户显式传递的 --server、--standalone 或自定义 OPENCODE_CONFIG_CONTENT 均通过 exec "$real" "$@"
      原样直通。
  • 用户设置优先：
      • agy：AGY_CLI_OSC7501="${AGY_CLI_OSC7501:-on}"，用户在环境预设的值优先保留。
      • opencode：[ -n "${OPENCODE_CONFIG_CONTENT:-}" ] && exec "$real" "$@"，用户预设配置优先保留。
  • --standalone 条件注入：仅在交互式启动且未指定独立服务端相关参数时注入 --standalone（事实依据：opencode 共享后台服务不读取会话级环境变量）。
  • JSON 转义：orientation 路径通过 $(printf '%s' "$orientation" | sed 's/[\\"]/\\&/g') 处理反斜杠与双引号转义，并在 printf '{"instructions":["%s"]}'
  中格式化，符合合法 JSON 结构。

  ### 3. 后台进程环境与状态生命周期

  • 环境变量读取：processArgs.py:151-153 经 KERN_PROCARGS2 仅过滤并读取 A2A_SHIM= 这一个环境变量，既不保留也不泄漏用户进程的其他环境信息。
  • OSC 7501 解析与 carry 机制：terminalClis.ts:34-48 的 readOsc7501 正确处理了跨分段数据，包含：
      • 报告内容中间被拆分；
      • 报告恰好在开头 \x1b]7501; 转义序列内部被截断（向下一 chunk 传递 carry，超过 4096 字节丢弃以防无界膨胀）；
      • 忽略探测包 \x1b]7501;?\x07，不产生假状态。
  • 状态映射与“不猜”原则：terminalClis.ts:51-56 严格将 working 映射为 running，idle/done/clear 映射为 idle，blocked 且 kind=question 映射为
  waiting_user_answer；权限确认（kind=permission）、登录（kind=auth）及未识别信号一律返回 unknown，绝无臆测。
  • 清除机制：panes.ts:335 在检测到前台进程组组长退出（!leader）时将 pane.cliTurn 置 null；并在持有报告时每 5 秒（WIRING_RECHECK_MS）自动复查一次，CLI
  退出后即刻清除状态。
  • 主控行与角色申请：
      • roleRequests.ts:181：接入全部在 terminalClis 登记的 CLI。
      • sidebar.ts:202-205：对 turns === 'osc7501' 的主控采用 osc7501State(pane?.cli_turn)，未接入或未报告时呈现“未知”。


  ### 4. 测试与验证实证

  • 期望值来源：test_t187_osc_cli_e2e.py 中的状态期望值直接源自 ticket 要求与 facts.md 的实测协议，而非抓取被测系统的实际输出。
  • 红态与变异体验证：
      • red-main-02：在未改动的 main 分支上运行，18 项检查精准失败在未接入提示缺失、角色未识别、OSC 状态未解析等缺陷断言上。
      • 变异体 no-carry-02：单段查找报告，分段与前缀截断测试被拒（opencode_split_report_running、opencode_prefix_split_running）。
      • 变异体 blocked-is-waiting-02：将 permission 等 blocked 状态误当等待回答，被拒（agy_permission_unknown 预期 unknown 得到 waiting_user_answer）。
      • 变异体 kept-after-exit-03：退出后保留最后报告，被拒（opencode_exit_unknown 预期 unknown 得到 idle）。
      • 变异体 enter-only-02：仅在敲回车后复查前台，被拒（CLI 自主 leave 后未敲回车，未能按时清理状态）。
      • 变异体 env-order-01：按登记顺序挑选外层 CLI，被拒（opencode_request_cli 在嵌套 Claude 环境变量下被认成 claude）。
  • 替身与真实 CLI 评估：
      • 替身 t187_fake_cli.c 为原生编译 C 程序，模拟了真实 CLI 在 argv/环境/OSC 7501 序列格式上的全部实测特征。
      • 真实运行测试 test_t187_real_opencode_controller_e2e.py 配合真实 opencode v2.1.4 与真实免费模型（Big Pickle），在 summary.json
      中完整记录了申请主控、批准生效、运行中→等待回答→空闲的状态流变迁，并证实模型遵守了开局说明（未在文件系统搜索 a2a）。


  ### 5. 文档与界面文案一致性

  • README.md:10-45 准确记录了 5 个包装脚本、terminalClis.ts 接入点、OSC 7501 状态解析原则及已知限制。
  • 侧栏“已知缺口”文案客观平实，指明了 agy/opencode 缺乏每会话钩子导致输入不记入审计、等权限或登录时呈现未知等事实，不含任何夸大或营销腔。
  ──────
  ## 审查发现（Findings）

  ### [F1] ancestors() 解析进程名受限于首个 Token，对解释型脚本 CLI 嵌套识别失效

  • 文件与行号：terminalCli.ts:244-250
  • 严重度：P2
  • 失败场景：
  ancestors() 使用正则 /^(\d+)\s+(\d+)\s+(\S+)/ 从 /bin/ps -axo pid=,ppid=,args= 提取父进程名字并取 basename(match[3])。
  当 CLI 属于通过解释器执行的脚本（如 npm 安装的 Claude Code 或部分安装形态的 Node/Python CLI），其进程启动参数第一项为解释器本身（如
  /opt/homebrew/bin/node），match[3] 解析结果为 "node"，而非 "claude" 或 "agy"。
  若用户在一个外层 CLI（如 opencode）中嵌套启动了此类 CLI，commandCli 触发父进程链回溯时，ancestors() 返回的程序名列表中包含 "node" 而非真实的 CLI
  名字，导致 ancestors().find(name => claimed.includes(name)) 无法匹配内层 CLI，可能错误回退到外层二进制 CLI 或返回 undefined（使角色申请变为“未知”）。

  ### [F2] CLI 退出后若立即跟进非 CLI 前台进程，状态残留直到该进程退出

  • 文件与行号：panes.ts:335
  • 严重度：P3
  • 失败场景：
  panes.ts 中清空 pane.cliTurn = null 的触发条件是 if (!leader)（即当前前台无非 shell 进程）。
  如果用户或复合脚本在 CLI 退出后立刻启动了其他前台命令而没有在 shell 提示符停留（例如执行 opencode; sleep 60 或 agy; top），watchWiring 查出的 leader 是
  sleep。由于 sleep 不在 terminalClis 中，pane.unwiredCli 会被置为 null，但 pane.cliTurn 并未被清除，导致在后续 60 秒内侧栏继续显示 opencode
  退出的最后状态，直到 sleep 结束返回 shell 提示符后才变为“未知”。

  ### [F3] opencode 包装脚本的子命令识别依赖目录判断，单文件启动时漏加参数

  • 文件与行号：opencode:360
  • 严重度：P3
  • 失败场景：
  包装脚本使用 case ${1:-} in ''|-*) ;; *) [ -d "$1" ] || exec "$real" "$@" ;; esac 区分交互式启动与子命令（如 auth、serve）。
  如果用户以单个文件作为启动参数交互打开（如 opencode README.md）或首参数传入文本，因 [ -d "$1" ]
  为假，该逻辑会将其误判定为子命令而直接执行原始程序，导致漏加 --standalone 与 OPENCODE_CONFIG_CONTENT 开局说明。
  ──────
  T-187 REVIEW INCOMPLETE
