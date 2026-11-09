# T-249-1 第四次派发：修复与交付记录

**PASS（本卡 worker 范围）**：两处 Git 详情缺陷已有真实 Git 红绿证据，`no-panel` 已加入真实窗口测试和必跑编排，卡上三条机械完成条件均通过。

**INCOMPLETE（整票集成验收）**：本轮未运行真实 Electron 窗口、新包、窗口里的三个变异或独立 Computer Use 验收；这些仍由主控在集成前完成。无界面检查不证明窗口可用，也不替代独立审查。

## 身份与版本

- 任务 `a2a+T-249-1`；attempt `27481daa-4502-44a9-873e-c00a7b1cab4a`；session `21013bd8-945a-4b32-8f9d-3ee62af22cfb`；fence `3`；spec_rev `4`。
- 当前 worktree 基线：`8683c4edba5ff635fea7e2918af059e4cd5ba07c`。
- 先读取审查 `controller/review-01.md`，再按任务卡的原命令导入 `dc51588832c705aaee0463fb1b96b5586e4c91b7..0c3da7adedf5a2c0a61af32cf3d1bb2bb39b6083`，先提交为 `d0fd21e9424e642ef00bb0898d9af2f386e7f35e`。
- 本轮修复代码与测试：`432b270f3fba92941bfffe1b00912b2dc444b4c9`。之后只补交本轮报告和状态证据；完整交付提交号见 submit 请求。
- 环境：Node `v26.5.0`、Git `2.52.0`；自动提交尾注记录 `codex-cli 0.167.0`、`gpt-6-astra`、`xhigh`。详细绑定见 [run-context.json](run-context.json)。
- 旧 `attempt-fence2/`、旧 RESULTS 与此前失败记录原样保留；它们不算本轮通过证据。

## 改动及其依据

1. `gitGraphModel.ts` 的 `diffArgs` 在根提交 `show`、普通提交 `diff`、未提交 `diff` 三条路径中统一使用 `:(top,literal)` 路径。真实反例覆盖 `file*.txt`、`file[1].txt`、`:(glob)*.txt`，逐项检查选中文件内容存在、另一文件的 sentinel 不存在，并与独立 `git --literal-pathspecs` 输出逐字相等。
2. `fileArgs` 读取 HEAD：存在时使用该提交；`rev-parse --verify -q HEAD` 返回 1 时读取 Git 空树标识作为基线。状态、行数和随后单文件 diff 使用同一基线。读取失败仍抛错，不用空列表代替失败。`CommitDetails` 已接上异步读取并保存基线；未跟踪文件仍从 `ls-files --others` 加入列表，点击时显示尚无 diff 的说明。
3. `gitHost.ts` 只新增精确的 `hash-object -t tree /dev/null` 只读形式；没有允许 `-w` 或其他文件/类型。带写选项和其他文件参数的反例均被拒，读取详情前后的 Git 元数据直接按文件内容比较保持一致。空树标识由当前仓库的 Git 读取，不硬编码对象格式，也不写对象。[Git 的 diff 文档](https://git-scm.com/docs/git-diff)说明比较基线可为 tree；[hash-object 文档](https://git-scm.com/docs/git-hash-object)区分对象标识计算与 `-w` 写入。
4. `test_t249_git_graph_e2e.py --mutant no-panel` 在源码副本里将 `renderer.tsx` 的 `{dockOpen && <PanelDock` 换为 `{false && <PanelDock`。窗口加载后，先等面板开关打开，再查询实际 DOM，最多等 20 秒；缺少面板必须写下 `侧边面板存在` 的失败断言。查询时 CDP 抛错直接保留为 INCOMPLETE，不能当作面板不存在的红态。
5. `RUN-OUTSIDE-T249.sh` 必跑 `no-panel`、`parents`、`order`。每个变异都须非零退出、报告 FAIL、命中自己的指定失败断言、清理成功且用户 hc core 不变，才满足该项预期。输出目录改为本轮 `attempt-fence3/outside-<时间戳>/`。本轮未改变脚本清理所有权和打包方式。

面板仍由 `Workbench` 右侧的 `PanelDock` 挂载；聚焦窗格键经 preload 送到主进程，普通终端取 shell cwd，受管窗格取 worktree。Git 仍由主进程 `gitHost.ts` 的 `execFile` 按 argv 执行。无界面入口继续复用同一模型与命令。没有修改门禁、冻结验收、依赖清单或锁文件；没有新增依赖或 T-250 功能。

## 本轮实际运行

| 命令或检查 | 结果及证据 |
| --- | --- |
| `/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t249_git_host.mjs` | 修复前 19 项中 10 项失败：9 个路径反例、1 个无 HEAD 列表反例，见 [host-red.txt](host-red.txt)。修复后及最终均 22/22，见 [host-green.txt](host-green.txt)、[host-final.txt](host-final.txt)。 |
| 同上，加 `--test-name-pattern=unborn single-file\|hash-object`（位于测试文件参数前） | 修复前单文件 diff 报 `bad revision 'HEAD'`，2 项读权限反例已通过，见 [unborn-diff-red.txt](unborn-diff-red.txt)。修复后该 diff 已包含在 22/22 中。 |
| `/usr/bin/python3 workbench/tests/test_t249_outside_safety.py` | 新增编排要求在旧脚本上 3 项失败，见 [outside-safety-red.txt](outside-safety-red.txt)；修正后与最终均 5/5，见 [outside-safety-final.txt](outside-safety-final.txt)。覆盖变异登记/必跑、指定断言分类、启动失败、DOM 缺失与 CDP 故障区分、旧运行与链接目标不被清理。 |
| `/usr/bin/python3 acceptance/T-249/check_git_graph.py` | 最终 PASS，见 [acceptance-request-tmp.txt](acceptance-request-tmp.txt)。这是本轮实际重跑结果，冻结程序没有改动。 |
| `node workbench/app/build.mjs --slot t249-fence3-check` | renderer/main/preload 构建成功，见 [build.txt](build.txt)。有大于 500 kB 的 chunk 提示；本轮没有性能收益主张。 |
| 源码 diff、Shell 和 Python 语法 | PASS，命令见 [static-checks.txt](static-checks.txt)。 |

首次冻结验收有两项失败，原输出保留在 [acceptance-final.txt](acceptance-final.txt)，该文件名中的 final 不表示通过。当时 `TMPDIR` 放在本 worktree 下，夹具因此落入真实门禁 state 的 `worktrees/` 子树，产品正确拒绝了建分支和删分支。随后独立重放建分支得到明确的只读错误，见 [acceptance-fixture-location.json](acceptance-fixture-location.json)。这不是原生沙箱权限拒绝；未改权限、保护逻辑或验收条件。将夹具放到任务已授权的请求临时目录后重跑通过。

重放机械验收时，使用处于受管 worktrees 树之外的测试临时目录。例如本 attempt 中可用：

```sh
TMPDIR="$A2A_REQUEST_DIR" /usr/bin/python3 acceptance/T-249/check_git_graph.py
/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t249_git_host.mjs
/usr/bin/python3 workbench/tests/test_t249_outside_safety.py
```

本轮构建仅临时在 `workbench/app/node_modules` 链接现有依赖，使用自己新建的请求临时目录作为 TMPDIR；没有在构建输出里放链接。构建体量与清理状态见 [build-cleanup.json](build-cleanup.json)，构建目录、缓存和临时依赖链接均已删除；测试夹具已清理，只留文本证据。原始工具输出的行尾空格保留，源码与文档 diff 检查无新增空白错误。

## 自查与证据边界

按项目的 `design-integrity-review` 实现者自查规则，检查从导入提交到修复提交的增量。扫描找到真实仓库根，`findings=[]`、`acceptance_changes=[]`，见 [design-scan.json](design-scan.json)。这只用于定位，不能单独证明结构正确。人工核对了真实调用方、空树读取的精确权限形式、失败传播以及脚本的指定断言分类；没有新增吞错、重试、兼容路径或平行 Git 实现。

按 `behavioral-acceptance-review` 检查证据边界：宿主测试经过生产模型、生产宿主和真实 Git，期望独立从 Git 读取；22 项里保留了读权限、受管写保护与 HEAD 虚线终点的旧回归。脚本检查使用模拟报告和 DOM 查询结果，只证明编排分类逻辑。`no-panel` 的真实窗口反例本轮 **未运行**，不能将这 5 项检查当作它的窗口红态。没有再开 worker 内的独立审查会话；正式独立审查由门禁安排。

全仓测试未运行：本轮没有修改共享门禁、存储、公共接口或依赖配置，回归范围是 Git 图宿主、测试编排和界面构建。真实焦点/固定目录、菜单、拖宽、Esc、watch 时序和打包后行为仍须真实窗口检查。审查 01 留下的 Esc 与终端焦点限制仍交 Terra 核对，没有将未复现的猜测当成缺陷修补。

## 主控的集成前步骤

在交付候选的 worktree 中、沙箱外运行（使用全新 slot）：

```sh
bash workbench/app/RUN-OUTSIDE-T249.sh t249-fence3-review-20261108
```

脚本运行真实窗口绿态及三个指定变异，并执行 `npm run package:mac -- --variant test --slot t249-fence3-review-20261108`，输出独立 bundle id 的 Enchanted Test。包路径由脚本打印，只保留待验收包；不替换或启动 `/Applications/Enchanted.app`。主控还需核对正式 Enchanted 前后 PID/启动时间和用户 hc core 不变，再由 `gpt-6.1-terra` 用 Computer Use 与常规测试独立验收。敏感脚本的证据须由用户阅读批准后才能集成；本 worker 不集成、不 push。

项目地图收尾检查退出 1，见 [project-map-status.txt](project-map-status.txt)：`T-257` 关闭但缺 Resolution；`REVIEW.md` 因本脚本变化而 stale。前者在开工时已存在，后者须主控核对覆盖版本。两个范围外问题已通过 issue 排队上报（请求号 `a36705fb-53fd-4251-aab8-b664d2ed3454`、`bf4f6bcb-86eb-48da-b2af-964d50a2d295`），未改地图、票或 REVIEW.md；`workbench/README.md` 已同步本轮行为。queued 只表示排队，不表示问题已送达或处理。

额外可写目录为 `[]`，没有修改额外目录。请求目录只用于本 attempt 的 issue/submit 请求与已清理的临时测试、构建文件，请求文件不会进入提交。最终 Git 提交后按任务卡显式 submit，排队不等于门禁接受或验收通过。

**Works**：本轮两项缺陷的真实 Git 红绿成立，三条机械完成条件通过；`no-panel` 已进入真实窗口必跑路径，分类检查通过。

**No regression**：宿主 22/22、脚本 5/5、冻结验收及 renderer/main/preload 构建通过；全仓和真实窗口未运行。

**Risk / undo**：整票验收、治理状态与敏感脚本用户审批未完成；候选尚未集成或 push，主控可经门禁拒收/回收本 attempt，原候选、红态与失败现场文本仍保留。
