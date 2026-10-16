# C-I3条件式单Enter：按键前的完整核对契约

用户rev 2已授权执行主控代签09C，并允许**实际命令、stop、目标、原屏与预批准模板逐项一致时**自动按一次Enter；任一不一致停、INCOMPLETE。本文件是后续driver的执行契约，字段模板 [09C-I3-CONDITIONAL-PERMISSION](09C-I3-CONDITIONAL-PERMISSION.json) 未绑定/未签，当前不能发键。

## 预批准的形成

C-I1真实Stop产生实际stop_id/created_at与本地请求ID；target所有身份来自真实dispatch/claim而非自报。C-I2的真实拒绝反馈触发C-I3根。C-I3假API发送本次已批准的实际stop命令，Bash input只有command；Claude停在真实PermissionRequest，**尚未执行Bash**。尽早在120秒前完整取原屏、核对Bash命令/一次性Yes、真实permission_event和active prompt，执行主控把实值填进模板并签字。这里不预造permission事件/原屏，也不先发送Enter取样。

签字件须绑定：合并后实际源码/包、scene/root/role/preset/launch/session/thread、实际dispatch/global seq/prompt/tool_use/permission_event，原stop/request/created_at、target task/attempt/session/fence/spec_rev/thread/workspace/launch/shell/leader/native session/lstart，完整原屏文件/页链、精确命令argv与command、窗口身份/输入代次，以及最多一次写入。任何占位符、缺字段、旧场景、旧签字或非executor签字均不可用。

## driver唯一可达的按键路径

1. 确认当前阶段C-I3、已签批准、未出现该许可的Enter intent/不确定写入，早期场景读回通过。实际stop仍同一created_at且无ack，持续模拟停止要求未撤销，目标和角色身份未变。
2. 不发键地从offset0开始用同一严格reader读取**完整当前输出**：launch相同、offset连续、total固定、每页字节匹配、非EOF零进度拒绝，最后单独读到EOF。大于64KiB必须读所有页；不能用尾窗/首个前缀代替全屏。
3. 将全部实际字节与执行主控签过的完整原屏文件逐字相等比较，同时把当前PermissionRequest实际tool_input.command、注册tool_use command/argv、预批准模板三方逐项比较。command不加额外shell内容、不靠裁剪/模糊匹配；stop和target逐个字段比，不凭屏幕缩写认领。当前选项必须仍为一次性 `❯ 1. Yes`。
4. 当前window仍绑定该launch/thread、同active dispatch与native prompt/permission事件、输入代次无变化；序列化窗口请求前再核对身份/无新输入。读屏成功不算已按键，report_attempted不算written。
5. 真实wall age严格>120000ms，观察到stop后的monotonic已≥120100ms；预定自动开始截止130000ms、场景硬截止150000ms。若早于门槛只等待而不发键，等待分段≤20秒；到门槛后**重新执行步骤1～4**，不能复用等待前的读屏。截止已过或时钟不可信，INCOMPLETE、零新键。
6. 所有条件同真后，先持久化本次唯一Enter intent，再沿已有authenticated Electron renderer→preload→main→daemon→Panes通路发送**一个awaited CR**。不使用Digit1、默认批量Enter、持久allow；不走之前丢回执的sendInputEvent后立即关窗路径。窗口真实request_id/intent/written和对应user_inputs.form=action全部保存；不新增业务turn_submit_intent，不把CR当message。
7. 从真实第二条Messages取实际工具queued回执，等真实Stop/relay得到业务结果；再核对actual emergency actor=ideation、同target/stop、真实年龄、单Esc、无ack、原attempt仍在。只确认反馈C-I4，不重做stop。失败与多余POST按事实计预算。

任何一步不一致、缺页、源变、错误命令/身份/stop、屏幕等待期间增长、批准字段不同、原屏过期、读回/写入未知，立即记录INCOMPLETE，不发后续键、不自动改签/刷新放行、不重试已消费intent。`written`未知时仍不得第二次Enter；主控从原回执处置，不用重建UUID冒充新许可。用户撤销要求/授权同样停止。

## 合并后冻结前必须证明的反例

真实reader入口的只读一页/total变化/零进度；命令一字不同、stop或target换成另一实际对象、错native/prompt/permission_event、旧完整原屏/签字、窗口代次变化、重复执行intent、发送前异常、已写回执丢失、提前/超时/出现ack。拒绝路径必须证明零write_intent/PTY键（已发但未知的情形如实保留一次intent、不得再发），而非只检查返回字符串；正例经同Electron/window路径只有一个CR与action。user授权不免除这组证明。

当前驱动及这些真实时序证明均未实施/运行。禁止仅凭schema解析或脚本return READY宣称自动Enter可用；后续必须先完成入口红绿和一次性行为，再入合并后冻结包。
