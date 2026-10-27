# T-195 独立只读审查（第 4 轮）

## STATUS

**NO_GO**。F1、F2、F3 的指定反例已关闭，M1 的启动时间过滤也通过复验；**F4 的错误边界仍有缺口：日期目录的父目录不可访问时，查询会把读取失败当成目录不存在，重新给出旧线程链接。** 另有一处 P3 文档事件名错误。本轮真实 CLI e2e 在完成 8 项检查后超时，整体为 **INCOMPLETE**，不能用既有 `green-10` 替它改记为通过。

TARGET：`/private/tmp/t195-cand4`，HEAD `ed5a63bd5c00363fa7f3f9053c5a5dd84e3d7309`；审查范围为 `87c30f0 → ed5a63b` 及第 3 轮发现的关闭情况。T-193 的 `78d83d2` 不在本次验收范围。

验收依据为 T-195 ticket、brief 和第 3 轮报告：复制文本包含 CLI 名、当前原生会话 ID、对应记录路径；无法确认身份时置灰并说明原因。按 **Ubiquitous language** 区分 CLI 实例、shell 命令、原生会话及线程；按 **Deep modules** 检查读取职责和错误边界；沿现有复制入口检查这条 **Tracer bullet**，不扩展成全站审查。

| 第 3 轮事项 | 本轮结论 | 依据与边界 |
|---|---|---|
| F1：OSC 133 命令边界被当作 CLI 实例 | **关闭** | 删除 `noteBoundaries`、命令计数及 zsh OSC 133 钩子；终端 opencode 无条件置灰并说明报告不带进程号。真实 PTY 中独立命令、分号、管道、子 shell、替换为 bash 后重启均未给出旧号；用户原有 preexec/precmd 仍执行。 |
| F2：复制使用菜单打开时的缓存 | **关闭指定反例** | 本次标准构建的真实 renderer 右键旅程中，后台失效后点击会重新查询并阻止复制；后台换号后首次点击只更新菜单，第二次点击才复制新号。bridge 和复制接收器为合成数据，未测系统剪贴板。 |
| F3：新增 OSC 解析器在 ST 跨块时丢报告 | **关闭** | 有问题的第二套解析器已删除。剩余 `readOsc7501` 在实际 `startShell` 的 onData 回调中遍历全部 40 个单切点，均保留回合 ID；所有切点的终端 opencode 链接均不可用。 |
| F4：Codex 文件读取错误逃逸 | **部分关闭，未在根因层关完** | readdir EACCES、stat ENOENT、open EACCES、read EISDIR 和半写入 JSON 均返回明确不可用；但日期目录预检仍吞掉父目录 EACCES，见下面 R4-F1。 |
| M1：扫描把启动前的 rollout 算作本次线程 | **关闭指定反例** | mtime 早于 `created_at` 的记录被跳过；同工作区的旧根线程、旧的不可读文件均不使已确认绑定置灰。不是按首行 timestamp 过滤。 |
| T-104 归因不完整 | **同一断言的归因缺口已补证；回归未通过** | 新的 v4 与 base-inplace 两份摘要都停在第 213 行，归档原始 PTY 均有 `LOGIN=on,INTERACTIVE=on,RC=loaded`，且都含相同的额外 A2A 环境变量键，详见 EVIDENCE。 |
| README 与事实文档不一致 | **主要语义已同步，仍有 P3 事实错误** | 两份文档均已写明终端 agy/opencode 禁用、受管与终端 Codex 的来源区别；事实文档对终端 Codex 的事件名仍写错，见 R4-F2。 |

## FINDINGS

### R4-F1 · P2 · 日期目录预检把 EACCES 当成“不存在”，读取失败反而恢复旧线程链接

位置：[nativeLink.ts:141](/private/tmp/t195-cand4/workbench/src/nativeLink.ts:141)，相关返回路径为 [nativeLink.ts:48](/private/tmp/t195-cand4/workbench/src/nativeLink.ts:48) 和 [nativeLink.ts:53](/private/tmp/t195-cand4/workbench/src/nativeLink.ts:53)。这行预检不是 v4 新增，但位于本轮 F4 所要覆盖的 Codex 目录读取边界内。

`if (!existsSync(directory)) continue` 位于新增 try/catch 之前。`existsSync()` 在日期目录的祖先目录没有搜索权限时也返回 false；因此后面的 readdir catch 根本不会执行。只要较早日期的绑定文件仍可访问，扫描就可能漏掉后续线程，然后把旧号作为可用结果返回。

本轮先在直接模块探针复现，再通过**真实 daemon、真实 SQLite 和 `native_link` socket 请求**确认。输入是合成的跨月 monitor 启动记录及两份 rollout 首行，没有真实模型或长期存活的 CLI 进程。具体过程：

1. 启动时间设为 2026-09-30；绑定线程 A 的记录在 `sessions/2026/09/30/`，线程 B 的记录在 `sessions/2026/10/27/`；两份记录的 cwd 相同，mtime 均晚于启动时间。
2. 权限正常时，真实 socket 返回 `available:false`，明确指出 B 不是绑定的 A。
3. 将本探针自己的 `sessions/2026/10` 目录设为 000。直接枚举 10 月 27 日目录得到 EACCES，`existsSync()` 却为 false；同一 socket 随后返回 **`available:true`、线程 A 及 9 月的旧记录路径**。
4. 恢复权限后，同一查询再次因 B 而置灰。所有夹具权限均已恢复。

证据：[socket-02.json](socket-02.json)、[socket 探针](probe-socket.mjs)、[io.json](io.json)。这是“减少可读信息使身份从不确定变成可用”的反例，不依赖根据实现输出猜当前会话。它不证明真实用户遇到这种目录权限变化的频率；故定为 P2，不把合成日期说成真实跨月运行记录。

修复方向：在现有 `codexRootThreads` 的目录读取职责内区分“目录确实不存在”和“目录无法检查”。直接读取并分类错误，仅跳过预期的缺失目录；EACCES 等错误返回带路径和原因的不可用结果。不要重试、跳过读不了的目录后选择旧号，或增加另一套身份判断。

COUNTEREXAMPLE：当前 v4 本身在这条不可读目录反例上失败；其余 9 条 I/O/过滤检查通过。现有 `codex-read-error-escapes` 变异只覆盖文件 catch，无法覆盖这个在 catch 之前被 `existsSync()` 消解的错误。

RULE：这是重复出现的“无法读取被当成没有匹配”的失败类。应在 T-195 现有 e2e 的 `native_link` 入口增加跨日期子树的权限扰动检查：正常可读时第二根线程置灰 → 后续子树不可读时仍置灰且说明读不了 → 恢复权限后仍因第二根线程置灰；并保留真正不存在日期目录的正常对照。审查只提出检查，不修改测试或 ticket。

### R4-F2 · P3 · 事实文档仍把终端 Codex 报告写成 pane_native_session 事件

位置：[2026-10-27-native-session-ids.zh-CN.md:8](/private/tmp/t195-cand4/findings/2026-10-27-native-session-ids.zh-CN.md:8)。

本轮改写的 Codex 条目同时介绍受管 worker 和项目终端，结尾称“记在 `pane_native_session` 事件”。实际终端路径为 `daemon.ts` 的 `terminal_hook` → `Panes.noteShellHook()` → `noteNativeReport()`，后者在 [panes.ts:360](/private/tmp/t195-cand4/workbench/src/panes.ts:360) 写的是 **`shell_native_session`**；受管 Codex 才使用 `pane_native_session`。

这是静态调用链证据，影响排障时应查询哪类事件，不影响复制按钮本身。把该句明确分成两种事件即可；无需改实现。README 对受管/终端来源及禁用条件的主要描述已与代码一致。

## EVIDENCE

### 本轮独立运行

环境：Node `v26.5.0`。脚本、夹具、构建输出和报告均写在本审查目录；候选源码只读。

| 检查 | 实际结果 | 产物 |
|---|---|---|
| 标准 renderer/main/preload 构建 | **PASS**，退出 0；有大于 500 kB chunk 的提示 | [stdout](build.stdout)、[stderr](build.stderr) |
| 真实 PTY、zsh、前台进程观察及实际链接函数 | **7 PASS / 0 FAIL**，退出 0 | [脚本](probe-pty.mjs)、[结果](pty.json)、[stderr](pty.stderr) |
| 实际 nativeLink、signal、恢复态 scan 和 onData | **12 PASS / 0 FAIL**，退出 0 | [脚本](probe-native.mjs)、[结果](native.json)、[stderr](native.stderr) |
| 实际文件权限与格式边界 | **9 PASS / 1 FAIL**，退出 1；失败为 R4-F1 | [脚本](probe-io.mjs)、[结果](io.json) |
| 真实 daemon 的 socket 反例及前后对照 | **FAIL**，退出 1；权限故障时旧号变可用 | [脚本](probe-socket.mjs)、[结果](socket-02.json)、[stderr](socket-02.stderr) |
| 标准构建 renderer 的右键/复制旅程 | 稳定复制、失效拒绝、换号首次不复制、第二次复制新号，**4 个场景通过** | [稳定](ui-observations/click-05.json)、[失效](ui-observations/click-06.json)、[换号首次](ui-observations/click-07.json)、[换号再次](ui-observations/click-08.json) |
| 冻结候选的真实 CLI e2e | **INCOMPLETE**，退出 1；前 8 项通过，终端 Claude 首次报告等待超时 | [运行脚本](run-frozen-e2e.py)、[摘要](frozen-e2e.json)、[stderr](frozen-e2e.stderr)、[诊断边界](e2e-diagnostic.json) |
| 冻结核对 | 开始、结束 HEAD 一致；受控文件无差异，原有未跟踪 `workbench/node_modules` 保留 | [开始](candidate-start.json)、[结束](candidate-final.json) |
| project-map 只读检查 | 开始及结束均 Problems 0、Stale living docs 0 | [结束输出](map-status-final.txt) |

![后台失效后，真实 renderer 的菜单说明原因并阻止复制](ui-codex-disabled.jpg)

UI 通过本次构建的原样 JS/CSS 运行，合成 bridge 提供 Codex 链接，复制接收器仅记录文本，不访问系统剪贴板。`click-05` 有一次稳定复制；`click-06` 查询已返回不可用而 copies 数量仍为 1，`aria-disabled=true`。重新加载夹具后，`click-07` 显示新线程但 copies 为空；`click-08` 只含新线程文本。按钮使用 aria-disabled 而非 HTML disabled，最终阻止副作用的是 `copyLink` 的检查；没有把 `buttonDisabled:false` 当成失败或成功判据。

完整 e2e 是候选自带脚本的副本，**只调整 ROOT 和临时目录位置**，未改业务输入、断言或等待时间。已独立通过真实 Claude、真实 Codex 的原生 ID/记录内容核对、受管 Claude `/clear` 置灰及 Codex 注入第二根线程置灰。Claude 的模型接口为本地脚本服务；Codex 使用真实模型。终端阶段的原始 PTY 显示已提交提示、收到本地模型回复及运行 hook 的界面，但该终端未留下 `shell_native_session` 事件。原因未查明，不将它断言为 v4 引入的产品缺陷，也不把后续未执行检查算作通过。隔离 CODEX_HOME 只复制 auth.json，结束已整体删除；未读取认证内容到输出。

复现命令见 [review-runs.json](review-runs.json)。直接探针重跑需使用未存在的目录和新的输出文件，例如：

```sh
node /private/tmp/t195-review4/probe-io.mjs /private/tmp/t195-review4/io-replay-01 > /private/tmp/t195-review4/io-replay-01.json 2> /private/tmp/t195-review4/io-replay-01.stderr
node /private/tmp/t195-review4/probe-socket.mjs /private/tmp/t195-review4/socket-replay-01 > /private/tmp/t195-review4/socket-replay-01.json 2> /private/tmp/t195-review4/socket-replay-01.stderr
```

UI 重放：`python3 /private/tmp/t195-review4/ui-server.py /private/tmp/t195-review4/ui-replay-01`，打开返回的本机 URL，右键 Codex 行。先复制稳定链接并保存观察；保持菜单打开，点“使后端会话失效”，再点复制并保存。重新加载后，打开菜单、点“改为新会话”，第一次复制应只更新菜单，保存后第二次复制应只记录新号。夹具控件仅改变合成后台和保存观察，不改产品菜单实现。

### 既有测试、红态与变异的独立性

只读核对摘要和候选测试源码，摘录见 [existing-evidence-audit.json](existing-evidence-audit.json)。

- `green-10.json` 确有 15 项 PASS。初始 ID/路径期望来自真实 CLI 写出的 transcript/rollout 中的 ID 与 cwd；没有导入生产身份选择函数来生成答案。新根线程和旧 rollout 是测试主动生成的独立输入；旧记录 mtime 由真实 launch 的 created_at 减去一小时设定。格式断言使用返回 ID/路径拼接约定文本，仅证明文本字段完整，身份真实性另由记录核对证明。
- opencode/agy 是协议与 SQLite 替身，不是本次真实 CLI 实测。终端 opencode 改为禁用是本轮 brief 明示的范围收缩：删除旧“同号重新可用”的断言与该契约一致，不能继续把它当作承诺提供的能力。受管 opencode 路径保持，未被这个禁用分支误伤。
- `red-v3-87c30f0.json` 在终端 opencode 的目标断言失败，并保存了 v3 返回可用 `ses_first` 的结果。摘要状态仍是 INCOMPLETE；它是有效的目标红态，不是全套运行完成。
- 五个 `mutant-v4-*` 都拒绝了目标坏行为：忽略 Claude 异号的变异在 `/clear` 置灰等待处超时；忽略 Codex 第二线程、把旧 rollout 算入、文件错误重抛、终端 agy 按目录猜号四个变异均在对应业务断言上失败，并保存错误返回值。未见语法错误或启动失败冒充杀死变异。
- Claude 变异的超时证明必需的置灰状态未出现，不等同于逐次保存了仍可用的旧 ID。五份摘要均为 INCOMPLETE，不能改称整套变异运行 PASS。
- `green-10` 和变异摘要的 revision 为 null，运行源不绑定冻结完整提交；只作为外部留存证据。本轮直接探针、标准构建及 e2e 明确使用冻结候选。F2 没有候选自带的界面自动化或变异，本轮 UI 运行补足了指定反例的行为证据。

### T-104 与结构边界

新 `regression-t104_shell-v4.json` 和 `regression-t104_shell-base-inplace.json` 均失败于第 213 行只允许 `A2A_PROJECT` 的环境变量清单断言。两份外置盘归档的原始 PTY 均成功输出登录/交互/RC 标记，且都出现 `A2A_TERMINAL_BIN`、`A2A_TERMINAL_PLUGIN`、`A2A_TERMINAL_CLI`、`A2A_NODE`、`A2A_TERMINAL_SOCKET`、`A2A_TERMINAL`、`A2A_TERMINAL_TOKEN` 等键，见 [抽取证据](t104-evidence-lines.json)（临时 token 已遮盖）。因此本轮不再沿用上一轮错误的“基线先失败于 LOGIN”比较；该条旧测试期望与两份运行环境相同地不符。摘要没有绑定基线完整 SHA，且后续断言未执行，不能据此声称 T-104 全通过或所有后续行为均已归因。

新增 catch 的职责范围基本合理：目录读取、文件 stat、首行打开/读取/关闭及解析都由 `codexRootThreads` 所在模块拥有；失败返回不确定及具体路径，没有跳过坏文件、备用库或重试。catch 没有覆盖启动记录 JSON、事件数据库查询或整个 nativeLink，从而不会把这些错误冒充 Codex 文件读不了。旧文件在 stat 后按 mtime 排除；可读的其他工作区和 subagent 记录也不会使当前绑定置灰。这些正例均已在 io 探针检查。剩余问题恰在上述边界之前的 existsSync 预检。

## LIMITATIONS

- 这是 v3→v4 修复的定向审查，不是整票之外的全站、全部 CLI 或发布验收。没有重跑 T-118、T-121，也不验收 T-193。
- socket 反例采用合成启动记录与 rollout，通过真实存储/daemon/传输执行；没有让真实 Codex 跨月运行或复现真实用户目录权限故障。发现的是可重复的错误降级路径，不是事故频率。
- UI 证据只覆盖本次实际构建 renderer 的复制旅程；未执行 Electron IPC 与操作系统剪贴板的完整集成，不声称查询与剪贴板写入在所有异步时序下原子完成。
- 本轮真实 CLI e2e 超时，终端 Claude hook 未报告的原因仍未知，后续终端场景与新增文件检查未在该次完整 e2e 中执行；它们的其他独立证据层次已分别注明。
- 新 socket 探针第一次因自身括号语法错误在执行前退出；保留 [原脚本](probe-socket-01.mjs) 与 [stderr](socket.stderr)，不计为产品红态。修正探针后才得到 socket-02 的有效反例。早期 UI 夹具用 opencode 的合成可用值检查通用 renderer，后改为 v4 支持的 Codex 输入；前者保留，正式 UI 结论引用 click-05～08。
- 没有修改候选、原仓库、ticket、用户全局配置或已有证据，没有提交。真实 CLI 使用隔离配置；Codex auth 副本已删除。自建 PTY 已退出，两次自建 daemon 均已请求停止，自建浏览器页已关闭，HTTP 服务器已通过所属执行会话中断退出。直接发送 SIGINT 的首次清理请求被沙箱拒绝，随后会话中断成功；没有借此申请额外权限。
- 未实施任何修复。本报告对该冻结候选给出 NO_GO，不替未来候选预先作通过结论。
