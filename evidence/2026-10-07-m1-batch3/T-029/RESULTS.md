# T-029：coop.py 改接 Muster（2026-10-07）

状态：**BLOCKED**。三项 Acceptance 已有证据，真实 `run` 被目录信任对话阻断；ticket 保持 open。不能据此宣布运行时切换或 M1 通过。

## 当前验收

| Ticket 条目 | 结论 | 命令与证据 |
| --- | --- | --- |
| 只调用 Muster，保留版本与启动规则 | PASS | `coop.py` 使用绝对 `MUSTER_BIN`；未提供、不是文件或不可执行时拒绝，无 PATH/Herdr 回退。真实启动 argv、Codex 0.160.1 与 Muster 0.9.3 的输出见 `final-runtime-01/events-paused.json`、`status-paused.json`。保留 gpt-6.1-sol、xhigh、显式 service_tier=fast、check_for_update_on_startup=false 和原 submit/验收/CAS/回收门禁。 |
| 交付 8、恢复 9、编排 18 | PASS | `python3 -B evidence/2026-10-07-m1-batch3/T-029/runtime_probe.py --checks --binary /Volumes/WD-Elements/dev-cache/a2a/target/worker-t029/debug/muster --output evidence/2026-10-07-m1-batch3/T-029/final-runtime-01` 在独立 Muster pane `w1:p1` 中调用三套既有验收。`final-runtime-01/suites/result.json` 记录 8/9/18 项、0 failure、0 error，以及 MUSTER pane/socket 身份。三份 `*.trace.json` 保存全部 CLI/Git/SQLite 请求和实际中断；`artifacts.tar.gz` 保留独立 repo/worktree。编排负例使用 Muster/Codex 替身，明确只是隔离编排证据，不证明真实模型边界。 |
| 真实 Codex run 完整闭环 | BLOCKED | 从同一 Muster pane 内调用 `acceptance/live_run.py`，600 秒显式 submit 等待期限。Codex 在 `w1:p2` 请求信任 `/private/tmp/t029-2uoclfw5/fixture`，尚未投递。暂停时的原始 UI 见 `final-runtime-01/w1-p2.txt`；产品 run 收据在该目录 `final-runtime-01-live_run/commands.jsonl`；task/attempt/事件见 `status-paused.json`、`events-paused.json`。无候选、验收或集成通过结论。 |
| fence 反事实 | PASS | 同一 Muster pane 内执行 `check_fence.py`，通过真实 CLI 注册独立 Git repo、claim、创建合格候选，然后用 fence+31 submit。正确候选返回 stale_fence，task/ref 保持；`final-runtime-01/fence-correct/result.json` 为 PASS。删除唯一 submit fence 校验的错误实现接受提交、把 task 从 claimed 改成 submitted，两个业务断言失败，见 `fence-mutant/result.json`；错误实现自身结果保持 INCOMPLETE，没有把它写成通过。 |

## 候选、构建与证据绑定

生产接线候选为 `9247c5c9e9c1279d1b95e0c4616cf454015ba141`。运行探针与版本记录冻结于 `0bea0e6728548fd894addbcb54ccccbfff6ff2a2`；二者的 coop.py、muster 与 scripts/build diff 为空，见 `build-result.json`。最终二进制由本 ticket 的冻结提交构建：

```sh
MUSTER_BUILD_SLOT=worker-t029 ./scripts/build build --locked --manifest-path muster/Cargo.toml
```

完整构建日志为 `build-9247c5c.log` 和 `build-0bea0e6.log`；最终调用 exit 0，实际槽为 `/Volumes/WD-Elements/dev-cache/a2a/target/worker-t029`。33 条引擎 warning 原样保留；没有改 Rust 引擎，也未另跑引擎自带单元套件。早期红态只复用 T-027 二进制，最终检查使用 worker-t029 二进制。

task=`automatic-pagination`，attempt=`593b440eec864a42b853a0898c122679`，session_id=`1729eadd3c2c4b0782fac2c37e7bf4f3`，fence=1，spec_rev=1。主控 Claude Code（Herdr `wF:pM`），worker Codex（`wF:pT`）。模型与启动请求在 metadata、startup_argv 和 command_intent 中记录；请求 Fast 不等于供应商实际 tier 已验证。目录信任阶段没有可用于真实交付结论的原生会话证据。

运行记录追加写入，没有覆盖旧失败。没有直接修改状态数据库，没有绕过持锁 verify/integrate/reclaim，没有更新用户工作分支或 push。运行前剥离全部继承 HERDR/MUSTER 变量与 CODEX_THREAD_ID；新 server 不继承 CODEX_HOME，Codex 使用正常 ~/.codex。没有安装、复制、修改或批准用户 hook；最终对 config.toml、hooks.json、herdr-agent-state.sh 的逐字节比较均相同，见 `final-runtime-01/result.json`。现有 Herdr hook 在缺少 HERDR_ENV/socket/pane 时退出，检查见 `normal-home-hook-boundary.json`。所有 server 控制均绑定自己创建的含 t029 名称的会话，用户 Herdr 未被重启或修改。

## 红态与额外权限保护

- `red-suites-01`：在产品改动前，把既有编排边界的可执行名和上下文迁移到 Muster，业务断言未变。8 项交付、9 项恢复通过；18 项编排中 13 项失败、0 error，旧产品要求 HERDR_ENV。完整 snapshot、trace、日志和 repo archive 均保留。红态属于新的运行时合同，不能称为原 Herdr 实现缺陷。
- `red-live-02`：真实 Muster server/pane 内的旧 dispatch 和 run 均以 herdr_context_required 拒绝。没有向用户 Herdr 转发请求。原入口仅迁移外部控制可执行文件，原门禁答案不变。
- `red-live-01`：探针误把成功 pane run 的空 stdout 当 JSON；已保留 driver-failure 和实际 dispatch 红态。错误后自己创建的 server 已退出，补发 stop 返回 Connection refused；未把这一探针错误算作业务红态。
- `green-suites-01`：初步本地 8/9/18 全通过，属于纯 CLI/Git/SQLite 和隔离编排证据。这个阶段结果中的 repository_head 是结束时提交；实际执行源码 snapshot 保留，生产源码与冻结接线候选一致。最终 Muster pane 复验另记录开始/结束版本与运行时上下文。
- `red-hook-review-01`：依据 T-027 的真实 Hooks need review 界面，建立 idle 但需权限的外部边界。未加保护时自动 prompt 并回收 pane，两个业务断言失败。增加启动保护后 `green-hook-review-01` 通过，不 prompt、不关闭 pane。没有改 oracle 或降低 startup ready 条件。

**Tracer bullet** 为真实 Muster CLI→server→pane→coop.py→门禁；模型的最后一段停在显式权限门。**Deep modules** 保留已有持久门禁，不另造 runtime 适配器或平行 API。**Ubiquitous language** 沿用 CONTEXT 的 task/attempt/session_id/fence；引擎控制字段仍为 spec 允许的 workspace/tab。

## 权限交接、审查与剩余工作

具体权限范围、主控检查材料和已绑定现场在 [APPROVAL-REQUEST.md](APPROVAL-REQUEST.md)。原 run 已返回 paused，没有输入 trust 选项或 Enter。暂停时 server/pane 被保留；交接前的权威 agent list 返回 server_not_running，ps 确认原 PID 不存在。worker 没有发送 final run 的 server stop，退出原因未确定。会话目录、task/attempt、worktree、原始 UI 和归档仍保留，原 pane ID 不能当 live handle。见 handoff-live-scene.json、handoff-server-exit.json。主控须先核对这次退出与持久状态，再批准目录信任及明确恢复步骤；身份不确定时不得回收或重派。恢复后清理仍绑定原 attempt，新 run 不接管旧身份。

真实 run 尚未获得许可，冻结候选的 fresh-context 独立只读审查尚未执行；不能拿既有 T-027 审查替本候选背书。恢复后完成真实交付、独立 oracle、CAS、回收，再冻结全部证据做一次审查，记录模型与冻结提交。

复跑 `runtime_probe.py --checks` 前，需要让 suites/fence 临时目录名包含这次输出目录名：当前 first-run 的子目录名固定，已经保存的 `.runtime/t029-suites` 与 fence 目录会使下一次同结构运行拒绝 mkdir。不得删除旧现场来消除冲突；可在获批恢复后做最小命名修正。该限制不改变本次已完成的三套验收或 mutant 结果。

根 README、MAP、AGENTS、CONTEXT 未修改。`project_map.py status` 结构问题为 0，README/CONTEXT stale：README 需要写明 MUSTER_BIN、Muster 运行时、live_muster.py 的新入口及当前真实 run 尚未通过；CONTEXT 术语未变，可由主控核对后更新 Verified；README 的 Covers 需替换已删除的 live_herdr.py。worker 按任务书交给主控处理。
