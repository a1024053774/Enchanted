# T-007 phase 1 只读观察（2026-10-06）

状态：INCOMPLETE（产品）；本轮两次观察已结束。此报告不作产品 PASS、ticket 关闭或集成结论。

## 范围与依据

目标是核对父版本业务红态与夹具错误的区分、红态确认与实施的可见顺序，以及身份和配置证据。只读取本项目规范、本轮证据及指定 recovery-build 的 Herdr get/visible；未控制 Herdr、发送消息、启动 agent、修改代码/状态/ticket/Git。唯一新增文件为本报告和 monitor-phase1.jsonl，均以独占创建防止覆盖。

本轮契约：.project-map/specs/recovery-2026-10-06.md；父源码声明为 aca370a30fb1fdd938cf89c29ffe2e2f75a21583，独立源文件为 check-parent-aca370a-aa00373174a0.py。验收绑定真实 CLI、SQLite、Git，故障仅针对夹具创建的 CLI。沿用 Ubiquitous language；这是已验收 Tracer bullet 的恢复观察，不评判 Deep modules 的实现质量。

## 两次可见采样（UTC）

| 采样 | get / visible 时段 | 运行态 | 可见内容 |
| --- | --- | --- | --- |
| 1 | 06:09:37.355–06:09:37.740 | working；state_change_seq=4548 | 先前 READY 等待记录；主控放行；worker 宣布开始并读取 red-ready.json，实际输出 ready=true；尚未可见产品补丁 |
| 2 | 06:10:22.029–06:10:22.219 | working；state_change_seq=4558 | 可见 coop.py 补丁，包含操作锁、集成意图绑定与恢复分支 |

两次均指向 pane wF:pB、tab wF:t1、terminal term_65d25b3b904ba46；原生 Codex session 由 Herdr 报告为 01a10fcb-d5d5-78a1-9a25-78f5977e7d7d（source=herdr:codex）。没有使用 UI 焦点或继承 pane 环境代替此实时身份。

## 父版本 9 项与错误分类

最终原始证据 check-20261006T060615.461887Z-464eb642.json：06:06:15.463854–06:06:37.384650，exit=1；9 项、4 项 business-red、5 项通过、0 项 fixture-error。red-ready 摘要和最终 trace 结果一致。

| 测试场景 | 最终父版本记录 | 可见依据 |
| --- | --- | --- |
| 存活 verify 排除重复 verify / integrate | business-red | 返回 not_submitted / not_verified，未按契约返回 operation_busy |
| 存活 integrate 排除重复 verify / integrate | business-red | 两个并发调用超过夹具 2 秒界限，随后夹具终止它们 |
| verify 中断后新 ID / worktree / 完整 oracle | business-red | 返回 not_submitted，ID 没变，仍 verifying，未启动新 oracle |
| CAS 前恢复同一 intent | business-red | 引用仍 G，却返回 needs_reconciliation；未完成缺失 CAS |
| CAS 后补记且不再写 Git | 已记录通过 | 最终 trace 的 PASS 项 |
| CAS 后外部 X 拒绝 | 已记录通过 | 同上 |
| CAS 后引用删除拒绝 | 已记录通过 | 同上 |
| 中断后撤销/重领，旧身份拒绝 | 已记录通过 | 同上 |
| 中断后规格变化，旧候选拒绝 | 已记录通过 | 同上 |

“已记录通过”仅引用父版本场景记录，本观察者未重跑或独立验收产品。

首轮 check-20261006T060434.951455Z-8674cac3.json 保留 2 项 business-red、2 项通过、5 项 fixture-error；5 项均抛 FixtureError: Expected one persisted integration intent; observed: []。red-ready 明确排除这些错误，不把它们充作产品红态。第二轮 check-20261006T060526.582230Z-9dac2832.json 和最终轮均为 4/5/0。现有记录支持分类已正确分开；首轮 observer-schema 根因是证据作者的说明，本轮没有另做夹具代码审计。

## 红态确认与实施顺序

- 06:02:55.471074 的已有 commands.jsonl 可见读取中，worker 报告“未修改文件”，red-ready 尚不存在，READY 等待。
- 最终父版本执行在 06:06:37.384650 结束；red-ready.created_at=06:07:00.250371，文件 mtime=06:07:00.251358。
- 主控放行 prompt 记录于 06:08:24.522883–06:08:24.832604，明确引用 4 项业务失败、5 项通过、0 夹具错误。
- 本轮第一次采样可见 worker 收到放行后开始实施，并实际读取 ready=true。
- 第二次采样可见产品补丁；coop.py 当前 mtime=06:10:04.399782，晚于确认和放行。

结论是可观察顺序与门禁要求一致，未发现提前实施证据。先前“未修改”的模型自报、一次 clean diff 的可见摘要和当前 mtime 都不是连续编辑审计；因此不能证明绝无更早写入，也不能从 prompt 成功返回的 idle 推导业务进度。

## 模型、原生 session、程序 PID 与配置声明

界面两次显示 GPT-6.1-Sol xhigh fast；启动 argv 明确请求 -m gpt-6.1-sol、model_reasoning_effort="xhigh"、service_tier="fast"、check_for_update_on_startup=false。这些是 CLI 可见选择和请求配置，未独立观测供应商实际模型路由、推理档位或实际 tier。

Herdr get 的 native session 与程序协调层 attempt.session_id / fence 是不同身份。fixture trace 中 attempt、session_id、fence、spec_rev 是该隔离场景的受管身份，不能替代上述 Codex 原生 session。

程序 PID 来自已有故障证据：被终止 CLI 为 4976、4984、5024、5112、5197、5298、5415、5495、5606，均保留 argv、identity_check、SIGKILL、exit=-9、alive_after=false；其中 4976/4984 是超时并发调用的清理。例：verify 中断 CLI=5024，before-CAS CLI=5112，after-CAS CLI=5197。这些是历史夹具 PID，不是 recovery-build 的 Codex PID；Herdr get 未返回该 worker 程序 PID，本轮未另查进程表，不能声称已绑定。

启动记录显示本 monitor 请求 GPT-6.1-Sol high；已有 startup visible 记录显示 Codex v0.160.1。本轮未把模型名、terminal title、native session 或 PID 相互等同。

## 缺失证据与误判风险

第二次采样时没有 build-*.json；实现绿态、T-006 8 项本候选复验、代表性 known-bad 反事实和固定候选独立审查均未纳入本轮证据。没有冻结交付代码版本，不能拿父源码版本或测试运行时 repository_head 当本候选完整版本；本轮只观察到 task=T-007 和 worker 身份，不证明业务 submit/acceptance/integration 身份绑定。

red-ready.status=PASS 绑定 claim=parent-business-red-established；parent_suite_status=INCOMPLETE、exit=1 明确表示产品父版本仍不满足契约。不得把该 PASS、worker 的 working/idle、先前 T-006 通过或自然语言“开始/完成”当产品通过。

manifest.md 仍写“等待独立父版本故障证据”，与现已存在的 red-ready 不同步；它的配置“均为 xhigh Fast”也不能概括本 high monitor。仅记录，不改它。

本轮开头 project_map status：exit=0，Problems=0、Stale=0，T-007 claimed by recovery-build。收尾 06:10:36.848–06:10:37.176：exit=1，Problems=0、Stale=1；CONTEXT.md 因 coop.py 未提交修改、覆盖文档未修改被标 stale。该机械提示不证明词汇内容已错误，需由有权写入者核对。本 monitor 无权修复，未将项目状态写成健康通过。

原始采样命令、时刻与工具返回见 monitor-phase1.jsonl。部分前期大段 cat/摘要调用在工具返回中截断，日志保留截断标记；随后有无 traceback 的完整分类摘要补足 9 项核对。初始发现调用发生于详细计时日志建立前，日志显式列出命令但不补造原时刻。没有后续轮询，不等待实现完成。
