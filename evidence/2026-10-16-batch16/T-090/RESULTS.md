# T-090-1 修复与宿主验收交接

状态：INCOMPLETE。最小产品修复与静态检查完成；修复后的宿主绿态、整组回归及独立审查尚未完成，不宣称产品 PASS。task `T-090`、attempt `a1`、worker `s16-t090`，身份与完整启动 argv 见 `worker-launch.json`。启动参数请求 `gpt-6.1-sol`、xhigh、default tier；实际供应商 tier 未核对。

## 已核对证据

- 红态采集 PASS：`red-01.json`、`red-01.archive.json`，起点 `f08a280bdf6142443efd52d4897d2305fd68987f`。指定原方法 1 test、1 error、0 failure、0 skip；审查报告已接受，结束核对以 `review_worker_workspace_changed` 失败。worker 在开始和结束时 HEAD 相同且不等于 C。详情见 `RED-READBACK-01.md`。
- 起点反例 PASS：`boundary-baseline-01.json`、`boundary-baseline-01.archive.json`。HEAD 改动、变脏和切换到预先存在的同提交分支三条场景均被拒；共享 refs 未变，task paused、review unknown，产生问题记录并保留现场，没有 `review_reclaimed`。三条均无宿主或清理错误。
- 第二轮绿态读回：`green-regression-02.json`、`green-regression-02.archive.json`。ready 探针、focused 原用例、coop 原 8 项 PASS；recovery 原 9 项为 7 项通过、2 errors，run 18 及后续未运行。两条失败现场没有 review_lifecycle_failed；当前转入三版本诊断，见 `RECOVERY-DIAGNOSIS-01.md`，不得将该轮上调为 PASS。
- 首轮历史对照 `recovery-three-versions-01`：exec/t078 的 `150ef6516` 已运行两方法，deleted-ref error、external-X PASS。比较器误把原恢复故障注入的确认退出 -9 当作“未确认”，停止了后续版本；原结果保留。已修诊断脚本，增加真正的 main 合入前点，续采命令及证据见 `EXIT-CHECK-DIAGNOSIS-01.md`。
- 四点对照补采 PASS：`recovery-four-versions-02` 中 main-before-T082 `271ac55d82d0e20067e03e2fa4a990e55ef7b434`、main-T082 `0e6c2b833f6da64243f71d670ea45bb9116fda4d`、T090 `18dd12c29f523227d9fc6fd4c123a674f10bf7fa` 各运行同两方法，均为 run 2 / error 0 / failure 0 / skip 0，均有 review_result 与 review_reclaimed，无 review_lifecycle_failed。该结果只覆盖指定两方法，不代替完整回归。
- 第三轮完整回归 INCOMPLETE：`green-regression-03` 绑定 `e50c16f5cf6bce138c62634952cf381b2251f859`，ready 探针、focused、coop 8、recovery 9 全部通过；run/orchestration 18 为 14 通过、2 failures、2 errors、0 skip。CAS、cards、worker 边界、T-082 与变异阶段未运行。原错误及断言失败不改判，四例只读核对见 `RUN-LOAD-DIAGNOSIS-03.md`、`run-observed-03.json`。
- 第四轮完整回归 INCOMPLETE：`green-regression-04` 绑定 `8c971b99d46094bc3e9cb3f0bf772de6f6ab3f4a`，ready、focused、coop 8 通过；recovery 原 9 方法中 7 方法通过，after-CAS bookkeeping 与 before-CAS same-intent 两方法各产生正文及清理 error，共 4 errors、0 failures、0 skip。后续组未运行。两条保存事件均没有 review_lifecycle_failed、review_worker_workspace_changed、review_protocol_failed 或 rejected；细节见 `REVIEW-READBACK-04.md`、`review-observed-04.json`。
- 第五轮完整回归 INCOMPLETE：`green-regression-05` 绑定 `a74adeddc5494474472560a150f5ac33ab4a502e`，ready、focused、coop 8、recovery 9 全部通过；run 18 为 16 通过、1 failure（transient-tool）、1 error（unknown-identity）、0 skip，后续组未运行。两条没有 review_lifecycle_failed 或 review_worker_workspace_changed；unknown-identity 的 identity_conflict 是原负例主动更换 workspace 触发的预期身份拒绝，其方法仍因 5 秒 prompt 超时而 error。详见 `PROCESS-LOAD-DIAGNOSIS-05.md`、`run-observed-05.json`。
- 修复前项目状态 PASS：主控补齐稀疏检出的 `.grilling` 后，`project_map.py status --root .` 为 0 problems、0 stale living docs。先前非零输出原样保留，未改地图。产品修改后，status 按 covers 规则标记 `workbench/README.md` stale，见 `project-map-candidate.txt`；该文件与地图均不在写入边界，由主控核对 Verified。

## 产品改动

只修改 `workbench/src/gates/core.ts` 的审查开始与结束 worker 边界：开始时把实际 HEAD、分支、status 写入现有 `review_requested` 追加式事件；结束时按 task、attempt、review_id 读取本次快照并比较，要求初始及结束 status 均为空。缺失快照仍拒绝；保留原有 worker 路径、登记和分支归属检查。

审查候选仍绑定冻结 C；原有审查目录干净、共享 refs 未变、副本与启动参数核对、结束核对后才写 `review_reclaimed` 和集成前置均未改。没有修改 `acceptance/`、公共契约类型、冻结协议、启动策略、测试 driver 的回收逻辑；没有 reset worker、跳过回收或伪造事件。

测试增加三条通过真实 CLI/后台/relay/Git/SQLite 的外部变更反例。原整组 runner 仅增加原方法选择参数，仍核对完整原组成员数量、继承方法身份与原断言。

## 两个恢复用例的主控裁定与非阻塞 issue

主控 #13／#7 在当前对话明确裁定（逐字）：

> 这两例是偶发、对时序/负载敏感的失败，不是 T-090 引入，也不是 T-082 引入。

本报告采用该裁定：四点原件表明同类客户端超时在合入前分支也出现，而三个 main／T-090 点的同两例均可通过，记录为既有测试的时序敏感问题。具体慢点与负载因果机制尚未定位，不据此声称稳定性已证明或所有后续超时都可忽略。旧 error 保留为 error，完整回归不跳过、不加长超时、不加重试。

已用 `scripts/inbox send --from worker:s16-t090 --to triage --kind issue` 上报 [20261016T162759Z-worker:s16-t090-issue-001](../../../.project-map/inbox/20261016T162759Z-worker:s16-t090-issue-001.md)，读回确认 `blocking:false`。正文 `ISSUE-RECOVERY-VERIFY-TIMEOUT.md` 附三处原件：`green-regression-02/recovery/`、`recovery-three-versions-01/pre-T082/recovery/`、`recovery-four-versions-02/`。此条 inbox 写入由主控本轮明确要求，未改地图、ticket、验收或全局配置。

## 第三轮编排失败与负载证据

主控 #14／#8 报告第三轮结束时 `uptime` 的负载均值为 13.81 / 30.52 / 25.81（10 核），主要为用户其他项目 sitecraft-ai 的 tsc 与 next-build。记录见 `load-report-03.json`：这是主控提供的结束时单点证据，没有补造 worker 采样或逐用例 CPU 测量。

只读核对发现：两条 prompt error 对应边界 start 晚于 cli_started 约 6.31 秒、6.86 秒，超过原 5 秒观察窗口；matching-reclaim 方法自己的 8 秒 run 在 integrating 阶段先 deadline、约 0.13 秒后才 integrated，第一次显式 reclaim 才改变现场；run-entry 方法自己的 run 在 reviewing 阶段先 deadline、之后 driver 才完成审查和显式集成，attempt 尚未 reclaimed，故未创建 attempt 保留 ref。后者不是上一方法的连带污染，也未观察到已创建 ref 丢失。

四项均有可由短时限拖慢解释的触发链，未发现独立于这些时限的额外门禁／ref 缺陷。环境负载与之相符，但不是“唯一原因已证实”或“回归通过”的证明，也未单独测量快照检查的耗时贡献。原结果保持 INCOMPLETE，下一步在低负载下执行相同完整组，不改验收、期限或重试策略。

## 第四轮审查症状核对

主控 #15／#9 提供的本地每分钟 1 分钟负载样本为 13:03=6.57、13:07=33.44、13:09=42.83、13:11=13.40，用户其他项目在运行中再次推高负载。审查延迟对应约本地 13:06～13:08，不能以启动时 6.57 把整轮称为低负载。来源与尚待主控归档的原日志状态见 `load-report-04.json`；未补造原始采样。

after-CAS 的 report 入库后，worker HEAD、分支、status 三次结束读回均与请求快照相同且干净。driver 最后一次 events 的服务端结果在 17:07:06.853Z 尚无回收事件，后台于 17:07:07.160Z 实际写入 review_reclaimed；截止读回 task=verified、review=passed。其正文 error 是 driver 期限先结束，清理的 follow-up error 是原防重复保护，不是门禁拒收。

before-CAS 的原件与初步转述不同：正文先在原 12 秒 verify 客户端等待超时，清理又在原 3 秒等待后看到 CLI 为 `<defunct>`、无法确认活进程 argv，故停止信号操作；没有 reviewer driver 的 signal，也没有结束核对。它在读回时 review=running，不补称已经回收或已证明结束核对通过。两条都仍在 setup_candidate，尚未触发 CAS 故障或 daemon 重启。

本轮没有出现要求停止的 worker 边界拒收或其他门禁拒收码；按该次负载记录保存时限现象，不将相同 driver 报错文字等同于原 T-090 缺陷复发。实际 error 与整体 INCOMPLETE 原样保留；不据此宣布完整恢复验收通过，不改代码、期限或重试。

## 第五轮与负载来源更正

主控 #16／#10 提供的摘要数值为本地 14:20=1.78、14:23=3.16、14:24=22.68、14:25=58.68；run 组实际从 14:23:02 开始，尖峰与后段方法重合。transient 自己的 run 先 deadline，后台审查／回收后再显式集成，未自动回收 worker，因此缺少 attempt ref；unknown-identity 先在 5 秒 prompt 观察窗超时，随后按该负例预设报 identity_conflict，尚无 candidate、verify 或 worker_boundary。原失败均不改判。

进程设计核对证明：18 个 daemon 生命周期不重叠，峰值 1、均退出 0；没有 18 方法并行、真实 PTY／模型群起。该组却有大量累计短进程调用：291 条 exec 为 Node 的入口、另 133 条 quality-driver Node CLI、389 条 fixture Git、815 个 daemon Git router PID、319 次 Python 边界服务调用。这些不是同时占 CPU 的数量，也不能据此认定 58 的来源。

主控已更正此前把 03／04 全归因于其他项目构建的判断。当前把 03～05 的具体责任进程统一记为未确认：保留负载数值及当时由谁转述，不把“其他项目构建”或“本测试自身”任一假设写成已测得的原因。原件没有尖峰时逐 PID CPU 快照；当前 ps 格式探针被沙箱拒绝，也不能补出历史数据。根因归因仍 INCOMPLETE，见 `run-process-design-05.json`、`load-report-05.json`。

## 宿主绿态与整组命令

从本 worktree 执行，使用新 label，不覆盖已有红态或基线：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-01
```

上述首轮命令实际在宿主准备阶段遇到 ready 发布竞态，INCOMPLETE；尚未执行业务断言。原件与摘要均保留。诊断、测试工具修复及本地确定性探针见 `READY-RACE-01.md`。产品 `daemon.ts` 未改，T-090 门禁候选行为仍为 `0bcc5ab66deaa5cae69b17672ebb2d2ae3d641c2` 中的实现。

第二轮命令（已执行；包含三个已停止临时目录的明确归档授权，这三个原目录已经归档清理，不能原样重跑）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-02 --archive-owned /private/tmp/t090-ready-feirgO --archive-owned /private/tmp/t090-ready-local-01 --archive-owned /private/tmp/s3f-lpmafq64
```

四点对照的补采命令已执行并通过（原件与旧首点分开）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/compare-recovery.py --label recovery-four-versions-02 --version main-before-T082 --version main-T082 --version T090
```

第三轮完整整组命令已执行，停在 run/orchestration；三个归档参数的原目录均已归档清理，不可原样重跑：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-03 --archive-owned /private/tmp/t090-compare-4sx2giy2 --archive-owned /private/tmp/s3f-pobyg0vj --archive-owned /private/tmp/t090-source-bsolfugr
```

第四轮命令已执行，启动负载较低但中途再次升高，停在 recovery（该归档参数的旧目录已清理，不可原样重跑）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-04 --archive-owned /private/tmp/t090-source-m1buaeqm
```

脚本先归档该已停止的遗留 source checkout，再运行真实子进程/文件系统 ready 发布探针；随后按顺序运行原冻结候选用例、coop 8、recovery 9、run/orchestration 18、CAS 1、cards 15；三条 worker 边界反例；T-082 七条正常及结束核对场景；四个启动变异（只读 argv、错误工作目录、联网、tmp 可写）；省掉 worker 结束检查的坏实现分别运行三条新反例，必须命中 `T090-WORKER-HEAD`、`T090-WORKER-DIRTY`、`T090-WORKER-BRANCH` 的业务失败。最后一项证明新反例能拒绝已知坏实现，宿主或导入错误不算拒绝证据。

该轮已归档 `/private/tmp/t090-source-m1buaeqm`，运行夹具也已归档并清理；所有旧外置盘原件保持原样。第五轮的 run 原件在本票外置盘 `green-regression-05/run/`，不覆盖任何旧结果。

当前下一步仅做三个版本完整 run 18 的串行对照，并新增只读进程采样，不先改实现或原验收：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/compare-recovery.py --suite run --sample-processes --label run-three-versions-01 --version main-before-T082 --version main-T082 --version T090
```

第三点本次固定为实际失败候选 `a74adeddc5494474472560a150f5ac33ab4a502e`（与历史 18dd 的 workbench/acceptance diff 为 0）；另两点仍为 `271ac55d8...`、`0e6c2b833...`。每版完整原 18 方法，只覆盖方法选择／证据采集 runner，版本之间串行，不改变原期限或增加测试重试。父进程约每 5 秒采样 ps/uptime，记录 PID／PPID、状态、CPU、命令名与当前测试 runner 的祖先关系；不采集参数或环境，不操作任何用户进程。真实采样须在宿主预检，若缺失保持诊断 INCOMPLETE，不编造 CPU 结论。细节及监控开销／短命进程漏采的限制见 `PROCESS-LOAD-DIAGNOSIS-05.md`。

新输出位于外置盘 `run-three-versions-01/`，完整日志及进程快照均留外置盘，仓库只存摘要与清单。它不是新一轮完整 green 回归，也不替代后续 CAS/cards、worker/T-082 与独立审查。外层整组看守 600 秒与现有 run-host 相同，不传给原方法。

新 label 的原始输出直接写 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-04/`；仓库仅生成摘要及 `.archive.json`。source checkout 与所有变异源码在内置盘 `/tmp/t090-source-*`，完整执行成功后连同运行夹具复制到外置盘，核对文件数、字节数后才清理原件；失败则保留 source checkout 并报告路径。已完成但失败的测试夹具在拒绝退出码之前归档，不改其失败结果；没有自动重试或延长原测试期限。外置盘缺失即报错。借用既有依赖，不安装、不构建、不链接构建输出。真实模型回合为 0，PTY/原生进程观测是受控输入，不据此声称真实 Codex 沙箱边界已复验。

红态可复制保留的起点源码快照到内置盘复现（输出目录必须另取新名，复制来源保持只读）：

```sh
T090_REPLAY_ROOT="$(mktemp -d /tmp/t090-red-replay-XXXXXX)"
cp -R /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/red-01/source "$T090_REPLAY_ROOT/source"
python3 -B "$T090_REPLAY_ROOT/source/workbench/tests/run_s3_rebased_regression.py" --suite coop --case test_submit_requires_clean_head_and_cannot_replace_frozen_candidate --revision f08a280bdf6142443efd52d4897d2305fd68987f --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/red-replay-01
```

重放旧 runner 的临时夹具与内置盘源码副本仍需按 T-088 归档，不能因重放失败覆盖原件。

## 当前检查及限制

PASS：`node --check workbench/src/gates/core.ts`；Python 文件 AST 解析；改动的 TypeScript 测试文件语法检查；ready 发布步骤的真实文件系统/子进程确定性探针及已知坏实现检出；`git diff --check`；UTF-8 回读；修改边界核对。未跑构建（本任务不需要构建，也没有安装依赖）。

INCOMPLETE：run 18 三版本对照与实际进程负载归因、完整回归（含 CAS/cards、worker/T-082 及变异）、主控独立审查、门禁验收与集成，以及 living doc Verified 核对。第五轮 ready、focused、coop 8、recovery 9 通过，但 run 18 仍失败，不能借旧通过上调本轮结果；不能将旧恢复用例的主控裁定自动扩展到新的编排失败。worker 已只读对照 README 的审查段（115–119、194–197 行）：正文要求审查期间 worker 未变，与本修复一致，未发现需要改写的语义；仍由主控完成地图核对。候选完整提交号在 worker 最终交接中报告；本报告不替代显式交付、验收或集成。
