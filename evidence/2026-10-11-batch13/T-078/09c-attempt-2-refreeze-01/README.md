# 主控 #360：绑定已通过的协调器排练，重冻第2场

状态：**协调器排练 PASS；第2场材料准备中，场景 NOT_RUN／INCOMPLETE**。本轮不启动现场，不发键、不调模型。旧materials-03与所有失败/签字原件保留，不改写旧结论。

## 运行基线与冻结提交分开记录

主控已运行 [协调器真实链](../09c-coordinator-rehearsal-01/real-chain-outside-01/result.json)：源码 **dc15dc3f0169f8689c5cded440676031cfa48bf5**，POST7/1、roots4/1、scene_age_ms123303.453125、completion_age_ms123477.2919921875，模型0，cleanup PASS/root已删/停后SQLite读0。父进程从实际HTTP、事件、目标字节独立核对原stop、无ack、单Esc和>120/<150秒。

[重复拒绝原件](../09c-coordinator-rehearsal-01/real-chain-outside-01/flow/coordinator-duplicate-refusal/result.json) 记录：协调器完整执行1次、拒绝入口探针1次；122个原文件共1615318字节保持不变，gate事件、POST、按键及覆盖增量均0。不是第二次业务执行。

本次只更新收据校验与冻结元数据。整个 `workbench/`（含所有运行测试工具）、`acceptance/`、`scripts/` 必须逐字节等于dc15；产品src/app/acceptance也继续等于7a6edbff8。新包用 `runtime_source_revision=dc15...` 明确绑定实际运行版本。`source_revision`／`revision` 则如实记录包含本次收据校验器的完整冻结提交，不能把新元数据文件冒称为dc15原有文件。两者在新SOURCE、static与批准件中同时可见。

校验器原先仅接受旧0da排练，按新收据输入的[旧入口红态](binding-red-01.json) 拒绝；更新为仅接受本次dc15协调器PASS、完整重复拒绝收据、原时钟与独立读回后，[绿态](binding-green-01.json) PASS。原四回归收据仍完整核对：02的INCOMPLETE只来自CAS分类器，cas-03替代、lock-04补齐；不静默忽略02，不排除整个tests目录。

## 新文件与执行顺序

新包 **09c-executable-materials-04**，未签材料 **09c-attempt-2-materials-02**；Stage A输出仍为从未创建的 **09c-stage-a-02**，运行时另建全新root，不复用第一场或排练的进程/身份。`i1-prompt.txt` 与前一包逐字节相同，protocol、预算、阶段顺序、协调器逻辑均不改。

1. 主控核对/签新材料 `stage-a-approval.json`，运行 `STAGE-A-COMMAND.txt`；到READY_FOR_APPROVAL停。Stage A只起两只假API、daemon、确定性目标，不起角色。
2. 新 `ROLE-MATERIAL-COMMANDS.txt` 第一条只生成ideation P1。从其完整未签B1批准开始，dry-run→real→bind-launch；按新P1的ONBOARD-COMMANDS逐屏只发六键（ArrowUp、ArrowDown、Enter、Security notes Enter、信任ArrowDown、Enter）。B1 plan是security-notice+原文，s7实际key purpose为onboarding-notice。不符仅换-02重读，不按键。
3. 主控确认完整s13空提示符/manual、签readiness-consent，运行READINESS-COMMAND，核对0POST/0业务提交且不release。然后才生成并依次完成executor B1/首启/readiness；同一时间只做一个角色启动步骤。
4. `OWNER-BIND-COMMAND.txt` 按本场Stage A与两份实际B1 manifest核对九PID/argv/lstart、原claim/target，再 `RUNTIME-COMMAND-MATERIALS.txt` 只生成 `09c-c2-preparation-01` 的运行命令与空签字policy。
5. 在计时前独立运行C-I3唯一slot的BUILD命令，逐份签五阶段approval与 `timed-preapproval.json`；串行ARM五阶段，不发输入。
6. C-I1 INITIALIZE只初始release一次；START只dispatch，由已放行窗格自然送达，不再release。OBSERVE等待真实PermissionRequest并完整读屏cmp；PREPARE生成未签C-I1许可与独立SCREEN-CMP命令。主控逐字核对完整I_SEND_STOP命令、thread/attempt/input refs、`❯ 1. Yes`后签C-I1许可。
7. 仅运行新生成的 **TIMED-RUN-COMMAND.txt**。预先由主控给定签名，例如 `主控 #NNN T-078 09C 第2场 C-I2/C-I3 条件式单Enter预批准`，同时填入 `timed-preapproval.json.approval_ref` 与命令 `--signature-ref`，两者必须逐字相同；`approved_by=executor`。真实场不用排练的REHEARSAL ONLY签名。
8. 单入口先check/一次Enter C-I1，再无人工等待地完成C-I2 observe→完整读屏cmp→机械核对命令/argv、原stop/request/thread/目标/Yes→按policy签实际草稿→check→再次核对→单Enter→collect；随后C-I3 observe/cmp→后台条件式driver→实际template逐字段核对→签draft→fsync+独占link原子发布→等待真实>120秒单Enter与Stop/relay。最后C-I4与C-E1 collect。自动根不重新dispatch。
9. 单入口返回后、回收前运行CLOCK-ORIGIN-SAVE命令保存根级原origin到C-I1证据树；先完整脱敏归档/逐成员读回再正常停机的回收仍另批，停机后不读SQLite。

角色/PID/claim/permission/stop ID全部从本场实际回执生成，当前不伪填。完整命令中现有脚本、冻结包与输入应存在，future_inputs明确等Stage A/B1；所有输出目录全新且独占创建，不覆盖。任何不符停止后续按键，已发生动作如实留存，不重试不确定Enter。

预算保持 ideation **4 roots / 7 POST**、executor **1 / 1**、共8POST、三工具许可、模型0；C-I2按键提前截止90秒、实际stop_too_early必须<120秒且目标零增量；C-I3 wall>120000、mono≥120100，整场<150000ms；目标恰一个Esc、无ack、不kill/reclaim/归档目标作为业务停止。
