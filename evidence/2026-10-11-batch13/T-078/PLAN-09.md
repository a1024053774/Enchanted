# 材料 09：分场景扩展单回合通路

依据主控 #116。08e 仅证明固定 CLI＋假 API 的一个完整回合，原件已提交 `675fac49`；用户处置由构思主控抄录并单独提交 `f3b33316`。整票仍 INCOMPLETE、open。所有实际启动／Unix socket／Electron／ps／信号均交主控执行，不申请提权，不启动真模型或真实 Codex。

本次准备按 09A → 09B → 09C 连续审批；这只是顺序，紧急停止与双主控范围不删除。本次 launch 只对应 09A；09B/09C 的新 manifest、权限与执行器在 09A 实际取消行为读回后冻结，不把它们写成当前已实现／已验证。T-077 合入后由主控安排变基，当前材料全部重新生成并完整重跑。

## 事实和未知

- observed：08e UserPromptSubmit／Stop 都有 prompt_id，值相同，hook exit 0；单回合 API、busy→idle、cleanup 已读回。
- observed：当前 launch 仅配置 turn_limit=1；Claude signal 显式拒绝多回合，controller relay 明确未启用。nullable 主控窗格的 window_input 仍套用 worker attempt 校验。Esc 的现有写入只设 interrupted，没有清理 Claude active 关联。
- documented：[官方 common input](https://code.claude.com/docs/en/hooks#common-input-fields) 定义 prompt_id 可关联一个用户 prompt；[官方 Stop](https://code.claude.com/docs/en/hooks#stop) 不在用户中断时运行。不能等待一个保证不存在的 Stop 才清理 Esc，也不能伪造 hook。
- unknown：固定 2.1.296 在本次流式假 API 取消时的实际网络关闭、屏幕、是否有额外请求／其他 hook；第二回合的实际 ID 与 late Stop 时序，均须 09A 原件证明。

**Tracer bullet**：先一名真实 CLI 的取消与第二提交，再扩展两个实际角色及 inbox。**Deep modules**：复用现有窗格、串行写入、窗口凭据与门禁，改其所有者处的生命周期，不新增并行入口。**Ubiquitous language**：窗口放行、人工介入、回合、派发、stop／ack／只中断沿用本仓术语。

## 09A：Esc 释放与第二条 nonce

一个新隔离根、真实 ideation CLI、两条独立 nonce、两个主 Messages 请求。调用者 executor 仍是已认证的 operator；本场景不冒称双主控互相协作。fake API 首请求流保持开放，接受取消；第二请求独立可进入，不能被第一条占住。不会由 fake API 产生 CLI hook 或后台完成事件。

| 步骤 | 动作／证据 | 失败停点 |
| --- | --- | --- |
| A0 | 新 launch 参数、环境白名单、root／session／thread／代码／源码绑定；逐屏主题、固定 notice、信任 Down→Yes→读回→Enter；主提示符 readiness 单独批准 | 版本、原文、身份、目录或权限选择不符；不补键、不重试 |
| A1 | 另批 continue：初始放行，登记 nonce1，paste＋CR，实际 UPS1 stdin／exit 0、prompt_id1、active1、busy、API request1；API 仅发送开始事件并持有 | hook 缺／非 0、无可核对 prompt_id、dispatch 或 API 不匹配、额外请求 |
| A2 | busy 期间登记 nonce2；保存 queue 与 PTY 前后字节，nonce2 尚无 paste／CR／请求2 | 自动注入或二次提交提前发生 |
| A3 | 经本实例窗口凭据发送一次 Esc，记录用户动作、write intent／written、retired active1；active=null、interrupted=true、state=busy，queue2 保留；fake API 记录真实 peer 取消 | 用户记录失败、Esc 字节不符、active 未释放、队列自动放出、网络未取消／额外请求；不合成 Stop |
| A4 | 另批用户放行：窗口 action queue-release，清理 draft／interrupted，nonce2 单次 paste＋CR；UPS2、prompt_id2≠id1、active2、API request2 | 用 operator 初始 release 代替用户放行、重复副作用、ID 复用或第一回合占住第二请求 |
| A5 | 放开第二脚本响应；ACK2、实际 Stop2 stdin／exit 0、ID2 精确匹配、一次 pane_idle，active=null | 旧／错误 Stop 结束回合2，缺 hook、非 0、重复完成、请求预算越界 |
| A6 | cleanup 只停本 manifest 的服务；实际 CLI 退出确认后归档／删除本根；>5 MiB 外置留清单 | PID／启动身份不符、仍存活、无法确认或超限未归档 |

原件测试／反例（不启动 CLI）：用 08e 实际 hook 字段复现 Esc 不清 active、单回合限制、旧 Stop 错配、放行残留关联；窗口 nullable 主控与 worker attempt 边界分别检查。缺 ID、重复 ID、late Stop、窗口撤销、身份／版本改变、记录失败、超预算均不能被绿态隐藏。业务红态与不可达入口红态分类保存；不能改原 acceptance 断言。

09A 预算：两次根提交、两个主 Messages 请求，真实模型 0；count_tokens 只返回固定夹具值，不算模型请求。一个实际 CLI，每次启动独立批准。取消／完成等待有界，失败保留、不换认证、模型或 CLI，不自动重试。Electron 用户动作是受控测试操作，报告不冒称真实用户亲手操作的观测。

## 09B：stop → 执行 → ack

真实 ideation 与 executor CLI 均只连假 API，各自隔离 HOME／CLAUDE_CONFIG_DIR、launch/session、capability 和请求目录；另有受管确定性 worker 接收器作为目标，明确标注不是真实 Codex。每个 CLI 的启动、工具权限与引导单独审批。Claude inbox 转交、角色凭据及 target 绑定必须先有红／绿和权限反例，不能用 operator 凭据替实际角色。

| 步骤 | 必须读回 | 失败停点 |
| --- | --- | --- |
| B0 | 两份独立完整 argv/env／角色卡／hooks；同任务归属及 worker task/attempt/session/fence；各自新屏引导批准 | 共享／复制用户认证、身份串用、无法绑定目标、未批准工具权限 |
| B1 | ideation 实际 CLI 的库客户端写 stop；请求／Stop hook 转交／库行；sender 取其凭据，stop_id 与目标固定 | 整入口不可达、参数伪造 sender 被采信、未入库或重复条目 |
| B2 | executor 收同一条 stop 及带标记唤醒；实际 CLI 客户端执行 stop，库行调用者 executor、目标 PTY 只一个 Esc | 用脚本自报代替真实角色调用、错目标、kill／archive／reclaim 或记录失败 |
| B3 | executor ack 引用同一 stop_id；库追加 ack，来源真实，重复 ack 不多写／不多中断；ideation 收回执 | ack 未拥有、来源冒充、ack 先于执行、重复副作用 |
| B4 | 错 session／撤销凭据／伪造 from/role 反例及最后完整 cleanup | 放松 submit／角色边界；不修改业务断言 |

假 API 工具响应只是驱动实际 CLI 调用预先批准的夹具命令；不会直接 append inbox 或伪造 hook。准确工具命令、权限参数、根提交／Messages 预算在 B manifest 中展开后另批，当前未冻结、未运行。

## 09C：120 秒无 ack 后只中断

与 B 一样使用实际角色与受管夹具目标，新的 stop_id。fixture 明确持续要求停止该隔离目标；不能把它报告成用户真实现场紧急请求。executor 故意不 ack，由受控 fake API 屏障保持，记录没有 ack 的事实。

| 步骤 | 必须读回 | 失败停点 |
| --- | --- | --- |
| C1 | ideation 写新 stop；真实 created_at、target 与身份；executor 接收但无 ack | 无法核对、旧 stop_id、错目标或身份 |
| C2 | 真实时钟早于 120 秒的 break-glass 调用被拒，PTY 不多写；按不超过 30 秒的只读采样记录无 ack、用户 fixture 仍要求 | 快进数据库时间、用 mock 时钟充当此实测、提前放行、采样失联 |
| C3 | ≥120 秒仍无 ack，ideation 实际客户端只做中断；追加实际调用者、耗时与目标；只一个 Esc，非 kill/reclaim/archive | 自动升格权限、未重新核对 ack／目标／用户 fixture、任何越界副作用 |
| C4 | 已有 ack／撤销身份／错误 stop 反例，全部由对应规则拒绝；所有本次进程 cleanup | 只用“入口整体拒绝”冒充规则证据、自动重试或清理未确认 |

C 最长 150 秒观察窗口，超过即 INCOMPLETE。每个真实等待阶段输出进展，主控分段观察，不让 worker 发起超过 60 秒的阻塞等待。C 的新 launch／工具命令／输入／预算须在 B 的真实角色与 inbox 证据通过后另行冻结审批；本次不启动。
