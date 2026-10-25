  8f36d6495），审查结论如下：
  ──────
  ### 一、逐项核对结论

  #### 1. 根因与最小改动层

  • 根因确认：准确。macOS 隐私授权弹窗（TCC）在应用更换或首次启动被系统其他窗口遮挡时，CLI 阻塞于内核系统调用（如 openat），PTY
  未产生任何标准输出/错误流字节，终端窗格处于纯空白状态且界面没有任何状态感知。
  • 最小根因层：
      • processSnapshot.py:87-88：仅将已由 libproc 结构体读取的启动时间戳 'started': after.start_sec + after.start_usec / 1e6
      随进程字典暴露，无额外系统调用开销。
      • panes.ts:283-330：仅在终端输入后（shellInput）激活静默检查；在 6 秒安静期后通过进程树核验前台进程组组长（pid === pgid && pgid ===
      tpgid）及其启动时间，确认“启动晚于最后输出”这一机械事实；输出到达时（terminal.onData）立即同步清空。
      • renderer.tsx:465-467：只在 pane?.silent_foreground 存在时渲染提示横幅。
  • 无异常吞噬 / fallback / 重试 / 平行 API：
      • panes.ts:326-330 中的 catch 将异常记录为 silent_foreground_check_failed 审计事件并将 silenceCheck 复位为
      false，属于常驻定时器中防止未捕获异常导致守护进程崩溃的安全兜底，未做盲目重试，无 fallback 备用分支。


  #### 2. 真实入口与期望值独立性

  • 真实入口证据：
      • 端到端验收脚本 test_t174_silent_cli_hint_e2e.py 真实拉起 Electron 实例、a2a 后台守护进程、node-pty、zsh 及编译后的 C 语言替身
      CLI（t174_cli.c），全程 0 模型调用。
      • 运行产物 green-01.json 与 runs.log 完整记录 6 项断言全部通过（6.8 秒出现提示，输出后后台与 DOM 均撤销提示，正常启动 12
      秒内无提示，空闲提示符无提示）。
      • 截图证据完整：silent-hint.jpg（提示展示状态）与 after-output.jpg（有输出后提示消失）。
  • 期望值独立性：
      • 断言直接依据 Ticket 需求与时序物理规则设计，检查程序名、包含“权限弹窗”与“可能”、有输出即撤掉，而非抄写运行产物的偶然哈希或非契约字符串。


  #### 3. 红态与变异拒绝

  • 修前红态落点：
      • red-main-01.json 在基线 8f36d6495 上运行，idle_prompt_no_hint 通过，随后在无输出 CLI 上准确触发 AssertionError:
      超时：后台标出无输出的前台程序，真实落在缺陷断言上。
      • 保留了因环境选择器问题导致失败的早期运行现场 setup-error-01/，符合留存原始失败证据的规则。
  • 真实坏实现变异：
      • 变异 --mutant no-start-check 将 leader.started * 1000 <= outputAt 替换为
      false（代表只检测前台是否存活且无输出，但忽略该进程是否在启动后已有过输出的坏实现）。
      • 在 mutant-no-start-check-01.json 中，该变异在正常启动 CLI 闲置时误报提示，被 normal_start_no_hint 准确拒绝（11 次检测到错误提示并抛出断言）。


  #### 4. 修改边界与文案质量

  • 修改边界：
      • 生产代码仅改动 workbench/app/renderer.tsx（3 行）、workbench/src/panes.ts（34 行）、workbench/src/processSnapshot.py（2
      行），未越界修改任何不相关逻辑，未涉及用户系统权限变更或额外探测代码。
  • 界面文案：
      • 窗格文案：“{command} 启动后还没有任何输出。它可能在等 macOS
      的权限弹窗（例如“想访问‘文稿’文件夹”），弹窗可能被其他窗口挡住了，请移开其他窗口找一找。有输出后这条提示自动消失。”
      • 语言平实克制，以“可能在等”表述推测原因，给出具体移开窗口找弹窗的可操作建议，明确说明有输出后自动消失，无营销腔与 AI 机器味。


  #### 5. 正确性与回归风险

  • panes.ts:319 具备防御性竞态检查（if (pane.outputAt !== outputAt || pane.stopped) return;
  ），确保在异步进程探测期间一旦有输出到达或窗格关闭，立即作废当前探测结果，避免错误挂载提示。
  • 检测逻辑严格限制在项目终端 role === "shell" 实例，受管 worker/controller 窗格不受任何影响。
  ──────
  ### 二、审查发现明细（Findings）

  • 发现 1（P3 - 轻微优化项）
      • 文件与行号：panes.ts:288
      • 严重度：P3
      • 场景描述：const silence = setInterval(() => void this.watchSilence(pane), 1000); 未调用 .unref()。虽然终端在 onExit 时会通过 clearInterval(silence)
      释放定时器，但在极端异常退出或宿主进程关闭且 PTY exit 未触发时，未 unref 的定时器理论上会阻止 Node.js 事件循环自然退出。当前 a2a
      后台本为长驻进程，实际运行无阻断影响，后续如有批处理重构建议补充 .unref()。

  ──────
  T-174 REVIEW PASS

