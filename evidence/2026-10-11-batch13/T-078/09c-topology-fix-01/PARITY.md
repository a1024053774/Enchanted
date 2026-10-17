# #364检查清单的本次落实

旧逐处清单及原行号：[SKIPPED-CHECKS](../09c-attempt-2-diag-01/SKIPPED-CHECKS.md)。旧文本副本/source tar不改写；新执行代码按以下入口走，不再以REHEARSAL名义跳过检查。

| 旧缺口 | 当前接线/反例 | 外部证据状态 |
| --- | --- | --- |
| raw_retention.check_identities两处scene豁免；REHEARSAL owner许可 | 两处分支删除；`validate_owner_receipts`始终调用，九标签恒定要求、双读恒定、全量集合无关顺序进topology。REHEARSAL现在是反例输入，非运行profile | 旧源红→候选绿；移除四门的坏变异均被拒 |
| 原root/source/claim/target/identity_receipt/daemon/target两PID/API ready/profile/argv/角色manifest与session/debug | 新9进程CScene走同一个prepare-rev2-owner producer与raw validator，原Stage A字段来自真实dispatch/进程；21项unit真实文件反例另存metadata-cases | 本地局部PASS；真实九进程全链待外跑 |
| 直接Python peer且shell_pid==leader | host真正spawn zsh，再由zsh派生peer；peer ready保存真实pid/ppid/session；processInfo两读lstart+完整argv尾+原shell父PID。manifest标Python，shell/CLI不得同PID | TS/AST检查PASS；实际job control/父链待外跑，未伪造九进程绿态 |
| Stage A/B1/P1准备省略 | 标准card_save/create/dispatch保持真入口；Stage A增加原五身份及完整readiness/result，B1调用同一read_stage_a_binding/validate_role_approval，P1通过真实--stop-before-cli核对文件冻结、role/settings、复用API原PID/argv/ready | 新链待外跑；原四回归组合的Stage A生产包检查未用手写packet冒充“已全跑”，详下段 |
| 供应商version/help、主题/安全提示/信任/用户readiness | peer不冒充Claude。真实三时点probe的B1使用同一run-09b-stage-b→run_t078_p1→claudeLaunch/controller_start，原2.1.296 --version/help与逐键/完整reader都跑；主控必须确认s13再采idle | 真实probe未跑；只有既有主控首启证据不能替本次新probe |
| 原7进程owner、手写roles少字段 | 新链用09C owner+原Stage A/两manifest/graph，真九进程。原unit/HTTP工具仍是明确spy运输层，但也补完整收据并调用同一validator/topology接口 | 本地unit/Handler通过；不是实际ps证据 |
| 直接Popen cleanup、无标准tar/签字/finish | 新CScene.cleanup先一致backup+原clock留存，同一raw.capture/archive_capture/readback/finish，独占cleanup批准与shutdown-intent；正常daemon_stop→panes.shutdown，API各一次SIGTERM。停后不读SQLite。失败保留root | 本地归档次序/坏tar/未签/源变化反例PASS；真实全链生命周期待外跑 |
| 09B startup pending每键应仍queued/无I2 | 这不是场景豁免：09C本来先双角色就绪。09B既有startup真实入口/M5与A16六键原件保持来源；本次只改确定性host进程层后，该host相关回归须外跑，不能借09C PASS代替09B | 命令见REGRESSION-COMMANDS，未跑 |
| offline/check_only/dry_run | 单元时钟、文件和运输层只用于局部拒绝/次序反例；不算真实时间/ps/窗口/Stop/回收绿态。只读模式仍保持零业务副作用，不能强迫dry-run开始按键 | 文本/AST扫描无新scene豁免；原历史版本不改 |

上轮清单把标准Stage A整套冻结源/四回归收据前置也列为“排练没有走过的路径”。这些生产包门没有REHEARSAL绕过分支，不能为了使scratch通过就删除它们：新scratch仍不宣称自己是通过四收据Stage A门的生产launch包。对应预检继续由真实生产材料入口及其现有反例验证；本轮共享B1、P1前置、owner与topology实际接线，不伪造一份历史PASS来填scratch的source差异。若主控要求scratch本身也必须通过全部四历史收据门，应先安排当前工具版本的受影响回归/明确绑定，再生成完整标准包；**本次未完成这一额外生产包等价证明，不能将此行标绿或启动第3场。**

新排练还需实际通过标准归档/finish及九进程probe。只要任一项是INCOMPLETE，第3场保持NO_GO；本次交接标记只表示探针/候选脚本可交主控实跑，不表示09C验收或“所有外部边界已证明”。
