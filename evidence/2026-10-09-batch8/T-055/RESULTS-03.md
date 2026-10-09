# T-055 ready_rev 2：实现与验收交接

状态：**INCOMPLETE（工程验收 PASS；最终候选的独立审查待执行主控决定）**。最终 fork 候选 `2330534b2cf906b9d8f0a0b643adb370683d7fe0`，基线 `6efac8432d7ae37e74b76e42d4e9fd3004d9a0e2`，分支 `a2a`，未 push。ticket 保持 open，待主控关闭。首轮及第二轮 BLOCKED 报告、所有红态和异常原样保留。

依据 T-055 `ready_rev: 2` 与决定 01～03。用户最后确认“确认是用户或其他已知会话改动”，见 [确认记录](user-config-confirmation.json)。未改地图、规则、术语、ticket 正文或验收条件。

## 主控需要决定

一次 fresh-context 只读审查由 `t055_acceptance_review` 完成，目标固定为 `27344e471`，结论 **FAIL**，发现一个 P1：原生会话已归档但 attempt 尚未回收时，答复被保存，却没有 `forward / session-ended` 处置。[审查原始结论](acceptance-review-raw.txt) 保留 FAIL，未上调。

已在真实隔离服务复现并修复：只捕获明确的 `Refusal("session_ended")`，追加转交记录；其他送达错误继续失败。随后收尾发现原生 archive 拒绝重复执行，服务端在读回已归档事实后不再发第二个 archive，门禁仍核对停止、身份和最终归档状态。两项修复都有真实红绿记录及最终候选的既有套件复验。

任务书只授权一次独立审查，已执行；没有自行再开审查。最终候选未经再次独立审查，故不宣称独立验收 PASS。执行主控可审阅修复证据后经门禁验收/关闭，或明确授权追加复核。这是对证据边界的保守判断，不是 skill 明文要求增加审查次数；[behavioral-acceptance-review](</Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md>) 要求“Review one frozen candidate snapshot in a fresh, read-only context.”，并规定候选变化时返回 INCOMPLETE，不能追逐变化中的目标。旧候选的判定不能替最终候选背书。

## 工程验收与独立预期

Tracer bullet 经真实 Synara 应用服务层、MCP 凭据、门禁核心 SQLite、HTTP/CLI、任务窗口与原生 Codex app-server。Deep modules 的持久化与状态写入仍由核心负责；Ubiquitous language 沿用 task、attempt、thread、用户输入、人工介入。没有第二套门禁业务状态、内容含义的正则/关键词判断、自动标注或运行依赖。

| 条件 | 结果与证据 |
| --- | --- |
| 父修订红态 | PASS：真实 `tools/list` 无 a2a_raise，面板路径未挂载，脚本合同断言失败。[red-entry-01.json](red-entry-01.json)、red-entry.py 与 setup-failures-02.txt |
| 免确认红绿与保护反例 | PASS：未登记目录时 3 正例失败、9 保护反例通过；只加工具名后 12/12。测试运行实际 CodexAppServerManager 的权限决策，只控制原生 I/O；涵盖 full-access、已有 grant、无 grant、lease 缺失/退休、空闲/过期 turn、其他 thread/server、停止中、无关工具。permission-red-rev2.log、permission-green-rev2.log、service-delivery-candidate.log |
| 真实无人批准上报 | PASS：Codex 0.162.0 / gpt-6.1-sol / xhigh，full-access 依据决定 03 第 3 项。没有 approval.respond、coordinator 标记或待批准请求；返回问题 1 与 UUID，实际记录落库。[unattended-observation](round4/unattended-observation.json)、unattended-issues.json、model-turns.json |
| 活跃凭据与身份反例 | PASS：第二个真实 turn 的同一线程凭据携带伪造 thread/threadId 参数，上报仍绑定原 task/attempt/thread，正文哨兵逐字保存；编号 2、3。未绑定 task 的活跃原生帧被 stale_thread 拒绝，真实 worker 空闲后被 caller_turn_inactive 拒绝，无效凭据 HTTP 401。后两类及非受管帧不运行替身模型，HTTP/凭据/网关/核心均为真实实现。[boundaries](round4/boundaries/negative-state-unchanged.json)、raise-2/3 输入及回执 |
| 门禁业务状态 | PASS：上报、答复和反例前后的完整 task 相等，仍 claimed，fence、attempt、候选、验证与集成字段均不变。收尾 reclaim 的 ready 变化另行记录，不归因于用户输入 |
| CLI/HTTP 严格 JSON 链 | PASS：实际 a2a/scripts/gate → cli.ts → HTTP 返回 issue → answer → delivered；status/events 含 task/attempt/thread 绑定。CLI 只借用夹具自建的 endpoint/PID 发现文件，未模拟业务结果、不代表 Electron 启动器验收。round4/boundaries/gate-*.json 与 *-command.json |
| 面板与发送 | PASS（功能，不判断外观）：真实 dev UI 位于会话旁，标题、正文、blocking、回复框与按钮可见；后上报的问题 3 为 blocking，排列为 1、3、2，区别于编号顺序。[发送前截图](round4/panel-final-before-send.png)、[发送后截图](round4/panel-final-after-send.png)、panel-final.json |
| 精确用户消息与实际接收 | PASS：预期串由 spec 第 4 节手写，未导入实现模板；去除输入末尾空白后，消息逐字相等，role=user、dispatchOrigin=user。真实 worker 第二次 turn 收到并回复该答复。[reply-oracle.json](round4/reply-oracle.json)、reply-complete-native.json |
| answer 与派生事件恰一次 | PASS：普通送达场景恰 1 条 answer、reply_to=问题 UUID、1 条指向 input_id 的 human_intervention、0 条重复 message；message id 对应原生消息。来源引用缺 event id/序号的探针先红后绿，现指向权威 Gate answer 域记录。source-ref-red/green.json |
| 重启、重放与不可变 | PASS：上报后重启仍在；答复后再重启，记录链、输入与全部门禁事件逐条相同，observer=healthy。对 issue_records、user_inputs、events 的 6 次 UPDATE/DELETE 被 append-only trigger 拒绝。[replay-oracle.json](round4/replay-oracle.json)、append-only-final.json |
| 会话结束与未知送达错误 | PASS：真实归档会话在 attempt 未回收时先红态，修复后保留答复、转交 executor、理由 session-ended，不新增原生消息；600 字 Unicode 正文截断也手写核对。未知送达错误不转交、不伪称成功。[ended-session-red/green.json](round4/ended-session-green.json)、unknown-delivery-negative.json |
| 归档会话经门禁回收 | PASS：重复 thread.archive 被原生拒绝的红态保留；修复后同一原生已归档会话经 gate reclaim 成功，current_attempt=null。[reclaim 红态](round4/reclaim-final.json)、[绿态](round4/reclaim-archive-green.json) |
| 既有套件 | PASS（最终 2330534b2）：交付 8 + 恢复 9 + 编排 18 = 35，仍为既有独立分页 oracle；分别 17/17、18/18。delivery-recovery-delivery-candidate/、orchestration-delivery-candidate/ 保留 exact argv/env/源码/输出/Git 现场 |
| membership | PASS：两任务、角色、CAS、未知身份、重复成员、跨项目、gate 项目绑定、trusted origin、OPTIONS、共享任务操作锁。membership-final.jsonl、round4/membership-* |
| 类型、lint、格式、相关 Vitest | PASS：最终全 workspace typecheck、lint、fmt:check exit 0；lint 870 warnings、0 errors，sync-fs 检查通过。服务/权限 68/68、gates 1/1、web 人工介入/字号检查通过。未跑完整全仓测试、平台边界检查或桌面构建，按任务书限于相关检查；无平台/process 代码改动 |

实际实时上报初段与来源字段修复、审查后的结束分支修复分别保存代码版本，未把某个早期候选的完整通过结论移给最终候选。普通上报/答复的真实证据、最终改变分支的独立反例红绿以及最终既有套件分别支撑对应行为；最终独立审查仍为缺项。

## 上游清单、范围外发现与过程失败

上游只改两处文件：`AgentGateway.ts` 的 import 与注册；`computerToolPermission.ts` 的一个网关目录项。其他改动在原四个目录内：gates 核心/CLI、contracts、server a2a、web a2a，以及 a2a 内的权限测试。未改 codexAppServerManager、其他工具、会话权限策略、共享 dist、依赖目录或正式工作台。

范围外解析发现保持开放：[native-name-finding.md](native-name-finding.md)，收件箱 `20261009T115645Z-worker:t055-issue-001`。缺 tool_name 的受控生成提示中，数字名称 a2a_submit 与 a2a_raise 都保留提示；当前真实 CLI 成功，未将该格式探针冒称为真实 CLI 失败。原 13 项诊断与失败测试源码全部保留，正式目录保留本票的 12 项契约；未修改不在批准范围内的解析器。

准备失败均保留：错用相对 Playwright 路径、未处理延迟导览造成按钮等待/浏览器关闭、误将工具拒绝的纯文本当作 JSON、重复 project workspace root 被拒。修改的是夹具等待、入口与预期封装，不改产品保护。GPU 开关探针未解决问题，最终脚本已移除该开关；直接点击迟到的 Skip tour 后通过。Node/Bun 启动失败及旧版本断言见前两轮报告。

## 隔离与交付

最终无人批准场景只有 2 个真实 turn；决定 02 阶段另有 1 个 turn/1 次 accept（id `7c10bc35-5a69-435e-b472-591d62fab07e`，理由和时间见 round3/manual-approval.json），发生在决定 03 撤销之前；首轮阻塞另 1 次。没有为修复、重启、边界与收尾再调用模型。

所有 CODEX_HOME 都在 /tmp，只有 auth.json 副本、核对过的夹具根、git add/commit 两条规则、固定 CLI/显式 Fast 请求/关闭启动更新，无 hook；整个 home 已删除，证据与归档不含 auth 或 endpoint。原始 rollout 与含 HMR token 的诊断仅本地保留并排除 Git，分享诊断已脱敏。Fast 请求不证明供应商 tier，原生设置读回 priority。

用户 config.toml 的 mtime 在 11:22:15 UTC 变化，大小/权限和 rules 不变；用户确认来源是用户或其他已知会话。Herdr 原始 status 前后相同，不宣称用户配置字节未变。[cleanup-auth-final.json](cleanup-auth-final.json) 与确认原话保留。

只停止本次创建并核对 PID/命令的进程，最终 server/Vite/provider 均退出；没有操作正式工作台或用户 Herdr。SQL/Git/worktree 完整现场在 retained-final-fixtures.tar.gz（索引 JSON），不登记 gitlink、不删除失败现场。未 push，其他人的 dirty 文件与 .grok/ 保留。

重放命令在每个 *.command.json；真实完整场景用 start-server.py、prepare-real.py（full-access）、panel-send.mjs、reply-phase.py、boundaries-and-cli.py，必须换新 evidence label/root，避免覆盖原场景。模型额度与隔离规则继续适用。当前需要执行主控对最终独立验收缺项作决定。
