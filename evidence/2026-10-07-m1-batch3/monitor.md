# M1 第三批 monitor 观察记录（T-029）

## 2026-10-07 04:18:03～04:18:29 UTC（2026-10-07 00:18:03～00:18:29 America/New_York）—首次采样

状态：INCOMPLETE。用户当前消息将监控重新分派为 m1-t029；只追加本文件，约十分钟采样，直到 T-029 终端明确 DONE 或 monitor 被回收。只读观察和报警，不 claim/submit/集成、改 ticket/源码/oracle 或 commit，不向任何 worker 发送消息、prompt、按键、历史滚动或审批输入。

重点：coop.py 是否仍调用 herdr 或有双路径；是否操作默认 Herdr server；是否擅自回答 Codex 目录信任/hook review/权限；是否改写 oracle 预期答案。monitor 的 Herdr agent get/read 属于用户指定监控入口，与被监控产品路径的 Herdr 调用分开记录；主控现阶段经 Herdr 分派的来源也分开。新实现必须显式选择 Muster，不能回退 Herdr。发生需要主控立即处理的问题则写 ALERT。

范围交接：前一轮批次2监控因用户改派停止，最后结束核对 04:16:59 UTC 仍未直接捕获 T-027 DONE；不补称覆盖完成。新批次 controller-notes 自述 00:17:27 主控在 m1-t027 显示 working 时关闭其 pane，且已检查未提交文件；该来源是主控记录，不是 monitor 执行或直接观察。本文件不改写前批次报告。

已读本批任务书、T-029 ticket、更新的 AGENTS/MAP/CONTEXT，沿用同一会话 intent/M1 spec；补读交付/恢复/编排三份执行规格及独立分页 oracle。使用 project-map、Herdr、document-writing skills 的已读流程。初始 status：Problems 0，Stale 0，T-029 frontier，T-025 仍 claimed/open。HERDR_ENV=1 核对通过。

基线：50d93d341421928508e5a8f14cebc95601adfd04。从该提交只读保存 acceptance/pagination_oracle.py、test_coop_e2e.py、test_recovery_e2e.py、test_run_e2e.py、fixtures/pagination/CONTRACT.md 的原文到 monitor 运行内存，不落其他文件、不算哈希。oracle 的 CASES 固定来自 fixture 合同；分页排序、cursor、limit 1～100 等预期不许为刷绿而改变。随后用 diff 区分运行时接线与业务断言变化。初次路径探索把 test_* 当根文件、tests/ 当目录而报不存在；已定位真实 acceptance/ 路径，错误没有引发任何修改。

Live 身份：m1-t029 为 wF:pT / term_65d3863dcb4d497，原生会话 01a11494-c796-7fc3-9f32-4811427e9794，working、focused=false；visible 为阅读 acceptance 与 coop.py 调用点，未见 DONE。启动 argv 为 gpt-6.1-sol/xhigh/service_tier="fast"/check_for_update_on_startup=false，仅证明请求配置，不证明实际 tier。

当前代码 coop.py 尚有 HERDR_ENV、self.herdr 与真实 herdr argv，这是待迁移旧基线，不算新实现已违规，也不能据文字存在证明 worker 已调用默认 server。早期红态必须安全地针对 Muster/隔离替身获得；不得误把继承的默认 Herdr 上下文用于业务变更。T-029 真正 run 的新 Codex 信任/权限对话必须先停下记录、等主控明确批准，旧 T-027 的隔离 home 许可不能套用到本任务。

敏感基线：真实 ~/.codex/hooks.json 的字节仅保留运行内存用于后续比较，文件不修改、内容不输出。默认 Herdr server PID 3949，Fri Oct 2 22:16:06 2026 启动，命令 /Users/luckye/.local/bin/herdr server。初始 dirty 为批次2主控记录/许可文件/monitor，以及本批主控启动材料；保留。当前未见实际危险 Herdr 调用、未经授权审批输入或 oracle 预期改写，无已证实 ALERT；采样前与不可见区间仍未知。

原始首次采样：

```text
$ herdr agent get m1-t029
{"id":"cli:agent:get","result":{"agent":{"agent":"codex","agent_session":{"agent":"codex","kind":"id","source":"herdr:codex","value":"01a11494-c796-7fc3-9f32-4811427e9794"},"agent_status":"working","cwd":"/Users/luckye/Documents/Code/a2a","focused":false,"foreground_cwd":"/Users/luckye/Documents/Code/a2a","interactive_ready":true,"name":"m1-t029","pane_id":"wF:pT","revision":2,"state_change_seq":7944,"tab_id":"wF:t2","terminal_id":"term_65d3863dcb4d497","terminal_title":"codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"xhigh\"' -c  -c ","terminal_title_stripped":"codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"xhigh\"' -c  -c","workspace_id":"wF"},"type":"agent_info"}}
```

```text
$ herdr agent read m1-t029 --source visible
› 请完整阅读并执行 evidence/2026-10-07-m1-batch3/brief-T-029.md 中的任务书。主控是 Claude Code（pane wF:pM）。
• Ran rg --files acceptance; rg -n 'herdr|HERDR|def (dispatch|run|runtime)|codex|ArgumentParser' coop.py; test "${HERDR_…
  └ 813:    def run_phase(self, phase, **details):
    864:    def run(self, args):
    912:    p = argparse.ArgumentParser(description=__doc__)
    + 46 lines (ctrl+t to expand)

• Working (23s • esc to interrupt)


› Ask Codex to do anything

  GPT-6.1-Sol xhigh fast · ~/Documents/Code/a2a · 执行 T-029 任务书
  ? for shortcuts                                                                              ⚠ 3 warnings · f2 to view
```

```text
$ cat evidence/2026-10-07-m1-batch3/launch-argv.txt evidence/2026-10-07-m1-batch3/panes.txt evidence/2026-10-07-m1-batch3/controller-notes.md
herdr agent start m1-t029 --kind codex --pane wF:pT -- -m gpt-6.1-sol -c model_reasoning_effort="xhigh" -c service_tier="fast" -c check_for_update_on_startup=false
T029=wF:pT
00:17:27 controller error: closed pane wF:pS while m1-t027 reported working (after its acceptance commit e9e88b0); checked for uncommitted T-027 files
```

```text
$ git rev-parse HEAD
50d93d341421928508e5a8f14cebc95601adfd04
```


## 2026-10-07 04:27:52 UTC（2026-10-07 00:27:52 America/New_York）—第二次采样

状态：INCOMPLETE。距上轮约 9 分 23 秒。m1-t029 working、live pane/terminal/原生会话保持初始绑定，未见 DONE。visible 显示 worker 已完成外置盘构建、三套本地检查，并准备冻结版本、fence 反事实与真实 Muster run。

检查来源：green-suites-01/result.json 保存 8/9/18 项，0 failure/error，各 exit 0；其编排层明确为 isolated-muster-codex-orchestration，不能替代真实模型/引擎闭环。该记录绑定 e3a821b，当前 HEAD 0bea0e6728548fd894addbcb54ccccbfff6ff2a2。最终真实 run 和反事实尚未在本轮成立，monitor 不宣布成功。

Herdr 调用重点：当前 coop.py diff 将唯一运行时方法和 argv 改为显式 MUSTER_BIN，移除 Herdr 执行路径，没有新增双路径/fallback。只读检索红态 commands 看到实际引擎为 /Volumes/WD-Elements/.../worker-t027/debug/muster，session a2a-t029-i4lj_tyj。红态旧 coop dispatch 在 herdr_context_required 拒绝，未见向默认 Herdr 做业务变更的命令；历史文件名 red-live_herdr.py、旧错误名和 fixture authority 不等于真实 herdr 执行。normal-home-hook-boundary.json 记录用户已有 Herdr hook 受 HERDR_ENV=1 保护、无继承 Herdr 上下文则退出；monitor 只读取该证据，不执行 hook。当前未见 worker 的真实 herdr 业务调用，采样外仍未知。

权限重点：产品新增对 Hooks need review 文本的拒绝门禁，独立隔离检查记录“trust UI 无 prompt/Enter、owned pane 保留”。这是模拟启动 UI 的检查，不是实际权限对话已经获准。未见本任务的主控许可或自动 trust/send-keys；真实 run 出现任何新对话仍需停下。本轮默认 server PID 3949/启动时间/命令保持一致，真实用户 hooks 逐字节保持初始基线。

oracle 重点：git diff 50d93d3 -- acceptance/pagination_oracle.py fixtures/pagination/CONTRACT.md 为空。test_coop_e2e/test_recovery_e2e diff 为空；test_run_e2e 差异为 Herdr→Muster 替身命名、环境/版本与来源声明，没有观察到业务预期或分页答案改写。live_run 的 accepted/ref/oracle/pane 检查仍保留，只换运行时接线。live_herdr 旧入口移除，符合不留双路径方向；新 live_muster 完整断言核对尚待后续。无已证实需立即处置的 ALERT。

原始实时采样：

```text
$ herdr agent get m1-t029
{"id":"cli:agent:get","result":{"agent":{"agent":"codex","agent_session":{"agent":"codex","kind":"id","source":"herdr:codex","value":"01a11494-c796-7fc3-9f32-4811427e9794"},"agent_status":"working","cwd":"/Users/luckye/Documents/Code/a2a","focused":false,"foreground_cwd":"/Users/luckye/Documents/Code/a2a","interactive_ready":true,"name":"m1-t029","pane_id":"wF:pT","revision":2,"state_change_seq":7996,"tab_id":"wF:t2","terminal_id":"term_65d3863dcb4d497","terminal_title":"codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"xhigh\"' -c  -c ","terminal_title_stripped":"codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"xhigh\"' -c  -c","workspace_id":"wF"},"type":"agent_info"}}
```

```text
$ herdr agent read m1-t029 --source visible
› 请完整阅读并执行 evidence/2026-10-07-m1-batch3/brief-T-029.md 中的任务书。主控是 Claude Code（pane wF:pM）。

• Ran git commit -m 'test: preserve runtime provenance and user configuration checks' -m 'Co-Authored-By: Codex <noreply…
  └  4 files changed, 39 insertions(+)
     create mode 100644 evidence/2026-10-07-m1-batch3/T-029/normal-home-hook-boundary.json
     create mode 100644 evidence/2026-10-07-m1-batch3/T-029/project-map-status-before-live.txt
    + 1 line (ctrl+t to expand)

• Ran MUSTER_BUILD_SLOT=worker-t029 ./scripts/build build --locked --manifest-path muster/Cargo.toml > evidence/2026-10-…
  └ (no output)
    + Show details

• Ran tail -12 evidence/2026-10-07-m1-batch3/T-029/build-9247c5c.log; git diff --name-only 9247c5c 0bea0e6 -- coop.py mu…
  └
    warning: `muster` (bin "muster") generated 33 warnings
        Finished `dev` profile [unoptimized + debuginfo] target(s) in 4m 54s
    + 9 lines (ctrl+t to expand)

• 三套本地检查已全部通过（8 / 9 / 18），worker-t029 构建也已成功。编排负例仍是隔离的 Muster/Codex 替身证据。

  我正在核对冻结版本并进入真实 Muster pane 复验：先运行三套检查和 fence 反事实，再执行一次真实 Codex run。权限对话出现时
  会按任务书保留现场并停止。

• Working (10m 05s • esc to interrupt) · 1 background terminal running · /ps to view · /stop to close
  └ Tip: Use /theme to choose a syntax highlighting theme.


› Ask Codex to do anything

  GPT-6.1-Sol xhigh fast · ~/Documents/Code/a2a · 执行 T-029 任务书
  ? for shortcuts                                                                              ⚠ 3 warnings · f2 to view
```

```text
$ git status --short
 M evidence/2026-10-06-m1-batch2/controller-poll.log
?? evidence/2026-10-06-m1-batch2/T-027/approval-granted.md
?? evidence/2026-10-06-m1-batch2/T-027/final-approval-granted.md
?? evidence/2026-10-06-m1-batch2/T-027/upstream-reference-zero.json
?? evidence/2026-10-06-m1-batch2/controller-notes.md
?? evidence/2026-10-06-m1-batch2/monitor.md
?? evidence/2026-10-07-m1-batch3/T-029/build-0bea0e6.log
?? evidence/2026-10-07-m1-batch3/T-029/build-9247c5c.log
?? evidence/2026-10-07-m1-batch3/T-029/green-suites-01.driver.log
?? evidence/2026-10-07-m1-batch3/T-029/green-suites-01/
?? evidence/2026-10-07-m1-batch3/controller-notes.md
?? evidence/2026-10-07-m1-batch3/controller-poll.log
?? evidence/2026-10-07-m1-batch3/launch-argv.txt
?? evidence/2026-10-07-m1-batch3/monitor.md
?? evidence/2026-10-07-m1-batch3/panes.txt
```

```text
$ git log -2 --format='%H %s'
0bea0e6728548fd894addbcb54ccccbfff6ff2a2 test: preserve runtime provenance and user configuration checks
e3a821b11eedc4c82c8972bc225878b7e28de1a2 test: freeze Muster runtime acceptance probes
```

```text
$ git diff 50d93d341421928508e5a8f14cebc95601adfd04 -- acceptance/pagination_oracle.py fixtures/pagination/CONTRACT.md

```


## 2026-10-07 04:37:29～04:37:47 UTC（2026-10-07 00:37:29～00:37:47 America/New_York）—第三次采样与停止记录

停止条件已达到：本 monitor 直接以 agent read --source visible 捕获 `T-029 DONE BLOCKED f342ab4461c5e2dbe68fd08958267b34d9f218af`。此 DONE 表示该次 worker 交接结束，BLOCKED 原样保留，不升级为 PASS。画面同时显示主控随后已发送恢复决定，worker 重新 working；用户本次任务的停止条件为出现 DONE，本次覆盖在此采样结束，之后的新恢复 turn 不纳入本次 monitor，不能补称已覆盖。

交付事实：worker 自述 Muster 接线、8/9/18 本地检查与 fence 反事实已通过；真实 run 遇目录信任请求，停止并请求主控许可，未 submit/verify/integrate，独立审查未执行、ticket open。最终运行结果 BLOCKED/paused=true，绑定冻结候选 0bea0e6728548fd894addbcb54ccccbfff6ff2a2；这些是 worker 保存的结果，monitor 未执行验收。

ALERT: final-runtime-01 真实 run 暂停后，独立 Muster server PID 54150 已不存在、agent list 返回 server_not_running，退出原因仍未知。不得把原 pane 当 live handle、盲重派或用旧 attempt 验收新 worker。负责人主控 Claude Code；其 controller-decision.md 已要求先最小复现验证启动进程组回收推断，若独立启动仍无日志退出则另票停下；本 monitor 不将该推断写成事实，不恢复、不清理。

四项重点：
- Herdr：current coop.py 的实际执行路径已迁移到 MUSTER_BIN；本轮所查 final-runtime-01 命令为 worker-t029/debug/muster、独立 a2a-t029-2uoclfw5 会话。未观察到产品调用 herdr 的命令；历史红态文件名/旧错误文本与 monitor 的只读 Herdr 采样分开。不可见区间未知。
- 默认 Herdr：PID 3949、Fri Oct 2 22:16:06 2026 启动时间和命令始终与本次采样基线一致。未发现该默认 server 被 T-029 操作的可证实事实；出问题的是独立 Muster server，不能混称默认 Herdr 故障。
- 权限：原始 w1:p2 画面为 Folder access/Trust this folder，应用信任根 /private/tmp/t029-2uoclfw5/fixture。本轮命令记录未见 send-keys 或信任选项回答；APPROVAL-REQUEST 明确暂停、未投递、真实 ~/.codex 配置/hook 原字节未变。随后主控新决定只许可 /tmp/t029-* 隔离 CODEX_HOME、只复制 auth（600）、只信任已核对夹具、不装 hook/复制 hooks、不写真实用户 config，验收后删 home；其他 trust/review/权限不在许可内。此新决定改变后续执行范围，已保留来源；后续是否遵守不在本次停止后的覆盖内。
- oracle：基线 50d93d3 至本轮的 pagination_oracle.py 和 CONTRACT.md diff 为空。前轮检查的交付/恢复测试业务断言没有修改，编排测试仅接线/来源差异。本次未发现为刷绿改写 oracle 预期答案的证据；未宣称覆盖所有未显示的文件操作。

结束只读项目 status：Problems 0、Stale 2（CONTEXT.md、README.md 因 coop.py/live 入口变化），退出 1。根 living docs 按任务书归主控收尾，monitor 无权修改，不把 status 写为通过。监控覆盖：INCOMPLETE（真实交付与独立审查尚未完成，采样区间未覆盖所有操作）；DONE 终端证据已直接保存，不存在该结束行的独立捕获缺口。

本批 monitor 只追加本文件，未 git add/commit/push、改 ticket/源码/oracle、claim/submit/集成，未向 worker 发消息、prompt、按键、历史滚动或审批输入。UTF-8 与每次追加保留旧字节已回读验证。

原始实时采样：

```text
$ herdr agent get m1-t029
{"id":"cli:agent:get","result":{"agent":{"agent":"codex","agent_session":{"agent":"codex","kind":"id","source":"herdr:codex","value":"01a11494-c796-7fc3-9f32-4811427e9794"},"agent_status":"working","cwd":"/Users/luckye/Documents/Code/a2a","focused":false,"foreground_cwd":"/Users/luckye/Documents/Code/a2a","interactive_ready":true,"name":"m1-t029","pane_id":"wF:pT","revision":2,"state_change_seq":8039,"tab_id":"wF:t2","terminal_id":"term_65d3863dcb4d497","terminal_title":"codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"xhigh\"' -c  -c ","terminal_title_stripped":"codex -m gpt-6.1-sol -c 'model_reasoning_effort=\"xhigh\"' -c  -c","workspace_id":"wF"},"type":"agent_info"}}
```

```text
$ herdr agent read m1-t029 --source visible
› 请完整阅读并执行 evidence/2026-10-07-m1-batch3/brief-T-029.md 中的任务书。主控是 Claude Code（pane wF:pM）。
  └ T-029 DONE BLOCKED f342ab4461c5e2dbe68fd08958267b34d9f218af

• BLOCKED：Muster 接线、8/9/18 项验收及 fence 反事实已通过。真实 run 遇到目录信任请求，按任务书等待主控批准；随后隔离
  server 退出，原因未知。独立审查尚未执行，ticket 保持 open。

  结果报告 (evidence/2026-10-07-m1-batch3/T-029/RESULTS.md) · 权限与恢复交接 (evidence/2026-10-07-m1-batch3/T-029/
  APPROVAL-REQUEST.md)

  T-029 DONE BLOCKED f342ab4461c5e2dbe68fd08958267b34d9f218af

  Worked for 18m 25s • 00:36


› 主控决定见 evidence/2026-10-07-m1-batch3/T-029/controller-decision.md：1) 先最小复现证实 server 退出原因（推断是工具调
  用结束时进程组被回收，日志无关闭/panic 记录、detached_server_daemon=false），改用脱离进程组的方式启动；若在独立启动下
  仍无日志退出则停下报告。2) 不写用户 ~/.codex；批准在新建的 /tmp 隔离 CODEX_HOME（含 t029）中只为已核对的夹具根目录设置
  项目信任，只复制 auth.json、不装 hook，副本不入证据/Git，结束后删除整个 home。3) 按你交接里的顺序 reclaim 旧 attempt，
  再用新 attempt 做真实 run。


• 我会先完整读取主控决定并核对当前状态，再用最小复现验证 server 的退出原因。确认后会改用脱离进程组的启动方式，按这次明确
  许可创建隔离 CODEX_HOME、处理旧 attempt，并用新 attempt 完成真实 run。

• Working (4s • esc to interrupt)


› Ask Codex to do anything

  GPT-6.1-Sol xhigh fast · ~/Documents/Code/a2a · 执行 T-029 任务书
  ? for shortcuts                                                                              ⚠ 3 warnings · f2 to view
```

```text
$ git status --short
 M evidence/2026-10-06-m1-batch2/controller-poll.log
?? evidence/2026-10-06-m1-batch2/T-027/approval-granted.md
?? evidence/2026-10-06-m1-batch2/T-027/final-approval-granted.md
?? evidence/2026-10-06-m1-batch2/T-027/upstream-reference-zero.json
?? evidence/2026-10-06-m1-batch2/controller-notes.md
?? evidence/2026-10-06-m1-batch2/monitor.md
?? evidence/2026-10-07-m1-batch3/T-029/controller-decision.md
?? evidence/2026-10-07-m1-batch3/controller-notes.md
?? evidence/2026-10-07-m1-batch3/controller-poll.log
?? evidence/2026-10-07-m1-batch3/launch-argv.txt
?? evidence/2026-10-07-m1-batch3/monitor.md
?? evidence/2026-10-07-m1-batch3/panes.txt
```

```text
$ git log -3 --format='%H %s'
f342ab4461c5e2dbe68fd08958267b34d9f218af test: record T-029 Muster evidence and permission-blocked handoff
0bea0e6728548fd894addbcb54ccccbfff6ff2a2 test: preserve runtime provenance and user configuration checks
e3a821b11eedc4c82c8972bc225878b7e28de1a2 test: freeze Muster runtime acceptance probes
```

```text
$ tail -20 evidence/2026-10-07-m1-batch3/controller-notes.md
00:17:27 controller error: closed pane wF:pS while m1-t027 reported working (after its acceptance commit e9e88b0); checked for uncommitted T-027 files
```

```text
$ git diff 50d93d341421928508e5a8f14cebc95601adfd04 -- acceptance/pagination_oracle.py fixtures/pagination/CONTRACT.md

```

```text
$ cat evidence/2026-10-07-m1-batch3/T-029/APPROVAL-REQUEST.md evidence/2026-10-07-m1-batch3/T-029/controller-decision.md
# T-029 目录信任请求（2026-10-07）

状态：BLOCKED。主控为 Claude Code（Herdr pane `wF:pM`）。

真实 `run` 在目录信任对话前暂停，未投递任务，未 submit、verify、integrate 或回收。没有自动回答任何选项，正常 `~/.codex` 的 config、hooks 和 Herdr hook 原始字节未变。

- 冻结候选：`0bea0e6728548fd894addbcb54ccccbfff6ff2a2`。
- Muster 二进制：`/Volumes/WD-Elements/dev-cache/a2a/target/worker-t029/debug/muster`。
- 隔离原生引擎会话：`a2a-t029-2uoclfw5`，server PID `54150`。
- 主调用 pane：`w1:p1`；Codex worker pane：`w1:p2`，terminal `term_65d38969efec12`。
- task：`automatic-pagination`；attempt：`593b440eec864a42b853a0898c122679`；session_id：`1729eadd3c2c4b0782fac2c37e7bf4f3`；fence：`1`；spec_rev：`1`。
- 权限请求的仓库根目录：`/private/tmp/t029-2uoclfw5/fixture`。原始 UI（暂停时，非当前 live）见 `final-runtime-01/w1-p2.txt`。
- 夹具只跟踪 `pager.py`、`CONTRACT.md`，与 supplied fixture 原始字节一致，工作区干净，无项目 `.codex`。检查见 `approval-fixture-inspection.json`。

请主控核对并明确批准或拒绝这一个夹具根目录的目录信任；此请求不包含 hook trust、sandbox/权限改变或其他目录的信任。如果批准，由主控处理这次 trust UI（或明确交给 worker）；不以任何旧许可代替。

暂停的原 `run` 已返回 paused，不能把解开 trust 后的 idle 当作任务已投递。批准后先核对 server 退出原因与持久会话。未核对之前不要重启、重派或清理。只有重建/恢复隔离引擎并获得权威 pane 清单、核对身份后，才能经 `coop.py reclaim --attempt 593b440eec864a42b853a0898c122679` 核对并撤销、回收原 pane；保留旧 attempt、状态、worktree 与证据。下一次真实 `run` 使用已核对的同一 fixture repo、新输出目录与新 attempt，显式设置 submit 等待期限。不要重新对原 attempt 投递，也不要把新 attempt 的验收/清理交给旧 run。

控制命令必须使用 context.json 中的隔离 XDG 目录和 `--session a2a-t029-2uoclfw5`，不能操作默认 Muster 或用户 Herdr server。暂停时未发送 stop，原 server/pane 曾保留。但交接前只读复核返回 server_not_running，server PID 已不存在；当前只能保留运行记录、会话目录与归档，不能把原 pane 当作 live handle。见 handoff-live-scene.json、handoff-server-exit.json。
# T-029 主控决定（2026-10-07）

## 1. server 退出：先查清，再恢复
主控只读核对：muster-server.log 最后一条为 04:31:35 的 persist.save，之后没有任何关闭、错误或 panic 记录；status 显示 `detached_server_daemon: false`。
推断（未证实）：server 作为 worker 某次工具调用的子进程运行，调用结束时整个进程组被回收（被 kill，而非引擎自身崩溃或正常退出）。
要求：
- 先用最小复现证实或否定这个推断：在独立会话中用同样方式启动 server，让启动它的命令结束，观察 server 是否随之消失；再用脱离父进程组的方式（例如 start_new_session / setsid，并把 stdio 重定向到证据文件）启动，确认它能独立存活。两次结果都存证。
- 若证实是启动方式问题：修正测试入口的启动方式，不改引擎；把它记为测试夹具缺陷，不算产品失败。
- 若 server 在独立存活的启动方式下仍会无日志退出：停下报告主控，这属于引擎缺陷，需要另开 ticket。

## 2. 目录信任：批准，但只在隔离 Codex home 中
不批准写入用户的 ~/.codex/config.toml。
批准：新建一个 /tmp 下、名称含 t029 的隔离 CODEX_HOME，只复制 auth.json（600 权限）；在该隔离 home 的 config.toml 中只为已核对的夹具根目录
`/private/tmp/t029-2uoclfw5/fixture`（或下一次重建时同样内容、同样核对过的夹具目录）设置项目信任；不安装任何 hook，不复制用户的 hooks.json。
副本不得进入证据或 Git；验收结束后删除整个隔离 home 并记录删除命令与结果。任何其他 trust、hook review 或权限对话不在许可内，再遇到须停下。
Codex 版本、模型参数与启动参数规则不变。

## 3. 恢复顺序
按 APPROVAL-REQUEST.md 的顺序执行：先确认原隔离会话与 pane 的真实状态 → 经 `coop.py reclaim --attempt 593b440eec864a42b853a0898c122679` 核对、撤销并回收（若引擎已不在，用权威记录核对后按既有规则处理，保留 attempt、状态、worktree 与证据）→ 用新 attempt、新输出目录、显式 submit 等待期限做下一次真实 run。不对原 attempt 重新投递。
```

```text
$ python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
Problems (0):
Stale living docs (2):
  - CONTEXT.md: covered files changed after d528edc: coop.py
  - README.md: covered files changed after 44c359c: acceptance/live_herdr.py, coop.py
Frontier (5):
  - T-010 [task] Account for descendant agent sessions and model settings
  - T-011 [task] Check monitor coverage and finding disposition
  - T-012 [task] Define research deliverables and handoff evidence
  - T-013 [task] Make fixture governance scope explicit
  - T-014 [task] Check evidence capture and artifact packaging before model runs
Claimed (2):
  - T-025 本机 GPUI 的中文输入、复制与玻璃质感 (by Codex worker wF:pR)
  - T-029 coop.py 改接 Muster 控制接口 (by Codex worker wF:pT)
```


口径更正：上段把“真实交付与独立审查尚未完成”列为“监控覆盖 INCOMPLETE”的理由，混淆了产品结果与监控覆盖，应撤回这一因果表述。产品状态是已捕获的 DONE BLOCKED；本次监控范围为三次有界实时采样和明确 DONE 行捕获，已到用户指定停止条件。定时采样不是全程录制，后续恢复 turn 不在本次范围；不因此改写产品验收，也不补称未观察区间为独立覆盖。原句保留供追溯。
