# 主控 #358：09C 第2场冻结与计时段单入口

状态：**材料冻结与静态核对 PASS；场景 NOT_RUN／INCOMPLETE**。冻结源码为 `0599c601a38bf96aebb1dde100082ca2a4093ae0`，详情见 [SOURCE](../09c-attempt-2-materials-01/SOURCE.json)。本轮只写工具、材料及运行不启动场景的局部检查，没有启动 daemon、API、角色、Electron，没有发业务输入或按键。模型预算0。不得执行已移到T092的真登录材料。

## 基线与授权

主控沙箱外 [real-chain-outside-03](../09c-fix-01/real-chain-outside-03/result.json) **PASS**，绑定 `0da09fb9f5f61f1fcd4b9c319bac800fd1ea85bc`：实际POST ideation7/executor1、roots4/1、scene_age_ms122778.90014648438，真实 wall>120000且<150000、模型0、cleanup PASS、origin原字节留存。主控另用两个独立Python3.9进程核对进程局部monotonic与系统CLOCK_MONOTONIC，此事实归主控观察，本轮未重跑。

这是确定性PTY替身的真实daemon/relay/HTTP/Electron排练，不是Claude第2场完成。新协调器复用其已验证入口，但整段协调器尚未实跑，局部验证不能替它背书。

第2场继续按rev2用户授权：执行主控代签09C阶段，只有实际命令、原stop、目标、完整原屏与预批准模板逐项一致才自动单Enter，任一不符停止后续按键。每次记录为执行主控批准的test-simulated-user自动化，不冒称用户亲手操作。签字由主控给定，本worker不签。

## 冻结与前置

`freeze-c2.py` 使用同一个 `prepare-09b-executable.py` 生成 **09c-executable-materials-03**，保留静态root，实际运行必须另建新root。材料在 **09c-attempt-2-materials-01**，Stage A输出全新 **09c-stage-a-02**；第一场所有原件/失败结论保留，不复用其HOME、root、PID、launch或session。源码以冻结当时实际提交为准，产品workbench/src、app、acceptance与7a6edbff8逐字节无变化。

Stage A预检仍逐项核对四份原回归收据，包括02的INCOMPLETE只来自CAS分类器、由cas-03替代、lock-04补齐。对已修测试工具不再假称其字节等同旧回归版本：仅显式列出的12个修复文件必须与0da09fb9f排练源码原字节相同，再绑定该完整排练收据；新增协调器、验证测试及本次生成器另列为冻结待审工具，其他产品、acceptance、脚本和测试闭包仍拒绝变化。没有排除整个tests目录，没有放宽旧收据判定。

标准source tar包含Python reader闭包、时钟/permission/phase/HTTP工具、新协调器及其生成器；冻结后逐成员与实际Git源码字节比较。具体提交与收据见材料 `SOURCE.json` / `static-check.json`，签字字段保持空。

## 主控串行执行顺序

1. 核对并签材料 `stage-a-approval.json`，运行 `STAGE-A-COMMAND.txt`，停在READY_FOR_APPROVAL。只起两只假API、daemon、确定性目标，角色CLI0。
2. `ROLE-MATERIAL-COMMANDS.txt` 第1条只生成ideation P1。使用新P1里的 `stage-b-approval.json`、`B1-COMMANDS.txt`（dry-run→real），再 `BIND-LAUNCH.txt`。逐屏按 `ONBOARD-COMMANDS.txt`：ArrowUp→ArrowDown→Enter、Security notes逐字一致才Enter、信任屏ArrowDown选Yes才Enter；不符只换-02读屏，不发键。B1 screen plan仍是security-notice加screen_text，实际s7 key purpose是onboarding-notice。
3. 主控读到完整s13空提示符/manual后签新 `readiness-consent.json`，执行 `READINESS-COMMAND.txt`，核对本角色0POST/0业务提交。此命令不release。之后才按同样步骤生成并启动executor角色；同一时刻只启动一个角色。
4. 两角色readiness完成后运行 `OWNER-BIND-COMMAND.txt`，用本场Stage A与两个实际B1 manifest绑定九进程PID/完整argv/lstart/目标；再运行 `RUNTIME-COMMAND-MATERIALS.txt`。它只写 **09c-c2-preparation-01**：完整未签 `timed-preapproval.json`、ARM与单入口命令；不启动窗口，不发输入。
5. 主控提前运行新生成的 `C-I3-BUILD-COMMAND.txt`，唯一slot含本场ideation launch；build输出目录先独占创建，不覆盖已有slot。逐份核对/签五阶段approval，以及timed-preapproval，按ARM-ALL串行arm。ARM不发输入。
6. ideation `phases/C-I1/INITIALIZE-COMMAND.txt` 仅初始release两角色一次；`START-COMMAND.txt` 只登记/派发批准提示，让已放行窗格自然送达，不再release。`OBSERVE-COMMAND.txt` 只读等待真实PermissionRequest，完整分页读屏并cmp到原件，不按键。
7. 运行C-I1 `PREPARE-PERMISSION-COMMAND.txt` 生成未签许可及独立 `SCREEN-CMP-COMMAND.txt`。主控完整读屏cmp、核对登记的I_SEND_STOP Bash.command、实际target thread/attempt/input refs与`❯ 1. Yes`后签 `permission-approval-01.json`。不能把一次性工具Enter当成新提示提交。
8. 在 `09c-c2-preparation-01/TIMED-RUN-COMMAND.txt` 中只替换 `--signature-ref` 的占位文字为预签policy的完全相同approval_ref，再执行**这一条**。它先check/Enter C-I1、结算并保存原origin，随后无人工等待地执行下述计时段。不要另跑C-I1 Enter或任何C-I2/C-I3按键命令。
9. 计时段返回后、任何回收前执行材料 `CLOCK-ORIGIN-SAVE-COMMAND.txt`，把根级原origin逐字节保存到C-I1 execute目录；失败场若origin已经生成也照做。该目录属于owner已登记的phases证据树，后续逐成员脱敏归档必须包含它。计时段本身不删除root，也不执行回收；停机/外置归档仍另批。

所有读取使用严格完整分页reader。每条命令绑定本次实际readiness/input/manifest；未来文件依赖在运行时出现前不伪造attempt或stop ID。

## 单入口的停止条件与预算

| 阶段 | 实际来源／操作 | POST / roots / 许可 |
| --- | --- | --- |
| C-I1 | 批准的窗口停止请求，真实Bash排队→Stop/relay→delivered；单入口先check再一次Enter，结算并绑定持续停止要求 | 2 / 1 / 1 |
| C-E1 | 真实stop收件箱唤醒，单一POST保持、不ack；晚中断证明后中性结尾 | 1 / 1 / 0 |
| C-I2 | 原send的实际反馈。只读observe→完整P1读屏cmp→生成许可→实际Electron NativePermission核对完整命令/argv、thread/stop/request、目标、原屏/Yes→按预批准policy签新草稿→check→再次读屏/时钟检查→一次Enter→真实settlement/collect | 2 / 1 / 1 |
| C-I3 | 实际stop_too_early反馈。observe/cmp→后台现有条件式driver→逐字段核对实际template/原屏/stop/target→签独立draft→fsync+独占link原子发布→等待driver真实>120秒单Enter和真实Stop/relay结算 | 2 / 1 / 1 |
| C-I4 | 原晚中断执行反馈，只collect中性确认 | 1 / 1 / 0 |

总计ideation **4 roots/7 POST**，executor **1/1**，合计8 POST、三次工具许可、真实模型0。POST按实际请求文件计数，不按成功响应推算；自动根只来自原反馈/收件箱，不重新派发。原created_at不改，C-I2工具按键提前截止90秒保留30秒余量，实际必须证明120秒前stop_too_early且目标零字节。C-I3保持wall>120000、mono≥120100、整场≤150000ms；目标最终恰一个Esc，不kill/reclaim，不ack。

单入口的顶层输出先mkdir独占成功才绑定结果；重复调用立即拒绝，原result逐字节不变。所有阶段输出与许可文件预先检查不存在，随后由各自真实入口独占创建。C-I2签字留未签原件，C-I3 draft与approved独立命名，发布不覆盖。任一步不符立即停止**后续**按键；已经发生的C-I1/C-I2动作按原收据留存，不能倒称整场零键。后台driver异常时只中断自有harness进程以执行finally关闭其Electron，不向角色或目标发信号；不确定Enter不重试。

新协调器静态保护 [timed-guards-01](timed-guards-01/result.json) PASS：真实排练C-I3模板正例、拼接/错thread/stop/request/seq/tool/target/Yes/截断反例，去掉验证器的坏变异暴露到按键哨兵；实际重复CLI入口在已有输出上零进程/窗口/键、原字节不变。这些是保存输入与transport spy的局部合同检查，**整段协调器实时执行尚未运行**，本包不是launch批准或09C验收PASS。

[冻结后路径与前置检查](material-check-02/result.json) 实跑PASS：322成员逐字节核对、四原回归与显式修复闭包检查通过；未签Stage A被拒，错排练收据与额外产品差异被拒。Stage A与四条后续材料入口（两角色各一条、owner、运行命令绑定）现有脚本/输入路径存在，所有输出均全新；依赖实际readiness/P1的路径明确标记future_inputs，未伪造它们存在。
