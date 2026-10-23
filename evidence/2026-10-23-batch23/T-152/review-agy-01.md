# T-152 独立审查 01（agy）

- 审查员：agy 1.4.6，gemini-3.8-flash-high，Herdr 可见窗格 wG:p1A，auto 模式只用读文件工具，只读副本，候选 ba8745b93。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-152-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-152-r1/prompt.txt)"
# pane wG:p1A started 2026-10-23T19:56:33Z candidate ba8745b93914cb7b9ebec31bb13992855acd4c6b
```

- 审查后候选副本 git status 0 行改动。结论 PASS，无 P0–P3 发现。

## 窗格中的报告原文

```text
○ Thought for 5m 31s (`t152_review_host...)
● Explored 62 files (ctrl+o to expand)

▸ Thought for 20s

   T-152 只读独立审查报告

  审查对象：T-152 候选提交
  ba8745b93（相对起点 32ffb4e6d
  的全部改动见 full.diff）
  审查范围：workbench/tests/test_t082_revi
  ew_boundary_e2e.py、workbench/tests/t152
  _review_host.ts、workbench/tests/t152_re
  al_review_submit.json，以及
  evidence/2026-10-23-batch23/T-152/
  内的任务卡、RESULTS、FLOW-
  AUDIT、变异与运行记录。
  审查角色：只读独立审查员（未运行任何
  shell 命令、未写任何文件）。
  ──────
  ## 审查结论汇总

  根据用户授权 user-
  decision.md（构思主控转达
  20261023T185657Z-ideation-answer-
  001）、任务卡 CARD.md、ticket
  T-152-migrate-t082-review-boundary.md，
  以及 T-082、T-141
  现行契约与产品实现代码，逐项核对结果如下
  ：

  1.
  断言过时性与独立依据：符合要求。修改的网
  络与启动断言确因 T-141
  放宽网络限制而过时，新断言依据 T-141
  规格/ticket/裁定及产品门禁代码
  gates/core.ts:2383–2392，并非抄录被测代
  码输出；未借迁移放松任何有效检查。
  2. 有效检查保留情况：全部保留。ticket
  列出的 5
  项核心检查（审查副本建立/清理、共享 refs
  变化作废、review_requirements.workspace
  绑定、结束核对完成前拒绝集成含 held
  socket
  正负对照、脏结束作废）及原套件所有 18
  条业务断言完整保留，无一弱化、跳过或删除
  。
  3.
  红态有效性与变异代表性：全部落在保留的有
  效检查上。4 个业务变异（no-end-
  check、nonempty-workspace、omit-shared-
  refs、false-copy-removed）分别精准命中
  REVIEW-END-BEFORE-INTEGRATE、REVIEW-
  REQUIREMENTS-WORKSPACE、REVIEW-REFS-
  INVALIDATE、T082-COPY-
  REMOVED，均为真实的门禁安全缺陷；4
  个非法启动变异命中 T082-LAUNCH-REFUSED。
  4.
  修改边界与产品代码完整性：严格守界。产品
  代码 workbench/src/** 与
  workbench/app/**
  零修改；未修改任何共享基类测试文件（test
  _quality_chain_e2e.
  py、test_quality_tracer_e2e.
  py、controlled_quality_pty.
  ts）或其他测试；新增的专用 host 与 JSON
  仅被本测试引用；.project-map/**
  未纳入交付提交。
  5. 局部覆盖与 Stop
  信封真实性：确认无旁路与伪造。本地
  release_worker、stop_turn、send_review
  与 held-socket Stop
  均调用真实门禁命令或直连真实 control.
  sock，错误时立即抛出
  HarnessFailure；Stop 信封中的 cwd 与
  transcript_path 均动态提取自当前 launch
  在受控 PTY 中登记的真实 worktree 与
  rollout
  日志路径，无任意路径、无跳过校验、无伪造
  结果；改动规模完全符合“迁移本文件”。
  ──────
  ## 逐项详细审查证据

  ### 1. 被改断言过时性与独立依据核对

  • 断言 T082-REVIEW-
  ARGV（test_t082_review_boundary_e2e.py:1
  23–133）：
      • 旧断言：要求
      sandbox_workspace_write.
      network_access=false 与 features.
      network_proxy=false。
      • 过时事实：T-141
      票（T-141-loosen-managed-limits.md）
      决议“网络全开，不再强行关闭代理”。生
      产代码 panes.ts:734 启动参数为
      sandbox_workspace_write.
      network_access=true，并不再附加
      proxy 关闭开关。
      • 新断言独立依据：
          1. T-141 授权与分辨率明确“Codex
          审查员一次性副本仍以 untrusted
          打开，网络全开，-a never
          保留”（参见 20261023T151224Z-
          ideation-answer-001 及 T-141
          Resolution）。
          2. 门禁生产代码
          gates/core.ts:2386–2391
          明确要求审查员启动必须包含：-a
          never、projects={...
          =trust_level="untrusted"}、sandb
          ox_workspace_write.
          network_access=true、sandbox_wor
          kspace_write.
          exclude_slash_tmp=true、sandbox_
          workspace_write.
          exclude_tmpdir_env_var=true。
      •
      判定：断言确实过时，新断言直接来自规
      格与门禁守则，且增加了对 -a never 与
      untrusted
      绑定的断言，未放松仍有效的沙箱与临时
      目录排除检查。
  • 断言 REVIEW-END-BEFORE-
  INTEGRATE（test_t082_review_boundary_e2e
  .py:354–356）：
      • 改动：由原来的 finally: held.
      close() 之后检查移至 socket
      关闭之前，并新增要求 result.
      get('error') ==
      'review_end_check_required'。
      • 独立依据：生产代码 core.ts:2416 的
      requireGate(ended,
      "review_end_check_required")。
      •
      判定：强化了断言（从任意错误收窄为精
      准错误码匹配），且在释放 held socket
      之前立即验证门禁拦截，防止坏实现先集
      成后因后续夹具错误掩盖红态。
  • 默认执行列表排除
  launch_boundary_refused（test_t082_revie
  w_boundary_e2e.py:415）：
      • 事实与依据：该 case 断言 verify
      启动被门禁拒收（review_launch_bounda
      ry）。在未被变异的合法产品代码上，启
      动参数完全合法，verify
      必然成功；将它直接作为无变异的绿态运
      行属于逻辑矛盾。本票 runner
      run_suite.py 专门为该 case 提供了 4
      个启动参数变异（readonly-
      argv、wrong-workspace、network-
      disabled、tmp-
      writable）进行专门验证，该 case 的 3
      条断言没有被删除或弱化。

  ──────
  ### 2. ticket 列出的有效检查保留核对

  对 ticket
  明确要求保留的各项检查逐一在代码中核实：

   ticket 要求… │ 对应测试方… │ … │ … │ …
  ──────────────┼─────────────┼───┼───┼───
   审查副本建立 │ tracer_revi │ T │ t │
                │ ew_copy     │ 0 │ e │ 保
                │             │ 8 │ s │ 留
                │             │ 2 │ t │ ：
                │             │   │ _ │ 校
                │             │   │ t │ 验
                │             │   │ 0 │ 目
                │             │   │ 8 │ 录
                │             │   │ 2 │ 存
                │             │   │ _ │ 在
                │             │   │ r │ 、
                │             │   │ e │ 无
                │             │   │ v │ g
                │             │   │ i │ i
                │             │   │ e │ t
                │             │ -C│ w │ 、
                │             │   │ _ │ 以
                │             │   │ b │ 及
                │             │   │ o │ e
                │             │   │ u │ v
                │             │   │ n │ i
                │             │   │ d │ e
               │              │   │ a │ w
               │              │   │ r │ _
               │              │   │ y │ c
            │          │          │ _ │ a
            │          │          │ e │ n
            │          │          │ 2 │ d
          │        │        │         │ i
                │ w_copy │ -C │ 45: │ ：
               │              │   │ p │ a
               │              │   │ y │ t
               │              │   │ : │ e
               │              │   │ 2 │ _
               │              │   │ 3 │ c
               │              │   │ 4 │ o
               │              │   │ – │ p
               │              │   │ 2 │ y
               │              │   │ 3 │ _
               │              │   │ 7 │ c
               │              │   │   │ r
               │              │   │   │ e
               │              │   │   │ a
               │              │   │   │ t
               │              │   │   │ e
               │              │   │   │ d
               │              │   │   │ 事
               │              │   │   │ 件
   审查副本清  │ tracer_revie │ T │ : │
   理          │ w_copyreal_p │ 0 │ 2 │ 保
               │ ayload_repor │ 8 │ 4 │ 留
               │ t_roundtrip  │ 2 │ 3 │ ：
               │              │   │ – │ 校
               │              │   │ 2 │ 验
               │              │   │ 4 │ 副
               │              │   │ 5 │ 本
               │              │   │ : │ 目
               │              │   │ 3 │ 录
               │              │   │ 9 │ 已
               │              │   │ 9 │ 不
               │              │   │ – │ 存
               │              │   │ 4 │ 在
               │              │   │ 0 │ 、
               │              │   │ 0 │ 以
               │              │   │   │ 及
               │              │   │   │ e
               │              │   │   │ v
               │              │   │   │ i
               │              │   │   │ e
               │              │   │   │ w
            │          │          │   │ _
            │          │          │   │ c
               │              │   │   │ a
               │              │   │   │ n
               │              │   │   │ d
               │              │   │   │ i
               │              │   │   │ d
               │              │   │   │ a
               │              │   │   │ t
               │              │   │   │ e
               │              │   │   │ _
               │              │   │   │ c
               │              │   │   │ o
               │              │   │   │ p
               │              │ -C│   │ y
               │              │   │   │ _
               │              │   │   │ r
               │              │   │   │ e
               │              │   │   │ m
               │              │   │   │ o
               │              │   │   │ v
               │              │   │   │ e
               │              │   │   │ d
               │              │   │   │ 事
               │              │   │   │ 件
   共享 refs   │ shared_refs_ │ R │ : │
   变化作废    │ changed      │ E │ 2 │ 保
               │              │ V │ 8 │ 留
               │              │ I │ 8 │ ：
               │              │ E │ – │ 校
               │              │ W │ 2 │ 验
               │              │   │ 9 │ a
               │              │   │ 4 │ s
               │              │   │   │ k
               │              │   │   │ p
               │              │   │   │ a
               │              │   │   │ u
               │              │   │   │ s
               │              │   │   │ e
               │              │   │   │ d
               │              │   │   │
               │              │   │   │
               │              │   │   │
               │              │   │   │
               │              │   │   │
               │              │ -R│   │
               │              │   │   │ 、
               │              │   │   │ n
               │              │   │   │ k
               │              │   │   │ n
               │              │   │   │ o
               │              │   │   │ w
               │              │   │   │ n
               │              │   │   │ 、
               │              │   │   │ 保
               │              │   │   │ 留
               │              │   │   │ 现
               │              │   │   │ 场
               │              │   │   │ 副
               │              │   │   │ 本
               │              │   │   │ 、
               │              │   │   │ 主
               │              │   │   │ 分
               │              │   │   │ 支
               │              │   │   │ 未
               │              │   │   │ 推
               │              │   │   │ 进
               │              │   │   │ 、
               │              │   │   │ 上
               │              │   │   │ 报
               │              │   │   │ s
               │              │   │   │ s
               │              │   │   │ u
               │              │   │   │ e
               │              │   │   │ 、
               │              │   │   │ 记
               │              │   │   │ 录
               │              │   │   │ e
               │              │   │   │ v
               │              │   │   │ i
               │              │   │   │ e
               │              │   │   │ w
               │              │   │   │ _
               │              │   │   │ s
               │              │   │   │ h
               │              │   │   │ a
               │              │   │   │ r
             │           │        │   │ e
            │          │          │   │ d
          │        │        │         │ _
               │              │   │   │ r
               │              │   │   │ e
               │              │   │   │ f
               │              │   │   │ s
               │              │   │   │ _
               │              │   │   │ c
               │              │   │   │ h
               │              │   │   │ a
               │              │   │   │ n
               │              │   │   │ g
               │              │   │   │ e
               │              │   │   │ d
               │              │   │   │ 、
               │              │   │   │ 禁
               │              │   │   │ 止
               │              │   │   │ e
               │              │   │   │ c
               │              │   │   │ l
               │              │   │   │ a
               │              │   │   │ i
               │              │   │   │ m
   requirement │ requirements │ R │ : │
   s.workspace │ _workspace_c │ E │ 3 │ 保
   绑定        │ hanged       │ V │ 0 │ 留
               │              │ I │ 5 │ ：
               │              │ E │ – │ 校
               │              │ W │ 3 │ 验
               │              │   │ 0 │ 篡
               │              │   │ 8 │ 改
               │              │   │   │ o
               │              │   │   │ r
               │              │   │   │ k
               │              │   │   │ s
               │              │   │   │ p
               │              │   │   │ a
               │              │   │   │ c
               │              │   │   │ e
               │              │   │   │ 时
               │              │   │   │ 立
               │              │   │   │ 即
               │              │   │   │ a
               │              │   │   │ u
               │              │   │   │ s
               │              │   │   │ e
               │              │   │   │ d
               │              │   │   │
               │              │   │   │
               │              │   │   │
               │              │ -R│   │
               │              │   │   │
               │              │   │   │
               │              │   │   │ 、
               │              │   │   │ n
               │              │   │   │ k
               │              │   │   │ n
            │          │          │   │ o
            │          │          │   │ w
            │          │          │   │ n
            │          │          │   │ 、
          │        │        │         │ 拒
               │              │   │   │ 绝
               │              │   │   │ 且
               │              │   │   │ 无
               │              │   │   │ e
               │              │   │   │ v
               │              │   │   │ i
               │              │   │   │ e
               │              │   │   │ w
               │              │   │   │ _
               │              │   │   │ r
               │              │   │   │ e
               │              │   │   │ s
               │              │   │   │ u
               │              │   │   │ l
               │              │   │   │ t
               │              │   │   │ 落
               │              │   │   │ 库
   结束核对完  │ integration_ │ R │ : │
   成前拒绝集  │ before_end_c │ E │ 3 │ 保
   成（held    │ heck(dirty=T │ V │ 5 │ 留
   socket      │ rue)         │ I │ 4 │
   负对照）    │              │ E │ – │
               │              │ W │ 3 │
               │              │   │ 5 │
               │              │   │ 6 │ ：
               │              │   │ : │ o
               │              │   │ 3 │ c
               │              │   │ 6 │ k
               │              │   │ 4 │ e
               │              │   │ – │ t
               │              │   │ 3 │ 窗
               │              │   │ 6 │ 口
               │              │   │ 8 │ 期
               │              │   │   │ 集
               │              │   │   │ 成
               │              │   │   │ 被
               │              │   │   │ 拒
               │              │   │   │ 且
               │              │   │   │ 返
               │              │   │   │ 回
               │              │   │   │ e
               │              │   │   │ v
               │              │   │   │ i
               │              │   │   │ e
               │              │   │   │ w
               │              │   │   │ _
               │              │   │   │ e
               │              │   │   │ n
               │              │   │   │ d
               │              │   │   │ _
               │              │   │   │ c
               │              │   │   │ h
               │              │   │   │ e
               │              │   │   │ c
               │              │   │   │ k
               │              │   │   │ _
               │              │   │   │ r
               │              │   │   │ e
               │              │   │   │ q
               │              │   │   │ u
               │              │   │   │ i
               │              │   │   │ r
               │              │   │   │ e
               │              │ -E│   │ d
               │              │   │   │ ；
               │              │   │   │ 释
               │              │   │   │ 放
               │              │   │   │ 后
            │          │          │   │ 脏
            │          │          │   │ 变
            │          │          │   │ 更
          │        │        │         │ 导
          │        │        │         │ 致
             │           │        │   │ 作
             │           │        │   │ 废
             │           │        │   │ 、
             │           │        │   │ 不
             │           │        │   │ 集
             │           │        │   │ 成
             │           │        │   │ 、
             │           │        │   │ 不
             │           │        │   │ 回
             │           │        │   │ 收
             │           │        │   │ 并
             │           │        │   │ 上
             │           │        │   │ 报
             │           │        │   │ s
             │           │        │   │ s
             │           │        │   │ u
             │           │        │   │ e
   结束核对  │ integrati │ REVIEW │ : │
   完成前拒  │ on_before │ -END-  │ 3 │ 保
   绝集成（h │ _end_chec │ BEFORE │ 5 │ 留
   eld       │ k_clean(d │ -INTEG │ 4 │
   socket    │ irty=Fals │ RATET0 │ – │
   正对照）  │ e)        │ 82-    │ 3 │
             │           │ INTEGR │ 5 │
             │           │ ATE-   │ 6 │ ：
             │           │ AFTER- │ : │ 窗
             │           │ END    │ 3 │ 口
             │           │        │ 7 │ 期
             │           │        │ 0 │ 同
             │           │        │ – │ 样
             │           │        │ 3 │ 拒
            │          │          │ 7 │ 绝
          │        │        │         │ 集

  ──────
  T-152 REVIEW PASS

─────────────────────────────────────────────
>
─────────────────────────────────────────────
? for shortcuts       Gemini 3.8 Flash · high
```
