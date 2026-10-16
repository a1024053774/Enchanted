# 三版本首轮停止原因与 deleted-ref 定位

2026-10-16。已保存现场核对 PASS；完整四点对照仍为 INCOMPLETE。

原件 `recovery-three-versions-01/pre-T082/recovery/` 位于本票外置盘归档。原 `unittest.txt` 明确：deleted-ref error，external-X ok；原 2 方法共 1 error、0 failure。不得把 external-X 改称失败，也不覆盖原顶层 INCOMPLETE。

## 退出确认的检查错误

本 worker 的比较器把所有历史 daemon 代次都要求退出 0，因此误拒绝了原恢复实验的预期故障注入。停止发生在检查 `process_exit != 0` 时，尚未对该代次执行后续 ps；不是 ps 查错 PID，也没有证据表明该 PID 仍存活。

| 用例／代次 | 原件事实 |
| --- | --- |
| deleted-ref／1 | PID 76241，process_exit=0，16:05:45.345672Z confirmed_exited。 |
| external-X／1 | PID 77428，process_exit=-9，16:07:01.299938Z confirmed_exited；同一 artifact 的 signals 在 16:07:01.204783Z 记录 target=owned-daemon、daemon_generation=1、SIGKILL/9、reason=after real Git CAS。 |
| external-X／2 | PID 78910，process_exit=0，16:07:33.991229Z confirmed_exited，随后 daemon_stopped。 |

`acceptance/test_recovery_e2e.py` 的 external-X 原方法调用 `start_git_fault("after")`；历史 adapter 验证拥有者、barrier 和 socket 后给原 daemon 发 SIGKILL，确认退出，再启动新代次恢复。这是验收所要求的故障，不是残留或启动失败。主控本轮还独立确认没有相关残留进程；续跑仍逐 PID 再核对，不用该口述代替脚本检查。

最小修法：先要求 confirmed_exited；无该 PID/代次的指定故障注入记录时只接受退出 0；有同 PID、同代次、owned-daemon、SIGKILL/9、after real Git CAS 的唯一记录时只接受 -9。随后仍用 ps 要求 PID 不存在。不能放宽为接受任意负退出码。

该记录判断需隔离验证，先列失败方式：误拒绝合法的故障退出；错误 PID 或代次借用别人的信号；没有退出确认仍放行；无故退出 -9 或其他非零被当作预期；已有业务 error 被上调成 PASS。保存的真实三代次作为正例，改动 PID/代次/确认字段的反例必须拒绝；原比较器在真实正例上失败的现场就是修复前红态。

## deleted-ref 并未永久卡在 verification 清理

此处区分本轮 `150ef6516` 与先前 `green-regression-02`，不混用两次截止点。

本轮 pre-T082 原事件：completion_check seq 65 在 16:05:23.840Z；verification_result seq 76 在 16:05:25.337Z；保留引用的 rev-parse/update-ref/rev-parse/cat-file 于 16:05:25.344Z～16:05:27.838Z 完成。verification worktree remove seq 86 在 16:05:27.844Z 发起，seq 87 在 16:05:28.460Z 返回 0，seq 88 在 16:05:28.464Z 记录 verification_worktree_removed。

随后 seq 89 review_requested、seq 94 review_started（16:05:30.201Z）；服务端 verify 结果在 16:05:30.210Z 为 ok=true。原方法先前已经抛出 12 秒客户端等待错误；清理时再调用原 `complete(handle)`，其 adapter 驱动了历史成功结果的审查，最终 seq 95 review_result、seq 111 review_reclaimed（16:05:38.313Z）。这不撤销原方法的超时 error，CAS 后删除引用场景没有由该失败方法完成。

oracle release 文件 mtime 为 16:05:17.477011Z，结果文件 mtime 为 16:05:23.811646Z。若按原代码紧接 release 调用 complete 的 12 秒计算，期限约为 16:05:29.477Z：verification 目录清理已经成功，时间落在 review 的启动窗口。该时刻是根据原代码与文件时间估算，未作为精确的 TimeoutExpired 打点。

因此，现有证据显示有限步骤持续推进且验证目录成功清理；没有某个 Git 清理操作永久挂起，也没有 review_lifecycle_failed。准确的 TimeoutExpired 发生瞬间未单独打点；只能由原方法期限和带时间事件定位窗口，不能从最终读回猜一个永久阻塞点。将保留 oracle release/result、CLI launch/complete 和这些事件的紧凑时点记录。

## main 上的第四个点

`git show a75070236` 只有一个父 `e5f8a506...`；该父已经含 T-082 产品实现，不能当作“合入前 main”。main reflog 的实际顺序是：`271ac55d82d0e20067e03e2fa4a990e55ef7b434` → `a75070236a2f5b1dda9cd3b425e4c619e7031af7`（merge exec/t082: Fast-forward）→ `0e6c2b833f6da64243f71d670ea45bb9116fda4d`。T-082 首个产品提交 `5459d6fdb...` 的父也正是 `271ac55d...`。

保留旧 exec/t078 的 `150ef6516` 作为已采集的分支对照；后续只新增 main-before-T082 `271ac55d...`、main-T082 `0e6c2b833...`、T090 `18dd12c29...` 三点，不重跑已采集版本。四点的原恢复验收需再次核对逐字节相同。旧目录及临时源码 `/private/tmp/t090-compare-4sx2giy2` 保留，未清理或覆盖。

## 修正验证与续采命令

`exit-check-replay-01.json`：用旧原件的三代 daemon 验证新检查均通过；五条错误证据反例（错误 PID、错误代次、无注入证明、缺少退出确认、意外退出码）均被拒绝。该检查只重读保存的记录，不启动宿主、不重复业务测试，也不代替续跑时的 ps。`prior-source-check-01.json` 确认原临时 checkout 的产品与验收文件仍为原字节，测试目录只覆盖了方法选择器。

紧凑时点见 `pre-t082-deleted-timeline-01.json`；main 身份证据见 `main-t082-reflog-01.txt`。四点 Git/验收字节与依赖路径预检 PASS，见 `compare-recovery-preflight-02.json`，selected 只有尚未运行的三点。

主控沙箱外执行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/compare-recovery.py --label recovery-four-versions-02 --version main-before-T082 --version main-T082 --version T090
```

新输出 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/recovery-four-versions-02/`，与旧 -01 分开。它只新增 3×2 方法执行，与 -01 已采集的 2 方法合成四点对照；每个版本保留自己的产品、adapter、driver 与宿主，只覆盖原方法选择/证据采集 runner。没有改验收、超时或增加重试。顶层 PASS 仅表示选定数据采集完成，产品仍为 INCOMPLETE。
