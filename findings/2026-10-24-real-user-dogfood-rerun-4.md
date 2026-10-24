# Enchanted 多 agent 真实使用第四轮重跑（2026-10-24）

状态：PASS（本轮目标：一个 Codex CLI worker 的任务经独立审查并经门禁集成）。Codex worker、审查员均为 `gpt-6.1-sol` / `high` / 不开 Fast；应用内主控是用户自己的 Claude Code 2.1.310 / `claude-haiku-5-5`；外层测试员为 Claude Sonnet，经 lcu 做 Computer Use。只做这一个任务，不覆盖前三轮已验过的条目，也不代表全域可靠。

## 范围与证据边界

产品基线 aacc1bb81；实例 `/private/tmp/t164-dogfood-dc_5rakx`，一次性 `demo-repo`。测试员只操作 PID 96695 的隔离 Electron（窗口 URL 已核对为本实例）；业务与门禁操作都经界面里的应用内主控完成，没有直连 socket、调用门禁、改库或读认证文件。事后只读实例 sqlite 和原生日志核对身份与计数。界面里的“用户输入”由测试 agent 操作，不冒称真人输入。详细时间线、事件序号、回合统计见[运行记录](../evidence/2026-10-23-batch24/T-164/rerun-4/RESULTS.md)。

## 步骤

1. 打开 demo-repo，开项目终端，手启 `claude --model claude-haiku-5-5`，信任本实例目录。
2. 主控经 `a2a request executor` 申请角色，窗格顶栏出现批准条，点“批准”后角色生效（图 01、02）。
3. 交任务 T-1：Codex worker 新建 `shopping.md`，只列零库存食材（香蕉、面条）；worker 与审查员 gpt-6.1-sol high。主控保存卡、派发 a1（图 03）。a1 交付。
4. 主控 verify 失败（`oracle_failed`）：它把完成条件写成了主仓库绝对路径，而 worker 在 worktree 里交付。候选内容本身正确。主控按 card_save v2 → `revise` → 普通 reclaim a1 → dispatch a2 走通，reclaim 一次成功（图 04）。
5. a2 交付，verify 通过（自检 9/9 与正式检查），门禁新开 Codex 审查会话，结论“可合并”，无 findings，5 个变异检查全拒（图 06、07）。
6. 打分后 integrate，demo-repo 的 main 从 17464e6 前进到 `7ce91a867078651a7f3f8eb87c7d96281fd97293`，任务 accepted（图 08）。

## 与目标相关的观察

- Codex worker 被 verify 拒绝后“修订→普通 reclaim→重派”这条路径在 gpt-6.1-sol 下走通：a2 正常启动并交付。启动失败路径（N05/T-170 原症状）本轮没有出现，不能据此说“已修好”，只能说正常路径未复现问题。
- 独立审查由门禁新开 Codex 会话完成（同 CLI 同模型），审查前有 review-copy，结束后回收；未见协议拒收。
- 启动 argv 记录完整：`-m gpt-6.1-sol -c model_reasoning_effort="high" -c service_tier="default"`；三个会话的原生日志 turn_context 均为 gpt-6.1-sol / high。

## 新发现

- N07 worker 的 blocking 问题在主控已修订重派后仍悬在问题页：a1 worker 上报的“阻塞：门禁验收读取主仓库绝对路径”，主控 revise 后问题仍显示“等你决定、阻塞”，问题页角标最后是 2。这符合“只有用户能关闭 blocking”的规则，但没有任何关联提示说明其根因已随新卡版本消除，用户需要自己判断。我没有关闭它。（图 05。对产品是体验问题还是预期，留给构思主控判断。）
- N08 主控的卡错误是任务级流程成本，不是产品缺陷：绝对路径完成条件写进卡后，门禁 oracle_failed，需要 revise/reclaim 一轮；此前 oracle_paths 为空还被拒两次（事件 #1、#2）。门禁都如实拒绝并留证，没有放行。
- 测试输入侧：macOS 打开面板的 Cmd+Shift+G 路径栏会自动补全并曾显示另一个已不存在的旧实例路径（`t164-dogfood-0zw8tib0`）；这是系统控件行为，不归产品，仅提醒后续测试员核对目录。

## Herdr 对照

走到“Codex worker 经独审并门禁集成”共用 Claude 6 个应用内回合、Codex 7 个回合，约 20 分钟（含一次因主控卡错误导致的 revise/重派）。门禁的拒绝与恢复路径（oracle 拒绝、revise、reclaim、新 attempt、独立审查、integrate、打分）都由工作台事件完整记录，序号见 RESULTS；Herdr 期这些步骤依赖主控与人工在多个 pane 之间协调。本轮没有做同任务的 Herdr 对照实验，不据此宣称提速或可靠性改善。
