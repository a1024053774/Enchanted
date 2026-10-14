# final-04：relay helper 缺口与后续阶段预检

**INCOMPLETE。** 原 `outside-rebase-final-04/` 和控制台输出完整保留。run 已执行 18/18 并通过，CAS 1、cards 15 通过；relay-conflict 在第一次 commit 构造提交消息时抛 AttributeError，尚未验证两次交付或进入本例的 verify/integrate。不是 relay 产品拒收。

## 缺口和修复归属

`test_relay_conflict_e2e.RelayConflict` 直接继承 TaskCardsCLI。合流后的父级 commit 在 thread_id 非空时调用 managed_trailers；DaemonCards 和 MultiTurn 有此 helper，RelayConflict 没有。原始 traceback 见 `outside-rebase-final-04/relay-conflict/unittest.txt`，已保存的首次 dispatch 回复包含该 attempt 的 runtime_identity.launch，但 native_session 尚为空，不能拿它伪造原生身份。

本轮只在 RelayConflict 补这个 helper。它按传入 attempt 的 launch 读取该夹具的 env/runtime 记录，再读取该 launch 的合成 rollout：Tool 取启动环境，Model/Effort 取实际 turn_context，Native-Session 取 runtime，Launch 绑定传入 attempt。没有从 requested model 推定实际模型，没有修改门禁身份条件、提交内容、重放断言或 acceptance。这里的原生日志仍是受控外部事实，不是新模型证据。

局部 helper 检查故意让请求模型与观察模型不同，并构造 fence 1、fence 2 两套独立记录；父级 commit 须解析 helper 并使用各自的九项身份。修前 3 项中 1 error，正是 AttributeError；修后 3/0/0。其余两项核对 T-076 四个类的手工/受管 commit 分支和 relay cli 的 ok/error 关键字转发。Git 与 CLI 在这些局部检查中只录制参数，不提供业务 PASS。

## 先预检后修复

修复前先检查了 final 计划在 relay-conflict 及其后的 Python 入口：relay、受控尾注候选、identity、shutdown、T-076 tracer、wide、reviewer 故障、协议控制、来源冻结。按实际选择的名单实例化 **8 类、52 个场景**，不执行 setUp；沿 self、super、显式父类调用和 cleanup 回调追踪 helper，核对方法存在性、显式参数绑定和字段来源。初次发现只有上述 missing_method，保留在 `final05-preflight-before/`。

修复后再检查 QualityDriver 与 CommandLog 的构造器和 helper 签名，完整结果为 **1,170 处调用绑定、0 个方法/签名缺口、0 个未解析字段**，见 `final05-preflight-complete/run.json`。星号展开位置原样列入 unpacked_calls；relay 的 **kwargs 仅转给接受 ok/error 的父级，已做局部调用检查。T-076 的父级 commit 仅由无 thread_id 分支调用，因此父级内的 managed_trailers 分支不可达；四个类的两类 attempt 均已在局部 helper 检查实际执行，没有给 T-076 增加替代 helper 或更改其业务断言。

这项检查不证明动态记录内容、启动后的字段初始化、并发时序或完整业务流程。受控尾注候选实际走 commit_by_hook，仍保留生产 hook 与真实 CLI/Git 的验证方式；局部录制对象没有取代它。

## 后续边界的轻量检查

九个 Python CLI 的 --help、十一份 TypeScript 入口/host 的语法检查通过。relay core、relay CLI、relay scope、全局去重变体、native-final 和 panes 六组无后台边界检查通过。结果分别保留在 `final05-boundaries-before/` 与 `final05-boundaries-completion/`；原始命令见 commands.jsonl。没有启动 daemon、模型或真实 PTY。

dispatch-state 的语法检查通过；轻量执行到 readThread 时触发真实 `/bin/ps`，沙箱报 `spawn EPERM`，未到后续业务断言。证据为 `final05-boundaries-before/dispatch-state/results.json` 和同目录原始 stderr，顶层仍保留 INCOMPLETE，没有重试或改断言。该调用来自 `Panes.processInfo`，不是 Python 方法缺口；它留在主控沙箱外的 final-05 全量阶段运行。后续可重放的轻量脚本已明确把该项列为 deferred_outside，不再误当纯离线项。

首次临时模块清单把 test_conflict_trailer_proofs 写成带 _e2e 的名称，import 当即失败；正式脚本改为磁盘上的准确模块名后运行。此为新探针的清单错误，未改产品或业务断言，也未算作红态。

## 再生成命令

在本 worker worktree 下运行，输出必须另取新目录，保留所有旧结果：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/preflight-final-05.py --output evidence/2026-10-11-batch13/T-077/preflight-replay-05
python3 -B evidence/2026-10-11-batch13/T-077/probe-fixture-helpers-05.py --output evidence/2026-10-11-batch13/T-077/helper-replay-05
python3 -B evidence/2026-10-11-batch13/T-077/preflight-boundaries-05.py --output evidence/2026-10-11-batch13/T-077/boundary-replay-05
```

修前脚本副本保存在各 before 目录的 preflight-at-run.py；修前 method 缺口的真实入口结果由 final-04 提供。全量 final-05 仍需主控运行；本轮产品保持 `5d0bf1e8`，真实模型回合 0，ticket open，独立审查未启动。
