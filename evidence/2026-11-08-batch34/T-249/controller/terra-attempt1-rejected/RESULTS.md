# T-249 独立窗口验收：INCOMPLETE

- 任务 `a2a+T-249-2`，attempt `95a2750d-484c-427c-98fb-577f5a7ca84f`，session `b847f76f-b14f-4a80-9dd6-0911094f7b66`，fence 1，spec_rev 1。
- 实际 Test 包 revision `1243bc15f979976967cfd2d5cdd3a2acce6df635`；父任务最终候选 `18c108fcaed1c4ecf51831f2272578a3b09427be`。本次在父候选源码 worktree 运行常规测试；本次 `git diff --exit-code 1243bc15f979976967cfd2d5cdd3a2acce6df635 18c108fcaed1c4ecf51831f2272578a3b09427be -- workbench acceptance` 退出 0。没有声称父候选重新打包。
- 包 `/private/tmp/t249-outside-9iitgp1b/a2a-build-t249-fence4-details-20261108-01/Enchanted Test.app` 的 Info.plist bundle ID 为 `org.a2a.workbench.test`，包内 package.json revision 如上。Computer Use 看到窗口 renderer 的 file URL 指向此包，且显示“后台已连接”。正式 Enchanted 未操作；未启动其他包或 agent CLI。
- 主控启动前记录 Test state 与凭据目录不存在，见 `evidence/2026-11-08-batch34/T-249/controller/terra-environment-start.json`。本次未遇到文稿或其他权限提示。测试 state 由主控所有，未删；夹具根 `/private/tmp/t249-terra-20261108-01` 增加了测试用 `tmp` 和测试运行产生的临时内容，不进入产品集成，交主控清理。

## 自己的 Computer Use 观察

1. 从 Test 窗口打开 alpha，创建普通 zsh 终端，打开侧边 Git 图。列表依次显示未提交的改动（2 个文件）、合并功能分支、主分支第二次提交、功能分支提交、根提交；main、feature、terra-tag 标签分别出现在预期行。独立 Git 顺序、父关系和引用在 `git-oracle.json` 的 `before.alpha`，图中连线视觉上呈两分支汇合；未逐一在界面展开合并提交核对完整父哈希。
2. 点根提交，详情显示 `77ca35547003aef14c5729327027ce475d12f558`、无父提交，以及 `file*.txt`、`file-other.txt`、`first.txt`。点 `file*.txt`，显示 `+literal star root`。Esc 一次回详情，再一次关闭详情。点普通提交显示 `d2e1270223348078e0b71b3c87a8f4b35091ed70`，父前缀 `77ca355470`；其 `file*.txt` diff 只显示 `-literal star root`、`+literal star second`。转选功能分支提交显示 `e72d3352c2e919d4313162c02e3b55b5d8d264f8`、父前缀相同、文件 `feature.txt`；重复点击该行 AX 树无变化，未见旧文件残留。选择未提交行后显示 `first.txt` 与 `untracked.txt`；前者 diff 显示 `main second` 和 `+working change`。
3. 右键合并提交 → 新建分支，输入 `-invalid` 点新建，提示“分支名不能以“-”开头。”；随后改为 `terra-created` 按 Esc 关闭，Git 读回引用仍为原始三项。重新打开创建，填 `terra-created`、不勾选检出并创建，界面提示成功；Git 读回只多出 `refs/heads/terra-created` 指向 `d676203242b62319515d6914974346e77bab32ab`。右键该标签删除，第一次点取消，Git 读回分支仍在；第二次确认删除，界面提示已删除，最终 Git refs 与基线相同（`git-oracle.json`）。未 push、pull 或连接远程。输入框 Esc 后终端截图未见插入的新命令；未对终端输入缓冲做独立检查。
4. 在同一个普通终端用 `cd` 到 beta，面板随后显示 beta 及“另一个仓库”；固定后同一终端 `cd` 回 alpha，面板仍显示 beta；取消固定后显示 alpha。进入 many，面板列出 `three`、`group/two`、`group/one`，与独立夹具目录一致。**未创建第二个终端，也未验证切换终端焦点**，因此不能把同窗格 `cd` 结果扩大为跨窗格固定验证。
5. `cd` 到 unborn 后，列表显示未提交的改动（3 个文件）；详情列出 `file[1].txt`、`staged.txt`、`untracked.txt`，`file[1].txt` diff 显示 `+bracket staged`、`+bracket working`。随后 `cd` 到实际受管路径 `/Users/luckye/Library/Application Support/a2a-orchestrator-test/worktrees/terra/readonly`；面板显示门禁管理 worktree 只读原因。右键提交的打标签、新建分支、Revert、重置均禁用且带同一原因，复制项可用。操作后 Git status 显示 detached、无变更，refs 与 alpha 原始 refs 一致。但准备时 `oracle-before.json` 中 managed 是另一个临时路径，非此受管路径；缺实际路径操作前元数据快照，不能证明完整元数据前后不变。未改门禁状态。
6. 尝试两次拖动面板分隔处，截图未观察到宽度改变；不能据此确认拖动是否命中，也未验证向右调整与双击复原。未保存截图文件；上面的内容来自当时 Computer Use AX 树和屏幕观察，不是可供重放的视觉记录。Test 普通终端通过关闭按钮关闭；Cmd-W 调用后自动化返回超时，随后应用清单不再列出 Enchanted Test，正式 Enchanted 仍列出。

## 独立 Git 对照及机械检查

`git-oracle.json` 保存 UI 操作前独立脚本生成的 oracle（注意其中 managed 路径限制）、操作后 Git status/refs、Git 提交/文件/diff 和 unborn 文件内容。`ui-observations.json` 是本次界面实际观察的手工转录，非产品接口生成。`check_observations.py` 不依赖临时目录或产品源码，比较记录的提交顺序、标签、文件、提交哈希、父前缀及 diff。正常副本退出 0；`wrong-commit.json` 改错提交哈希退出 1，`mixed-file.json` 混入文件内容退出 1。原始结果见 `observations.log`、`mutant-wrong.log`、`mutant-mixed.log`。这只验证已转录事实之间的关系，不证明界面实际发生了这些动作，也不证明报告全文或未观察项。

## 常规测试与来源区分

本次实际运行的命令和环境见 `COMMANDS.md`。冻结 `acceptance/T-249/check_git_graph.py` 显示 PASS、退出 0；`node --test workbench/tests/test_t249_git_host.mjs` 为 22 项通过、退出 0；`python3 workbench/tests/test_t249_outside_safety.py` 为 6 项通过、退出 0。原始输出依次在 `acceptance.log`、`node.log`、`outside.log`。这些常规测试与本次真实窗口互为补充，不能代替上面未完成的窗口场景。

主控称同一产品代码版本此前真实窗口正例两次各 142 项、五个变异，并提供父任务 review `9155d2de-7eeb-4515-b31b-46214d7f7532`，详见主仓库 controller 证据；这些是主控来源，不是本次 CU，也未由本报告独立复跑。父任务 verified 不替代本次独立验收。

## 进程与缺口

任务卡给定正式进程 PID 81233，启动时间 `2026-11-08 13:56:08Z`；这只是派发信息，不是本次核实。开始时 `ps -p 81233 -o pid=,lstart=,command=` 被沙箱拒绝（`operation not permitted`，退出 127），按卡未换命令绕过，也没有结束时独立进程事实。问题请求 `e95d9ce0-b4d4-4e21-817c-29fa3394bea7` 已排队，请主控核实。宽度及只读基线缺口已通过 `62395ac4-bcfd-4fcf-ba12-9073e7664dfc` 上报，两者 queued 不是已处理。

**Works**：上述实际窗口观察与独立 Git 数据的已记录部分一致；机械检查的两个错误副本均判红。

**No regression**：三项指定常规测试通过；并非全套回归。

**Risk / undo**：本次只改证据目录及指定临时夹具，测试分支已删除；主控清理自己创建的 Test state 与临时夹具。尚缺跨终端焦点、面板宽度、实际受管 worktree 操作前元数据和正式进程起止核实，须补证后才能判断完整验收。未发现可复现的产品缺陷，但不足以给整体 PASS。
