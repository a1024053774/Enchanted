# T-113 Enchanted 产品页：验证记录

- 任务：T-113 / attempt a1，worker `s18-t113`（用户指定由 Claude 模型来做，本票例外）
- 分支：`exec/t113`，起点 main `1267805a2`；按执行主控 #62、#63 两次 merge main（不 rebase）：先合入含 T-112 的 `0797da885`，再合入含 AGENTS.md 修订的 `13b983030`
- 记录时间：2026-10-20
- 第一轮独立审查（`independent-review-01.md`，审查对象 `28b2ab19b`）判 NO_GO，F1、F2、F3 已修复，见下文“审查 01 的修复”。
- 第二轮独立审查（`independent-review-02.md`，审查对象 `8341208d7`）判 NO_GO，R02-F1 已修复，见下文“审查 02 的修复”。手机一轮的停顿已查明是测试方法的问题，不是页面的问题，见“运行稳定性”；驱动改成每个场景一个新的 Chrome 进程之后，连续两次完整运行都是 327/327。
- 状态：**INCOMPLETE**。站点文件、演示交互、禁用 JS、内部链接、检索与对照表都已完成并通过；有两项在本票内无法变绿：
  1. 外链检查 7 项 404：链接指向改名后的 `a1024053774/Enchanted`，要等 T-114 改名并公开后才存在。已上报 issue `20261020T173836Z-worker:s18-t113-issue-001`，建议移到 T-114 第 ⑥ 步复验。
  2. `project_map.py status` 在本稀疏 worktree 里报 8 个问题：都是 `findings/` 和 `.grilling/` 不在稀疏检出范围内造成的断链，起点上就有，本票没有新增；需要合入后在 main 上复核 0 问题（T-108、T-110 也是这样处理的）。

## 交付了什么

站点放在 `docs/`，按 GitHub Pages「main 分支 /docs」方式发布：不用 Actions，没有构建步骤，也不引用任何外部库或字体。

| 文件 | 作用 |
| --- | --- |
| `docs/index.html` | 全部文字内容。演示区里有一段不依赖 JS 的说明文字 |
| `docs/assets/site.css` | 页面样式；深浅两套配色，跟随系统，也可以手动切换 |
| `docs/assets/site.js` | 主题切换，以及只在启用 JS 时显示的引导和重置按钮 |
| `docs/assets/demo.css` | 演示窗口的样式，取自 `workbench/app` 的 css，选择器限定在 `.wb` 下，保留 Synara MIT 声明 |
| `docs/assets/demo.js` | 演示的预设数据和交互：纯前端，不连后台，不调模型 |
| `docs/.nojekyll` | 让 Pages 原样发布，不经 Jekyll 处理 |

本目录里的验证脚本：`check_demo.mjs`（浏览器驱动）、`scenarios.mjs`（逐项预期）、`check_links.py`、`scan.sh`、`mutants.sh`。运行输出也在本目录：`browser-run.txt`、`links.txt`、`scan.txt`、`mutants.txt`、`flaky-runs.txt`。

## 复现命令

在仓库根目录运行。需要 Node 26（自带 WebSocket）、Python 3、本机的 Google Chrome。浏览器检查用无头 Chrome：每个场景新起一个 Chrome 进程，配一个新建的临时 profile（在 `/private/tmp/t113-chrome-*`，结束时删除），不碰用户自己的 Chrome profile。

```sh
python3 -m http.server 8613 --bind 127.0.0.1 --directory docs &   # 静态服务器
node evidence/2026-10-20-batch18/T-113/check_demo.mjs --url http://127.0.0.1:8613/ --shots /private/tmp/t113-shots
python3 evidence/2026-10-20-batch18/T-113/check_links.py docs
sh evidence/2026-10-20-batch18/T-113/scan.sh
sh evidence/2026-10-20-batch18/T-113/mutants.sh                 # 自带 8614 端口的服务器
kill %1; rm -rf /private/tmp/t113-shots
```

`--shots` 可以省略。按用户 2026-10-19 的裁定（“证据截图什么的都不要了”），截图只写到 `/private/tmp` 供自查，不进仓库。

本次的环境：Google Chrome 155.0.8059.85，Node v26.5.0，Python 3.9.6，macOS（arm64）。

## 红态

起点 `1267805a2` 上没有 `docs/`：

```
$ git ls-tree --name-only HEAD docs
（无输出，exit 0）
```

## 演示交互：真实浏览器逐项点击

`browser-run.txt`：**327/327 PASS**（审查 02 修复、驱动改为每个场景一个 Chrome 进程之后；连续两次相同），桌面（1440×900）和手机（390×844，DPR 2，开启触摸模拟，用触摸事件轻点）各跑一遍。每个场景结束都核对控制台，没有 error、warning 或未捕获异常。

预期取自 T-113 票列出的交互和真实工作台的源码（`workbench/app/renderer.tsx`、`FlowPage.tsx`、`QuestionsPanel.tsx`、`AppNotifications.tsx`、`workbench/src/sidebar.ts` 的 `aggregate`），没有拿本页实现的输出反推。

| 场景 | 票里的交互 | 主要检查 | 桌面 | 手机 |
| --- | --- | --- | --- | --- |
| 01 | 点击切换项目 | 当前项、标题、agent 树随项目切换；没有会话的项目显示空状态和“未知” | PASS | PASS |
| 02 | 侧栏层级树和七种状态；点击切换任务 | 第 0/1/2 层缩进；“未归属”；两个项目合起来覆盖七种状态；点击 agent 后切到它的任务并聚焦窗格（没打开的窗格会打开）；折叠后的汇总文字和汇总状态；任务条切换 | PASS | PASS |
| 03 | 提问面板作答、状态回落、应用内通知 | 通知三行内容、Dock 角标 1；点通知跳回窗格；没选时不能发送；选项填入答复框；发送后显示“答复已送入窗格”；随后面板消失，状态回到“运行中”，通知和角标清空，项目行改按剩下的状态汇总；答复写回终端；两个开关分别生效 | PASS | PASS |
| 03b | 非默认选项、自由答复、通知开关往返（审查 01 的 F1、F2 之后补的） | 选“包含”时终端说包含；选“保留一个版本”时终端说保留；自由答复写回原文，只确认收到，不套用预设决定；关掉通知再打开，同一问题不重放，Dock 待答数和侧栏状态不变。预期取自真实 `QuestionsPanel.tsx`（所选答案原样送入窗格）和 `notificationCenter.ts:29–41`（关闭时清空 active、保留 seen） | PASS | PASS |
| 03c | 与原型属性同名的自由答复（审查 02 的 R02-F1 之后补的） | 两道题分别输入 `constructor`、`__proto__`、`toString`：原文写回、只确认收到、提问面板关闭、状态回到运行中、没有页面异常 | PASS | PASS |
| 04 | 右键窗格菜单（分屏、放大、重命名、关闭、转发右键） | 六项菜单的顺序与真实应用一致；方向键、End、Esc，Esc 后焦点回到 ⋯；向右、向下分屏的几何位置；放大和还原；重命名后保留角色；转发右键后终端区不弹菜单，标题栏仍弹；关闭后布局复原。手机上从 ⋯ 打开菜单，转发右键只在桌面测 | PASS | PASS |
| 05 | 流程页（泳道、阶段、胶囊、折回线、“还有 N 个”） | 7 条泳道；当前阶段；打回 2 次以及分来源计数；审查员和 worker 所在的列；贯穿监视；“阶段未知”；已集成的票默认折叠，展开后 5 段都完成；先显示 4 个，展开到 6 个；未归属；横向滚动 | PASS | PASS |
| 06 | 终端里预设的几行输出 | worker 的红态输出；审查员窗格只读；worker 窗格提示输入会记为人工介入；独立终端；新建终端 | PASS | PASS |
| 07 | 键盘可达 | Enter 选中项目，重绘后焦点不丢；Tab 移到下一项；空格折叠；引导按钮把焦点带到提问选项；焦点轮廓可见 | PASS | 不适用 |
| 08 | 手机宽度、深浅色、不出现横向页面滚动 | 两种宽度下页面都没有横向滚动（打开流程页后也没有）；手机上演示画布可以左右滚动并显示提示；跟随系统的深色和浅色；手动切换并在刷新后保留；浅色页面下演示窗口仍是工作台的深色 | PASS | PASS |
| 09 | 禁用 JS 时内容可读 | 11 段关键文字都在；需要脚本的控件隐藏；没有横向滚动 | PASS | PASS |
| 10 | 会话模型设置（T-112 合入后补的，真实侧栏“图例与设置”里新增了这一块） | 角色选项与 `ExecutionSettings.tsx` 一致；出厂默认 Worker 为 gpt-6.1-sol / high / 不传 Fast，构思主控为 claude-haiku-5-5 / low（取自 T-112 Resolution）；保存后提示“已保存，下次启动生效”；只改所选角色；没保存就切换角色，改动不生效 | PASS | PASS |

已知坏版本（`mutants.txt`）：把 `docs` 复制到临时目录，每次只注入一处缺陷，八个变体都被对应的检查拒收。

| 变体 | 注入的缺陷 | 被哪些检查拒收 |
| --- | --- | --- |
| answer-keeps-waiting | 作答后状态不回落 | 03：状态回落、通知消失、角标清空等 8 项 |
| dock-follows-notifications | Dock 角标跟着应用内通知开关走（T-110 要求两者分开） | 03：关掉通知不影响 Dock 角标（桌面和手机） |
| flow-more-off-by-one | 超过 5 个才折叠 | 05：超过四个时先显示四个 |
| split-replaces-pane | 分屏把原窗格替换掉 | 04：向右分屏后多一个窗格 |
| execution-save-ignored | 保存会话模型设置时不写入 | 10：保留新保存的 xhigh 等 4 项 |
| reply-ignores-choice | 不管选什么都回第一个选项的决定（即审查 01 的 F1） | 03b：“包含”“保留”“自由答复”三项，桌面和手机共 6 项 |
| notice-replays-after-reenable | 不记“已提醒过”，重新开启就重放（即审查 01 的 F2） | 03b：重新开启后不重放同一问题（桌面和手机） |
| reply-prototype-lookup | 回复查表改回 `question.replies[value] ?? question.freeReply`（即审查 02 的 R02-F1） | 03c：桌面加手机全部 38 项 |

检查本身也拦下过实现里的真实缺陷，都已修复：

- favicon 404 让控制台报错（tracer 阶段）；
- `.tour` 的 `display:grid` 盖过了 `hidden`，禁用 JS 时引导仍然显示；
- Dock 角标被错误地绑在通知开关上；
- 菜单项、通知文字的断言写法问题（属于测试本身，已改）。

另有两处是自查截图时发现的视觉问题，已修复：三格布局下构思主控的提问面板溢出到相邻窗格；通知在每次重绘时重放进场动画。

运行稳定性，照实记录（`flaky-runs.txt`）：机器高负载期间（load average 约 6–8，swap 已用约 5.7 GB），连续三次完整运行的手机一轮出现 CDP 超时和标签页断开，没有一条断言失败。同期用 `data:` 网址的平凡页面在手机模拟下跑 6/6 PASS。负载回落后，手机一轮 120/120 PASS（页面 JS 堆 1–2 MB，DOM 节点数随页面状态变化，没有持续增长），当时的最终完整运行 249/249 PASS；合并 main 并加入场景 10 后为 269/269 PASS。根因没有查清，不归因于页面，也不改判那三次。

审查 01 修复之后又出现了三次同样的停顿，其中一次在 load average 约 1.7 时，所以只用负载解释站不住。排查经过：

- 关掉桌面一轮的标签页、把新标签页置前之后，仍然失败；
- 停住时发 `Debugger.pause`，8 秒内没有暂停，说明渲染进程当时没有在执行 JS，不是页面脚本死循环；
- 手机一轮单独跑一直通过（140/140，JS 堆 1–2 MB，监听器数稳定）。

于是把驱动改成每个视口新起一个 Chrome 进程。之后连续三次完整运行都是 289/289 PASS（load average 约 1.6–2.4）。根因仍未查明；那段时间负载也较低，不能完全排除负载的影响。全部失败记录原样留在 `flaky-runs.txt`。

审查 02 修复之后（新增场景 03c，手机一轮在同一标签页里多了六次加载和输入），完整运行变成每次都在同一处停住：手机 03c 第六次输入时 `Input.insertText` 超时，之后的手机场景全部 CDP 超时。本次提交的 `browser-run.txt` 就是这样一次运行：252/259，失败的 7 项都是手机一轮的“运行”超时，没有断言失败；桌面一轮全部 PASS。负载很低时也会发生（load average 约 1.4），没有找到 Chrome 的崩溃报告，也没有内存压力。在本地另试过两种驱动改法：每个场景新开标签页，以及加上 Puppeteer 默认的自动化启动参数。两种都没有解决，Chrome 进程在手机 03c 之后不再监听调试端口。按执行主控 #68，这些改法都已撤回。

根因排查（执行主控 #69 要求判断是页面卡死还是测试方法问题）。每一轮都是：加载页面，聚焦 T-14 的答复框，输入 `toString`，按需发送，手机视口，同一 Chrome 进程：

| 循环 | 结果 |
| --- | --- |
| 平凡的 `data:` 页面，轻点输入框后输入 | 12/12 |
| 本页，轻点 agent、轻点输入框、输入，不发送 | 12/12 |
| 本页，轻点 agent、轻点输入框、输入、轻点发送（发送会重绘并移除这个已聚焦的输入框） | 第 12 轮停住 |
| 本页，全部改为鼠标点击 | 16/16 |
| 本页，鼠标点击聚焦输入框，轻点发送 | 16/16 |

结论：停顿要满足两个条件，用触摸模拟的轻点聚焦文本输入框，随后重绘把这个输入框移除，并且在同一个浏览器进程里累计约 11 次。停住时 `Debugger.pause` 停不下来，说明页面 JS 没有在运行；页面 JS 堆保持 1–2 MB，监听器数稳定。所以这不是页面脚本死循环，而是无头 Chrome 触摸模拟的问题，属于测试问题。审查 02 的 R02B 用鼠标点击聚焦输入框，所以没有遇到。只把输入框改成鼠标聚焦不够：04 里页面在轻点之后自己聚焦重命名框，照样停住。

处理：`check_demo.mjs` 改为每个场景新起一个 Chrome 进程，场景之间不共用浏览器。测试里仍然用真实的触摸轻点，超时没有加长。场景自己停住时照常报 FAIL，只是不再连累后面的场景。改动后连续两次完整运行都是 327/327 PASS，八个变体照样全部被拒。没有在真机上验证真实手机是否受影响；目前也没有证据表明真机上会出现。

没有验证的：真实手机（iOS Safari、Android Chrome）和真实触控板手势，只用了 Chrome 的移动设备模拟；Safari 和 Firefox；读屏软件的实际朗读。

## 链接检查

`links.txt`：14 项 PASS，7 项 FAIL。

- 内部：11 个锚点、4 个资源文件都存在。
- 第三方外链 `https://github.com/Emanuele-web04/synara`：200。
- 指向 `https://github.com/a1024053774/Enchanted/...` 的 7 个链接（Releases 两处、仓库首页、`intent.md`、`workbench/README.md`、`LICENSE`、`workbench/LICENSE.synara`）现在都是 404：仓库还叫 a2a，而且是 private。已核对其中 4 个文件在 `exec/t113` 的 HEAD 里和远端 `a1024053774/a2a` 的 main 上都存在（`git cat-file -e HEAD:<路径>`、`gh api repos/a1024053774/a2a/contents/<路径>?ref=main`）。Releases 页要等 T-114 发布后才有内容。处理见 issue `20261020T173836Z-worker:s18-t113-issue-001`。

## 检索：凭据、本机路径、邮箱

`scan.txt`：对 `docs/` 和本目录检索四类模式，全部没有命中（grep exit 1）。

- 凭据模式：GitHub token、`sk-` 或 `sk-ant-` 密钥、AWS key、私钥头、Slack token、Bearer、带值的 `api_key`/`secret`/`password`/`token`；
- 本机用户目录和卷路径：macOS 与 Linux 的用户主目录前缀、外接卷前缀、Windows 用户目录（正则见 `scan.sh`）；
- 邮箱地址；
- 真实会话标识：32 位十六进制的 launch 号、UUID。

反例：临时放一个金丝雀文件 `docs/scan-canary.txt`，四类各写一个（运行时拼出来的）样本，四类全部命中，随后删除。

```
HIT   凭据模式
HIT   本机用户目录与卷路径
HIT   邮箱地址
HIT   真实会话与启动记录标识
```

演示数据全部虚构：项目 inkwell、tidepool、ledger-cli，路径用 `~/work/...`，launch 号是 4 位短号。CLI 版本号 `2.1.302 (Claude Code)`、`codex-cli 0.163.0` 是公开版本号，取自 T-091、T-108 的记录。

检查过程中，一次崩溃的栈信息把本机路径写进了 `browser-run.txt`，是检索发现的；驱动随后改成在明细里把脚本目录换成 `./`，并重新生成了这个文件。

## 内容出处对照

页面上的每个功能点都能对应到真实软件或已合入的 ticket。“未做”的条目在页面上有标签。T-112 合入后，原来标“开发中”的那一条已移到“现在能用的”。

### 产品定位和机制

| 页面内容 | 出处 |
| --- | --- |
| Enchanted 是产品名，a2a 是它的编排内核 | T-113、T-114 用户选项“Enchanted,a2a 是其编排内核” |
| 只支持 macOS，CLI 只支持 Claude Code 与 Codex，需要本机已装并登录官方 CLI | `README.md`“当前状态”“环境与安装依赖”；`intent.md`“方案” |
| 关掉窗口，agent 继续跑 | `README.md` 第一段；`CONTEXT.md`“编排后台” |
| 模型自报完成不代替验收 | `README.md` 第二段；`CONTEXT.md`“Submit”“Acceptance gate” |
| 规矩写在提示词里，长对话容易丢 | `intent.md`“要解决的问题”最后一条 |
| 门禁五阶段：认领与实现、交付、机械检查、独立审查、集成 | `workbench/src/flowStages.ts`；`workbench/README.md` 第一段 |
| 任务卡字段：目标、非目标、修改边界、完成条件、验收文件 | `CONTEXT.md`“任务卡”“验收文件”；T-080 |
| 旧 attempt 的交付拒收 | `CONTEXT.md`“Claim”“Stale/unverified result”；AGENTS.md“证据和交付” |
| 检查串：身份与版本、路径、验收文件、完成条件、红态、规则式检查、尾注 | AGENTS.md 第三阶段“门禁不能省”；T-070 |
| 打回写回原 worker，次数有上限 | T-080 Resolution（写回原 worker，计入 3 次上限）；T-077（重新验收上限） |
| 审查每次新开，在一次性副本里、断网，要查完成条件并做变异检查 | T-082 Resolution；AGENTS.md“审查是为每次交付新开的只读会话” |
| 集成到工作分支，不 push | AGENTS.md“全过才集成到项目工作分支，不 push” |
| 提示词管判断，脚本管事实，不做策略引擎 | AGENTS.md、`intent.md`“方案”；T-070 |
| 门禁不是安全沙箱 | `README.md` 第二段最后一句 |
| 两层主控与各角色的职责 | `CONTEXT.md` 前七条；AGENTS.md“构思主控与执行主控” |
| 主控发的提示词不算用户输入；worker 窗格里打字记为人工介入 | `CONTEXT.md`“用户输入”“人工介入”；`renderer.tsx` 的窗格底栏文案 |

### 现在能用的

| 页面内容 | 出处 |
| --- | --- |
| 原生 CLI 跑在交互终端，由常驻后台托管 | T-075、T-091（已关闭）；`intent.md` |
| 侧栏项目目录，分支和领先、落后提交数 | T-107 已合入部分（d28afcb88；该票仍 open，只因缺口另开了票）；`renderer.tsx` 的 `project-git` |
| agent 层级树、七种状态、折叠汇总、识别不到显示“未知” | T-107 已合入部分、T-109 Resolution；`sidebar.ts` 的 `stateLabels`、`aggregate` |
| zsh 窗格、分屏、放大、重命名、关闭、转发右键、布局恢复 | T-104、T-105 Resolution；`renderer.tsx` 窗格菜单 |
| 界面里作答原生提问；多选题和无法核实的提问回原终端答 | T-108 Resolution；`QuestionsPanel.tsx`（`supported` 条件和“请在原生窗格作答”） |
| 应用内通知、后台时的 Dock 角标、两个开关、不调用系统通知 | T-110 Resolution；`AppNotifications.tsx` |
| 流程页 | T-111 Resolution；`FlowPage.tsx` |
| 界面新建项目与任务（简化表单） | T-106 Resolution（裁定 B） |
| 退出应用不结束会话，重开时恢复窗格和布局 | T-096 Resolution；`workbench/README.md`“退出应用只断开视图，保留打开集” |
| 打包成可双击的 macOS 应用 | T-102 Resolution |
| 模型、思考强度和 Fast 按角色在设置里改，下次启动生效；主控派发时可覆盖；取值由 CLI 判断，a2a 记录完整启动参数 | T-112 Resolution（777db09a1 合入，票已关闭）；`workbench/app/ExecutionSettings.tsx`；AGENTS.md（13b983030）“模型与思考强度不写死” |
| 任务卡由命令生成和校验 | `CONTEXT.md`“任务卡”；T-106 的 `card_template`、`card_validate` |
| 验收文件受保护 | T-080 Resolution |
| worktree 命名、清理、冲突写回 worker | T-077 Resolution；`intent.md`“并行 worktree” |
| 提交尾注，并与启动记录核对 | `CONTEXT.md`“提交尾注”；T-073、T-084 |
| 验收打分 | `CONTEXT.md`“验收打分”；T-073；`scripts/score` |

### 即将、已知限制、路线图

| 页面内容 | 标注 | 出处 |
| --- | --- | --- |
| arm64 构建、ad-hoc 签名、没有公证、首次打开要右键打开或解除隔离 | 限制 | T-102 Resolution；T-114 第 3 步 |
| 作者本人的日常派发还没切到工作台；切换条件见 `intent.md` | 限制 | AGENTS.md“切换”；`intent.md`“期望结果：切换”；`README.md` |
| 后台重启后，正常登录的主控不自动续接，worker 窗格不恢复执行 | 限制 | `README.md` 最后一段；`workbench/README.md`；T-096 |
| 没有可靠性、吞吐、成本的对照数据 | 限制 | AGENTS.md“首轮运行是探索性基线”；T-113“不做” |
| 不写 `~/.claude`、`~/.codex`，权限经启动参数传入 | 说明 | AGENTS.md“权限只在工作台内”；`README.md` |
| 复盘 | 未做 | `CONTEXT.md`“复盘”；T-072 D29 |
| 四个指标视图 | 未做 | T-072 D30（模型使用分类、一次到位率与打回原因、注意力消耗、打分汇总） |
| 新建任务时由 agent 补全任务卡 | 未做 | T-106 Resolution“未做：交给 agent 补全任务卡” |
| 旧 Enchanted 的四项：看清加载的指令和 Skill、找出重复问题、带原文引用的建议（只预览导出）、秘密清洗与出站边界 | 未做 | 本机旧 Enchanted 仓库的 `intent.md`“目标”和“R6 首个可验证闭环”（只读查阅）；T-114 用户选项“规划成我们这个 a2a 仓库的未来 feature”；AGENTS.md（13b983030）“旧 Enchanted 的功能只作为路线图里的未来 feature，在本仓库规划” |
| GPL-3.0；Synara MIT 声明 | 说明 | 仓库 `LICENSE`、`workbench/LICENSE.synara`；AGENTS.md“项目开源” |

## 视觉取材

演示窗口和真实工作台同族：颜色、字号、间距、圆角、状态色和图标都取自 `workbench/app/style.css`、`flow.css`、`questions.css`、`notifications.css`，没有另起一套。底色 `#111111`，文字 `#fcfcfc`，强调色 `#0169cc`，边线 `rgba(252,252,252,.12)`，圆角 10px 和 6px；运行中 `#6cb6ff`，等待 `#e6b450`，流程当前阶段 `#79b9f6`，打回线 `#b99663`；胶囊色板与 `FlowPage.tsx` 相同。所有文案照真实界面原文，只有窗口标题写“（演示）”，连接状态写“演示数据 · 未连接后台”。

演示里固定的位置改成了相对演示窗口定位。窗口外框（红黄绿三个按钮和标题栏）真实应用里由系统绘制，演示里补画了一个，并在标题栏显示 Dock 角标的数字。

页面本身用同一组角色色。浅色是补出来的一组同角色取值；工作台目前只有深色，所以演示窗口不随页面切到浅色，页面上写明了这一点。视觉记忆点是首屏那条门禁轨道：画法和流程页一样，圆点、细线加 `›››`。

和真实工作台不同、需要说明的地方：

- 演示的新建终端、分屏只开普通 zsh 窗格；真实应用里，“新建项目目录”“新建任务”会打开系统对话框和表单，演示只显示一行说明；
- 点击没有打开窗格的 agent 时，演示按“向下分屏”把它的窗格加进来。真实应用由后台的 `selectAgent` 决定窗格位置，具体位置没有逐一核对。
- 标题栏里的 Dock 角标数字是“应用在后台时的待答数量”的示意。真实应用在窗口位于前台时把角标设为零（`workbench/app/main.ts:40–46`），演示不模拟前后台切换；页面的演示说明里也写明了这一点（审查 01 的 F3）。
- 作答以后，演示用 900 ms 的定时器模拟原生确认；真实应用要等原生 CLI 确认。终端里追加的说明按所选的预设选项给出，自由答复只确认收到原文。

## 审查 02 的修复

| 发现 | 修复 | 证据 |
| --- | --- | --- |
| R02-F1 / P2：自由答复是 `constructor`、`__proto__`、`toString` 时取到原型成员，`reply.map` 抛 TypeError，画面停在发送中 | `demo.js`：用 `Object.hasOwn(question.replies, value)` 判断是否命中预设选项，其余文本一律走 `freeReply`；没有加 try/catch | 场景 03c；变体 reply-prototype-lookup 被拒；`red-03c-8341208d7.txt`：`8341208d7` 上 0/38，控制台检查记下 `TypeError: reply.map is not a function` |

审查 02 的静态逻辑探针从 `REVIEW-OUTSIDE-02.sh` 原样抽出运行（脚本固定了候选号 `8341208d7`，不能直接用于新提交）：sentinel 模式下，`8341208d7` 上六项“自由答复原型同名”全部 FAIL（TypeError），修复后 6/6 PASS；普通模式两边都是 10 项 PASS。该脚本的定向变异“固定首选回复”的锚点是 `question.replies[value] ?? question.freeReply;`，修复后这段文本已不存在，重新冻结时需要把锚点改成 `Object.hasOwn(question.replies, value) ? question.replies[value] : question.freeReply;`。`mutants.sh` 里本票的同一变体也因此改了锚点，并改成锚点找不到时报 RUN ERROR，不再在未变异的副本上误跑（之前一次运行因此把 reply-ignores-choice 误报成 NOT REJECTED）。

## 审查 01 的修复

| 发现 | 修复 | 证据 |
| --- | --- | --- |
| F1 / P2：作答后终端宣称的决定与所选相反 | `demo.js` 的 `question.reply` 改为按选项给出的 `replies`；自由答复用 `freeReply`，只确认收到原文 | 场景 03b；变体 reply-ignores-choice 被拒 |
| F2 / P2：关闭再开启通知会重放同一问题 | 按 `notificationCenter.ts` 的 observe：按问题记 `noticeSeen`，关闭时清空 `noticeActive`；Dock 待答数单独按等待中的问题计 | 场景 03b；变体 notice-replays-after-reenable 被拒 |
| F3 / P3：Dock 演示没有说明前后台语义 | 页面演示说明和上面的简化说明里写明 | 页面文字；本文 |

审查脚本 `REVIEW-OUTSIDE-01.sh` 把候选号固定为 `28b2ab19b`，候选有任何改动时都会以 INCOMPLETE 退出（这是审查者的设计，本票没有改它）。所以我把脚本里的静态探针和浏览器场景原样抽出来单独运行，抽取方式是：取 `probe.write_text(r'''` 与 `extra.write_text(r'''` 到对应 `'''` 之间的文本，不改一个字节。

- 静态探针：在 `28b2ab19b` 的 `demo.js` 上 2 PASS、3 FAIL（与审查记录相同）；在修复后的 `demo.js` 上 5/5 PASS。
- 浏览器场景 R01（桌面）：修复后 6/6 PASS。
- 审查脚本的定向变异 more-count-wrong（`list.length - 4` 改成 `- 3`）：被场景 05 的“超过四个时先显示四个”拒绝，桌面和手机都是。
- 本票场景 03b 在 `28b2ab19b` 的站点上取得红态：8 项 FAIL，每个视口 4 项，分别对应 F1 的三种答法和 F2，原文见 `red-03b-28b2ab19b.txt`。

要正式跑审查脚本，需要审查者把脚本里固定的候选号更新为新的冻结候选。

## 过程

两次合并 main 之后，核对了页面里所有随 main 变化的内容：T-112 从“即将”移到“现在能用的”，演示侧栏补上真实应用新增的“会话模型”设置；AGENTS.md 的新文字与页面一致：路线图把旧 Enchanted 的功能写成本仓库以后的功能；改名完成前，演示窗口仍显示“a2a 工作台”。合并带进来的其他改动有 T-115（open 的缺陷票），不涉及页面上的功能点。


先按 tracer bullet 打通一条：首页骨架加“侧栏切换项目”，在真实 Chrome 里桌面、手机各点一遍（17/18，唯一的 FAIL 是控制台抓到的 favicon 404）。之后才扩展到全部内容和交互。

临时文件都在 `/private/tmp` 下：`t113-shots`、`t113-http.log`，以及各次运行的 Chrome 临时 profile。验证结束后已删除，静态服务器也已停止。
