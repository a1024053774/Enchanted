---
id: T-095
title: 把"worker 在提问面板里等主控回答"识别成独立状态，不再显示为 working
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

2026-10-17 T-094 的 worker 用 Codex 的提问面板（默认折叠，按 shift+← 展开）在等执行主控回答，Herdr 却显示 `working`，执行主控漏看了（执行主控报告，用户先发现）。AGENTS.md 要求"任务失败、权限等待、业务阻塞……分别记录，不能用一个 blocked 或 done 掩盖差异"；"等待主控回答"目前没有独立状态。

1. 先读回：提问面板出现时，Herdr 的 `agent_status`、屏幕读取与工作台里该 worker 的状态各是什么；折叠与展开两种形态都要覆盖。
2. 把"等待主控回答"作为独立状态记录和显示（Herdr 期的监视脚本、工作台任务视图二者以哪个为准，执行时按现状定，不双写）。
3. 识别靠屏幕或事件里的机械事实（面板标记），不用正则猜用户意图（见 `feedback-intent-classification-no-regex`）；识别不到时报"未知"，不报 working。

## Acceptance

- [x] 红态：在折叠与展开两种形态下，当前状态读出为 working，保留读屏原件。
- [x] 绿态：两种形态都读出"等待主控回答"，并带 worker 与 launch 身份。
- [x] 反例：普通 working（模型在思考或跑命令）不被误报成等待；面板被关闭或已回答后状态回落。
- [x] `project_map.py status` 0 problems。

## 说明

- 来源：执行主控 2026-10-17 消息与 triage issue；构思主控裁定另开票、不并入 T-094（T-094 是启动失败，本票是运行中状态识别，验收与写入范围不同）。已标就绪（见下）。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："我现在在现场，T-095开工，然后 T-010到 T-014你评估一下……"，构思主控据此标就绪（`ready_rev: 1`）。

## 裁定（2026-10-18）

执行主控 needs-decision：红态原文"读出 working"与 10-18 三次真实运行不符（Herdr 报 blocked；仅 10-17 见过 working，无原件）；"关闭或回答后回落"在 Ctrl+] 跳过后原生日志无"已解决"事件，报 unknown，"已回答"路径未测。用户选"B: 按 A 改口径，再用 1 个根回合补测“已回答” (Recommended)"，选项原文："红态改成“修前状态读取里没有等待主控回答这个状态”；回落改成“离开等待主控回答”，跳过后报 unknown 就算满足。再花 1 个真实模型根回合（用 fast）把“已回答”路径测一遍——这正是“答完了状态还卡在等待”的误报风险点，值得测。"

据此：红态=修前读取里不存在"等待主控回答"状态；回落=离开该状态；跳过后无解决事件、报 unknown 写入已知限制；补测"已回答"路径须有真实原件，状态卡在等待即为失败。真实模型根回合追加 1 个（累计 5），用户已批准，不得再追加。

## Resolution

2026-10-18，执行主控按门禁验收 **PASS**（口径按用户裁定 B），合入 main，未 push。冻结候选为 `bef1b55e331b7c078820b908a3eba17feea478e7`（exec/t095），产品版本 `faa2b9b3b`；其后 `20ec1452c` 只补审查报告。

- **产品**：新增 `scripts/agent-status`，作为 Herdr 期的只读状态命令，内部值 `waiting_controller_answer`，界面显示"等待主控回答"。输出带 worker、launch、pane 与 native session 身份。判定只看机械事实：折叠时底部出现 `? N question` 计数行，或展开时控制条上同时出现 `⌃] skip` 和 `⇧→ main prompt`，并且要与 Herdr 的 `blocked` 互相印证。只有一边成立、身份不符，或屏幕与原生日志冲突时，一律报 `unknown`，不报 working。不改 Herdr、dispatch，也不写全局配置。
- **真实证据**：共 5 个根回合。第 3、4 个由执行主控追加，第 5 个由用户批准。原件在外置盘 `a2a-evidence/2026-10-16-batch16/T-095/`。
  - 红态：用修前候选回放原件，不存在"等待"这一状态。
  - 第 4 回合（green-anchor-independent）：折叠、展开两种形态都正确判为"等待主控回答"。
  - 第 5 回合（answered）：提交 A 之后，即时、30 秒、60 秒三次读取都已离开等待。
  - 第 1、2 次绿态（第 2、3 回合）解析器过严，全部 NO_GO，原件保留。
- **独立审查**：reviewer s16-t095-rev（launch-9406490baf8d4644872b7d83896a22b6）PASS，三个变异都被拒。
- **已知限制**：
  - 原生日志里没有可识别的"已解决"事件，所以跳过或答后回落时只报 `unknown`，回不到 working。第 5 回合日志其实有 A 的应答和 turn 完成，但当前解析器没有识别。
  - 折叠计数行有时不出现（第 1、5 回合都是如此），这时折叠态只能报 `unknown`。
  - 并发下 herdr get 曾有两次超过 3 秒，返回 `unknown`，根因未定，生产中 Herdr 繁忙时同样会读成 `unknown`。
  - 原票红态写的"读出 working"在 2026-10-18 未能复现：三次运行 Herdr 都报 blocked；10-17 那次 working 只有观察记录，没有原件。
- 打分：`score-59810a27bf2041a2973dd86578f4c1c0`（边界 3、工程 2）。
