# 恢复两用例的首轮诊断与三版本对照交接

2026-10-16。当前归因 INCOMPLETE；原现场读回、对照脚本静态检查 PASS。不修改门禁、`daemon.ts`、测试 driver、12 秒期限或 `acceptance/`。

## 原现场实际发生了什么

`green-regression-02` 绑定 `18dd12c29f523227d9fc6fd4c123a674f10bf7fa`：ready 探针 PASS，focused 原用例 PASS，coop 原 8 项 PASS，recovery 原 9 项中 7 项通过、2 errors，run 18 与后续场景未执行。两个 error 都来自 `setup_candidate(verified=True)` 内的异步 verify 客户端等待期限；尚未进行各自的 CAS 后故障注入。

原件：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-02/recovery/`。紧凑读回见 `recovery-observed-01.json`，只读其已保存 JSON 和 `fixtures.tar.gz`，未打开停机 SQLite。下面“没有”均限定到各自 `state_readback_saved` 截止点，不能代指此后全部后台状态。

| 原方法 | 截止点与事实 |
| --- | --- |
| `test_after_CAS_deleted_ref_requires_reconciliation` | 读回 15:48:10.835441Z：task=reviewing，但 review 尚为空；seq 76 在 15:48:06.867Z 保存 verification_result，seq 85 为 verification_cleanup_intent，seq 86 在 15:48:09.565Z 正在执行 verification worktree remove。没有 review_requested、review_result、review_lifecycle_failed、review_reclaimed。 |
| `test_after_CAS_external_X_requires_reconciliation` | 读回 15:49:15.772634Z：task=reviewing，review=running；seq 97 在 15:49:11.270Z 保存 review_requested，worker HEAD 为 C，分支为原受管分支，status 为空；seq 103 在 15:49:14.482Z 保存 review_started。没有 review_result、review_lifecycle_failed 或 review_reclaimed。服务端在 15:49:14.485Z 记录 verify request_result ok=true；这不是客户端收到结果的证明。 |

两条 `quality-control/driver.jsonl` 都只有 preparation、executor-score-prepared，没有驱动 reviewer 的 command-intent；后台请求记录也没有 pane_release 或审查 signal。两个客户端分别在 15:48:08.091545Z、15:49:12.063689Z 被原测试 cleanup 以“cleanup of owned timed-out CLI”终止，退出 -9。external-X 的服务端成功结果晚于客户端被清理，不能把它补称为该用例通过。

两个 daemon 的 stderr 均为空，均在正常清理后退出 0（PID 57844、58934）。独立 oracle 子进程均有 exit_code=0 的结果文件。当前证据排除了“读回时已被 worker 边界检查以某个错误码拒绝”：结束核对根本没有被触发；external-X 的快照绑定确实存在且干净。它也显示这次超时发生在收到 verify 结果及驱动审查之前。

尚不能据此证明 T-082 或 T-090 与时间开销完全无关，也不能归因于机器负载、缓存、Git 包装进程或慢 I/O。对三个版本的同两方法实跑尚未进行；不提高等待期限或先改完成流程来遮住差异。

## 沙箱外三版本命令

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/compare-recovery.py --label recovery-three-versions-01
```

脚本固定以下完整版本，串行在三份新的内置盘 `/tmp/t090-compare-*` checkout 中各运行同两条原方法，共 6 次方法执行；既有依赖只读借用，不安装、不构建、不启动真实 CLI/模型。

1. T-082 前：`150ef6516f6ef5aaa6855631b770ce262991ffbf`。
2. main T-082：`0e6c2b833f6da64243f71d670ea45bb9116fda4d`。
3. T-090：`18dd12c29f523227d9fc6fd4c123a674f10bf7fa`。

预检已确认 `acceptance/test_recovery_e2e.py` 在三版本中逐字节相同。产品、验收、各版本自己的 adapter、driver、宿主原字节保留；只覆盖 `run_s3_rebased_regression.py` 为当前原方法选择/证据采集 runner，逐版本保存原 runner、覆盖文件及精确 diff。仍检查原组 9 方法成员及继承方法身份，不替换业务方法；12 秒测试期限、协议和故障注入逻辑均不变。

旧版本保留其原 ready 发布方式；若再遇启动竞态，将作为环境/测试准备失败照实报告，不额外叠加新的宿主修复，不自动重跑。顶层 PASS 只表示三组结果及退出核对均已采集，`product_status` 始终 INCOMPLETE，必须分别看 test_status/errors 和事件。

新输出：`/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/recovery-three-versions-01/`；仓库仅留同名 JSON 摘要与 archive 清单。每版记录原测试状态、具体 error/failure、带截止点的实际 review 事件及错误码、verify 请求时点和最后 12 条门禁事件。原始 readback、stderr、fixture、命令输出都在外置盘。

只有确认该版 daemon 已退出 0、PID 不存在、无清理错误，才运行下一版。夹具与源码均先复制归档，核对文件数和字节数一致后再清理本次创建的原目录。外层 360 秒只是诊断进程看守期限，不传入任何原测试；看守超时则保存 PID、原始输出和 /tmp 目录，停止剩余版本，不发额外信号或重试。

## 后续归属

对照结果到达前不改变语义或扩大修复范围。若要改变原恢复验收的等待或外部 actor 驱动方式，须先由主控确认根因与验收意图；本轮只交付诊断和可复现对照入口。原 source `/private/tmp/t090-source-bsolfugr` 仍保留，未移动或覆盖。
