# mutant-cas 分类失败诊断（主控 #342）

**分类器修复与保存结果重放 PASS；新的真实门禁单段复验尚未运行，INCOMPLETE。** 原整组输出不改写。

根因是 `run-review-followup-regressions.py` 的预期 claim 写错。旧 runner 第 65–67 行只接受 `CAS rejects a changed expected old value` 或 `CAS preserves the external writer reference`；实际选中的原方法 `workbench/tests/test_cas_race.py::CASRace.test_external_write_between_read_and_cas_is_preserved` 根本不产生这两条 claim。原整组顶层 traceback 正好停在该 claim 匹配断言。

原方法的预期来自 CAS / R8 契约：在 Git 写入前有独立外部提交时，保留该提交，重新验证新的 G 和不变的 C，不能无条件更新引用。变异 helper 只删了 `update … M G` 的 expected-old 参数 G，未改变用例、调度、oracle 或其他门禁代码。已将留存的变异源码与当前原源码按同一 helper 的单点替换逐字核对，完全一致。

## 期望与实际证据

以下均来自 [原 assertions.json.gz](review-followup-regressions-02/mutant-cas/assertions.json.gz)，其完整 observed 保留；[诊断 JSON](mutant-cas-diagnosis-01/result.json) 只另做摘要。

| 原方法的 claim | 实际 expected / observed | 判定 |
|---|---|---|
| CAS revalidation binds the new G and unchanged C | 新 G=`d7aad81945b9faf39a91af4a20230f4033617d1a`；实际仍为旧 G=`932b795cc4460345ee4e211f2f441cb39e54afaa`；C 两者均为 `af04bc3ad17feac4e5a9db9578a4416f3efe4990` | false |
| CAS integration preserves ancestor d7aad81945b9faf39a91af4a20230f4033617d1a | `merge-base --is-ancestor` 期望 0，实际 1 | false |
| CAS revalidation executes the oracle again | 期望 2，实际 1 | false |
| CAS preserves external writer content | 工作目录的 external.txt 内容仍在 | true；不能替代 Git 祖先关系或重验 |

[原 run.json](review-followup-regressions-02/mutant-cas/run.json) 为恰一个指定方法、1 failure、0 error、0 skipped、`classification=business-red`；实际子进程 exit 1。宿主 artifacts 证明加载的是 manifest 中 cas 变异 core。变异确实破坏并被原方法检出了应检的 CAS 行为，失败没有落到另一个测试或宿主启动路径。相同整组中的未变异 [CAS 正例](review-followup-regressions-02/cas/run.json) PASS。

## 修复与可证伪检查

只修改本票 runner：CAS 分支核对原方法、上述三条失败的 claim 及其具体 G/C、祖先退出码、oracle 次数，继续要求已加载变异 core、exit 1、零 error/skipped 和 business-red。没有修改 `acceptance/`、`workbench/`、变异 helper、冻结 protocol 或旧结果。

同一个 [保存原件重放入口](test-mutant-cas-classifier.py)，在改分类器前 [red-01](mutant-cas-classifier-red-01/result.json) 拒绝了有效红态；改后 [green-01](mutant-cas-classifier-green-01/result.json) 11/11 PASS：原件被接受，10 个反例均拒绝（无关失败、G 实际正确、oracle 实际已重验、C 被换掉、外部祖先实际保留、加载错 core、夹具 error、非 business-red、选错原方法、未变异正例成功）。这些是分类器保存结果重放，未运行门禁/API/角色 CLI/模型，不能充当新的 CAS 场景实跑。

新增 `--only-mutant cas` 只运行一个原方法。它仍逐字核对冻结版的全部 workbench、acceptance、scripts 和 prepare，分类器自身绑定当前已提交 HEAD，拒绝未提交修改；新输出明确标 `scope=mutant-cas only`。该模式仍用未改的 helper 生成同一单点变异（helper 同时保存另两个变异源码，但不会执行它们）。全量模式的原冻结检查不变；本次不重签旧全量冻结、不复跑已过整组、不把旧顶层 INCOMPLETE 改成 PASS。

## 交主控执行

见 [确切命令](MUTANT-CAS-RECHECK-COMMAND.txt)。`--check-only` 已实际运行，exit 0、suites 为空、mutants 仅 cas、路径/语法/单点位置 PASS，输出在 [check-only.stdout.txt](mutant-cas-diagnosis-01/check-only.stdout.txt)。正式运行预计子测试 exit 1，runner 验证指定业务红态后 exit 0、PASS；若宿主错误、错误断言、超时或冻结输入改变则 INCOMPLETE，不重试。硬等待上限沿原 runner 为 900 秒；超时保存已登记进程/现场，不盲发信号。真实模型和供应商 CLI 均 0。

输出使用全新 `review-followup-mutant-cas-03/`，旧目录不覆盖。此命令未在 worker 会话执行。lock 变异在原整组首败之后未运行，本轮也不运行；F4 整体保持 INCOMPLETE。A16/09C 两场未启动，原 Stage A 的全量回归 PASS 前置仍不满足，不能用单段 PASS 冒充全量 PASS。
