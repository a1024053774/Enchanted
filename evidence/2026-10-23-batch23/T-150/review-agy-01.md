# T-150 独立审查 01（agy）

- 审查员：agy 1.4.6，gemini-3.8-flash-high，Herdr 可见窗格，auto 模式只用读文件工具，只读副本。
- 启动 argv：

```
agy --model gemini-3.8-flash-high --mode auto --add-dir /Users/luckye/Documents/Code/a2a-review/T-150-r1 -i "$(cat /Users/luckye/Documents/Code/a2a-review/T-150-r1/prompt.txt)"
# pane wG:p16 started 2026-10-23T19:15:30Z candidate 4aefa2b3a884fde62c6bb72d074165111496f016
```

- 审查后候选副本 git status 0 行改动。结论 PASS，无发现。

## 窗格中的报告原文

```text
○ Thought for 3m 6s (If `save...)
● Explored 17 fil... (ctrl+o to
expand)

▸ Thought for 44s
   T-150
  独立审查报告：workbench/tests
  /test_t091_pane_ipc.mjs
  契约迁移与红绿验证

  ## 1. 审查概述

  • 审查对象：Ticket T-
  150（候选提交 4aefa2b3a
  相对起点 32ffb4e6d）
  • 授权依据：user-decision.
  md（用户 2026-10-23
  裁定选择选项
  C，授权迁移受保护测试文件
  workbench/tests/test_t091_pan
  e_ipc.
  mjs，保留有效安全检查并在现行
  代码取得红绿态）
  • 代码变动范围：仅修改
  workbench/tests/test_t091_pan
  e_ipc.mjs（见 full.
  diff），无任何产品代码变动，
  无新增辅助测试模块
  •
  证据记录：candidate/evidence/
  2026-10-23-batch23/T-150/（含
  ASSERTIONS.md、RESULTS.
  md、RUN-LOCAL-01.sh
  及运行输出 local-01-
  DgE6Uo/summary.json）
  •
  审查结论：PASS（各项核对均成
  立，无 P0–P2 缺陷）
  ──────
  ## 2. 核心核对项审查结果

  ### 2.1
  被改断言的过时依据与新期望来
  源核实

  审查逐行比对 full.diff 与
  candidate/evidence/2026-10-
  23-batch23/T-
  150/ASSERTIONS.md 中的 189
  处原始断言项，确认所有被改动
  断言均有明确、独立的现行规格
  与 Ticket
  依据，不存在抄录产品当前输出
  作为测试期望的情况，也没有借“
  迁移”弱化任何既有安全保证：

  1. 旧“默认第一次启动显示当前
  worker”改为“未指定 task
  启动为空布局，显式 task
  初次启动回退当前 worker”：
      • 依据：T-119（无 task
      启动契约）与 T-
      139（多视图模型）。在
      workbench/app/main.ts 的
      prepareSelection 中，无
      task
      启动为顶层项目/概览视图，
      不得自动分配 worker
      或签发输入凭据；显式指定
      task
      启动且未持久化布局时，依
      然保持回退 worker
      并保存布局的检查。
      •
      核实：test_t091_pane_ipc.
      mjs:171-183 增加了对
      run({ state, userData })
      的断言，不仅检查窗格 key
      数量为 0，还严格断言
      credentialNumber ===
      0；紧接着保留显式 task
      启动持久化 worker
      的正向验证。
  2. IPC 名单改为 38 个
  Handler、40 个 Bridge
  成员的依据充分性：
      • 依据：原测试写死 23 个
      Handler / 24 个 Bridge
      成员，源自早期历史契约。
      自 T-119 以来，主进程与
      preload
      陆续按票据增加了跨进程通
      信接口：
          • T-119：a2a:decide-
          role-request /
          decideRoleRequest（1
          个）
          • T-132：a2a:issues /
          issues、a2a:issue-
          answer /
          answerIssue、a2a:issu
          e-dispose /
          disposeIssue（3 个）
          • T-134：a2a:records
          /
          records、a2a:metrics
          / metrics（2 个）
          • T-135：a2a:archive-
          usage /
          archiveUsage（1 个）
          • T-
          136：a2a:retrospectiv
          es /
          retrospectives、a2a:r
          etrospective-start /
          startRetrospective、a
          2a:retrospective-
          schedule /
          saveRetrospectiveSche
          dule、a2a:retrospecti
          ve-decide /
          decideRetrospectiveSu
          ggestion（4 个）
          • T-137：a2a:reflect
          / reflect（1 个）
          • T-140：a2a:project-
          settings /
          projectSettings、a2a:
          pick-extra-directory
          /
          pickExtraDirectory（2
          个）
          • T-
          112：a2a:execution-
          settings /
          executionSettings（1
          个，原测试作为可配置
          分支处理，现行合同常
          驻）
      • 核实：经核对
      workbench/app/main.ts（第
      164–505 行），实际注册的
      ipcMain.handle 确为 38
      个（28 个窗口级接口 + 10
      个窗格级接口）；workbench
      /app/preload.ts（第 12–54
      行）暴露的属性确为 40
      个（38 个 IPC 方法 +
      paneKeys、home 2
      个只读属性）。测试通过
      expectedHandlers 和
      expectedBridge
      对集合一致性及单次注册进
      行了严格的双向断言，依据
      完全成立。
      • 特别亮点：在
      test_t091_pane_ipc.mjs:58
      -78 的 windowInterfaces
      与 paneInterfaces
      声明中，为全部 38
      个接口提供了合法参数夹具
      （如真实 UUID
      格式哨兵、非空数组等），
      确保后续在执行
      iframe/未知发送方拒绝断言
      时，被测代码绝不会因“参数
      校验失败”提早报错而伪通过
      ，必须真正穿透到
      windowTarget 验证
      /Unknown window/。
  3. 被删除的“无 task
  不能创建终端”分支依据充分性：
      • 依据：原测试中
      withShell && !withPanes
      模式下曾包含断言 await
      assert.rejects(() =>
      bridge.newTerminal(),
      /请先选择任务/)。但该限制
      早在 T-119
      支持未归属终端（unassigne
      d
      shell）与项目终端时已被取
      代。在原测试的默认合同
      questions-flow
      中，withPanes
      恒为真，该分支本就是死代
      码。
      • 核实：main.
      ts#createTerminal（第
      594–606 行）与
      prepareSelection（第 650
      行）明确支持 project ===
      null
      时的独立终端（工作目录回
      退用户
      Home）。test_t091_pane_ip
      c.mjs:555-559
      正确删除了旧模式分支，保
      留并执行了未归属终端的正
      向创建、cwd
      检查及独立凭据关闭，依据
      充分成立。
  4.
  任务终端创建与项目终端视图分
  离（T-139 导航模型）：
      •
      依据：原测试要求在任务内
      新建终端时 created.
      paneKeys.length ===
      selectedAgain.paneKeys.
      length +
      1，即将终端直接混入当前任
      务窗格。T-139
      将终端归属提升至项目级，
      任务内新建终端会自动切至
      项目终端视图，任务窗格与
      终端窗格解耦。
      •
      核实：test_t091_pane_ipc.
      mjs:560-596
      将断言调整为：创建后切入
      项目终端视图（created.
      task === null，paneKeys.
      length ===
      1，不复用原任务
      key）。同时补充了完整的闭
      环导航验证（项目概览为空
      窗格 → 切换回任务仅显示
      agent 窗格且终端停泊禁写
      → 重新选择终端 agent 复用
      key 与原凭据 →
      显式关闭清空布局），没有
      遗漏任何边界。

  ──────
  ### 2.2 Ticket
  所列有效检查保留情况核实

  对照 Ticket T-150
  验收标准，全部有效边界均完整
  保留并得到了防御性加固：

   Ticket 规…  │ 测试实现与… │
  ─────────────┼─────────────┼─
   跨窗 pane   │ [test_t091_ │
   key 拒收    │ pane_ipc.mj │
               │ s#L201-     │
               │ L207](file: │
               │ ///Users/lu │
               │ ckye/Docume │
               │ 窗 key 及   │
               │ [bKey,      │
               │ undefined,  │
               │ '', 17,     │
               │ 'unregister │
            │ 'unregist │
            │ ered-     │
               │ ed, '', │
               │ 17,     │
               │ 'unregi │
               │ stered- │
               │ sentine │
               │ l']，要 │
               │ 求精确  │
                   │ 测  │
                   │ 试  │
                   │ 外  │
                   │ 窗  │
                   │ key │
                   │ 及  │
                   │ [bK │
                   │ ey, │
                   │ und │
                   │ efi │
                   │ ned │
                   │ ,   │
                   │ '', │
                   │ 17, │
                   │ 'un │
                   │ reg │
                   │ ist │
                   │ ere │
                   │ d-  │
                   │ sen │
                   │ tin │
                   │ el' │
                   │ ]， │
                   │ 要  │
                   │ 求  │
                   │ 精  │
                   │ 确  │
                   │ 拒  │
                   │ 绝  │
                   │ /Un │
                   │ kno │
                   │ wn  │
                   │ pan │
                   │ e   │
                   │ key │
                   │ /， │
                   │ 且  │
                   │ 传  │
                      │ f │
                      │ i │
                      │ n │
                      │ e │
                      │ d │
                      │ , │
                      │ ' │
                      │ ' │
                      │ , │
                      │ 1 │
                      │ 7 │
                      │ , │
                      │ ' │
                      │ u │
                      │ n │
                      │ r │
                      │ e │
                      │ g │
                      │ i │
                      │ s │
                      │ t │
                      │ e │
                      │ r │
                      │ e │
                      │ d │
                      │   │
                      │   │
                      │   │
                      │   │
                      │   │
                      │   │
                      │   │
                      │   │
                      │   │
                      │   │
                      │ -s│
                      │ ，│
                      │ 要│
                      │ 求│
                      │ 精│
                      │ 确│
                      │ 拒│
                      │ 绝│
                      │ U │
                      │ n │
                      │ k │
                      │ n │
                      │ o │
                      │ w │
                      │ n │
                      │ p │
                      │ a │
                      │ n │
                      │ e │
                      │ k │
                      │ e │
                      │ y │
                      │ / │
                      │ ，│
                      │ 且│
                      │ 传│
                      │ 输│
                │ 、re │
                │ view │
                │ er   │
                │ 侧栏 │
                │ 查看 │
                │ 不发 │
                │ 凭据 │
                │ （L2 │
                │ 56） │
                │ 、en │
                │ ded- │
                │ cont │
                │ roll │
                │ er   │
                │ 不发 │
                │ 凭据 │
                │ （L2 │
                │ 63） │
                │ 、非 │
                │ 法三 │
                │ 窗格 │
                │ 不发 │
                │ 凭据 │
                │ （L2 │
                │ 91） │
                │ 、空 │
                │ 布局 │
                │ 重开 │
                │ 不发 │
                │ 凭据 │
                │ （L3 │
                │ 28） │
                │ 、窗 │
                │ 口目 │
                │ 录操 │
                │ 作不 │
                │ 发凭 │
                │ 据（ │
                │ L342 │
                │ ）、 │
                │ 外来 │
                │ shel │
                │ l    │
                │ 不发 │
                │ 凭据 │
                │ （L3 │
                │ 74） │
                │ 、恢 │
                │ 复失 │
                │ 败   │
                │ work │
                │ er   │
                │ 无输 │
                │ 入凭 │
                │ 据（ │
                │ L486 │
                │ ）   │
   关闭与身份请 │ test │ PASS
   求竞争迟到凭 │ _t09 │
   据撤销       │ 1_pa │
                │ ne_i │
                │ pc.m │
                │ js:4 │
                │ 20-4 │
                │ 30： │
                │ 在   │
                │ wind │
                │ ow_o │
                │ pen  │
                │ 挂起 │
                │ 期间 │
                │ 触发 │
                │ 窗口 │
                │ 关闭 │
                │ ，核 │
                │ 对关 │
                │ 闭操 │
                │ 作必 │
                │ 须等 │
                │ 待身 │
                │ 份请 │
                │ 求完 │
                │ 成后 │
                │ 才销 │
                │ 毁， │
                │ 且请 │
                │ 求完 │
                │ 成后 │
                │ 签发 │
                │ 的迟 │
                │ 到凭 │
                │ 据被 │
                │ 立即 │
                │ 撤销 │
                │ （!l │
                │ iveC │
                │ rede │
      controller view must not
      issue an input
      credential（L347）
      •
      验证本质：历史/已结束控制
      器仅读，严禁签发可写凭据
      。
  8. late_identity（窗口关闭
  detachPanes 时不再等待 pane.
  opening）：
      • 命中有效断言：Closing
      must wait for the
      admitted identity
      request（L426）
      •
      验证本质：窗口关闭与凭据
      签发并发竞争时的锁同步与
      防泄漏撤销。
  9. iframe（移除 event.
  senderFrame !== event.sender.
  mainFrame 校验）：
      • 命中有效断言：Iframe
      sender accepted:
      a2a:snapshot（L273）
      • 验证本质：子 frame /
      iframe 跨域安全边界拒收。


  结论：9
  个变异全部落在业务核心的安全
  边界、并发时序竞争与布局持久
  化断言上，无一落在“接口名单比
  对”上，且均代表生产代码可能出
  现的严重坏实现（越权、凭据泄
  漏、竞态破坏、安全边界绕过）
  。本地重跑证据 local-01-
  DgE6Uo/summary.json
  显示：绿态退出码
  0，每个变异均以退出码 1
  失败并精确命中指定的聚焦业务
  断言，不存在因 setup/import
  错误而产生的伪红态。
  ──────
  ### 2.4
  修改边界与产品代码纯洁性

  1. 允许边界：仅允许修改
  workbench/tests/test_t091_pan
  e_ipc.mjs 以及本次证据目录
  evidence/2026-10-23-
  batch23/T-150/**。
  2.
  禁止边界：workbench/src/**、w
  orkbench/app/**、其他测试、HI
  STORICAL.md、.project-
  map/**。
  3. 检查结果：
      • 检查 full.
      diff，改动文件唯一且仅为
      workbench/tests/test_t091
      _pane_ipc.mjs。
      •
      生产代码（workbench/app/m
      ain.ts、preload.ts
      等）完全只读未动。
      •
      未引入任何第三方外部依赖
      或新建辅助文件。
      •
      严格遵守了单票修改边界要
      求。

  ──────
  ### 2.5 防御性设计与证据复核

  1.
  防篡改与不可覆盖性：测试报告
  写入均使用 { flag: 'wx'
  }，若目标文件已存在直接抛出错
  误，防止意外覆盖或擦除失败证
  据。
  2.
  变异唯一定位保护：test_t091_p
  ane_ipc.mjs 第 629
  行包含防御性检查 assert.
  equal(candidate.
  split(before).length - 1,
  1)，确保变异目标在生产代码中
  全局唯一存在，杜绝因代码行变
  动导致变异替换落空或替换多处
  的虚假红态。
  3. 相关回归套件：执行主控在
  RUN-LOCAL-01.sh
  中一并运行了同属窗口模型与序
  列号边界的
  test_t139_selection.mjs 与
  test_t110_window_sequence.
  mjs，均正常
  PASS，未引发系统级回归。
  ──────
  ## 3.
  审查发现清单（Findings）

  本次审查未发现任何阻断性或严
  重缺陷：

  • P0（致命破坏 /
  越权逃逸）：0 项
  • P1（验收未达标 /
  契约削弱）：0 项
  • P2（潜在隐患 /
  边界覆盖遗漏）：0 项
  • P3（建议与信息性提示）：0
  项
  ──────
  T-150 REVIEW PASS

──────────────────────────────────
>
──────────────────────────────────
? for shortcuts
```
