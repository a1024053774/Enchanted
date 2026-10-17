# T-078 整票独立终审 02

STATUS: **PASS**（仅指下述 rev 2 范围的冻结候选审查；不代表已关闭 ticket、集成或切换日常派发）

TARGET: `022a2d2902e8a2c6233c3523b3475cc803b3bb91`

2026-10-17。派发身份：`launch-0f40afe0c56049ec8788d907bc703daa`。审查者没有作者及终审 01 的会话历史，没有读其聊天、调用模型、启动供应商 CLI、派子 agent、修改候选或执行门禁交付。角色卡先从 main 的 `.project-map/roles/reviewer.md` 读取；结论来自本次检查，不沿用旧 reviewer 的通过结论。

## 判定范围与独立答案

答案先从 main 的 T-078 ticket rev 2、其中逐字用户答复、TARGET 的 `intent.md`、`native-cli-orchestration-2026-10-10.md` 第 5/6/9/12 节、`controller-split-user-input-2026-10-09.md` 重建。09B 的阶段与精确命令来自冻结 `09b-materials-01/protocol.json`；09C 的预算、真时钟及条件式单 Enter 来自 rev 2 用户答复、冻结 09C 材料及其协议。RESULTS、请求、处置索引和 worker 核对器只用于定位，不是答案。

- 三窗格移至 T-091；真登录移至 T-092。本次没有运行已准备的真登录命令。这两项不计入本票通过分母。
- 系统 IME：**INCOMPLETE**，用户已决定本轮不做；合成 composition、中文文本或 xterm 事件不能代替系统输入法。
- 09B/09C 是实际 Claude 交互 CLI、loopback 假 API、确定性受管目标的证据。它们证明原生工具、hook、编排与门禁链路，不证明真实模型判断、真实 Codex 行为或正常登录 profile。
- 原工作树 HEAD 为 `43db303f621da9fdcf92a2b7c170faedf641de06`；实际相对 TARGET 涉及 RESULTS、REVIEW-CANDIDATE 和 REVIEW-REQUEST 三份说明/冻结文件，并非字面上只有请求一份。它们没有改变本次唯一 TARGET。所有候选源码和仓内证据均按 `git show` / `git cat-file` 的 TARGET 原文读取。变异副本 HEAD 也是 TARGET，结束时无受控文件差异。

使用 behavioral-acceptance-review / evidence-first-testing；结构风险按 design-integrity-review 的路由并入验收审查，前端只审本票输入/放行旅程的工程边界。没有把源码审查称为新的 Electron 实跑。

## 本次证据入口

本次 scratch：`/private/tmp/t078-final02-mut-out/`，没有把外置 tar 的正文复制进 Git。下列审查程序、输出和失败现场保留在该目录：

| 本次检查 | 入口与产物 | 结果 |
| --- | --- | --- |
| tar 原件、POST/SSE/tool_result、Stop/relay、许可 capture、目标字节、时钟 | `audit-archives.py` → `archive-audit-02.*.txt`、两份 `*-audit.json` | 退出 0 |
| 许可原屏最后许可区、协议 argv、A15 E4 恢复链 | `audit-permissions.py` → `permission-audit-03.*.txt`、`permission-audit.json` | 退出 0 |
| 实际身份、隔离路径、根提交/UPS/Stop/全局序号 | `audit-identities.py` → `identity-audit-02.*.txt`、`identity-audit.json` | 退出 0 |
| 336 源码、独立 Python 导入、原回归与回收原始退出采样 | `audit-source-regression.py` → `source-audit-02.*.txt`、`source-regression-audit.json` | 退出 0 |
| 新 sentinel 与 5 个单处错误实现 | 下节的 command JSON、patch、stdout/stderr、业务断言 | 好候选退出 0；错误实现退出 1 |
| 项目地图 | `project-map-final.txt` | 退出 0；Problems 0 / stale 0 |

重放只读核对的命令为 `python3 -B /private/tmp/t078-final02-mut-out/audit-archives.py`、`audit-permissions.py`、`audit-identities.py`（后二者使用同目录完整路径）。源码核对与变异运行器要求新输出目录；已存在的红态、数据库与原始输出不得覆盖。变异的每条实际 argv、cwd、40 秒硬超时及退出码均在对应 `*.command.json`。没有需要主控代跑的沙箱外检查，因此未生成 OUTSIDE 执行请求，也没有申请沙箱升级。

## 必审范围 1～6

### 1. 实际调用者、Stop 与 worker 边界：PASS

检查了 `panes.ts` 的 `caller()`、`daemon.ts` 的 signal/Stop 回调、`relay.ts` 的 schema 1/2 分支、请求文件绑定、`core.ts` 的 inbox/stop 入口与直接调用方。

controller 的合法 null attempt 没有替 worker 取消 attempt/session/fence/spec_rev 检查。controller 核对持久 launch 的 id/thread/task/project/preset/session/spec_rev、原生 session、当前 prompt/submission、Stop 处理中状态以及真实 leader；异步后重新检查。worker 分支仍核对当前 attempt、撤销及 fence。请求参数 `from`、`role`、`actor` 不充当实际 caller。

从两份 tar 直接关联全部 10 个业务工具调用：同 ID 的 Bash tool_use → 原生 tool_result（`queued=true`、`delivered=false`、非空 request_id）→ 对应原生 Stop → relay_received → relay_results。不是把工具返回 queued 当作同步完成。A16 的 `--from executor` 实际落库仍为 ideation，`--role ideation` 的 ack 实际仍为 executor；本次新变异另证明这种错误会被拒绝。

每场九身份及父子/前台进程组关系可从留存身份回执核对。两个角色各自的 CLI 2.1.296 argv、角色卡、session、loopback endpoint、HOME/config/tmp/requests/hooks/user-data 都绑定本场 root 与角色；没有读取用户 HOME 或复制认证。此项是审阅留存运行证据，没有查询旧 PID。

### 2. pending → 首启 → delivered → 原 I2：PASS

A16 的原 stop 为 `d48f9f7c-187e-4fcd-b125-58ec345710b6`，原 request 为 `4c754e99-a65e-450f-8381-bbb92d6114a0`，原 created_at 为 `2026-10-16T21:06:39.345Z`，没有因 executor 上线而重建。

原始投递历史是 pending、pending/role_session_missing、pending、queued、delivered。上线 unknown 及六个首启键的七份只读观察均仍 queued、无 I2，首启键不是送达证据。executor 的原 inbox dispatch 在 `turn_submitted` seq **176** 后才有 delivered；原反馈 intent 为 177、反馈提交为 186、登记为 **187**。同一原 request 的反馈与 I2 各一次，没有新 send 冒充恢复。实际全局业务序号是 I1=2、E1=3、I2=4、E2=5、E3=6、I3=7、E4=8、I4=9、E5=10、E6=11，由原 dispatch/UPS/HTTP 关联取得。

delivered 后才登记原 I2 的时点要求来源是主控 #299 的解释；没有把它写成用户逐字指定。

### 3. 输入、声明与 UPS：PASS；系统 IME 单列 INCOMPLETE

检查 Electron renderer/main → window 凭据/序号 → daemon 记录器 → Panes 写入链。新输入、二进制输入及 composition 在异步前保留输入代次；放行声明绑定窗口、launch、具体中断与输入代次，在身份等待及记录等待后重新核对。后台不会用删除 CLI 草稿来满足声明。控制键为 action，普通文本为 message，注入登记与用户输入分开；受管 worker 的人工介入来自用户输入引用。

09A-3R2 的历史源码为 `643d59bfadbf07466ee28d57f471b8ef3d10646f`。与 TARGET 比较，app/main、renderer 及声明释放的相关实现未变；后续 Panes/daemon 的许可、controller relay、首启及反馈变更按各自新证据审查。没有把 09A 原实跑上调为当前整合版的新实跑。

本次外部 sentinel `FINAL02_独立哨兵_7Zq9_ 空格\t正文` 验证精确接纳、保留内部空格/TAB、仅去尾 CR/LF，以及拼接新草稿必须 UPS block。M3 取消 block 后明确失败。完整 reader 的新长度/变化另列下节。系统 IME 未验证，仍为 INCOMPLETE。

### 4. 完整 reader 与审批：PASS

三 caller 为 `run_t078_p1.py`、`t078_09b_i1_permission.py`、`t078_09b_phase_driver.py`；均接冻结的完整 reader，源闭包在独立目录可导入。新探针用 **131081 / 196619** 字节、32771 字节页和外部 sentinel，要求全部字节与独立 EOF；total 变化（含 EOF 才变化）、缺页 offset、零进度分别由具体错误拒绝。M4 提前返回时，正常输入即因 incomplete_output_capture 失败，不是依赖导入错误。

直接从 A16 tar 核对七屏 total：I1 **15877**、I3 38646、E1 16044、E2 29103、E3 43187、E4 60872、E5 **78282**；E5 超过单页。C3 三屏 total 为 **15945 / 33352 / 47553**。每屏 capture 均有连续页与 EOF，且 raw 长度等于 next=total。Bash.command 与冻结协议展开后的 argv、同 ID tool_result、原 PermissionRequest、签字及一次 permission_control_written 相互一致。原屏最后许可区可以读到完整命令和一次性 Yes。

A15 E4 的旧截断结果、原未签 `permission-approval-01.json`、`screen-recovery-02` 和签字件 02 均保留；恢复与执行仍指向同一 dispatch。A15 I1 的旧直接 total 缺失没有被推算补齐；本次使用用户批准的新场 A16 原屏补证。

证据边界：十份 dispatch 许可 raw 均实际保留并由本次读取；Enter 前再次比较的证明包括冻结 `verify_permission_output` 实现、执行结果的 verified capture，以及部分独立 screen/cmp 原件。并非每次比较都另存一份重复 raw，不能把检查收据说成那份不存在的重复屏幕原件。

### 5. 09B 全协议与 09C 真时钟：PASS

外置 tar 只读，未解包回仓库：

| 场景 | tar 成员/文件/文件字节 | POST ideation/executor | 根 ideation/executor | 许可 ideation/executor |
| --- | --- | --- | --- | --- |
| A16 `09b-a16-raw-01/scene.tar.gz` | 929 / 767 / 7995114 | 6 / 11 | 4 / 6 | 2 / 5 |
| C3 `09c-attempt-3-raw-01/scene.tar.gz` | 778 / 648 / 8478871 | 7 / 1 | 4 / 1 | 3 / 0 |

逐 POST 读 request/response/meta：完整 SSE message_stop、长度、wire、200/complete 均相符。全部 hook 五件齐全、finished exit 0；根的 session/prompt 不重复，实际登记正文与全局序号逐根匹配。

A16 的错目标、越权 ack、已 ack 再停分别真实返回 worker_target_required、recipient_required、stop_already_acknowledged。E3/E4 指向同一 ack，只有一条 ack 与一次 wake。target 相对 baseline 只增加 `1b`；emergency actor=executor，目标/stop 不变，没有 kill/reclaim 替代中断。

C3 原 stop 为 `a649f79c-f2a1-4cd1-bcd3-f623abe6f16c`，创建于 **04:03:56.934Z**。早拒绝为 **4655ms**；实际 emergency 在 **04:05:58.927Z**，距原 stop **121993ms**。actor=ideation，仍是同一目标、同一 stop，无 ack、单 Esc。按键前观察 **121527.934ms** 与晚中断时点分开；tar 的 `files/evidence/37/timed-01/result.json` 中 **123102.578ms** 是后续完成观察，不能代替实际调用时刻。本次另由该原件重算完成观察的 wall/OS monotonic，见 scratch `final-clock-audit.json`。

本次用原 wall 与 OS CLOCK_MONOTONIC origin/sample/enter 重算差值，符合 1000ms 容差；连续采样覆盖等待，未快进数据库。检查了 Clock 使用共享 OS monotonic 的实现、150 秒期限、持续原停止要求和条件式单 Enter 的绑定。第 1/2 场失败、超预算及首场 C-I1 首份结果丢失仍 INCOMPLETE，没有被第三场覆盖。

### 6. 合并、回归、闭包与回收：PASS

TARGET 的 `workbench/src`、app、acceptance 与原回归提交 `7f45637794b5455d46125242dae90efba4863aee` 无差异，也与 A16 业务源码 `7a6edbff87df85077b3a05d38f3cfd5654cde9c1` 无差异。没有把变更后的新业务代码借旧通过结论背书。

T082 的独立 candidate/review worktree、启动边界和 review_reclaimed 前置，与 T090 在 review_requested 时冻结实际 worker HEAD/branch/clean status 的检查共存；后者没有误要求实际 worker HEAD 永远等于较早的 C。

`review-followup-regressions-02` 的 coop 8、recovery 9、run 18、CAS 1、cards 15 的 run.json 全方法执行、0 failure/error/skipped，合计 51。原顶层 **INCOMPLETE** 不改判：CAS 分类器例外明确由 `review-followup-mutant-cas-03` 补判，lock 由 04 补齐，T078 pending/startup-domain/startup-entry/worker 另有四段退出 0。原 fence/CAS/lock 坏实现有真实业务失败断言、0 errors；其原 run.json 自身仍为 INCOMPLETE，外层才把预期失败分类为成功捕获，不能把二者混称 PASS。

标准 09B prepare 的 Python 依赖显式入包；包 05 的 **336** 源文件逐字节等于 TARGET。独立目录执行 Python `-I -B` 导入 reader 与直接 caller 的依赖成功，未让宿主 checkout 补模块。

拓扑只允许实际受管角色 CLI 的直接子 caffeinate：核对 kernel executable `/usr/bin/caffeinate`、精确 `-i -t`、1～300 秒、每角色最多一个、父角色身份及两次拓扑；缺受管进程仍拒绝。排练由创建 Popen 的父进程 reap；真实 launchd 场的观察器不接管 waitpid，Z 仍为存在。

C3 cleanup 原收据是已执行、dry_run=false：归档及逐字节读回先于正常认证 daemon_stop；原 API 40009/40010 各一次 SIGTERM。直接核对保存的退出采样，最终九身份均 ps exit 1、空 stdout、无 stderr，未把 Z 当消失；停后 SQLite 读 0，root_removed=true，slot 保留。`09c-attempt-3-raw-readback-01/review.json` 的独立签字与本次 tar 重数相符。没有操作已回收现场。

## F1～F7 逐项结论

| 项 | 本次结论 | 说明 |
| --- | --- | --- |
| F1 A15 原件缺失 | PASS（替代证据）；A15 原缺口仍 INCOMPLETE | 用户批准的 A16 tar 可逐 POST/hook/relay/许可独立复核，未补造 A15 |
| F2 09C 与范围修订 | PASS（rev 2 范围） | C3 真时钟成立；三窗格 T091、真登录 T092；IME INCOMPLETE |
| F3 新独立变异 | PASS | 本次 5 个单处错误实现，先好候选通过；详见下表 |
| F4 整合回归 | PASS | 同业务源码、51 原方法、明示 02 的 CAS 分类器 INCOMPLETE 与 03/04 补证 |
| F5 I1 直接 total | PASS（A16 新场） | A16 15877 原屏/直接 total/capture/签字/单 Enter 可核；A15 旧缺失仍未知 |
| F6 reader 冻结闭包 | PASS | 标准 prepare、336 文件原文、独立导入与新长度/变化探针 |
| F7 回收状态 | PASS | 按已执行回执及原始退出采样判断；没有沿用旧准备文档的未执行状态 |

## F3：本次新错误实现与实际失败

只改 `/private/tmp/t078-final02-mut`，每次单处变更、运行后按原字节恢复；没有修改 acceptance、协议或答案。期望来自用户/spec；独立 sentinel 与边界为本次新输入。

| 变异及 patch | 错误实现 | 实际命令/输出入口 | 失败断言与退出码 |
| --- | --- | --- | --- |
| `M1-caller.patch` | inbox 的有效角色改由 args.from 覆盖 | `M1-caller.command.json`、同名 stdout/stderr、`M1-caller-data/result.json` | 正常 executor report 因伪造 from=user 被拒，预期 ok=true；退出 1 |
| `M2-early.patch` | ideation 的等待门槛改成 >=0 | `M2-early.command.json`、`M2-early-data/result.json`；另有 `candidate-M2-early.*` | 0/119999/120000ms 本应拒绝却实际中断；冻结候选测试 ideation_cannot_interrupt_early 也报 true != false；均退出 1 |
| `M3-ups.patch` | 关闭 UPS 正文不匹配 block | `M3-ups.command.json`、`M3-ups-data/result.json` | 拼接草稿期望 decision=block，实际 undefined；退出 1 |
| `M4-reader.patch` | reader 第一页后提前结束 | `M4-reader.command.json`、`M4-reader-data/result.json` | 两个正常新长度均 incomplete_output_capture，未交付完整字节/EOF；退出 1 |
| `M5-from-entry.patch` | 仅把落库 from 改成 args.from | `M5-from-entry-sentinel.*`、`M5-from-entry.*` | 外部 sentinel 与冻结 queue_is_not_delivery 均期望 executor、实际 user；退出 1 |

好候选：`baseline02-contract.command.json` 的七条业务检查、`baseline02-reader.command.json` 的六个 reader 场景以及 `candidate-domain-baseline.command.json` 的冻结领域测试均退出 0。领域测试只经 loader 将 mkdtemp 目录重定向到获准 scratch，未改原测试或断言。

失败证据保留：首次自写探针因缺 signals 子目录失败，属于装配错误；`baseline-contract.stderr.txt` 原样保留，不算产品红态。初次把 M1 跑进冻结领域测试时，先触发业务失败，后续测试又因其缺失 entry 退出 2，保留 `candidate-M1-caller.*`，不把后续装配异常算充分反例；独立 M1 探针退出 1，另用更精确的 M5 在冻结测试取得退出 1。tar/源码审阅脚本也保留各次字段假设错误与版本，最终只按上表退出 0 的检查判定，没有改原证据凑通过。

## 未覆盖、文档收尾与可达问题

在本次已审范围内，没有确认需要阻断该冻结候选的可达违约。新探针属于领域/信号/reader 的隔离行为证据；真实边界依靠本次直接读取的原 CLI/HTTP/hook/PTY/退出原件。没有新跑完整 Electron、Stage A/B1、业务、cleanup、系统 IME、真登录或真实模型能力实验；也不作可靠性、吞吐或成本收益主张。

RESULTS 最后阶段如实写三窗格转 T091、真登录转 T092、IME 未验证，以及旧失败场与终审待执行。TARGET 和 main 的 ticket Resolution 仍保留旧阶段的 INCOMPLETE 记录，未冒称当前整票已过；rev 2 的修订已在同票明确。主控闭票时仍须写入本次最终证据与两项转票、IME 限制，不能原样把旧阶段 Resolution 当作本次关闭结果。这是主控的闭票收尾，本 reviewer 没有修改 ticket 或宣布其已关闭。

未发现需另开范围外 issue 的确认问题。结束时临时候选受控源码干净，主工作树只新增本报告；没有 commit、checkout/reset/stash、push、submit、集成、全局配置或外部进程操作。

T-078 FINAL-02 REVIEW PASS
