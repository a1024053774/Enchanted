# T-197 独立只读审查（第 2 轮）

STATUS: PASS

TARGET: `/private/tmp/t197-cand`，基线 `bb447be5010a825ffa36dfe56b714682037a520c` 加该目录的 `T-197.diff`，范围以 `SNAPSHOT.txt` 为准。

RELEASE: FULL_GO（仅指本轮 T-197 冻结候选可合并，不代表整个产品已完成发布验收）。

本轮未发现可复现的 T-197 缺陷。冻结候选、绑定它的真实入口绿态和反例记录，加上本轮独立输入及变异检查，足以支持本次合并。第 1 轮的候选漂移阻断已由冻结副本和明确绑定的证据解决；本轮没有读取活动工作区的 T-198 改动来判断 T-197。

## FINDINGS

无需要修复的发现，因此没有缺陷对应的文件行号、失败场景或修复建议。以下为验收核对结果及可追溯位置，均不列作缺陷。

| 验收项 | 结果与依据 |
| --- | --- |
| accepted 未回收也不占路径，事件记录不计入 | PASS。`workbench/src/gates/core.ts:1304` 将同仓库、路径相交的 accepted attempt 放入 `not_counted`，其余占用放入 `conflicts`；`:1307` 保存检查事件。冻结绿态经真实集成得到 accepted 后，再认领同路径任务成功，且旧 attempt 未回收；本轮读回现场数据库核对了事件。独立检查还覆盖 accepted 与两个进行中 attempt 混合重叠。 |
| 进行中重叠无理由仍拒绝并给清单 | PASS。`core.ts:1305`、`:1311` 保留任务、attempt、快照和路径，错误为 `path_overlap`，提示主控写 `overlap_reason` 或等待。独立混合场景同时返回两个进行中的任务，accepted 只出现在 `not_counted`，错误清单与持久化事件一致。 |
| 空字符串、纯空白理由无效 | PASS。`core.ts:1287` 调用 `text()`（`:99`），拒绝空字符串、普通空格及 Unicode 空白，返回 `invalid_text`。冻结绿态覆盖混合全角空白；本轮另测空字符串及不换行空格／全角空格。 |
| 有理由放行，理由与事实入事件 | PASS。`core.ts:1308` 保存理由原文、冲突身份、路径、执行主控身份及通过状态。本轮以不同中文理由及带首尾空格、尖括号的理由验证输入依赖和原文保留；进行中占用不会因同场存在 accepted 而被漏掉。 |
| 任务页显示重叠和理由 | PASS（历史数据及消费代码链）。`workbench/src/gates/taskHistory.ts:31` 生成“路径重叠”、任务、路径、放行理由和通过状态；干净检查及仅有 `not_counted` 的检查不生成噪音。本轮既检查真实绿态事件的投影，也通过 `core.ts:3699` 的真实 `task_history` 请求处理器读取独立事件。未变化的基线 `app/TaskRecord.tsx:77` 将 label、passed、detail 渲染到时间线；IPC 见基线 `app/preload.ts:33`、`app/main.ts:333`。未进行 Electron 实机视觉检查。 |
| SKILL.md、a2a help、README、角色卡一致 | PASS。主控说明 `terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md:24`、`src/terminalCli.ts:43`、`README.md:449` 均说明跨任务重叠由主控看清单判断，放行须写理由，accepted 不占用。实际运行 help 确认输出包含该规则。SKILL.md 第 28～33 行、help 第 35～46 行和 `roles/worker.md:17` 的“不用交叠参数绕过”约束的是改卡后旧会话的回收流程，与跨任务判断的适用场景不同；monitor、reviewer 不负责认领，未发现另一个执行主控禁止放行的条款。 |

已沿直接调用核对：`claim` 与 `dispatch` 共用 `core.ts:1563` 的认领路径，并在全局认领锁内检查占用；`run` 保存 `overlap_reason`（`:3019`），再由 `runDispatch`（`:3033`）转交 `dispatch`。没有增加 worker 的认领权限。

状态语义也与需求相符：正常集成及恢复路径只在分支推进、读回和内容核对成功后把 attempt 设置为 accepted（`core.ts:4278`、`:4338`）。仅机械验收通过、审查通过或集成尚未完成，不会提前释放路径；集成失败事件不等于 accepted。独立输入覆盖 submitted／verified、integrating、rework 等状态。Ubiquitous language 统一使用实际状态名 `accepted`，不把“机械验收通过”误当作 accepted。

## EVIDENCE：做过的检查与命令

### 候选绑定

本轮运行：

```sh
cd /private/tmp/t197-review2
python3 verify-snapshot-v2.py > snapshot-check-v2.json 2> snapshot-check-v2.stderr.log
```

退出 0，PASS。脚本用 `git archive` 读取指定提交的约定目录，在本审查目录重建基线并应用提供的补丁，再直接比较冻结副本的 602 个文件／符号链接，差异为零，没有计算摘要。另用 `git show <指定提交>:workbench/app/<文件>` 保存未变化的 UI 消费代码至 `runtime/baseline-ui/`；没有读取这些文件的活动工作区版本。

第一次辅助脚本 `verify-snapshot.py` 在解压前因当前 Python 的 `tarfile.extractall()` 不支持 `filter` 参数退出 1。原脚本、空输出 `snapshot-check.json` 和异常日志 `snapshot-check.stderr.log` 均保留。v2 改用系统 `tar`，使用新的归档、输出及重建目录完成检查；该辅助脚本故障不是业务红态。

### 已提供的真实入口证据

以下三份记录的版本绑定依据为本轮 BRIEF；本轮检查了冻结测试代码及记录内容，没有重新执行这些命令。在冻结副本的 `workbench` 目录运行绿态和变异；修前红态在含该提交的原仓库运行同一测试文件：

```sh
python3 tests/test_t131_parallel_workers_e2e.py --summary <新绿态结果路径>
python3 tests/test_t131_parallel_workers_e2e.py --mutant accepted-still-counted --summary <新变异结果路径>
python3 tests/test_t131_parallel_workers_e2e.py --revision bb447be50 --summary <新红态结果路径>
```

- `evidence/frozen-green.json`：PASS，全部 15 项检查，包括 accepted 未回收后再认领、`not_counted`、进行中重叠清单、空白理由拒绝和理由入事件。测试经过独立后台进程、socket、真实 Claude Code CLI、Git 和 SQLite；模型接口为本地脚本服务，`real_model_turns=0`。
- `evidence/frozen-mutant.json`：在 `accepted_attempt_holds_no_paths` 上因错误的 `path_overlap` 失败。
- `evidence/red-bb447be50.json`：指定修前源码在同一业务断言失败，测试文件按 BRIEF 与冻结副本逐字相同。后两份记录的顶层状态均为 `INCOMPLETE`，本报告将其作为明确的业务断言失败证据，没有称其为整套测试 PASS。
- 其余未绑定版本的历史 green／mutant／red 记录及 `green-01-test-keyerror.json` 均保留，不用于判定当前候选通过。历史 `history_check.ts` 使用相对源码导入，也不单独作为当前版本的动态证明。

测试新增断言观察的是认领结果、状态和事件，预期来自 T-197／T-196 的领域规则；没有导入生产常量来生成答案。冻结测试对拒绝清单的路径只检查非空，本轮补充独立哨兵路径的精确核对。

### 本轮独立检查

```sh
node independent-check.ts > independent-check.json 2> independent-check.stderr.log
node check-frozen-events.ts > check-frozen-events.json 2> check-frozen-events.stderr.log
node /private/tmp/t197-cand/workbench/src/terminalCli.ts help > a2a-help.txt 2> a2a-help.stderr.log
python3 run-mutants.py > mutant-check.json 2> mutant-check.stderr.log
```

上述命令均退出 0；对应 stderr 均为空。

- `independent-check.json`：PASS，24 项门禁／请求处理检查与 5 项历史投影检查。直接载入冻结模块，在审查目录的真实 Git／SQLite 隔离现场运行。输入包含未创建的哨兵文件、不同任务名、两个当前占用者、一个 accepted 占用者及不同理由；预期来自需求和既有回收契约，不由实现输出生成。状态、清单、事件和历史分别核对。
- `check-frozen-events.json`：PASS，8 项检查。以只读连接打开冻结绿态记录所指向的现场数据库，核对 T-4／T-5 的原始事件与摘要逐项一致，确认 accepted 的不计入路径、拒绝／放行的持久化状态、理由原文，以及从这些真实事件得到的两条重叠时间线。
- `a2a-help.txt`：实际 CLI help 输出包含看 `conflicts` 判断、理由不能为空、accepted 不占路径的规则。
- `mutant-check.json`：5 个变异全部在业务断言上被拒绝，各变异进程退出 1、输出 FAIL；没有把导入异常、环境缺失或崩溃算作检错成功。源码派生副本、每次 stdout 和 stderr 保存在 `runtime/mutants/`，没有修改冻结副本。

脚本均以本目录为产物根目录。复验请复制脚本和所需 evidence 输入到新的审查目录，再运行上述命令；现有现场及红态不应覆盖。脚本中的目录唯一性检查会拒绝复用已有的隔离现场。

## COUNTEREXAMPLE：坏实现能否被拒绝

| 坏实现 | 本轮独立检查结果 |
| --- | --- |
| accepted 继续进入占用清单 | REJECT：`accepted-live-thread`、`accepted-no-thread` 及混合占用场景失败；另有提供的真实入口变异和修前红态支持。 |
| 进行中的 attempt 全部不计入占用 | REJECT：`claimed`、`submitted` 等状态及两个当前占用者的清单／历史检查失败。 |
| 有理由仍一律拒绝 | REJECT：新的中文理由、原文保留及混合放行场景失败。 |
| 放行但事件丢失理由 | REJECT：理由原文及请求处理器历史检查失败。 |
| 任务历史隐藏放行理由 | REJECT：`allowed-sentinel-reason` 失败。 |

这组检查能区分应拒绝与应放行，能检测忽略输入或丢失审计内容的实现；结论不外推为拒绝所有可能的错误实现。

## LIMITATIONS

- 按本轮 BRIEF，未重跑完整端到端测试。当前 Codex 沙箱已知会使 worker 交付的 `sandbox-exec` 失败；本轮真实入口结论采用明确绑定冻结副本的已提供绿态与业务红态，独立补充检查属于 L1 隔离逻辑及真实存储读回，不冒充本轮新取得的 L3 完整入口绿态。
- 任务页检查覆盖真实事件、历史请求处理器和指定基线的既有 IPC／React 消费链，未启动 Electron，也没有视觉截图。`app/` 不在交付的冻结子集内，因此消费代码严格读取指定提交；没有据此声称应用的窗口、布局或其他页面通过实机验收。
- 未动态制造集成崩溃／恢复或真实合并失败；其状态判定依据为直接源码路径及隔离状态输入。未验证真实模型理解主控说明；脚本化模型只证明编排入口和状态行为。
- 本轮能力范围是编排状态、事件、路径作用域和 CLI／任务历史。检索记忆、生产部署、外部消息及生产账户写入为 N/A；没有扩大为这些能力的发布审查。权限只核对相关直接调用及原有边界未被本补丁扩展，没有宣称重新审计全部身份隔离。
- 未更改仓库、冻结副本、测试、分支或既有证据；所有新增脚本、派生副本、日志与报告均写在 `/private/tmp/t197-review2`。没有发现需要新增 RULE 的重复缺陷类型。

结论：可合并
