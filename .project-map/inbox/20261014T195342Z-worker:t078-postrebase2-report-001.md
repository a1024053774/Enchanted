---
from: "worker:t078-postrebase2"
to: "executor"
kind: "report"
reply_to: ""
refs: ["task:T-078-1", "commit:bf9bb9d75def72c7c74ef6389bcb82647a29a697"]
created_at: "2026-10-14T19:55:07.539175Z"
schema: 1
title: "T-078 第二次变基局部通过，交单一沙箱外回归阶段"
id: "20261014T195342Z-worker:t078-postrebase2-report-001"
---

# T-078 第二次变基后的夹具迁移与回归

当前局部检查 **PASS**；沙箱外入口回归与单角色真实 Claude 切片 **INCOMPLETE**。本轮没有启动供应商 CLI、API、Electron 或模型，没有改产品源码，也没有自行执行 Git 写入。

主控 #168 已完成有界变基：`bf9bb9d75def72c7c74ef6389bcb82647a29a697`，固定目标 `490de67d05a08ccf8a453a78694a106288579b47`，包含 T-080 与 T-083。原日志 `/private/tmp/t078-rebase-main-2-2gc_c6bb` 的十个文件已逐字节拷入 [execution](rebase-main-2/execution/COPY-RESULT.json)，原件保留。变基结果 PASS、无冲突，备份 `backup/t078-before-main-2-be6e0195102e` 保留。

目标是让 T-078 自建夹具使用当前任务卡契约，并检查这次变基影响的入口。验收条件是三个实际卡生成器通过当前 schema、当前打分和 T-083 契约通过、真实库／hook／窗口回归通过且自建后台退出。单角色 Claude 的收件箱转交、stop／ack、09B／09C 和整票验收另有入口与审批门槛，不用本轮局部检查代替。

## 迁移及红绿证据

三个实际卡生成器为 `test_t078_input_entry.py`、`test_t078_inbox_entry.py`、`run_t078_p1.py`。迁移前，前两个字典缺字段或模板保留空数组，被 T-080 当前生产 validator 拒绝；[红态](post-rebase-2-card-red/results.json) 3/3 INCOMPLETE、exit 1。原结果保留。

这三个卡现在都显式声明 `oracle_paths: ["value.txt"]`。该文件在各夹具建库时先写入并提交，输入与收件箱夹具的完成条件读取其固定基线；P1 只承载主控协议实验，不交付 worker 候选，完成条件仍明确拒绝交付。没有保留旧格式分支或更改实际派发给本 worker 的卡。输入与收件箱夹具的执行器声明同步为当前 `gpt-6.1-sol`／`xhigh`，这些声明不启动模型。

[同一探针绿态](post-rebase-2-card-green/results.json) 3/3 PASS、exit 0。探针从实际三个源文件的 AST 取卡表达式，执行当前生产 schema；独立期望是已指定的夹具基线 `value.txt`。它只证明卡生成表达式与 schema，起始文件确实存在、claim 与受管入口仍由沙箱外阶段核对。

| 检查 | 新证据 | 结果与边界 |
| --- | --- | --- |
| 三个卡生成器 | [green](post-rebase-2-card-green/results.json) | 3/3 PASS；无 daemon／claim |
| 打分读写契约 | [run](post-rebase-2-score-schemas/run.json) | 34/34 PASS；实际临时库中写 schema 2，缺 oracle 字段拒绝，schema 1 历史字节不改，不写主仓打分 |
| T-083 入口回归 | [summary](post-rebase-2-t083/artifacts/summary.json)、[command](post-rebase-2-t083/command.json) | 原有 7/7、0 failures/errors；假启动器与临时 Git，不启动真实 Herdr agent／模型，未改该验收文件 |
| 收件箱领域 | [results](post-rebase-2-inbox-domain/results.json) | 11/11 PASS；角色与存储逻辑，运行时送达为受控事实 |
| 窗格状态／存储 | [results](post-rebase-2-pane-runtime/results.json) | 11/11 PASS；PTY／进程边界为 spy |
| 主控窗口身份 | [results](post-rebase-2-controller-window/results.json) | 5/5 PASS；实际 verifier 闭包，liveness 为模拟 |
| Claude epoch | [results](post-rebase-2-claude-epochs/results.json) | 7/7 PASS；采用 08e 原始 hook 输入，后续 prompt／PTY 为合成 |
| 窗口绑定 | [results](post-rebase-2-window-binding/results.json) | 13/13 PASS；实际 main／驱动分支与归档快照，未开 Electron |

各目录保留确切 argv、stdout／stderr 与结果。以上检查不能外推为真实 Claude 工具执行、角色凭据转交或实际系统输入法通过。没有新独立 reviewer；本阶段不宣称整票交付或发布验收。

## 主控运行的单一沙箱外阶段

先按原启动身份运行 [commit-post-rebase-2.sh](commit-post-rebase-2.sh)。脚本固定检查当前 HEAD、分支、原 CODEX_THREAD_ID／worker 身份、空 index 与修改范围；提交三个夹具、探针、本轮证据、阶段脚本和报告，钩子自行生成尾注。成功后生成 `post-rebase-2-source-freeze.json`，绑定新提交；不变基、不启动实验。

然后在沙箱外运行一次：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/post-rebase-2-stage.py --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/post-rebase-2-outside-01
```

顺序与预期由既有验收断言给出，不以本轮产品输出生成答案：

1. 库版 inbox 管理入口 8 项，确认夹具卡可以保存／create 与原有角色反例。
2. 当前冻结版本原有任务卡验收 15 项；沿用已验收的断言与 adapter，不覆盖业务测试方法。
3. 空框声明真实 daemon/window/hook 入口 17 项；PTY 与供应商 liveness 是 spy，核对真实 hook block 输出／退出码及声明过期反例。
4. 实际 Electron／PTY 的确定性接收器 runtime 12、input-failures 11、worker-inbox 14 项。只新建一次前端构建，后两场复用该次相同构建。供应商 CLI 与模型 0。

脚本检查冻结 HEAD、固定目标是其祖先、源码无已跟踪／未跟踪变动、外置缓存卷挂载；移除继承的角色、Git 与供应商环境，逐项写原始输出。命令失败即 INCOMPLETE、停止，不重试；超时保留该 harness PID／process group／argv 与现场，不发信号。每个入口的既有清理必须完整通过，空框夹具额外核对 daemon.pid／control.sock 已移除。根与构建 slot 保留，不在本阶段删除 slot。若失败，先诊断本次原件，不能直接换目录重跑。

尚未运行的上述六组为 INCOMPLETE。旧 09A 两场实跑仍是旧候选的历史证据，未重跑；完整 8/9/18/CAS 也未在本次变基后重新运行，不借用旧 PASS。本阶段只做当前变基影响的卡、打分、默认启动配置与 T-078 输入／收件箱回归。

## 下一条 Tracer bullet

沙箱外阶段 PASS 后，再准备单个真实 Claude 角色的 Bash 收件箱命令 → 原始请求 → 真实 Stop → 后台实际调用者 → 结果反馈这一条 Tracer bullet，先以当前冻结产品取得真实入口红态。只读确认当前入口仍要求 worker attempt/turn，主控启动为 nullable attempt，并有 `controller_relay_not_enabled`；红态需要辨明实际最先失败的契约，不能先删拒绝或伪造 attempt 来绕过。

沿用 PLAN-09BC-01 与主控 #163 的批准：隔离 HOME、假服务、真实模型 0；实际工具通路和每会话许可先查固定版本材料；各场景每角色根提交 ≤6、主 Messages ≤12、合计 ≤24。先交该切片 launch 的具体 argv、动作／逐屏批准与停止条件，未获该次 launch 批准不启动。红态后才在已分配文件实现实际角色身份、转交与工具反馈，取绿态和边界反例，随后冻结 09B；09B 实跑后才冻结 09C，09C 用真实 >120000 ms 且总观察 ≤150 秒。
