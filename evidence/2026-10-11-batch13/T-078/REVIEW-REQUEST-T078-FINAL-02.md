# T-078 整票独立终审02请求（准备件，未派发）

**STATUS: INCOMPLETE（审查未执行）；证据冻结与回收前置PASS。唯一冻结候选 `022a2d2902e8a2c6233c3523b3475cc803b3bb91`。** 仓库 `/Users/luckye/Documents/Code/a2a-wt-t078`、分支exec/t078。此候选包含第3场全部输出/签字、只读原件复核、外置原件清单指针、独立tar审阅和正式回收收据，以及F1～F7处置。此后仅增加本请求的提交不改变TARGET，reviewer不得追移动HEAD。

主控#374已完成停前全量归档、逐成员字节读回、独立tar重数/凭据审阅签字、owner-bound finish；root已删。压缩包776457字节，778成员/648文件（8478871字节），644逐原件指针；POST7/1、roots4/1、三许可、中断距原stop121993ms。认证daemon_stop正常关闭角色/目标，两个API各一次SIGTERM、原PID确认缺席，停后SQLite读0。正式来源见 `09c-attempt-3-cleanup-01/result.json`、`09c-attempt-3-raw-readback-01/review.json`、`09c-c3-tar-check-01/result.json`。worker没有重跑回收或自行派审查；F3仍由执行主控安排fresh reviewer。

**审查操作边界：** 只读冻结Git原文、保存回执和外置tar；原root/PID已回收，不得查询/操作旧进程、打开已停SQLite或重新执行Stage A/B1/业务/cleanup。需要变异时仅在主控提供且绑定本TARGET的临时worktree/scratch中运行批准的无模型探针。

## 冻结与事实来源

- 当前业务src/app/acceptance逐字节等于7a6edbff8，含T082/T090、pending/startup。C3运行工具77865b044；完整材料源码8f359d364只另含收据选择/冻结元数据。A16按原09B协议完整补跑且原件已外置；09C第3场真实CLI/真时钟PASS。
- 先从ticket修订rev2、原用户答复、intent/spec/冻结09B与09C协议重建验收，不以RESULTS/本请求/worker新核对器充当答案。三窗格已移T091；真登录移T092，备好的真登录命令禁止运行；系统IME本轮未验证，明确INCOMPLETE。不是扩大本票、也不是把这三项改为PASS。
- 原终审01保持NO_GO/INCOMPLETE；逐项入口见 [FINAL-02-DISPOSITION.md](FINAL-02-DISPOSITION.md)。A15原件缺失与I1直接total缺失永远不补造；A16是用户批准的替代证据。第1场C-I1首份结果丢失、两失败场次超预算/失败均仍INCOMPLETE。
- A16外置原件 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a16-raw-01/scene.tar.gz`，逐原件pointers与仓内bundle清单可定位。已回收root不能再操作，旧准备文档只作原时点记录。C3原件也已保留于同批 `09c-attempt-3-raw-01/scene.tar.gz`，对应bundle/逐原件指针在09c-c3-closeout-materials-01；两场均已回收，不能按旧准备文档重跑。

## 必审范围

1. **真实身份与Stop入口。** controller launch/preset/project/task/spec_rev/native session/prompt_id、真实leader和请求目录；实际Stop才转交queued请求。worker attempt/session/fence/CAS/撤销边界不能被controller合法null attempt绕过。`--from executor`/`--role ideation`不能覆盖真实caller；核对实际队列回执到relay/inbox，不将queued冒充同步执行。
2. **pending→首启→delivered→原I2。** A16原stop/request/created_at不重置；无目标会话时pending对发送方可见、零反馈；上线unknown只排队，首启六键后原收据仍queued/无delivered/无I2；初始release后的turn_submitted seq176之后才delivered/原feedback187，原I2恰一次。I2时点是主控#299解释，不冒称用户逐字指定。
3. **输入与UPS。** 用户/注入/自动化来源、control action与message、新键入/composition使空框声明失效、绑定具体中断/输入代次、后台不删草稿、UPS精确登记正文与仅尾CR/LF规范化。保留09A历史版本边界，不上调成当前整合版新实跑；系统IME不算通过。
4. **完整reader与审批。** 三实际caller完整分页/EOF；缺页/total变化/零进度拒绝，新增未见过长度/变化案例。A15 E4截断/同一dispatch恢复记录与旧未签件保留。A16七次许可原屏/直接total/签字/单Enter、C3三次许可同样完整；核对原tool_use的Bash.command与同ID tool_result，不能用后验PASS填缺失前屏。
5. **09B全部协议与09C真实时钟。** 从tar逐POST重数A16 ideation6/executor11、roots4/6、许可2/5；全部SSE/queued→真实Stop/relay、错目标拒绝/一次Esc/ack/重复ack/越权ack/已ack stop拒绝、实际全局seq。C3从tar独立重数7/1、roots4/1、许可3/0；原stop创建04:03:56.934Z，早拒绝4655ms，晚实际emergency04:05:58.927Z（121993ms），actor ideation、同目标/stop、单Esc、无ack、未kill/reclaim。区分按键前121527.934ms与最终观察123102.578ms；原wall+OS CLOCK_MONOTONIC算术与差值阈值、持续停止要求、条件式单Enter及不覆盖结果。
6. **合并、回归、闭包、回收。** T082的review副本/启动边界/review_reclaimed前置与T090实际worker HEAD/branch/status边界共存；四份原回归组合明确处理02的CAS分类器INCOMPLETE，不静默忽略。标准prepare冻结p1_output及Python依赖，包05的336源码与Git原文一致。只在合法真实CLI子进程的精确规则内允许caffeinate，缺受管进程仍拒；排练原Popen由创建者reap，真实launchd场不接管waitpid，Z不算退出。归档先于停机、原件字节读回/独立tar审阅/九身份、正常daemon_stop、原API一次SIGTERM、停后SQLite0、root删除与slot保留；只有已执行收据才记cleanup PASS。

## 新独立变异完成条件（F3）

主控提供绑定最终候选的独立临时worktree及scratch，正式工作树只读。按Herdr期#335裁定，reviewer可只在该副本做 **2～5个新错误实现**，不再因无门禁副本跳过。先好候选通过，再每次只改一处；期望来自用户/spec，新增外部sentinel输入，不能改acceptance/协议/答案凑红。建议从UPS不阻断拼接、真实caller被参数覆盖、首启键误报delivered(M5)、过早紧急中断、只读reader提前返回等选择3～5项；保存各patch、确切命令、stdout/stderr/退出码和实际失败断言。worker的8个坏证据运输层反例不抵该义务。

不启动真实角色CLI/供应商模型，不读用户HOME，不操作任何既有现场，不发送业务消息/按键或再执行cleanup；若探针需受控daemon/PTY，仅主控授权的副本scratch入口，隔离、硬超时、保存失败与自行回收。读外置tar不向Git复制凭据/认证头。审查按behavioral-acceptance-review建立独立oracle，遇异常吞噬/兼容/平行路径按design-integrity-review核对，但不为看起来能过而改候选。

返回唯一报告 `independent-review-final-02.md`：冻结TARGET、总体PASS/INCOMPLETE/NO_GO、分项来源、F1～F7逐项结论、2～5变异证据、未覆盖/范围修订与可达问题。整票关闭/集成仍归执行主控门禁；本请求不自行submit、集成、push或切换日常派发。
