# T-153 独立审查 01（agy）

- 审查员：agy 1.4.6，gemini-3.8-flash-high，Herdr 可见窗格 wG:p1B，auto 模式只用读文件工具，只读副本，候选 6fbef7525。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-153-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-153-r1/prompt.txt)"
# pane wG:p1B started 2026-10-23T20:29:07Z candidate 6fbef75255105589094f6eb4ef80fcd188836293
```

- 审查后候选副本 git status 0 行改动。结论 PASS；一条 P3：RESULTS.md 开头的状态停在交付 04 之前，执行主控已在 RESULTS 末尾补记，原文保留。

## 窗格中的报告原文

```text
○ Thought for 3m 28s (The prompt indicates several Codex runs, each intended to achieve...)
● Explored 27 files (user-decision.md, full.diff, T-153-migrate-worke...) (ctrl+o to expand)

▸ Thought for 40s
   a2a 项目 T-153 独立审查报告

  审查对象：T-153 迁移过时测试 run_worker_delivery.py 到现行契约
  候选版本：6fbef7525（相对起点 b058e3a75）
  审查授权：user-decision.md（用户 2026-10-23 裁定：选 C 迁移 4
  个安全边界测试，保留有效检查，现行代码红绿态）
  审查员：只读独立审查员（read-only independent reviewer）
  ──────
  ## 1. 审查结论与总览

  经逐行比对 full.diff、候选文件 run_worker_delivery.py、门禁契约与全部 4
  轮真实沙箱外运行证据（累计 15 个真实 Codex 回合），审查结论如下：

  1. 过时断言确实过时：被改断言（pane_release 已删、硬编码旧 CLI
  版本、旧两阶段无审查集成、短任务名及全局 relay
  key、旧网络关闭约束）均有明确且独立的规格/commit/ticket
  依据，未抄产品当前输出，未借迁移之名放松检查。
  2. 有效检查完整保留：ticket 列出的所有核心检查（真实 Stop
  批次只处理一遍、重复交付回放、门禁回执只注入一次且仅产生无工具收据回合、实际
  turn_context→delivery→尾注）全部保留，并在收据回合工具检查上做了加强（严格按
  task_started/task_complete 区间扫描工具调用）。
  3. 红态有效且落在保留检查上：变异 repeat-feedback 模拟 daemon.ts
  漏去重重复回放，命中保留检查 STOP-BATCH-ONE-NOTICE，导致 exit 1 /
  NO_GO，代表真实坏实现。
  4.
  严格遵守修改边界：除测试文件自身与证据文件外，零改动产品代码，未碰其他测试或共享基类。
  5. 夹具 Oracle 补强合规：Oracle 从 5 项补强至 116 组用例并经 151
  个系统变异扫查验证，完全依据夹具卡合同补足首/中/末行及类型等价类，未迎合产品代码；审查员
  提示词与要求未做任何修改。
  ──────
  ## 2. 逐项核对与分析

  ### 2.1 被改断言是否确实过时，新期望是否来自独立依据

   被改内容     │ 原期望       │ 新期望        │ 独立依据（非抄产品输出） │ 判定
  ──────────────┼──────────────┼───────────────┼──────────────────────────┼───────────────
   pane_release   │ 调用            │ 移除调用，依赖  │ T-              │ 确实过时，依据
                 │ pane_release  │ 原生 ready     │ 127（282906b9e）彻底 │ 成立
                │ 手动放行领导 │ 自动放行      │ 该命令，无替代命令       │
                │ 进程         │               │                          │
   Tool 尾注    │ 硬编码       │ 独立运行      │ T-118 不限 CLI           │ 确实过时，依
                │ 'Tool':      │ codex --      │ 版本，规定记录实际安装版 │ 据成立
                │ 'codex-cli   │ version       │ 本                       │
                │ 0.162.1'     │ 动态获取安装  │                          │
                │              │ 版本并核对    │                          │
   网络沙箱策略 │ sandbox_poli │ sandbox_polic │ T-141                    │ 确实过时，依
                │ cy.network_a │ y.network_acc │ 用户明确裁定“网络全开”   │ 据成立
                │ ccess is     │ ess is True   │                          │
                │ False        │               │                          │
   集成流程     │ verify       │ verify        │ native-cli spec          │ 确实过时，依
                │ 返回后直接   │ 启动独立      │ §3.5–7、T-070/T-         │ 据成立
                │ integrate    │ reviewer，等  │ 072、core.ts:2402-2418   │
                │              │ 待 verified   │ 强制要求 review_required │
                │              │ 与            │ 和 score_required        │
                │              │ review_reclai │                          │
                │              │ med，提交     │                          │
                │              │ score-file 后 │                          │
                │              │ integrate     │                          │
   任务标识与   │ 短名 T-075-  │ 项目命名空间  │ T-123 任务命名空间与     │ 确实过时，依
   relay 键     │ 3、全局      │ B-fixture+T-  │ relay 请求隔离契约       │ 据成立
                │ id:delivery  │ 153-1、launch │                          │
                │              │ 隔离键        │                          │
                │              │ id:<launch_id │                          │
                │              │ >:delivery    │                          │
   授权与外置盘 │ 旧 batch12   │ 显式传入 --   │ AGENTS.md 2026-10-19     │ 确实过时，依
                │ turn-        │ turn-         │ 内置盘构建裁定与个人代理 │ 据成立
                │ budget.jsonl │ authorization │ 默认授权规则             │
                │ 与 WD-       │ ，数据留 /tmp │                          │
                │ Elements     │               │                          │
                │ 挂载         │               │                          │

  没有任何检查在迁移中被偷偷删减或弱化。

  ### 2.2 ticket 列出的有效检查是否全部保留

  对照 T-153-migrate-worker-delivery.md 所列要求：

  • 真实 Stop 批次只处理一遍：保留。run_worker_delivery.py:320-322 与
  run_worker_delivery.py:407-408 严格断言 len(worker_notices) ==
  1；run_worker_delivery.py:394 严格核对 relay_processed 的 delivery 次数恰为 1。
  • 重复交付回放：保留并补强。run_worker_delivery.py:392-393 检查 DELIVERY-
  REPLAY，且增加断言 event['data']['result'].get('ok') 为真。
  • 门禁回执只注入一次且仅产生无工具收据回合：保留并补强。run_worker_delivery.py:410-422
  检查 len(messages) == 1、RECEIPT-TURN-BOUNDARIES（检查该 turn 的 task_started 与
  task_complete 区间完整且递增）、并在该区间切片内全面扫描 RECEIPT-NO-
  TOOLS，消除了旧代码依赖元数据 passthrough 漏掉导致空匹配假绿的漏洞。
  • 实际 turn_context→delivery→尾注：保留。run_worker_delivery.py:362-376 提取原生会话中与
  delivered['turn_id'] 匹配的 turn_context，核对 model 与 effort
  一致，并对提交说明里的全部 9 项 A2A-* 尾注做逐字集合比对。
  • 其他检查：后台守护进程隔离、错误 fence / 不完整请求拒绝、status/issue
  正常转交、独立主分支提交 G/C/M 双父合并与 host 文件无损、submission_metrics
  统计核对等全部原样保留。

  ### 2.3 红态变异与坏实现的有效性

  • 变异注入机制：run_worker_delivery.py:188-208 通过 --mutant repeat-feedback
  仅在临时工作目录 /tmp/source/workbench/src/daemon.ts 施加变异，将：
    if (!receipt.replayed && !isPendingInboxResult(receipt.result)) receipts.push(receipt);
  修改为：
    if (!isPendingInboxResult(receipt.result)) receipts.push(receipt);
  该变异不修改任何检出源码。
  • 坏实现真实性：该改动移除了回放回执的去重判断，使得同一个 Stop 批次中重复的 delivery-
  copy.json 回放结果被再次塞入反馈通知列表，导致工作进程收到额外的反馈排队。
  • 红态命中点：在 repeat-feedback.json 中：
    "status": "NO_GO",
    "outcome": "contract_failure",
    "failure_id": "STOP-BATCH-ONE-NOTICE",
    "checks": [
      {
        "id": "STOP-BATCH-ONE-NOTICE",
        "passed": false
      }
    ]
  准确命中了保留的有效检查 STOP-BATCH-ONE-NOTICE（源自原测试中的核心有效断言 'one Stop
  batch must produce one gate notice'），而不是落在任何被改动的断言上。

  ### 2.4 修改边界与产品代码零改动

  • Diff 范围：full.diff 显示相对 baseline b058e3a75，仅修改了一个文件：
  workbench/tests/run_worker_delivery.py（587 行 diff）。
  • 产品代码：workbench/src/、workbench/roles/、workbench/terminal/、workbench/hooks/
  等产品源码零修改。
  • 其他测试：未碰任何其他测试用例；未修改共享基类；证据文件与 ticket 均位于专有路径下。
  ──────
  ## 3. 特别核对项深入审查

  ### 3.1 夹具 Oracle 补强是否仅按卡片合同、未迁就产品

  • 夹具卡合同：卡片规定实现 src/normalize.py 与 src/report.py：每项包含
  name（去空白后不为空）与 minutes（非负整数，bool 不算）；按去空白后的 name 合并 minutes
  并按 name 升序排序；正常退出 0 且仅输出一行 JSON；非法输入抛
  ValueError("invalid_minutes"|"invalid_name")，CLI 退出 2 并只输出一行错误 JSON。
  • 补强过程审查：
      1. 第 02 轮绿态被真实 reviewer 指出验收仅 5 项用例，漏测“缺失 minutes”及“成功多行
      JSON”；
      2. 第 03 轮绿态被真实 reviewer
      指出非法输入用例全为单行输入，漏测“多行列表中仅后续行非法（仅校验第一行仍能通过）”；
      3. 第 04 轮 worker 编写 MUTATION-PLAN-04.md，补齐 minutes 19 类与 name 14
      类非法输入在 3 行输入中分别置于首/中/末行的 99 组矩阵测试，加 8 组时长边界及 9
      组手写正反例，扩充至 116 组用例，并通过 MUTATION-SWEEP-04.json 验证了两份 Oracle 对
      151 个错误变异的 302 次拒绝（100% 杀死）。
  • 结论：测试所针对的是 Codex 生成的夹具工作代码（src/normalize.py 与 src/report.py），非
  a2a 编排产品自身。Oracle
  补强使得验收条件更加严密、具有完备的反事实检验能力，完全源自任务卡契约，未从产品输出来抄
  答案，更未迎合或迁就任何产品代码。

  ### 3.2 是否改动审查员提示词或审查要求

  • 核对 reviewer.md：内容保持原样，未作任何修改。
  • 核对门禁中审查员提示词生成逻辑（core.ts:2491）：未作任何修改。
  • 核对执行配置：run_worker_delivery.py:266 仅保存模型为 gpt-6.1-sol、high、fast=false。
  • outside-04-DGpPxgHM 中 reviewer 自行施加了 5 个源码变异（M1 bool 校验、M2 去空白、M3
  合计累加、M4 时长补零、M5 退出码 2）并确认全部被 Oracle
  拒绝后，独立给出“可合并”结论。没有任何为了让 reviewer 通过而放宽要求的作弊行为。

  ### 3.3 真实 Codex 运行与回合记账

  核对全部 4 轮真实沙箱外运行：

  • 01 轮（outside-01-JVDho4I0）：card_save 阶段因缺少 ticket project 前置在启动前失败，0
  模型回合。
  • 02 轮（outside-02-18rhLiEc）：变异场 worker 2 回合（红态有效）；绿态场 worker 2 +
  reviewer 1 回合（reviewer 判需修复），使用 5 回合。
  • 03 轮（outside-03-Ad2MYLoU）：变异场 worker 2 回合（红态有效）；绿态场 worker 2 +
  reviewer 1 回合（reviewer 判需修复），使用 5 回合。
  • 04 轮（outside-04-DGpPxgHM）：注册场 0 回合；变异场 worker 2 回合（红态有效）；绿态场
  worker 2 + reviewer 1 回合（reviewer 独立通过），使用 5 回合。

  累计 15 个真实 Codex 模型回合，账目与 SQLite 数据库事件记录完全吻合，所有运行均在独立
  CODEX_HOME
  下执行，且退出后隔离凭证已彻底销毁。相关回归测试（test_relay_cli.py、test_relay_core.ts
  、test_hook_turn_facts.py）在 04 轮全部 PASS（exit 0）。
  ──────
  ## 4. 发现项清单（Findings）

  无 P0、P1、P2 严重问题。发现 1 项文档陈旧度说明（P3）：

  ### FINDING-001 (P3)

  • 文件与行号：RESULTS.md:3
  • 严重度：P3（文档说明）
  • 现象描述：RESULTS.md 开头仍保留 worker 在沙箱内提交冻结时的文字：“状态：INCOMPLETE...
  完整绿态及新候选独立审查仍待
  04”。沙箱外的第四轮运行实际已由执行主控执行完毕，完整的运行结果、红绿态 JSON
  及三项回归证据已存入同目录下的 outside-04-DGpPxgHM/。这是 a2a 流程中“沙箱内 worker
  冻结代码与自查计划 -> 沙箱外主控执行真实模型运行 ->
  独立审查员审查全链路”的正常工作留痕，不影响技术与证据的完备性。
  ──────
  ## 5. 审查判定

  候选版本 6fbef7525 对 workbench/tests/run_worker_delivery.py
  的迁移严格遵循了现行契约；有效检查全部保留并有所补强；红态落在真实保留检查上；Oracle
  补强严谨独立且经 151
  变异扫查证实；未改动任何产品代码或审查要求；真实沙箱外运行充分且证据确凿。

  T-153 REVIEW PASS

─────────────────────────────────────────────────────────────────────────────────────────────
>
─────────────────────────────────────────────────────────────────────────────────────────────
? for shortcuts                                                       Gemini 3.8 Flash · high
```
