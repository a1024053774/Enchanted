# RUN-OUTSIDE-05 四场诊断（实施前）

状态 INCOMPLETE，诊断基于候选 7c58ba11c5dad6c2fef79e0b19ed8da0abd6145e。先读四场 JSON、完整日志、各夹具 state.sqlite3 的任务/门禁/编排事件及变异源码，保留现场不改写。

| 场景 | 观察 | 根因假设及分类 | 实施前验证 |
| --- | --- | --- | --- |
| t127-no-untrusted | /private/tmp/t127-jtngazz6；verify 返回 review_launch_boundary，worker 交付完成，review 未进入 running（CLI 已创建）。矩阵 proof 实际为 OperationalError: unable to open database file | 正确的提前启动参数拒绝；证据读取器失败，不是原生变异没被抓住。数据库 header 为 WAL 模式，已没有 -wal，普通 mode=ro 在原路径和单文件副本均失败，immutable 静态读取成功。更底层 SQLite/文件系统为何打不开 sidecar 尚未证明，不推成产品权限缺陷 | 静态读取原始 review_requested、review_lifecycle_failed 的真实输入，原 helper 原拒绝成立，仅补回候选 untrusted 后同门禁 PASS；控制输入/输出位于 /private/tmp/t141-trust-replay06-97em5e90/ |
| t127-trusted-copy | /private/tmp/t127-ee16kyjo；verify 同样被 review_launch_boundary 提前拒，proof 为同一个 SQLite 打开错误 | 与上一场同类，实际是 trusted 参数被正确拒；不能凭通用错误码宣称通过 | 原 helper 检查实际参数确为候选 trusted；仅将其恢复 untrusted 后同门禁 PASS；数据同上目录 |
| t127-folder-runtime-unbound | /private/tmp/t127-xsm6h8bg；错误的 reviewer 原生 cwd 为审查 Git worktree，记录中的工作目录仍是 candidate copy；scanner 被变异后绑定该会话，但从 UserPromptSubmit 到 Stop 共 10 次 hook 被 question_origin_unverified 拒绝；没有 review_submit，review 仍 running | 原测试预期到达 review_native_session_folder，但更早的 hook 来源检查正确拒绝，故等待业务终态超时。reviewer-folder-unbound 只改了扫描匹配与 rootFile，没有伪造内存 record.worktree，属于故障注入不完整；不是候选放过错误目录 | validateHookEnvelope 明确要求 value.cwd == pane.record.worktree。36fc44914 至本候选 workbench/src 无变化；与 c113e7120 的 questions.ts、paneRecovery.ts 也无变化。旧 test 注释已记下 question_origin_unverified 会更早拒绝；无需先跑一个必被旧 worker 断言截断的基线来猜根因 |
| t127-gate-folder-unchecked | /private/tmp/t127-45ht7653；与上一场相同的实际 cwd、10 次来源拒绝与 Stop 拒绝，无 review_submit；只是后层 native-session-folder guard 被关掉 | 后层 guard 变异被更早的正确来源检查遮蔽；单纯超时不能证明关闭后层检查这一变异被行为断言抓住，也不能把它改计 PASS | 原生两场都未到被删除的 guard。必须使隔离源码的 runtime 故障注入在扫描与 hook 来源两处一致，才能分别证明后层 guard 正例与删除该 guard 的反例 |

最小改动方向：

1. 证据读取限定为已结束夹具、无非空 WAL 的静态数据库，直接 immutable 读取，不做失败后换读法的 fallback；仍要求原 helper 的实际错误参数校验、原记录拒绝、只修 trust 后通过。缺输入、WAL 未落盘或其他边界错误仍 INCOMPLETE。
2. 不把两个目录超时改成成功，不改 question_origin_unverified 的生产检查，也不改原来的 review_native_session_folder 行为断言。仅补齐 reviewer-folder-unbound 这个隔离源码变异：在持久 launch 记录保存之后，把 pane 内存中的 worktree 来源字段伪造为 review workspace；既有两条 scanner 伪造保留。持久 launch、readThread 的 attempt workspace 和候选期望仍指 candidate，因而后层必须依据真实 session_meta.cwd 拒绝。关闭后层 guard 时原行为断言应失败。这个效果还需真实 RUN-OUTSIDE-06 验证，不能用本地语法或回放当作已走通。
3. RUN-OUTSIDE-06 只运行上述四场及 t127 绿态。若仍有更早正确拒绝，继续记录真实层级并保留 INCOMPLETE，不压低断言或增大等待期限。

实施前补充的静态发现：`daemon.ts` 在门禁真实拒绝 reviewer receipt 后调用 `failReviewProtocol`，后者把 task 设为 paused、review 设为 unknown；当前“审查结束”的等待谓词没有接纳 paused。补齐故障注入后若后层门禁确实拒绝，仍可能被这项等待缺口挡住。拟只把 paused 纳入等待终态，仍执行原来“review 未 passed 且出现指定 review_native_session_folder 拒绝”的断言，正常绿态仍必须通过 review_passed；不改等待时长，不把暂停算作正常审查通过。
