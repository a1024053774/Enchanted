# T-141 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pT，交互 auto 模式（只用读文件工具），只读副本，候选 65ca19f8b。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-141-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-141-r1/prompt.txt)"
# pane wG:pT started 2026-10-23T16:54:46Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，两条 P3（用户 MCP 不在写入沙箱内；未信任目录需用户自己信任一次），均为用户已裁定的行为。

## 窗格中的报告原文

```text

○ Thought for 3m 27s (Analyzing `RUN-OUTSIDE-06.sh` and the corresponding `matrix...)
● Explored 15 files (full.diff, 20261023T125315Z-ideation-answer-001.md, 20261023T...)
● Explored 1 file (candidate.txt) (ctrl+o to expand)

▸ Thought for 50s
   T-141 独立审查报告：放宽受管会话限制

  我是 a2a 项目的只读独立审查员（reviewer）。针对任务 T-141（放宽受管会话限制）
  候选版本 65ca19f8b（相对起点 3f8813b0e 的 15
  个改动文件）以及相关的运行证据（evidence/outside05-
  jYDNPNbR/matrix.json、evidence/outside06-pOPgrnDF/matrix.json
  等）进行了逐项源码核对与审计。
  ──────
  ## 1. 审查结论概述

  • 产品实现：产品代码在 panes.ts 与 core.ts
  中准确实现了网络全开、保留写入范围硬边界、Codex 保留 -a never、Claude 独立加载用户
  MCP、Codex reviewer 副本强制 untrusted 且受门禁比对、worker/monitor
  沿用用户信任配置。整个改动中未发现任何隐式 fallback、平行路径或吞异常逻辑。
  • 受保护文件改动：test_t140_extra_dirs_e2e.py 仅在夹具配置中为 demo 仓库配置
  trusted，断言零修改；test_t127_codex_home_e2e.py 仅修改了用户授权的四处 worker
  期望与对应的变异入口定位，三个检查重命名符合新契约语义，审查员侧断言与超时完全未被
  放宽；其他受保护验收文件未发生任何改动。
  • 第 6 轮 4 场判定修正：对 4 场的修正仅为证据提取方式（SQLite immutable=1 避免 WAL
  sidecar 锁故障）、单变量门禁反事实验证、补全变异注入的内存 worktree
  字段以及识别后台拒绝时的 paused
  终态。所有变异均如期被对应的门禁或行为断言拦截，未放宽任何判定标准。
  • 安全性：worker 写入的 .codex 配置、hooks 与 exec policy 因 reviewer
  副本被强制加上 -c projects={<candidate_copy>={trust_level="untrusted"}}
  而无法在审查员会话中执行；文件写入边界无法通过额外目录或共享临时目录绕过。

  综合判定：通过（PASS）。
  ──────
  ## 2. 逐项核对详情

  ### 2.1 产品代码实现（panes.ts、gates/core.ts 等）

  1. 网络全开与代理继承：
      • Codex：panes.ts:734 显式传入 -c sandbox_workspace_write.
      network_access=true，并删除了原有覆盖用户网络代理的 features.
      network_proxy=false，沿用用户自身的代理配置。
      • Claude Code：panes.ts:141 在 --settings 中配置 sandbox.network: {
      allowedDomains: ["*"], allowAllUnixSockets: true, allowLocalBinding: true
      }，完全开放外网、本地连接与 Unix Socket。
      • 验收核对：outside-05 第 7 场 green 验证了两类真实 CLI 对 https://example.com
      的实际 curl 调用均成功返回。
  2. 写入范围硬边界：
      • Codex：panes.ts:730-738 保持 --sandbox workspace-write，通过 writable_roots
      严格限制只写 requestDirectory（worker）及已登记的 extraDirectories；通过
      exclude_slash_tmp=true 与 exclude_tmpdir_env_var=true 严格排除共享 /tmp 与宿主
      $TMPDIR。Codex 的临时目录重定向至请求目录或工作目录内的 .a2a-tmp/（#L757）。
      • Claude Code：panes.ts:138-142 中，文件工具仅放行
      Edit，且仅允许当前工作目录、请求目录与额外目录，不放行 Write；shell 沙箱设置
      allowUnsandboxedCommands: false，通过 denyWrite 收回整个 Git common dir。
      • 用户 MCP 服务的写入不在 Bash 沙箱限制内，此项符合用户裁定 A，并在
      README.md:38-39 与 worker.md:120 中如实记录，门禁路径边界检查依然有效。
  3. Codex -a never 与问题上报/主控答复闭环：
      • panes.ts:730 明确保留 -a never；门禁 core.ts:2386 强制校验 reviewer 带有 -a
      never。
      • 原生审批需要确认的操作会立即被拒，角色卡明确指引 worker 通过 issue ... --
      blocking true 挂起回合上报，主控使用 answer_issue
      答复，后台经正常原会话队列送达，worker 读取答复并继续交付。该链路在
      test_t141_loosened_limits_e2e.py 及 outside-05 的 green 场次中通过真实
      Electron 页面与后台状态验证，且在 answer-dropped 变异中被有效拦截。
  4. Claude MCP 配置：
      • 移除了 --strict-mcp-config，保留 --setting-sources "" 避免合入用户 settings
      文件中的权限扩展；
      • panes.ts:724-726 仅在 $HOME/.claude.json 顶层包含非空 mcpServers
      时，通过原生 --mcp-config 单独传给 CLI；
      • 通过只匹配 ^mcp__ 的 PreToolUse hook（#L135-L136）放行 MCP
      工具，排除了已被真实 CLI 拒绝的无效通配符 permissions.allow:
      ["mcp__*"]，且不扩大对 Bash 或原生文件工具的权限；
      • reviewer 门禁 core.ts:2356-2363 严格核对 --mcp-config 必须指向当前 launch
      HOME 下的 .claude.json，其他路径一律拒绝。
  5. Codex 目录信任与 Reviewer 隔离：
      • worker 与 monitor 不再传 projects=... 参数，沿用用户自身配置与原生信任继承；
      • 仅 reviewer 对一次性候选副本传入 -c
      projects={<candidate_workspace>={trust_level="untrusted"}}（panes.ts:731）；门
      禁 core.ts:2387 精确校验这一条；
      • 启动流程中，trusted 目录依赖原生终端状态包 OSC 7501;state=idle:app=codex
      与领导进程核对直接放行（panes.ts:932-943）；untrusted 目录（如
      reviewer）在安静等待后仅输入回车选择不保存信任的 "Open
      restricted"，再等待同一个 OSC 7501 状态包放行；遇到未配置信任（unset）弹出
      "Trust and continue" 时不按键，直接失败并记录
      codex_folder_trust_requested，不代选信任、不修改用户配置。
  6. 平行路径、吞异常、fallback 审查：
      • 无任何绕过门禁的后门或平行通道；
      • 异常处理严格：processInfo 校验失败记录 codex_startup_failed，JSON 解析或
      SQLite 异常均直接抛出并标记 INCOMPLETE，绝无吞异常；
      • 无任何失败时尝试降级或容错的 fallback。

  ──────
  ### 2.2 受保护验收文件改动核对

  1. **test_t140_extra_dirs_e2e.py**：
      • 唯一改动为第 169–171 行：在测试自建的隔离 CODEX_HOME 的 config.toml
      中，把该测试创建的 demo 仓库配置为 [projects."..."] trust_level="trusted"。
      • 所有的检查名、断言表达式、期望值及超时参数完全未改。改动严格落在 controller-
      decision.md 执行主控裁定范围内。
  2. **test_t127_codex_home_e2e.py**：
      • 夹具部分（第 213–214 行）：同 T-140，仅在隔离 CODEX_HOME 中添加测试自身的
      demo 仓库 trusted，符合用户 20261023T151224Z 裁定 A；
      • 四处授权 worker 期望与断言改动（符合用户 20261023T153252Z 裁定）：
          • 第 359 行：restricted_answered_before_first_task 改为
          trusted_worker_starts_directly，期望启动事件直接为 ['turn_submitted']；
          • 第 478 行：project_codex_hooks_not_run 改为
          reviewer_project_codex_hooks_not_run，明确断言候选中的项目钩子不得在
          reviewer 中运行（not any(name.startswith('project') and name.endswith('-
          reviewer') for name in markers)），不再禁止 trusted worker 运行项目钩子；
          • 第 487 行：user_home_not_rewritten 中由 '[projects' not in config_after
          改为 '[projects' not in (added or '')，仅禁止 a2a 向配置追加新
          [projects，保留夹具初始配置；
          • 第 491 行：worker_folder_untrusted_in_argv 改为
          worker_trust_not_overridden，断言 worker 启动参数中不得出现 projects= 或
          projects.。
      • 变异定位与故障注入补全：
          • untrusted-config-missing、project-trusted、session-folder-
          differs、resume-worker-in-argv 字符串定位更新至当前源码形态；
          • reviewer-folder-unbound（第 106–107 行）补充伪造内存 pane.record.
          worktree，使 hook envelope 能正常通过前置校验，让被测会话能走到后层门禁
          review_native_session_folder；
      • 等待谓词调整（第 438 行）：
          • 将 'paused' 补充入“审查结束”的等待终态，适应门禁拒绝 reviewer 时 task
          转入 paused 的生命周期逻辑，未放宽拒绝断言；
      • 审查员断言保护：
          • reviewer_same_home_untrusted_copy（审查副本 untrusted
          打开）、reviewer_mutations_ran_in_copy（副本变异运行且拒绝）、reviewer_pro
          ject_codex_hooks_not_run、reviewer_result_refused_*
          等断言全数保留，没有被放宽。

  3. 其他受保护文件：未触及任何其他受保护验收文件。
  ──────
  ### 2.3 第 6 轮 4 场判定修正核对

  1. 证据读取修正（t127-no-untrusted 与 t127-trusted-copy）：
      • 第 5 轮中两个场景因 SQLite 普通只读模式在已终止夹具上遇到 OperationalError:
      unable to open database file 而导致提取失败，记录为 INCOMPLETE。
      • 第 6 轮修正为 ?mode=ro&immutable=1 静态读取，并在读取前断言 -wal
      不存在或为空，绝不忽略未落盘证据；
      • 提取出的实际启动参数通过 workbench/tests/t141_review_trust_rejection.mjs
      输入真实 reviewLaunch 门禁，验证原始参数确实触发
      review_launch_boundary，且仅恢复 untrusted
      这一项参数后立即通过门禁；同时反事实测试证明混入其他错误（如 sandbox
      变动）后依然被拒。这严格证明了拒绝纯粹源于 trust
      参数，判定标准实质更严格，绝非放宽。
  2. 拒绝层与故障注入对齐（t127-folder-runtime-unbound 与 t127-gate-folder-
  unchecked）：
      • 第 5 轮中因变异注入不完整，导致 hook 提前被前置的 question_origin_unverified
      拦截，未能到达后层门禁
      review_native_session_folder，从而导致等待审查终态超时。
      • 第 6 轮在变异中补齐了内存 worktree 字段的同步伪造，使 hook
      顺利进入门禁流程：
          • 在 t127-folder-runtime-unbound 中，门禁 reviewSubmit 准确以
          review_native_session_folder 拒绝该次审查；
          • 在 t127-gate-folder-unchecked
          中，关闭该门禁后审查异常通过，立即被测试底部的行为断言
          reviewer_result_refused_session_folder_differs 捕获（AssertionError:
          {'state': 'passed', ...}）。
      •
      这证明了变异被预期目标层断言精准捕获，修正是为了使后层可达，未作任何降级处理。
  3. paused 终态识别：
      •
      仅用于纠正等待循环的终止条件，避免等待超时。等待结束后对拒绝事件和状态的核验依
      然完全执行，未改变验收断言。

  ──────
  ### 2.4 安全与写入边界审计

  1. Worker 配置与脚本在审查员中失效：
      • Codex reviewer 启动时被强制指定 -c
      projects={<candidate_workspace>={trust_level="untrusted"}}；
      • 在 untrusted 模式下，Codex 绝不加载工作区内部的 .codex/config.toml、.
      codex/hooks.json 与 exec policy；
      • 门禁对该参数进行硬性比对，测试对 reviewer 运行 project hook
      进行了否定断言。worker 写入的任何恶意钩子或配置均无法污染独立审查过程。
  2. 写入边界穿透防范：
      •
      额外目录必须是系统已登记的项目配置，且必须是绝对路径。门禁对额外目录进行了严格
      比对。
      • Codex 通过 exclude_slash_tmp=true 与 exclude_tmpdir_env_var=true
      关闭了宿主全局共享临时目录写入权限，仅允许请求目录或审查目录内部的独立 .a2a-
      tmp；
      • Claude Code 原生文件工具被完全剥夺 Write 权限，仅允许被授权路径下的
      Edit；shell 沙箱收回 Git common dir，且禁止沙箱外命令执行。
      • 端到端测试中宿主直接读取验证证明：/tmp、宿主 $TMPDIR 以及未授权的外部目录 Y
      均无法被写入。

  ──────
  ## 3. 发现项清单

  本次审查未发现阻碍发布的阻断性缺陷（P0/P1/P2）。下列条目为设计边界核对与已知特性的
  记录（P3）：

  ### [P3-01] Claude Code 用户 MCP 服务执行边界独立于文件沙箱

  • 文件与行号：panes.ts:121、README.md:38-39、worker.md:120
  • 严重度：P3（已知行为与文档声明一致）
  • 场景描述：用户配置的 MCP 服务作为独立进程运行，不受 Claude 的 Bash
  写入沙箱约束。若用户配置了具备宽泛写文件能力的外部 MCP
  服务，其写入范围不受工作区沙箱限制。
  • 审查结论：符合用户 20261023T125315Z 裁定 A（“放开用户
  MCP；硬边界只对原生文件工具与 shell 成立，MCP 写入不在边界内，RESULTS 与 README
  如实写”）。代码已保留原有门禁路径比对，且在角色卡与 README
  中进行了完整声明，不构成安全违规。

  ### [P3-02] Codex Worker 在未设置信任的目录下启动需人工介入

  • 文件与行号：panes.ts:870-873
  • 严重度：P3（符合用户裁定）
  • 场景描述：如果 worker 所在的项目目录或其父仓库从未被用户在 Codex
  中配置过信任，Codex 启动时会显示 "Trust this folder?" 对话框。系统不会代按 "Trust
  and continue"（避免擅自修改用户的 ~/.codex/config.toml），而是记录
  codex_folder_trust_requested 并中止启动。
  • 审查结论：完全符合用户 20261023T125315Z 裁定（“不自动选，经上报等我”）。worker
  遇到此类情况需由用户在终端自行信任一次，行为符合预期。
  ──────
  T-141 REVIEW PASS
```
