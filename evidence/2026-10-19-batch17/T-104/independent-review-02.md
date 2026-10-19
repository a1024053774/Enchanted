# T-104 第二轮独立审查（2026-10-19）

STATUS: PASS

TARGET: `45c127b5af03bfdc50802579bda50b88a98dc2c7`，分支 `exec/t104`；起点 `cc18d93dbbcf2ee641dc92befe68e5b0609b4807`；中间合并 `edd469f6b9d2d34bedb3a9479159fbb917dc43d5`，第二父提交 `ea206484b8bcdae19fa4edd91b7553af22ff757b`。

第一轮的两项问题已关闭：shell 逐次输入元数据不再追加，重启自动另建 shell 的错误实现已被完成条件拒绝。本轮未确认需要修复的新缺陷。此结论限本票开发候选的审查，不代表打包、发布、集成或日常派发切换已经完成。

EVIDENCE:

## 标准、独立性和范围

- 按派发顺序读取主仓库 reviewer 角色卡、AGENTS、通过 `ls` 定位并用 `git show main:.project-map/tickets/T-104-workbench-plain-shell-pane.md` 读取的 ticket，以及两段 RESULTS；另读 MAP、CONTEXT 和当前 intent。验收答案来自 ticket 第 1～5 条及本轮主控裁定，作者报告和脚本用于定位原件。
- 用户原话按本轮派发引用：`选"A 先补功能再打包"`。记录范围按本轮更正：不记录 shell 输入正文及逐次输入元数据，允许布局和进程诊断事件，保留 agent 的输入和人工介入记录。没有沿用第一轮任务书写过头的“只有创建和关闭事件”。
- **Tracer bullet**：检查 UI → IPC → daemon → PTY → 登录 zsh → 关闭／恢复。**Deep modules**：检查复用的窗格、凭据和事件流是否仍承担各自职责。**Ubiquitous language**：普通终端为项目级 `role: shell` 窗格，和 task、attempt、受管 worker 分开。
- 使用 `git show 45c127b5a`、`git diff cc18d93db 45c127b5a`、`git diff ea206484b 45c127b5a`、`git show --cc edd469f6b` 读取候选和合并原文。开始时 worktree 干净，最终候选号未变。
- 本轮只在新建的 `/private/tmp/t104-review-02-b8gax5bl/` 和获准的两个交付文件写入。副本用 `git archive` 提取，没有新建 worktree；没有修改候选、依赖原件、门禁、全局配置或旧证据。
- 本轮亲自运行隔离合同、八次夹具对照及三个变异；真实 daemon／PTY／Electron 证据来自主控已运行的原件，本轮没有重新启动这些进程，也没有调用供应商 CLI、模型或子 agent。两类证据在下文分别标明。

## 第一轮问题与本次修复

| 项目 | 独立核对 | 结论 |
| --- | --- | --- |
| R1：逐次输入元数据 | `daemon.ts:69` 按后台保存的窗口角色识别 shell；已关闭或重启的窗口按原 `window_opened` 与 launch 关联判断，不信任客户端自报角色。`:189` 仅对非 shell 追加 admitted；`:448` 在认证和通用事件追加前识别，`:452`、`:457`、`:463` 同时覆盖成功与拒绝路径。序号和 request_id 的内存检查仍在 `:181`。 | PASS |
| 已知坏候选是否真的被新检查拒绝 | `review-fix-02-backend/metadata-known-bad` 的 36 个 src 文件逐字节对应 `d54826223`；真实运行在 privacy 阶段报“shell 逐次输入事件进入事件流”。归档库确有 8 条 admitted。好候选同场景退出 0，库中 admitted 为 0。 | PASS |
| 重启反例是否生效并被抓住 | `restart-mutant` 的 36 个 src 文件相对当前候选只有 `panes.ts` 一处差异：在 recover 的 shell 分支加 `this.startShell(record.project, record.worktree)`。第一次 daemon_stopped 后，seq 60、62 确有两条新 shell_created 和新 PID 81916、81917；测试在 restart 阶段报“后台重启新增了 shell launch 或创建事件”。 | PASS |
| 测试是否只看旧 launch | `test_t104_shell_e2e.py:257`～`:270` 比较全部 shell launch 和创建事件，并核对完整项目打开集；UI 场景也做前后 inventory 比较。好候选重启前后均为同两个 launch；不再只验证旧 launch 为 ended。 | PASS |
| 是否削弱其他检查 | 本轮新增隔离探针执行真实 window handler、Panes 写入串和门禁 SQLite 记录器：shell 写入接收器但不产生 user_input／人工介入；worker 的独立哨兵输入产生一条同 attempt 的 user_input 和一条带相同 input_id、fence 7、spec_rev 9 的 human_intervention，并保留 admitted。 | PASS（隔离层） |

上述真实后台坏版本均退出 1，业务错误、阶段和实际错误效果相符；不是依赖缺失或启动失败。各次 `cleanup_complete` 为 true。隐私正文变异也只有一处新增原始请求日志，确实在 privacy 阶段报“shell 输入内容泄漏进事件流”。未把测试报告使用的 INCOMPLETE 标签误读为坏版本未被拒绝。

## 按 ticket 重建的语义检查

| 验收语义 | 依据与结论 |
| --- | --- |
| 属于项目，不绑定 attempt，不经门禁 | PASS。`panes.ts:127` 的 task、attempt、session、fence、spec_rev 均为空；创建调用 startShell，不走 claim／submit。当前真实 UI 库中两个 shell launch 的这些身份字段也为空，project 为 alpha。项目内跨任务保留，跨项目不混入另一项目布局。 |
| 创建／关闭事件有 shell 角色，无输入正文和逐次元数据 | PASS。当前真实 UI 库有两条 shell_created、两条 shell_closed，无 admitted；正文 nonce 检查、通用请求 ID 检查和 agent 记录表为空检查均执行。布局、窗口开关和进程诊断事件仍保留，符合本轮裁定。 |
| 输入不算人工介入 | PASS。shell 分支在 `daemon.ts:194` 直接调用 shellInput，未进入 recordInput／appendUserInput；本轮隔离探针核对写入效果与零记录。当前真实 UI 库的 user_inputs、user_input_ingress、dispatch_records 均为 0。 |
| 登录 zsh，无模型参数或全局写入 | PASS。固定 `/bin/zsh -l -i`，只添加 A2A_PROJECT，剔除继承的 A2A_*、GIT_CONFIG_*、CODEX_THREAD_ID；启动记录只保存该项目环境。普通系统环境仍继承，并非把 PATH、HOME 全部清空。真实独立 cwd、登录和交互配置读回符合输入；未见写全局配置的产品路径。 |
| 关闭结束子进程 | PASS（本场景）。关闭先串行等待输入，再观察进程树，SIGHUP 后逐个核对退出；不能确认则拒绝。当前 UI 记录中 shell 84047、前台／后台 sleep 84061、84060 的独立 ps 均已无记录；另一打开终端 84073 在关闭界面时仍活，停止后台后退出。 |
| 重启显示已结束且不重新拉起 | PASS。recover 对 shell 明确 continue，两个恢复循环均不进入 agent 续接；历史快照返回 ended 和空 shell_pid。当前真实 UI 的完整 inventory 不变，重开图显示“已结束”、只读且进入按钮禁用；实际自动启动变异被拒。 |
| 与 agent 标识分开 | PASS。普通终端显示“普通终端 / zsh / 项目目录”，无 attempt、人工介入提示和队列放行按钮；同窗口历史 worker 仍显示受管身份、历史 attempt、只读和人工介入提示。 |
| 门禁与操作锁不变 | PASS（差异及相关回归）。相对合入 main，本票未改 gates/core.ts；相对 cc18 的 core 差异只有 T-103 的只读 listProjects/listTasks。锁、fence、CAS、submit、验收、集成路径未被本票改写。 |

## 安全与合并

- `daemon.ts:143`、`:147` 的 shell_start／shell_close 均要求 operator。更前面的匿名白名单、launch 仅 signal、window 命令白名单仍拒绝其他身份。shell 不能充当 agent 身份，派发也要求 agent pane。已有真实后台原件包含匿名创建、窗口越权、跨项目、伪造 shell launch 身份等拒绝结果。
- **cwd 的准确边界**：`app/main.ts:109` 的 new-terminal IPC 无 renderer 路径参数；`:116` 重新读取当前任务，`:118` 核对任务／项目，`:121` 使用该任务 repo。窗口主 frame、每窗格 key 和窗口间隔离仍生效。本轮将 cwd 改成 `/private/tmp` 的变异被明确的 cwd 业务断言拒绝；删掉 frame 校验的变异也被 iframe 拒绝断言抓住。
- **operator CLI 没有项目目录沙箱**：`daemon.ts:145` 将已认证 operator 的 cwd 交给 `panes.ts:120`，后者只检查已有绝对目录并 realpath，不查询项目登记或 worktree 归属。因此 operator 可以传项目外目录，也可以使用未登记但格式合法的项目号。这是明确保留的可信管理接口边界，不能把 UI 的防注入结论扩大为后台对 operator 的目录限制；未发现匿名、agent 或 renderer 借此越权的路径。本轮不据此擅自新增权限合同。
- 新增桥接只有无参数 newTerminal，不公开 operator 凭据、通用后台命令或任意路径。完整 main/preload 合同仍运行未知窗口、iframe、跨窗格 key、历史 worker、重复 launch 和关闭竞态等断言。增加窗口级 IPC 后未确认新的可达提权。
- 合并原文同时保留 projects_list／tasks_list 与 shell_start／shell_close／pane_layout；目录查询的只读分类、不追加请求日志的行为、window 载荷脱敏，以及 CLI 参数和 noTask 集合均保留。当前候选相对 ea206 的差异没有改写 T-103 的列表实现。主控 merge-01 原件及当前 review-fix-02 的 picker／shell 合同通过，与该静态结论一致。

## 两项旧回归：本轮八次对照

原件：本轮 `/tmp` 目录中的 `fixtures-results.json`。每个产品版本分别使用 cc18 的旧夹具和当前修正夹具，源码、夹具和输出路径分开保存。

| 产品版本 | 旧夹具 worker-dispatch／conflict-panes | 修正夹具 worker-dispatch／conflict-panes |
| --- | --- | --- |
| cc18d93db | 退出 1／1 | 退出 0／0 |
| 45c127b5a | 退出 1／1 | 退出 0／0 |

- worker-dispatch 的旧夹具使用假 PTY PID 123，却查询系统真实 PID 123；两版本均报 libproc 的 `proc_pidinfo_failed_or_short / errno 1`。修正提供与假 PTY 一致的进程观察边界，其他 exec 仍执行真实版本查询。
- conflict-panes 两版本旧夹具均在 new_attempt_binds_only_its_own_rollout 报 `restore_argv_missing`；修正仅给合成 argv 补上 `-a never`，满足已有 resumeArgv 合同。
- 逐行比较确认两文件既有断言没有删、改或放宽；辅助身份、领导者替换、原生日志绑定和登记先于发送等检查保留。旧夹具失败不算 T-104 的产品红态，也不证明真实 PTY 边界。

COUNTEREXAMPLE:

## 本轮新建的一次性变异

先在候选副本运行完整 `test_t091_pane_ipc.mjs --contract shell`，退出 0；其 direct 版本也先退出 0。direct 版本保留原 exercise、夹具及业务断言，仅去掉外层历史版本／内置变异自检，以便直接判断本轮错误实现。另一个输入探针先在候选退出 0，再运行 M3。

| 单处错误实现 | 本轮结果 |
| --- | --- |
| M1：main 的新建终端 cwd 从 current.task.repo 改为 `/private/tmp` | 退出 1，`Terminal cwd must come from the selected task`，实际与期望目录明确不同。 |
| M2：windowTarget 删除 senderFrame 与 mainFrame 的比较 | 退出 1，iframe 的 assert.rejects 报 `Missing expected rejection`。 |
| M3：daemon 恢复无条件 window_request_admitted | 退出 1，独立输入探针报“shell 逐次输入元数据必须为零”，实际 1、期望 0。 |

复现命令及完整退出结果在 `ipc-results.json`、`input-results-02.json`；命令形式如下，输出须用未使用的新路径：

```sh
node --experimental-vm-modules /private/tmp/t104-review-02-b8gax5bl/ipc-direct.mjs /tmp/新IPC结果.json --source /private/tmp/t104-review-02-b8gax5bl/mutant-cwd --contract shell
node /private/tmp/t104-review-02-b8gax5bl/input-contract-02.mjs /private/tmp/t104-review-02-b8gax5bl/candidate /tmp/新输入结果.json
```

上述命令从本仓库运行，IPC 合同的历史原文只通过只读 git show 取得。输入探针供应当前 attempt 状态、窗口对象和 PTY 接收器，执行的是候选原 handler、Panes 和 SQLite 记录器；没有把它当成真实 socket／原生进程证明。首版探针因未剥离 TS 类型而语法失败，保留 `input-contract.mjs` 和 `input-results.json`；修正测试装载器后使用新文件、新结果，不把装载失败计作抓住变异。

## 真实原件、截图和版本绑定

- 核对 backend-03、merge-01、ui-01 和当前 review-fix-02；本轮结论优先使用后者的真实原件。`review-fix-02/ui/source-snapshot` 的全部 19 个文件与 `git show 45c127b5a:<path>` 逐字节一致，包括产品文件、验收脚本和运行脚本。run.json 的 HEAD 字段仍为 d548，是提交前运行，不能单看该字段归错版本。
- backend 的 known-bad 36 个 src 文件对应 cc18，在 CLI 参数解析处因不认识 `--cwd` 失败，这是新功能缺失的合同红态，不把它说成 daemon 已收到命令后的拒绝。真实 UI 红态另外确认无按钮、无桥接、无 handler。
- 三个后台变异的 src 相对当前候选分别只有正文日志、admitted 条件、recover 新建调用这一处错误；已检查实际差异、失败阶段与数据库，不仅采信 suite 的 PASS。
- 目视检查当前真实运行的五张图：red-no-terminal 无入口；green-terminal 显示独立 nonce、中文空格 cwd、LOGIN=on、RC=loaded，普通终端与历史 worker 并存；green-closed 移除 shell；green-project-shell 仍显示运行中；green-ended 显示已结束、只读、进入按钮禁用。历史 worker 的黄色“未恢复”提示仍保留。
- 当前 UI 归档主库只有 4096 字节，数据仍在配套 WAL。首次 immutable 读取主库报无表，未计作产品问题；本轮将 sqlite3、WAL、SHM 一起复制到新 `/tmp/ui-db-copy` 后只读查询，未修改归档原件。核对两个 shell 的空受管身份、两个创建／关闭事件和三个 agent 记录表为空。相关失败及读回保存在 `ui-db-immutable-failure.txt`、`raw-detail-check.json`。
- 截图只证明显示。进程结束来自独立 ps，隐私来自 nonce、请求 ID、事件和数据库，自动启动排除来自全部 launch／创建事件的前后 inventory。

FINDINGS:

- 没有本轮确认需修复的缺陷。operator CLI 的 cwd 范围见上面的明确边界；不宣称后台实现了未存在的项目目录限制。

## 结构完整性

按 design-integrity-review 的路由，候选触及接受面，主体采用 behavioral-acceptance-review，同时逐项检查结构风险。scanner 在干净候选返回空 findings，仅作定位结果。

新增异常处理属于 trace、关闭、退出核对和恢复诊断所在层：失败设置 failed 或留下 shell_exit_unconfirmed，历史状态保持 unknown，不自动重新启动。terminate 的 Promise.allSettled 用于等待已排队写入后继续关闭，不能替代其后的进程核对；退出轮询没有重放输入或启动动作。nullable 迁移在事务内保留旧行并恢复追加式 trigger。未引入平行门禁、第二套输入记录器、自动重试、兼容双写或掩盖失败的兜底。

窗口历史查询用于在失效凭据拒绝路径继续执行隐私裁定，角色来自已有后台事件和 launch，未增加客户端自报角色的授权捷径。requireShellPane 承担 IPC 身份核对，未确认浅包装层扩张问题。

LIMITATIONS:

- 本轮未新跑真实 Electron／daemon；当前候选的真实边界通过源码快照绑定及原件核对成立。本轮 worker 正向输入证据为真实 handler／Panes／SQLite 的隔离层，未冒称重新跑过可输入供应商 CLI；本票没有调用模型的需要或授权。
- 显式关闭证明覆盖正常 shell 及前后台 sleep。忽略信号、脱离进程树、shell 自然退出后遗留子进程、daemon 突然死亡的行为没有新运行证明；不据未运行的场景宣称任意进程均保证被清理。
- 未验证打包入口、窄屏、系统输入法或任意用户 zsh 配置，不宣称可靠性、性能或成本改善。
- `REVIEW-OUTSIDE-02.sh` 是可选的真实后台补充复验，尚未运行，不计入本次 PASS。它从冻结候选 archive 建副本，先跑好候选，再跑正文日志、元数据和重启三种错误；只修改 node-pty 测试副本执行位，原件写外置盘，不启动 Electron。若后续另做 Electron 验证，仍须使用内置盘二进制。

RULE:

本轮未确认重复的新失败类别，不新增治理规则。现有真实入口验收已加入 shell 逐次元数据检查和全量重启 inventory；继续保留这两个机械反例及 agent 正向输入检查即可。

## 地图与交付检查

开始及结束在稀疏 worktree 跑规定 status：8 个未检出文档问题、0 stale。另在当前候选的 git archive 文档／源码副本运行同一 status，以 GIT_DIR 只读引用本 worktree 元数据、GIT_WORK_TREE 指向该副本、GIT_OPTIONAL_LOCKS=0，结果退出 0：Problems (0)、Stale living docs (0)。没有注册新 worktree，也没有修改地图或 Git 元数据；`map-archive.json` 保存准确命令和环境。直接对无 Git 的 archive 首次检查报四项 Verified 需要日期，属于检查方式限制，未冒充候选失败或通过。

交付只有本报告和 REVIEW-OUTSIDE-02.sh。脚本经 bash 语法和内嵌 Python AST 检查，两个文件按 UTF-8 回读；git diff --check 通过。未 commit、checkout、reset、stash、push、submit、集成、申请升级、调用模型或使用问题面板。

T-104 REVIEW PASS
