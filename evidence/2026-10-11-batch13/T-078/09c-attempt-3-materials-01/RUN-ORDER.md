# 09C 第3场执行顺序（未启动，逐阶段待批）

标准包 `09c-executable-materials-05`，完整冻结提交 **8f359d3640702b6e36bac282237250f19128495d**，实际排练运行源码 **77865b044b5a5fedeeec12e62eae1314b87bf885**。两者只差收据/冻结元数据；workbench、app、acceptance、scripts逐字节相同。本场实际root/claim/launch/session/stop尚未产生，均须取本场回执。

1. **Stage A。** 核对SOURCE、static-check与七份绑定收据。四份业务回归中的原整体INCOMPLETE仅按明示CAS替代、lock补齐处理。只签 `stage-a-approval.json` 的approved_by/approval_ref，再整文件执行 `STAGE-A-COMMAND.txt`，输出全新 `09c-stage-a-03`。READY_FOR_APPROVAL即停，核对五初始进程、真实attempt/session/fence/thread/workspace、角色CLI0/模型0。旧stage-a-approval-template仅留历史，不签；FREEZE-AFTER-PASS是已执行的一次性生成命令，不重跑。

2. **ideation B1。** 只运行 `ROLE-MATERIAL-COMMANDS.txt` 第一条，从本场readiness生成 `09c-c3-b1-ideation-p1-01`。签其stage-b-approval后，依次执行B1-COMMANDS的dry-run、real，分别停下核对；实际输出为 `09c-c3-b1-ideation-01`。执行BIND-LAUNCH，从真实结果取manifest/launch label，禁止复制旧manifest。

3. **ideation首启/readiness。** 按生成的ONBOARD-COMMANDS逐屏核对后逐键签发。完整分页reader；初读不符只换新-02重读，仍不符停。六键依次是：s1 ArrowUp到Auto、s3 ArrowDown回Dark mode、s5 Enter、s7 Security notes逐字相同后Enter、s9本场隔离repo信任屏ArrowDown到Yes、s11确认Yes后Enter。B1 plan为security-notice+原文，s7单键purpose为onboarding-notice；禁Digit1/默认信任Enter。written键不能因发键后快照失败而重发。s13完整原屏须空提示符+manual，签readiness-consent再运行READINESS-COMMAND，证明0 POST/0业务输入；采用-02时命令也绑定那份原屏。

4. **executor B1/首启/readiness。** ideation完成后才运行ROLE-MATERIAL第二条，生成 `09c-c3-b1-executor-p1-01`；同样B1→BIND-LAUNCH→六键→s13→readiness，实际B1输出新 `09c-c3-b1-executor-01`。同一时间只进行一个角色启动步骤。两角色HOME/config/tmp/shell/requests/hooks/user-data隔离，共用broker/state/repo；业务POST仍0。

5. **绑定与预批准。** 依次执行OWNER-BIND-COMMAND、RUNTIME-COMMAND-MATERIALS，从实际Stage A/两manifest核对九身份/完整argv/lstart/父链及caffeinate窄规则，生成新 `09c-c3-preparation-01`。执行该目录C-I3-BUILD-COMMAND，唯一slot含c3与实际launch。主控逐份签两个P1中C-I1/C-I2/C-I3/C-I4/C-E1的approval及preparation/timed-preapproval。ARM-ALL五条逐条串行，首败即停，均须ARMED/input_sent=false。

6. **签名参数。** 主控预给一段UTF-8签名，原样写入timed-preapproval.approval_ref，并替换TIMED-RUN-COMMAND的 `--signature-ref FILL_WITH_PREAPPROVED_SIGNATURE_REF`。例如参数形式 `--signature-ref '主控给定的完整签名文本'`，须与policy逐字相同，不能运行占位文本。用参数数组或正确shell引用，禁止变量名与全角标点拼接；签字文件临时写入后原子替换。

7. **C-I1到许可屏。** ideation的C-I1 INITIALIZE一次、START一次；前者初始放行，后者只登记批准的test-simulated-user stop请求，不再release。OBSERVE只观察，不重dispatch；再PREPARE-PERMISSION→生成的SCREEN-CMP。完整原屏与dispatch-01原屏逐字节一致，主控核对完整Bash command（不是argv）、实际refs/目标、无拼接、同一dispatch/PermissionRequest及 `❯ 1. Yes`，才签C-I1 permission-approval-01。任一不符停，零Enter，不改原件。

8. **一个计时段入口。** 只运行preparation/TIMED-RUN-COMMAND一次：C-I1 check→一次Enter→tool_result排队回执→真实Stop/relay取得原stop id/created_at；C-I2 observe→完整读屏cmp→生成许可→逐项核对command/thread/原stop/target/原屏/Yes与预批准policy→同一签名原子发布→check→一次Enter→collect；C-I3 observe→完整cmp→后台条件式驱动→模板核对→签草稿→原子发布→等驱动；最后C-I4与C-E1 collect。自动根只读真实反馈，按实际全局dispatch.seq关联，不写死#1/#2。

9. **时钟与停线。** C-I2保留age<90000ms预检，实际stop_too_early且target0；C-I3仅wall>120000ms、mono≥120100ms、全场<150000ms时一次Enter。时钟差超过原1000ms阈值仍拒绝。任一步身份/命令/原屏/模板/时钟/预算不符，整场INCOMPLETE并停止后续动作；不重复执行、不重试不确定键、不覆盖输出。180秒批准等待上限不能延长本场<150秒业务观察；本场自动阶段已事先逐项批准。

10. **原件与回收。** 计时段返回后（失败亦然），若原clock已产生，在回收前执行CLOCK-ORIGIN-SAVE-COMMAND独占保存原字节，不能重置created_at。停前保留逐POST request/response/meta（不含认证头）、hooks全原件、完整许可屏/批准/动作收据、真实Stop/relay/inbox、target字节、clock与拓扑诊断；外置tar逐成员类型/字节读回、独立重数签字后，才owner-bound认证daemon_stop→panes.shutdown→helper缺席→各原API一次SIGTERM→全部PID实际缺席→停后只验文件/归档→删root，停后SQLite读0。真实场景由launchd收养，NativeRuntime不对外来PID waitpid。slot不删。回收身份/批准须按本场实际原件生成，不填假PID或旧stop；终审前不宣告整票PASS。

## 预算与结果

| 阶段 | 角色 | roots | 实际POST | 工具许可 |
| --- | --- | ---: | ---: | ---: |
| C-I1 | ideation | 1 | 2 | 1 |
| C-I2 | ideation | 1 | 2 | 1 |
| C-I3 | ideation | 1 | 2 | 1 |
| C-I4 | ideation | 1 | 1 | 0 |
| C-E1 | executor | 1 | 1 | 0 |
| 合计 | 两角色 | 5 | 8 | 3 |

ideation4/7、executor1/1、供应商模型0，两只真实Claude Code 2.1.296角色，目标是确定性receiver，不启动真实Codex。所有失败/重试POST按实际计数，超限停。要求真实>120/<150秒后只中断、最终目标恰一个Esc、原stop无ack；各阶段没有未批准按键。
