# T-077 r3 C2 尾注失败：只读诊断

2026-10-13，回应主控 #87。**INCOMPLETE**。r3 已观察并预留 4/4；用户要求“再不过就停下报告，不自动追加”。本轮新增真实回合 0，没有准备新启动，没有改 C2、原失败、门禁状态或产品代码。

## C2 原文与逐项差异

C2 为 `8b94d92812d0f8667f7d44dcbc178d9b343e2f8c`。原始读回为 `real-conflict-03/attempt-2/command-output/00275.stdout.bin`，对应 `commands.jsonl` 的命令 275（git show -s --format=%B，exit 0）。逐字节副本为 `real-r3-diagnosis-02/C2-message.txt`：

```text
Preserve summary unit while adding mean_ms

A2A-Fence: 2
A2A-Spec-Rev: 1
A2A-Task: T-077-12
A2A-Attempt: 3d5237d9-cc68-47a7-a2ff-9a5448febb00
A2A-Session: 4608635c-7a00-475d-9024-acd1866eabda
A2A-Role: worker
A2A-Tool: codex-cli 0.162.1
A2A-Model: gpt-6.1-sol
A2A-Effort: xhigh
A2A-Native-Session: 01a135c8-fdc4-7b62-9c70-5e7726cd9f6e
A2A-Launch: 9b06963e-5718-4286-9dd3-921591a3b339
```

| 字段 | expected | 实际比较 |
| --- | --- | --- |
| A2A-Task | T-077-12 | 完全相同，1 项 |
| A2A-Attempt | 3d5237d9-cc68-47a7-a2ff-9a5448febb00 | 完全相同，1 项 |
| A2A-Session | 4608635c-7a00-475d-9024-acd1866eabda | 完全相同，1 项 |
| A2A-Role | worker | 完全相同，1 项 |
| A2A-Tool | codex-cli 0.162.1 | 完全相同，1 项 |
| A2A-Model | gpt-6.1-sol | 完全相同，1 项 |
| A2A-Effort | xhigh | 完全相同，1 项 |
| A2A-Native-Session | 01a135c8-fdc4-7b62-9c70-5e7726cd9f6e | 完全相同，1 项 |
| A2A-Launch | 9b06963e-5718-4286-9dd3-921591a3b339 | 完全相同，1 项 |
| A2A-Fence | 无此约定字段 | 多余，值为 2 |
| A2A-Spec-Rev | 无此约定字段 | 多余，值为 1 |

缺失 **0**，值不同 **0**，重复 **0**，多余 **2**，总共 **11** 项。失败是 `len(fields)==9` 不成立；不是新 attempt 的 Task/Attempt/Session/Launch/Native-Session 值错。expected 来自本次启动、当前 attempt 身份及已观察到的原生 UUID，与九项规范对应，未根据提交原文反推。

## 归因

直接来源是被测 worker 自己的提交命令。`fixture-artifacts.tar.gz` 中：

`codex-home/sessions/2026/10/13/rollout-2026-10-13T11-02-07-01a135c8-fdc4-7b62-9c70-5e7726cd9f6e.jsonl`

ordinal 73、2026-10-13T15:04:24.783Z 的 custom_tool_call，交付 turn `01a135c8-fe72-7163-b329-1cafc90eb477`，明确执行了：

```text
git commit -m 'Preserve summary unit while adding mean_ms'
  --trailer 'A2A-Task: T-077-12'
  --trailer 'A2A-Attempt: 3d5237d9-cc68-47a7-a2ff-9a5448febb00'
  --trailer 'A2A-Session: 4608635c-7a00-475d-9024-acd1866eabda'
  --trailer 'A2A-Fence: 2'
  --trailer 'A2A-Spec-Rev: 1'
  --trailer 'A2A-Role: worker'
  --trailer 'A2A-Tool: codex-cli 0.162.1'
  --trailer 'A2A-Model: gpt-6.1-sol'
  --trailer 'A2A-Effort: xhigh'
  --trailer 'A2A-Native-Session: 01a135c8-fdc4-7b62-9c70-5e7726cd9f6e'
  --trailer 'A2A-Launch: 9b06963e-5718-4286-9dd3-921591a3b339'
```

这是一次独立 Git 命令，排版仅为阅读；完整原始工具输入保存在 `real-r3-diagnosis-02/diagnosis.json`。两个额外字段不是生产 hook 的字段：`workbench/hooks/hook.py:add_trailers` 只声明九项；launch-record.json 的新 attempt/session/launch 环境也正确。worker 同时手写了九个正确值，因此最终提交正确不能单独证明九项全由 hook 生成；本次没有观察到 hook 串身份的证据。

夹具九项 expected 符合 `native-cli-orchestration-2026-10-10.md` 第 8 节的列举，亦与现有 gate 的闭合字段检查一致：`workbench/src/gates/core.ts:1814` 起的 checkTrailers 只接受九种 A2A 字段，每项一个值，否则 invalid_trailers。Fence/spec_rev 是交付请求的身份字段，不在提交尾注这九项里。

故本次属于**被测 worker 添加不受支持字段的交付错误**，不是已确认的产品跨 attempt 尾注身份缺陷，也不是夹具期望写错。门禁的 submit 只冻结候选；尾注检查属于 verify，提交状态不意味着尾注已通过。按当前源码，若随后 verify C2，会因额外字段报 invalid_trailers；这是源码推论，本轮未调用 verify 来补跑原实验。

没有通过删除字段、放宽断言或改变门禁来把真实失败改成通过。若要让 hook 自动删掉所有额外 A2A 字段，或允许 Fence/Spec-Rev，则会改变现有写入/验收边界，需要另作决定；不作为本轮“修复”执行。主控 #87 的“产品缺陷→受控红/修复/绿/变异体”条件本次未成立，未开展该分支。

## 已到达的流程与未到达的流程

| 阶段 | 原始证据与结论 |
| --- | --- |
| 第一真实 worker 交付 | C1=`929efcc2698ad35960a65302295d90d21e684f1f`，旧 launch `e9cf7727-772d-41db-bd76-e71ffc2d7e93`；relay_processed 586 为 ok=true |
| 真正文本冲突 | conflict-reply.json：verification `e225af05-4fed-4d05-9c88-313e635e20cb`、G=`2254ae38f92ec81dd382f0ddeee3c620ddbb2745`、M=null、merge exit 1；src/summary.py 有三阶段未合并项和冲突 diff，state=merge_failed |
| 旧会话结束与替换 | orchestration 644 native_session_ended、654 pane_archived；gate 119 conflict_worker_replaced。新 attempt `3d5237d9-cc68-47a7-a2ff-9a5448febb00`，fence 2、base=G、conflict_source 指向上述 verification |
| 新 worker 整理并显式重交 | C2 真实存在；gate 132 submitted，task.state=submitted、candidate_commit=C2。其正确的新原生身份已经绑定 |
| 同编号转交成功 | orchestration 1294 relay_processed，key=`id:9b06963e-5718-4286-9dd3-921591a3b339:delivery`、ok=true。与旧 launch 的 delivery 是两个请求；没有出现旧的全库 request_id 冲突 |
| 两个新回合结束 | a2 两个根 task_started/turn_context，均 sol/xhigh；Stop 1292、1328，随后 pane_idle 1296、1330。r3 总计 4 个根回合 |
| 尾注失败 | wait_receipt 在第 187 行抛出 AssertionError；receipt-boundary.json 尚未写出。原 run.json、traceback 和命令输出原样保留 |
| C2 verify/integrate | **未到达**。当前 verification=null、integration_intent=null；库中只有旧 C1 的一个 merge_failed verification，没有 C2 验收行、verified 或 integrated 事件 |

同一个 home 的两个归档根日志各有自己的 UUID/cwd。事后逐字节比较旧日志与 attempt-1/original-rollout.jsonl 一致，结果保存在诊断 JSON；这是本次只读诊断补充的事实，不补称为原 runner 在失败后继续通过了 history-isolation 或集成检查。

`run.json` 为 INCOMPLETE，observed_total_root_turns=4、isolated_home_removed=true。r3 4 回合预算已用尽；含 r1 与 r2，实际观察累计 9、保守占位累计 10。本轮没有启动模型、改账、重开 home 或操作进程。完整冲突验收与独立审查仍未完成。

## 重新生成诊断

在本 worker worktree 执行，新输出目录不得已存在：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/diagnose-real-r3.py --output /tmp/t077-r3-diagnosis-replay
```

该 reader 只读原始命令输出、归档和 immutable SQLite 快照，不执行 Git 写操作或门禁。第一次临时 reader 把 different 的空字典与空列表比较，出现 reader AssertionError；已仅修类型比较，原错误留在 `real-r3-diagnosis-01/reader-error.txt`，新输出改为 `real-r3-diagnosis-02`。该临时错误不算产品红态，也没有覆盖真实失败。
