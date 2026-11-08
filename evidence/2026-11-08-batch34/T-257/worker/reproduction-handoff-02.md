# T-257：交主控运行真实入口复现

状态：INCOMPLETE。2026-11-08，按主控 #36 的答复编写专属测试，等待主控在有权限的环境中执行。旧 `RESULTS.md` 和首次沙箱拒绝证据不改写。本轮没有修改生产代码，没有启动真实夹具、后台或 Codex，也没有重试被拒的 `/private/tmp` 操作。

## 运行命令

工作目录必须是本 attempt 的 worktree：

```text
/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-257-1-a1
```

主控运行修前版本（下列摘要必须尚不存在；重复运行请换新文件名，不覆盖）：

```sh
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 workbench/tests/test_t257_codex_stop_continuation_e2e.py --revision 5c7df3a93019cea1a690194773d967bebb69a4ef --summary evidence/2026-11-08-batch34/T-257/worker/red-controller-01.json
```

不带参数时运行完整场景，使用当前工作区的产品源码。默认摘要在本票 worker 证据目录，文件名含 UTC 时间和 UUID；开始及结束都会打印 `SUMMARY=<绝对路径>`。`--summary` 拒绝已有文件，`--revision` 只切换临时副本里的产品源码。主控添加的 `workbench/node_modules` 链接保持原样，不提交、不清理、不安装新依赖。

## 探针与 oracle

期望值来自 T-257 的验收条目，不来自生产代码输出。既有 `scripted_claude.Fixture` 只负责真实后台、项目、终端角色和门禁，`t112_native_api` 只负责原生 Responses 协议。没有 fake pane，没有修改数据库或写入假的 rollout，没有 TS 依赖。测试中的 fixture 任务只发送四个真实 `status` 请求，不执行 verify/integrate、不声称通过交付质量串。

测试默认完整运行以下顺序：

1. 派出真实交互 Codex，隔离 HOME/CODEX_HOME，本地 Responses 接口，`requires_openai_auth=false`。没有复制用户配置或凭据；夹具的 Claude 路径设成 `/usr/bin/false`，不会启动 Claude。后台仍走产品 `daemon_start`，其 `transport.ts` 用 `detached: true` 脱离调用者进程组。
2. 第一次模型请求停在响应屏障中。核对真实领导进程、原生会话及 attempt 绑定，然后经真实门禁 reclaim，要求 `worker_working`。
3. 释放模型，让原生 CLI 依次执行四个门禁 `status` 命令，显式请求经首个真实 Stop 转交。
4. 只在临时产品副本的 `panes.ts` 启动参数位置，把原有 signal 命令包进观测脚本。脚本原样传入 stdin、调用原命令一次、保留 stdout/stderr/退出码；首次 Stop 在原命令返回后等待释放文件，最长四秒。原 hook 十秒超时、状态转换、门禁、权限检查均不改。观测脚本由 Python 文件内嵌生成，不是待移植的新依赖。
5. 测试从后台事件确认真正的门禁回执已经 `turn_submitted` 后释放 Stop。必须证明回执提交早于 `hook_release`；`hook_release` 是包装命令向 CLI 返回前的边界记录，后续真实 UPS 证明 CLI 已消费返回。不会把后台的 `request_result` 当作 CLI 收到 hook 返回的时间。
6. 要求真实 Codex 的第二个 UPS 与首轮使用同一 `turn_id`，且期间只有一次原生 `task_started`。回执响应停在第二个模型屏障中，再核对 reclaim 被 `worker_working` 拒绝，并通过真实 `pane_dispatch` 排入随机 UUID 消息；消息必须先留在队列。
7. 释放回执模型响应，要求同 turn 的第二个 Stop（`stop_hook_active=true`）、两个 Stop 的正常返回，以及原生 `task_complete`。检查窗格结束、随机消息恰好投递一次并原生完成、四个请求没有重复执行，最后 reclaim 成功。

摘要中的 `timeline` 保存后台 seq/time、UPS/Stop、原生开始/完成、回执粘贴/提交、pane 状态与 relay 结果；`hook_timeline` 保存 hook 进入、原 signal 返回、屏障释放及向 CLI 返回边界；`observed` 保存三次 reclaim 结果与关键 pane 快照。完整启动 argv 和版本也入摘要；环境变量和凭据不入摘要。

## 如何判定红态

预期修前结果是退出码 1、`status=FAIL`、`defect_reproduced=true`。摘要应同时证明：窗口与同 turn 续轮前提全部成立；真实原生回合已经完成；最终 pane 仍 busy、随机消息仍排队，最后 reclaim 的 error 是 `worker_working`。

预期失败断言包括 `continuation_stop_reaches_idle`、`queued_message_delivered_once`、`queued_message_native_complete`、`pane_settled_idle`、`completed_attempt_reclaimed`。两个工作中拒绝回收断言应通过。

环境、协议、身份绑定或调度前提不足时返回退出码 2、`status=INCOMPLETE`，保留诊断，不能把它当红态；没有自动重试。若没有命中同 turn 或四秒屏障窗口，先看时间线再调整探针，不能直接改生产代码。修后退出码 0、`status=PASS` 需要所有前提及业务断言都满足。

该脚本只有一个明确顺序的真实入口场景；后续实现前仍需按任务卡在真实模块上做有意义的 0～2 次事件顺序或带种子调度搜索，保存反例。当前没有执行搜索，也没有通过本测试证明所有身份、fence、操作锁或中断回归。

## 清理与当前检查

测试先记录文本诊断和本次目录的文件数、字节数、时间与结果，再删除本次 fixture（含临时源码、home、数据库及 hc 安装）和本 launch 记录指向的临时请求目录；共享依赖链接目标与共享 hc 缓存不删。若后台/core 清理无法确认，保留现场并将结果降为 INCOMPLETE，不删除目录。失败文本摘要始终保留。

当前已单独通过 Python 主脚本与内嵌 observer 的语法检查、JSONL 换行检查、插桩锚点检查和 `--help`；本回合开始的 project-map status 退出 0，Problems/Stale 均为 0。未运行真实入口。一次静态检查脚本误把 `git diff --no-index --check /dev/null <新增测试>` 的退出码 1 当作命令失败（stdout/stderr 都为空），导致当次汇总脚本的断言退出；这不是产品红态。后续汇总尝试在 `subprocess.run(...).communicate` 等待管道一直未返回，已 Ctrl-C 中断，退出 130；当时未打印步骤，不能确认是 help 还是 status 子命令。用于排查的 `ps -axo pid,ppid,etime,command` 被沙箱以 `operation not permitted: ps` 拒绝，退出 1，没有换工具绕过。上述事实保留于静态检查摘要；中断的汇总不能算通过。

完成真实红态后，请把本次摘要路径、退出码和具体序列交回原 worker；若主控试运行发现测试自身缺陷，先给出原始摘要。本 worker 将修订开发测试并保留失败记录，仍不碰冻结验收。收到缺陷专属红态前不修改生产行为；此阶段不发送完成 submit。

**Works**：新增专属真实入口脚本及精确运行步骤，静态检查可读；完整行为证据待主控运行。

**No regression**：生产代码、既有测试、冻结验收和旧证据未改；未运行产品回归。

**Risk / undo**：调度探针尚未实测，可能需要基于真实时间线修正；T-257 尚未修复。没有生产行为需要回退。额外目录改动：无。
