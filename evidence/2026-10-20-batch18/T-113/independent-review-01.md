# T-113 第一轮独立审查

STATUS: NO_GO

TARGET: `28b2ab19bcd2fe500125fdb9be1540e07f8ad0fc`，分支 `exec/t113`，2026-10-20。

本轮只审产品页与其验收证据，没有修改候选、调用模型、启动子 agent、提交、发布或写全局配置。开始时工作区干净；写入只有本报告和 `REVIEW-OUTSIDE-01.sh`。阅读了 reviewer 角色卡、AGENTS、T-113、T-114、RESULTS、地图、术语表和 intent。使用 project-map、behavioral-acceptance-review、frontend-production 和 document-writing 的相关检查方法。

目标是核实页面事实、真实工作台同族行为、隐私边界、静态发布条件和完成条件的拒错能力；不重新验收整个工作台，不执行 T-114 发布。Ubiquitous language 沿用项目的状态与阶段名称。Tracer bullet 的历史仅作过程记录，不替当前候选背书；Deep modules 本轮没有实现或抽象调整。

结论：有两项 P2 演示行为偏差，需修复。独立补充逻辑探针已复现；真实浏览器部分按派发写成沙箱外脚本，本会话没有启动 Chrome，不能把脚本存在写成验证通过。既有功能出处、资源依赖和静态发布结构在已查范围内没有阻断问题。外链与地图仍有明确的后续核对项。

## 确认的缺陷

### F1 / P2：选择另一选项后，终端仍宣称采取原来的决定

- 位置：`docs/assets/demo.js:70`、`:73`、`:455`；`scenarios.mjs:79`～`:92`。
- 复现：初始提问选“包含”并发送；或点 T-14 的 worker，选“保留一个版本”并发送。
- 实际：第一题先写入 `› 包含`，随后追加“默认不包含已归档条目”；第二题先写入保留答案，随后追加“按答复继续：删除 0.8 迁移代码”。`question.reply` 固定，不随作答变化。
- 预期：预设演示可以不调用模型，但可点击的选项和随后宣称的决定必须一致；自定义答复也不能被解释成固定的相反决定。真实 `QuestionsPanel.tsx` 将用户所选答案传给 send，没有用固定答案覆盖用户选择。
- 影响：演示在最主要的作答路径上表达与用户选择相反的行为。现有检查只选择“不包含”，并仅检查写回行包含它，没有检查后续说明是否矛盾。
- 证据：本轮执行 `sh evidence/2026-10-20-batch18/T-113/REVIEW-OUTSIDE-01.sh --static-only`，默认分支 PASS，两项相反选择断言 FAIL。该探针执行当前原始 JS 的事件处理与定时回调，用最小 DOM 替身收集渲染文本；它证明确定性分支错误，不证明浏览器呈现。
- 最小修正：按预设选项选择对应回复；或统一只确认收到原文，避免替任意自由答复作固定解释。补非默认选项与自由答复检查。沙箱外脚本已有两题的浏览器复现断言。

### F2 / P2：通知开关重新启用会重放同一问题

- 位置：`docs/assets/demo.js:140`、`:565`；真实规则在 `workbench/app/notificationCenter.ts:29`～`:41`，T-110 Resolution 明确“同一问题只提醒一次”。
- 复现：尚未作答时展开“图例与设置”，关闭“等待用户回答时提醒”，再开启。
- 实际：`notices()` 只根据开关和当前等待状态筛选；开启后同一条通知立即重新出现。
- 预期：真实 `NotificationCenter` 在禁用时清空 active，并保留 seen；再次开启不重放已经观察过的问题。侧栏等待状态与 Dock 待答数量可以继续存在。
- 影响：演示的应用内通知语义与已合入软件不同；RESULTS 的简化说明没有披露这项差异。原场景 03 只关开关，没有重新打开。
- 证据：同一 `--static-only` 探针中“关闭通知后清空”PASS，“重新启用不得重放同一问题”FAIL。沙箱外脚本另有真实点击的复现断言。
- 最小修正：按问题记录通知是否已经展示，保持开关和待答计数分离，并增加关闭再开启的检查。

### F3 / P3：Dock 演示缺少前后台语义说明

`docs/assets/demo.js:394`～`:396` 只按待答数与开关显示窗口内的数字；真实 `workbench/app/main.ts:40`～`:46` 在有聚焦窗口时强制清零。RESULTS 已说明角标画在标题栏，但没有说明未模拟前台清零。页面的功能文字“应用在后台时显示”是正确的；建议在演示或简化说明中明确这是后台待答数量的示意，不把当前数字当作前后台行为验证。此项不单独作为阻断理由。

## 内容出处核对

RESULTS 对照表共 42 条。本轮独立核对下列 31 条，超过一半；核对对象是票的 Resolution 或当前源码/规范正文，不只读作者的表格。此处 PASS 表示页面陈述有出处，不表示重新运行了这些票的产品验收。

| 条目 | 独立核对来源 | 结果 |
| --- | --- | --- |
| 产品名与 a2a 编排内核定位 | T-113、T-114 用户逐字选项；AGENTS 改名决定 | PASS |
| macOS、两家 CLI、本机安装登录 | README 当前状态与环境；intent 方案 | PASS |
| 关窗口后后台继续运行 | README 首段；CONTEXT 编排后台 | PASS |
| 自报完成不替代验收 | README 第二段；CONTEXT Submit/Acceptance | PASS |
| 长对话易丢提示词规程 | intent 要解决的问题 | PASS |
| 门禁五阶段 | `workbench/src/flowStages.ts` 全文 | PASS |
| 任务卡与验收文件 | CONTEXT；T-080 Resolution | PASS |
| 拒收旧 attempt | CONTEXT Claim/Stale；AGENTS 证据和交付 | PASS |
| 机械检查串 | AGENTS 第三阶段；T-080 Resolution | PASS |
| 打回原 worker 与三次上限 | T-080 Resolution，明确计入 3 次上限 | PASS |
| 新审查会话、候选副本、断网、变异要求 | T-082 Resolution；AGENTS | PASS |
| 集成工作分支而不 push | AGENTS 第三阶段 | PASS |
| 提示词管判断、脚本管事实 | intent 方案；AGENTS | PASS |
| 门禁不是安全沙箱 | README 第二段；页面同时保留此限制 | PASS |
| 两层主控与角色分工 | CONTEXT 前部；AGENTS 主控章节 | PASS |
| 用户输入与人工介入 | CONTEXT；`renderer.tsx:311`～`:312` | PASS |
| 原生 CLI 与常驻后台 | intent 方案；README 首段 | PASS |
| 项目分支与领先落后数 | `sidebar.ts` 的 gitFacts；renderer 项目行 | PASS |
| 层级树、七状态和折叠汇总 | T-109 Resolution；`sidebar.ts` stateLabels/aggregate；renderer renderAgents | PASS |
| 普通终端、分屏、改名、恢复等 | T-104、T-105 Resolution；renderer 菜单 | PASS |
| 原生提问与不支持情形回原终端 | T-108 Resolution；QuestionsPanel supported/writable | PASS |
| 通知与独立 Dock 开关、不用系统通知 | T-110 Resolution；AppNotifications/NotificationCenter/main | 功能出处 PASS；演示有 F2/F3 |
| 流程页 | T-111 Resolution；FlowPage 全文 | PASS |
| 新建项目/任务用简化表单 | T-106 Resolution 裁定 B | PASS；演示简化已披露 |
| 退出不结束会话，恢复布局 | T-096、T-105 Resolution；workbench README 打开集 | PASS；不能推导后台重启后自动续接 |
| 可双击 macOS 包 | T-102 Resolution | PASS；未公证限制已写 |
| 按角色修改模型/effort/Fast，下次启动与覆盖 | T-112 Resolution；ExecutionSettings/executionSettings 全文 | PASS |
| 任务卡命令生成和校验 | T-106 Resolution 的 card_template/card_validate | PASS |
| 验收文件受保护 | T-080 Resolution | PASS |
| worktree 清理和冲突交回 worker | T-077 Resolution；intent 并行 worktree | PASS |
| 后台重启后的正常登录/worker 恢复限制 | README 当前状态；workbench README；T-096 Resolution | PASS |

其余记录类功能没有全部重新追到执行代码；不将抽查扩大为全产品重验。页面 7 项路线图均带“未做”，没有把旧 Enchanted 的能力列成已有。旧原型四项具体细节本轮没有重读冻结目录，只核对其未来功能定位与用户决定一致。全页未发现可靠性、吞吐、成本收益承诺或虚构测量结果；初版、日常尚未切换、恢复和签名限制均明确保留。

## 演示与真实工作台的对照

- 状态：七个名称、图标与 `sidebar.ts` / renderer 相同；aggregate 的优先级逐分支相同：等用户、等主控、运行、空或含未知、未恢复、空闲、已结束。unknown 不被当作忙/空闲。
- 层级：renderer 与演示都按父子关系分 controller 与任务组，并显示后代汇总。演示固定夹具不证明真实父 launch 采集，但本票没有声称连接后台。
- 流程：FlowPage 的五阶段、230px 列、胶囊颜色、超过四个折叠、已集成默认折叠、checks/review 分来源折回线与演示一致。`flow.css` 和演示 CSS 的线宽、颜色、间距相符。
- 提问：字段、按钮、待确认文字与 QuestionsPanel 相符。真实作答后状态要等原生确认；演示用 900ms 定时器模拟成功，不能据此证明原生写回，页面已说明纯前端预设。两题固定回复错误见 F1。
- 通知：三行文字、点击定位与两开关取自 AppNotifications；重新启用的生命周期不同，见 F2。
- 视觉：核对底色 `#111111`、文字 `#fcfcfc`、强调 `#0169cc`、边线、10/6px 圆角、等待/运行色和流程胶囊色；未见另起界面体系。未对当前候选做实际渲染视觉确认。
- 已披露简化：窗口框由网页绘制；固定定位改窗口内定位；创建项目/任务只给说明；缺失 agent 窗格按向下分屏加入；浅色只作用产品页。这些未被当作真实系统能力。Dock 的额外简化需补说明。

## 安全、隐私、协议与 Pages

独立检索使用 `git grep`，不依赖 rg；扫描目标为全部受控 `docs/`，包含 HTML、JS、CSS。实际命令的结构为 `git grep -n -E '<模式>' -- docs`，四次均 exit 1、0 行命中：

| 类别 | 实际模式范围 | 结果 |
| --- | --- | --- |
| 凭据 | GitHub classic/PAT、sk 系列、AWS AKIA、私钥头、Slack、Bearer；带值赋值另由作者 scan.sh 覆盖 | PASS：0 命中 |
| 个人绝对路径 | macOS/Linux 用户主目录、卷目录、Windows Users 路径 | PASS：0 命中 |
| 邮箱 | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` | PASS：0 命中 |
| 真实标识 | `launch-` 加 32 位十六进制，及 UUID 格式 | PASS：0 命中 |

可复现的独立检索命令如下；路径模式分段引号拼接，避免把扫描规则文本误当作站点泄漏：

```sh
git grep -n -E '(gh[pousr]_[A-Za-z0-9]{20,}|github_''pat_|sk-(ant-)?[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|xox[abpr]-|[Bb]earer [A-Za-z0-9._-]{16,})' -- docs
git grep -n -E '(/''Users/|/''home/|/''Volumes/|[A-Za-z]:[\\]+Users[\\])' -- docs
git grep -n -E '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' -- docs
git grep -n -E '(launch-[0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})' -- docs
```

补跑作者的 `sh evidence/2026-10-20-batch18/T-113/scan.sh` 也为四类 CLEAN，写本轮两个文件前和首稿完成后均为 CLEAN。之后补入完整扫描表达式时，证据扫描曾将报告中的表达式本身误判为凭据命中（只命中报告规则文本，站点未命中）；改为列出上面的独立模式并引用现有 scan.sh 的赋值规则后，再次检查 CLEAN。该过程不涉及候选或真实秘密的修改。人工阅读演示正文均为虚构项目与预设终端内容；短 launch 标识不是完整真实会话号。模式扫描不能单独证明任意文本绝不曾出现在真实会话里，本轮未接触用户原始转录。

资源检索命令：`git grep -n -E '(fetch[[:space:]]*\(|XMLHttpRequest|WebSocket|sendBeacon|@import|url\(|https?://|src=|href=)' -- docs`。命中只有本地样式/脚本、页内锚点、导航外链和内联 SVG favicon 的 XML 命名空间。没有运行时外部库、字体、CSS URL、模型请求或统计上报，因此没有需要固定版本的 CDN 依赖。`.nojekyll` 已受控，四项静态资源均为相对路径，没有构建步骤或站点根路径假设。

`python3 evidence/2026-10-20-batch18/T-113/check_links.py docs --offline`：13 项文件/锚点 PASS，外链跳过，失败 0。7 个指向未来 Enchanted 仓库的外链条目（含重复 Release 链接）依派发移交 T-114 第⑥步，不因离线检查而称通过；Synara 外链本轮也未重新请求。线上 Pages、Release 与下载都不在本轮执行范围。

页面有 GPL-3.0 说明和 Synara 两位权利人的 MIT 版权声明，并链接仓库完整许可；独立读了根 LICENSE 与 workbench/LICENSE.synara，名称和年份一致。演示 CSS 保留来源注释。

## 完成条件与变异检查

作者驱动通过 Chrome CDP 派发真实鼠标、触摸和按键，不只是调用点击处理函数；控制台监控、禁用 JS、主题与几何检查都有实质断言。审查了完整 scenarios 和驱动：状态规则、菜单顺序、四个会话的折叠阈值、通知开关分离、角色设置默认值均能在真实源码找到独立依据。固定项目标题和会话数量属于演示夹具断言，不能独立证明产品能力。

已有 `mutants.txt` 记录五项被拒：作答仍等待、Dock 错绑通知、四个阈值改五个、分屏替换原窗格、设置保存失效；都有目标业务断言失败，分屏变体除运行异常外还有“多一个窗格”失败，并非只用崩溃当拒收。主控消息所述旧候选 249/249 是外部提供的历史证据；作者当前记录是 269/269，本轮没有独立重跑，不升级其证据等级。

缺口：默认选项的顺向检查漏掉 F1，关闭开关的单向检查漏掉 F2。由用户选择和真实 NotificationCenter 规则导出的独立输入已经写入沙箱外脚本；两个坏行为在补充逻辑探针里均被拒。

脚本全量模式还在新的临时副本中构造以下两项变异，使用当前作者驱动经真实 Chrome 检验：

| 变异 | 改动 | 精确拒收要求 | 本轮状态 |
| --- | --- | --- | --- |
| answer-keeps-waiting | `agent.state = 'running'` 改为不变 | 场景 03 的“构思主控回落为运行中”必须 FAIL | INCOMPLETE：已写脚本，未实跑 |
| more-count-wrong | 显示数量从 `list.length - 4` 改为 `list.length - 3`，实际展示仍四个 | 场景 05 的“超过四个时先显示四个”必须 FAIL | INCOMPLETE：已写脚本，未实跑 |

第二项与作者已有的阈值变异不同，专查“还有 N 个”数字本身。拒收需 rc 1 且有指定断言 FAIL；启动错误或超时不算变异被抓。副本只在新建临时目录内；服务器用 start_new_session，退出时回收。Chrome 沿用作者隔离 profile 与 finally 清理方式，不建符号链接、不写截图。完整复现命令：

```sh
sh evidence/2026-10-20-batch18/T-113/REVIEW-OUTSIDE-01.sh
```

脚本固定核对完整候选号，运行现有桌面/390px 手机模拟全量检查，再运行独立输入与两项定向变异。当前候选预期独立输入部分失败；不把此预期当作实际浏览器结果。shell 语法和 Python 3.9 AST 兼容性已检查；`--static-only` 实跑返回 1：2 PASS、3 FAIL。临时目录已删除，余留 0。

## 未完成与范围外上报

- INCOMPLETE：当前候选的真实 Chrome 渲染、控制台、手机横向滚动、深浅色、Tab 顺序/焦点、键盘完整操作、禁用 JS，以及本轮两项真实浏览器变异尚未独立实跑。静态上有 hidden、无 JS 正文、焦点样式及语义按钮，但它们不能代替浏览器验证。手机模拟不等于真机验证。
- INCOMPLETE：地图开始和结束均 exit 1，8 个问题、0 stale；`git ls-files -t` 确认相关 findings 与 grilling 文件标记 S，符合稀疏检出缺失。未修地图或扩展检出；合入前/后需主控在完整 main 上验证 0 问题。
- INCOMPLETE：T-114 发布后外链复验和线上演示检查。
- 范围外发现，交主控处置：根 README“环境与安装依赖/构建与运行”仍要求外置盘，并将构建输出写到外置盘；AGENTS 已明确 2026-10-19 起允许内置盘。workbench README 仍有 T-111“尚未取得沙箱外结果”的旧说法，而其已关闭票 Resolution 已记录沙箱外 PASS。这些不是本页新增，本轮不改，也不使用问题面板；请在文档维护或 T-114 README 更新中核对。

本轮建议先修复 F1、F2，补 F3 的简化说明，再由执行主控运行沙箱外脚本并保留文字结果。真实浏览器与变异缺口关闭前，不能据此报告本票验收 PASS。

T-113 REVIEW NO_GO
