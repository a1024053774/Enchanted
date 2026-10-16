# T-090 独立审查 01

STATUS: INCOMPLETE

TARGET: `exec/t090`，`ca6ac9aa3d998fd376dc4693bb06a6f05cd77f46`。

2026-10-16，fresh-context reviewer。开始时及写报告前的 `git rev-parse HEAD` 均为上述 revision，分支为 `exec/t090`。未改共享候选、测试、地图或全局配置；未调用模型 API，未请求沙箱升级。本报告是唯一交付写入。

在本次检查范围内，未发现可达的产品逻辑缺陷。产品修复保持了 T-082 的其余边界，已有各套件的分次通过记录可以支持修复的功能回归结论。但是，本 reviewer 的基线及三个独立变异都在夹具启动阶段被 `/bin/ps` 权限拦住，不能证明独立变异已被业务断言捕获；`project_map.py status` 仍有一项 stale living doc。因此不能给独立审查 PASS，也不能关闭 T-090。

## EVIDENCE：独立重建的验收

验收来源是 T-090 票第 18–36 行、T-082 票原文和受保护的 `acceptance/test_coop_e2e.py:505–536`，未以 worker 的 RESULTS 或诊断报告充当答案。

- 冻结 C 后，worker 可以在审查开始前提交 later_bad；再次 submit 必须拒绝替换 C，verify 必须验证并保留 C。
- 审查开始时保存 worker 实际 HEAD、分支、干净状态；结束时要求这些状态未变。开始时脏或 detached 不能成为合法基线。
- 候选号不变、审查目录保持 detached 于 C 且干净、共享 refs 不变；审查副本、启动边界和结束核对后才能集成的前置不能放松。
- 异常必须使审查失效、暂停并上报，保留现场；不能伪造 `review_reclaimed` 或把 worker reset 回 C。
- 红态、交付 8、恢复 9、编排 18、T-082 启动与结束边界及四个启动变异均须有证据；独立 reviewer 须自己完成少量有效变异检查；地图须无 stale 项。

受保护验收及产品路径：`git diff f08a280bdf6142443efd52d4897d2305fd68987f ca6ac9aa3d998fd376dc4693bb06a6f05cd77f46 -- acceptance` 为空，产品改动仅为 `workbench/src/gates/core.ts` 的 21 行 diff。其余测试工具变更是 ready JSON 原子发布与选择原验收方法；没有改原业务断言、延长期限、跳过回收或写入伪造事件。

## EVIDENCE：产品边界核对

| 检查 | 冻结代码与判断 |
| --- | --- |
| 只放宽 worker HEAD 与 C 的相等要求 | `core.ts:2220–2224` 获取 worker 实际状态，`:2232` 保存进 `review_requested`，`:2344–2351` 从该请求读回比较。没有改冻结候选的交付检查。 |
| 候选绑定 | `core.ts:3444–3449` 仍要求报告候选号同时等于 task 与 review 的候选号，并绑定 verification；`:2334` 仍要求审查 worktree HEAD 为 C；`:2164` 集成前再次绑定 C。worker 快照没有用来替换 C。 |
| 快照缺失 | `core.ts:2346–2347` 中缺事件、缺 `worker_boundary` 均不满足 `expected && ...`，以 `review_worker_workspace_changed` 拒绝；没有采用当前状态或 C 的 fallback。旧的无快照 review 也不能据此通过。 |
| 错误 review_id / attempt | SQL 同时过滤 task、attempt、`$.review.review_id`，参数来自本次 review，未使用“最新请求”或仅按 task 查找。`:177–179` 的事件表与追加式触发器禁止更新、删除；正常产品路径以随机 review_id 一次创建请求。没有找到可让另一次 review 的快照被正常取用的入口。数据库被越权直接插入伪造事件不在本次授权威胁边界内。 |
| 审查开始前已脏 | 快照会记录脏状态，但 `expected.status === ""` 是结束核对的额外必要条件，即使后来清干净也拒绝。启动前不立即拒绝会消耗一次审查，但不会把脏基线放行。 |
| detached 或错误分支 | 获取快照和结束读取都容许 symbolic-ref 返回 1，以便判定状态；`expected.branch === refs/heads/a2a/<attemptName>` 仍是必要条件。起始 detached 返回空串而被拒，结束 detached 或切分支则不等于原分支。 |
| 目录、refs、副本 | `core.ts:2320–2341` 仍检查副本位置/存在/非链接，审查 worktree 注册、detached、HEAD、干净，以及 worker 的预期路径和 worktree 注册；`:2326–2327` 比较共享 refs。没有被 worker 快照替代。 |
| 回收与集成顺序 | `core.ts:2285` 起 reclaim 持操作锁，先做边界检查、删副本、删审查 worktree，之后才写 `review_reclaimed`；`:2167–2172` 的集成前置仍要求该 review 的回收事件。失败路径 `:2176` 起使当前审查 unknown、task paused 并上报，未发成功回收事件。 |

上表中缺快照、错 review_id、起始脏和起始 detached 的结论来自控制流核对，未冒充本 reviewer 已跑过的真实入口反例。三条新增 worker 用例从干净的单次审查起步，不直接覆盖这些输入。HEAD 反例同时进入 detached 状态，不能称为只隔离 HEAD 一项比较；它确实隔离了 worker 边界与共享 refs，另有同 HEAD 切现有分支的专门反例。

## EVIDENCE：原始运行记录读回

以下归档根目录记为 `A=/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090`。逐项读取其 `run.json`、失败 traceback 与相关 SQLite 导出事件，而非只读仓库摘要的 PASS 字段。

| 项目 | 读回及结论 |
| --- | --- |
| 修复前红态 | `A/red-01/focused/run.json`：1 条，1 error；不是断言直接报门禁错误，而是 driver 等待回收超时。`readbacks/t-qrrkgqfa.json` 进一步确认 C=`11834f7be2819e8141edcf5bd6f90e105953f667`，worker HEAD=`900e915ff58454af17760fb8d51f519a50c86590`；seq 136 为 `review_lifecycle_failed/reclaim/review_worker_workspace_changed`，task paused，无 `review_reclaimed`。业务红态成立。 |
| 修复前反例基线 | `A/boundary-baseline-01/worker-boundary-baseline/run.json`：HEAD、dirty、branch 三条 passed，清理无失败。修复前确实具有这些拒绝能力。 |
| focused 与交付 8 | `A/green-regression-05/focused/run.json`、`coop/run.json`：1/1、8/8，0 failure/error/skip，collection_errors 为空。focused 的请求 seq 121 保存 worker HEAD=`c923953ce609d9870d885784ec5f0e8ade823dec`，C=`dd1af4a0d3a93f081db31ec808055042412e226e`，干净且在预期分支；seq 162 回收，最终 verified，仍绑定 C。 |
| 恢复 9 | `A/green-regression-03/recovery/run.json` 及 `green-regression-05/recovery/run.json`：均 9/9，0 failure/error/skip，collection_errors 为空。 |
| 编排 18 | `A/run-three-versions-01/T090/run/run.json`：18/18，0 failure/error/skip，collection_errors 为空；比较记录中 pre-T082 main、T-082 main、T-090 三版本分别全部通过。 |
| CAS、任务卡 | `A/green-remaining-01/cas/run.json`、`cards/run.json`：1/1、15/15，0 failure/error/skip，collection_errors 为空，绑定冻结 revision。 |
| worker 三反例 | `A/green-remaining-01/worker-boundary/run.json`：三条 passed。各 case 的实际 refs 与 refs_at_review_start 相等；外部 HEAD/branch/dirty 变化后均 paused、review unknown、上报 `review_worker_workspace_changed`，保留副本与审查目录，无 reclaimed/integrated。注意不能拿 verify 前的 refs 作对照：verify 自己会创建保留 ref。 |
| T-082 七场景 | `A/green-remaining-01/t082-end-and-launch/run.json`：副本正常生命周期、审查目录外部写入、真实 payload 读回、共享 refs 变化、错误 mutation workspace、脏/干净两种提前集成窗口，七条全部 passed。 |
| 四个启动变异 | `A/green-remaining-01/{readonly-argv,wrong-workspace,network-enabled,tmp-writable}/run.json`：各自 passed，均经 `launch_boundary_refused` 检查真实门禁拒绝，没有把这四个预期拒绝冒称坏实现的 suite 失败。 |
| 删除 worker 检查的三个反事实 | `A/green-remaining-01/worker-check-omitted-{worker_head_changed,worker_became_dirty,worker_branch_changed}/run.json`：分别为 contract_failure，failure_id 为 `T090-WORKER-HEAD/DIRTY/BRANCH`，清理无失败。原始读回中错误实现把 task 留在 verified、review passed，删副本/审查目录并写 reclaimed；不是依赖缺失或宿主崩溃导致的红。 |

`green-remaining-01.json` 和其清单在审查开始时是已有未跟踪文件，因此是冻结提交之后的补充运行证据，不是冻结提交内文档；本次没有把它们加入 Git。其受测源码绑定冻结 revision，原始归档可读。

### 分次通过是否足够

T-090 第 29 行要求整组在修复版本上通过，没有规定必须一个进程或一次 uninterrupted run。分次运行本身不足以否定功能验收，但必须证明每套件的源码和验收同一性。

本次比较 `18dd12c29`、`e50c16f5c`、`a74adeddc` 至冻结 revision 的 `workbench/src`、`workbench/tests`、`acceptance`、`fixtures`，diff 均为空；宿主诊断脚本的变化单独存在于 evidence 中。另直接逐字节比对下列四份原始归档中的上述 168 个受控文件，每份均零缺失、零差异（未计算哈希）：

- 恢复 9：`A/green-regression-04/fixtures/t090-source-m1buaeqm/source`。
- 交付/focused 的 green-regression-04 运行源码：`A/green-regression-05/fixtures/t090-source-fbwjfo50/source`。
- 编排 18：`A/run-three-versions-01/fixtures/t090-compare-__8xy32f/T090`。
- 剩余检查：`A/green-remaining-01/fixtures/t090-source-jhw_4fsa/source`。

所读取 green-regression-03、04、05、green-remaining-01 的 `candidate.patch` 均为 0 字节，没有未提交产品补丁。上述分次绿态可合并用于“同一产品与验收文件上的各项功能回归已通过”的判断。整组从未在同一次运行中全部通过，`green-regression-01` 至 `05` 的 INCOMPLETE 必须保留；不能将它们改报整组 PASS，也不能据此宣称可靠性、性能或高负载稳定性。独立变异与 stale 项仍使本次整体审查 INCOMPLETE。

### 偶发失败的归因强度

- `green-regression-01/focused` 是 ready 文件空内容的 JSONDecodeError，发生于 setUp；原子发布修在测试宿主，未改产品或验收断言，随后同一入口有通过记录。它不是 T-090 产品业务红态。
- 恢复失败的直接原因可以核实：`green-regression-02` 的两条为 verify 12 秒期限；`green-regression-04` 另有 driver 的 8 秒回收期限。后者原始 readback 中 `test_after_CAS_recovers_bookkeeping_without_Git_write` 在 17:07:01.101 有 review_result，17:07:07.160 有 reclaimed，无 lifecycle_failed。等待超时不能等同于边界拒绝。另有 cleanup 的 incomplete-followup、defunct PID 错误，也应保留，不能只计最初超时。
- run 失败不全是同一种异常：包含 5 秒 prompt 等待错误及 retained-ref 断言失败。`green-regression-05/run/readbacks` 的 transient-tool 场景中 run 自 18:24:39.451 开始，预算 8 秒，18:24:52.830 已记录 run_deadline，18:24:59.401 才 reclaimed；后续受控执行者继续显式 finalize，不能把它当成 run 已按期完成。缺失保留 ref 与这条 deadline/回收路径相符。unknown-identity 场景则记录 identity_conflict，dispatch 约耗时 3.75 秒，prompt 夹具未在自身窗口观察成功；不能统称为产品漏检身份。
- `recovery-four-versions-02` 名称虽含 four，实际选择的是三版本、每版本两条曾失败的恢复用例，均通过；不是四版本也不是三版本各跑恢复 9。`run-three-versions-01` 才是三版本各跑 18 条。
- 三版本对照与同修复版本的完整绿态支持“这些失败尚不能归为 T-090 的确定性功能回归”。它们不能单独证明“全部由系统负载导致”这一因果结论，尤其不能证明新检查没有额外耗时；本次也未做独立、匹配负载的因果实验。按直接观察归类为夹具期限/观察失败是有依据的，负载是合理推断而非已排他证明的根因。

## FINDINGS：按严重度

1. **[P2，完成条件未满足] `.project-map/MAP.md:83`，关联 T-090 票 `:31`。** 开始及报告前运行指定 status 命令，均为 Problems 0、Stale living docs 1，`workbench/README.md` 因 `workbench/src/gates/core.ts` 变化被标 stale。可达复现命令为 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`，退出 1。这里尚未证明 README 正文有具体错误，但“无 stale”这一明确条件已不满足。应由有写入权的执行者核实文档；按实际情况更新文档或登记已验证版本，再重跑 status。reviewer 不代改地图。

没有确认的 P0/P1 产品缺陷。独立变异受阻是下面的证据限制，不把环境限制伪装成产品缺陷。

## COUNTEREXAMPLE：完成条件与变异检查

隔离目录 `/private/tmp/t090-review-j1118p_x`。用 `git clone --shared --no-checkout` 建副本，sparse-checkout 取相关目录，再在副本 checkout 冻结 revision；只在副本的 workbench 中生成变异，依赖链接到既有 `/Users/luckye/Documents/Code/a2a/workbench/node_modules`。未修改共享 worktree。Node `v26.5.0`，Python `3.9.6`，真实模型回合 0。

令 `R=/private/tmp/t090-review-j1118p_x`、`S=$R/source`。实际执行命令如下（临时路径在报告保存后清理，主控复跑须新建隔离目录）：

```sh
python3 -B "$S/workbench/tests/test_t090_review_worker_boundary_e2e.py" --source "$S" --output "$R/baseline-worker"
python3 -B "$S/workbench/tests/test_t090_review_worker_boundary_e2e.py" --source "$R/M1-omit-worker" --output "$R/M1-omit-worker-result" --case worker_head_changed
python3 -B "$S/workbench/tests/test_t090_review_worker_boundary_e2e.py" --source "$R/M2-omit-clean-status" --output "$R/M2-omit-clean-status-result" --case worker_became_dirty
python3 -B "$S/workbench/tests/test_t090_review_worker_boundary_e2e.py" --source "$R/M3-omit-current-branch" --output "$R/M3-omit-current-branch-result" --case worker_branch_changed
```

| 变异 | 精确改动及预期可达错误 | 本 reviewer 实际结果 |
| --- | --- | --- |
| M1-omit-worker | 删除 `core.ts:2347–2351` 整个 worker 状态 requireGate，保留路径、refs 与审查目录检查。worker 在审查中 checkout detached base 仍会被错误回收；应命中 `T090-WORKER-HEAD`。 | 退出 1，harness_error，failure_id null，未到业务断言。 |
| M2-omit-clean-status | 删除 `core.ts:2350` 的当前 status 比较，把前一行末尾 `&&` 改为逗号；保留 `expected.status === ""` 与 HEAD/branch 比较。审查中写脏 worker 将被错误回收；应命中 `T090-WORKER-DIRTY`。 | 退出 1，harness_error，failure_id null，未到业务断言。 |
| M3-omit-current-branch | 只删除 `core.ts:2349` 的当前 symbolic-ref 比较行。审查中切到预先存在、指向同一 C 的分支将被错误回收，refs 不变；应命中 `T090-WORKER-BRANCH`。 | 退出 1，harness_error，failure_id null，未到业务断言。 |

原版基线同样在第一条 worker_head_changed 的 setUp 失败。四次的共同原文为：

```text
PermissionError: [Errno 1] Operation not permitted: '/bin/ps'
test_quality_chain_e2e.py:160 in start_host
  observed = self.process(['/bin/ps', '-p', str(self.host.pid), '-o', 'pid=,ppid=,pgid=,command='])
HarnessFailure("[Errno 1] Operation not permitted: '/bin/ps'")
```

四份 `cleanup.json` 均为 `failures: []`、`host_exit: 0`，确认只关闭本次夹具启动的 daemon。原版与三变异的 `node --check <对应路径>/workbench/src/gates/core.ts` 全部退出 0，排除了这三处变异自身的语法失败；语法检查不算业务变异证明。

本次**没有**把四个退出 1 计为“测试抓住错误实现”，也没有删除进程组检查、伪造 ps 结果或借别的工具规避沙箱限制。worker 已有的三个“删除整块 worker 检查”反事实是真实业务红态，但来自先前执行者，不能替代本 reviewer 自己完成变异的要求。

交主控的最小补证：在允许 `/bin/ps` 的宿主中新建上述冻结候选的隔离副本，按表中精确改动重建 M1/M2/M3，原版先全部通过，再分别运行对应命令；要求三个错误实现以相应业务 failure_id 失败且无 harness_error/清理失败。需要额外权限的命令仅在此报告交接，本次未申请升级。完成之前，本项为 INCOMPLETE。

## LIMITATIONS 与交接

- 没有独立重跑原交付/恢复/run 整组；本次已确认夹具的进程观察被沙箱拒绝，未重复做必然相同的宿主失败。对它们的判断基于原始保存输出、事件与受测文件直接比对。
- 没有再调用真实 Codex reviewer。启动保护相关产品代码未改，本票使用的四个启动参数反例与七个生命周期场景有新运行证据；这不能扩大为本次重新证明了真实操作系统写保护或模型审查能力。
- 快照缺失、错 review_id、起始脏和起始 detached 的动态覆盖未补做。静态路径均 fail closed；若主控要求这些也有真实入口证据，须在允许的宿主补做，不能将此处静态判断记成运行 PASS。
- 全部既有异常和未跟踪补充证据保留。独立会话的命令、共同失败原文、结果与清理读回已记录在本文；按派发要求清理本次临时目录及四个自有 q76 夹具目录，不保留副本或后台服务。

RULE: 关闭前既要确认冻结产品与验收文件的同一性，也要区分 contract_failure 与 harness_error；独立变异必须命中业务断言。现有 runner 已记录 outcome/failure_id/cleanup_failures，执行主控应据此验收，不把任意非零退出视为有效红态。已有 status 机械检查负责拒绝 stale 文档；本次未新增治理规则或改验收条件。

T-090 REVIEW DONE
