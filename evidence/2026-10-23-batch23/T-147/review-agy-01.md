# T-147 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pR，交互 auto 模式（只用读文件工具），只读副本，候选 aa1a83aa0。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-147-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-147-r1/prompt.txt)"
# pane wG:pR started 2026-10-23T15:41:08Z
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS。F-01（P2）：worktree 起点是 2e36efb7c，不是含 ticket 的 fda7d194d（执行主控建 worktree 时先取了起点再提交 ticket）；用 git merge 合入，ticket 不受影响。F-02（P2）：RUN-OUTSIDE-01.sh 写死 worktree 路径，复跑需在该 worktree 或改路径。F-03（P3）：检查名沿用旧字面，按卡要求不改。

## 窗格中的报告原文

```text

○ Thought for 3m 41s (This task invol...)
● Explored 22 files (ctrl+o to expand)

▸ Thought for 21s
   T-147 独立审查报告

  审查对象：T-
  147（按用户裁定更新受保护验收文件
  test_t121_role_request_e2e.py:515 的
  sidebar_drops_closed_controller
  断言）
  候选提交：aa1a83aa0（worktree 分支
  exec/t147）
  对比基线：fda7d194d（执行主控建票提交
  ）/ 2e36efb7c（worker 实际起点）
  审查依据：

  •
  20261023T125315Z-ideation-answer-001.
  md（用户裁定 B，问题 3）
  •
  20261023T153252Z-executor-report-001.
  md（用户逐字选择“保留并标已结束
  (Recommended)”）
  • regression-04-NOTE.md（main 分支 T-
  121 失败证据）
  • run.json（执行主控沙箱外实跑证据）
  ──────
  ## 一、逐项核对结论

  ### 1. 改动范围与代码边界

  • 受保护文件改动仅限授权一行：在
  test_t121_role_request_e2e.py:515
  中，仅第 515 行被修改：
    -
  check('sidebar_drops_closed_controlle
  r', not [agent for agent in
  sidebar['agents'] if agent['id'] ==
  a['launch']])
    +
  check('sidebar_drops_closed_controlle
  r', [agent['state'] for agent in
  sidebar['agents'] if agent['id'] ==
  a['launch']] == ['ended'])

  • 其他检查名、断言、超时完全未动：
      • 前置检查
      closed_terminal_identity_refused
      （第 513 行）保持不变；
      • 后续检查
      role_free_again_after_close（第
      518 行）保持不变；
      • 检查名称
      sidebar_drops_closed_controller
      保持不变；
      • 所有轮询、超时参数（如 deadline
      = time.monotonic() +
      15）无任何变动。
  •
  产品代码零改动：workbench/src/、workb
  ench/terminal/
  等所有产品代码均未修改。
  • 注：full.diff 包含了因 worker
  起点不一致产生的 ticket
  文件删除差异（详见发现项 F-01）。

  ### 2.
  新断言对裁定的保真度与防退化能力

  • 忠实表达裁定：
      • 新断言 [agent['state'] for
      agent in sidebar['agents'] if
      agent['id'] == a['launch']] ==
      ['ended'] 表达的是：匹配指定终端
      id 的条目必须存在、数量必须恰好为
      1，且其 state 必须等于 'ended'。
  • 能确切拒绝“删掉条目”的旧行为：
      • 若条目被删，推导式结果为 []，[]
      == ['ended'] 判定为
      False，准确触发断言失败。
  • 能确切拒绝“仍标运行中”等错误：
      • 若状态为运行中，结果为
      ['running']，!=
      ['ended']；若为其他非 ended
      状态或 None，同样失败。
  • 无意外放宽：
      •
      防止多条目/重复条目：若侧栏出现重
      复条目（如 ['ended',
      'ended']），列表长度大于
      1，不等于
      ['ended']，会被严格拒绝；
      • 身份仍有效防线未松：第 512–513
      行保留了对已关闭终端凭据请求的拒
      绝检查（closed_terminal_identity_
      refused），且第 516–518
      行验证了角色已释放可被新终端重新
      申请（role_free_again_after_close
      ）；
      •
      其他终端不受干扰：列表推导式严格
      按 agent['id'] == a['launch']
      过滤，侧栏存在其他终端或 agent
      条目不会引起意外断言失败。


  ### 3. 证据链完整性

  • 候选绿态：
      • green.json 与 green.log
      表明完整 T-121 退出码为 0，全部
      49 项 check 均 PASS。
  • 旧行为红态：
      • old-behavior-red.json 与
      old-behavior-red.log 表明 --
      revision 045e8cfb1 退出码为
      1，状态为 INCOMPLETE，前序 43
      项通过（含
      closed_terminal_identity_refused
      ），精确红在目标断言
      AssertionError:
      sidebar_drops_closed_controller:
      None。
  • 自动化判据：
      • run.json
      对比两项退出码、错误信息及 checks
      列表，确认反例精确击中目标。
      • local-checks.json 亦通过 AST
      静态输入穷举了 5
      种状态组合，行为一致。

  ──────
  ## 二、发现项清单

  ### F-01：Worker 起点不一致导致
  full.diff 呈现 ticket 删除差异

  • 文件与行号：
      • full.diff:1-36
      • RESULTS.md:5
  • 严重度：P2（合并风险 / 追踪脱节）
  • 事实与根因：
      • 执行主控在 fda7d194d 创建了
      ticket 文件 .project-
      map/tickets/T-147-t121-assertion-
      after-decision-b.md 并派发任务。
      • Worker b23-t147 从更早的起点
      2e36efb7c 检出分支，未包含
      fda7d194d 的提交。Worker
      检查三处代码范围无 diff 后未
      rebase，交付时亦未提交 ticket
      文件（遵循了“未修改
      ticket”的规则）。
      • 因此，候选版本 aa1a83aa0（及
      candidate/ 副本）中不存在该
      ticket 文件。full.
      diff（fda7d194d..aa1a83aa0）显示
      该 ticket 被 deleted file mode
      100644。
  • 失败场景：
      • 若执行主控采用 git apply full.
      diff 或无上下文 patch
      方式合入，会导致 main 分支上的 T-
      147-t121-assertion-after-
      decision-b.md 被误删。
      •
      处置要求：执行主控在集成时应使用
      标准三方合并（git merge
      exec/t147），基线为
      2e36efb7c，main 分支上的 ticket
      会被正常保留，切勿直接以 patch
      覆盖。


  ### F-02：复现脚本中硬编码了 worker
  的绝对工作区路径

  • 文件与行号：
      • RUN-OUTSIDE-01.sh:3
  • 严重度：P2（脚本可移植性缺陷）
  • 事实与根因：
      • 脚本第 3 行写死 cd
      /Users/luckye/Documents/Code/a2a-
      wt-t147 || exit 1。
  • 失败场景：
      • 当临时 worktree a2a-wt-t147
      被清理回收，或在其他检出目录运行
      该脚本时，脚本将因路径不存在直接
      退出 1 失败。
      •
      建议：未来任务脚本应使用当前目录
      或脚本所在仓根路径（如 $(git rev-
      parse --show-
      toplevel)）。本次沙箱外复跑已由执
      行主控在原 worktree
      成功执行并产出证据，不影响本次验
      收有效性。


  ### F-
  03：检查名称保留了旧语义字面（说明性
  ）

  • 文件与行号：
      •
      test_t121_role_request_e2e.py:515
  •
  严重度：P3（命名与实际行为轻微脱节）
  • 事实与根因：
      • 检查名称为
      sidebar_drops_closed_controller，
      字面意思是“侧栏丢弃/删除已关闭主
      控”，但新断言实际验证“侧栏保留该
      主控且状态标为 ended”。
  • 失败场景 / 评估：
      • Ticket 明确规定 其余 T-121
      检查名、断言、超时不变，保留检查
      名是为了保障既有下游检查项列表（c
      hecks
      数组）的向后兼容与统计一致性。此
      项无害，符合任务卡要求。

  ──────
  ## 三、审查总结

  T-147 严格按照用户裁定 B
  与执行主控选择题指令，精准修改了受保
  护验收文件
  test_t121_role_request_e2e.py:515。新
  断言表达精准无漏洞，严密覆盖了存在性
  、唯一性与 ended
  状态，未放宽身份鉴权与角色释放约束；
  产品代码完全未动；沙箱外绿态与反例红
  态证据确凿。两处 P2 发现（ticket diff
  差异与脚本硬编码路径）属于集成提示与
  脚本稳健性问题，不影响核心断言与验收
  逻辑的正确性。

  T-147 REVIEW PASS
```
