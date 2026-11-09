# T-249-1 第五次派发：恢复范围自查与证据边界

本文件是本次 worker 的实现者自查记录，不是门禁独立审查。按任务卡复用相同代码的旧检查，不另开审查会话，也不修改根目录冻结的 `REVIEW.md`。

## design-integrity-review 实现者自查

STATUS: PASS

SUMMARY: 本轮恢复范围内未确认新的结构缺陷；产品源码和开发测试与旧候选完全相同。

TARGET: `6e6af856f91b617ac7e8827f363947678ab17efb`，基线 `b7cce248c5ed85dd9342ade10886287365273863`；来源候选 `9f96a9121ba6ed8d77a514a0a78c9341ceaacb86`。

FINDINGS:

- 无本轮新确认的缺陷。读取根目录 `REVIEW.md` 后，对完整恢复差异运行扫描；扫描的 13 项是定位项，不是缺陷数，`acceptance_changes=[]`。命令：`python3 /Users/luckye/.agents/skills/design-integrity-review/scripts/design_integrity.py --cwd . --base b7cce248c5ed85dd9342ade10886287365273863 --format json`，退出 0，仓库根正确，原输出见 [design-scan.json](design-scan.json)。
- 复用旧 [attempt-fence3/RESULTS.md](../attempt-fence3/RESULTS.md) 的源码自查，并读取 Git 中的 `controller/review-01.md` 原文。旧审查的模型不符，不能用作通过结论；其中两条已复现 P2 及未验证限制仍是检查依据。
- 本轮人工核对恢复的调用链：`Workbench → PanelDock → preload → main → gitHost.execFile`；CLI 使用同一 `readGraph`、`gitAction` 和 `commandsFor`。没有第二套 Git 实现。按 **Deep modules** 核对，共用模型承担解析、泳道、校验及命令构造，IPC 只跨越 Electron 边界；本轮没有新增抽象或接口。
- 本轮核对 `fileArgs` 只在 HEAD 查询返回 1 时改用 Git 空树标识；其他错误仍传播。宿主只允许精确的 `hash-object -t tree /dev/null`。`diffArgs` 的根提交、普通提交和未提交三条路径均保留 `:(top,literal)`。详情列表与 diff 共用所读取的基线，并显式补入未跟踪文件；相应真实 Git 检查 22/22。
- 扫描命中的边界与旧代码相同：localStorage 的容错仅影响视图偏好；读取 shell cwd 失败记录日志并使用启动目录；watch/状态增量刷新失败记录日志，保留票要求的 15 秒完整轮询；历史、菜单、详情与写操作错误传给界面或非零 CLI 退出。没有新增自动写重试或静默成功路径。
- 本轮重新阅读敏感脚本的所有权与判红代码：只清理脚本新建的私有临时根；清理未获确认时保留现场；三个变异须命中各自指定业务断言，启动错误不能算红态。5/5 脚本检查为模拟报告和清理夹具的检查，实际打包与进程清理仍待主控实跑。

LIMITATIONS:

- 这是恢复范围实现者自查，未再次做整套源码独立审查。旧证据仅按明确的文件等同性复用；新 attempt 的机械结果已经实际重跑。
- Esc、终端焦点、固定目录、watch 时序、拖宽和菜单交互未在本轮窗口验证；旧审查中的焦点疑点保持未验证，不据猜测改代码。
- 根目录 `REVIEW.md` 的 Verified 和敏感脚本批准由主控及用户处理。

## behavioral-acceptance-review 证据说明

STATUS: INCOMPLETE

SUMMARY: 三条机械条件具备真实 Git 或有界编排证据；整票仍缺真实窗口、指定窗口变异、独立审查和 terra 验收，不能给出整票接受或发布通过结论。

TARGET: `6e6af856f91b617ac7e8827f363947678ab17efb`。

EVIDENCE:

- 独立 oracle：冻结 `acceptance/T-249/check_git_graph.py` 经 CLI 入口调用生产模型/命令，以夹具的 `git rev-list --date-order --parents`、`for-each-ref` 和 `status` 为期望；泳道期望取自需求规则的手推。当前 attempt PASS，程序未改。
- 宿主检查经过生产 `gitHost.ts`、`gitGraphModel.ts` 和真实 Git；单文件 diff 独立使用 Git 的 `--literal-pathspecs` 结果，另查选中文件 sentinel 存在且其他文件 sentinel 不存在。覆盖三种 diff 路径、三个特殊文件名、有／无 HEAD 的混合状态、受管写拒绝和 Git 元数据逐文件内容不变。本轮 22/22。
- 编排检查确认 no-panel 已登记且必跑、三个变异对应的断言分类、启动失败不算红态、DOM 缺失与 CDP 故障不同、清理不越过自有目录；本轮 5/5。模拟结果只证明分类逻辑，不证明 Electron 或面板行为。
- 确认全部 57 个导入文件与来源候选相同，因而旧反例可追溯；本轮未重造变异，也没有把历史红态写成本轮运行结果。

FINDINGS:

- 本轮未复现新的缺陷；待验收限制见下。

COUNTEREXAMPLE:

- 两条 P2 的旧真实 Git 红态原样保留：`../attempt-fence3/host-red.txt` 的 9 个字面路径反例和无 HEAD 文件列表反例，以及 `unborn-diff-red.txt` 的单文件 diff 失败。本轮同一生产实现的修复检查全部通过。
- 旧 `../attempt-fence2/headless-20261108T035950/{parents,order}.txt` 保留父提交颠倒和排序颠倒的业务断言失败；这仅证明无界面检测能力。
- 旧审查 01 记录 managed-write 和 no-dashed-head 变异被宿主检查拒绝；本轮原样保留保护及断言，并重跑相应正例，未再次运行这两个变异。
- no-panel 在旧无界面条件中存活，因此不能由机械 PASS 推导面板存在。当前脚本已必跑真实窗口 no-panel，并要求失败项为“侧边面板存在”；本轮没有运行该窗口反例。`../attempt-fence3/outside-safety-red.txt` 仅是旧编排缺少 no-panel 要求的红态。

LIMITATIONS:

- 按 Agent 产品证据层，本轮冻结 CLI 属于独立进程加真实 Git 的入口证据，宿主检查属于真实本地依赖证据；桌面交互入口证据仍缺失。
- 能力范围：身份／作用域只证明 Git 宿主的受管目录保护；外部副作用只证明夹具分支读回；文件只证明 Git 文件名、状态及 diff。异步 watch、桌面交互和实际打包尚未验证；检索／记忆、模型理解及编排状态机不在本恢复范围内。
- 独立 `gpt-6-astra` xhigh 审查由主控经门禁安排。主控随后运行真实窗口绿态及 no-panel、parents、order 三项指定红态，打包 Enchanted Test，再由 `gpt-6.1-terra` 做 Computer Use 与常规测试；用户须阅读敏感脚本证据并批准后才可集成。

RELEASE: INCOMPLETE
