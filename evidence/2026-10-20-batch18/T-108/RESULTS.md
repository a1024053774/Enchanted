# T-108 / a1：第五轮早确认与写入链缺陷已修复；局部 PASS，整票 INCOMPLETE

2026-10-20，执行主控 #32。父候选 f533fd16e608cb73f666246700206fe28e21503c，仍在 exec/t108。修复未提交，待主控执行 RUN-OUTSIDE-COMMIT-07.sh；本报告不冒报 SHA。新增模型回合、模型调用和供应商调用均为 0。

F1-05 的两处根因已分别修复。同一问题的原生 PostToolUse 在逐键写入结束前到达时，answerQuestion 会核对 answer_intent 之后的原生确认，要求 session、submission、turn、question 及答案内容均匹配；身份、当前回合可信度、输入代数和窗格生命周期仍逐次核对。正向确认成立才停止余键、成功返回，并记录 confirmed 和实际键数。合法的匹配 Stop 若已使同一回合 idle，也可成功收尾；未知、撤权、内容变化、不同答案或新输入不走成功分支。没有把 question_input_changed 一律兜底为成功。

后台 serializeWrite 与 Electron 主进程 sendWindowCommand 分别保留原调用者的错误回执，只让用于排队的 Promise 恢复可执行状态。下一次操作重新核对身份与运行状态。主进程有同类堵流缺陷，本次先用其实际函数取得业务红态，再做最小修正。实际 PTY 写入结果未知仍保存 pane.failed；队列入口拒绝后续操作，连已在队列中等待的输入也不能写出。shellInput 作为共享队列的另一写入口，补齐物理写异常的失败事实并重抛，避免解除 Promise 堵塞后漏过真正未知。无重发、重试、新 PTY 或平行 API。

**先红后绿：** 修产品前运行独立审查的原复现，rc=1，原生已 answered，首答与下一条 userInput 都因 question_input_changed 拒绝，PTY 只有两键；摘要 /private/tmp/t108-review05-early-original-red.json。新默认测试在修前也取得业务红态。最终 replay_review05_red.py 用 git archive 冻结 f533fd16e 的产品、普通复制依赖，只叠加本次测试：429 项旧 hook 合同通过，早确认、早确认后 Stop 及普通记录拒绝后三项重点断言失败，后续输入均未写出；旧 main.ts 也被“被拒请求不得污染下一条请求”的断言拒绝。最终红态证明 /private/tmp/t108-review05-red-final-proof.json，测试原始退出码均为 1。导入、初始化或依赖错误不计红态。

**局部 PASS：** 默认 test_t108_questions.mjs 的 429 项 hook 合同与 14 项作答生命周期合同全部通过。生命周期包括确认早到、晚到、最后一键期间到达、确认后匹配 Stop、不同答案、确认后撤权／改输入／未知、发送期间失效、记录拒绝、实际 PTY 未知、排队中的未知写入，以及 shell 的拒绝与未知对照。正常路径只记一条 answer，早确认仅写两键，剩余 Enter 不再写入，下一条输入可用，重复作答仍拒绝；物理结果未知不写后续字节。

无模型入口的漏检也已修复。驱动仍通过真实 DOM 提交，随后只读 SQLite，将第一个 window_answer 的传输 ID 与窗口 request_id／sequence、当前 launch 准入及最终 request_result 关联；只看到 clicked、题目消失或 answered 不再算通过。该检查实际回查主控提供的 /private/tmp/t078-2-t108-350ywzx4，拒绝了原六项 PASS 中首答失败的记录，摘要 /private/tmp/t108-review05-original-receipt-red.json。run_t108_native_e2e.py 再独立核对首答回执，并在匹配 Stop 后向同一窗格粘贴随机标记、不按 Enter，要求准确的写入意图、写入完成事件及原 PTY trace 的新回显，同时保持假 API 两个根请求（一次输入与一次工具续接）。这是精确字节传输检查，不从屏幕文字推断问题语义。

RUN-OUTSIDE-RECHECK-05.sh 已运行，rc=0，完整局部产物在 /private/tmp/t108-review05-recheck-BPz1VG：组合 IPC、原拒绝检查、侧栏、T-109 层级、T-111 流程、Claude Stop、输入顺序／中断、Codex 原件回放、正常 AskUserQuestion 自身 PermissionRequest 原件回放及实际 daemon/socket 的只读零写入和身份冲突均 PASS。随后新增主进程同类修复，又单独运行最终 driver（9 项）和组合 IPC，均 PASS；构建 PASS，成功临时构建目录已清理，日志保留。Python 3.9 语法检查通过。设计扫描器只定位物理写失败后记录并重抛及证据报告边界；这不构成独立审查 PASS。

本轮 sidebar.ts、renderer.tsx 均无修改。main.ts 仅第 131–133 行调整输入链错误传播；panes.ts、questions.ts 与 daemon.ts 承担原作答生命周期和回执接线。T-109 树与 T-111 流程未改。旧红态重放脚本仅补复制新导入的生命周期测试文件，防止旧证明因缺测试模块而中断。README 已同步语义与本轮完整入口待跑状态。

**INCOMPLETE：** 新候选的已安装 CLI／Electron 无模型完整入口尚待主控运行，独立审查也未开始；本次局部 PASS 不替代这两项。project_map status 仍 rc=1，8 个既有稀疏检出缺失链接、0 stale，原文在 project-map-review05-final.txt。未新增真实模型回合、凭据读取、全局配置写入、截图、submit 或 push。原失败现场及审查材料保留。

主控执行命令（摘要路径必须新建）：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-07.sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-review05-01.json
# 如需重跑局部合同与冻结父候选红态：
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-05.sh
```

精确局部摘要为 review05-fix-local.summary.json。以下保留历史记录；旧完整入口的六项 PASS 已被第五轮首答回执审计纠正，不能作为本候选通过结论。

---

# T-108 / a1：第四轮权限证明缺口已修复；局部 PASS，整票 INCOMPLETE

2026-10-20，执行主控 #30。父候选 f3a4a5416213e912076437cfd8ce6f69a0e3091f，仍在 exec/t108。修复 SHA 待主控执行 RUN-OUTSIDE-COMMIT-06.sh 后生成；未冒报提交。新增模型／供应商调用均为 0，没有新增真实模型回合。

F1-04 的根因是把“可选证据不存在”当作正向匹配。本次只收紧 questions.ts 的 questionPermission：必须提供完整且与保存内容完全一致的 tool_input.questions，tool_input 只能包含 questions；未知额外参数不被归一化丢弃。问题及选项内的额外字段也会因完整结构不一致而被拒绝。session、prompt／turn、submission、唯一待答问题及可选 ID 的既有核对保留；CLI 不提供 ID 的正常路径不要求它。失败仍走已有的当前回合未知事实处理，同步撤销显示状态与作答资格，没有新增异常兜底、重试、屏幕判断或门禁路径。

本次边界来自主控 #30 的明确收紧：“同问题例外必须有正向证明，也就是 tool_input.questions 存在，且问题内容与保存的问题完全一致”。因此把此前 permission_self_no_content 从正例改成阻断反例；full、matching_id、sending 正例保留，并实际通过。不是降低断言，也没有一律阻断合法的同问题权限请求。

**先红后绿：** 修前 f3a4a5416 上复现原审查 forged-name 输入，观察到 waiting_user_answer、answer 新增 1、PTY 按键 3，业务断言 unknown 失败，产物 /private/tmp/t108-review04-forged-original-red.json。加入正式矩阵后，修前 9 项业务失败；用 replay_review04_red.py 从冻结 f3a4a5416 的 git archive 重建产品、只叠加最终测试，再次取得 429 项中 9 项失败的红态。不存在导入、初始化或依赖故障冒充业务红态。

**当前默认完成条件：429 项全部 PASS。** 正式反例包含只有名称、空参数、command 参数、先收到完整 PreToolUse(Bash) 后伪装为 AskUserQuestion、复制旧 ID 后仍带 command／空参数、错误 parallel-permission ID、完整 questions 同时夹带 command／file_path，以及问题／选项内夹带额外字段。每种新增伪造形状配明确旧回合、异 session、子 agent 对照；非当前事件不得污染当前题目，当前无法核实事件必须 unknown、问题不可答、answer／PTY 零新增、active 保留、无完成／transfer。完整 Bash parallel-ID 权限请求也保持阻断。

正常原件回放 PASS：原生 PermissionRequest 没有 tool_use_id，但 questions 完整相同，问题仍为 waiting_user_answer；作答关联记录 1、PTY 边界写键 3，PostToolUse 确认后 answered，匹配 Stop 后 idle。原件来自 /private/tmp/t108-native-e2e-03.json；本次没有启动 CLI／Electron，不冒充新候选的完整入口验收。

RUN-OUTSIDE-RECHECK-04.sh 已实际运行，rc=0，产物在 **/private/tmp/t108-review04-recheck-FQOpGT**：正常原件回放、组合 IPC／原拒绝检查、侧栏、T-109 层级、T-111 流程、Codex 回放、Claude Stop／异 session、队列／输入顺序、实际 daemon/socket 零写入与身份冲突合同均 PASS。该整组运行时矩阵为 424 项；之后补入审查表中的精确 parallel-ID 对照，未改产品，并单独重跑最终默认矩阵与冻结父候选红态，均为 429 项，摘要分别是 /private/tmp/t108-review04-green-final.json 和 /private/tmp/t108-review04-red-final-proof.json。构建 PASS，成功临时构建目录已清理、日志保留。设计扫描器仅定位到红态证据脚本的报告异常边界；该边界保存错误并退出非零，不是产品兜底，也不是独立审查结论。

相对 f3a4a5416，产品只改 questions.ts；sidebar.ts、renderer.tsx、panes.ts 均无修改。README 已同步严格的正向证明条件。map status 仍 rc=1，8 个既有稀疏检出缺失链接、0 stale，原文在 project-map-review04-final.txt。原始失败现场和前四轮审查材料均保留，没有归档或删除失败证据。

主控重跑命令（摘要路径须为新文件，下面无模型入口摘要尚未创建）：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-06.sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-review04-01.json
# 需要复跑局部合同：
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-04.sh
```

**INCOMPLETE：** 新提交对应的已安装 CLI／Electron 无模型完整入口与独立审查尚待主控运行。正常原件回放和父候选完整入口的 PASS 不能替代它们。未新增真实模型、凭据读取、全局配置写入、符号链接、submit、push、截图或第二门禁。精确证据路径和边界见 review04-fix-local.summary.json。

以下保留第三轮及更早阶段记录；其中较宽的可选内容条件已由 #30 的正向证明要求取代。

---

# T-108 / a1：第三轮结构修复与主控 #28 裁定已实现；局部 PASS，整票 INCOMPLETE

2026-10-20。基于合并 main 后的 d42e8b3fa7b174f052ef43c17a81e68230ee968e。修复提交尚待主控执行 RUN-OUTSIDE-COMMIT-05.sh，不能冒报 SHA。新增模型／供应商调用均为 0；没有运行真实模型回合。

主控 #28 对 blocking issue 20261020T081754Z-worker:s18-t108-issue-001 的裁定已落实：同一 AskUserQuestion 自身的 PermissionRequest 仍属于该提问。它必须匹配当前唯一 waiting／sending 问题的 session、submission、prompt／原生 turn；可用的 tool_use_id、turn_id 和问题内容也须一致。内容用现有问题结构归一化后，与 SQLite 保存的 JSON 表示逐字段比较，不依赖屏幕、正则或关键词。已验证的同问题事件追加 native_question_permission，保留正常题目与原生 Enter 的当前根交互绑定，不产生独立 permission_wait。它不能清除已有未知或其他权限等待。

Bash 等其他工具权限请求继续优先使旧问题未知且不可答；缺工具名、公共关联字段缺失、ID／内容冲突与无法核实的同名请求，由已认证 launch 绑定未知事实并拒绝。问题投影、侧栏、answer 准入、每次异步后的按键写入以及 Stop 完成共同读取 currentTurnTrust。所有旧身份、过期回合与子 agent 拒绝／忽略检查保留；受管 worker 的 gate／attempt／fence 核对没有改动。

默认 test_t108_questions.mjs 的机械合同共 **388 项，全部 PASS**。新增同问题权限事件的完整字段、匹配 ID、未提供可选内容及发送期间正例；错误调用 ID、内容、选项、题头、turn、非法内容与公共字段缺失均阻断。其他权限请求的每个缺字段及对照仍同时检查显示未知、问题不可答、answer 零新增／仅保留失效前已开始的记录、PTY 零后续写入、active 保留、无完成／转交／解锁。

修前合并候选 d42e8b3fa 叠加最终合同后，388 项中 **286 项被业务断言拒绝**；原始输出 rc=1，已由 replay_review03_red.py 复现并保存。关键反例包括 PostToolUse 缺 cwd／transcript_path、Stop 缺 prompt_id，以及已有问题后出现 Bash PermissionRequest：旧候选仍显示 waiting_user_answer，而要求是 unknown。修前不是本次逐项补丁的实现，也没有用导入或初始化错误充当红态。

正常原件对照也已 PASS：/private/tmp/t108-native-e2e-03.json 中的真实 CLI hook，回放后依次 running → waiting_user_answer → waiting_user_answer；界面作答使用的 answer 路径新增 1 条关联记录、向 PTY 边界写 3 次按键，原生 PostToolUse 后问题 answered，匹配 Stop 后 idle。此前一律阻断的未提交版本在相同原件上得到 unknown != waiting_user_answer 的红态（/private/tmp/t108-permission28-same-red.json）。本次回放没有启动 CLI／Electron，不冒充新的完整入口验收。

完整局部重跑脚本 RUN-OUTSIDE-RECHECK-03.sh 已实际运行，rc=0，全部摘要在 **/private/tmp/t108-review03-recheck-gnnzaR**。除 388 项与正常原件回放，还通过了组合 IPC（22 handler、23 bridge，含 answer／flow／层级及原有反例）、侧栏只读、T-109 层级、T-111 流程、Codex 原件回放、Claude Stop／异 session 合同、队列／中断／输入顺序合同，以及实际 daemon/socket 的零写入和异会话冲突合同。构建 PASS，成功临时构建目录已删除，日志保留。精确摘要和边界见 review03-fix-local.summary.json。

相对 d42e8b3fa，共享文件只做 sidebar.ts 第 101 行只读事件查询接线，纳入 permission_control_written；renderer.tsx 无修改。main 中 T-109 的树及 T-111 流程功能保留。README 已更新公共字段／统一可信度及 #28 的权限区分。此前探针、失败、BLOCKED 记录与第三轮审查文件均保留，worker 不自行关闭 blocking issue。

待主控执行（每次摘要路径必须新建，下面路径尚未使用）：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-05.sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-review03-01.json
# 需要复跑局部合同时：
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-03.sh
```

**INCOMPLETE：** 当前提交对应的新 CLI／Electron 无模型完整入口、独立审查尚待主控运行；历史六项 PASS 不替本候选背书。地图 0 问题条件仍有 8 个既有稀疏检出缺失链接，未改地图来消掉它们。原始运行与失败夹具保留在 /tmp，未放入 Git、未归档或删除。没有新增全局配置写入、符号链接、门禁入口、截图、submit 或 push。

以下为 #28 裁定前及更早阶段的保留记录；其中 BLOCKED 和运行状态仅属于当时阶段。

---

# T-108 / a1：第三轮结构修复已保存，权限语义待裁定（BLOCKED）

2026-10-20，执行主控 #27 后的进度。main 已按 git merge 合入，HEAD 为 d42e8b3fa7b174f052ef43c17a81e68230ee968e。当前修复全部未提交，没有把半成品提交为候选。新增模型／供应商调用均为 0。

当前回合可信度已集中到 questions.ts：身份明确的旧回合、异 session 和子 agent 先排除；公共关联字段在事件分流前校验；拒绝与解析失败由已认证 launch 的 session／submission／turn 追加未知事实。原生 turn 尚不可知时明确记为 null，不把 submission ID 冒充原生 turn。问题投影、侧栏状态、作答准入、每次异步后的 PTY 写入及 Stop 完成前都读取同一份可信度。未知持续约束该 submission；正常无关工具不能清除它。合法 PermissionRequest 优先使旧问题不可答；仅记录原生权限控制输入可清除权限等待，不能清除未知事实。

默认 test_t108_questions.mjs 的矩阵已扩大到 **373 项，当前全部 PASS**：Claude 与 Codex 各种 hook 的 cwd、transcript_path、prompt_id／turn_id、session_id 和适用的工具字段逐项缺失，配完整当前、明确旧回合、异 session、子 agent 对照；还有运行中缺字段的 Stop、非法响应／JSON、PermissionRequest、记录与逐键写入期间的失效。每个拒绝场景同时检查未知、问题不可答、answer 零新增或仅保留失效前已开始记录的输入、PTY 零后续写入、active 保留、无完成／转交／解锁。完整 PermissionRequest 对照也运行全部阻断断言。

**修前业务红态已取得。** 可重建的冻结合并候选 d42e8b3fa，叠加最终测试，不修改产品：373 项中 271 项被业务断言拒绝，没有导入、初始化或依赖故障冒充红态。关键四例均仍显示 waiting_user_answer：PostToolUse 缺 cwd、缺 transcript_path，Stop 缺 prompt_id，以及正常 PermissionRequest 到达已有问题之后。重建命令与摘要见 replay_review03_red.py、/private/tmp/t108-review03-red-repro-01.json。

组合 IPC（保留 answer／flow／层级和原拒绝检查）、侧栏只读、T-109 层级、T-111 流程、实际 daemon/socket 的零写入与异会话冲突合同、Codex 原件回放、Claude 正常 Stop／异 session 拒绝、队列／中断／迟到 Stop 及输入顺序合同均 PASS。相关旧合成夹具只补齐公共字段，没有删断言。Codex 新启动的 hook 来源复用已有严格 nativeSessionFile 定位器；恢复已有定位结果可直接核对。collector 的扫描范围、辅助来源及异会话拒绝语义保持原样。构建 PASS，工作者创建的成功临时构建目录已清理，输出日志保留。所有摘要路径见 review03-progress.summary.json。

**仍 BLOCKED：正常提问原件与一律权限阻断冲突。** 旧完整入口六项 PASS 的 /private/tmp/t108-native-e2e-03.json，真实 hook 顺序本身就包含 PreToolUse(AskUserQuestion) → PermissionRequest(AskUserQuestion)。本轮用原件回放实际 signal／SQLite／作答路径，得到等待用户回答 → 未知，answer 新增 0、PTY 写入 0。这符合 #26 一律阻断的要求，却挡住了原有“从工作台界面作答写回”的正常路径。观察摘要 /private/tmp/t108-review03-permission-conflict-02.json 不作为新完整入口 PASS。已追加 blocking issue 20261020T081754Z-worker:s18-t108-issue-001；详细事实及最小裁定见 permission-semantics-issue.md。

请主控裁定：同一 AskUserQuestion 自身的 PermissionRequest 是否属于这个原生提问；其他工具权限请求仍优先阻断旧问题。若一律阻断，需要明确原有界面作答验收如何满足。未自行加入例外，未重跑真实模型，未新跑 Electron，未宣称独立审查通过，未交修复提交脚本。RUN-OUTSIDE-RECHECK-03.sh 可重跑局部合同和上述冲突观察，不执行提交；脚本只做语法验证，组成命令已分别执行，不把整份脚本说成已跑。

相对 d42e8b3fa 的共享文件接线：sidebar.ts 仅第 101 行，把 permission_control_written 纳入只读事件查询；renderer.tsx 无修改。T-109 树与 T-111 流程保留。地图状态仍 rc=1，8 个既有稀疏检出缺失链接、0 stale，见 project-map-review03-progress.txt。原始失败现场保留在 /tmp，未放进 Git；未归档或删除这些现场。

以下保留此前阶段记录；其中运行与批准状态仅属于各自阶段，不代表当前未提交实现通过。

---

# T-108 / a1：无模型完整入口 PASS，整票 INCOMPLETE

分支 exec/t108，起点 6411bdff8482ba47da207efa6a295a12666222aa。未运行任何真实模型回合，model_calls=0、vendor_calls=0。CLI 原生交互探针只连接本地假 API，未使用正常登录。

## 主控 #6 复跑处置

旧入口 `/private/tmp/t108-native-e2e-01.json` 为 INCOMPLETE，保留原文件与夹具。失败在驱动第 3 次调用 prompt，尚未点击答复。驱动模板把 `\r` 展开为 JavaScript 字符串中的裸回车；独立解析复现 SyntaxError。已用 JSON.stringify 序列化终端字节，补 renderer-console.jsonl 和错误回执中的 console 摘要。选项禁用与所有原有断言保留。

局部验证：`node workbench/tests/test_t108_driver.mjs /private/tmp/t108-driver-fix-02.json`，PASS。相同解析路径拒绝旧的裸回车，候选驱动实际脚本可解析，写入字节严格等于 bracketed paste 和单独 Enter。它不替代 Electron 入口复跑。

清理实际执行了 daemon_stop 且移除了 daemon.pid；遗漏的是原生 CLI 的退出核验。产品 terminate 对 controller/worker 只等待 PTY shell，未像 shell 窗格一样确认子进程，CLI 的独立进程组可能存活。范围外缺口已报 triage：20261020T055224Z-worker:s18-t108-issue-001。未改产品关闭或门禁语义。

处置脚本先检查完整 session、debug 路径、启动时间、PID 和 argv，再向准确的测试 PID 发信号；PID 被复用或归属无法核实时拒绝，不删除旧夹具。新的入口 finally 绑定本次捕获的原生 CLI／daemon 身份，清理后确认两者退出；摘要填入 model_calls、vendor_calls 与假 API 请求数。Electron 未退出时保留构建目录。

交主控执行，结果均待回传：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-CLEANUP-01.sh /private/tmp/t108-cleanup-01.json
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-02.json
```

## 已有局部证据

- Claude 2.1.304 实际 CLI hook：单选 `/private/tmp/t108-claude-probe-05.json`、自由答复 `/private/tmp/t108-claude-free-01.json`、两题 `/private/tmp/t108-claude-batch-01.json` 为 PASS；多选探针失败，未开放多选写回。
- Codex 0.163.0 实际 CLI hook：同步单选 `/private/tmp/t108-codex-probe-03.json`、自由答复 `/private/tmp/t108-codex-free-03.json` 为 PASS；异步 `/private/tmp/t108-codex-probe-02.json` 只返回 accepted，不证明阻塞，保持未知。
- 新功能的旧实现红态 `/private/tmp/t108-red-02.json`：真实 signal 入口拒绝 PreToolUse，属于未实现新合同的预期红态。早一场 red-01 是夹具未建立 turn_submitted，不作为红态。
- 当前 hook／PTY 局部合同 `/private/tmp/t108-green-02.json`，12 项 PASS；IPC `/private/tmp/t108-ipc-01.json` PASS，保留原拒绝检查。
- T-107 只读回归 `/private/tmp/t108-sidebar-01.json`、`/private/tmp/t108-readonly-01.json`、`/private/tmp/t108-review-regressions-01.json` 为 PASS；后者包含旧实现与写入变异对照。

这些是局部或无模型证据，不证明正常登录、实际模型提问或系统通知。真实模型计划须先通过无模型完整入口，再交主控批准。T-093 正常登录入口固定 Claude 2.1.302，当前只安装 2.1.304，版本缺口未绕过。

`project_map.py status` 存在起点已有的 8 项稀疏 checkout 缺失链接，尚未满足票中 0 问题；不修改地图或其他 ticket 消除该报告。

## 主控 #8／#9：第二次入口超时

清理脚本 `/private/tmp/t108-cleanup-01.json` 为 PASS。第二次入口 `/private/tmp/t108-native-e2e-02.json` 仍为 INCOMPLETE，model_calls=0、vendor_calls=0，CLI 与 daemon 均已确认退出，没有残留。

`Matched Stop after answer` 是 until 超时的说明：要求问题回答后原生回合结束，匹配 Stop 推回 idle；不是禁止 Stop。保持该验收期望。故障属于测试夹具，未修改产品状态逻辑。

现场独立证据：

- 假 API 根请求数和总请求数均为 8。原生 hook 只有 UserPromptSubmit、PreToolUse、PermissionRequest、PostToolUse，没有 Stop；PostToolUse 确认回答为“西区”，native_question_resolved 已为 answered。
- 原生 session 文件中 msg_t108_2 的 content 为 text=""、stop_reason=end_turn；后紧跟 CLI 自身追加的 `[Your previous response had no visible output. Please continue and produce a user-visible response.]`。
- claude-debug.log 在 05:56:23.732 读到第二个流，05:56:23.797 再发请求；之后 409 重试直到清理。夹具把最终正文写进 content_block_start，却没有 content_block_delta/text_delta，CLI 因而组装出空回复，并撞上夹具原有的两次请求上限。

修复：按 [官方 SSE 文档](https://platform.claude.com/docs/en/build-with-claude/streaming) 发送空 text block start、text_delta 正文、block stop、end_turn 和 message_stop。同一错误也在 Claude 独立探针夹具中修正。两次根请求上限与 idle 断言均保留；额外要求原生最终文本为“已收到答复。”，唯一 Stop 与唯一 UserPromptSubmit 的 prompt_id 相同，pane_idle 事件在 answered 之后且携带该 Stop。摘要无论成功失败都保留已收到的 hooks、回合事件和每次假请求的 tool_result ID。

局部反事实（同一个实际 HTTP handler，无模型）：

```sh
python3 -B workbench/tests/test_t108_fake_stream.py --source /private/tmp/t108-e2e-before-sse-fix.py --summary /private/tmp/t108-sse-red-01.json
python3 -B workbench/tests/test_t108_fake_stream.py --source workbench/tests/run_t108_native_e2e.py --summary /private/tmp/t108-sse-green-01.json
```

第一条 rc=1，准确拒绝未传 text_delta 的最终回复；第二条 rc=0，PASS。Python 3.9 语法与 git diff --check 通过。这不替代实际 CLI／Electron 完整入口。

新的完整入口交主控执行，摘要尚未生成：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t108-native-e2e-03.json
```


## 主控 #11：候选与真实回合计划

主控回传 `/private/tmp/t108-native-e2e-03.json` rc=0，PASS。六项均通过：实际 controller_start／已安装 CLI、Electron 问题与选项及等待状态、DOM 作答写回原 PTY、PostToolUse 确认后匹配 Stop／idle、answer 用户输入引用该问题、重复作答拒绝。model_calls=0、vendor_calls=0；假 API 根请求与总请求均为 2，两个测试进程确认退出。仓库保留 `no-model-03.summary.json` 与小型 `native-hook-samples.json`，不保存截图、SQLite 或运行日志。

Codex 当前 CLI hook 原件回放 `/private/tmp/t108-codex-hook-replay-green-01.json` PASS，已知坏对照 red-02 因 running != waiting_controller_answer 准确失败；red-01 是夹具缺字段，未计作红态。原件来自实际 0.163.0 CLI＋本地假 API，不是供应商真实模型证据。

交主控提交当前候选：`zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-01.sh`。脚本固定本 worker 的公开身份环境，原钩子核对启动记录并自动加尾注；git add 带 --sparse，只加本票文件。不运行 submit、不 push、不写 git config。提交尚未执行，SHA 待主控回传；候选未经过本次独立 reviewer 审查，不宣称可集成。

真实模型计划见 [REAL-TURN-PLAN.md](REAL-TURN-PLAN.md)：仅申请 Claude 1 根，预计 2 条生成请求，T-093 正常登录，600 秒 F/D 生命周期。当前缺该入口固定的 Claude 2.1.302 二进制，不用已装 2.1.304 绕过。准备工具和真实命令均未运行，未读取正常登录凭据。Codex 选择已保存原生 CLI hook 原件回放，新增真实预算 0；来源与同步真实模型证据的缺口明确保留，不能靠改口径标全票 PASS。

合并冲突位置见 [CONFLICT-LINES.md](CONFLICT-LINES.md)：sidebar.ts 5、22–24、46–48、101–102；renderer.tsx 12–13、16、56、300。未改侧栏树结构或树渲染。

另有起点已有的 Codex xhigh 强制规则与当前 high 规定冲突，已报 triage 20261020T061048Z-worker:s18-t108-issue-001。本票不修该规则、不绕过门禁开真实 worker。

## 主控 #13：记录当前版本，真实运行待外部执行

首个候选已由主控提交为 **16b412964**。用户逐字：“跑真实回合,版本不重要,以后肯定要经常更新 cli 版本的”。主控据此批准 Claude haiku 5.5 low 的 1 个根回合，T-093 正常登录；失败不补发、不自动重跑；Codex 原件回放新增 0 根。effort 冲突由主控另票处理，本修订未改 panes.ts。

三处发行号锁已去除：claudeLaunch.ts 与 claudeLoginSession.py 校验本次版本记录的结构，claudeLogin.ts 在受保护环境读取 --version 并与本次 manifest 观测值核对，拒绝运行期间版本变化；不再要求等于 2.1.302。准备工具自动读实际安装版本；启动记录的 cli_version、role_card_revision 与最终 facts 的 cli_version／internal_state_version 跟随该次版本。保留私有 session/manifest 等值、auth_original_reads=1、版本失败、当前身份、隔离 HOME、网络与凭据清理检查。

没有静默认定 2.1.304 的内部状态仍可用。现有 T-093 onboarding/auth 探针改为读取并核对当前版本，其余安全检查、未知屏幕停止、禁止业务按键及清单差异判定均保留；外部探针尚未运行。真实脚本要求探针 PASS、清理成功、无凭据泄漏且版本仍一致，再走原保护入口；只发送一次根输入并沿用已通过的 Electron 问题/作答路径。实际登录与模型执行尚未发生。

本地验证（全部无真实凭据读取、无供应商模型调用）：

| 信号 | 结果 |
| --- | --- |
| test_t093_launch_profile.ts，修前 16b412964 产品源码 | /private/tmp/t108-version-profile-red-01.json：因 normal_login_version_requires_probe 精确失败；不是其他入口故障 |
| 同一版本构造合同，修后 | /private/tmp/t108-version-profile-green-01.json：PASS，4 项；动态 2.1.304、非法版本拒绝与原 hook 合同 |
| test_t093_session_once.ts | /private/tmp/t108-version-once-green-01.json：PASS，4 项；实际构造使用 2.1.304 替身，严格一次消费未变 |
| test_t096_restore.mjs | /private/tmp/t108-version-restore-green-01.json：PASS；样本改为记录 2.1.304，保存版本不一致仍拒绝，正常登录恢复仍拒绝，原变异继续拒绝 |
| test_t091_claude_version.mjs | /private/tmp/t108-version-refusals-01.json：PASS；缺 CLI、探针失败、版本不一致、并发身份拒绝及原变异保留 |
| test_t093_probe_safety.py | 22 项 PASS；仅合成探针辅助检查，不是实际 CLI／OS 探针 |
| test_t093_prepare_failure.py | /private/tmp/t108-version-prepare-failure-01.json：PASS，3 项 |
| test_t093_forwarder_port_policy.py | /private/tmp/t108-version-port-policy-01.json：PASS，10 项 |
| test_t093_session_cleanup.py | /private/tmp/t108-version-session-cleanup-01.json：PASS，5 项 |
| Codex 原件回放 | /private/tmp/t108-version-codex-replay-01.json：PASS，新增真实根回合 0 |

相关命令均为 `LC_ALL=C node [--experimental-vm-modules] workbench/tests/<上表脚本> <摘要路径>` 或 `LC_ALL=C python3 -B workbench/tests/<上表脚本> [摘要路径]`。Python 3.9 AST、zsh 语法与 git diff --check 通过。

按顺序交主控执行（尚未执行修订提交，不能冒报 SHA）：

```sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-02.sh
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-VERSION-PROBE-01.sh /private/tmp/t108-version-probe-01.json
# 仅上一步 PASS 后：
zsh evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-REAL-01.sh /private/tmp/t108-version-probe-01.json /private/tmp/t108-real-01.summary.json
```

外部版本探针与真实回合均待运行，整体仍 **INCOMPLETE**。新真实脚本仅做语法和调用合同核对，未取得 OS／CLI／供应商边界的新绿态；不复用旧 T-093 或无模型 PASS 代替。
