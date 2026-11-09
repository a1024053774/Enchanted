# T-262 当前候选完成报告（用户 #111）

INCOMPLETE：自动行为测试 PASS，整票 INCOMPLETE。当前候选可按用户 #111 指示提交并显式 submit，供主控在准确提交上打 Test 包、做原生 select 键盘观察和独立审查；这些剩余工作不由 worker 预先称为通过。

**Works**：主控真实 Electron/后台完整场景 `green-outside-04.json` 为 38 项 PASS / 退出 0；父版 `red-outside-05.json` 的排序及任务双区过滤业务红态有效，四个已知坏实现均在相应业务断言 FAIL / 退出 1。当前三个源文件与主控绿态后快照逐字节一致，见 [provenance-08.json](provenance-08.json)。
**No regression**：完整场景也验证人工介入、原文与控制字符、完整回执、刷新、跨项目切换与迟到响应、错误恢复、空态、真实 900×700 窄窗和 details 键盘操作。静态/语法及 diff 检查已通过；旧 Claude 全流程和全仓测试未运行，不能称其 PASS。未改其他页面、后台、冻结文件、schema、API、依赖或全局配置。
**Risk / undo**：缺少完整原生 select 键盘 Computer Use 和独立审查，整票验收留给主控。当前只提供候选；如需撤回，由主控通过正常门禁拒收或安排回退。未 push，worker 不 verify/integrate/reclaim。全部原失败和修订前快照保留，额外可写目录 []，无额外目录改动。

## 当前身份与实现

task `a2a+T-262-1`；attempt `64d48cf7-0cfc-4078-8a13-6f0067297990`；session `f08fffc6-d09d-4a7c-8253-e5ddf60fca04`；fence 2；spec_rev 2。base 为 `3647a07bdacb514cdc303965be8c52b84d9356b2`，启动记录为 `235c886f-da43-46b9-bdb6-93f9d479a7c0`，环境报告工具为 `codex-cli 0.167.0`；实际模型/强度由提交钩子读取原生会话写入尾注，不手工填写。完整候选 SHA 由本次提交和 submit 请求绑定。

RecordsPage 采用一个记录索引，统一用户输入和门禁回执的任务/会话筛选、倒序与选项；只有一种来源的会话也可选，同名主控用首条记录时间及短身份区分。原文、追溯和完整 JSON 通过 details 展开。两类读取共同发布、旧请求失效，CSS 规则限定于记录页。

测试通过独立 SQLite 原始记录、真实后台/IPC/Electron 页面与正常表单操作验证上述行为。窗口尺寸由本票自有启动器读取真实 BrowserWindow；每次项目/独立终端切换先确认身份和标题，再进入“记录”。详见 [NAVIGATION-07.md](NAVIGATION-07.md)。本轮没有再改产品或测试，也没有重跑任何真实场景。

## 已取得证据

来源均为主控在本 worktree 为外层 cwd、原生沙箱外的实际运行；worker 只读核对并复制必要结果。主仓库原目录为 `/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/`；同目录 diagnostics/stdout 保留，具体来源和副本路径见 provenance。退出码来源为用户 #111 的主控实跑回传。

| 运行 | 原状态 / 退出码 | 所证明的事实 |
| --- | --- | --- |
| `red-outside-05.json` | FAIL / 1 | 父版排序与双区任务过滤的两个独立业务断言检出缺陷 |
| `green-outside-04.json` | PASS / 0 | 当前候选完整 38 项通过 |
| `mutant-no-sort-02.json` | FAIL / 1 | 取消排序被检出 |
| `mutant-receipt-task-02.json` | FAIL / 1 | 回执忽略任务被检出 |
| `mutant-ignore-session-02.json` | FAIL / 1 | 忽略会话被检出 |
| `mutant-no-full-receipt-02.json` | FAIL / 1 | 完整回执原文被替换时被检出 |

汇总及必要原始 JSON 在 [controller-08](controller-08/)。四个 mutant 的 02 后缀是此前未使用的文件名，全部在 green04 后以 navigation-07 当前脚本运行；`controller-runs-07.command` 中后缀 04 的变异命令未再执行，不是缺失证据。

这组运行均 `core_cleanup` 返回 `stopped=true`，`cleanup.removed=true`，无供应商 CLI。green04 的真实窗口和内容尺寸均为 900×700，导航快照实际记录“终端 → 记录”，传输延迟/断连计划完成且代理无错误。随机哨兵证明刷新从真实存储读到新增输入及回执，不是固定页面输出。

历史 `green-outside-02` 保持 INCOMPLETE（Browser CDP 命令不存在），`green-outside-03` 保持 FAIL（导航未重新进入记录页）；修复驱动后才取得 green04，未删除或改写旧结论。父版05的两个业务断言未被后续驱动修订削弱，按用户指示不重跑。

## 自查与交付边界

- [design-integrity-self-review-08.md](design-integrity-self-review-08.md)：自查 PASS，未发现已确认结构缺陷；历史快照及当前测试中的合法异常边界保留，失败分类、取证和清理由运行器负责。
- [behavioral-acceptance-self-review-08.md](behavioral-acceptance-self-review-08.md)：自动行为证据成立，整票仍 INCOMPLETE；这是实现者自查，不能替代独立审查。
- select 的程序化表单选择不称作原生键盘证明。完整原生键盘 CU、准确提交的 Test 包观察及独立审查由主控完成，再走验收集成。
- 项目地图 Problems 0、Stale living docs 1；README 的候选说明由主控集成时同步，worker 不越权改 README 或地图。未操作正式 Enchanted、T-249 Test 或其他任务。
- 提交前核对写入范围、冻结文件、身份和钩子；提交后核对自动尾注和完整 SHA，再按本次身份 submit 一次。queued 仅表示请求排队，不代表受理或验收通过；正常回执不再新增提交。

---

以下阶段记录保留原文与原状态，旧身份不代表本次交付身份。

# T-262 worker 阶段记录

BLOCKED

**Works**：已核对真实记录来源及调用链，新增无模型 E2E 夹具草稿；尚未取得业务红态，产品代码未修改。
**No regression**：未运行回归测试；本次没有产品行为变更。project-map status 在开始与停止前均为 Problems 0、Stale living docs 0。
**Risk / undo**：隔离后台的进程残留核对被沙箱拒绝，现场保留待主控核对；测试草稿未完成、未提交、未 submit。

## 任务与边界

任务 `a2a+T-262-1`，attempt `767db60f-662d-4440-87ed-3eedb07bf6b7`，session `e2d73e46-1c34-4cae-a6b4-2b67a67cdcc4`，fence 1，spec_rev 1。
基线 `f80d5cdbf0e1b62de864300eff7bb4497f8c4c70`。本次仅新增测试草稿及本目录证据，未改冻结验收文件、后台或其他页面。额外可写目录为 []，没有额外目录改动；临时夹具位于本 attempt 的请求目录。

小目标：统一用户输入和门禁回执的任务/会话筛选、倒序与身份展示，保留原文和完整回执，覆盖异步切换与键盘、窄窗场景。非目标与任务卡一致。

## 已核对事实

- `RecordsPage` 由 `renderer.tsx` 按所选项目挂载。输入记录自己加载、筛选，`Receipts` 单独按项目加载，没有任务/会话筛选。
- `userInputRecords.ts` 把输入的 thread 映射到已有 launch；无 launch 输入仍有 thread。后台 `relay_receipts` 返回 launch，保留完整 result。
- 会话选项当前只有角色和任务，同名项目主控无法区分；输入读取按插入顺序返回，页面没有倒序处理。
- 测试复用现有 Electron 启动入口和纯清理 helper，不调用旧测试的 Claude Fixture。依赖从既有 checkout 只读使用，未安装依赖。

## 首次运行与阻断

精确命令见 `commands.txt`，原始精简 JSON 见 `red-01.json`。退出码 1。

真实后台已进入 hc 启动流程，但在 `workbench/src/hc.ts:201` 调用 `/bin/ps` 核对 core 和调用者的进程组时返回 `spawn EPERM`。这属于环境失败，不是需求断言失败，不能用作红态。未打开 Electron 窗口，未进入页面断言，未启动 Claude 或任何额外 agent CLI。

清理 helper 先调用私有 core 的停止步骤，随后 `/bin/ps` 残留进程检查同样返回 `PermissionError: Operation not permitted`。不能确认所有进程已退出，未删除现场；目录、时间、文件数和字节数见 `fixture-status.json`。没有换命令重试权限检查。

按 worker 角色卡的权限拒绝规则，blocking issue 已写入请求目录：`28dda935-00a8-4af9-b8be-d8058958cf27`，返回 `queued=true, delivered=false`。排队不是主控已受理。请求文件没有放进 Git。

## 待完成

主控需处理允许产品原生 `/bin/ps` 身份核对与残留检查的隔离环境，并核对回收上述现场。权限变化交用户决定。环境恢复后先取得父版业务红态，再实现页面，扩展测试的刷新/竞态、空态/错误、完整内容、键盘与窄窗断言，运行 2–5 个已知坏实现及相关回归；最后做结构自查、主控独立审查和门禁交付。

测试目前是 Tracer bullet 草稿，只包含两个业务断言，不能代表完整验收。behavioral-acceptance-review 未执行；design-integrity-review 尚无产品候选可审。没有把程序操作称为人工 Computer Use。

## 用户 #92 后续：测试环境交接

以上为首次阻断时的记录，原证据保留。主控已完成旧夹具清理并接手真实入口测试，worker 权限未变。当前状态 INCOMPLETE：仅修订夹具与启动诊断，产品代码未改，等待主控取得有效父版红态。修订、准确运行命令和本地检查见 [ENVIRONMENT-02.md](ENVIRONMENT-02.md)。

## 用户 #96 后续：排序红态与候选

主控已取得有效父版排序红态。worker 在卡内完成页面候选和扩展测试，隔离标准构建通过；真实键盘驱动及完整绿态、变异仍待主控运行，状态 INCOMPLETE。详见 [IMPLEMENTATION-03.md](IMPLEMENTATION-03.md) 与 `controller-runs-04.command`。旧证据未覆盖。

## 主控 #102 后续：新 attempt 恢复

INCOMPLETE。本次为 attempt `64d48cf7-0cfc-4078-8a13-6f0067297990`、fence 2、spec_rev 2，旧 attempt 已回收，上文身份与“等待重启”是历史记录。三个文件跨 base 无冲突，候选与精简证据已经恢复，测试改用真实 select 的标准表单选择路径；业务期望和 details 的 Enter 检查不变。本轮没有启动应用、ps 或构建，没有 Git 提交或 submit。

当前事实、检查与限制见 [RESUME-05.md](RESUME-05.md)；主控下一步准确命令为 `controller-runs-05.command`。完整绿态、四个变异、原生 select 键盘 Computer Use 与独立审查仍待补，不沿用旧候选的通过结论。

## 主控 #104 后续：窗口尺寸驱动

INCOMPLETE。主控已跑完前两条：父版 `red-outside-05` 在排序与双区任务筛选有效失败，候选 `green-outside-02` 前 21 项检查通过、无业务失败，因 Browser CDP 窗口命令不存在而中断，两次清理成功。worker 本轮只将尺寸操作移到自有 Electron 启动器，读取真实 BrowserWindow 尺寸；原窄窗和后续业务期望、四个变异不变。见 [WINDOW-DRIVER-06.md](WINDOW-DRIVER-06.md)。下一步命令改为 `controller-runs-06.command`，不再重跑父版。未提交或 submit。

## 用户 #108 后续：补齐切项目后的记录页入口

INCOMPLETE。`green-outside-03` 已通过前 26 项检查，之后等待 beta 记录失败，原 FAIL 和成功清理证据保留。worker 核对了项目导航回到终端的既有语义，本轮只修测试：五处入口统一等待项目身份及标题后点击“记录”，保留原数据、业务断言、迟到响应顺序和四个变异，增加清理前精简页面诊断。说明见 [NAVIGATION-07.md](NAVIGATION-07.md)，新命令为 `controller-runs-07.command`，候选输出 `green-outside-04.json`；父版不重跑。未启动应用或后台，未提交或 submit。
