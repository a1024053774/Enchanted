# T-029：coop.py 改接 Muster（2026-10-07）

状态：**BLOCKED**。三项 Acceptance 已有新候选证据。主控许可下已解决 server 生命周期和目录信任、reclaim 旧 attempt；第二次真实 `run` 被 Git 暂存权限对话阻断，ticket 保持 open。不能据此宣布运行时切换或 M1 通过。

## 当前验收

| Ticket 条目 | 结论 | 当前命令与证据 |
| --- | --- | --- |
| 只调用 Muster，保留版本与启动规则 | PASS | `coop.py` 仍是单一显式绝对 `MUSTER_BIN` 路径，版本检查和原门禁未变。当前真实 argv、Codex 0.160.1、Muster 0.9.3 见 `final-runtime-02/events-paused.json`。无 Herdr fallback。 |
| 交付 8、恢复 9、编排 18 | PASS | `final-runtime-02/suites/result.json`：8/9/18、0 failure、0 error，在新候选的脱离进程组 Muster pane 内复验。三份 trace 与完整 repo/worktree archive 保留。编排负例仍仅为隔离 Muster/Codex 替身证据，oracle 预期未变。 |
| 真实 Codex run 完整闭环 | BLOCKED | 新 attempt、fence=2 已开始工作，pager.py 已修改，但 `git add -- pager.py` 请求沙箱外写入 Git index.lock。原始 UI、run_blocked 收据、claimed task 和未提交 worktree 见 `final-runtime-02/w1-p2.txt`、`status-paused.json`、`worker-worktree-paused.json`。尚无 commit/submit/独立验收/集成/回收。 |
| fence 反事实 | PASS | `final-runtime-02/fence-correct/result.json` 为 PASS；去掉唯一 submit fence 校验的 mutant 接受 fence+31，改变 task，两个业务断言失败，见 `fence-mutant/result.json`。错误实现结果保持 INCOMPLETE；该预期业务失败构成反事实证据，不是环境错误。 |

当前复验入口（本次许可已使用，不能据此自动启动下一次模型运行）：

```sh
python3 -B evidence/2026-10-07-m1-batch3/T-029/runtime_probe.py --checks --isolated-codex-home \
  --fixture-repo /private/tmp/t029-2uoclfw5/fixture \
  --existing-state /Users/luckye/Documents/Code/a2a/.runtime/final-runtime-01-live_run/state \
  --binary /Volumes/WD-Elements/dev-cache/a2a/target/worker-t029/debug/muster \
  --output evidence/2026-10-07-m1-batch3/T-029/final-runtime-02
```

## 候选、构建与证据绑定

当前冻结候选为 `328922f94cb24ed05a4cb5d448427d87be3fb445`，构建证据为 `build-328922f-result.json`、`build-328922f.log`，exit 0。相对前候选，coop.py、muster 与 scripts/build diff 为空；变更是测试入口生命周期、授权的隔离 home、目录唯一命名和复用同一注册 task 的 live 参数。生产接线为 `9247c5c`，首轮 runtime 冻结为 `0bea0e6`，其旧记录保留。最终二进制由本 ticket 的冻结提交构建：

```sh
MUSTER_BUILD_SLOT=worker-t029 ./scripts/build build --locked --manifest-path muster/Cargo.toml
```

完整构建日志为 `build-328922f.log`，旧 `build-9247c5c.log` 和 `build-0bea0e6.log` 保留；最终调用 exit 0，实际槽为 `/Volumes/WD-Elements/dev-cache/a2a/target/worker-t029`。33 条引擎 warning 原样保留；没有改 Rust 引擎，也未另跑引擎自带单元套件。早期红态只复用 T-027 二进制，最终检查使用 worker-t029 二进制。

task=`automatic-pagination`，当前 attempt=`b102c2a0ec3b447f8a022c1c042d2b13`，session_id=`8eca1e6c59f94b44aca000e5360c5bdd`，fence=2，spec_rev=1。run ID=`09a2c4e076704e01b0d7e60688b2071b`。主控 Claude Code（Herdr `wF:pM`），worker Codex（`wF:pT`）。模型与启动请求在 argv/事件中记录；请求 Fast 不等于供应商实际 tier 已验证。没有保留下本次原生 rollout metadata；home 删除后收集器输出空数组，该数组不是原生会话证据。

运行记录追加写入，旧失败不覆盖。没有直接修改状态数据库，没有绕过持锁 verify/integrate/reclaim，没有更新用户工作分支或 push。server 继承环境剥离 HERDR/MUSTER 与旧 CODEX_THREAD_ID/CODEX_HOME，再设置获批隔离 home；用户 ~/.codex 原始配置字节保持，旧第一轮正常 home 和本轮隔离 home 的不同授权边界均留档。当前 auth 副本仅在 `/tmp/t029-codex-s21w85ap`，600 权限，只生成一项已核对夹具信任配置，不复制用户 config/hooks/rules。`isolated-home-cleanup.json` 记录完整删除；三个当前 archive 检查均不含 auth.json 或该 home。实际 model self-test 不是独立 oracle 通过证据。

## 红态与额外权限保护

- `red-suites-01`：在产品改动前，把既有编排边界的可执行名和上下文迁移到 Muster，业务断言未变。8 项交付、9 项恢复通过；18 项编排中 13 项失败、0 error，旧产品要求 HERDR_ENV。完整 snapshot、trace、日志和 repo archive 均保留。红态属于新的运行时合同，不能称为原 Herdr 实现缺陷。
- `red-live-02`：真实 Muster server/pane 内的旧 dispatch 和 run 均以 herdr_context_required 拒绝。没有向用户 Herdr 转发请求。原入口仅迁移外部控制可执行文件，原门禁答案不变。
- `red-live-01`：探针误把成功 pane run 的空 stdout 当 JSON；已保留 driver-failure 和实际 dispatch 红态。错误后自己创建的 server 已退出，补发 stop 返回 Connection refused；未把这一探针错误算作业务红态。
- `green-suites-01`：初步本地 8/9/18 全通过，属于纯 CLI/Git/SQLite 和隔离编排证据。这个阶段结果中的 repository_head 是结束时提交；实际执行源码 snapshot 保留，生产源码与冻结接线候选一致。最终 Muster pane 复验另记录开始/结束版本与运行时上下文。
- `red-hook-review-01`：依据 T-027 的真实 Hooks need review 界面，建立 idle 但需权限的外部边界。未加保护时自动 prompt 并回收 pane，两个业务断言失败。增加启动保护后 `green-hook-review-01` 通过，不 prompt、不关闭 pane。没有改 oracle 或降低 startup ready 条件。

**Tracer bullet** 为真实 Muster CLI→server→pane→coop.py→门禁；模型的最后一段停在显式权限门。**Deep modules** 保留已有持久门禁，不另造 runtime 适配器或平行 API。**Ubiquitous language** 沿用 CONTEXT 的 task/attempt/session_id/fence；引擎控制字段仍为 spec 允许的 workspace/tab。

## 恢复与当前权限交接

[主控决定原文副本](controller-decision-used.md) 批准先复现生命周期原因，以及新建隔离 home 的 auth 副本和唯一项目信任。

`lifetime-attached-01` 的同 PGID server 在 launcher 结束后消失，没有 shutdown/panic 日志；`lifetime-detached-01` 的独立 PGID server 被 PID 1 接管，跨多次独立工具调用持续 running，只有明确的 owned server stop 才出现 shutdown 日志。启动差异证实生命周期夹具问题；具体回收信号未采集，不把机制推断写成 kernel trace。`lifetime-and-recovery-result.json` 保存边界与结论。只修 Popen(start_new_session=True)/stdio，不改引擎。当前 server 在工具调用结束后的最新 handoff 核对仍 running；原第一次退出不计作产品失败。

旧 engine/shell/Codex PID 均不存在，先将原布局保存为 session-before-reclaim.json，避免启动新 terminal 后占用旧 pane ID；同一原命名空间的真实空 pane 清单确认不存在旧执行，再从新 Muster 控制 pane 经原 attempt 的 reclaim CLI 撤销、回收。原 attempt/worktree/历史/布局保留。`reclaim-old-01/result.json` 为 PASS，不曾对旧 attempt 重新投递。

新 `live_run.py --existing-state` 在原 ready task 上发起新 attempt，先核对仓库、基线与冻结 oracle/instructions，保留原事件前缀，不新建第二个 task 数据库。缺失该参数的合同红态在 `red-reuse-state.json`；真实新 run 已到 waiting_submit、fence=2，但全程绿态尚被权限门阻断。runtime 子目录随完整输出路径唯一命名，旧固定目录冲突已修复，旧目录不删除。

第二次暂停请求见 [APPROVAL-REQUEST-02.md](APPROVAL-REQUEST-02.md)。当前是真实 Git 暂存权限对话，不是目录信任；主控原许可明确不覆盖任何其他权限请求。未输入任何选项，未改变沙箱、添加 approval rule 或把用户 config/rules 复制进隔离 home。task=claimed、run=paused；当前 server 和 blocked worker pane 保留，隔离 Codex home 按许可已删除。第一项请求、原始 UI 与 server 退出材料仍保留在 APPROVAL-REQUEST.md / final-runtime-01 中，不当作当前 live 状态。

真实 run 仍未完整通过，fresh-context 独立只读审查尚未执行；不能复用 T-027 审查。取得本次额外 Git 权限许可后，按主控裁定处理当前 attempt，再完成真实 submit、独立 oracle、CAS、回收，冻结全部证据做一次审查并记录模型、冻结提交。

根 README、MAP、AGENTS、CONTEXT 未修改。`project_map.py status` 结构问题为 0，当前只报告 README stale。README 需写 MUSTER_BIN、live_muster.py、当前真实 run 边界；README 的 Covers 需替换已删除的 live_herdr.py。worker 按任务书交给主控处理。此报告是 worker 自查与证据交接，不是当时的独立监控。
