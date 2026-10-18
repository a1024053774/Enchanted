STATUS: PASS
TARGET: 3096bef9a2f0b3b0db739a51ad662dad3f0bdd83

T-094 独立审查 01，2026-10-17。起点为 `61786370428c3ec5f894ea60acccf2695d54c2dc`；绑定 task T-094 / attempt a1 / ready_rev 1。先读取主仓库 reviewer 角色卡，再用 `git -C /Users/luckye/Documents/Code/a2a show c06a73179:.project-map/tickets/T-094-launch-worker-intermittent-start-failure.md` 读取最新 ticket。RESULTS 和 REVIEW-REQUEST 仅用于定位；预期来自该 ticket、其用户裁定和本次主控 #81 的明确要求。

本次目标是判断该冻结候选能否满足启动、失败诊断和半成功分类合同。非目标为实现、修复、调模型、操作真实 Herdr、最终门禁验收与集成。开始时、结束检查时 HEAD 都是上述 SHA，原工作区开始时干净；原受控文件未改。唯一仓库写入是本报告和同目录 `REVIEW-OUTSIDE-01.sh`。审查临时目录为 `/tmp/t094-review-01.DMBVIS`（实际路径 `/private/tmp/t094-review-01.DMBVIS`），原始测试输出保留在那里。

EVIDENCE:

1. 独立预期与 ticket Acceptance

| 检查 | 结论 | 独立核对依据 |
| --- | --- | --- |
| 真实红态及 stderr、启动记录 | PASS | 外置 red-01：5 次，3 成功、2 busy；失败 pane 为 wF:p5A、wF:p5B。原始 stderr 有 agent_pane_busy，旧启动记录只有通用退出码错误。归档中的父脚本逐字等于起点生产脚本。 |
| 同条件多次启动，或失败有可读原因 | PASS | 外置 busy-02：同一稀疏 worktree，10/10 rc 0、phase=started；每次只有一次 agent start。按原始 JSONL 重算，最终 shell 独占采样到 start 的间隔为 1570.103–1594.133ms。 |
| 半成功单独记录并拒作成功消费 | PASS | 外置 unregistered-01：真实 Codex PID 65114，名称缺失；注入 agent_name_not_found，rc 1、phase=failed、outcome=started_unregistered。复制该原始记录后调用候选 prepare-commit-msg 入口，rc 1，明确拒绝“启动记录没有成功启动”，记录和提交消息未变。 |
| 不改 Herdr server，不影响用户正在使用的 Herdr | PASS | diff 没有 Herdr server、shell 或全局配置文件；启动器和探针中没有重启 server 的调用。原件中的关闭操作逐一对应本次 split 返回的 pane，均 rc 0；本 reviewer 没有启动或关闭真实 pane。 |
| project_map.py status | PASS | session 开始和结束均 rc 0，Problems (0)、Stale living docs (0)；结束输出保存在临时目录 project-map-final.txt。 |

原件根目录为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-094/`。以下计数与字节数由直接遍历原件得到，均与冻结候选的清单一致；没有计算校验值。

| 原件目录 | 文件数 | 字节数 |
| --- | ---: | ---: |
| red-01 | 166 | 209723 |
| busy-01 | 265 | 400734 |
| busy-02 | 331 | 672466 |
| green-01 | 166 | 246600 |
| unregistered-01 | 34 | 106578 |
| revised-acceptance-01 | 268 | 864829 |

原件中保存的 launch_record 快照与各自 identity/records/launches.jsonl 最后一行逐字段一致。busy-02 的运行提交为 `acf747d948be03df6ea91bb852bdfa545e938ee0`，它的生产启动器和 probe-start.py 与冻结候选逐字一致；可将该真实边界证据用于当前产品。锚点 `b612e6f68680a5a308f8a91b6bd0e09469b86493` 到冻结候选仅有五个文档或证据文件变化。

2. 根因与证据边界

busy-01 共 8 次，6 成功、2 busy。第 1 次 wF:p5J / launch-835b22996eb8413b82176914c752ee37 在放行前最后一份快照中仅有 shell PID 81538；busy 后首次采样出现同组的 `/opt/miniconda3/bin/python /opt/miniconda3/bin/conda shell.zsh hook` 和 zsh 子进程。第 4 次 wF:p5N / launch-c279b01084c04d06a5a5fc3881c0993d 同样先只有 shell PID 82933，随后采到 `conda shell.posix activate base` 和子 shell 链。

旧代码在首次满足 shell/pgid/进程条件时立即 break。代码与原件共同支持的根因是“一次 shell 独占快照被当作稳定就绪”，并非同一快照里有子进程却被忽略。记录不支持先前“稀疏 Git 提示符就是占用者”的说法。busy 后采样存在时间差，不能证明 Herdr 拒绝瞬间的精确进程或内部检查分支。

green-01 原件为 4 成功、1 busy，未改写成全成功；其失败保留原始 Herdr stderr、error_code=agent_pane_busy、outcome=not_started。unregistered-01 是明确的故障注入：真实 pane run 启动未命名 Codex，真实 agent start 调用数为 0；它证明分类和拒收，不能冒充自然发生的丢名竞态。

3. 稳定窗口与结构检查

生产引用均指冻结候选：

- `scripts/launch-worker:134` 固定单调时钟截止点；循环不更新 deadline。每次查询使用剩余期限，147 行在查询返回后再次检查截止点，避免越过期限后放行。
- `scripts/launch-worker:151` 保留 shell PID、前台 pgid、唯一进程 PID、shell 名称的全部条件；157 行起计算合格窗口，162 行在不合格采样后清空起点；159 行要求至少 1.5 秒。采样启动间隔目标为 100ms，慢查询不堆叠。
- `scripts/launch-worker:169` 是唯一 start 调用点，不在重试循环内。轮询只观察 shell 就绪，不重复启动。没有新增 --timeout 延长 agent 启动时限。
- `scripts/launch-worker:183` 将最后成功采样完整写入 shell_foreground 和错误文本；没有成功采样时明确为 null。持续占用测试实测约 30 秒后失败，且没有 start/close。
- `scripts/launch-worker:176` 在诊断前保存原始失败命令、返回码、stdout、stderr；随后诊断不会覆盖原失败。busy 后仅一次 process-info 加一次 agent get，各有 5 秒期限，并核对 pane 身份。
- `scripts/launch-worker:212` 把诊断异常追加到 observations；注册查询失败不等同于注册缺失。`scripts/launch-worker:225` 区分活 Codex 与未注册名称，仍写 phase=failed，返回非零，不把半成功放进成功路径。入口没有 pane close 调用。

按 design-integrity-review 检查 Reachability、Ownership、Architecture、Proportion：这些分支均由真实启动命令或明确故障注入到达；启动入口拥有诊断、分类和保留 pane 的责任，处置权交主控。没有增加平行启动入口、兼容分支或通用恢复层。Deep modules：沿用已有启动入口和记录校验器，不增加转发层；Tracer bullet：沿真实启动命令到追加记录、再到 Git 钩子消费验证；Ubiquitous language：沿用 pane、启动记录、phase、outcome 的现有术语。

结构扫描器以冻结 diff 为输入；为让其定位无扩展名的脚本，只在扫描输入中补 .py，未改候选。定位到 28 行 JSONDecodeError / return None、105 行 TimeoutExpired；也手工检查了外层失败捕获和诊断捕获。前者只表示 stderr 不是可解析的结构错误码，调用者仍保留原文、使用通用错误身份并失败退出；后者保存部分输出后重新抛出。诊断捕获明确保留异常、维持失败或 unknown，没有静默成功、吞异常或隐藏重试。扫描结果保存在临时目录 originals-audit.json，扫描安静与否均未被当作通过依据。

4. 两个获准验收文件

实际 acceptance diff 只有 `test_launcher_shell_ready_e2e.py` 和 `test_herdr_traceability_e2e.py`。

shell 验收在 125 行起保留 unknown、初始化子进程、不同 pgid、shell PID 被其他程序替换的输入，改为用外部事件时间断言最终连续 1500ms，并继续要求 split → process-info → 单次 start。152 行起的环境绑定、记录身份/配置、phase、native_session、提交及尾注检查逐项 AST 相同。其余八个原方法 AST 相同；新增持续子进程超时 argv 场景增强本票要求。未放宽旧超时、挂起、错误、身份不符、失败不重试或保留 pane 断言。

版本验收的预期来自转交同次 `codex --version` 的独立回执，129 行与 prepared.cli_version 比较；146 行的 A2A-Tool 预期来自该回执。除这个预期来源外，assert_trailers 的 AST 相同：九项尾注数量及字段、项目版本、完整启动 argv、模型、强度、tier、sandbox、审批参数仍核对。其余十五个原方法 AST 相同。归档 tests-used 中两份测试逐字等于冻结候选，未使用陈旧测试背书。

第 1 条红态成立：归档旧 `617863704` 的稳定窗口场景因仅 72.493ms 就 start，在 1500ms 业务断言失败；超时场景因缺 shell_foreground 失败。后者属于缺失目标诊断字段，不是依赖或启动环境错误。

第 2 条采用变异体的依据成立：本次主控 #81 明确要求按裁定审查；归档旧实现确实执行 --version 并正确记录 0.163.0，所以修订后旧实现通过是正确的。错误版本变异仅在 cli_version 表达式附加 `-wrong-version-mutant`；真实 --version 回执仍为 0.163.0，launch 命令 rc 0，而测试在 `assertEqual(prepared["cli_version"], observed)` 因值不等失败。它证明修订断言能识别版本记录失真。归档驱动最初要求 old-version 必须红，因此保留 status=INCOMPLETE / rc=1；本审查没有回改原件或把那次总运行改称 PASS，而是按明确裁定分别评估各步骤。

5. 本 reviewer 新运行的候选检查

全部先运行好候选，再运行变异。通过 `git archive` 提取 scripts、acceptance、worker 角色卡到 /tmp；没有 git worktree、checkout、reset、stash 或候选提交。临时目录自有 Git metadata 仅用于启动记录读取冻结版本，通过只读 object alternates 引用源对象；未登记共享 worktree。Git 提交行为仅来自既有测试在 /tmp 自建的夹具仓库。

统一命令为：

```sh
python3 -B /tmp/t094-review-01.DMBVIS/run_review.py candidate
python3 -B /tmp/t094-review-01.DMBVIS/run_review.py mutants
python3 -B /tmp/t094-review-01.DMBVIS/audit_originals.py
```

| 候选检查 | 结果 | 时间与原件 |
| --- | --- | --- |
| scripts/test_launch_worker_failure.py --report …/candidate-contract.json -v | PASS，9 项，0 failure / error | 52.899s；candidate-contract/ 与 candidate-contract.json |
| acceptance/test_launcher_shell_ready_e2e.py --artifacts …/candidate-shell-artifacts | PASS，7 项，0 failure / error | 102.478s；candidate-shell/ 与对应 artifacts |
| acceptance/test_herdr_traceability_e2e.py --artifacts …/candidate-trace-artifacts | PASS，7 项，0 failure / error | 39.187s；candidate-trace/ 与对应 artifacts |

上表路径均在本审查临时目录。每条完整 argv、退出码、stdout、stderr、硬超时状态和输出目录保存于各检查的 run.json；验收夹具和命令日志也保留。Herdr 是显式替身；traceability 仅调用真实 Codex --version，不发模型提示。半成功消费另见 half-consumer/run.json，rc 1 是预期拒收。

COUNTEREXAMPLE:

三个新变异各自从冻结 SHA 的 git archive 单独提取，仅改一个位置；测试源码始终使用未改的候选测试。每个都在真实 scripts/launch-worker 子进程入口之后，由目标业务断言拒绝，均无环境错误或硬超时。

| 变异 | 唯一改动 | 命令选择与目标失败 | 结果 |
| --- | --- | --- | --- |
| skip-stable | 稳定窗口判断改为 if True | shell 验收 --launcher mutant-skip-stable/scripts/launch-worker --case test_delayed_shell_then_commit；38.576ms < 1500ms，140 行断言失败 | PASS：拒绝，测试 rc 1，1.850s |
| drop-timeout-argv | 超时错误文本序列化 last_shell_info 改为 None | shell 验收 --launcher mutant-drop-timeout-argv/scripts/launch-worker --case test_child_foreground_times_out_with_argv；随机独立 argv 不在错误文本中，192 行断言失败 | PASS：拒绝，测试 rc 1，31.368s |
| half-as-success | failure 记录 phase="failed" 改为 phase="started" | 边界测试 --launcher mutant-half-as-success/scripts/launch-worker LaunchFailure.test_process_started_without_registration_is_distinct -v；记录阶段 started 与要求 failed 不符 | PASS：拒绝，测试 rc 1，2.787s |

完整命令和日志分别在 reject-skip-stable/、reject-drop-timeout-argv/、reject-half-as-success/；各副本的 mutation.json 保存确切替换，half-as-success.json 保存启动记录。第 2 个变异仍保留结构化 shell_foreground，因此失败专门证明错误摘要中的 argv 没有被结构字段检查遮住；第 3 个变异通过记录校验并实际写出 started，随后在阶段业务断言失败。

FINDINGS:

- 未确认本次范围内需要修复的缺陷；本冻结候选的独立审查为 PASS。
- 两条修订验收有独立预期、旧实现或已知坏实现反例，其他受保护断言未见放宽。
- README 既有原生门禁入口段落过时是 REVIEW-REQUEST 已明确交主控另处置的范围外事项；本次没有修改或自行关闭它。

LIMITATIONS:

- 1500ms 是用户接受的采样稳定判据，不能证明 shell 初始化已经结束；大于窗口的空闲间隙、采样之间出现并消失的子进程仍可能导致 busy。README 已明确描述；不据此宣称永久消除竞态。
- 外置原件证明本轮真实 Herdr/CLI 边界；本次 23 项新运行使用显式 Herdr 替身，不能单独代替真实边界。真实验证可用于当前候选的依据是对应生产源码未变，不是旧结论自动继承。
- busy-02 的十次成功不证明长期可靠性、性能或成本收益；半成功真实进程加注入错误不证明自然丢名故障的发生率。
- 未做用户全局文件的历史快照比较；“不改配置/不重启”的判断基于完整候选 diff、执行路径和原始调用记录，而非对主机所有外部操作的追溯。
- 一次辅助 ps 观察被沙箱拒绝；它不参与验收判断，未升级权限、未把此拒绝当作变异红态。所有必要候选检查和变异检查已在沙箱内完成。
- REVIEW-OUTSIDE-01.sh 是可独立重放的交接脚本，语法、内嵌 Python、UTF-8 无 BOM 和 LF 已核对；本 reviewer 未执行沙箱外重放。脚本每段打印段名、输出目录和退出码，测试子进程有硬超时及进程组终止；只用 Herdr 替身和 codex --version，不启动真实 pane。没有等待该脚本回传的必需验收缺口。
- 原始新运行保存在 /tmp，未越权写外置盘归档。最终门禁验收与集成仍为 INCOMPLETE，须由执行主控通过唯一门禁完成；本报告不替代该步骤。

RULE:

- 本候选未确认重复缺陷，因此不新增治理规则或规则整改任务。

T-094 REVIEW PASS
