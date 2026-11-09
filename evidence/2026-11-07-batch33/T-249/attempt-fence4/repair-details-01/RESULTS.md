# T-249-1：门禁 #52 详情验收缺口修复

**PASS（机械条件与编排分类）**：冻结验收通过、宿主 22/22、脚本安全检查 6/6。已补入从可见提交行到详情、再从文件按钮到单文件 diff 的真实窗口旅程，以及 no-details、no-diff 两个指定反例。

**INCOMPLETE（新增窗口路径与整票验收）**：本轮没有运行 Electron。新窗口正例和五项变异仍须主控按已批准的两层流程在沙箱外执行，不能将本轮机械通过解释为详情用户路径已验收。扫描和收尾地图检查因读取源文件未返回而中断，详见工具限制。

## 身份、候选与范围

- 保持 task `a2a+T-249-1`、attempt `b33751df-0d57-4223-834d-4d467b199e22`、session `dcfd69d9-6557-4901-bd83-24bb348f0693`、fence `4`、spec_rev `5`；原生会话仍为 `01a1bb74-756f-7dd0-9cae-f71d9c81e0f6`。
- 失败候选：`1e1e5ef7bfb1faa8a0af8df064ac6834e2579a93`；审查 verification：`10991a07-6711-4027-abb6-25d42fb69ab0`。本次由门禁 #52 明确要求修复并沿用本 attempt 重交。
- 修复源码提交：`9940ade191a9d8f0273a1ee664c6c52039306bcd`。之后只补交本目录文本证据；最终完整提交号以本轮 submit 为准。
- 只改现有窗口开发测试、脚本安全开发测试、`RUN-OUTSIDE-T249.sh` 和 README；产品模型、宿主、React 组件、冻结 `acceptance/**`、根 `REVIEW.md`、门禁与依赖均未改。
- Node `v26.5.0`、Git `2.52.0`、Python `3.9.6`；自动提交尾注继续记录 `gpt-6-astra`、`xhigh` 和同一启动记录，见 [run-context.json](run-context.json)。没有手写尾注。

## 先复现，再补观察路径

先写 [不变量与观察矩阵](INVARIANTS.md)，针对“共享模型仍在，但已承诺的界面功能被断开”这个重复失败类别逐项核对。保留原有图、写操作、跟随、固定、多仓库、受管保护的检查；本次补齐详情和 diff 两处缺失的观察点，没有再开盲审。

在本 attempt 请求目录创建一次性源码副本，仅将 `{selectedCommit && <CommitDetails` 改为 `{false && selectedCommit && <CommitDetails`。`/usr/bin/python3 .../repair-details-01/reproduce_gap.py` 在副本运行三条原始完成条件，退出码全为 0，复现了验收缺口，见 [gap-no-details.json](gap-no-details.json) 和三个 `gap-no-details-*.txt`。这是“机械条件拒绝不了明显错误实现”的失败证据，不声称旧产品真的没有详情。副本及临时 Git 夹具已清理。

随后补充分类检查，在尚未改窗口测试与 RUN-OUTSIDE 时运行：

```sh
TMPDIR="$A2A_REQUEST_DIR" PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 workbench/tests/test_t249_outside_safety.py
```

退出 1，6 个测试内共 5 处失败：缺少详情 DOM 业务观察函数、两个新变异未登记、两个新指定断言未被编排识别，见 [outside-safety-red.txt](outside-safety-red.txt)。这份红态只证明编排缺口。

## 改了什么

1. `check_commit_details` 从可见提交行点击进入详情，核对可见标题、哈希、父提交、作者、提交者、正文和文件列表；再点可见文件按钮，核对显示的文件名、增删行数与完整 hunk 文本。期望来自独立的 Git `show`、`diff`、`ls-files`；不导入产品模型，不用 IPC 直接读取详情代替点击。
2. 先在主仓库普通提交执行这一旅程，使 no-details 和 no-diff 在写操作前就到达指定业务断言。后续专用仓库覆盖根提交／普通提交／未提交三条路径，每条点 `file*.txt`、`file[1].txt`、`:(glob)*.txt`；各文件内容带不同序号、阶段与随机标记，独立 `git --literal-pathspecs` 的完整 hunk 文本会拒绝混入其他文件的结果。
3. 独立 unborn 仓库覆盖已暂存、暂存后再修改、intent-to-add、未跟踪四种状态。前三类从文件按钮进入 diff，与 Git 空树比较；未跟踪文件检查明确说明。真实 Git 夹具探针已确认状态分别为 `A `、`AM`、` A`、`??`，见 [fixture-probe.json](fixture-probe.json)。这个探针不证明 UI。
4. `check_dom` 只在正常 DOM 查询一直没有预期结果时记录业务断言失败；CDP 异常直接传播为未完成。两种新增变异分别断开详情挂载和文件点击，不改 oracle。脚本必须运行 no-panel、no-details、no-diff、parents、order 五项；红态须命中自己的指定断言，且清理与用户 hc core 检查通过。
5. 脚本输出改为当前 `attempt-fence4/outside-<时间戳>/`，README 同步五个变异和待窗口实跑的边界。清理所有权、打包参数和对正式应用的保护未变。

## 本轮完成条件

执行封装：`/usr/bin/python3 evidence/2026-11-07-batch33/T-249/attempt-fence4/repair-details-01/run_current.py`。每项原始 argv、工作目录、TMPDIR、stdout/stderr 和退出码均在对应文本中；夹具位于已授权的 `A2A_REQUEST_DIR` 子目录。

| 原始命令 | 结果 | 证据 |
| --- | --- | --- |
| `/usr/bin/python3 acceptance/T-249/check_git_graph.py` | PASS，exit 0 | [acceptance-green.txt](acceptance-green.txt) |
| `/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t249_git_host.mjs` | 22/22，exit 0 | [host-green.txt](host-green.txt) |
| `/usr/bin/python3 workbench/tests/test_t249_outside_safety.py` | 6/6，exit 0 | [outside-safety-green.txt](outside-safety-green.txt) |

`probe_fixture.py` 退出 0；Python AST 语法检查、`bash -n workbench/app/RUN-OUTSIDE-T249.sh` 和 `git diff --check` 均通过。没有全仓测试或构建：本次只改 T-249 开发验收路径与编排，生产运行逻辑没有变化。

所有自建副本、探针及完成条件临时目录都已删除，删除前保留体量与状态摘要。未创建构建缓存、依赖副本、Electron、后台或 hc 进程。派发额外可写目录为 `[]`，无额外目录改动；门禁请求文件不进入 Git。旧报告和旧红态均原样保留。

## 自查及工具限制

design-integrity-review 实现者自查对象是 `1e1e5ef7..9940ade19` 的四文件差异。本轮新增的有界 DOM 等待不捕获异常；只有查询成功但结果缺失才进入指定业务断言。Git 预期失败只接受 HEAD 查询的 0／1 退出码；fixture、Git 和 CDP 其他异常不冒充变异红态。敏感脚本只扩展变异映射、必跑列表及本 attempt 输出路径，没有改变清理、依赖复制或打包所有权。没有新增产品 fallback、兼容路径或平行模型。人工自查未确认新的结构缺陷；自动扫描未完成，不能报告为空 findings。

behavioral-acceptance-review 证据结论为 **INCOMPLETE**：已复现旧 no-details 存活，新的真实窗口观察与反例已经接入，但尚未实际运行。6/6 只证明分类逻辑和必跑登记；已移除用产品源码字符串仍然存在来证明接线的检查，变异定位唯一性仍由真实 `source_tree` 在构建副本时保证。真实 DOM、详情文本、文件名和 diff 的行为证据须来自下一阶段窗口运行。

本轮开工 `project_map.py status` 已完成，Problems 0、Stale 1，仅根 `REVIEW.md`，见 [project-map-start.txt](project-map-start.txt)。收尾地图脚本与 design scanner 持续未返回，辅助读取扫描脚本也未返回；已中断这三个自有只读命令，Python 输出读取源文件被中断并退出 2，辅助读取退出 130。根因未知，不能沿用开工输出冒充收尾状态。`ps` 诊断被沙箱拒绝；未换路径、命令或权限绕过。完整输出见 [unavailable-checks.txt](unavailable-checks.txt)。

已排队上报两个非阻塞问题：`651a7897-8dae-4bf9-86d4-1af32c0d1984`（ps 拒绝）和 `4e88747c-5a41-4ae6-865b-8ca1a3ee37f2`（脚本源文件读取未返回）。两次均 `queued=true, delivered=false`，不表示已送达或处理。请主控补跑扫描／收尾地图状态，并按卡核对根 `REVIEW.md` 的 Verified；worker 不修改冻结治理文件。

## 主控的下一步

按本次固定候选完成门禁独立复查后，在沙箱外运行全新 slot：

```sh
bash workbench/app/RUN-OUTSIDE-T249.sh t249-fence4-details-20261108
```

必须获得真实窗口正例 PASS，及五项指定断言红态。其中 no-details 必须失败于“点击提交后详情可见”，no-diff 必须失败于“点击文件后单文件 diff 可见”；构建、启动、CDP 或清理错误都不能算相应红态。窗口绿态的 `run.json` 将记录五个详情场景的观察值及每个选中文件的 diff 文本。

随后仍由 `gpt-6.1-terra` 对新 Enchanted Test 做 Computer Use 与常规测试，核对 Esc、终端焦点、布局及任务卡其他条目；正式 Enchanted PID／启动时间和用户 hc core 须前后一致。敏感脚本证据经用户阅读批准后才可集成。本轮证据提交后使用原 CLI、同一身份显式重交一次；排队不等于门禁接收。

**Works**：旧 no-details 验收缺口已复现；详情／diff 的真实窗口旅程及两个针对性变异已补入；编排分类从修前 5 处失败转为 6/6。

**No regression**：冻结验收、宿主 22/22、脚本 6/6 与语法／差异检查通过；全仓、构建和真实窗口未运行。

**Risk / undo**：新增窗口代码仍待沙箱外正反例，工具扫描与收尾地图状态也待补。尚未集成或 push；主控可经门禁拒收／回收，同一 attempt 的原候选和全部旧证据保留。
