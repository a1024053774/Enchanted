# T-140 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:p7，交互会话，审查对象为只读副本（候选 708f30e08）。
- 启动 argv 记录（依次三次尝试）：

```
agy --model gemini-3.8-flash-high --mode plan --add-dir /Users/luckye/Documents/Code/a2a-review/T-140-r1 --add-dir /Users/luckye/Documents/Code/a2a-wt-t140/evidence/2026-10-23-batch23/T-140 --add-dir /Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch23 --print-timeout 0s --print "$(cat /Users/luckye/Documents/Code/a2a-review/T-140-r1/prompt.txt)" | tee /Users/luckye/Documents/Code/a2a-review/T-140-r1/review-01.md
# ↑ 01：--print 无头模式，因 shell 命令无法弹确认被自动拒绝，0 字节输出（未计入结论）
agy --model gemini-3.8-flash-high --mode plan --add-dir /Users/luckye/Documents/Code/a2a-review/T-140-r1 --add-dir /Users/luckye/Documents/Code/a2a-wt-t140/evidence/2026-10-23-batch23/T-140 --add-dir /Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch23 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-140-r1/prompt-02.txt)"
# 2026-10-23T11:32:43Z 会话中模式自行从 plan 变为 auto（编辑会自动批准）；执行主控把 candidate 设为只读兜底，审查后核对副本与证据目录无改动
# ↑ 02：plan 交互模式，逐条确认命令，用户嫌烦，主控退出（副本核对无改动）
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-140-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-140-r1/prompt-03.txt)"
# ↑ 03：本报告所用会话
```

- 审查后核对：候选副本 git status 0 行改动。
- 执行主控对发现 3（P2）的核对：不成立。panes.ts:35 注明 monitor 的工作区是它自己的目录；panes.ts:713 只在有额外目录时用 workspace-write，724 行 monitor 的可写根只有额外目录，worker worktree 不可写。发现 1、2（P3）记为已知局限。

## 窗格中的报告原文

```text
▸ Thought for 1m 34s
   T-140 独立审查报告

  审查对象：候选提交
  708f30e0873f5eaad42e7802b395d72482acf153
  （相对起点
  ebbae7bd09cee3a8220b948029f9033dc2906c90
  ）
  审查范围：workbench/
  下的前后端、门禁、角色卡、测试及沙箱外
  RUN-OUTSIDE-03 运行记录
  审查角色：a2a 只读独立审查员（reviewer）
  ──────
  ### 一、核心核对项审查

  #### 1. 目标达成情况

  • 编辑项目与追加式保存：
      •
      前端在项目行菜单增加“编辑项目”入口（r
      enderer.tsx:153），挂载
      ProjectSettings.tsx
      对话框，通过系统原生目录选择器添加，
      支持单项移除与保存。
      • 后台在 daemon.ts:485-495 处理
      project_settings_save，向
      orchestration_events 追加
      project_settings_saved
      事件，旧事件完整保留。在
      store.ts:383-395
      中按序回放，项目移除（project_removed
      ）后再打开不会继承旧的额外目录授权。
  • worker/reviewer/monitor 启动权限：
      • Claude Code：在 panes.ts:291-300
      中，额外目录被同时加入 CLI 的 --add-
      dir、permissions.
      allow（Edit(/<path>/**)）以及沙箱
      filesystem.allowWrite。
      • Codex：在 panes.ts:327 中，通过 --
      add-dir <path> 注入可写根，沙箱为
      workspace-write。
      •
      权限边界与移除：移除额外目录后，新启
      动的 Claude 和 Codex worker
      写该目录均被系统沙箱拒绝（在 green.
      json 中 T-RC 与 T-RD 实测 x: false,
      y: false）；未添加的外部目录 Y
      一律被沙箱拒绝。
      • 启动记录完整性：panes.ts:760 的
      launch 记录明确持久化了
      extra_directories 数组与包含实际 --
      add-dir 的完整 argv。
      •
      用户项目终端：用户普通终端仅执行交互
      式 shell（['-l', '-
      i']），启动参数保持不变。


  #### 2.
  门禁验证逻辑（workbench/src/gates/**）

  • 在 core.ts:2350-2370 中，门禁对
  reviewer 的校验严格按当前 launch 记录中的
  launch.extra_directories 放行：
      • 对 Claude：严格核对 argv.length ===
      16 + 2 * extraDirectories.
      length，末尾参数必须精确为
      extraDirectories.flatMap(p => ['--
      add-dir', p])，settings.permissions.
      allow 必须恰好为候选目录加额外目录的
      Edit 规则，settings.sandbox.
      filesystem.allowWrite 必须精确等于
      extraDirectories。
      • 对 Codex：严格核对所有 --add-dir
      参数与 extraDirectories
      一致，网络关闭、沙箱类型与 exclude
      tmp 等全部既有核对项均未放宽。
  •
  代码中没有新增任何异常捕获吞噬（try/catch
  吞错误）、没有
  fallback、没有兼容旧逻辑的松弛分支或平行
  校验入口。

  #### 3. 安全边界

  • 操作员鉴权：daemon.ts:486 强制要求
  authority.kind ===
  'operator'，worker/终端无权调用
  project_settings_save（在
  test_t140_extra_dirs_e2e.py 中经
  operator_only_settings 真实断言通过）。
  • 路径校验：
      •
      强制校验传入值为绝对路径且在磁盘上为
      实际目录（isAbsolute(path) 与
      statSync(path).isDirectory()）。
      • 解析真实路径并去重：[...new
      Set(input.extra_directories.map(p =>
      realpathSync(p)))]。
      •
      禁止将项目仓库本身作为额外目录（direc
      tories.includes(project.repo)）。
      • 符合
      ticket“可写，不要太重，不做独立门禁、
      worktree 隔离、只读模式”的边界定位。


  #### 4. 测试独立性、红态与变异检查

  • 测试独立性：test_t140_extra_dirs_e2e.py
  中的断言直接来自任务卡规则（如
  dict(x=True, y=False) 和 dict(x=False,
  y=False)），负例放在 /Users/Shared 下以防
  Codex 对 /tmp
  的默认写权限干扰负例效力；未依赖被测模块
  的内部计算结果。
  • 红态证明：修前版本 ebbae7bd0 运行时在
  Edit Project menu 处等待超时并失败（red.
  json），证明修前系统不存在该功能入口。
  • 变异证明：
      • claude-shell-deny-
      extra：将额外目录加入 worker 的
      Git/shell denyWrite，测试在 T-
      C_shell_boundary
      处精确触发断言失败（mutant-shell.
      json），证明对 shell
      权限缺失具备敏感性。
      • removed-directory-
      retained：模拟移除空列表时不更新
      store，测试在 T-RC_shell_boundary
      处精确触发断言失败（mutant-remove.
      json），证明对移除后权限残留具备敏感
      性。
  •
  “真实用户双击保存不会存旧列表”的结论与依
  据成立：
      • 旧失败的根因是测试脚本在同一个
      JavaScript microtask/task
      内同步连续调用了 .
      click()，绕过了浏览器事件循环与 React
      的批处理/渲染调度。
      • 在 ProjectSettings.tsx:45-50
      中，点击保存首先触发
      setBusy(true)，按钮即时变为
      disabled={busy ||
      !settings}，浏览器对处于 disabled
      的按钮会丢弃后续点击事件。
      •
      移除是前序独立动作，保存时闭包直接取
      当前组件最新渲染状态 settings!.
      extra_directories，单纯快速双击保存本
      身没有恢复已移除条目的机制。
      • 在 t140_cdp_click.mjs 中使用真实
      CDP Input.dispatchMouseEvent
      模拟快速双击保存（clickCount: 1 和
      clickCount: 2），实测捕获到的所有
      pointerdown 均为 isTrusted:
      true，且第二次保存点击触发前草稿条数
      已为 0，保存事件精确为 [[X], []]（见
      green.json）。

  ──────
  ### 二、审查发现（Findings）

  #### 发现
  1：未捕获不存在路径导致的异常类型不一致（
  P3）

  • 文件与行号：daemon.ts:489-490
  • 严重度：P3
  • 描述：input.extra_directories.some(path
  => ... !statSync(path).isDirectory())
  中，如果传入一个在文件系统中根本不存在的
  路径，statSync(path) 会直接抛出 Node.js
  的 ENOENT 异常，而非返回布尔值。
  • 失败场景：当通过 API 直接调用
  project_settings_save
  并传入不存在的路径时，外层将其捕获为未处
  理错误，返回 { ok: false, error:
  "orchestration_failed", details: "Error:
  ENOENT..." }，而不是常规的业务拒绝码
  invalid_extra_directory。由于前端是通过
  Electron
  的目录选择器选取有效目录，该问题仅影响非
  法 API 直调，系统未发生崩溃。

  #### 发现
  2：移除按钮的状态更新未采用函数式更新（P3
  ）

  • 文件与行号：ProjectSettings.tsx:61
  • 严重度：P3
  • 描述：移除按钮的点击回调为 onClick={()
  => setSettings({ ...settings,
  extra_directories: settings.
  extra_directories.filter(value => value
  !== path) })}，这里直接解构了当前闭包中的
  settings 对象，而在 add
  方法中则使用了函数式更新
  setSettings(current => ...)。
  •
  失败场景：若存在多个额外目录，用户以极快
  速度连续点击移除两个不同的条目，若两次点
  击落在同一微任务渲染周期之前，第二个点击
  可能使用未包含第一个移除结果的旧 settings
  快照，从而造成前一次移除被覆盖。建议统一
  切换为函数式更新。

  #### 发现 3：Codex monitor
  在配置额外目录时放宽至 workspace-write
  沙箱（P2 / 已知权衡）

  • 文件与行号：panes.ts:310
  • 严重度：P2
  • 描述：由于 Codex CLI 的 --sandbox read-
  only 不支持通过 --add-dir
  为特定外部路径授予写权限，当项目配置了额
  外目录时，代码将 monitor
  的沙箱模式调整为了 workspace-write。
  •
  失败场景：在该模式下，操作系统和沙箱层面
  对 monitor 打开了对其观察的 worker
  worktree 的物理写入权限。该设计完全遵循了
  ticket
  与用户原话中“不要太重，额外目录可写，不做
  独立 worktree
  隔离与只读模式”的决策，并在角色卡（monito
  r.md:8）与启动提示词注入中对 monitor
  加以只读约束，属于已知技术约束下的合理权
  衡。
  ──────
  ### 三、回归验证与验收结论

  • 沙箱外完整验收批次 outside-03-run.json
  包含 9 项实测，全部为 PASS：
      • driver-green：PASS
      • before-fix-driver-
      red：PASS（反事实断言失败退出）
      •
      red：PASS（修前版本在菜单项缺失处反事
      实失败退出）
      • green：PASS（全链路真实
      Electron/CDP/CLI 运行通过）
      • mutant-shell：PASS（shell deny
      反事实断言失败退出）
      • mutant-
      remove：PASS（移除保留反事实断言失败
      退出）
      • regression-t131（多 worker
      并发与门禁集成）：PASS
      • regression-t137（Reflect
      树与复盘调度）：PASS
      • regression-t127（Codex
      隔离环境与门禁）：PASS
  • 代码实现简洁，未引入冗余 wrapper
  或兼容分支，无阻塞性 P0/P1 缺陷。

  理由充分，准予通过。

  T-140 REVIEW PASS
```
