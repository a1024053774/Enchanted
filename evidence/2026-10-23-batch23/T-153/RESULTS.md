# T-153-1 / a1：交付测试迁移

状态：**INCOMPLETE**。首轮完整运行在注册前失败，尚无有效绿态或通知变异红态；修正后的沙箱内注册阶段已通过，但进程退出确认受沙箱限制，收尾为 BLOCKED。独立审查未运行，不宣称验收通过。

分支 `exec/t153`，起点 `b058e3a7585ccc85df190e90c01b52756c9d076e`。唯一修改的测试为 `workbench/tests/run_worker_delivery.py`；没有新增辅助模块，没有修改产品代码、共享基类或其他测试。

## 检查清单与改动

逐条原断言、判定、新期望与来源见 [INVENTORY.md](INVENTORY.md)；原始 assert 文本及命令清单见 [pre-edit-inventory.json](pre-edit-inventory.json)。该清单在修改测试前生成，静态诊断不是产品红态。

1. 删除唯一已删命令 `pane_release` 的调用（T-127，主控指出的 `282906b9e`）；仍观察领导进程，首条任务由原生 ready 自动放行。共享基类保持原样。
2. 按 T-118 用独立执行的安装 CLI `--version` 核对 Tool 尾注，保留其余八项尾注逐字核对，以及实际 turn_context → delivery → 尾注的模型/强度检查。
3. 按 T-141 将原生 sandbox_policy 的网络期望从 false 改为 true；保留 model 与 approval_policy=never。没有从当前运行结果取期望。
4. 按现行 spec §3.5–7、T-070/T-072，verify 后等待新的 reviewer、候选绑定报告及 review_reclaimed，再带 score-file 集成。仍检查 G/C/M、双父 merge、主分支回读、host 文件及独立 oracle。
5. 按 T-123，首次 card_save 与 create 都带同一 --project B-fixture；卡号使用符合来源 ticket 序号约定的 T-153-1。此后使用 create 返回的完整 task id 调用门禁、注入请求并核对尾注；回放检查绑定同一个 launch 的 delivery，不再要求旧全局键 `id:delivery`。全路径逐项核对见 [IDENTITY-AUDIT-02.md](IDENTITY-AUDIT-02.md)。
6. 保留错误身份/不完整请求拒绝、status/issue 转交、交付只处理一次、真实两个 worker 回合、单批单通知、原生通知文本只出现一次、无审批等待、queue 为空、独立 diff 指标。
7. 收据回合仍不得调用工具；额外要求其 task_started/task_complete 区间完整，在区间内检查所有 function_call/custom_tool_call，避免工具记录缺 turn_id 时空匹配。
8. 运行接口改为 `--summary <新路径>`，拒绝覆盖。支持 `--revision` 的隔离源码与 `--mutant repeat-feedback`，均不修改 checkout 产品源码。summary 中记录候选版本、目标版本/变异、命令、授权和原始现场路径。
9. 旧累计 turn-budget 和已不存在的早期决定05不再充当授权。主控运行时显式给当前授权文件；每场 worker 最多两回合、reviewer 最多两回合，不重试。模型 `gpt-6.1-sol`、high、普通速度，完整 argv 在运行现场保存。
10. 根据 AGENTS.md 的内置盘构建裁定移除旧的挂载前置条件。原始夹具、数据库、长日志留在 /tmp，不进入仓库；停止与隔离 home 删除仍经现有退出确认辅助函数。主控另按 T-088 归档，本次未作外置盘归档。

## 已运行

[local-checks-01.json](local-checks-01.json) 保存精确命令、退出值及输出；原始夹具在 `/tmp/t153-local-7hqzrlbo` 和相应测试报告指向的 /tmp 目录。

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| test_relay_cli.py | PASS，exit 0 | 真实 CLI 将 submit/status/issue 写入请求文件，无后台替身。 |
| test_relay_core.ts | PASS，exit 0，failure=null | 请求重复、错误身份、不完整、in-flight 不重执行及追加式记录；只证明 relay 层。 |
| test_hook_turn_facts.py | PASS，exit 0，5 场 | 真实 Git hook；包括不同请求模型、最新回合、辅助会话忽略与缺上下文。 |
| Python compile、--help、zsh -n、git diff --check | PASS | 语法与接口检查；不能替代完整链路。 |
| session 开始 project_map status | PASS，Problems 0、stale 0 | 初始地图健康；结束读数另存 status-end.txt。 |

## 待主控沙箱外运行

首轮 [outside-01-JVDho4I0/summary.json](outside-01-JVDho4I0/summary.json) 由主控运行：两场均在 card_save 因 unknown_task 失败，0 模型回合；三项相关回归均 exit 0。首轮输出保持原样，不当作产品红态。

运行新的 [RUN-OUTSIDE-02.sh](RUN-OUTSIDE-02.sh)，显式传入主控对新一轮真实回合和启动 hook 的授权文件；不复用只授权首轮的 controller-authorization-01.md：

```zsh
zsh evidence/2026-10-23-batch23/T-153/RUN-OUTSIDE-02.sh /绝对路径/本轮授权.md
```

新脚本先确认 registration-02/03/04 的三个自有后台 PID 已退出，再删除对应隔离 home，保留其他原始现场。然后用同一个入口 --setup-only 做零模型注册检查；该检查不通过就停止。通过后跑 repeat-feedback 变异、当前候选绿态及上表三个相关回归。每次建新的 `outside-02-XXXXXXXX/`，保存各场 JSON、stdout/stderr、命令和总 summary。两场真实运行总预留上限仍为 8 回合，失败不自动重跑。需要可用的真实 Codex 登录；只在注册完成后准备交付时复制 auth.json 到 /tmp 隔离 CODEX_HOME，只信任本次夹具根目录，只加入 git add / git commit 两条 allow，不写用户 ~/.codex。

变异只在 /tmp 源码副本移除“回放不再次反馈”的条件。有效红态必须同时满足：exit 1、NO_GO、contract_failure、failure_id=STOP-BATCH-ONE-NOTICE、两个真实 worker 回合已完成、隔离 home 已删除。启动、CLI 用法、超时、未分类断言或清理失败均不计红态。当前尚无本轮真实红态/绿态结果；上表局部通过不能替代它们。

独立 behavioral-acceptance-review 需由主控对冻结候选和沙箱外结果安排新的只读审查；worker 不把自查写成独立结论。没有修改产品异常处理或添加产品 fallback/兼容路径。

## 主控 #11 后的注册验证

精确命令和现场路径分别见 [registration-02.json](registration-02.json)、[registration-03.json](registration-03.json)、[registration-04.json](registration-04.json)。完整诊断见 IDENTITY-AUDIT-02：首个尝试在 /bin/ps 被沙箱拒绝；第二个尝试揭示卡号缺序号；第三个已通过真实 card_save/create/status，检查完整 id=`B-fixture+T-153-1`、尚无 attempt/candidate，0 模型回合。三次最终状态都是 BLOCKED（进程退出核对缺权限），不是完整运行 PASS。各自原始 raw/commands.json 和 stop.json 保留在 summary 指向的 /tmp 目录；RUN-OUTSIDE-02 会保存新的清理核对记录。

--setup-only 对完整交付路径只加一个分支：注册成功后结束；else 内原有交付、审查、集成和保留断言顺序不变。注册模式不复制 auth.json、不派发、不安装原生会话 hook。

## 范围外上报

已通过 `scripts/inbox send` 上报 `20261023T193353Z-worker:b23-t153-issue-001`（非阻塞）：被索引的 native-cli spec §5:118 仍写旧 socket/关网络契约，与 T-075 最终文件交付通道及 T-141 网络裁定冲突。正文见 [issue-spec-network.md](issue-spec-network.md)。本任务依据已授权的 T-153/T-141 继续，未修改规格。收件箱条目留在本 worktree `.project-map/inbox/`，不纳入允许路径以外的测试交付提交。
