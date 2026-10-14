# T-078-2：真实 Claude CLI 的主控通路计划

状态：**INCOMPLETE，仅交计划，等待批准；本轮没有实现或运行。**

执行者 `s13-t078r` 续接原生会话；按主控 #78 改为请求 `gpt-6.1-sol / xhigh`，不传 Fast。任务沿用 T-078 `ready_rev: 1`。worktree 为 `/Users/luckye/Documents/Code/a2a-wt-t078`、分支 `exec/t078`，当前提交 `38a7eeed9db48ca114b5d9ac747028d712e60468`。合流等待 T-076-2 提交，不提前改主 checkout 或变基。

授权来自主控 #78 及用户答复 `/Users/luckye/Documents/Code/a2a/.project-map/inbox/20261012T015257Z-ideation-answer-001.md`，回复 needs-decision `20261011T101958Z`：用户选择“C 假服务为主，真登录复核 2～3 回合 (Recommended)”。不是沿用 T-074 的运行授权。

## 1. 目标、边界与事实关口

补齐 T-078-1 尚未运行的主控启动、实际角色凭据、Claude hook 接线、互相唤醒和同任务三窗格。主体是官方交互式 Claude Code CLI 加本地假 Messages API；复核只验证一个真实模型接收者的唤醒。报告区分 CLI 行为、后台行为和模型行为。

允许修改仍限 workbench、本票证据和本 ticket Resolution；不改日常 `scripts/inbox`、原验收断言、spec、地图、全局配置、正式工作台或用户 Herdr。真登录例外只接受 CLI 自写本次会话历史；不读、不复制凭据，不修改用户 Claude 设置与权限。不运行真实 Codex 被测回合。

**Tracer bullet**：先一个真实 Claude CLI → 本地 API → 实际 hook → 后台状态的最薄链路，通过后扩展双主控、库收件箱、窗口和停止。**Deep modules**：复用现有 panes、认证、门禁及只追加记录，不另建一套主控网关。**Ubiquitous language**：沿用 CONTEXT 的窗格、派发、唤醒、回合、人工介入和未知状态。

已知依据：T-074 `rev4-claude/launch.json` 使用 `/Users/luckye/.local/share/claude/versions/2.1.296`、模型 `claude-haiku-5-5`；保存的 `rev2-preflight/local-help.json` 支持 `--effort`、`--settings`、`--permission-mode` 和 `--tools`。这些是旧运行／帮助证据，不代替本轮版本与协议探针。该帮助明确 `--bare` 会跳过 hooks，因此本计划不用它。

实施获批后先核对固定二进制、版本、帮助和最小 Messages 协议，结果保存新标签。`--effort low` 在这个固定 CLI／模型组合是否接受、hook 原始字段是否足以安全匹配提交、本地 API 是否引出完整权限流程，都仍需探针确认。失败即停，不换 CLI、模型、认证或适配路径，不读屏推断状态。

## 2. 隔离目录与进程

每个阶段新建 `/tmp/t078-2-<label>-<随机值>/`，保存其 realpath。其下：`repo/` 是夹具项目，`state/` 是唯一后台库，`tmp/` 是临时文件，`shell/` 是空 ZDOTDIR，`operator.json` 是本次管理凭据；每个主控另有 `home-<角色>/`、`claude-<角色>/`、`role-<角色>.md` 和 hook 设置文件。角色文件从批准的角色卡生成，不加载实施仓库中的待办或日常任务。

后台、API 和 Electron 由获批脚本启动，服务进程脱离调用者进程组。API 只绑定 `127.0.0.1` 的系统分配端口；在启动 CLI 前将端口、PID、session、launch、thread、argv、环境白名单、角色卡版本和代码提交完整展开为 launch manifest。秘密 capability 单独置于私有进程环境／文件，不写 manifest 或原始 API 请求头。

库只注册夹具项目与受管任务。两个主控属于同一任务；worker 窗格继续使用明确标注的确定性原生接收器，不能冒称真实 Codex。最终截图证明实际双 Claude CLI 和 worker 窗格的归属、输入及放行状态。

## 3. 准确启动参数与环境

下列为 argv 数组，不经 shell 拼接解释。`SESSION_UUID`、`ROLE_FILE`、`SETTINGS_FILE` 在每次批准前用该次 manifest 的具体值替换；不能复用上一轮 session。工作目录固定为该轮 `repo/`，shell 为 `/bin/zsh`，shell argv 为 `['-f','-i','-c', '<逐参数安全引用的 CLI 命令>; exec /bin/zsh -f -i']`。

### 假服务：每个主控

```text
[
  "/Users/luckye/.local/share/claude/versions/2.1.296",
  "--session-id", SESSION_UUID,
  "--model", "claude-haiku-5-5",
  "--effort", "low",
  "--permission-mode", "manual",
  "--settings", SETTINGS_FILE,
  "--append-system-prompt-file", ROLE_FILE,
  "--strict-mcp-config", "--mcp-config", "{\"mcpServers\":{}}",
  "--tools", "Bash,Read",
  "--disable-slash-commands"
]
```

从干净白名单构造环境：`PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin`、`SHELL=/bin/zsh`、`TERM=xterm-256color`、`COLORTERM=truecolor`、`LANG=en_US.UTF-8`、`LC_CTYPE=UTF-8`，`TMPDIR=<本轮>/tmp`、`ZDOTDIR=<本轮>/shell`、`HOME=<本轮>/home-<角色>`、`CLAUDE_CONFIG_DIR=<本轮>/claude-<角色>`、`DISABLE_AUTOUPDATER=1`；模型环境仅 `ANTHROPIC_BASE_URL=http://127.0.0.1:<已绑定端口>`、`ANTHROPIC_API_KEY=a2a-fixture-key-not-a-secret`。假 key 是公开夹具字符串，不是用户凭据。

不继承 OAuth token、真实 API key、代理、Bedrock/Vertex/Foundry 选择、父会话 A2A/CODEX 身份或 Git hook 环境。启动者不读取用户 auth 文件／keychain；若 CLI 要求登录、访问用户认证或本地请求未到指定假服务，停止该阶段。隔离 HOME 无条件使用，覆盖可能出现的 `.claude.json` 写入；不上用户 HOME 试错。

后台签发本角色的 `A2A_PROJECT/TASK/SESSION/ROLE/PRESET/LAUNCH/STATE` 与独立 capability。角色来自后台持久化的 preset 与凭据绑定，不信任 `--from`、`--role` 或环境自报；不能把 operator 凭据交给主控 CLI。hook 与 inbox 客户端使用同一后台入口，若沿文件转交，必须保留实际 launch、native session 和角色核对。

`SETTINGS_FILE` 只含经批准的本次 hooks，**不含** apiKeyHelper、登录、持久权限或免确认集合。UserPromptSubmit、Stop、PermissionRequest 的 command 精确为该次 argv 中的 Node 绝对路径、`/Users/luckye/Documents/Code/a2a-wt-t078/workbench/src/gates/cli.ts --state <本轮 state> signal --launch <本次 launch>`，stdin 原样转交；每个 hook 设 3 秒期限。若需 CLI 新事件，先列原始字段和用途交主控批准。PermissionRequest 仅证明批准状态，不用于推断回合结束；不自动批准权限。

### 真登录：只替换构思主控接收者

执行主控继续用已通过的假服务会话发送 report；构思主控先结束旧隔离会话，再用新 launch/session 启动真登录会话，不在同一进程切换 provider 或复用 capability。

```text
[
  "/Users/luckye/.local/share/claude/versions/2.1.296",
  "--session-id", REAL_SESSION_UUID,
  "--model", "claude-haiku-5-5",
  "--effort", "low",
  "--settings", REAL_HOOK_SETTINGS_FILE,
  "--append-system-prompt-file", REAL_ROLE_FILE
]
```

真登录环境保留用户正常 `HOME=/Users/luckye`，不设置 CLAUDE_CONFIG_DIR 或假的 ANTHROPIC_BASE_URL/API_KEY，不注入、提取或复制认证。只传本次 A2A 身份、临时目录、终端环境和已批准 hook 设置；清除父 worker 身份及假服务认证变量。不传 permission-mode、permission 覆盖或登录命令，不写用户设置文件。每会话 `--settings` 仅追加已批准 hooks；审批前交出完整 JSON，确认无 permissions 或认证覆盖项，不能写入用户设置文件。

CLI 可用正常登录且可自写本次 `~/.claude` 会话历史。只读回已知 session 的精确 transcript 路径，不枚举认证目录，不归档整个 `.claude`，也不删除用户会话历史。若出现登录、账户选择、权限设置更改或未批准启动提示，保存可见状态并停；不得把下一条提示或 Enter 当成同意。模型不是 `claude-haiku-5-5`、CLI 不支持所列参数，均停下交主控。

## 4. 假服务协议与运行顺序

假服务按公开 Messages SSE 格式返回 text/tool_use 与结束事件，支持探针实际需要的 `/v1/messages` 和 token-count 请求；其他路径、异常格式、重试或超预算请求单独留原始失败并停止。不代理到外部服务。请求体仅保存夹具输入；认证头不留证。

通过独立的屏障控制“收到请求但尚未结束”“结束 SSE”“返回指定 inbox Bash tool_use”。期望值来自任务合同和外部输入 nonce，不从 CLI 输出推导。工具请求限定本轮夹具及库客户端命令；权限正例和反例由真实 CLI 产生，不由假服务伪造 hook、权限事件、CLI 历史或后台 PASS。

1. 最小协议：一个真实 CLI，一次短输入；核对实际 API 请求、UserPromptSubmit、Stop、native session 和后台记录。这是可行性探针，不充当产品红态；协议不通即停。
2. 产品红态：在 T-078-1 起点记录只能静态 prepare、不能启动角色窗格的入口缺口。下游规则未到达不能算各项红态；后续每项新行为用撤回修复或单规则坏变异体补独立反例。
3. 双主控和凭据：实际 executor 写 report，ideation 收件箱和窗格收到同一条带标记唤醒；伪造 from/role、错误 session、旧／撤销 capability 应在写入前拒绝。角色记录必须保留真实 caller。
4. 忙闲：后台写 CR 立即记忙，不等待 hook；API 屏障持有回合时发 report，库先入队，PTY 无注入。放开真实 CLI 的回合结束后只送达一次；注入先登记、bracketed paste 后独立 CR，用户输入记录跳过注入。
5. Esc：屏障中断，晚到 Stop、重复 Stop 和重复 report 都不能自动放行；通过 Electron 用户放行按钮送达，记录 user action。不能用测试调用内部方法替代窗口入口。
6. 紧急停止：executor 收 stop 后执行只中断并 ack；另一个用例不 ack，真实等待 120 秒，119 秒禁止 break-glass，超过 120 秒仍无 ack 时 ideation 仅中断自建 worker，不能 kill/reclaim/archive。记录从实际凭据取 caller，并测试参数冒充、已有 ack、错误目标和撤销身份。
7. 同任务三窗格、手工输入与注入、关闭窗口和重启 unknown；不接管旧 PTY，不自动重放。Claude 原始事件缺关联字段时不虚构 Codex turn；提交匹配不能安全建立就保留 unknown 并上报。

允许先完成无模型的静态代码／纯逻辑检查，但获得本计划批准以前一律不开始。所有实际 CLI、API、Unix socket、Electron、ps 及进程信号步骤统一交本票 outside-sandbox.sh 执行，不申请提权。

## 5. 真模型复核与预算

假服务完成且证据读回一致后才进入真登录。真阶段使用上面一名真实构思主控接收者，另一名 executor 仍是实际 CLI 加假模型；报告明确这不是“两名真实模型互相协作”的证据。

默认 **2 个真实回合**，全卡最多 **3 个真实模型回合**：第一回合是短基线输入，确认真实 Haiku、hook 和 idle；第二回合由实际 executor 的 report 触发一次真实唤醒，输入带独立 nonce，真实回复必须包含该 nonce，核对后台登记、PTY 字节、实际模型记录与一次 Stop。第三回合只在前两回合通过、需要补一项明确复核时，另列目的和剩余额度批准；不能用于重试失败。

预算按实际模型调用计数：工具续轮、失败调用、误注入及自动续轮同样消耗，不只数用户 CR。真阶段要求模型不调用工具；任何工具／额外请求先停，不能补跑掩盖。若 CLI 无法提供可核对的调用计数，停止，不推断“仍有额度”。每个真回合限 60 秒，短回复目标不超过 80 tokens；不额外引入模型评判或真实 Codex reviewer 回合。

假服务主检查合计最多 18 次根输入提交、48 次 Messages 请求；每个常规用例 60 秒，停止用例上限 150 秒，整阶段 15 分钟。超过上限即保留 INCOMPLETE；没有自动重试、换账号或换模型。Codex 周额度耗尽也立即保存现场停止。

## 6. 逐次审批点

| 审批点 | 主控在批准前可审的具体产物 |
| --- | --- |
| P0 | 本 PLAN-2；先批准实施，当前交付到此停止 |
| P1：第一次真实 CLI／假服务探针 | 固定二进制版本、完整展开 argv/env 白名单、API listen 地址、隔离 HOME、hooks JSON、1 回合输入、退出／清理脚本；未批准不启动 |
| P2：假服务双主控检查 | 每个新进程分别提交 launch manifest、角色卡、hook 配置、场景和请求预算；启动／重新启动每次单独批准，不因 P1 获批推定全部启动授权 |
| P3：第一次真登录启动 | 明确 NORMAL HOME、模型、只追加 hooks、真实会话历史例外、不会读取认证；列 2 回合确切输入／发件流程和第三回合保留。主控批准前不启动真 CLI |
| P4：真实第 2／第 3 回合或任何真会话重启 | 发输入前核对已消耗模型调用与剩余额度，分别批准；新 CLI 进程须重新审批完整 argv。失败和额外模型调用仍占预算 |
| P5：交付合流 | 等 T-076-2 提交，主控安排 rebase；保留其质量／身份／停机行为，在合流候选检查本票及 8/9/18/CAS/反例，一次 fresh-context 独立审查后显式交付 |

审批申请经本票证据脚本、READY 停点交执行主控；登录、密码、系统权限等不在代批范围，出现即停并由主控交用户。已有选 C 的授权不重复询问认证路线，但具体启动仍按以上审批执行。

## 7. 停止条件、证据与清理

出现协议不兼容、登录要求、错误模型、外部调用、CLI 自动更新、记录器失败、无可靠回合匹配、来源无法核对、窗口输入与注入混合、越权写入、重复副作用、预算越界、未批准权限或 spec 冲突：立即停止对应阶段，保留原始红态／未知结果，不回退到模拟 CLI、读屏、替代登录或自动重试。产品失败按任务卡先保留红态，修复 diff 交主控审；范围／验收问题写 issue。

新标签下保存完整命令、时间、PID/launch/session/角色绑定、API 请求体与 SSE、hook 原始 stdin、后台库读回、PTY 字节、截图及新会话 transcript；capability、用户凭据、认证头不入证据。每项产物有重放命令和候选提交，>5 MiB 原件按规则外置归档。假 API 证明协议驱动的真实 CLI/hook/工具权限／状态与后台行为；真模型仅证明本次 Haiku 回合、nonce 响应和真实唤醒。两类结果分别写 PASS/INCOMPLETE，不用假模型输出证明模型判断。

清理只针对 launch manifest 记录的自建进程及本轮目录：先停止接纳输入，确认自建 CLI/后台/API 退出，核对 PID 与启动身份，删除本次 capability 和临时 HOME；异常未确认先保存现场，不删除。假服务空 HOME 可整体删除；真登录用户 `.claude`、`.claude.json` 和既有历史一律不清理。只归档已知本次 session 的记录，不复制用户设置或凭据。不关闭用户 Herdr、不停止正式后台、不 push。

本轮仅新增本文件；计划批准前不生成测试服务、hook 文件、启动脚本或任何进程。T-078 保持 open，最终状态仍须由实际证据决定。
