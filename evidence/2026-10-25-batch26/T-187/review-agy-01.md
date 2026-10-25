  ### 1. 审查概要与结论

  • 审查对象：T-187 候选 commit ff3caefbd（相对 main 的 workbench/ 改动见 full.diff）
  • 交付范围：增加 agy 与 opencode 在项目终端中作主控与普通终端支持（包装脚本、OSC 7501 状态解析、角色申请识别、开局说明与未接入提示）。
  • 完成状态：候选 RESULTS.md 已标记为 INCOMPLETE。经逐项代码审查、替身测试与真实 opencode
  运行日志核对，第一段终端侧的核心能力（状态流转、包装脚本转发、开局说明注入）已实现；但存在两处影响行为准确性的 P1 缺陷，且第二段 worker 权限及真实 agy 完整流程待用户裁决后推进。
  • 总体结论：T-187 REVIEW INCOMPLETE
  ──────
  ### 2. 逐项核对详情

  #### 2.1 workbench/src/terminalClis.ts

  • 登记表：集中定义了 claude、codex、opencode、agy 的 wired、turns 与 inCommand 属性。
  • OSC 7501 解析：正则匹配 \x1b\]7501;([^\x07\x1b]*)(?:\x07|\x1b\\)。跨段 carry 逻辑在已匹配后切取最后一段未闭合序列，但仅在 \x1b]7501; 前缀完整时生效（见发现项）。
  • osc7501State 映射：
      • working → running
      • idle / done / clear → idle
      • blocked 且 kind=question → waiting_user_answer
      • blocked 的权限确认（kind=permission）、登录（kind=auth）以及无报告均映射为 unknown，严格遵守“做不到的信号显示未知而不是猜”原则。


  #### 2.2 包装脚本 terminal/bin/agy 与 terminal/bin/opencode

  • agy：
      • 通过 real-cli.sh 跳过自身找到真实 CLI，exec "$real" "$@" 原样转发所有参数；
      • 环境变量使用 ${AGY_CLI_OSC7501:-on}，用户自身环境设置优先；
      • 设置 A2A_SHIM=agy 标明接入来源。
  • opencode：
      • 用户已有 OPENCODE_CONFIG_CONTENT 时直接原样转发 "$@"，用户设置优先；
      • 非交互启动判定：子命令（$1 非空、不以 - 开头且不是目录）或显式带 --server / --server=* / --standalone 时原样转发，不注入配置也不加 --standalone；
      • 交互启动时通过 orientation=$(cd "$(dirname "$0")/.." && pwd -P)/orientation.md 定位开局说明，并使用 sed 's/[\\"]/\\&/g' 对路径中的 \ 与 " 进行 JSON 转义，生成 {"instructions":[".
      .."]} 写入 OPENCODE_CONFIG_CONTENT；
      • 仅对交互启动追加 --standalone，满足要求。


  #### 2.3 workbench/src/processArgs.py

  • 通过 parts[argc:] 扫描进程启动环境，仅匹配 A2A_SHIM= 前缀并解码输出单个变量 shim，不读取、不泄露其他环境变量。

  #### 2.4 workbench/src/panes.ts

  • terminal.onData 中调用 readOsc7501(pane.oscCarry ?? "", data) 提取最新状态至 pane.cliTurn，并更新 pane.oscCarry；
  • 在 watchWiring 中读取 launch_of 输出的 shim，判断 cli.wired(launch)，当没有接入时挂上 unwiredCli；
  • 在 leader 不存在时清除 pane.unwiredCli = null 和 pane.cliTurn = null。但该检查依赖 \r 触发，导致进程退出后清理不及时（见发现项）。

  #### 2.5 workbench/src/sidebar.ts

  • 识别 roleRequest.cli 的 turns === 'osc7501' 时，侧栏主控行状态直接使用 osc7501State(pane?.cli_turn)；在无报告或 pane.unwired_cli 时显示为 unknown。
  • 侧栏“已知缺口”文案准确描述了 agy / opencode 依靠 OSC 7501 且权限确认显示未知的限制。

  #### 2.6 workbench/src/terminalCli.ts、orientation.md 与 roleRequests.ts

  • 开局说明合并至单点 workbench/terminal/orientation.md，terminalCli.ts 统一自文件读取；
  • roleRequests.ts 使用 Object.hasOwn(terminalClis, cli) 统一白名单校验；
  • a2a request 调用 commandCli(process.env) 识别运行环境。

  #### 2.7 测试 test_t187_osc_cli_e2e.py 与 t187_fake_cli.c

  • 期望来源：状态（running、idle、waiting_user_answer、unknown）、--standalone、开局说明与未接入警告均直接来自 ticket、facts.md 实测及 T-184/T-185 契约，未抄录被测代码输出。
  • 红态与变异：
      • red-main-01：在 main 分支上执行，16 项检查失败，精准落在未接入提示缺失、未知 CLI 及状态恒为 unknown 的缺陷断言上；
      • 3 个变异测试（no-carry 验证拆包丢失、blocked-is-waiting 验证猜测权限状态、kept-after-exit 验证退出后残留状态）均有效代表坏实现并被拒收。
  • 替身与真实 CLI 差异：
      • t187_fake_cli.c 真实模拟了 OPENCODE_SESSION_ID 继承与两者的 OSC 7501 退出/状态协议；但未模拟真实 agy 会先发送的 \x1b]7501;?\x07 终端能力探测。


  #### 2.8 真实运行 test_t187_real_opencode_controller_e2e.py 与 real-opencode-03/summary.json

  • 真实 opencode v2.1.4 实测 2 回合：
      • 正确识别 instructions，未在文件系统搜索 a2a，直接执行 a2a request executor；
      • 角色申请正确记录为 opencode；
      • 状态流完整观测到：空闲 → 运行中 → 空闲 → 等待用户回答（多选提问）→ 运行中 → 空闲；
      • 侧栏 DOM 属性 data-agent-state 与后台状态刷新完全同步。


  #### 2.9 README.md 一致性

  • 详细记录了 5 个命令、orientation.md 来源、A2A_SHIM、AGY_CLI_OSC7501、OPENCODE_CONFIG_CONTENT 机制及状态映射规则，与实现完全一致。
  ──────
  ### 3. 发现项清单

  #### 发现 1：commandCli 依赖环境变量顺序未实现“父进程链查找”，外层含 CLAUDECODE 时嵌套 CLI 会被误判为 claude

  • 文件与行号：terminalClis.ts:22-23
  • 严重度：P1
  • 失败场景：
  candidate/evidence/2026-10-25-batch26/T-187/facts.md 第 27 行明确指出：“探针的子进程继承了外层 Claude Code 的 CLAUDECODE=1。只按 CLAUDECODE 判断，会把嵌套在里面的 opencode 认成
  Claude。改为沿父进程链往上找，取第一个在 terminalClis.ts 里登记过的程序名，这样认出的是最内层的 CLI。”
  然而实际代码中并未实现父进程链回溯，仅为：
    export const commandCli = (env: NodeJS.ProcessEnv): string | undefined =>
      Object.keys(terminalClis).find(name => terminalClis[name].inCommand(env));
  Object.keys(terminalClis) 顺序固定为 ["claude", "codex", "opencode", "agy"]。若终端会话外层继承了 CLAUDECODE=1（例如在 Claude 终端内或子 shell 里运行 opencode / agy），调用 a2a request
  时，terminalClis["claude"].inCommand(env) 首先命中，导致申请角色被错误记录为 claude 而非当前实际运行的 opencode 或 agy。这与 facts.md 声明的机制直接相悖。
  ──────
  #### 发现 2：CLI 退出后未敲回车时，后台不调度 watchWiring，侧栏主控行持续残留假“空闲”

  • 文件与行号：workbench/src/panes.ts:319, 327-334, 342
  • 严重度：P1
  • 失败场景：
  在 Panes 中，清除前台退出残留报告的逻辑位于 panes.ts:334：
    if (!leader) { pane.unwiredCli = null; pane.cliTurn = null; return; }
  但是，watchWiring 仅在 pane.wiringCheckAt 到期时执行。对于正常接入的包装 CLI，unwired 为 false，因此第 342 行不会重新调度 wiringCheckAt。
  当用户在 opencode 或 agy 交互中退出（如输入 exit、按 Ctrl-D 或应用自身结束）回到 shell 提示符后，只要用户没有在 shell 提示符下再次按下回车键（\r），wiringCheckAt 便始终为
  undefined，watchWiring 永不执行。
  结果是：CLI 已经彻底退出回到 shell，但后台的 pane.cliTurn 仍保留退出前最后一次状态（如 idle），侧栏主控行无限期显示为“空闲”而不是“未知”。
  在测试 test_t187_osc_cli_e2e.py:623-626 中，测试代码通过显式插入 type_in(c, '\r') 规避了该问题（注释注明“a submitted line at the prompt has the daemon look at the foreground
  again”），证明此为已知执行机制缺陷，在真实用户交互中将产生假状态滞留。
  ──────
  #### 发现 3：仓库中缺失 Ticket 定义文件

  • 文件与行号：candidate/.project-map/tickets/T-187-agy-opencode-support.md（文件不存在）
  • 严重度：P2
  • 失败场景：
  任务输入要求及收件箱消息 refs 明确指向 .project-map/tickets/T-187-agy-opencode-support.md，且 .project-map/MAP.md 仅将 T-187 登记在 Not yet specified 列表中而未建档。候选分支缺少
  ticket 独立文件，无法通过正规项目地图检查溯源验收条件。
  ──────
  #### 发现 4：OSC 7501 跨段 carry 逻辑在转义前缀被切断时丢失报告

  • 文件与行号：terminalClis.ts:38-39
  • 严重度：P2
  • 失败场景：
  readOsc7501 在处理 carry 时仅查找完整前缀：
    const open = text.lastIndexOf("\x1b]7501;");
    return { carry: open >= end && text.length - open < 4096 ? text.slice(open) : "", turns };
  如果 PTY 数据块恰好在转义前缀内部切断（例如数据块 1 末尾为 \x1b]750，数据块 2 开头为 1;state=working\x07），text.lastIndexOf("\x1b]7501;") 将返回 -1，导致数据块 1
  末尾的切片被丢弃，数据块 2 也无法匹配，整条状态变更丢失。
  ──────
  #### 发现 5：readOsc7501 对缺少 = 的字段切片产生越界负索引

  • 文件与行号：terminalClis.ts:34
  • 严重度：P2
  • 失败场景：
  解析字段时直接使用 indexOf("=")：
    const fields = new Map(match[1].split(":").map(field => [field.slice(0, field.indexOf("=")), field.slice(field.indexOf("=") + 1)]));
  若第三方 CLI 发送了不含 = 的字段（例如探测标记 ? 或标志位 :flag:），field.indexOf("=") 为 -1。field.slice(0, -1) 会截掉字符串最后一个字符作为键，而 field.slice(0) 作为值（如 "flag"
  变成键 "fla"、值 "flag"）。虽不破坏现有 state 判断，但缺乏边界健壮性。
  ──────
  #### 发现 6：测试替身 t187_fake_cli.c 未覆盖真实 agy 的能力探测信号 ?

  • 文件与行号：t187_fake_cli.c:380-418
  • 严重度：P3
  • 失败场景：
  facts.md 说明真实 agy 启动时会先输出探测信号 \x1b]7501;?\x07 检查终端是否支持，而 Enchanted 不作应答。但替身 t187_fake_cli.c 从不发送此探测序列，导致解析器在真实终端场景下遇到 ?
  时的过滤表现未被自动化集成测试覆盖。
  ──────
  ### 4. 核心审查维度答复

  1. 根因是否找对，改动是否在最小根因层；有无吞异常、fallback、重试、兼容分支或平行 API：
      • 根因找对。改动直接在项目终端接入层（terminalClis.ts 登记表、bin/ 下同名包装脚本、processArgs.py 环境探测、panes.ts PTY 监听），未修改各 CLI 全局配置，属于最小根因层。
      • 无吞异常、无 fallback 重试策略、无平行 API。
  2. ticket 的每条验收是否有真实入口的证据；期望值是否来自 ticket/规格/用户原话而不是抄产品输出：
      • 侧栏状态映射与开局说明注入已有真实 opencode（real-opencode-03）及替身端到端测试（green-02）验证；
      • 期望值来自 facts.md 实测协议规范与 ticket 原话，未抄录产品临时输出；
      • 但 ticket 第 1 条验收（主控向 worker 派发全流程）因 worker 权限待定尚未完成。
  3. 红态是否在修前版本上落在缺陷断言上；变异是否代表真实坏实现并被拒绝：
      • red-main-01 在 main 分支精准触发 16 项失败断言；
      • 3 个变异测试均有效模拟真实缺陷并被自动化套件捕获。
  4. 是否越出任务卡的修改边界；界面文案是否清楚、不含营销腔：
      • 修改范围严格限定在 workbench/ 终端与主控接入相关文件，无越界修改；
      • 界面文案与侧栏提示词严谨清晰，如实陈述能力限制，无营销腔。
  5. 其他正确性、回归风险：
      • 存在上述发现 1（嵌套 CLI 识别）与发现 2（前台退出清理遗留）两项稳定性隐患；
      • 历史 T-184、T-185 经回归测试确认未受影响。

  ──────
  T-187 REVIEW INCOMPLETE
