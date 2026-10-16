# A-16 executor readiness、I2/E1 与后续阶段（主控 #348）

**本轮只写材料，没有执行 readiness、arm、release、阶段START、读屏、Enter或读回。** 当前I1已由主控完成，executor首启六键后的queued检查全PASS；其他阶段仍待各自签字。原件按rev2保留，模型0，冻结源码/reader/观察器不改。

## 紧接首启的四步

1. 主控运行 executor P1 的 `READINESS-CONFIRM-COMMAND.txt`：先以新输出 `onboarding/readiness-queued-readback.json` 刷新原stop，仍需queued/无delivered/无I2、六键/零业务输入；再核对完整s13的8893字节、capture/EOF、空提示符/manual与0 POST后排他写readiness。脚本只做收据刷新和确认，不arm/release/发键。
2. 签 ideation `phases/I2/approval.json`，执行其 `ARM-COMMAND.txt`。只登记原I2应答的批准，预期ARMED，不产生输入、POST或新派发；不是重新send。
3. 签 executor `phases/E1/approval.json`，执行其 `INITIAL-RELEASE-COMMAND.txt`。只release首启时已排队的原stop，观察实际inbox派发和全局seq；到 **READY_FOR_PERMISSION** 即停，不按Enter。
4. 在E1保持许可屏时，执行本目录 `DELIVERY-I2-READBACK-COMMAND.txt`：先复用原oracle collect I2，再只读核对原request/entry/created_at不变、实际executor `turn_submitted` 后才delivered/反馈、原I2 feedback/登记/提交恰各一次。预期当前POST为ideation3（I1两条＋I2一条）、executor1（E1首条）。输出新 `delivery-i2-readback-01.json`；不能重复arm/release或拿summary代替原收据。

I2时点沿主控#299的解释：pending阶段零反馈，原有I2在实际delivered后登记；这是主控对用户原话的解释，曾经独立审查认可，不冒称用户逐字指定了时点。protocol和预算不变。

## 各阶段分别执行

`stages.json`列出绝对目录与命令索引。所有phase approval均留空；必须逐阶段核对、签字，不批量执行。E1之后采用A15实际走通的因果顺序：

**E1 → E2 → E3 → E4 START到许可屏 → I3 START/许可/结算 → I4 → E4许可/结算 → E5 → E6。**

E3真实ack会同时唤醒E4与I3，两者首次POST/全局seq可交错。应及时分别签两个阶段并START，不假设哪个全局编号先出现；每个已发POST等待阶段批准最多180秒，任何超时/409即停，不能重发续等。E4可留在其许可屏等待I3/I4完成。

| 阶段 | 根的实际来源 | POST | 许可屏 | 主要读回 |
|---|---|---:|---:|---|
| I1（已完成） | 批准的模拟用户停止请求 | 2 | 1 | 原stop pending、feedback0、target0 |
| I2 | 原I1 send的delivered反馈 | 1 | 0 | 原request/entry，投递后恰一次 |
| E1 | 原stop inbox wake，初始release | 2 | 1 | wrong-target返回worker_target_required，目标无Esc |
| E2 | E1真实拒绝反馈 | 2 | 1 | 实际executor只中断原target，恰一个Esc |
| E3 | E2真实执行反馈 | 2 | 1 | 一条executor ack，reply_to原stop、一次wake |
| E4 | E3真实ack执行反馈 | 2 | 1 | 同一ack幂等，不重复wake/Esc |
| I3 | E3真实ack的inbox wake | 2 | 1 | 越权ack返回recipient_required |
| I4 | I3真实拒绝反馈 | 1 | 0 | 中性确认、Stop/idle、目标仍一个Esc |
| E5 | E4真实幂等反馈 | 2 | 1 | stop_already_acknowledged，不重复Esc |
| E6 | E5真实拒绝反馈 | 1 | 0 | 中性确认、Stop/idle、目标仍一个Esc |

有工具的每阶段独立流程（E1从已批准initial release开始，其余用START）：

1. 签phase `approval.json`，运行 `START-COMMAND.txt`，到READY_FOR_PERMISSION停。参数名dispatch仍沿现有入口，只有I1会真的pane_dispatch；后续阶段只登记应答批准并观察真实feedback/inbox wake。
2. `PERMISSION-SCREEN-COMMANDS.txt` 每次只取一组：完整分页读取后，逐字节cmp fresh screen.bin与该实际dispatch-01原屏。命令原文、stop/target引用、光标❯ 1. Yes均须一致；-02仅备用只读，不发键，仍不一致则停。
3. `PERMISSION-APPROVAL-COMMAND.txt` 从该阶段真实dispatch/permission事件与原屏生成空签字批准。未来ID尚未发生，此时不伪填permission文件；主控核对后再签。
4. `PERMISSION-CHECK-COMMAND.txt` 用新permission-check-01完整校验屏幕/active/签字，不build/开窗/按键；通过后单独运行 `PERMISSION-ENTER-COMMAND.txt`，新execute-02、一次awaited Electron Enter，记control action，不新增业务根。slot由stage、该output标签、实际角色launch共同确定，不覆盖旧slot。
5. Enter/业务结算通过后执行 `READBACK-COMMAND.txt`，新readback-03只读collect真实HTTP/UPS/Stop/relay/inbox/目标字节，不重复工具动作。每阶段实际dispatch.id/seq均从该阶段真实bound正文及原收据核对，不能拿阶段号当全局seq。

无工具的I4/E6仅签phase、START到PASS，再READBACK，没有许可/Enter。任何未知写入、正文/身份/命令/原屏不符、非预期HTTP、额外根/POST、目标字节或收据不符，都记INCOMPLETE停止、不自动重试/重按。

## 预算和原件

ideation4根/6 POST＝I1(2)+I2(1)+I3(2)+I4(1)；executor6根/11 POST＝E1～E5各2＋E6(1)，合计10根/17 POST、七次工具许可，供应商模型0。当前已用I1一根/两POST/一次许可；后续预期九根/十五POST/六次许可。POST按实际HTTP请求数计算，包括已发送但还在等批准的请求，不按完成响应估算。

所有screen、dispatch许可截图、Enter前核对均用同一个已冻结完整reader，严格total/范围/EOF；本场不引入等待稳定或容忍差异的工具改动。executor s11发键后采集被拒的原result保留INCOMPLETE，按键有written收据、独立s13完整，不重按。

两角色逐POST request/response/meta与hook stdin/started/finished/stdout/stderr均保留在活root；本轮没有归档、删原件或停机。回收前先用rev2工具结构脱敏、外置tar逐成员字节读回、从tar独立重数并留每原件archive指针，然后才单签finish；停机后不读SQLite。生成owner需两份实际B1 manifest，主包BIND-OWNER命令已具备，但也未在本轮执行。
