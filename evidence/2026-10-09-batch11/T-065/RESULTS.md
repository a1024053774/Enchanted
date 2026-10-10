# T-065：短窗口空态输入区

状态：INCOMPLETE（一次独立审查 FAIL；P1 已修复并通过本地验证，按 brief 不自行追审，待执行主控审修复 diff）。ticket 保持 open，待主控关闭。依据 ready_rev 1 与执行主控决定 controller-decision-01.md（a2a `47ce087`）。

开工 fork 基线：`1bcf20720`；局部候选 `95d525c56`；已审冻结候选为 fork `9654e1c63` + a2a `e18fead`。交付修复版为 `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`，修复 diff 见 review-repair.diff.patch，版本与三组运行的逐字源码绑定见 candidate-binding.json。不使用哈希或指纹。Herdr 期按 brief 以 fork/a2a 提交交付，不走门禁 submit，产品测试不调用真实模型。夹具 task/attempt/thread 身份见 fixture-identities.json，不冒称为真实 T-065 受管 attempt。

## 改动

| 文件 | 内容 |
| --- | --- |
| 上游 `ChatView.tsx` 空态布局与控件组装 | 输入区先占空间；次要内容按剩余空间收起；可见横幅完整换行；工具栏换行并保留分支控件的最小内容宽度 |
| a2a `IssuePanel.tsx` | 允许面板收缩，列表继续自身滚动；header/footer 保留 |
| a2a `TaskWindow.tsx` | 会话容器保留至少 192 CSS px，问题面板让出所需空间 |

没有增加依赖、API、异常处理、重试或兼容路径；没有修改其他上游文件。未改工作台数据或构建输出，未重启正式工作台、未 push。

## 视口与收起内容

空间规则基于输入区以外的剩余空态区域：横幅在高度 <380px 或宽度 <480px 时收起；logo 在高度 <240px 时收起；标题在高度 <160px，或宽度 <480px 且高度 <240px 时连同 hero 收起。可见内容都检查完整边界与文字裁切；隐藏内容是该规则的整块收起。

| 窗口 / 缩放 | 实际 CSS 视口 | 打开面板的高度（CSS px） | 打开面板收起 | 无面板收起 | 输入区 |
| --- | --- | --- | --- | --- | --- |
| 1600×1050 / 100% | 1600×1050 | 576 | 横幅、logo | 无 | PASS |
| 1280×900 / 100% | 1280×900 | 540 | 横幅、logo、标题 | 无 | PASS |
| 1280×720 / 100% | 1280×720 | 395.5 | 横幅、logo、标题 | 无 | PASS |
| 1600×1050 / 125% 模拟 | 1280×840 | 504 | 横幅、logo、标题 | 无 | PASS |
| 1280×900 / 125% 模拟 | 1024×720 | 371 | 横幅、logo、标题 | 横幅 | PASS |
| 1280×720 / 125% 模拟 | 1024×576 | 227 | 横幅、logo、标题 | 横幅 | PASS |

表中面板高度在修复版 toolbar-final01-ui / toolbar-many01-ui 中仍成立。最短缩放场景为会话保留 192px，换行后的完整输入区为 168.25px。无面板的数据为真实空问题列表，未用 DOM 隐藏面板。空间充足的无面板场景必须保留横幅、logo、标题，用来拒绝“全部一直隐藏”的错误实现。

## 一次独立审查与修复

审查者 `/root/t065_acceptance` 在 fresh context 只读审查 fork `9654e1c63` + a2a `e18fead`，没有读取 RESULTS、ticket Resolution 或 inbox 正文。原文与请求见 acceptance-review-raw.txt、acceptance-review-request.md。结论为 FAIL：P1，400px 会话列和两个小尺寸缩放时，Select branch 与 Temporary / Worktree 的工具栏按钮相交。

修复仅为 ChatView.tsx 空态工具栏的两个 class 字符串：flex-nowrap 改为 flex-wrap，分支 slot 的 min-w-0 改为 min-w-fit，保留文字并换行，不新增隐藏标签。review-repair.diff.patch 是执行主控需要看的修复 diff。遵守“FAIL 后不自行追审”，没有第二次独立审查，最终状态不写 PASS。

原裁切 flag 把既有底部权限按钮的屏幕阅读器标签也算作裁切。toolbar-diagnostic01.json 证明 Ask for approval 标签为 1×1px、clip-path: inset(50%)；它原本就在 <480px 的 footer 中用图标显示，名称仍可访问，此次生产改动没有修改该设计。测试改为检查实际绘制的文字，并增加工具栏按钮的两两相交面积、按钮在 tray 内的完整边界、可见文字在控件内的边界；不把空 span 当作文字。

最终同一 oracle 的 toolbar-counterfactual02-ui 加载已审冻结版本 9654e1c63，exit 1，只有三条业务失败：400px 窄列、125% 1280×900、125% 1280×720 的 toolbar buttons overlap。原始面积分别含 2664.59375px²、127.5625px²、556.15625px²。修复后的三个矩阵对应面积全为 0，已知坏版本仍被拒绝。

## 证据

- 红态 red01-ui、red02-ui：e94a0efc3 源码、1280×900、3 条待决定问题，exit 1，输入区在首屏外且就地点击命中失败。red01 保留夹具的禁用 provider 提示；red02 与后续候选通过产品按钮关闭该提示。
- green01-ui：局部候选在 125% 模拟中只有 73.4px，输入区失败；原始输出保留。主控批准 IssuePanel/TaskWindow 的空间调整后继续。
- 修复版 toolbar-final01-ui（3 条问题）：13 个几何场景、7 组面板控件检查，exit 0；另检查工具栏文字与按钮相交。
- 修复版 toolbar-no-panel01-ui：12 个几何场景，包含三种原尺寸、三种 125% 模拟、长中文、尺寸往返、400px 窄列，exit 0。
- 修复版 toolbar-many01-ui（15 条问题）：13 个几何场景、7 组面板控件检查，exit 0；最短缩放下的发送按钮、打包按钮与取消按钮另有完整可见截图。
- 三组均检查输入区完整位于首屏、坐标点击及输入成功、landing 未滚动、4 个元素的 6 对相交面积为 0、可见次要内容没有裁切。
- 控件检查将第一条和最后一条问题的标题、回复框与按钮滚动到列表内，核对完整边界和点击命中；实际点击“关闭”展开表单，再点击“取消”收回，不发送答复或处置问题。两份回复草稿还触发打包 footer，检查该 footer 占空间时的控件可达性。列表边缘可出现尚未完整滚动到的内容；各控件均能完整显露，未遮住输入区。
- 相关单元套件 related-tests03：35/35；既有固定浏览器套件 browser-tests03：5 个选中测试通过，208 个按过滤条件未运行；全 workspace typecheck03、lint03、fmt-check03：exit 0。lint 原始输出含 877 warnings、0 errors，不宣称零警告。

失败方式：400px 会话列用于宽度挤压；15 条待决定问题及 601 个 emoji 长正文证明列表自身滚动；英文原文与加长中文均检查几何和裁切；125% 逐个覆盖三种窗口尺寸。没有做启动耗时对照。

green02-ui 因截图标签重复被 O_EXCL 拒绝；no-panel01-ui 将 400px 窄列误判为“空间充足”，产生错误断言。二者输出、截图与相应脚本快照原样保留。纠正场景分类后重新完整运行；没有修改产品来迎合这两个测试错误。

## 局限与收尾

125% 是 Headless Shell 的 device-metrics 模拟（0.8 CSS 视口、DPR 1.25），未证明真实浏览器菜单缩放。后续截图直接经 CDP 保存，PNG 尺寸已核对；green01 的缩放截图仍有旧 viewport 问题，不能用于证明画布尺寸。所有 provider 禁用，正常空态验证关闭禁用提示；不外推到真实模型或其他提示/附件状态。外观由用户判断。

全部本任务隔离服务均按 PID、lstart 和命令核对后停止，见各 *-stop.json。外置盘上的数据库与 profile 原样保留。原始日志/patch 的尾空白和末尾空行不清洗；文档、脚本和产品 diff 另作空白检查。一次独立审查已 FAIL，修复后未再次审查，机械通过不能替代执行主控对修复 diff 的审查。

额外失败记录：toolbar-red01-ui 的初版裁切检查仍含屏幕阅读器标签；toolbar-green01-ui 换行后因此报错。toolbar-counterfactual01-ui 还将空 span 的零尺寸 Range 当成可见文字，同时也取得真实按钮相交。失败、诊断和脚本快照均保留；toolbar-counterfactual02-ui 纠正两类测试误报后只因真实相交失败。文档写入的 Python stdin 编码错误未修改原文件，改用 apply_patch 并回读 UTF-8，诊断见 encoding-edit-failure.txt。
