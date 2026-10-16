# F4：最终业务版完整受控回归（未运行）

2026-10-16，主控 #335。实际业务仍为 `dedd4f66bc424610183cbff2d7114e991483e1c6`；F6 与回归 harness 源冻结为 [review-followup-source](review-followup-source.json) 所记完整提交。执行入口先核对该提交是 HEAD 祖先、受保护源码逐字未变、工作区无未提交/未跟踪源码，再将实际 HEAD 传给原断言 runner。后续仅票内文档提交不会触发旧 HEAD==材料提交的死结。

**运行 INCOMPLETE；仅 check-only PASS。** 沙箱外由主控依次运行下列两条命令；新输出目录已做存在性检查，不存在才执行。任一非预期失败停止、不重试、不跳过下一组。没有 Claude/Codex 会话、没有真实模型回合；真实 gate/daemon/SQLite/Git 与确定性/受控线程运行时参与。

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/run-review-followup-regressions.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/review-followup-regressions-01 --check-only
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/run-review-followup-regressions.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/review-followup-regressions-01
```

| 顺序/子目录 | 实际调用与预期 | 已知红态及不能误判的失败 |
|---|---|---|
| coop | run_s3_rebased_regression --suite coop：原交付完整8方法，8/8、failures/errors/skipped=0 | T075旧入口35项socket超长只是入口红态，不能算业务反例 |
| recovery | --suite recovery：完整9方法，9/9，原故障注入与恢复断言 | lock变异须在业务断言失败，宿主启动/导入错误不算 |
| run | --suite run：完整18方法，18/18 | 其中受控线程项不冒称真实PTY/Codex；不改原用例成员或业务方法 |
| cas | --suite cas：补充1方法，1/1 | 老coop整组曾漏检CAS去旧值变异，因此必须另跑此方法 |
| cards | --suite cards：T075卡片/路径/完成命令/尾注/旧attempt-fence等正反例，共15方法，15/15 | 禁路径、失败完成命令、异任务尾注被拒；缺尾注的人工介入被记录，正常提交集成一次；包括追加式表检查。post-rebase-2-outside-01曾宿主初始化失败，已修夹具，不把它当预期红态 |
| mutant-fence | 原test_identity_gates_and_revocation_reject_old_verified_attempt；删掉submit fence核对 | 原测试exit1、errors=0、业务失败：fence+31被错误接受；协调器另判反例PASS |
| mutant-cas | 原test_external_write_between_read_and_cas_is_preserved；去CAS期望旧值 | 原测试exit1、errors=0；CAS拒外写/保留引用的独立断言失败，不能只看退出码 |
| mutant-lock | 原test_live_verify_excludes_verify_and_integrate；去BEGIN IMMEDIATE | 原测试exit1、errors=0；并发排他/不得第二oracle的业务断言失败 |

三变异复用 `prepare_daemon_mutants.prepare`，各只改当前core一个定位，保留patch/源包；每份宿主回执须证明实际加载对应mutant core。先跑五绿组，才在一次性source fixture里造变异；不编辑本worktree产品、他人票或业务断言。原runner仅增加显式单case/mutant参数，默认仍完整跑组并核对原方法数。输出含run.json、原方法/未执行清单、stdout/stderr、commands/artifacts/assertions gzip、运行时退出/状态读回和夹具归档。原始失败保持INCOMPLETE，顶层反事实成立才单独标PASS。

本轮所称T075正反例是上述15个当前后台门禁方法及fence/CAS/lock三反事实；**不声称重跑T075历史真实Codex沙箱/外网隔离或旧UI模型回合**。若验收要求重做该真实供应商边界，需另列预算/批准，不能从本命令推得。

每子阶段900秒上限；超时顶层记录INCOMPLETE及runner PID，停止后续，保留隔离句柄/夹具给主控核对，不盲发信号或删除。测试原生命周期负责正常daemon_stop；原runner报告残留/收集失败/超5MiB时不可改写PASS，先按batch13规则外置原件读回再处理。外置盘未挂载则开始前拒绝，不回退。命令本身不操作已回收A15、不推送、不修改用户HOME；原runner的短/tmp隔离仓库和受控宿主由各方法创建，原始状态在停机前采集，失败时保留实际stderr。
