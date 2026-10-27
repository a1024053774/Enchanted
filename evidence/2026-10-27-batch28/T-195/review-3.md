# T-195 独立只读审查（第 3 轮）

## STATUS

**NO_GO**。v3 修复了单条 zsh 命令之间的迟到报告、同号恢复、终端 agy 猜目录、恢复后 Codex 第二根线程及 Claude 旧 hook 恢复旧号这些已知反例；但仍有两项 P1：**命令行边界不能证明 CLI 实例归属**，以及**菜单缓存能绕过后端已经生效的失效判断**。另确认两项 P2。不能以 `green-09` 的 15 项通过验收本候选。

冻结对象：`/private/tmp/t195-cand3`，完整 HEAD `87c30f0e9d4404c47115f350652a54c7065e0b0b`；T-195 范围相对 `c7f2a92`，重点核对相对 `b6c2600` 的修复。候选受控文件和暂存区无差异，HEAD 开始、结束一致；保留原有未跟踪的 `workbench/node_modules`。没有修改候选、原仓库、ticket、用户配置或既有证据，没有提交。新夹具、报告、截图和构建输出只写本审查目录。

验收依据：T-195 ticket、T-189 第 4 条和本轮 brief。复制文本必须含 CLI 名、当前原生会话 ID、对应记录路径；身份不能确认时置灰并说明原因。按 **Ubiquitous language** 区分启动记录、agent 会话、原生会话、CLI 进程和 shell 命令行，后两者不能互相替代。审查只覆盖 T-195 及直接调用链，前端为复制旅程的部分审查，不是全站审查。

### R1～R5 逐条核对

| 上轮发现 | 本轮结论 | 独立证据及边界 |
| --- | --- | --- |
| R1：OSC 异步补 PID，倒序覆盖或绑给下一实例 | **具体异步路径已删除，归属根因未关闭** | `noteBoundaries()` 按字节流顺序绑定，连续 A/B 报告保留 B；不再调用异步前台观察补 PID。分开提交的 zsh 命令之间正确失效。但一行里有两个 CLI、子 shell 或换成 bash 时仍继承旧号，见 F1。 |
| R2：新进程报告同一 ID 后持续置灰 | **原反例关闭** | 真实 PTY 中，第一实例退出前报 `ses_other`；下一条命令启动后先置灰，再报相同 ID 即可用。命令号进入完整报告去重条件。此结论不替 F1 的“尚未报告就可用”背书。 |
| R3：终端 agy 按启动目录取旧库 | **原反例关闭** | `terminalLink()` 对终端 agy 直接禁用；真实 `cd B; agy` 返回原因，不再扫描 A 的库。受管 agy 仍按独占工作区扫描，未重新实测真实 agy 或内部 protobuf。 |
| R4：恢复后的 Codex 收集器看不到新根线程 | **原漏检反例关闭，读取故障处理未完整关闭** | 保留恢复态 `nativeFile` 和 offset，再造第二根 rollout；实际 `Panes.scan()` 未产出第二线程事件，`nativeLink()` 仍正确禁用，说明不再依赖那个缺失事件。新查询自带第二套扫描，存在 F4 和 M1；不能称为身份收集层已统一。 |
| R5：未经归属核对的 hook 日志决定 Claude 当前 ID | **旧号误用反例关闭** | 先确认启动号可用，再经实际 `signal()` 送新会话 hook，虽被状态路径拒绝，查询会禁用；随后送被拒绝的旧子会话 hook，仍禁用。查询不再用最后一条原始 hook 的 ID 作可用身份。真正 `/clear` 的边界证据来自既有 `green-09`，本轮不启动真实模型。 |

R3～R5 的后端禁用不能关闭 F2：用户已经打开的菜单仍可持有旧的可用结果。

## FINDINGS

### F1 · P1 · OSC 133 的“一条命令行”被当成“一次 CLI 运行”，新实例未报 ID 就继承旧链接

位置：[panes.ts:369](/private/tmp/t195-cand3/workbench/src/panes.ts:369)、[panes.ts:372](/private/tmp/t195-cand3/workbench/src/panes.ts:372)、[panes.ts:398](/private/tmp/t195-cand3/workbench/src/panes.ts:398)；边界来源：[.zshrc:10](/private/tmp/t195-cand3/workbench/terminal/zdotdir/.zshrc:10)。

`preexec` 在整条命令行开始前输出一次 C，`precmd` 在回到提示符时输出 D。保存的 OSC 报告只有 CLI 名、命令号和会话号。查询仅比较当前前台的 CLI 名和命令号，**没有证据证明是当前实例写出的报告**。

[pty-01.json](pty-01.json) 通过真实 node-pty、zsh、现有 opencode shim、macOS 进程观察和实际 `onData → shellNative → nativeLink` 复现四种输入。CLI 是遵循既有协议的最小替身：开局无 ID，输入会话号才报告它；记录库是合成 SQLite。

| 输入 | 观察 | 实际错误 |
| --- | --- | --- |
| `opencode; opencode` | 第一 PID 52932 报 `ses_resume` 后退出；第二 PID 52958 尚未报 ID；两者命令号均为 3 | 第二实例返回 `available:true, session:ses_resume`。 |
| `opencode \| /bin/cat; opencode \| /bin/cat` | 两组管道的 CLI PID 分别 52980、53004，命令号均为 4 | 第二组仍复制第一组的 ID。 |
| `(opencode; opencode)` | 第一阶段组 leader 是 zsh，链接正确禁用；结束时子 shell 优化为 `exec` 第二个 CLI，leader PID 53026 变成 opencode | 首个 CLI 的报告此前已按命令号保存；第二个 CLI 尚无 ID，却得到可用旧号。 |
| `exec /bin/bash --noprofile --norc` 后分别两次启动 `opencode` | 外层 zsh 消失，此后没有新的 C/D；PID 53102、53129 共用遗留命令号 7 | 第二次 bash 命令启动的 CLI 继承第一次 ID。 |

同一探针中的对照通过：独立提交两次 zsh 命令时，第二次先禁用，自己再次报告相同 ID 后恢复可用；普通用户 `preexec`、`precmd` 均确实执行。因此失败来自命令边界粒度，不是钩子完全没装上或夹具没有写库。四个反例均为预先规定的“新实例无 ID 必须禁用”，没有根据实现输出编造期望。

影响：返回的记录确实存在，但属于上一实例。README 的“前台换了进程就不再用”“退出或重启后等新的一次自己报”对这些常规 shell 输入不成立。本轮没有启动真实 opencode，也不声称测出了真实 CLI 触发该窗口的频率。

修复方向：在现有终端身份拥有层区分 CLI 实例及其可验证报告；OSC 133 只能提供外层命令行边界。无法证明实例归属的复合命令、子 shell 或 shell 替换场景应禁用，不能凭命令号继续沿用。不要恢复 v2 的“异步观察当前 PID 再给旧报告补 PID”。复验必须加入上述四个输入及新实例自己报告后的正例。

### F2 · P1 · 复制按钮使用打开菜单时的缓存，失效后的旧号仍会被复制

位置：[renderer.tsx:705](/private/tmp/t195-cand3/workbench/app/renderer.tsx:705)、[renderer.tsx:708](/private/tmp/t195-cand3/workbench/app/renderer.tsx:708)；实际写入入口：[main.ts:403](/private/tmp/t195-cand3/workbench/app/main.ts:403)。

菜单只在 `openAgentMenu()` 查询一次。`copyLink()` 直接把 `agentMenu.link.text` 交给 `copyText()`；侧栏轮询不更新该缓存，复制时也不复核。CLI 可以在菜单打开期间自行退出或换会话，无须用户点击终端。

本轮标准构建的原样 renderer JS/CSS 在浏览器中实际运行，注入合成 `window.a2a` bridge，后端会话状态和复制接收器由夹具控制；**没有使用系统剪贴板**。复现步骤：

1. 后端给出 `ses_original`，右键打开真实会话行菜单。对照点击成功，接收器收到该文本，见 [ui-web-click-01.json](ui-web-click-01.json)。
2. 重新加载完整夹具，点击测试控件，安排 5 秒后后端变为 `available:false`；立即右键打开菜单，取得仍有效的旧值。
3. 后端已失效后，菜单仍可点击。点击后界面显示“已复制”；接收器收到旧 `ses_original`，而同一份证据的 `current.available` 为 false，且只有打开菜单时的一次查询，见 [ui-web-click-02.json](ui-web-click-02.json)。
4. Escape 关闭后重新右键，立即正确置灰并显示原因。这是同一失效状态的恢复对照，见 [重新打开截图](ui-reopened-menu.jpg)。

![已失效的后端与仍显示“已复制”的菜单；右下是测试控件](ui-stale-menu.jpg)

影响：即使 R1～R5 的后端检查全部正确，当前用户入口仍能复制过期身份。这个问题同时影响受管 Claude `/clear`、Codex 新根线程及终端 CLI 退出，不限于 opencode。

修复方向：复制动作重新取得当前原生链接，返回不可用时更新菜单并停止复制；不要把先前菜单快照当成当前身份。需要在现有 main/daemon 调用链保持查询与复制的关联，不能另造一套前端身份推断。复验包含“菜单保持打开 → 后端确定失效 → 点击复制”，同时保留稳定会话的复制正例。浏览器证据证明 renderer 的缓存行为，不证明 Electron IPC 或真实剪贴板集成已通过。

### F3 · P2 · 新增 OSC 解析器在 ST 的 ESC 与反斜杠分到两个块时丢失完整报告

位置：[panes.ts:376](/private/tmp/t195-cand3/workbench/src/panes.ts:376)。

`noteBoundaries()` 用最后一个 ESC 作为残片起点。如果当前块正好结束在 ST 终止符（ESC 加反斜杠） 的 ESC，保存的只有这个终止 ESC，整个 OSC 开头和字段被丢弃。下一块只有反斜杠，无法恢复报告。

`native-01.json` 的 `osc_ST_all_byte_splits` 在实际 `startShell()` 注册的 `onData` 回调中，把有效报告 `ESC ] 7501;state=idle:app=opencode:id=ses_A ESC 加反斜杠` 遍历全部 40 个单切点；只有第 40 个切点失败。完整报告已到达、对应 SQLite 行也存在，但返回“opencode 还没报来这次会话的会话号”。PTY 数据块边界没有协议语义。

修复方向：保留从尚未闭合的 OSC 起点开始的残片，包括不完整的 ST；尽量复用现有 `readOsc7501()` 的流式分帧能力，避免回合状态和原生 ID 两套解析器理解同一字节流却不同步。回归包含 BEL、ST、开头与终止符的切分。本轮未确认真实 opencode 当前版本使用 ST；候选解析器明确接受该终止形式，且既有公共解析器也支持它。

### F4 · P2 · Codex 的文件读取故障未转成不可用结果，直接逃逸为查询错误

位置：[nativeLink.ts:141](/private/tmp/t195-cand3/workbench/src/nativeLink.ts:141)、[nativeLink.ts:152](/private/tmp/t195-cand3/workbench/src/nativeLink.ts:152)、[nativeLink.ts:160](/private/tmp/t195-cand3/workbench/src/nativeLink.ts:160)。

新增 `firstRecord()` 只把 `SyntaxError` 转为 undefined；`openSync()` 位于 try 外，EACCES、ENOENT 等打开失败直接抛出，读取时的其他 I/O 错误也重抛。上层只处理 `undefined`，因此无法兑现它的“读不了 Codex 的记录，分不出线程”分支。agy/opencode 的真实数据库错误则会在此模块归一化为 `available:false` 和原因，两条路径不一致。

[io-01.json](io-01.json) 用两份格式正确的合成 rollout，其中一份真实 `chmod 000`，返回 `EACCES` 异常而不是 `NativeLink`；结束时恢复权限。`native-01.json` 还保留了 `.jsonl` 目录造成 EISDIR 的故障输入。半写入 JSON 的对照能正常返回不可用，证明这里漏的是 I/O 边界。

这不是又一次“读不了却选旧号”：本例没有返回可用链接。经源码调用链，后台查询失败会被 main 抛到 renderer，菜单下方显示原始错误，而按钮 title 仍是“正在查找…”。本轮没有在 Electron 中复现该错误的最终文案，所以只把直接函数异常视为运行证据，UI 后果标为静态推理。

修复方向：由拥有原生记录读取职责的现有模块把无法检查的文件转换成明确的不可用结果，携带路径和读取原因；不要重试、跳过该文件或转去选择另一条记录。应覆盖真实文件 EACCES、遍历后文件消失，以及半写入记录。

## EVIDENCE

### 本轮独立运行

Node `v26.5.0`。SQLite、rollout、transcript、CLI 程序及 UI 数据均为本轮合成数据，没有读取或复制用户真实会话内容。

| 检查 | 实际结果 | 产物 |
| --- | --- | --- |
| 真实 PTY、zsh、shim、前台进程观察、实际链接函数 | 7 项：3 PASS、4 FAIL；无运行异常；退出 1 | [脚本](probe-pty.mjs)、[结果](pty-01.json)、[stderr](pty-01.stderr)、`pty-01/traces/` |
| 实际 `nativeLink`、`signal`、恢复态 `scan`、实际 onData、真实 SQLite | 14 项：11 PASS、3 FAIL；退出 1 | [脚本](probe-native.mjs)、[结果](native-01.json)、[stderr](native-01.stderr) |
| 实际文件权限故障 | 1 项 FAIL；退出 1；权限已恢复 | [脚本](probe-io.mjs)、[结果](io-01.json)、[stderr](io-01.stderr) |
| 本次构建 renderer 的实际右键/复制旅程，合成 bridge | 稳定复制 PASS；会话失效后旧值复制 FAIL；重新开菜单正确禁用 | [正常复制](ui-web-click-01.json)、[错误复制](ui-web-click-02.json)、[截图](ui-stale-menu.jpg)、[复现说明](UI-REPLAY.md) |
| 标准 renderer/main/preload 构建 | PASS，退出 0；超过 500 kB chunk 提示 | [stdout](build-01.stdout)、[stderr](build-01.stderr)、[运行记录](review-runs.json) |
| 候选冻结核对 | HEAD 不变；受控工作区和暂存区差异均为 0 | [检查](candidate-check.json)、[结束复核](candidate-check-final.json) |
| 原仓库 project-map 只读状态检查 | 开始、结束均退出 0：Problems 0，Stale living docs 0 | [开始](map-status-start.txt)、[结束](map-status-end.txt) |

**M1：另一个保留的 FAIL，不上调为安全阻断。** `native-01` 的 3 个 FAIL 分别是 F3、F4 的 EISDIR 输入，以及 `codex_root_before_launch_is_history`。最后一项创建了同工作区、同日但 timestamp 和 mtime 都早于 launch 一小时的另一根线程；新扫描仍称其为这个工作区“开了新线程”并禁用。`codexRootThreads()` 仅选日期目录，未过滤启动时间；原 `Panes.scan()` 发现新文件时会检查 mtime。这个差异确定存在，但本轮未通过产品入口证明“独占工作区中已有早于 launch 的根线程”的常规生命周期，所以不把它列为额外 P1，也不把原始 FAIL 改成 PASS。若要求“只考察自启动以来的新线程”，需补真实生命周期证据再修；README/注释不能把整日扫描说成精确的启动后扫描。

复现命令（均需换用未使用的夹具目录和输出名，保留本轮失败证据）：

```sh
node /private/tmp/t195-review3/probe-pty.mjs /private/tmp/t195-review3/pty-replay > /private/tmp/t195-review3/pty-replay.json 2> /private/tmp/t195-review3/pty-replay.stderr
node /private/tmp/t195-review3/probe-native.mjs /private/tmp/t195-review3/native-replay > /private/tmp/t195-review3/native-replay.json 2> /private/tmp/t195-review3/native-replay.stderr
node /private/tmp/t195-review3/probe-io.mjs /private/tmp/t195-review3/io-replay > /private/tmp/t195-review3/io-replay.json 2> /private/tmp/t195-review3/io-replay.stderr
```

构建实际命令：在候选 `workbench` 中，`TMPDIR/TMP/TEMP` 均设为 `/private/tmp/t195-review3/build-root`，运行 `node app/build.mjs --slot review3`。输出保存在 `build-root/a2a-build-review3/dist`。再次构建必须使用新 slot。

### 既有红、绿、mutant 与回归证据

只读核对指定摘要及测试源码；摘录见 [existing-evidence-audit.json](existing-evidence-audit.json)。没有重跑真实模型，也未读取它们留存的用户会话或认证副本。

- `green-09.json` 确实记录 15 项 PASS，包括真实 Claude worker `/clear` 和终端 `/clear`；Codex 首次记录由真实 CLI 写出，第二根线程是测试注入的 rollout 首行。opencode/agy 使用替身。它们支持 R2～R5 的指定场景，不覆盖 F1 的复合命令、shell 替换、ST 分块或 F2 的菜单缓存。
- `red-b6c2600.json` 和 `mutant-claude-ignores-other-session.json` 都在“/clear 后受管 Claude 的链接置灰”处超时；记录证明这条必需状态没有出现。它们的 `INCOMPLETE` 不是通过，也不能把超时扩大为已拿到每个时点旧 ID 的快照。
- `mutant-codex-ignores-second-thread`、`mutant-terminal-agy-by-directory`、`mutant-report-outlives-command-02` 均在业务断言上失败，分别明确保存旧线程可用、终端 agy 取旧库、重启继承旧号的结果。最后一份先失败于 `opencode_restart_does_not_inherit`，不是随后那条“退出前迟到报告”检查；不把尚未执行的断言算成已杀死该场景。
- 第一份 `mutant-report-outlives-command.json` 为 PASS，确实是存活反例；保留它是正确的。brief 说明后来删除重复清空逻辑，当前代码也未见那条额外清空路径；第二次变异能检出坏行为。但现有判据仍允许“一个命令号当一个实例”的坏实现通过，本轮 F1 是新的反事实。
- 常规 green/mutant 摘要的 `revision` 为 null，运行源是开发目录，不绑定本次完整冻结提交。作为外部留存证据使用，不宣称已逐字运行在 `87c30f0`。本轮独立脚本则直接导入冻结候选，开始与结束复核 HEAD。
- T-118 摘要两项 PASS；T-121 第 6 次摘要确为 49 项 PASS。顺带静态核对 `78d83d2`：把“限定终端原项目”调整为“可达任一已打开项目”，仍保留单任务单 repo、完整项目 ID 与矛盾项目拒绝，语义与 T-193/T-189 第 1 条一致。没有重跑这一回归，不能据此独立验收 T-193。
- **T-104 与 brief 描述不一致。** `regression-t104_shell-2.json` 的 traceback 失败于第 213 行 `A2A_` 环境变量清单；`-base.json` 失败于第 211 行 `LOGIN=on,INTERACTIVE=on,RC=loaded`。不是“同一 LOGIN 断言都失败”。基线较早失败，不能证明候选后面的环境变量断言是既有缺陷，也不能证明由 T-195 引入；该回归仍未完成归因，不能写成 PASS。

### 结构、说明及检查边界

按 **Deep modules** 检查：没有为这次复制新增另一套门禁，也未发现重试或用备用库掩盖读取失败。agy/opencode 的数据库 catch 明确返回读取失败；Claude 的 JSON catch 忽略不含可解析 ID 的入口，异号仅使绑定失效，不再把未验证 ID 升级为可用身份。但仍存在两组平行解释路径：

1. `readOsc7501()` 与新增 `noteBoundaries()` 都解释同一 OSC 流，后一条引入 F3。
2. Codex 身份收集器与 `nativeLink.codexRootThreads()` 各自发现根线程，过滤时间与异常处理不一致，见 F4、M1。R4 的特定查询结果变安全，不等于收集器的身份事实源已经统一。

受管 Claude 仍读原始 `hook_received`，但用途变为保守失效；daemon 在进入 `signal` 前核对 launch 身份，故不能将该日志再次用于选定另一个可用 ID。异号也可能来自子会话，当前“已不在启动时会话”的文字比“无法确认仍在启动会话”更肯定；本轮没有把这个保守禁用当成错误可用链接。

shell 启动仍硬编码 `/bin/zsh -l -i`，没有新增原生 bash 集成；用户 `exec bash` 是可达路径而非受支持集成的证明。用户自己的同名 `preexec/precmd` 在本轮保留并运行；未穷举插件重设 hook 数组、非零 hook 返回、`.zlogin` 改写和第三方 shell integration。自己的 C/D 使用 BEL，终端 UI 不显示这些标记。普通管道和子 shell 的实际安全影响已列入 F1，不能笼统写成“支持 shell”。

README 对受管 Claude“异号即置灰”、终端 agy“一律置灰”的描述与后端一致；“CLI 实例变了旧号不再用”受 F1 限制，“只给现在这个会话”还受 F2 限制。facts 的“现状”及“对 T-195 的影响”仍把受管 Codex 说成 hook 报号，后文已改为 rollout 绑定，文字内部不一致。只审未修改。

按 **Tracer bullet** 的标准，现有 socket 测试没有覆盖用户真正的“打开菜单 → 等状态变化 → 复制”旅程；本轮 renderer 探针补出了 F2，但没有替 Electron IPC、剪贴板、真实 CLI 和模型组成完整端到端验收。

### COUNTEREXAMPLE 与 RULE

已知坏行为不能被绿色首次启动样例替代：新实例未报告 ID 却复制旧号、后端已禁用却由菜单缓存复制、合法 OSC 按数据块切开后丢 ID，均被本轮独立输入检出。现有 mutant 对各自指定的坏实现有价值，不能外推为实例归属或 UI 时效性完整成立。

身份绑定失效已连续三轮出现。建议通过项目现有 task 流程把 F1 的四类真实 PTY 输入、F2 的菜单保持打开场景、F3 的分块矩阵、F4 的真实文件权限故障接到 T-195 现有验收入口；预期从 CLI 实例和夹具输入预先确定，并用相应坏实现确认断言确实失败。不要继续增加只覆盖一个当前补丁的条件开关。本审查没有建票、改测试或修复候选。

## LIMITATIONS

- 未重跑依赖真实模型和登录的完整 e2e，符合 brief。真实 Claude `/clear` 的证据来自既有摘要；Codex 第二根线程为文件夹具；未实际恢复真实 Codex 后开新线程。
- PTY 真实，CLI 替身和记录数据合成。它证明 shell 生命周期及协议处理，不证明真实 opencode 的 ST 使用、真实 agy 写库时序、内部 protobuf 格式或续会话功能。
- renderer 浏览器探针使用本次冻结构建 JS/CSS 和实际 React 菜单，但 backend/preload/复制器是合成 bridge；测试包装另加控制按钮并放宽其本地 `connect-src` 以保存结果。没有改变候选或生成的产品 JS/CSS，没有读写系统剪贴板。实际 Electron IPC 和剪贴板读回仍未验证。
- 首次独立 Electron 启动退出 134，stderr/stdout 均为空，脚本内结果目录没有建立；无法确定根因，不归咎于产品或断言为权限阻断。保留 [脚本](probe-ui.cjs)、[preload](ui-preload.cjs)、[stdout](ui-01.stdout)、[stderr](ui-01.stderr)。
- 浏览器夹具初版漏 `executionSettings`，出现空白；第二版测试控制脚本被 CSP 拒绝，未产生预期失效。这两次均为夹具问题，保留 `ui-web-index-01.html`、`ui-web-index-02.html`，没有算作产品失败或通过。补全测试 bridge、外置控制脚本后，才得到 F2 的有效输入/输出。
- M1 是已观察到的日期过滤差异，产品正常生命周期的可达性未补齐；T-104 两份回归也未完成同一失败点归因。均没有上调为已验收或全部回归通过。
- 没有读取或复制用户真实 `~/.claude`、`~/.codex`、opencode、agy 会话内容，没有更改全局配置、提交、部署或向他人发送消息。自建 PTY 已按探针退出流程关闭，自建浏览器页已关闭，本地 HTTP 服务器已停止。
- 本结论拒绝本次冻结候选；没有实施修复，不替下一轮候选预先作通过结论。
