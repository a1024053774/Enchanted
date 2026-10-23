# T-146 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:p6，交互会话，审查对象为只读副本（候选 acf17e6ad）。
- 启动 argv 记录（依次尝试）：

```
agy --model gemini-3.8-flash-high --mode plan --add-dir /Users/luckye/Documents/Code/a2a-review/T-146-r1 --add-dir /Users/luckye/Documents/Code/a2a-wt-t146/evidence/2026-10-23-batch23/T-146 --add-dir /Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch23 --print-timeout 0s --print "$(cat /Users/luckye/Documents/Code/a2a-review/T-146-r1/prompt.txt)" | tee /Users/luckye/Documents/Code/a2a-review/T-146-r1/review-01.md
# ↑ 01：--print 无头模式，shell 命令无法确认被自动拒绝，0 字节输出（未计入结论）
agy --model gemini-3.8-flash-high --mode plan --add-dir /Users/luckye/Documents/Code/a2a-review/T-146-r1 --add-dir /Users/luckye/Documents/Code/a2a-wt-t146/evidence/2026-10-23-batch23/T-146 --add-dir /Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch23 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-146-r1/prompt-02.txt)"
# 2026-10-23T11:32:43Z 会话中模式自行从 plan 变为 auto（编辑会自动批准）；执行主控把 candidate 设为只读兜底，审查后核对副本与证据目录无改动
# ↑ 02：plan 交互模式；一次被执行主控误按 Esc 打断后重开，仍逐条确认命令，用户嫌烦，退出（副本核对均无改动）
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-146-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-146-r1/prompt-03.txt)"
# ↑ 03：本报告所用会话
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，两条 P3 记为已知局限。

## 窗格中的报告原文

```text

▸ Thought for 35s
   T-146 候选交付独立审查报告

  审查对象：候选提交 acf17e6ad（相对起点
  ebbae7bd0）
  关联材料：

  • Ticket：candidate/.project-
  map/tickets/T-146-stale-running-state.md
  • 任务卡：evidence/card.md
  • 交付说明：candidate/evidence/2026-10-
  23-batch23/T-146/RESULTS.md（worktree
  对应位置）
  • 全量改动：full.diff
  • 沙箱外运行结果：outside-04-run-results.
  json 及 evidence/outside04-
  20261023T104746Z-9083/ 原始证据
  ──────
  ## 逐项核对结论

  ### 1. 改动是否达成 ticket
  目标与状态来源统一

  • 统一来源与状态一致性：
      • daemon.ts:406-412：reflect_tree
      改为直接调用 sidebarSnapshot
      获取所有会话的当前状态映射 new
      Map(sidebar.agents.map(agent =>
      [agent.id, agent.
      state]))，作为状态事实唯一输入。
      •
      reflect.ts:133-165：彻底移除了旧的私
      有状态推导逻辑（row.state === 'ended'
      ? 'ended' : 'running' 以及依赖
      lifecycle(record)
      的推导），受管会话与已批准终端主控均
      统一查表消费 sessionStates.get(...
      )；状态标签 state_label 直接复用
      sidebar.ts 的 stateLabels。
      •
      ReflectPage.tsx:20-22：删除了前端私有
      的 states 字典，直接使用后台下发的
      node.state_label。
      • 侧栏、流程页（flow.ts）与 Reflect
      页对同一会话消费同一 sidebarSnapshot
      事实。已结束会话在 Reflect
      中明确显示“已结束”；侧栏与流程沿用既
      有规则过滤已结束会话（若显示则均为已
      结束，不显示为“运行中”或“空闲”）；处
      于真实运行状态的会话在三处均显示为“运
      行中”。
  •
  另算状态的地方：无。所有状态计算均收口于
  sidebar.ts:agentState 及 roleRequests.ts
  的事实判断。

  ### 2. 门禁 gates/core.ts 与 panes.ts
  改动范围与质量

  • gates/core.ts：
      • core.ts:2344：仅在 reviewLaunch 的
      hookEvents 白名单中新增 "SessionEnd"
      一项。
      • 原因：审查员会话沿用 Claude Code
      启动配置，必须与 panes.ts:claudeArgv
      注册的 7 个钩子完全对齐。
      •
      边界：未放宽任何权限、未改动沙箱配置
      （allowWrite:
      []）、未放宽超时与命令比较，严格保持
      了审查员启动的隔离约束。
  • panes.ts：
      • panes.ts:69：仅在 claudeArgv 的
      hooks 映射中增加 "SessionEnd"。
      • panes.ts:1399-1409：在 signal()
      中接收 Claude 的 SessionEnd
      钩子，严格校验 session_id === pane.
      native、!value.agent_id（排除子 agent
      干扰）、cwd 匹配、transcript_path
      文件名匹配以及 reason 存在，写入
      native_session_ended 事件并置 pane.
      nativeEnded = true。
      • panes.ts:1353：在 status() 中将
      pane.nativeEnded 纳入 lifecycle:
      'ended'。
      • panes.ts:107：在 stopThread()
      中允许已确认 pane.nativeEnded
      的会话被门禁回收（解决 /exit 产生
      busy 状态但 CLI 已退出的正常回收）。
      • 质量：全部使用 check()
      强拒绝校验，无吞异常、无重试、无容错
      fallback 或平行路径。


  ### 3. T-137 测试改动合规性

  • test_t137_reflect_e2e.py:123-145：
      • 仅修改了夹具内部的辅助函数
      ask()：在发起角色申请时补充上报
      cli='claude'、native_session、native_
      home，并通过既有 terminal_hook
      通道写入一个脚本化
      UserPromptSubmit，使该执行主控具备原
      生 CLI 回合凭据。
      • 严格保持原有断言：检查名（如
      ended_controllers_listed、executor_un
      der_ended_ideation 等 10
      项）、检查表达式与预期值（包含第 243
      行 by[e2]['state'] ==
      'running'）完全未变。符合主控裁定“只
      许改夹具不许改断言”。


  ### 4. 新测试独立性与运行证据核验

  • 独立性：新测试
  test_t146_session_state_e2e.py 和
  test_t146_cli_exit_probe.py
  的预期均直接来自 ticket
  与任务卡定义（空闲 worker 显示空闲、存活
  worker 显示运行中、CLI
  退出及终端关闭后显示已结束），不依赖被测
  代码当前输出。
  • 红态与变异：
      • red（--revision
      ebbae7bd0）：准确失败于
      AssertionError:
      reflect_idle，真实复现了修前 Reflect
      把空闲 worker 显示为运行中的缺陷。
      • mutant（--mutant reflect-
      lifecycle）：将 reflect.ts
      恢复为旧推导算法，同样准确失败于
      AssertionError: reflect_idle。
      • native-red：在修前版本上执行 CLI
      自然退出，准确失败于 AssertionError:
      CLI exited with live zsh:
      sidebar=unknown,
      reflect=running，证明修前无法识别 CLI
      退出事件。
  • 证据一致性：
      • outside-04-run-results.json 与
      outside04-20261023T104746Z-9083/
      下的所有原始结果（green.json、native-
      green.json、t111.json、t137.
      json、session-end.json、reviewer-
      hooks.json）完全吻合，所有 6
      项绿态均为 PASS，退出码均为
      0，无虚报或假通过。

  ──────
  ## 发现项列表

   编号 │ 位置     │ 严重度   │ 说明与场景
  ──────┼──────────┼──────────┼────────────
   F01  │ panes.ts │ P3（观察 │ SessionEnd
        │ :1403    │ ）       │ 钩子对
        │          │          │ transcript
        │          │          │ 文件名的强
        │            │        │ 契约：当前
        │            │        │ 校验要求
        │            │        │ basename(t
        │            │        │ ranscript_
        │            │        │ path) ===
        │            │        │ ${pane.nat
        │            │        │ ive}.jsonl
        │            │        │ ``。该契约
        │            │        │ 符合官方
        │            │        │ Claude
        │            │        │ Code
        │            │        │ 行为且成功
        │          │          │ 防御了伪造
        │          │          │ 或外部会话
        │          │          │ 注入，但若
        │          │          │ 未来 CLI
        │          │          │ 变更
        │          │          │ transcript
        │          │          │ 命名规范，
        │          │          │ 会在此处触
        │          │          │ 发
        │          │          │ session_en
        │          │          │ d_mismatch
        │          │          │ 拒绝。当前
        │          │          │ 环境与测试
        │          │          │ 已通过，不
        │          │          │ 构成缺陷。
   F02  │ reflect. │ P3（提示 │ 已批准终端
        │ ts:146   │ ）       │ 主控状态回
        │          │          │ 退：若某个
        │          │          │ 已批准的主
        │          │          │ 控终端未产
        │          │          │ 生任何回合
        │          │          │ 且非
        │          │          │ Claude
        │          │          │ 原生会话，
        │          │          │ sessionSta
        │          │          │ tes.get(ro
        │          │          │ w.launch)
        │          │          │ 会返回
        │          │          │ unknown（
        │          │          │ 未知），Re
        │          │          │ flect
        │          │          │ 亦展示为“
        │          │          │ 未知”。该
        │          │          │ 行为与侧栏
        │          │          │ 对无回合终
        │          │          │ 端主控的展
        │          │          │ 示完全对齐
        │          │          │ ，符合同源
        │          │          │ 设计。

  (注：审查过程中未发现 P0、P1 或 P2
  级别缺陷。)
  ──────
  ## 结论

  本次改动完整实现了 ticket T-146
  的目标，将
  Reflect、侧栏与流程页的状态及标签统一收口
  至编排后台单源计算，彻底消除了 Reflect
  自算导致的“已结束/已空闲仍显示运行中”缺陷
  ；门禁与 panes.ts
  的改动严格受限于主控授权范围；T-137
  仅微调夹具未改动任何断言；新测试具备独立
  oracle，红态与变异充分有效，沙箱外完整
  e2e 与回归证据齐备。

  T-146 REVIEW PASS
```
