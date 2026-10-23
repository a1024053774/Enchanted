# T-146-4 独立审查 01（agy）

- 审查员：agy 1.4.6，模型 gemini-3.8-flash-high，Herdr 可见窗格 wG:pN，交互 auto 模式（只用读文件工具），只读副本，候选 c3caced73。第一次启动因内置盘满（ENOSPC）未起，清理后在同一窗格重启。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-146-a4-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-146-a4-r1/prompt.txt)"
# pane wG:pN started 2026-10-23T14:37:12Z
# restarted in pane wG:pN 2026-10-23T15:05:02Z after disk-full (ENOSPC) prevented the first start
```

- 审查后核对：候选副本 git status 0 行改动。结论 PASS，一条 P3（说明性，README 表述准确）。

## 窗格中的报告原文

```text

○ Thought for 3m 56s (The `AssertionError` message in...)
● Explored 43 files (card.md, 20261023T125315Z-ideati...)
● Explored 1 file (candidate.diff) (ctrl+o to expand)

▸ Thought for 21s

   T-146-4 独立审查报告

  作为 a2a 项目的只读独立审查员，对 T-146 第四个
  attempt（T-146-4 / 候选
  c3caced73）进行了全项代码审计、测试及证据核查。本审查
  未执行任何 shell 命令，未写入任何文件。
  ──────
  ## 一、审查核对结论

  ### 1. 判定是否落在根因与三状态一致性

  • 根因分析：
      • T-146-3 的回归失败（T-133/T-107
      test_t133_t107_terminal_controller_e2e.py
      超时“超时：身份已放弃”）根因在于：T-146-3 在
      sidebar.ts:173-185
      中将所有曾生效过角色的终端无条件保留在 agents
      中，并以 roleRequest.state === 'ended'
      判定会话结束。当用户在运行中的终端交回角色（a2a
      release）时，roleRequest.state 变为
      'ended'，但终端本身并未关闭。此时侧栏仍保留该终端
      为“已结束的主控”，导致 T-133/T-107
      等待主控条目消失超时。
      • T-146-4
      的修复落在生命周期真实根因：以终端窗格生命周期（s
      idebar.ts:177-181 pane?.lifecycle ===
      'ended'）区分终端关闭与角色交回，而非依赖
      roleRequest.state。
  • 三种状态展示核对：
      1. approved 的角色（终端运行中且角色有效）：
          • sidebar.ts:178：roleRequest.state ===
          'approved'，不跳过，推入 agents；
          • sidebar.ts:180-181：state
          取真实回合状态（last 或 running/unknown）；
          • sidebar.ts:189-190：agents 中已包含该
          launch，普通终端 terminals 过滤排除；
          •
          表现：侧栏作为主控显示当前回合状态，不作为普
          通终端显示。符合预期。
      2. 已结束终端上的角色（终端关闭 / pane lifecycle
      ended）：
          • sidebar.ts:178：pane?.lifecycle === 'ended'
          为真，无论角色是 approved 还是 ended
          均不跳过；
          • sidebar.ts:180：state 确定为 'ended'；
          • sidebar.ts:189-190：launch 在 agents
          中，不在 terminals 中；
          •
          表现：侧栏保留该主控条目并标“已结束”，不重新
          作为普通终端出现。完全符合裁定 B。
      3. 交回角色的活终端（roleRequest.state 为
      ended，但 pane 仍在运行）：
          • sidebar.ts:178：roleRequest.state !==
          'approved' 且 pane?.lifecycle !==
          'ended'，执行 continue 跳过主控列表；
          • sidebar.ts:189-197：agents 中不再含有该
          launch，落入普通终端遍历，按 pane?.lifecycle
          显示为普通终端（如 running 或 unknown）；
          •
          表现：侧栏主控条目消失，恢复为普通终端显示其
          真实生命周期状态。完全符合 T-133/T-107 合同。

  • Reflect 与 Flow 的同源一致性：
      • 流程页（Flow）：flow.ts:51-55 直接调用
      sidebarSnapshot 并消费 sidebar.
      agents，与侧栏完全同源，自动与侧栏保持一致；
      • Reflect 页：reflect.ts:28-35
      遍历该项目历来所有生效过的角色申请（held）。交回
      角色的历史条目因 row.state === 'ended' 标为
      'ended'；仍在有效期的角色通过 sessionStates.
      get(row.launch)
      消费侧栏投影状态。既保留了历史角色轨迹且标为“已结
      束”，又让有效会话与侧栏同源。无须修改 reflect.ts
      即可自然满足语义。

  ──────
  ### 2. 是否会导致 T-146-2
  的问题回归（关闭主控后被重新列为普通终端）

  • 否，不会回归：
      • 当主控终端关闭时，底层窗格生命周期为 pane?.
      lifecycle === 'ended'。
      • 在 sidebar.ts:178，条件 pane?.lifecycle !==
      'ended' 为假，主控条目被保留推入 agents（状态为
      ended）。
      • 在 sidebar.ts:189-190，普通终端判定 !agents.
      some(agent => agent.id === record.id)
      明确排除了已在 agents 中的终端 launch。
      • 既有单元测试
      test_t146_ended_projection.mjs:51-59 明确断言
      Closed confirmed controller must remain an agent
      且 No ordinary-terminal
      duplicate，在外部执行中完全
      PASS（ended-projection.json）。
      • 变异测试 controller-becomes-
      shell（模拟关闭后降为普通终端）在真实场景下被
      test_t146_session_state_e2e.py
      捕获并成功拒绝（t146-mutant-controller.json），表
      明防止该回归的屏障坚固有效。

  ──────
  ### 3. 修改边界、验收文件与代码质量审查

  • 修改边界与受保护文件：
      • 核对 full.diff：改动仅包含 workbench/README.
      md、workbench/src/sidebar.
      ts、workbench/tests/test_t146_release_visibility_
      e2e.py（新文件）与
      workbench/tests/test_t146_released_projection.
      mjs（新文件）。
      • 禁止修改的文件（flow.ts、FlowPage.
      tsx、gates/**、.project-map/**、AGENTS.
      md、CONTEXT.md）一律未被触碰。
      • 7
      项验收受保护文件（oracle_paths）未发生任何修改。
  • 断言与超时：
      • 未放宽任何既有测试断言，未加长任何等待超时。
  • 异常处理与路径设计：
      • 无任何吞异常（未引入空 catch 或屏蔽错误）。
      • 无 fallback、重试或投机性兼容 shim。
      • 逻辑在投影生成核心直接区分，无平行路径。

  ──────
  ### 4. 新测试、判定脚本与 .strip() 判据核对

  • 测试独立性：
      •
      test_t146_released_projection.mjs：独立于具体实现
      代码，按 ticket 规格构造 SQLite 夹具并传入明确的
      pane
      lifecycle（running、unknown、ended），断言交回、
      多角色交替和关闭终端时的各投影输出，并验证只读性
      。
      •
      test_t146_release_visibility_e2e.py：作为观测包装
      器，完全继承并运行原
      test_t133_t107_terminal_controller_e2e.py
      的全部逻辑与断言；仅在 放弃身份的回合结束
      阶段切入，增加对真实 Electron DOM 与后端 API 在
      Sidebar、Flow、Reflect 三处的严格断言。
  • 变异有效性：
      • 变异 stale-terminal-
      ui（在隔离前端中强制将普通终端 UI 标为
      ended）成功通过 DOM
      等待超时被拒绝，捕获了“后台已恢复为普通终端但 UI
      仍标已结束”的缺陷场景。
      • 变异 controller-becomes-
      shell（关闭主控后降为普通终端）成功被
      test_t146_session_state_e2e.py 捕获。
  • .strip() 判据修正分析：
      • 起因：scripted_claude.py:307 中 Electron.until
      超时格式化语句为 f'超时：{label} {last or
      ""}'。当表达式在评估中为 falsy
      且未抛出异常时，last 为
      None，格式化后末尾携带一个空格（"超时：交回后普通
      终端可见且运行中 "）。
      • 原 RUN-OUTSIDE-01.sh:66
      采用无空格的字面量严格相等判定，导致真实变异反例
      被误拒。
      • RUN-OUTSIDE-02.sh:40, 66 将错误字符串加上 .
      strip() 进行比较。
      • 判据未放宽：.strip()
      仅剥离首尾格式化空白字符，比对目标依然是完整的前
      缀和标签字符串（非 in
      或通配），且判定脚本继续强校验了非零退出码、visib
      ility_mutant 标记、前置 API 运行中检查、DOM
      确实呈现 ended 的完整业务违约字段（assert
      v['observed']['sidebar_dom'] ==
      [dict(state='ended', role='普通终端',
      ordinary=True, visible=True)]）。没有任何放宽。

  ──────
  ### 5. 发现项清单

  本次审查未发现 P0、P1 或 P2 级别缺陷。仅记录 1 项 P3
  提示性说明：

  • [P3] 文件路径引用说明：
      • 文件：README.md:20 与 card.md:8
      • 说明：README 中补充了对新增测试
      test_t146_released_projection.mjs
      的说明，表述准确，文档与实现严密对应。

  ──────
  ## 二、审查最终结论

  T-146-4 的改动精准落于根因，完全满足用户裁定 B 及 T-
  133/T-107
  合同；边界约束严格遵循；测试反例与变异真实有效；全套
  沙箱外回归与独立验证全部通过。

  T-146-4 REVIEW PASS
```
