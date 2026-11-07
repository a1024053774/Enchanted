---
id: T-249
title: 工作台的侧边面板位与第一个面板“Git 图”（照 herdr-git-graph）
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## 来由（用户原话，2026-11-07，本对话）

> ok,那还是用目前的.先不做 mod接口,我们先自己做一些我挑的想要的 Mod吧,但是如果能做成接口为以后拓展也更好. 目前我想要这两个:
>   1.https://github.com/rabeeh-ta/herdr-git-graph/tree/main  2.https://github.com/ChmaraX/herdr-gitview
>   你做的话新打包再做,避免影响现在这个enchanted终端.
>   然后之前的项目规则说放外置硬盘的规则弃用,直接在本机做就行,及时清理构建缓存,你来升级构思主控开票,然后开 opus5.5
>   medium模型执行,最后让codex用 6.1 terra用 computer use以及常规测试来验收.
>   你可能新的包会遇到macos隐私问题弹出是否允许软件访问文稿这个,因为新构建的应用没有同意过这个权限,所以这个我允许你用computer
>   use能力去点这个窗口去允许,不行的话你让code点,我都批准.

前一轮的判断（同一对话）：留在 Electron，不改 GPUI。

## 要做的

1. **面板位**（内部接口，不是公开的 mod 接口）：工作台项目视图的右侧加一个可开关、可拖宽的面板位。面板按内部注册表登记：`id`、标题、图标、组件，以及宿主给它的少量能力：当前跟随的目录、主题、经主进程按 argv 执行的 git（不经 shell）、打开文件、发通知。本票和 T-250 是它的两个使用者，所以接口只做这两个面板要用的部分；不加载第三方代码，不做清单文件、沙箱或市场。以后要开放 mod 接口另开决定票。
2. **跟随哪个目录**：默认跟随当前聚焦窗格的工作目录（普通终端取 shell 的 cwd，受管窗格取它的 worktree）；没有聚焦窗格时用项目主目录。面板上可以固定到某个目录，也可以取消固定。目录不是 Git 仓库时显示下面的多仓库列表（Manygit）。
3. **Git 图**：按 [herdr-git-graph](https://github.com/rabeeh-ta/herdr-git-graph)（MIT，Copyright (c) 2026 Rabeeh T A；借鉴代码或算法时在源码里保留其版权声明）的功能做：
   - 提交表：图线（泳道）、说明（标题加引用标签）、日期；宽度够时显示作者和哈希。按时间倒序，每页 300 条，滚到底或点“再加载 300 条”继续。“所有分支 / 当前分支”切换，“远程分支”复选框。
   - 最上面一行是未提交的改动，用虚线连到 HEAD。
   - 点提交打开详情：标题、哈希、父提交、作者、日期、提交者、正文、改动文件（+/- 行数）；点文件看 diff。
   - 右键菜单和双击标签检出；会改仓库的操作先弹确认框（破坏性操作标红），按原 mod 的 argv 执行：检出、检出远程分支、检出到提交、新建分支、打标签、重命名或删除分支、删除远程分支、删除标签、merge、rebase、cherry-pick、revert、reset（soft/mixed/hard）、push、推送标签、commit、pull --ff-only、stash、fetch。名字以 `-` 开头的一律拒绝，不能被当成选项。
   - 多仓库列表：目录下的仓库按文件夹分组，每行显示脏文件数、领先/落后、未推送、无远程、最新标签（可关）；点一行打开它的图。扫描深度 1～5，默认 3；不扫 home、`/`、`/Users/<x>` 这一层。
   - 刷新：监视仓库根目录和 git common dir，引用变化做完整刷新，其他改动只刷状态（节流 1.5 秒）；另外每 15 秒轮询一次。所有读操作带 `--no-optional-locks -c core.fsmonitor=false -c diff.autoRefreshIndex=false`。
   - 只用主题色，不写死颜色；可调列宽，双击分隔线复原；Esc 依次关闭选择器、diff、详情。
4. **受管 worktree 只读**（主控按项目规则定的默认，用户可改）：跟随的目录是门禁管理的任务 worktree 时，Git 图只读，写操作按钮不可用并说明原因；门禁保护 worktree 的 Git 元数据，用户直接改算人工介入。项目主目录和普通终端的目录可以写。
5. **新打包**：开发与验收都用 `npm run package:mac -- --variant test --slot <新 slot>` 打出的 “Enchanted Test”（独立 bundle id `org.a2a.workbench.test`、独立数据目录），不替换 `/Applications/Enchanted.app`，不停、不重启、不连接正在运行的 Enchanted 与它的后台和 hc core。

## 验收

- [ ] 端到端测试经真实入口（打包好的 Enchanted Test，或 `app/start.mjs` 以独立数据目录启动的 Electron）：测试自己建一个夹具仓库，包含两条分支、一次 merge、一个标签、一个未提交改动。面板里提交的顺序、父子关系和标签与 `git rev-list --date-order --parents --all`、`git for-each-ref` 的输出一致（期望值从 git 读，不从实现读）；未提交行存在并连到 HEAD。
- [ ] 至少一个写操作（新建分支，再删除）从界面执行，之后 `git for-each-ref` 显示的变化与预期一致；名字以 `-` 开头被拒，仓库不变。
- [ ] 跟随：聚焦窗格切到另一个仓库的终端时，面板换成那个仓库；固定后不再跟随。非仓库目录显示多仓库列表，数量与夹具一致。
- [ ] 受管 worktree 只读：跟随门禁 worktree 时写操作不可用，Git 元数据不变。
- [ ] 测试对已知坏的实现失败：例如把父子关系或排序故意改错的变异版本，测试判红。
- [ ] 独立验收：Codex `gpt-6.1-terra` 新开会话，用 Computer Use 操作 Enchanted Test 的窗口，加上常规测试，逐条核对上面几条，写验收报告。
- [ ] 正在运行的 Enchanted 前后不受影响：验收前后各记一次它的后台进程 pid 和启动时间，两次一致。
- [ ] 构建缓存、临时构建目录与测试夹具用完即清；证据目录只留文本摘要和截图的文字说明。

## 不做

不做公开的 mod 接口、第三方 mod 加载与沙箱；不做远程机器（原 mod 的 remote spaces）；不做原 mod 的自动更新检查；不改门禁；不 push；不替换 /Applications。

## 执行与授权

- 分工（用户原话见上）：构思主控开票；Claude Code `claude-opus-5-5`、medium 强度执行；Codex `gpt-6.1-terra` 用 Computer Use 和常规测试验收。
- macOS 隐私授权：新包首次访问“文稿”时，若弹出系统授权框，用户已授权执行方用 Computer Use 点“允许”；点不了就让验收的 Codex 点。只限这一个针对 Enchanted Test 的“文稿”授权框；其他系统设置、登录、付款等仍要停下问用户。每次代点记入证据（时间、谁点的、对话框原文）。
- 完成后在 worktree 的分支上提交，经验收 PASS 后合入本地 main，不 push。
