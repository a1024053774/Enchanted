# T-090-1 修复与宿主验收交接

状态：INCOMPLETE。最小产品修复与静态检查完成；修复后的宿主绿态、整组回归及独立审查尚未完成，不宣称产品 PASS。task `T-090`、attempt `a1`、worker `s16-t090`，身份与完整启动 argv 见 `worker-launch.json`。启动参数请求 `gpt-6.1-sol`、xhigh、default tier；实际供应商 tier 未核对。

## 已核对证据

- 红态采集 PASS：`red-01.json`、`red-01.archive.json`，起点 `f08a280bdf6142443efd52d4897d2305fd68987f`。指定原方法 1 test、1 error、0 failure、0 skip；审查报告已接受，结束核对以 `review_worker_workspace_changed` 失败。worker 在开始和结束时 HEAD 相同且不等于 C。详情见 `RED-READBACK-01.md`。
- 起点反例 PASS：`boundary-baseline-01.json`、`boundary-baseline-01.archive.json`。HEAD 改动、变脏和切换到预先存在的同提交分支三条场景均被拒；共享 refs 未变，task paused、review unknown，产生问题记录并保留现场，没有 `review_reclaimed`。三条均无宿主或清理错误。
- 第二轮绿态读回：`green-regression-02.json`、`green-regression-02.archive.json`。ready 探针、focused 原用例、coop 原 8 项 PASS；recovery 原 9 项为 7 项通过、2 errors，run 18 及后续未运行。两条失败现场没有 review_lifecycle_failed；当前转入三版本诊断，见 `RECOVERY-DIAGNOSIS-01.md`，不得将该轮上调为 PASS。
- 首轮历史对照 `recovery-three-versions-01`：exec/t078 的 `150ef6516` 已运行两方法，deleted-ref error、external-X PASS。比较器误把原恢复故障注入的确认退出 -9 当作“未确认”，停止了后续版本；原结果保留。已修诊断脚本，增加真正的 main 合入前点，续采命令及证据见 `EXIT-CHECK-DIAGNOSIS-01.md`。
- 四点对照补采 PASS：`recovery-four-versions-02` 中 main-before-T082 `271ac55d82d0e20067e03e2fa4a990e55ef7b434`、main-T082 `0e6c2b833f6da64243f71d670ea45bb9116fda4d`、T090 `18dd12c29f523227d9fc6fd4c123a674f10bf7fa` 各运行同两方法，均为 run 2 / error 0 / failure 0 / skip 0，均有 review_result 与 review_reclaimed，无 review_lifecycle_failed。该结果只覆盖指定两方法，不代替完整回归。
- 第三轮完整回归 INCOMPLETE：`green-regression-03` 绑定 `e50c16f5cf6bce138c62634952cf381b2251f859`，ready 探针、focused、coop 8、recovery 9 全部通过；run/orchestration 18 为 14 通过、2 failures、2 errors、0 skip。CAS、cards、worker 边界、T-082 与变异阶段未运行。原错误及断言失败不改判，四例只读核对见 `RUN-LOAD-DIAGNOSIS-03.md`、`run-observed-03.json`。
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

当前下一步，主控在负载低时沙箱外运行同一完整组（脚本与时限未变，仅使用新 label）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-04 --archive-owned /private/tmp/t090-source-m1buaeqm
```

脚本先归档该已停止的遗留 source checkout，再运行真实子进程/文件系统 ready 发布探针；随后按顺序运行原冻结候选用例、coop 8、recovery 9、run/orchestration 18、CAS 1、cards 15；三条 worker 边界反例；T-082 七条正常及结束核对场景；四个启动变异（只读 argv、错误工作目录、联网、tmp 可写）；省掉 worker 结束检查的坏实现分别运行三条新反例，必须命中 `T090-WORKER-HEAD`、`T090-WORKER-DIRTY`、`T090-WORKER-BRANCH` 的业务失败。最后一项证明新反例能拒绝已知坏实现，宿主或导入错误不算拒绝证据。

本轮只剩 `/private/tmp/t090-source-m1buaeqm` 源码现场；存在性、文件数与字节数预检见 `archive-owned-04-plan.json`。-03 的运行夹具已经归档并清理，不列入重复归档参数；旧外置盘原件保持原样。

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

INCOMPLETE：green-regression-04 低负载完整重跑（含 CAS/cards）、三个新反例的坏实现检出、主控独立审查、门禁验收与集成，以及 living doc Verified 核对。focused、coop 8、recovery 9 已在第三轮通过；run 18 本轮仍失败，不能上调。两个恢复用例的四点证据已采集并由主控裁定为既有时序问题，该裁定不自动扩展到尚未完成复验的四条编排场景。worker 已只读对照 README 的审查段（115–119、194–197 行）：正文要求审查期间 worker 未变，与本修复一致，未发现需要改写的语义；仍由主控完成地图核对。候选完整提交号在 worker 最终交接中报告；本报告不替代显式交付、验收或集成。
