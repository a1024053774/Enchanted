  ### 1. 约

  • 名称规则与门禁约束一致性：门禁原有的强制约束是“同一仓库所有任务必须共用同一个工作分支（project_branch_conflict）”。T-180 的命名规则定为
  refs/heads/${prefix}${project}（如 refs/heads/enchanted/demo），以项目为维度而非以任务为维度起名；同时在 defaultWorkBranch 中通过 gates.
  repoWorkBranch(repo) 优先检索该仓库已有任务绑定的分支，已有任务直接沿用（reason: 'repo_tasks'），完全避免了同一仓库新任务冲突。
  • ## 取舍说明（“改后对新任务生效”在已有项目不生效）：
      • 设置页
      • **
      • **


  ### 2. Cre

  • 三条入口统一处理：
  在 daemon.ts 中，三条 create 途径均包裹在统一的 createGate 函数中：
      1. 终端
      2. 后台启
      3. 操作
      三
  • 用户指定分支时行为完全不变：
  daemon.ts:316 明确判断 if (command.command !== 'create' || command.branch !== undefined) return await call(command);，当用户显式传递 branch
  时直接直通门禁，由门禁完成 refs/heads/ 前缀校验、Git 引用格式校验、存在性验证以及 project_branch_conflict 检查，完全不改变历史行为。
  • 同名分支已存在直接沿用的行为：
  见下方发现 P2。

  ### 3. Git

  • 新建分支安全性：
  workBranch.ts:562 使用的是 git -C <repo> branch <branch-name> HEAD。该命令仅创建分支引用，不执行 checkout/switch，工作区与当前 HEAD（如
  main）丝毫不动；整个实现中没有任何 push 操作或网络调用，测试也通过 SHA 对比证明了集成前后 main 分支完全未变。
  • 前缀校验严密性：
  workBranch.ts:549-553 的 checkWorkBranchPrefix 进行了层层防护：
      • 非字
      • 空白字
      • 以 -
      •
      • defaultWorkBranch 在拼接最终 ref 后再次调用 git check-ref-format <ref> 兜底。无法被绕过。


  ### 4. 测试期望、红态、变异与演进历史

  • 期望值独立性：期望值全部来源于用户 2026-10-25 原始要求与 Ticket T-180 目标，不是抄录代码实现产物。
  • 红态落在缺陷断言上：修前 main 运行 summary.json，create 未传 branch 时返回 invalid_text，精准落在 L07 的核心缺陷上。
  • 两个变异落点精准：
      • prefix-ignored（忽略设置前缀）：运行 [mutant-prefix-ignored-02](file:///Users/luckye/Documents/Code/a2a-review/T-180-r1/candidate/evidence/2026-10-
      • no-reuse（未沿用同仓库既有工作分支）：运行 [mutant-no-reuse-02](file:///Users/luckye/Documents/Code/a2a-review/T-180-r1/candidate/evidence/2026-10-
      project_with_tasks_keeps_branch_after_prefix_change（改前缀后已有任务的项目新建分支被门禁 project_branch_conflict 拒绝）。
  • test-v1-runs 历史如实反映：
  Ticket 作者在 RESULTS.md:47-50 中如实说明：第一版测试未覆盖“改前缀后已有项目沿用原分支”，导致变异 no-reuse 在 v1 误通过（[test-v1-runs/mutant-no-reuse-
  PASS）。作者发现测试缺陷后补齐了 T-3 校验并重跑了全套红绿与变异测试，将旧证据完好保留在 test-v1-runs/，完全符合诚信与证据保留规范。

  ### 5. 异常处理与最小改动原则

  • 全链路未引入无证据支撑的 fallback、重试或兼容垫片。
  • 不吞没关键异常，Git 分支创建失败时抛出带原因的明确 Refusal。
  • 截图证据 green-04-01-settings-prefix.jpg 经查看证实设置页表单控件与提示文案真实渲染生效。
  ──────
  ## 审查发现（Findings）

  ### [P1] 候选版本基于预先分支提交，full.diff 包含对已合入 T-177 的逆向删除

  • 位置：full.diff 全文（涉及 main.ts、renderer.tsx、sidebar.ts 等）
  • 现象与场景：候选提交 74724cfa0 是在 d7821a3b（T-182 闭票提交）上切出的，而当前 main 已合入 T-177（8e7976b9）。因此 full.diff 显示大量删除 T-177
  代码及删除 test_t177_sidebar_history_e2e.py 的 diff。
  • 风险分析：若合并时使用直接代码覆盖而非 Git 3-way merge（git merge），会导致已上线的 T-177 功能被误冲刷。经检查，T-180 与 T-177 在 main.ts、renderer.
  tsx、daemon.ts 中的改动处于不同函数或区块，3-way merge 可正常合并。
  • 处置要求：执行主控在合入 main 时必须使用 git merge 执行 3-way merge，并在合入后同时跑通 T-177 与 T-180 的 e2e 测试。

  ### [P2] 同名分支已存在时直接沿用，若该分支历史久远可能承载非预期 base

  • 位置：workBranch.ts:560
  • 现象与场景：若用户仓库中此前已经存在一个名为 refs/heads/enchanted/<项目> 的本地分支（例如几个月前的历史分支），当本次首个任务不传 branch
  时，defaultWorkBranch 检测到 exists(repo, ref) 为真，直接沿用该分支作为集成目标，其基准 commit（base_commit）将是该历史分支的 HEAD，而不是用户当前的
  main/master HEAD。
  • 风险分析：如果用户本地有未清理的陈旧同名分支，worker 会基于旧代码拉取 worktree。不过当前设计中回执已显式返回了 { created: false, reason: 'existing'
  }，且技能要求主控向用户汇报。在实际场景中概率较低，属于已知取舍。建议在后续若有用户反馈时考虑提示或警告。

  ### [P3] 回归测试 test_t131_parallel_workers_e2e.py 在 evidence 目录无独立 summary 文件

  • 位置：RESULTS.md:41
  • 现象与场景：RESULTS.md 表格记录了该回归测试为 PASS，但 evidence/2026-10-25-batch25/T-180/ 目录下未留下 t131 的 summary json
  文件（测试在临时目录执行完后未持久化清单）。虽然主测试集 test_t180 覆盖了多任务并行与集成验证，但回归证据留存略显单薄。
  ──────
  ## 综合评估

  T-180 的实现定位在最小根因层，设计清晰，对 Git 操作有严格的安全防护（不动 main、不切换、不
  push），三条入口统一收敛，前缀校验无漏洞，测试集与变异设计极为扎实，文档与文案无任何营销浮夸。

  T-180 REVIEW PASS
