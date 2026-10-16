# T-078 冻结候选独立终审 01

STATUS: INCOMPLETE

TARGET: `92874fe7f320a9a4a47e61adacedd26fc58078c7`，`exec/t078`。

整票关闭：**NO_GO**。只读分页修复、源码冻结边界及保存回执的关联核对有下述局部 **PASS**；不能把这些结论提升为 A-15 全场独立验收或 T-078 整票通过。本轮没有确认新的、已复现的产品业务违约；确认了独立验收原件缺失，并有未完成的验收和审查义务。

2026-10-16，执行主控 #334 派发的 fresh-context、只读审查。开始和写报告前 `git rev-parse HEAD` 均为 `99417a4960f41fc90ecc8e2226bb8ac1c643ed0f`；始终用 `git show 92874fe7…:<path>`、指定 revision 的 diff 和归档字节审查，没有追随 HEAD。工作区开始干净。`workbench/src`、`workbench/app` 与业务版本 `dedd4f66bc424610183cbff2d7114e991483e1c6` 的 diff 为空；本轮执行探针所用的 `workbench/src`、`workbench/app`、`workbench/tests` 与冻结候选的 diff 也为空。

只写本报告。临时产物集中在本轮新建 `/tmp/t078-final-review-vuwby4i2`，交付前删除；可复现脚本和观测保存在本文附录。未启动 daemon、API、Electron、角色 CLI，未发业务输入、未调用模型、未操作 A-15 进程、未直接打开历史 SQLite，未请求沙箱升级，未发送收件箱条目或改 Git 状态。session 开始及写报告前 project-map status 均为 Problems 0、Stale living docs 0。

## 独立重建的验收

目标是验证两个主控在工作台中的身份、输入、异步收件箱、唤醒和紧急停止；非目标是集成、关闭票、切换日常派发、供应商模型质量和本轮新业务实跑。Ubiquitous language 沿用 `CONTEXT.md`，不把异步 queued 回执叫作业务执行完成。现有 Tracer bullet 是真实门禁 → PTY → CLI hooks → Stop 转交 → 收件箱/目标读回；确定性目标和假 API 仅证明这一编排链路。Deep modules 的判断落在门禁、Panes、relay 的实际职责边界，不因包装函数或表格存在而判通过。

预期来自以下材料，未采用 worker 的 RESULTS 表格、新 oracle 或旧 reviewer 的 PASS 作为答案：

- `.project-map/tickets/T-078-controllers-in-workbench.md:18`、`:27`：两个 Claude 主控、同任务两个主控加一个 worker 的界面、手输与注入区分、忙闲/中断后的唤醒、收件箱权限、紧急停止、8/9/18 不退化。
- `.project-map/specs/native-cli-orchestration-2026-10-10.md` 第 5、6、9 节：每会话启动记录和权限；结构化信号、提交 CR 后即忙、结束才闲、Esc 后由用户放行；追加式事实记录。第 10 节禁止提前切换日常派发。
- main 收件箱 `/Users/luckye/Documents/Code/a2a/.project-map/inbox/20261016T012505Z-ideation-answer-001.md` 的用户原话：无会话时条目照常保存、待投递对发送方可见、待投递期间不回灌反馈、上线后走既有唤醒；protocol 与预算不变。stop 条目的原 created_at 不能被上线时间替代。
- `09b-materials-01/protocol.json`：I1/I3 各 2 POST、I2/I4 各 1；E1～E5 各 2、E6 为 1；合计 ideation 4 roots/6 POST、executor 6/11；工具是实际 send、错目标、stop、ack、外人 ack、重复 ack、已 ack stop；阶段按真实 ID 关联，允许 I/E 交错。
- 实际角色卡与 `workbench/src/gates/core.ts:2261`：reviewer 还须在门禁给定的一次性候选副本里做 2～5 个错误实现的完成条件检查。这一义务本轮没有完成，见下文。

## 按审查范围分别给结论

| 范围 | 结论 | 独立核对与边界 |
| --- | --- | --- |
| controller 身份、Stop 转交和 worker 旧权限边界 | **PASS（源码与保存回执范围）** | 两份实际 input/runtime/process manifest 的 launch、preset、task/project/spec_rev、原生会话、shell/CLI PID、请求目录相符；源码的真实 leader、Stop/current prompt、worker attempt/fence 检查仍在。没有重新观察已退出进程。 |
| pending、上线首启、实际提交与原 I2 | **PASS（保存事件及状态读回范围）** | 原 stop/request 不变；六次首启读回都是 unknown、active=null、同一 queued 消息、无 delivered 历史、无 I2、business_inputs=0；提交事件 176 后才有反馈 187，原 request/entry 的反馈、I2 登记、提交各一次。HTTP 总数仍受 F1 限制。 |
| 输入、空框声明、UPS、尾换行 | **PASS（源码及已有局部回归范围）；最终真实交互 INCOMPLETE** | 控制字节按 action；新输入/composition 增加代次；空框声明绑定中断和代次；后台不清 CLI 草稿；UPS 逐字匹配登记正文；仅登记文本尾部 CR/LF 规范化。09A 与非 Claude 的旧真实运行不是最终整合版的新实跑，真实系统 IME/自然人输入也未补测。 |
| 三 reader、E4 恢复、E5 完整屏、只读源码冻结 | **PASS（本次只读修复范围）** | 58→65 文件逐字节核对；三个真实 caller 均接完整分页，新增未见长度/变化分页探针通过；E4 同一 dispatch/event、旧截断保留、完整参考及 Enter 前 capture 一致；E5 93,747 字节一致。I1 历史直接 total 仍缺。 |
| A-15 七许可、真实 HTTP POST/响应及 hook 总数 | **INCOMPLETE（整场独立证明）** | 七份签字与 action/单 CR、各阶段 Stop/错误码/ack/seq 的保存回执可关联；无法从已删除 HTTP/hook 原件独立重数 17 POST、所有 200/完整 SSE 和原生 hook 次数。不能以 final-check 的投影填补。 |
| T-082 与 pending/startup 的合并共存 | **PASS（保存的六段受控回归范围）；本次完整 reviewer 门禁 INCOMPLETE** | merge-main-3-outside-01 的四段和 -02 的两段分开核对，未把第一轮 T082 启动失败抹去。四启动边界及结束核对有受控证据；本轮没有获配门禁候选副本，也没有完成自己的新变异。 |
| A-15 cleanup | **PASS（静态流程与归档字节核对）；实际回收独立复核 INCOMPLETE** | owner 绑定、归档先行、正常 daemon_stop/shutdown、仅原 API 各一次 SIGTERM、停后仅验归档、slots 保留的代码顺序成立。冻结提交已含 #333 回收收据，不能再写成未运行；本轮没有重新操作或观察清理。归档安全性不等于验收证据充分。 |
| T-078 整票关闭 | **NO_GO** | F1、未做的 09C/联合视图/最终完整回归，以及本轮 reviewer 完成条件未齐。 |

身份与权限的具体源码：`workbench/src/panes.ts:807` 的 caller 按持久 launch、preset/project/task/spec_rev、native session、当前 prompt、Stop 转交状态和前台 leader 联合核对；`:837` 的 worker 分支仍要求 attempt。`workbench/src/daemon.ts:291` 在异步调用前后重查 worker 当前 attempt/session/fence/spec/reclaimed，controller 另查 task/project/spec；`workbench/src/relay.ts:112`、`:129` 对 controller schema 2 和 worker schema 1 分别校验，controller 的 null attempt 没有成为 worker 的宽免分支。`:99` 要求 matched Stop，`:82` 对 request ID 重放只回原结果。工具 queued/delivered=false 的回执本身没有执行门禁业务。

保存的两角色身份：ideation launch `298e0f0e-3f2c-4a76-89b5-4cd5a12053a0`、native `be13441f-b3da-48aa-8ed4-d7f70dc3d04a`、shell/CLI `65816/65817`；executor launch `3e63bc20-ec07-4237-b7ec-a8381f5a57ec`、native `85c321f3-35c7-4504-9513-73481644652a`、`93415/93416`。两者同 project `t078-p1-project`、task `t078-09b-runtime-673c98da`、spec_rev=1。真实启动参数为 Claude Code 2.1.296、haiku/low/manual、隔离 HOME/config/tmp/shell/requests/hooks/user-data、loopback 假 API；不是用户 HOME 或供应商模型质量的证据。

按冻结 protocol 重算阶段预期，再对各阶段 execute/collect/readback 核对：实际 seq 为 I1=2、E1=3、I2=4、E2=5、E3=6、I3=7、E4=8、I4=9、E5=10、E6=11；不同角色的 prompt_id 各自唯一，Stop 的 launch/native 与启动记录相符。E1 为 worker_target_required、I3 为 recipient_required、E5 为 stop_already_acknowledged；E3/E4 为同一个 ack `324b5a30-e6d0-48c0-9f07-58532e66f1b3`。目标字节计数从 E2 的 1 保持到 E6，原最终投影记为 1b。后两项是保存读回，不是本轮对现场原字节的重新读取。

## 按严重度的问题与缺口

**F1 [P1] 独立审查所需 HTTP/hook 原件已在回收时丢失，整场预算和原生事件计数不能独立复核。**

来源：`evidence/2026-10-11-batch13/T-078/cleanup-09b-a15.py:169`、`:171`；`redact-a15-scene.py:23`；审查请求 `REVIEW-REQUEST-T078-FINAL.md:18`。脚本只保留汇总投影后删除 root；final-check-04 的 sources 仍指向原 `/private/tmp/t078-2-09b-run-yp09xosq/roles/...`。我按冻结 Git tree 查得 A-15 的 `.request.bin`、requests.ndjson、responses.ndjson、http-exchanges 原件均为 0；原场根已删除。实际读取外置 tar：仅 `projection/` 与 8,015 字节的 `projection/summary.json`，压缩包为 1,766 字节，没有逐 POST meta、原响应、原始 hook stdin/finished。

可达反例/缺口：若当时另有一次失败 POST/409，或汇总漏计了一次原生 hook，现在仅凭保存的 6/11 汇总和同一采集器生成的投影，独立 reviewer 无法排除；投影与采集器相互一致不能替代原件。没有据此断言现场实际发生过额外 POST。本轮确认的是证明链断开。最小处理：若主控另有完整、可关联的外置原件，提供原路径；否则保留 A-15 历史结果为“采集器当时报告 PASS、本次独立 INCOMPLETE”，下一次经批准的无模型复跑在清理前保留可逐 POST/hook 复核的最小脱敏原记录。无需保存真实认证信息，也不能事后补造本场原件。

**F2 [P1] 整票核心验收尚未完成，不能关闭 T-078。**

来源：`.project-map/tickets/T-078-controllers-in-workbench.md:27`、`:31`；`RESULTS.md:1243`、`:1247`、`:1248`。尚缺同任务两个主控加 worker 的联合界面验收；09C 尚无真实时钟超过 120,000ms、无 ack、持续停止要求下 ideation 只中断的真实 CLI 正例；真登录复核仍未运行。受控时钟逻辑、A-14 约 180 秒批准门、确定性 codex-receiver、各单窗格许可屏分别不能替代这些条件。最小处理是按现有授权边界逐项完成并留新证据；本 reviewer 不扩大范围启动它们。

**F3 [P2] 本轮 reviewer 的 2～5 个新错误实现检查未完成。**

来源：实际角色卡 `.project-map/roles/reviewer.md` 的“必查完成条件”，及 `workbench/src/gates/core.ts:2261`。派发只给出被审 worktree、冻结 revision 和唯一报告路径，没有给本轮门禁创建的一次性候选副本。本轮不能自行把共享候选或普通临时副本当作该门禁副本，也不能启动门禁业务补建。本轮只做只读输入故障探针和历史反事实复核，未修改任何候选生产逻辑；因此 formal mutation obligation 为 INCOMPLETE，不能自签“可合并”。主控须提供门禁副本，再按同一冻结候选完成这一项。

**F4 [P2] 最终整合版的 8/9/18 整组不退化证据缺失；旧真实输入证据也不能上调为本候选的新运行。**

来源：ticket `:33`、`RESULTS.md:1245`、`:1249`。合并后六段覆盖 pending/controller、startup/M5、worker 收件箱和 T082，是有价值的交叉回归，但不等于原交付 8、恢复 9、编排 18 整组重跑。09A-3R2 和非 Claude outside-final-01 绑定各自旧版本；后续源码及局部测试没有替它们制造新的真实边界观察。最小处理是在最终业务版本上跑原整组及相关反例并保存命令/产物；真实 Esc/放行链需要何种最终复验，由主控按原检查面补齐，不以局部绿态覆盖。

**F5 [P2] I1 历史许可屏缺直接 total，完整性只能作有限推断。**

来源：`RESULTS.md:1235`、`09b-a15-reader-fix-01/historical-screen-audit.json` 的 I1 行；`workbench/src/panes.ts:180`。I1 原参考 16,322 字节，Enter 前 Electron offset 同为 16,322，缺独立保存的 gate total。按固定单页最大 65,536 字节及完整 read 的源码，它不像 E4 那样被页上限截断；这个窄结论成立。但 cursor 不是总长，事后累计 PTY 也不能还原当时 total。本报告不把这条推断升级成“已独立核对当时全屏”，也不以此宣称 I1 的 Yes 实际越权。E1/E2/E3/I3 的直接完整 gate 样本可逐字节核对；I1 不具备同等级证据。需要闭合完整审批证据时应取得原件或在新场景补证，不能改历史签字与结果。

**F6 [P2，下一新场景前处理] 标准 prepare 尚未冻结新增 Python reader 闭包。**

来源：`prepare-09b-executable.py:41`～`:44`，以及 `09b-a15-reader-fix-01/FOLLOWUP-PREPARE-CLOSURE.md`。清单加入了全部产品 TS，却没有新 `p1_output.py`；三个 Python caller 已 import 它。可达缺口是下一次标准 prepare 能生成只冻结 caller、未冻结其实际 Python reader 的 source 包。本次 A-15 专用 65 文件包完整，故不将此判成当前续行包缺陷。沿用已有 issue `20261016T120838Z`，下一 09C/新场景前补标准清单并重新冻结。

**F7 [P3] 冻结审查请求的 cleanup 状态已过时。**

来源：`REVIEW-REQUEST-T078-FINAL.md:9`、`:20`、`:24` 写“未执行/仍存进程”；同一冻结候选的 `RESULTS.md:1261`、`09b-a15-cleanup-01/result.json` 已记录 #333 回收、root_removed=true、两 API 各 SIGTERM 一次。这是当前证据可用性判断的实质差别。报告按后者处理，不运行旧请求里的现场读回；需要更新交接说明时应追加准确边界，不改旧运行原件。本轮按唯一写入限制只在本报告上报。

## 三项主控判断的独立评估

1. **#299 的 I2 时点解释：PASS（解释一致性），不是用户逐字指定时点。** 用户明确禁止 pending 阶段回灌反馈，又保持 protocol/预算；protocol I2 是 actual send execution feedback。因此 pending 零反馈、实际 delivered 后只登记原 I2，能同时满足两者。源码 `daemon.ts:32` 只在 delivery=delivered 时结算，`relay.ts:57` 同步保留反馈 intent 防重复；崩溃后未知不重放。原件的 entry `c3ab1493-5c73-4af5-947f-a0f16f19d6c7`、request `80ef9485-80df-43f3-9791-bab43261cb5b`、created_at `2026-10-16T10:51:40.728Z` 保持，实际提交 176 在反馈 187 之前，各计数一次。独立接受的是这一有条件读法；若改为 queued 就回灌、重发 send 或加一个新 root，会违背它。
2. **I1 原屏判断：仅“未显示 64 KiB 上限截断”成立，直接完整性 INCOMPLETE。** 本轮独立理由见 F5；不能沿用“原 I1 PASS”字样作为完整性证据。用户关闭相关 blocking issue 的 disposition 没有追认这条缺失证据。
3. **#331 限只读证据链的修复范围：PASS。** E4 已有真实 permission_wait，不需要重发业务或改 protocol。补齐 P1 snapshot、phase capture、Enter 前比较三个 reader 是同一个根因的必要范围；追加同一 dispatch/event 的恢复记录及新签字避免伪改旧原件。本轮对归档逐字节重算：原 58 文件仅这三 caller 改变，其余 55 不变；新增 7 文件，共 65，全部与冻结 Git 字节一致。直接 diff 中 Enter 的业务段未改，新增 check-only 在 build/window/key 前返回，未放宽屏幕变化/active binding 检查。没有产品代码、Stop/relay、protocol 或预算夹带变化。F6 是后续新包边界，不应通过扩大本次只读范围顺手修掉。

## 完成条件与反事实检查

本轮没有门禁候选副本，未新造生产代码变异，不能用以下记录抵消 F3。逐项复核的历史反事实来自实际失败断言，而不是仅看 suite exit 非零：

| 错误实现/旧行为 | 命令与保存产物 | 实际拒绝点 |
| --- | --- | --- |
| M5：将首启键收据误当 delivered | `run-startup-receipt-checks.py --suite domain` 与 `--suite entry`；`merge-main-3-outside-01/startup-domain/result.json`、`startup-entry/result.json` 中有完整 argv | m5 子运行 exit 1：首键后刷新真实 delivery，observed=delivered、expected=queued。候选 domain 15 项、entry 14 项过，并有六次 release 前刷新。不是缺模块或进程失败冒充业务红态。 |
| 只读 reader 永远取第一页 | `python3 -B workbench/tests/test_t078_output_paging.py --entry-only --one-page-mutant --ps-mode real --output <新目录>`；外侧 nine-group 的 one-page-mutant | 两个 >64KiB 的外部 payload 仅取 65,536 字节，没有 EOF 完整 capture，业务字节断言失败；不是因为身份探测失败。 |
| 恢复器删掉“旧屏必须为严格前缀”检查 | `python3 -B workbench/tests/test_t078_permission_recovery.py --omit-prefix-check --output <新目录>`；外侧 recovery-mutant | 错误前缀用例未被拒绝，因此测试 exit 1；正常实现拒绝 original_screen_not_strict_prefix。 |

外侧九组的每项 argv、expected_exit、observed_exit 已核对，包含 parent screen/phase 红、candidate screen/permission/phase 绿、one-page、prefix mutant 和 freeze scope；本轮没有重跑其中需要真实 ps 的命令。新的独立分页探针采用协议要求的连续字节/固定 total/EOF 作为预期，而不是复制生产常量；具体见附录。真实 P1 screen 与 permission check-only 入口各以 131,113 和 196,621 字节重新跑过，并拒绝中页 total 变化及 EOF total 变化。独立 helper 另用 8,191/65,521/17,411/307 的变化页长，拒绝缺页、零进度、错 launch 和字节数不符。全部 15 个检查通过。

另运行 `python3 -B workbench/tests/test_t078_phase_capture.py --output /tmp/t078-final-review-vuwby4i2/phase-capture`，exit 0，155,701/155,701 字节、到 EOF；`python3 -B workbench/tests/test_t078_permission_recovery.py --output /tmp/t078-final-review-vuwby4i2/recovery`，exit 0，good/prefix/incomplete/binding/existing-output 五项均符合预期。这些只替换输出/身份传输或使用合成文件，scene_actions=0，不能冒充真实场景运行或新的 gated mutation。

E4 原屏 65,536 字节是新 76,125 字节的严格前缀；恢复结果的 dispatch、permission_event 与原结果完全相同，screen-03 与恢复全屏逐字节相同。E4 execute-02 的 Enter 前 capture.total_bytes=76,125。E5 dispatch 原屏与签字参考逐字节相同，Enter 前 total=93,747。七份 action 的 form=action、text=CR、command_id 与按键回执 request_id 一一对应，签字命令与各自实际 permission_event.tool_input 相符。E4 的两次 check-only 失败没有算 PASS；真正 Enter 路径本身执行完整校验，此项可独立成立。

T082 合并证据：-01 首次 T082 阶段失败原件保留；修受控宿主后 -02 的 green tracer 和 readonly-argv/wrong-workspace/network-enabled/tmp-writable 四个拒绝场景均 exit 0、场景断言通过；结束核对覆盖 real_payload_report_roundtrip、external_review_boundary_invalidated、shared_refs_changed、requirements_workspace_changed、integration_before_end_check、integration_before_end_check_clean。`gates/core.ts:2189` 的 review_reclaimed 前置仍在。这里证明受控门禁回归，不证明真实供应商 reviewer 的沙箱，也不等于本 reviewer 已通过其门禁。

## 整票关闭前还缺什么

1. 处理 F1：提供可核对原件，或按批准范围补一次保留最小原始事件的无模型运行。当前 final-check-04 只能作为历史采集结果，不可签成已独立核验的 17 POST/七原生 PermissionRequest。
2. 为本轮提供门禁一次性候选副本，完成 2～5 个新错误实现检查；将独立审查结果、候选身份及审查结束检查经唯一门禁归档。本报告本身不 submit、不集成。
3. 下一新场景前补标准 prepare 的 Python reader 闭包；继续保留本次旧截断、未签许可和所有失败原件。
4. 完成 09C 的真实时间与无 ack 只中断链、三窗格同任务联合视图，以及原 PLAN-2 的真登录复核。真实 Codex、自然人亲手输入和实际系统 IME 仍未被本场自动化证明；若验收需要这些边界，必须另取对应证据，不能写成当前 PASS。
5. 最终整合版跑 8/9/18 与 T075 正反例；补足旧 09A/非 Claude 真实证据对最终候选的复验边界。
6. 所有条件齐后由执行主控按门禁完成验收、打分、集成与票据关闭；本轮没有授权提前执行这些动作。

## 附录：本轮只读分页探针与观测

下列脚本是本轮实际 `/tmp/.../probe.py` 的原文；在同一源码 checkout、确认与 TARGET 的字节一致后，放入新建 `/tmp` 目录，以 `python3 -B <该目录>/probe.py` 复现。它不调用业务场景。辅助测试内部目录用完自行删除；外层新目录由调用者结束后清理。观测 JSON 随脚本保存于本报告，临时目录不作为交付依赖。

```python
import base64,importlib.util,json,sys,subprocess
from pathlib import Path
ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
OUT=Path(__file__).resolve().parent
REV='92874fe7f320a9a4a47e61adacedd26fc58078c7'
sys.path.insert(0,str(ROOT/'workbench/tests'))
for f in ['p1_output.py','test_t078_output_paging.py','run_t078_p1.py','t078_09b_i1_permission.py','t078_09b_phase_driver.py']:
 p='workbench/tests/'+f
 assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show',REV+':'+p],cwd=ROOT)
import p1_output as reader
import test_t078_output_paging as entry
payload=(b'fresh-review-20261016\0'+bytes(range(256)))*580
payload=payload[:131113]
records=[]
for fault in ['good','gap','total-change','zero-progress','wrong-launch','byte-count','eof-change']:
 calls=[]
 def fetch(offset):
  calls.append(offset);size=[8191,65521,17411,307][(len(calls)-1)%4]
  raw=payload[offset:offset+size]
  v={'launch':'fresh','start_offset':offset,'next_offset':offset+len(raw),'total_bytes':len(payload),'data_base64':base64.b64encode(raw).decode()}
  if fault=='gap' and len(calls)==2:v['start_offset']+=1
  if fault=='total-change' and len(calls)==2:v['total_bytes']+=3
  if fault=='zero-progress' and len(calls)==2:v.update(next_offset=offset,data_base64='')
  if fault=='wrong-launch' and len(calls)==2:v['launch']='other'
  if fault=='byte-count' and len(calls)==2:v['next_offset']-=1
  if fault=='eof-change' and offset==len(payload):v['total_bytes']+=1
  return v
 error=None
 try:
  value=reader.read_complete_output(fetch,'fresh')
 except ValueError as caught:error=str(caught)
 expected={'gap':'output_offset_gap','total-change':'output_total_changed','zero-progress':'output_zero_progress','wrong-launch':'output_launch_mismatch','byte-count':'output_byte_count_mismatch','eof-change':'output_total_changed'}
 passed=(value['raw']==payload and calls[-1]==len(payload)) if fault=='good' else error==expected[fault]
 records.append({'case':'independent-helper-'+fault,'pass':passed,'error':error,'calls':calls})
for kind in ['screen','permission']:
 script=ROOT/'workbench/tests'/('run_t078_p1.py' if kind=='screen' else 't078_09b_i1_permission.py')
 for fault,length in [('good',131113),('good',196621),('total-change',131113),('eof-change',131113)]:
  label=f'{kind}-{fault}-{length}'
  result=entry.entry_case(OUT/label,script,fault,'spy',length,'FRESH-INDEPENDENT-REVIEW-20261016',False,kind)
  records.append({'case':label,'pass':result['status']=='PASS','exit_code':result['exit_code'],'observed_error':result['observed_error'],'page_calls':result['page_calls']})
(OUT/'probe-results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
assert all(x['pass'] for x in records)
```

实际命令：`python3 -B /tmp/t078-final-review-vuwby4i2/probe.py`，exit 0。原始观测：

```json
[
  {
    "case": "independent-helper-good",
    "pass": true,
    "error": null,
    "calls": [
      0,
      8191,
      73712,
      91123,
      91430,
      99621,
      131113
    ]
  },
  {
    "case": "independent-helper-gap",
    "pass": true,
    "error": "output_offset_gap",
    "calls": [
      0,
      8191
    ]
  },
  {
    "case": "independent-helper-total-change",
    "pass": true,
    "error": "output_total_changed",
    "calls": [
      0,
      8191
    ]
  },
  {
    "case": "independent-helper-zero-progress",
    "pass": true,
    "error": "output_zero_progress",
    "calls": [
      0,
      8191
    ]
  },
  {
    "case": "independent-helper-wrong-launch",
    "pass": true,
    "error": "output_launch_mismatch",
    "calls": [
      0,
      8191
    ]
  },
  {
    "case": "independent-helper-byte-count",
    "pass": true,
    "error": "output_byte_count_mismatch",
    "calls": [
      0,
      8191
    ]
  },
  {
    "case": "independent-helper-eof-change",
    "pass": true,
    "error": "output_total_changed",
    "calls": [
      0,
      8191,
      73712,
      91123,
      91430,
      99621,
      131113
    ]
  },
  {
    "case": "screen-good-131113",
    "pass": true,
    "exit_code": 0,
    "observed_error": null,
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      },
      {
        "command": "pane_output",
        "offset": 131072
      },
      {
        "command": "pane_output",
        "offset": 131113
      }
    ]
  },
  {
    "case": "screen-good-196621",
    "pass": true,
    "exit_code": 0,
    "observed_error": null,
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      },
      {
        "command": "pane_output",
        "offset": 131072
      },
      {
        "command": "pane_output",
        "offset": 196608
      },
      {
        "command": "pane_output",
        "offset": 196621
      }
    ]
  },
  {
    "case": "screen-total-change-131113",
    "pass": true,
    "exit_code": 1,
    "observed_error": "ValueError('output_total_changed')",
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      }
    ]
  },
  {
    "case": "screen-eof-change-131113",
    "pass": true,
    "exit_code": 1,
    "observed_error": "ValueError('output_total_changed')",
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      },
      {
        "command": "pane_output",
        "offset": 131072
      },
      {
        "command": "pane_output",
        "offset": 131113
      }
    ]
  },
  {
    "case": "permission-good-131113",
    "pass": true,
    "exit_code": 0,
    "observed_error": null,
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      },
      {
        "command": "pane_output",
        "offset": 131072
      },
      {
        "command": "pane_output",
        "offset": 131113
      },
      {
        "command": "pane_status"
      }
    ]
  },
  {
    "case": "permission-good-196621",
    "pass": true,
    "exit_code": 0,
    "observed_error": null,
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      },
      {
        "command": "pane_output",
        "offset": 131072
      },
      {
        "command": "pane_output",
        "offset": 196608
      },
      {
        "command": "pane_output",
        "offset": 196621
      },
      {
        "command": "pane_status"
      }
    ]
  },
  {
    "case": "permission-total-change-131113",
    "pass": true,
    "exit_code": 1,
    "observed_error": "ValueError('output_total_changed')",
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      }
    ]
  },
  {
    "case": "permission-eof-change-131113",
    "pass": true,
    "exit_code": 1,
    "observed_error": "ValueError('output_total_changed')",
    "page_calls": [
      {
        "command": "pane_output",
        "offset": 0
      },
      {
        "command": "pane_output",
        "offset": 65536
      },
      {
        "command": "pane_output",
        "offset": 131072
      },
      {
        "command": "pane_output",
        "offset": 131113
      }
    ]
  }
]
```

本轮两个辅助路径查询曾因预期文件名不符失败：旧 executable 包没有 source-files.json；E4 的 screen-03 实际位于 p1 根的 a15-executor-E4-permission-screen-03。随后改按 tar 成员表和 Git tree 的实际路径核对，得到本文结果；这两次查询错误不算产品红态，也未改候选。

外置 archive 逐成员读取结果：projection/（目录）、projection/summary.json（普通文件，8,015 字节）。没有读取、输出或保存任何全局认证内容。证据充分性问题仅在本报告上报，遵守唯一写入和不发业务消息限制。

T-078 FINAL REVIEW DONE
