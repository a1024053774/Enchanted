# T-249-1 交付摘要：侧边面板位与 Git 图

票：`.project-map/tickets/T-249-git-graph-panel.md`；任务卡 T-249-1（base `c89b8ca47`）。

## 做了什么

- **面板位**（`workbench/app/panels/PanelDock.tsx`）：顶栏“面板”按钮开关；放在 `renderer.tsx` 的 `Workbench`
  组件里、`<main className="content">` 右侧（`.workbench` 是横向 flex）。可拖宽、双击分隔线复原，宽度和开关存在
  localStorage。内部注册表登记 `id`、标题、图标、组件；宿主能力只有：跟随的目录、主题、经主进程按 argv 执行的 git、
  打开文件、发通知。不是公开 mod 接口，不加载第三方代码。
- **跟随哪个目录**：渲染进程记下最后一次焦点/指针进入的 `section.pane`（`data-pane-key`）；主进程
  `a2a:panel-directory`（`main.ts`）对它取 `workbench_snapshot`：普通终端用 `lsof -d cwd` 读 shell 现在的 cwd
  （读不到时退回启动目录），受管窗格用它的 worktree；没有聚焦窗格时用项目（或任务）的主目录。面板每 2 秒重读。
  可固定、取消固定。目录不是 Git 仓库时显示多仓库列表（Manygit：按文件夹分组，脏文件数、领先/落后、未推送、无远程、
  最新标签可关；深度 1～5 默认 3；不扫 home、`/`、`/Users/<x>`）。
- **git 在哪一层执行**：`workbench/app/gitHost.ts`，只在主进程里用 `execFile('git', argv)`，不经 shell。读操作有
  子命令白名单、拒绝 `--output`/`--ext-diff`/`--textconv` 等选项，并统一前置
  `--no-optional-locks -c core.fsmonitor=false -c diff.autoRefreshIndex=false`。写操作由面板发来“动作”，argv 在
  `gitGraphModel.ts commandsFor` 里构造并再校验一次：名字以 `-` 开头、非法引用名、非法哈希一律拒绝。
- **Git 图**（`GitGraphPanel.tsx`、`gitGraphModel.ts`；照 herdr-git-graph，MIT，Copyright (c) 2026 Rabeeh T A，
  完整许可声明保留在 `gitGraphModel.ts` 头部）：提交表（泳道、标题加引用标签、日期；宽度够时作者和哈希），每页 300 条、
  滚到底或点“再加载 300 条”；所有分支/当前分支、远程分支复选框；未提交行（虚线连到 HEAD）；详情（标题、哈希、父提交、
  作者、日期、提交者、正文、改动文件 +/-）与 diff；右键菜单、双击标签检出；写操作先弹确认框，破坏性的标红；
  原 mod 的全部操作（检出、检出远程分支、检出到提交、新建分支、打标签、重命名/删除分支、删除远程分支、删除标签、merge、
  rebase、cherry-pick、revert、reset soft/mixed/hard、push、推送标签、commit、pull --ff-only、stash、fetch；后三个在工具栏
  “仓库操作…”里）。刷新：监视仓库根与 git common dir，引用变化完整刷新，其他改动只刷状态（节流 1.5 秒），另外每 15 秒
  轮询。颜色只用主题：泳道色取自终端主题色板（新的 `app/terminalPalettes.ts`，`renderer.tsx` 与面板共用）。
  可调列宽、双击复原；Esc 依次关闭菜单/对话框、diff、详情。
- **受管 worktree 只读**：跟随的目录在门禁 state 的 `worktrees/` 下时，Git 图显示只读说明，写操作菜单项不可用；主进程
  `gitAction` 也按同一规则拒绝（防止绕过界面）。
- **无界面入口** `workbench/app/panels/gitGraphCli.ts`：调用界面同一份 `readGraph`（模型）和 `gitHost.gitRead/gitAction`
  （命令代码），不另写一套。
- **半成品的处理**：之前停掉的会话在 `a2a-wt/git-panels` 写的 `gitHost.ts`、`panels/*` 和 main/preload/renderer 改动
  已搬过来并逐段核对；那个目录没有改动。核对后改了：泳道改为只按提交排（见下）；状态刷新改为真的只刷状态；共享的
  `readGraph`/`withStatus` 搬进模型供界面和 CLI 共用；引用带完整名；受管判断在 state 不存在时不抛错；`lsof` 失败时退回
  启动目录；去掉写死的泳道颜色；去掉 T-250 才有的“在改动面板中查看”菜单项。

### 与原 mod 不同的一处（已上报 issue）

原 mod 把未提交行当作一行放进 `lanes.js` 一起排，会把它右边的提交挤到别的列。验收脚本手推的泳道是“只按提交排”
（工作区有改动时 s1 仍在第 0 列、merge 在第 1 列），任务卡也写 rows 只含提交。所以实现是：提交的泳道照
`lanes.js` 规则只按提交算；未提交行另放在 HEAD 的列上（那一列在 HEAD 之上没被占用时），否则在最右新开一列，虚线一直
连到 HEAD 的圆点。这样提交所在的列不随工作区脏不脏而变。

## 测试命令与红绿结果

### 沙箱里已跑（无界面入口，真实 git）

```sh
python3 acceptance/T-249/check_git_graph.py          # 本 worktree：PASS
```

红绿自检：把 `workbench/app` 和 `acceptance/T-249` 复制到临时目录，套用端到端测试里同样的两个变异
（`test_t249_git_graph_e2e.py` 的 `MUTANTS`），在副本里跑同一个验收脚本。原始输出在 `headless-redgreen/`：

| 版本 | 结果 |
| --- | --- |
| 绿（未改） | exit 0，PASS（16 项全过） |
| 变异 `parents`（解析时父提交顺序颠倒） | exit 1，FAIL 4 项（父提交、泳道） |
| 变异 `order`（日志加 `--reverse`，从旧到新） | exit 1，FAIL 7 项（顺序、父提交、泳道、merge 线段） |

另：`node workbench/app/build.mjs --slot <新 slot>` 构建通过（renderer、main、preload），构建目录用完即删。
本机没有 TypeScript 编译器（`node_modules` 里没有 `typescript`），没有做类型检查。

### 沙箱里跑不了的（Electron）

在沙箱里启动 Electron 报 `bootstrap_check_in ... MachPortRendezvousServer: Permission denied`，起不来。所以经真实
Electron 入口的端到端测试 `workbench/tests/test_t249_git_graph_e2e.py` 已写好但**没有运行过**，红绿结果要由主控在沙箱外
运行后才有。它覆盖票里 Acceptance 的前四条：

1. 夹具（测试自己建）：两条分支、一次 merge、轻量标签和附注标签、一个未提交改动和一个未跟踪文件；面板里的顺序、
   父子关系、分支和标签与 `git rev-list --date-order --parents --all`、`git for-each-ref` 一致；未提交行在最上面，父提交是
   HEAD，文件数与 `git status` 一致，虚线连到 HEAD 的圆点。
2. 从界面新建分支再删除，`git for-each-ref` 的变化正好如此；删除的确认按钮是破坏性样式；`-bad` 被界面拒绝；绕过界面直接
   调 `window.a2a.gitAction` 用 `-f` 也被主进程拒绝；引用和未提交改动不变。
3. 跟随：一个从非仓库目录启动、再在 shell 里 `cd` 到 beta 的终端，聚焦后面板换成 beta（证明读的是 shell 的 cwd）；固定后
   聚焦别的终端不再跟随；取消固定后跟随到非仓库目录，多仓库列表正好是夹具里的 3 个仓库。
4. 跟随 `<state>/worktrees/` 下的目录时只读说明出现、写操作菜单项全部不可用、点了不弹框、直接调主进程被拒，`.git` 下所有
   文件内容前后一致。
5. 判红：`--mutant parents`、`--mutant order` 只改源码副本里界面用的模型，期望测试失败。

测试另记录用户自己的 hc core 前后快照，不一致即 `NO_GO`。

## 留给主控在沙箱外运行的命令

```sh
cd '/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-249-1-a1'
bash workbench/app/RUN-OUTSIDE-T249.sh            # 可选参数：包的 slot 名，默认 t249-<时间戳>
```

它依次：记下正在运行的 Enchanted 进程（pid、启动时间、命令行）→ worktree 没有 `node_modules` 时从主仓库 `ditto` 真复制一份
（打包会在 node-pty 里重编，不用符号链接，避免动主仓库那份）→ 跑验收脚本 → 端到端绿态一次、`parents`/`order` 两个变异各
一次（期望非 0）→ `npm run package:mac -- --variant test --slot <slot>` 打出 `Enchanted Test.app`（核对 bundle id
`org.a2a.workbench.test`、签名、构建目录只剩这个包）→ 删除 `/private/tmp/t249-*` 夹具、其他 `a2a-build-t249-*` 构建目录、
临时复制的 `node_modules` → 再记一次 Enchanted 进程并比较。

结果写到 `evidence/2026-11-07-batch33/T-249/outside-<时间戳>/`（每步的 `.log`、各次 `run.json`、`summary.json`），
全是文本；截图放在本机 `/private/tmp/t249-shots-<时间戳>/`，不进仓库。全部符合预期时最后打印 `PASS`。
留下的只有待验收的包 `/private/tmp/a2a-build-<slot>/Enchanted Test.app`，供 Codex 用 Computer Use 验收；脚本不打开它，
不替换、不启动 `/Applications/Enchanted.app`，不连接正在运行的 Enchanted 后台与 hc core。

## 改过的额外目录

无（本次派发没有额外目录）。
