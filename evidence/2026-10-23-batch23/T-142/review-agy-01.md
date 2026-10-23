# T-142 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pS，交互 auto 模式（只用读文件工具），只读副本，候选 cd8c31b76。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-142-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-142-r1/prompt.txt)"
# pane wG:pS started 2026-10-23T16:52:35Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，无发现项。

## 窗格中的报告原文

```text

○ Thought for 5m 50s (The `AssertionError` confirms the defect: the base revision correctly rejects `terminal_open` due to a s...)
● Explored 7 files (evidence, full.diff, T-142-controller-terminal-open.md, +4)
● Spawned 1 subagent
… 5 more actions (3 reads, 2 subagents) …
● Messaged 1 subagent
● Explored 38 files (README.md, RESULT.json, RESULT.json, +35) (ctrl+o to expand)

▸ Thought for 32s, 4.2k tokens

   T-142 独立审查报告：主控命令 terminal_open

  本审查基于 /Users/luckye/Documents/Code/a2a-review/T-142-r1/ 下的候选代码
  cd8c31b76（只读副本）、full.diff、ticket、card.md、RESULTS.md、探针材料与沙箱外各轮运行证据进行核验。
  ──────
  ## 一、产品代码核对

  ### 1. 门禁与身份校验

  • 在 daemon.ts:353-358 中，terminal_open 位于 terminalCommand 处理流中：
      • 第 353–354 行通过 const roleRequest = roleRequests.approved(terminal.id); if (!roleRequest) throw new
      Refusal("approved_role_required"); 强制核对终端角色，只有经界面批准的主控会话才能继续。
      • 第 356 行检查 if (input.project !== undefined && input.project !== roleRequest.project) throw new
      Refusal("role_project_mismatch");，禁止主控跨项目操作。
      • 第 357–358 行检查所属项目是否仍处于打开状态：const project = store.openedProjects().find(project => project.project_id
      === roleRequest.project); if (!project) throw new Refusal("project_not_opened");。
      • 完全复用既有角色审批与项目作用域机制，未创建平行门禁或特权旁路。


  ### 2. cwd 范围校验

  • 在 daemon.ts:359-363 中：
      • 第 359 行判断 typeof input.cwd !== "string" || !isAbsolute(input.cwd) || !existsSync(input.cwd) || !statSync(input.cwd).
      isDirectory()，严格拒绝非字符串、相对路径、不存在路径和非目录文件，抛出 Refusal("invalid_shell_cwd")。
      • 第 361 行通过 const cwd = realpathSync(input.cwd); 将传入路径解析为真实规范物理路径。
      • 第 362 行使用 [project.repo, ...project.extra_directories].some(root => cwd === root || cwd.startsWith(root.
      endsWith('/') ? root : root + '/')) 进行范围核验：
          • 放行：项目主目录自身、主目录子目录、已配置的额外目录（来自 T-140 的 extra_directories）自身及其子目录。
          • 拒绝：通过末尾斜杠处理（root.endsWith('/') ? root : root + '/'）杜绝了具有同名前缀的兄弟目录逃逸（如 /repo-sibling
          不会匹配 /repo/）；上级目录无法匹配前缀；符号链接经 realpathSync 展开后若指向项目范围外，前缀不匹配，均被第 363 行抛出
          Refusal("terminal_cwd_outside_project") 拦截。



  ### 3. 终端归属与属性

  • 在 daemon.ts:364 中直接调用 panes.startShell(project.project_id, cwd)：
      • 创建的记录中 role: "shell"，且 task: null、attempt: null、session: null、fence: null。
      • 第 275 行通过 this.rememberOpen(launch, ...) 登记在项目层打开终端列表（pane_layout_opened 的 task 为 null），不进入任何
      task 的视图布局，属于纯粹的项目普通终端。


  ### 4. 异常处理与无 fallback 检查

  • 业务分支均直接抛出对应
  Refusal（approved_role_required、role_project_mismatch、project_not_opened、invalid_shell_cwd、terminal_cwd_outside_project）
  ，无 try...catch 吞噬异常，无降级为默认路径或隐式 fallback 的行为。

  ### 5. CLI 与文档更新

  • terminalCli.ts:44-83 在 usage 中声明了用法，并在第 81–83 行增加了命名参数形式 a2a call terminal_open --cwd <绝对目录>
  解析，同时兼容原有的单参数 JSON 形式；参数不合法时打印用法并返回 2。
  • SKILL.md:67-78（第 3、7 步）与 README.md:127-130 同步补充了该主控命令的作用、权限限制、真实路径校验及终端归属说明。
  ──────
  ## 二、测试独立性与夹具核对

  ### 1. 原始工具回执绑定的可信度

  • 在 test_t142_terminal_open_e2e.py:267-283 中，函数 model_return(command)：
      • 遍历 fixture.api.bodies 捕获真实 Claude CLI 回传到本地脚本端点的底层 HTTP 协议报文。
      • 先建立 tool_use 记录：calls[part['id']] = part['input']['command']，再精确匹配 part['type'] == 'tool_result' and calls.
      get(part['tool_use_id']) == command。
      • 读取的是 CLI 工具底层真实返回的 tool_result，而非模型回复的正文（prose）或自报陈述，杜绝了模型幻觉或自圆其说。
      • 随后在第 346–370 行将回执内容与后台多维度交叉比对：
          • 核对 launch.id 与 workbench_snapshot 状态完全一致；
          • 在新开终端的真实 PTY 中执行 pwd 并校验落盘路径；
          • 核对侧栏快照中仅列入项目 terminals，未混入任务 agents；
          • 核对 pane_layout 确认新终端不在任务分栏中；
          • 在 Electron 界面中定位对应元素，真实点击并驱动界面 IPC 输入 pwd 再次比对。



  ### 2. 测试夹具改动的合规性

  • 夹具在第 307–312 行设置了隔离环境配置：
      • hasCompletedOnboarding: True 与 hasSeenAutoDefaultNudge: True；
      • permissions: {'defaultMode': 'default', 'allow': ['Bash(a2a request:*)', 'Bash(a2a call:*)'], 'additionalDirectories':
      [str(fixture.out.resolve())]}。
  • 探针依据与成对实验：
      • 依据 probe_t142_bash_redirect.py 及 probe-local-02.json:273-276 证实，Claude Code 2.1.309
      在对重定向目标写入时会要求二次确认（Output redirection ... needs approval），即便该目录已被列入
      additionalDirectories；而裸 a2a call 则完全正常。
      • 移除测试脚本中让模型在 Bash 命令里追加的 > out/main.json，改由脚本化接口捕获
      tool_result，属于测具数据采集通路的修正，并没有放松被测系统（terminal_open）的权限与功能断言。
      • 全程未注入任何诸如 Enter/Esc 的模拟按键来关闭对话框，完全依赖规范的配置文件项杜绝提示窗。

  ──────
  ## 三、红态与变异有效性核对

  ### 1. 起点红态（Red State）

  • 基线修订版本：c113e71203bd37e151241b6ce44bd4bf773e356f。
  • 在起点版本中，daemon.ts 尚未支持 terminal_open 分支，主控调用时落入 else throw new Refusal("role_command_not_scoped")。
  • red-revision-backend-05.json 及汇总脚本明确断言：进程退出码为 1，且失败精准落在 AssertionError: main_opened: {'ok': False,
  'error': 'role_command_not_scoped', ...}，证明红态真实落在未实现该命令的缺陷上。

  ### 2. 变异测试（Mutant）

  • 变异类型：cwd-unchecked。
  • 变异操作：在 daemon.ts 中删除范围核验逻辑 if (!withinProject) throw new Refusal("terminal_cwd_outside_project");。
  • mutant-backend-05.json:104-134 显示：
      • 合法的 main、extra、child 终端均成功创建；
      • 但同级兄弟目录 demo-sibling 被错误放行并成功创建终端（observed.sibling.ok == True）；
      • 测试在第 374 行的 check('sibling_refused', ...) 处精准捕获异常 AssertionError: sibling_refused，退出码为 1。
      • 变异精准证伪了不校验 cwd 范围的坏实现。

  ──────
  ## 四、修改边界与受保护验收文件核对

  根据 card.md:11-12 约束核对 full.diff：

  1. 改动文件列表：
      • workbench/README.md（允许）
      • workbench/src/daemon.ts（允许）
      • workbench/src/terminalCli.ts（允许）
      • workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md（允许）
      • workbench/tests/probe_t142_bash_redirect.py（允许，新探针文件）
      • workbench/tests/test_t142_terminal_open_e2e.py（允许，新测试文件）
  2. 受保护验收文件（oracle_paths）：
      • workbench/tests/test_t121_role_request_e2e.py：未修改。
      • workbench/tests/test_t124_controller_e2e.py：未修改。
      • workbench/tests/test_t139_t143_views_perf_e2e.py：未修改。
  3. 禁止修改区域：
      • workbench/src/gates/**、.project-map/**、AGENTS.md、CONTEXT.md 均未受改动。
  4. 回归情况：第 1 轮外部测试已证实 T-124、T-139/T-143 均 PASS；T-091 与起点一致不更差；T-121 属于已知既有冲突（由 T-147
  解决），T-142 未越权改动。
  ──────
  ## 五、审查发现项（P0–P3）

  本轮未发现任何阻碍合并或影响正确性的缺陷（无 P0、P1、P2、P3 级别发现项）：

  • 权限与作用域检查严密且无旁路；
  • 真实物理路径与边界校验无漏洞；
  • 独立端到端证据链完整且可复现。
  ──────
  ## 六、裁定

  T-142 REVIEW PASS
```
