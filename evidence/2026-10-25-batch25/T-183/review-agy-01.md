   Enchanted（a2a）项目 T-183 候选交付独立审查报告

  审查对象：Ticket T-183 候选提交（7efb5efd8 / full.diff）
  审查角色：只读独立审查员（评审执行主控自建缺陷票交付）
  相关材料：

  • Ticket：[candidate/.project-map/tickets/T-183-failed-create-leaves-branch.
  • 运行证据：T-183/
  • 用户授权转述：user-decision.md
  ──────
  ## 一、专项核对要点结论

  ### 1. 分支删除范围、沿用保护与旧值保护（是否会误删用户分支）

  • 仅删本次调用新建分支：
  在 defaultWorkBranch 中，只有执行 git branch 成功新建分支的分支路径才会返回 made: { ref, sha }。
  当同仓库已有任务（reason: 'repo_tasks'）或分支已存在（reason: 'existing'）时，返回值均不含 made（即 made ===
  undefined）。
  用户显式指定分支时，createGate 在入口处直接直通门禁：if (command.branch !== undefined) return await
  call(command);，完全不经过默认分支推导逻辑。
  在 daemon.ts:416-419 的清理触发条件中严格要求 if (made)，因此沿用已有分支和用户指定分支绝对不会被清理。
  • update-ref CAS 旧值保护到位：
  [dropWorkBranch](file:///Users/luckye/Documents/Code/a2a-review/T-183-r1/candidate/workbench/src/workBranch.
  git -C <repo> update-ref -d <made.ref> <made.sha>
  Git 原生校验分支当前指向必须严格等于创建时的 commit SHA（made.sha 来自 HEAD^{commit}
  解析出的完整散列）。若外部有任何并发提交或指针变动，Git 命令非零退出报错，绝不会误删已被推进的代码。
  • 误删用户分支风险：无。既有分支未被标记 made；指定分支不走该流程；发生外部变更受 CAS 严格保护。



  • 门禁拒绝原样返回与抛出，未吞异常：
  在 createGate 中：
      • 若 call
      result
      • 若
  • work_branch_cleanup_failed 的合理性：
  若在回滚分支时 git update-ref -d 失败（例如分支被挪动或 Git
  锁竞争），[dropWorkBranch](file:///Users/luckye/Documents/Code/a2a-review/T-183-
  此机制不属于禁止的补偿路径（compensating hack）或投机重试/降级，而是针对非原子跨系统交互（Git + SQLite
  Gate）在失败时的严格副作用回滚（Rollback）。如果回滚动作受阻，它拒绝静默吞没，而是显式报错并将原始拒绝原因
  refusal 嵌在 details 中暴露给调用方。这符合最小破坏原则和防毁损原则。

  ### 3

  • 根因准确：T-180 架构设计中，由于门禁层要求校验分支必须已在 Git 中存在，编排层 createGate
  必须在交由门禁前预先建好工作分支；当门禁因卡版本不存在、项目冲突等原因拒绝时，未对预建分支做回滚，导致分支残留
  。
  • 改动处于最小根因层：改动仅集中在 workbench/src/daemon.ts（编排层在门禁失败时调用清理）和
  workbench/src/workBranch.ts（基础操作层提供带 SHA
  的创建与带旧值保护的清理），未向门禁内部引入复杂分支管理，未改动任何无关文件。
  • 无不良设计：未引入任何 fallback 兜底、自动重试、兼容模式双写或平行 API。

  ###

  • 测试期望独立性：期望值完全来源于 Ticket T-183 验收标准（不带 branch 且卡版本不存在的 create
  被拒后仓库无残留分支；随后正常 create 回执 created: true, reason: default），绝非依照实现代码输出反推。
  • 红态落点精准：
  修前在 main 上运行 [red-main-01](file:///Users/luckye/Documents/Code/a2a-review/T-183-
      1. refused_cr
      .
      2.
      精确复
  • 变异拒绝：
  变异 [keep-branch-on-refusal](file:///Users/luckye/Documents/Code/a2a-review/T-183-
  01](file:///Users/luckye/Documents/Code/a2a-review/T-183-r1/candidate/evidence/2026-10-25-batch25/T-
  • 绿态与非回归：
  [green-01](file:///Users/luckye/Documents/Code/a2a-review/T-183-r1/candidate/evidence/2026-10-25-batch25/T-
  项场景，证明已有项目沿用原分支、前缀修改、用户指定分支等能力毫无回归）。



  • [RESULTS.md](file:///Users/luckye/Documents/Code/a2a-review/T-183-r1/candidate/evidence/2026-10-25-
  • 所有测试运行记录（green-01、red-main-01、mutant-keep-branch-01）真实留存于 evidence 目录中且数据一致；
  • 未做项在 RESULTS.md 中如实主动披露（未覆盖分支被移动时的
  work_branch_cleanup_failed，未耗费额度用真实模型复跑），完全符合诚信与额度约束（user-decision.md）。
  ──────
  ## 二、

  ### [P3

  • 位置：[workbench/src/workBranch.ts:51-54](file:///Users/luckye/Documents/Code/a2a-review/T-183-
  • 严重度：P3
  • 失败场景：
  在首个 create 命令执行并被门禁拒绝的瞬间（数毫秒内），如果外部并发进程篡改或推进了该工作分支，Git 的 update-
  ref -d 将因 commit SHA 不匹配而拒绝删除，代码会抛出 Refusal('work_branch_cleanup_failed')。
  当前 e2e 测试集未通过注入延迟或模拟竞争来触发该异常路径。作者已在 RESULTS.md 的“没做 /
  未验证”中坦白说明。鉴于真实场景下此种毫秒级外部冲突概率极低且属防御性设计，风险可控，无需阻断交付。

  ###

  • 位置：[workbench/src/daemon.ts:415-418](file:///Users/luckye/Documents/Code/a2a-review/T-183-
  • 严重度：P3
  • 失败场景：
  createGate 分别在 catch (error) 与 if (!result?.ok) 两处调用了 dropWorkBranch。变异字典中仅包含了针对 if
  (!result?.ok) 的变异 keep-branch-on-refusal，未对 catch (error) 路径设置变异。因 gates.call 内部已包裹
  try/catch 通常返回 { ok: false }，catch 块主要防御守护进程中断或 RPC
  级致命异常，主测试集与现有变异已足够覆盖绝大多数真实场景。
  ──────
  ## 三、

  候选改动精准击中 T-181 实测暴露的“门禁拒绝导致工作分支残留”缺陷，严格遵守最小根因层改动原则。Git
  操作具有严密的 CAS
  安全保护，绝对不误删已有分支及用户分支；原样保留异常与门禁回执，未吞没任何关键信息；测试期望来源于 Ticket
  验收条件，红态、变异与绿态证据确凿且可复现，文档如实。

  T-183 REVIEW PASS
