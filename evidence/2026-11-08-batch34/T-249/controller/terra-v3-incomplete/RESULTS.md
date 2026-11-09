# T-249 独立窗口验收：INCOMPLETE

受管任务 `a2a+T-249-2`，attempt `acbdf9b4-39ee-4438-a9d9-d23fd21a6031`，session `b68e0eac-d9c7-455c-aaa0-bbe24fa36e0f`，fence 3。验收对象是 `/private/tmp/t249-outside-9iitgp1b/a2a-build-t249-fence4-details-20261108-01/Enchanted Test.app`，bundle `org.a2a.workbench.test`。包版本按派发资料为 `1243bc15f979976967cfd2d5cdd3a2acce6df635`；父交付 `18c108fcaed1c4ecf51831f2272578a3b09427be` 的产品输入一致性由主控 `controller/worker-v6-product-equivalence.json` 记录，本次未重新打包或自行重算一致性。独立实测不引用旧窗口观察作为本次结果。

## 结论与缺口

本次不能判 PASS：unborn 未跟踪文件的内容未能在 UI 查看；列宽拖动的两次 CUA 尝试都返回工具错误，没有完成拖动或双击复原；正式后台进程前后核对按任务分工由主控补证。CUA 屏幕截图在工具回合中可见，但未保存成独立截图文件，终端缓冲和列分隔条的视觉观察因此没有可重放图片。验收脚本只对手工记录的部分可见值与独立 Git 数据做比较，不能证明操作真实性、图线几何或全文。

未跟踪文件最短复现：第二个普通 shell 进入 `-03/repos/unborn`，点“未提交的改动（3 个文件）”，点 `? untracked.txt`，UI 显示“未跟踪文件，还没有 diff。”而夹具实际内容是 `new file before first commit`。是否需要显示未跟踪文件内容涉及任务条件的解释，已通过 issue `615d6c13-e172-4a8f-a2d9-2de6644d6510` 上报，状态为 queued，非已处理。Git 状态和文件原文保存在 `git-facts.json`。

截图中说明/日期分隔条位于表头；CUA `app.drag([1168,147],[1100,147])` 和 `app.drag([2338,294],[2200,294])` 均立即返回 `Computer Use server error -10005: noWindowsAvailable`。这不是产品列宽缺陷证据，也没有前后宽度；按卡上两次定位上限停止并上报 issue `253ac5be-e61d-41ab-8b29-a706d3e54782`（queued）。双击复原未执行。需要主控协调工具并补做拖动、宽度测量和双击。

## 本次 CUA 操作和观察

- 按完整路径取得 Test 应用。已有项目与前轮记录，选择本轮 `-03/repos/alpha` 并创建普通 shell 后，显示“后台已连接”和“跟随聚焦窗格”，路径为本轮 alpha。未启动模型 CLI。
- 提交表由上至下为未提交（2 文件）、合并功能分支、主分支第二次提交、功能分支提交、根提交；`main`、`feature`、`terra-tag` 标签可见，未提交与 HEAD 有虚线连接。独立 `rev-list --date-order --parents --all`、refs 和 status 保存于 `git-facts.json`。该文件的 Git 标题顺序与手记一致；线条端点只作视觉观察。
- 点合并行：完整哈希 `d676203242b62319515d6914974346e77bab32ab`，显示两父前缀 `d2e1270223`、`e72d3352c2`；点 `feature.txt` 显示 `+feature content`。点根行：哈希 `77ca35547003aef14c5729327027ce475d12f558`、无父，文件有 `file*.txt`、`file-other.txt`、`first.txt`；点字面 `file*.txt` 显示 `+literal star root`，未见另一文件内容。点普通提交：哈希 `d2e1270223348078e0b71b3c87a8f4b35091ed70`，点 `file*.txt` 显示 `-literal star root` 与 `+literal star second`。点未提交行的 `first.txt` 显示 `+working change`。从一个 diff 直接切换到其他提交时详情更新；重复点普通提交，显示不变。
- 在已经可见的 merge diff 中连续按 Esc：第一次返回文件列表和详情，第二次关闭详情。另在 alpha 终端输入未执行的 `echo ESC_BUFFER_SENTINEL`，打开新建分支框，输入 `terra-cancel` 后按 Esc；截图中缓冲仍显示该文本，确认框关闭；Git refs 后读无 `terra-cancel`。本次没有持久截图，结论受此限制。
- 合并行右键新建 `terra-created`，未勾选检出；UI 报已新建，随即 `git for-each-ref` 显示新增且仅新增指向 `d676203...` 的 `refs/heads/terra-created`。右键该标签删除，UI 报已删除；在同一合并行尝试 `-invalid`，UI 提示“分支名不能以‘-’开头”，Esc 取消。最终 refs 与 status 均逐字符串等于操作前（见 `git-facts.json`）。未 push/pull。
- 创建两个普通 shell，第一在 alpha，第二 `cd` beta。聚焦第二个时面板显示 beta 和“另一个仓库”；点击第一个时回 alpha；固定 alpha 后聚焦第二个仍是 alpha；取消固定后显示 beta。第二 shell 进入 `many`，面板列出 `three`、`group/two`、`group/one`，与夹具目录三仓库一致。
- 第二 shell 进入真实 `~/Library/Application Support/a2a-orchestrator-test/worktrees/terra/readonly-03`。面板说明门禁管理 worktree 只读；仓库操作菜单只有说明及复制路径，提交右键的打标签、新建分支、Revert、重置均 disabled 并带相同说明。操作前通过 `git rev-parse --absolute-git-dir` 与 `--path-format=absolute --git-common-dir` 确认分别是 `-03/repos/alpha/.git/worktrees/readonly-03` 和 `-03/repos/alpha/.git`；读取全部 54 个文件的路径及原始字节到本轮临时快照，UI 操作后再次读取，新增、删除、字节变化均为空，`git for-each-ref` 字符串相等。快照位于额外目录供主控清理，不以哈希代替比较。
- unborn 文件列表为 `file[1].txt`、`staged.txt`、`untracked.txt`；前者 diff 显示 `bracket staged` 和 `bracket working`，后者 `staged.txt` 显示 `staged before first commit`；`git show :file[1].txt` 独立确认 index 只有第一行。未跟踪项结果见缺口。
- 关闭本次两个普通终端；列表变为历史 2 个。`super+w` 后 CUA 报 timeout，再读取显示另一前轮 alpha 窗口，说明本次窗口不再是当前窗口；没有操作该前轮窗口。没有删除 Test 数据或夹具。

## 常规测试与数据来源

外层执行目录均为本任务 worktree。所有临时测试夹具放 `TMPDIR=/private/tmp/t249-terra-20261108-03/tmp`，测试自行清理。固定产品根记为 `P=/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-249-1-a5`：

1. `python3 "$P/acceptance/T-249/check_git_graph.py"`：该脚本要求子进程 cwd 为产品根，实际由 Python `subprocess.run([...], cwd=P, env=...TMPDIR...)` 执行，外层 cwd 未改变。退出 0，PASS，原始输出 `check-git-graph.txt`。覆盖独立 Git 顺序、父提交、引用、泳道、状态与 CLI 写操作。
2. `TMPDIR=/private/tmp/t249-terra-20261108-03/tmp node --test "$P/workbench/tests/test_t249_git_host.mjs"`：退出 0，22 pass、0 fail，输出 `git-host.txt`。
3. `TMPDIR=/private/tmp/t249-terra-20261108-03/tmp python3 "$P/workbench/tests/test_t249_outside_safety.py"`：退出 0，6 tests OK，输出 `outside-safety.txt`。

独立数据来自 `git -C <alpha> rev-list --date-order --parents --all`、`for-each-ref --format='%(objectname) %(refname)'`、`status --porcelain=v2 --branch`，各提交 `show -s --format=%s`、`diff-tree --root --no-commit-id --name-only -r`、`--literal-pathspecs show` 或 `diff`，以及 unborn 的 `git show :file[1].txt` 和实际文件。未调用产品源码生成期望。`managed-before.json` 是主控本轮 UI 前独立读取的真实 worktree 信息；其他原始小型输入在 `git-facts.json`。

`python3 evidence/2026-11-08-batch34/T-249/terra/check_observations.py` 退出 0；两个反例分别执行相同命令并传 `wrong-parents.json`、`wrong-diff.json`，均退出 1，分别命中父提交和单文件内容断言，输出各自 `.txt`。脚本不检查未展示的未跟踪内容、拖动、菜单、视觉图线或报告文字，也不证明手工观察真实。

主控已有该包产品输入的两次各 142 项真实窗口正例及 no-panel/no-details/no-diff/parents/order 反例；这是主控原有证据，非本次运行。正式 Enchanted 和用户 hc 未操作；正式进程前后 PID/启动时间没有在本会话核对，待主控补充。

## 清理与范围

只在允许的 evidence 目录写入报告、记录和核对脚本；额外目录 `/private/tmp/t249-terra-20261108-03` 写入临时 Git 元数据快照，并由测试使用其 `tmp`；夹具保留供主控按所有权清理。没有修改产品源码、冻结验收、任务票或治理规则。停止前项目地图状态复核见交付时输出。
