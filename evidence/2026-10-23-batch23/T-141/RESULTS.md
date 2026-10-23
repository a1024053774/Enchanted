# T-141-1 / a1 交付记录

状态：**INCOMPLETE**。候选实现与本地契约检查已完成；执行主控正在沙箱外运行 `RUN-OUTSIDE-01.sh`，真实 Electron、两类 worker 的工具权限、问题答复闭环与三套回归的结果尚待回传，不能据此关闭 ticket。

工作目录 `/Users/luckye/Documents/Code/a2a-wt-t141`，分支 `exec/t141`，起点 `3f8813b0e`。任务来源为 T-141 ready_rev 1；交付提交号以 `DELIVERED` 消息为准，真实运行脚本另保存当时的完整 Git 版本和工作区状态。未 push、未合并 main，未修改三份 oracle 文件、地图、ticket、AGENTS.md、CONTEXT.md 或其他 worker 的源码。

## 候选行为

- Claude worker/reviewer 去掉 `--strict-mcp-config`，允许用户配置的 MCP 工具；保留 `--setting-sources ""`，避免项目设置扩大原生工具写入范围。Bash 沙箱允许所有域名、Unix socket 与本地连接，保留原生文件工具的目录限制、Git common dir 禁写与原有两条 Git 例外。
- Codex 保留 `-a never`、workspace-write、a2a hook 和角色选择的模型/强度/tier；移除项目信任、网络代理和 TUI 通知覆盖，显式开放 workspace-write 网络。写入根为当前 workspace、worker 请求目录和项目额外目录，不沿用用户配置中额外的可写根。
- Codex 排除共享 `/tmp` 与原 `$TMPDIR`，worker 的 shell 临时文件放在请求目录的 `.a2a-tmp/`；reviewer/monitor 放在各自一次性工作目录的 `.a2a-tmp/`。新 e2e 同时检查 tempfile 能运行、共享临时根不能写，另设 `shared-temp-writable` 反例；这些原生权限检查结果尚待回传。
- trusted 目录依据原生 `OSC 7501;state=idle:app=codex` 包及前台领导进程核对放行首条任务；untrusted 只代按不保存信任的 Open restricted，并等待同一个 ready 包；unset 记录 `codex_folder_trust_requested`，不按 Trust and continue。后续 idle 包不代替 Stop 或业务验收。
- worker 角色卡说明原生审批拒绝后用 `issue` 上报、必要时结束回合等主控答复。沿用原有 `answer_issue` 与会话队列，没有新增通信接口或放宽门禁检查串。
- reviewer 门禁只同步启动参数契约；会话/attempt 绑定、候选目录、原生身份、不同于 worker、禁止 resume/fork、写入范围与其余质量串保持原检查。

用户裁定由执行主控在本会话转述，引用 `20261023T125315Z-ideation-answer-001`：MCP 选 A，放开用户 MCP；硬边界只对原生文件工具与 shell 成立，MCP 写入不在边界内；门禁路径检查照旧。**用户 MCP 服务的写入权限不由 Bash 文件沙箱限制**，README 已明确，不宣称 MCP 写入也被限制在 worktree。

未改 `claudeLaunch.ts`：其中 strict MCP 参数属于旧的隔离 controller 入口；本任务明确针对 worker/reviewer，实际路径在 `panes.ts`。

## 已取得的证据

| 检查 | 结果与范围 | 文件 |
| --- | --- | --- |
| 新启动契约修前 | 预期红态：Claude 仍禁止用户 MCP | `launch-red.json` |
| 同一启动契约候选 | PASS；执行 Claude 参数生成器并核对 Codex 启动源约束，不是原生权限证明 | `launch-green-02.json` |
| 真实生产启动记录 → 真实 reviewer 参数门禁 | PASS；两类 CLI 的合法记录通过，扩大写入根、改审批策略、注入 Git 配置、错配工作目录均拒绝 | `reviewer-contract-03.json` |
| trusted 初次放行修前反事实 | 预期红态：起点源码不能按原生 ready 包放行 | `startup-red-01.json` |
| 初次放行候选与独立屏幕样本 | PASS；分包、仅一次放行、后续 idle 不替代 Stop；其他 app、普通文本、进程身份不明、已停止均不放行；外部 untrusted/unset 屏幕只选 restricted/不选 Trust | `startup-green-02.json` |
| 主控沙箱外三种目录信任探针 | 已观察 trusted 有 ready 包；untrusted/unset 停在各自对话框，没有首回合前 SessionStart；零模型调用。原始摘要的 INCOMPLETE 状态保留 | `probe-codex-start-01/*.json`、`outside-startup-facts.json` |
| 原生 untrusted 选项后续探针 | PASS（仅启动信号）：等屏幕安静再选 Open restricted 后收到 ready 包；零模型调用 | `restricted-startup-facts-02.json` |
| 主控沙箱外目录信任继承三变体 | PASS 仅指独立观察符合三种期望；CLI 0.163.0，无模型、无代按信任。原始摘要的 INCOMPLETE 保留，不当作整票 PASS | `probe-trust-inheritance-01/facts.json`、同目录原始脚本与摘要 |
| IPC 与起点比较 | PASS 仅指“不更差”：起点与候选同样在过期的 handler 名单断言失败；两者都不是 IPC 绿态 | `ipc-comparison.json` |
| RUN-OUTSIDE 工作目录修复 | 修前从仓库父目录运行，修后正确进入本 worktree，且先核对测试入口存在；只执行脚本前缀 | `runner-root-red.json`、`runner-root-green.json` |
| Python / zsh 语法、diff 空白检查 | PASS；不代替真实运行 | 下方重现命令 |

第一轮 reviewer 契约夹具因继承 a2a Git hook 而初始化失败，保留 `reviewer-contract-01.json`；夹具改为初始化时禁用该夹具 Git hooks 后重跑通过。首轮 untrusted 探针过早按 Enter，没有取得 ready 包，保留 `restricted-startup-facts.json`；按生产入口已有的安静等待规则修正探针后取得后续观察。它们均不算业务红态。

本地重现（输出换成未存在的新路径）：

```sh
node workbench/tests/test_t141_launch_contract.mjs <新摘要>
node workbench/tests/test_t141_reviewer_contract.mjs <新摘要>
node workbench/tests/test_t141_startup_signal.mjs <新摘要> [源码根目录]
python3 -B workbench/tests/t141_probe_codex_start.py --trust untrusted --open-restricted --summary <新摘要>
PYTHONPYCACHEPREFIX=/tmp/t141-pycache python3 -m py_compile workbench/tests/test_t141_loosened_limits_e2e.py workbench/tests/t141_probe_codex_start.py
zsh -n evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-01.sh
git diff --check
```

修前启动信号测试的源码由 `git archive 3f8813b0e workbench/src workbench/roles workbench/terminal workbench/hooks` 解到独立 `/tmp` 根，再链接现有 `workbench/node_modules` 和 `package.json`；该根作为测试第二参数，不修改当前候选。

## 待运行的真实入口与局限

`zsh evidence/2026-10-23-batch23/T-141/RUN-OUTSIDE-01.sh` 为每次运行创建新证据目录，依次跑：修前版本、新候选、网络关闭变异、丢答复变异、共享 tmp 可写变异、原生 Write 不受限变异，以及 T-140 / T-131 / T-132 原始回归。脚本核对红态/变异必须失败在对应断言，环境失败不算抓住已知坏实现；矩阵输出保留实际状态与错误。

新 e2e 使用真实后台、真实门禁、真实 Electron 和已安装的交互 Claude/Codex CLI；Messages/Responses 由本地脚本接口驱动，**不证明模型会自发理解或选择 issue 工作流**。它实际驱动原生审批拒绝，再驱动 issue，并核对问题面板、主控接口答复和 worker 继续交付；不以 answer_registered 事件替代送达。

只读 behavioral-acceptance-review 针对冻结候选 `bf3d00a82` 给出 FAIL：外部脚本多退一级目录、e2e 缺原生文件工具调用。原报告保留在 `acceptance-review-01.md`。后续修复脚本路径，补 Claude 原生 Write 的额外目录成功与范围外拒绝、CLI 工具结果和测试进程实际文件读回；shell 探针的结果也由测试进程读回文件核对。新增 `native-tools-unrestricted` 反例。脚本目录已取得独立红绿，原生 Write 用例与反例的结果尚待回传；没有把这些修复当作新候选独立审查通过。

MCP 放在测试专用 `$HOME/.claude.json` 的顶层 `mcpServers`，属于用户作用域配置；服务的 tools/call 收据与 CLI 工具结果共同证明调用。Codex 使用 `/tmp` 下的隔离 home，仅有夹具 provider、已核对夹具根的 trust 和两条 git allow 规则；使用无凭据的本地接口，故没有复制 auth.json，结束会删除整个隔离 Codex home。未写真实 `~/.claude`、`~/.codex`。

| 任务卡条件 | 当前结论 |
| --- | --- |
| Claude / Codex 公开地址 curl 成功 | INCOMPLETE，待真实 e2e；只计划验证公开 HTTPS，其他协议未验证 |
| 用户 MCP 可调用 | INCOMPLETE，待原生 CLI 与 MCP 服务收据 |
| 原生审批拒绝 → issue 面板 → 主控答复 → 原 worker 继续 | INCOMPLETE，待真实 e2e |
| 原生文件与 shell 越界拒绝、额外目录可写 | INCOMPLETE，待真实 e2e 与 T-140 |
| 完整 argv、reviewer 不因新参数被拒 | 本地生产 builder/真实参数门禁 PASS；真实会话审查仍 INCOMPLETE |
| 原始版本红态、至少两个变异 | 本地契约红态已取得；真实 e2e 红态与四个变异均 INCOMPLETE |
| T-140 / T-131 / T-132 回归 | INCOMPLETE，外部批次运行中，结果尚待回传 |

临时目录：Codex 已收紧共享临时根，原生红绿证据仍待 `shared-temp-writable` 与候选运行。Claude 保留 CLI 原生的每用户临时目录：[官方沙箱文档](https://code.claude.com/docs/en/sandboxing#temporary-directories)说明其用于 sandbox shell 临时文件，T-122 既有探针也记录强行禁止会破坏 shell；本票不在没有独立原生证据时改写该机制。影响是原生 CLI 必需的临时区仍属例外，不能宣称只可写 worktree/请求目录/额外目录这三类路径。新测试分别记录 `/tmp`、原 `$TMPDIR`、实际 shell TMPDIR 与 tempfile 的结果；当前尚未实测，不把历史探针当新候选通过。

执行主控补充了 Codex CLI 0.163.0 的三种无模型原生观察，脚本与摘要原样保存于 `probe-trust-inheritance-01/`：

| 已配置的信任与新目录结构 | 实际观察 |
| --- | --- |
| 信任主仓库，Git worktree 放到另处 `state/worktrees/demo/T-1` | 继承主仓库信任，直接进入输入框，出现原生 ready 包 |
| 信任 `state/review-copies`，在其下创建非 Git 目录 `r-1` | 继承祖先信任，直接进入输入框，出现原生 ready 包 |
| 信任父目录，在其下新建独立 Git 仓库 | 不继承父目录信任，出现 Trust this folder?，没有 ready 包 |

因此不能把“每次新 reviewer 副本都会暂停”当作产品结论：用户自己信任一次项目仓库和 `<state>/review-copies` 后，worker worktree 与 reviewer 非 Git 副本分别继承这两处信任，新任务与新审查不需逐个处理。尚无适用信任时才上报，等用户在终端自己信任；a2a 不代按，不写 `~/.codex`。这组三变体只证明当前 CLI 的信任继承，不证明网络、工具权限或完整 e2e。原始摘要仍为 INCOMPLETE，观察事实单独汇总，不改原始状态。

inbox `20261023T125143Z-worker:b23-t141-issue-001` 中 T-140 夹具的担忧保留为待核对项，原始 oracle 未改。`RUN-OUTSIDE-01` 正由执行主控在沙箱外运行，T-140 是否需要调整以其实际结果为准，现在不作夹具失败或修改决定。

Codex 无额外目录的 monitor 继续使用原有 read-only 模式；本票真实网络验收针对 worker/reviewer，不宣称此 monitor 网络已放开。原始夹具、截图和大日志由执行主控依 T-088 归档；本 worker 未删除已有现场。session 开始及提交前 project-map status 为 0 problems / 0 stale。

## 留给构思主控同步的治理文字

本 checkout 的 `AGENTS.md` 共 109 行，全文检索没有“worker 沙箱关网络”或“Codex untrusted”原文，不能给出不存在的行号。请构思主控核对其规范源；本 worker 未改该文件。

- `AGENTS.md:33`：“权限只在工作台内：角色卡、任务卡路径加门禁检查、每会话的 CLI 启动参数、收件箱命令行四层（T-071）。a2a 系统不写 `~/.claude`、`~/.codex` 等全局配置，钩子与权限只经每会话的启动参数传入。”该约束保持；unset 信任由用户自己处理。
- `AGENTS.md:36`：“真实 Codex 验收使用 /tmp 下的隔离 CODEX_HOME：只复制 auth.json；只信任已核对的夹具根目录；只复现用户规则中的 `git add`、`git commit` 两条 allow prefix_rule；hook 只在主控逐次批准后安装。”本次无凭据的脚本接口不需要 auth 副本。
- 关网络与单 socket 原文实际在 `.project-map/tickets/T-075-tracer-bullet-daemon-gate-pane.md:52`：“worker 的每会话启动参数只放行编排后台那一个 Unix socket，网络保持关闭”；第 59 行：“开 Codex 托管网络代理，域名名单留空，只放行后台 socket”；第 131 行记录 A2 未验证成、改走 B。它们是日期记录，由构思主控核对 T-141 后应怎样索引，worker 不改。
- 强制 untrusted 的当前使用说明原在 `workbench/README.md`“用户的 Codex home”一节，已随本候选改为继承用户配置；MCP 写入不属于原生文件与 Bash 沙箱边界也已写入该 README。门禁路径检查没有因此放宽。
