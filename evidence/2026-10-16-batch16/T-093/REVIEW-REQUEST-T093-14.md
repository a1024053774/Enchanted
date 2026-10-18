# T-093 上游关闭确认的 EPERM 时序交接 14

**INCOMPLETE：局部红绿与严格反例通过；新 counts 单场及 V 独立核对待主控在沙箱外运行。**
候选绑定最终 `T-093 FROZEN <完整 SHA>`。task T-093 / attempt a1，worker s16-t093；session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。
最终实现冻结 ae54aac378d7e646b8677e1763cf604ef8a182c4，限定复核 [UPSTREAM-SHUTDOWN-REVIEW-02.md](UPSTREAM-SHUTDOWN-REVIEW-02.md) 确认原 P1 的 L1 缺口关闭；实际 OS/V 仍为 INCOMPLETE。此后只补文本证据，运行代码未改。命令仍使用最后 FROZEN 的完整 SHA。

主控 #116 已在 079842e8b 完成 primary04、green04、演练核对及正式六场。primary 命中预定主动失败，两条完整 JSON 均匹配；green 和演练核对通过。正式 none 通过，五个变异均命中预定业务断言，但 counts 收尾有一项未确认，因此原六场核对仍为 INCOMPLETE。
原件摘要见 chain-07-validation-summary.json，原独立结论 chain-07-check.json、rehearsal-04-check.json；原失败不覆盖。

## 定位与修复

counts 原主失败是 `missing_raw_request_must_be_detected`，阶段 missing_record，两个上游请求已完成。
次要错误不是文件读取失败或关闭收据超时，而是 `process.kill(-U.pgrp, 0)` 返回 `EPERM`；原 stack 精确落在读取 `U/closed.json` 之后的 gone 调用。
U 的代码先关闭两个监听 socket，再写 closed.json，最后返回退出。这个收据只能证明端点已关闭，不能证明进程已经退出。
同一结果的最终 writer_exit 又确认 U 组已经消失；旧 gone 只有 ESRCH 返回 true，因此后续已观察到 ESRCH。
counts 变异仅把 counts_match 改为 true，不改请求、stop、进程或 profile 路径。证据指向“端点已关闭、进程尚未确认退出”的查询窗口，而非变异导致收据无法读取。
没有采集 EPERM 的具体内核／策略来源，不把 EPERM 推断为已退出。

修复只在测试链的 gone 谓词把 EPERM 表示为“尚未确认”，继续原有有界等待。ESRCH 仍是唯一退出证明；正常 kill(0) 返回和 EPERM 都返回 false；其他错误仍抛出。
U 仍必须先读关闭收据，再在原 5000ms 期限内确认组不存在。D 收尾及最终全部 writer 屏障使用相同谓词，原期限和删除前确认不变。
持续 EPERM 或仍活着会到期限失败、保留清理错误，未确认 writer 时禁止删除。主失败仍先落盘，清理错误另外列出。
最终 all_exited 还必须同时满足最后采集的每个 groups/children.exited，不能仅沿用此前 quiet() 的结果。即使早前两次 ESRCH，只要最终逐项查询为 EPERM，汇总即 false、禁止删除。
没有新增重启、终止信号、非保护查询、profile 权限或成功降级；产品源码、门禁、网络与 auth 规则未改。

## 局部证据与限制

- upstream-shutdown-red-02 在旧真实 C 回调上命中 `transient_query_denial_must_wait_for_ESRCH`；green-01 七场通过，含 EPERM→EPERM→ESRCH、存活→ESRCH、已退出、持续 EPERM、持续存活、缺关闭收据和其他查询错误。
- upstream-shutdown-mutant-01 把 EPERM 当已退出，被退出业务断言拒绝；不允许仅凭收据或权限拒绝通过。
- counts-selection-red-01／green-01 验证新的 `--counts-only` 范围。V 复用原有每场全部断言，只要求集合为 counts 一场；默认仍要求六场。错候选／错场景／重复／错主失败／清理失败／查询权限未知／存活 writer 都拒绝；不能和 rehearsal 混用。
- chain-publication-green-07 五项、chain-cleanup-oracle-green-05 十二项和 upstream-prompt-green-03 十三项通过。
- 首轮冻结 74b7db2bd 的独立审查 FAIL，原文 UPSTREAM-SHUTDOWN-REVIEW-01.md；它以最终 group／child 的 ESRCH→ESRCH→EPERM 时序复现汇总未约束明细的 P1。现已将汇总绑定全部最终明细，writer-exit-red-01／green-01 的同一实际 D／writer 回调七项由两项失败转为全通过；原失败不改写。

上述是 L1：执行实际 C 回调、finishChain、V main，但用外部给定 signal 时序／收据。不运行真实进程查询、嵌套 sandbox、CLI、auth、网络或模型，不能代替本机新 counts 入口。
首轮提取器把 return 交给顶层 TS parser，尚未进入业务检查；harness-01 单列保留，不计红态。修正提取器后才取得 red-02，再改行为。

复现命令（各输出必须不存在）：

```sh
node workbench/tests/test_t093_upstream_shutdown.ts /private/tmp/t093-r14-shutdown.json
node workbench/tests/test_t093_writer_exit.mjs /private/tmp/t093-r14-writer-exit.json
python3 -B workbench/tests/test_t093_counts_result_selection.py /private/tmp/t093-r14-selection.json
node workbench/tests/test_t093_chain_publication.ts /private/tmp/t093-r14-publication.json
python3 -B workbench/tests/test_t093_chain_cleanup_oracle.py /private/tmp/t093-r14-cleanup-oracle.json
```

## 沙箱外只重跑 counts 与独立核对

按主控要求，本次不重跑其他五场或演练。使用本次完整冻结 SHA、新输出及同名 events 原件，不改旧 chain-07 记录。两个入口脚本均自行挂既有 OS profile；不得加 `--guarded`。

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本次完整冻结SHA
bash "$repo/evidence/2026-10-16-batch16/T-093/EVIDENCE-RECHECK-03.sh" \
  "$repo" "$candidate" /private/tmp/t093-chain-08-counts.json counts-always-match
```

预期 rc 2、INCOMPLETE、primary_failure 恰为 `missing_raw_request_must_be_detected`，cleanup_failures=[]、fixture_removed=true、所有 writer 退出已确认。若不符即停，回传主／次错误，不运行核对或其他场景。

```sh
python3 -I -S -B "$repo/workbench/tests/check_t093_chain_results.py" \
  --counts-only --candidate "$candidate" --output /private/tmp/t093-chain-08-counts-check.json \
  /private/tmp/t093-chain-08-counts.json
```

预期 rc 0／PASS，cases 恰为一项 counts-always-match，primary_matched=true、pass=true。V 继续独立查询原登记组／子进程／报告者，EPERM 不算退出。
这只形成新候选的 counts 复验证据，不把旧五场改写成新候选运行。共享 processInfo 的调用点及 T-091/T-078/T-096 回归仍见请求 13；T-096 旧记录集成检查项保持 INCOMPLETE。
不以本次冻结代替 submit、验收或集成，不启动真实模型回合。
