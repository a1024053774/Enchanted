  ## 一、核心核对点审查

  ### 1. 根因支撑与推理严密性

  • 根因结论：主控 Claude 进程是由操作者使用绝对路径 /Users/luckye/.local/bin/claude 启动的，绕过了 Enchanted 注入在 $PATH
  前置目录中的包装脚本，导致启动参数未附加 --plugin-dir，进而插件未加载、钩子与 a2a skill 缺失。
  • 证据链核对：
      1. process-argv-env.txt:4：实测运行中的主控 Claude 进程（PID 66577，父进程为终端 zsh PID 62132，祖父进程为 Enchanted 后台 PID 61281）其 command
      明确记录为 /Users/luckye/.local/bin/claude --model claude-haiku-5-5，_ 环境变量记录为 /Users/luckye/.local/bin/claude。
      2. process-argv-env.txt:7-8：该进程环境中的 PATH 首项为 /Applications/Enchanted.app/Contents/Resources/app/terminal/bin，A2A_TERMINAL_BIN
      也指向该目录，证明 ZDOTDIR 引导链已正常生效。
      3. pty-commands.txt:4-7：终端 trace（traces/35057a76-ff4c-4763-85e4-d72d1d9a2371/pty.raw）记录了操作者的完整命令序列：
          • 23:26:51 claude --model claude-haiku-5-5（卡在 L01 权限弹窗，被 Ctrl-C 中断）；
          • 23:30:51 claude --version; echo rc=$?（正常输出 2.1.310）；
          • 23:30:51 claude --model claude-haiku-5-5（中断结束）；
          • 23:31:02 /Users/luckye/.local/bin/claude --model claude-haiku-5-5（使用绝对路径启动，后续整轮测试均在此进程中运行）。
      4. claude:4-6：Enchanted 包装脚本的工作原理是通过 exec "$real" --plugin-dir "$A2A_TERMINAL_PLUGIN" "$@" 挂载插件。当操作者输入绝对路径时，UNIX Shell
      行为直接执行目标二进制，完全不进行 PATH 查找，因此包装脚本被跳过，--plugin-dir 参数未注入。
      5. shim-argv.txt:2-4：通过 stub 验证，正常键入 claude 会展开包含 --plugin-dir ...，而绝对路径启动则不会。
  • 推理完整度：证据从底层进程表（ps）、终端 PTY 原始字节（pty.raw）、环境与包装脚本源码四个维度形成闭环，推理严密无跳步。

  ### 2. 已排除假设的依据审查

  RESULTS.md:28-34 中列出的 4 项假设均有确凿依据排除：

  1. Herdr 继承环境（HERDR_*/CLAUDECODE 等）干扰：process-argv-env.txt:7-8 证实即便存在 Herdr 变量，PATH 与 A2A_TERMINAL_BIN 仍然正确设置；
  2. 用户 zsh 配置覆盖 PATH / alias / 函数劫持：zprobe-installed-0.1.3.txt:1-7 用真实的交互登录 zsh（加载用户实际 .zprofile、.zshrc）实测，whence -a claude
  首项即为包装脚本，commands[claude] 指向包装脚本，不存在别名或函数冲突；.zshrc:7 与 .zlogin:3 均保证在用户脚本执行后将包装脚本目录置回 PATH 首位；
  3. 替换应用期间插件目录失效：包装脚本与插件目录权限均为 -rwxr-xr-x，可正常执行；
  4. Claude 2.1.310 对 --plugin-dir 兼容性：T-176 与 T-181 真实测试已证实，只要带有 --plugin-dir，Claude 2.1.310 即可正常加载插件并送达钩子。

  ### 3. 判 PASS、不改代码、真实复验挪到 T-186 的合理性

  • ticket 验收条件核对（T-184-stop-hook-not-delivered.md:24-25）：
      • 验收 1：“写出根因并附证据（进程 argv、环境、复现命令）；未能复现时写 INCOMPLETE 与已排除的假设，不写成 PASS。”
      根因已确凿查明并完全复现，“未能复现”的 INCOMPLETE 条件不触发。
      • 验收 2：“若可修：修前在真实应用（从 Dock/Finder 启动）复现钩子缺失，修后 Stop/UserPromptSubmit 送达后台、侧栏状态随之变化；用户自己在项目终端敲
      claude 时同样生效。”
      该条明确带有前置条件“若可修：”。本案已证明并非产品缺陷，而是实测时的偶发人为操作偏差（为避开 L01
      弹窗卡顿而手工换用绝对路径），产品代码无需修改（full.diff 为空）。在“无需修代码”的前提下，“若可修”分支不适用。
  • 流程与额度合理性：
      • T-186（blocked_by: [T-184, T-185]）是 0.1.4 版本的打包发布与产品页更新任务，且明确包含在真实应用下的端到端复验（lcu 复看）。若在 T-184 中判
      INCOMPLETE 并等待 T-186 的验证，将导致循环死锁；
      • 在已通过 zprobe.py 和 shim-argv.txt 证明正常输入 claude 必走包装脚本的前提下，不在旧版本（0.1.3）额外消耗用户 Claude API
      额度，将真实端到端复验合并至 0.1.4 的 T-186 统一执行，符合项目原则。


  ### 4. 凭据与隐私内容检查

  • 核查 process-argv-env.txt:11-12：所有可能包含凭据的变量名（如 A2A_TERMINAL_TOKEN=、HERDR_SOCKET_PATH=、SSH_AUTH_SOCK=
  等）均只保留变量名，未记录任何变量值；
  • 核查其余文件（pty-commands.txt、zprobe.py、zprobe-installed-0.1.3.txt、shim-argv.txt、RESULTS.md）：均无 API Key、OAuth token、密码或私人敏感信息；
  • 凭据扫描合格，无泄露。

  ### 5. RESULTS 如实性检查

  • RESULTS.md 忠实反映了实测进程号、时间戳、命令执行序列与取证脚本输出；
  • 在“没做 / 未验证”小节中如实披露了“未改动产品代码”、“未另起真实 Claude 复验而挪至 T-
  186”，并客观提出了“绝对路径启动是否需要加固”的设计考量交由构思主控裁定，无隐瞒或虚饰。
  ──────
  ## 二、标准审查五项核对

  1. 根因与改动层级：根因找对（操作偏差导致绝对路径绕过包装脚本）；产品无修改（full.diff 为空），无多余 fallback、重试、兼容分支或平行 API。
  2. 验收证据与期望值：证据采集自真实运行现场（ps/env/pty/zsh 交互环境）；期望值来自 UNIX 标准 PATH 查找机制与 T-120 包装规范，而非抄产品输出。
  3. 红态与变异：本卡为纯调研排查票，无新产品代码产生，故无测试红绿态更替；现场操作失误证据与包装脚本机制对照清晰。
  4. 修改边界与文案规范：无超出任务边界的文件修改；RESULTS 及证据描述客观直白，无营销腔。
  5. 回归风险：不涉及代码改动，对现有系统无引入回归风险。
  ──────
  ## 三、审查发现项清单

   编号 │ 位置          │ 严重度     │ 说明与失败场景
  ──────┼───────────────┼────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
   F01  │ RESULTS.md:38 │ P3（提示） │ 敲 claude 正常入口的真实应用 UI 端到端送达未在 T-184 本卡直接起真实模型复验，而是依赖 T-181 历史证据与 zprobe.py
        │               │            │ 间接证明，并将端到端 UI 确认委托给 T-186。失败场景：若 Claude Code 2.1.310 或包装脚本在特定 Electron
        │               │            │ 窗格交互时还存在未被探测到的其他隐藏问题，该问题将被递延至 T-186 的 lcu 复验时才暴露。
   F02  │ claude:5      │ P3（建议） │ 当前 T-120 的包装机制完全基于 PATH
        │               │            │ 劫持，若用户或自动化流程在终端内显式敲入绝对路径（例如脚本硬编码），插件依然会被静默绕过。RESULTS
        │               │            │ 已正确记录该设计取舍并上报构思主控，无需在缺陷票中擅自加固。
  ──────
  T-184 REVIEW PASS
