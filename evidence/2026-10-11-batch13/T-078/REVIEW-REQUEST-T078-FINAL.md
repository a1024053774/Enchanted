# T-078 当前候选独立审查请求

2026-10-16，主控 #332/#333。**独立审查 INCOMPLETE／待主控安排。整票 NO_GO（尚缺 09C 等证据），不得把本请求作为验收 PASS。** worker 没有新开 Codex/子代理，也不以自查替代新上下文。

仓库 `/Users/luckye/Documents/Code/a2a-wt-t078`，分支 exec/t078。**唯一冻结候选为 `92874fe7f320a9a4a47e61adacedd26fc58078c7`**，含 A-15 正式回收输出与签字件。请主控将此完整 revision 传给新只读 reviewer，不让 reviewer 追逐移动 HEAD；之后的剩余验证计划与本请求文字更新不改变该候选的运行结论。运行版本组合固定为：

- 业务源码 `dedd4f66bc424610183cbff2d7114e991483e1c6`（含 main/T-082 合并、pending/startup 与受控宿主修复）；当前 workbench/src、app 与该版本的 Git diff 为空。
- 完整 reader harness `c0c5caee3e70e58abadbd55efa4eade72a44370b`，包 09b-a15-reader-harness-01；原 58 文件只改三个只读 caller、其余 55 逐字不变，新增闭包显式列出，harness 65 文件。不可只审显示函数。
- A-15 全部续行原件/签字与外侧 9 组复验提交 `34aa4e130`；全场安全投影/来源为 09b-a15-final-check-04。主控 #333 的 dry-run、脱敏归档和正式 cleanup 均 PASS，已纳入上述冻结候选；不能以准备期 file check 替代这些运行原件。
- scope 不含推送/集成/关闭票、真实供应商模型质量、真实 Codex、用户自己的 HOME、09C 的尚未进行实跑。

从 ticket、用户原话 answer 20261016T012505Z、spec 及冻结 protocol 重建验收，不把 worker 的表格或新 oracle 当答案。先核对 [全票状态](RESULTS.md) 文末与 [A-15 全场来源](09B-A15-FINAL-CHECK.md)，然后检查以下可达行为及独立反例：

1. 两个实际 controller 的 launch/preset/project/task/spec_rev/native session/prompt_id、真实 leader 与请求目录绑定；Stop 才转交异步请求、工具 queued 不冒充执行、worker fence/attempt/CAS 没被 controller 的 null attempt 绕过。伪造 --from/--role、外人 ack、错目标、重复 ack、已 ack stop 有实际拒绝/幂等证据。
2. 无角色会话的 stop 真正保存 pending，发送方可见、无反馈，created_at 不重置；上线后 unknown 队列不写业务；六个首启键允许但真实收据仍 queued，M5 将 key receipt 当 delivered 的坏实现必须失败；初始 release 的 turn_submitted 才 delivered，原 request/entry 的 I2 恰一次。delivered 后 I2 时点是主控解释，不改写用户原话。
3. 输入/注入区分、控制字节 action、composition/new input 使空框声明失效、声明引用具体中断/代次、后台不删草稿、UPS 精确登记匹配、仅尾 CR/LF 的登记规范化、Stop 行为不被 UPS 输出路径改动。09A/非 Claude 证据的原版本与当前整合回归边界须明确。
4. 三个许可 reader 的真实入口拒绝缺页、total 变化、零进度，EOF 完整性不是第一前缀相同；E4 追加恢复引用同一实际 dispatch/permission_event，旧截断原件保留；E5 93,747 字节原件与 Enter 前读取一致。核对外侧9组、已知坏实现与真实续行，另选未见过长度/分页变化，不能仅采信新测试全绿。
5. 七次实际 PermissionRequest 与签字/单 Enter/action 对应，4/6 roots 与 6/11 实际 POST、所有响应200、本场目标恰一个 Esc、Stop/idle、单一 ack 和全局 seq。计数按 HTTP POST 原件，不只成功响应；历史消息中的重复 tool_use 不算新执行。
6. T-082 的 review 副本、启动边界、review_reclaimed 集成前置，与 inbox/pending/startup 共存；合并后六段运行原件、四启动边界变异及结束核对。旧 pending/startup 独立 PASS 只覆盖原候选，不能省略本次合并交叉。
7. 清理的 owner 绑定、只给 API 一次 SIGTERM、角色/target 正常 shutdown；外置逐成员字节复核、先归档后停止、停机后不读 SQLite、slots 不删除。核对已执行的 09b-a15-cleanup-01-dry-run、09b-a15-redacted-01、09b-a15-cleanup-01 与主控签字；九进程已退出，root 已删除。归档为白名单摘要，1,766 字节；不要求重跑清理。

明确给出限制的影响：I1 历史许可屏缺直接 gate total，三窗格联合视图未验、09C 未运行、真登录复核未运行、8/9/18 未在最终整合版整组重跑。标准 prepare 的 reader 新闭包 issue 20261016T120838Z 尚在；A15 专用冻结已完整，下一新场景须先处理。不将人工审批自动化写成真实用户亲手，也不把确定性目标写成真实 Codex。

现成反事实：UPS/HookTrace 原入口红态；pending-chain 旧行为；startup M5（第一轮漏检、补真实刷新时点后检出）；一页 reader/total 变化/零进度；E4 首次截断事实。新 reviewer 可在隔离临时目录做有界只读 probe，不发送输入或重建 A15。本请求没有授权 reviewer 改候选或启动新业务场景。

原 root 中带 headers/system/metadata 的 API 日志按已批准脱敏规则没有原样归档。17 POST 的逐项安全投影、停机前读回与执行主控核对已保存；root 删除后不能再从原 HTTP body 重算。审查应明确该可复核性边界，不把脱敏摘要称为完整原始请求档案。disposition 20261016T133204Z 原件的作者为执行主控，转述用户决定，只关闭 E4 范围裁定阻塞。

请返回 PASS / INCOMPLETE / NO_GO 等真实范围结论，逐条写来源、可达反例与缺口；整票关闭由执行主控按门禁完成。

## 主控 #335 追加说明：F7 回收状态与新审查前置

以上独立终审01的历史目标仍为92874fe7f，不改其报告或运行原件。该历史候选中的旧请求文字曾写“cleanup未运行/仍存进程”，实际同提交已有主控#333的正式PASS回执；后续99417a496已经修正文案，本节再次明确：**A15已回收**，九进程退出、两个API各一次SIGTERM、root删除；`09b-a15-cleanup-01-dry-run/result.json`、`09b-a15-redacted-01/result.json`、`09b-a15-cleanup-01/result.json`和签字件是唯一事实来源，外置tar1,766字节。不得按历史请求去操作或重建旧现场，不读已停机SQLite，不将cleanup PASS当作HTTP/hook验收完整。

独立终审01为整票NO_GO/INCOMPLETE，F1指出汇总投影不能独立复核17 POST/七原生许可。此限制继续有效；用户决定是否补跑09B，worker的[保留方案](09B-MINIMAL-RAW-RETENTION-01.md)不是补跑授权，也不补造旧原件。I1直接total仍缺，F5不改判。

F6已在源码`a853ad58b91f0363fcb933c50ff15ff15e2d3caf`补标准prepare的八个Python reader依赖；标准旧包58文件/闭包红态、新包66文件/归档独立导入和坏包反例均保留。业务`workbench/src`和`app`相对A15版本无变化。F4整组及T075正反例命令已准备、实际未运行；其runner只新增显式单case/mutant参数，不改变原业务方法。后续新review必须由主控明确传入新冻结候选，不能用旧92874fe7f的结论给新增harness背书。

F3按主控#335的Herdr期裁定：下一轮fresh reviewer在**主控提供的、绑定所审完整revision的隔离临时worktree**做2～5个新错误实现检查，沿T082先例；不再将“无门禁副本”当本期无法做变异的理由。先合格candidate，再每变异一处，以独立完成条件检出业务失败，保留patch/退出码/原始断言，临时worktree用后由主控按绑定回收。worker本轮不创建reviewer、不代做该项、不改已回收reviewer的旧报告。
