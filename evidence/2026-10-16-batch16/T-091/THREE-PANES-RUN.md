# T-091 三格候选：主控实跑材料

日期：2026-10-17。状态 **INCOMPLETE，green-02 与回归 -02 待实跑**。green-01 因固定 CLI 2.1.296 已被自动更新删除而在建窗前失败；五类回归 -01 的包装问题及局部真实结果见 RESULTS。旧输出原样保留，不能沿用给新候选。界面方向不变。

重启后接手的交付身份：`launch-71afbd1600cb451a9d9354aa7768e72b`，受管 session `d4277ace-1dde-425b-99b8-8988f1df751f`，原生会话 `01a14a05-4472-70e1-af77-58414340c1ee`。脚本摘要与本次提交使用这些值；旧运行的身份不改写。

## 三格绿态及两个拒绝反例

先核对 [run_three_panes.py](run_three_panes.py) 开头的完整清单，再填本次批准引用。主要预算如下：

| 项目 | 本次预算与操作 |
| --- | --- |
| CLI／后台 | Node 26.5+、生产 daemon；CLI 路径和版本显式从参数传入，本轮为 2.1.302。两个交互主控、三个串行受控 C receiver（外任务、旧 attempt、当前 worker）、真 Codex 0、Electron 43.4.1 一个进程。版本探测最多 5 次尝试：脚本前置 1、两个成功启动各 1、版本不符 1、缺失路径 1；缺失路径不会实际启动 CLI |
| 数量与输出限制 | 同时最多两个主控 CLI、一个受控 receiver、一个 Electron；三个 receiver 串行，先确认前一个退出再启下一个。最多 120 次驱动 RPC、读屏上界 360 次、原始帧 3 张。stdout 达 32 MiB 后不发下一次探测，一份正在接收的回复可跨过此阈值；完整输出写外置盘，终端只打印一行摘要。run.json 记录启动尝试、读屏、截图和 stdout 字节数。真 Codex 新增 0，主控须另核对 Herdr 中现存 Codex 会话总数不超过 3 |
| 旧身份夹具 | 前两个 receiver 各经一次 pane_release 消费原先排队的测试提示，以 bracketed paste＋CR 进入模拟回合；各通过一个真实 hook CLI 子进程发送合成 Stop，确认 idle，再以原 attempt 经门禁 reclaim。两个模拟回合，供应商模型回合 0 |
| 主控首屏 | 只观察原始输出、快照和进程；不聚焦、不输入、不回答信任／主题／登录／权限界面，不放行主控提示 |
| 当前三格 | 每格一次 composition-start、一次 focus-observation IPC，仅登记元数据；六种未知 key 调用均须拒绝；一份错误跨格放行声明须拒绝，不实际放行 |
| worker 输入 | 只聚焦当前受控 worker，一份预先生成的中文 nonce bracketed paste，submit=false，再失焦。UI Enter／Esc／其他控制键 0 |
| 布局与滚动 | 两个主控各滚动自己的终端，不聚焦；1440×900、1200×800、900×650，再回 1440×900，核对三格均可见、终端有高度、绑定和焦点不变 |
| 反例 | 维持前两个主控身份，只替换第三个为错 task launch、同 task 旧 attempt launch，调用同一个生产 run，要求在建窗／发凭据前拒绝。不把历史只读格算当前第三格 |
| 版本反例 | 在两个主控启动前，经真实 controller_start 分别传不存在的路径和错误预期版本 0.0.0，要求返回 controller_executable_missing／controller_version_mismatch，且不增加 pane_started。产品每次启动自行执行一次 --version，不能用脚本前置探测替代 |
| 截图 | 各尺寸一张不剪裁、不拼接原始单帧；先核对 PID／启动时间／完整命令及唯一窗口号，再用 screencapture -l，只截本次隔离窗口。1440×900 的 green-original.png 为同屏主证据 |
| 网络／登录 | loopback 假 API 拒绝所有 POST，预算 0；不复制 auth.json、不触碰真登录或全局配置。fake_posts=0 仅统计本夹具 API，不是系统级零出站证明 |
| 收尾 | ready 未确认（包括提前退出）就保留现场等主控，脚本不自动向 Electron 发信号；ready 确认才正常退出，三份凭据关闭且三个原 agent 仍存活后，再停止后台。确认登记 writer 消失后复制归档，链接不跟随，原件保留 |

```sh
python3 -B evidence/2026-10-16-batch16/T-091/run_three_panes.py \
  --source /Users/luckye/Documents/Code/a2a-wt-t091 \
  --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/green-02 \
  --label green-02 \
  --claude /Users/luckye/.local/share/claude/versions/2.1.302 \
  --claude-version 2.1.302 \
  --approval-ref '<本次主控逐项核对上述 CLI、hook、输入与收尾后的批准引用>'
```

成功应为 PASS／rc 0，green_observed、negatives_passed、version_refusals_passed、cleanup_complete、archive_complete 均为 true，fake_posts=0，无 error、post_close_error、archive_error、cleanup_errors。任一设置／权限／合同／收尾失败都保留为 INCOMPLETE，不重试、不换标签覆盖失败。配置路径不存在时在任何 daemon／receiver／Electron 启动前即报清楚的错误；不扫描其他已安装版本，不关闭自动更新。

期待身份在 UI 打开前由夹具启动记录冻结。外置目录保存 expected.json、三份角色 snapshot、三份 process、完整命令、独立原 trace、按 launch 归属的 driver 输出、原始单帧、用户输入／介入／同 request 收据链、版本与窗格拒绝记录和归档夹具。角色与 task／launch／attempt 靠后台字段及进程核对，不靠标题；三格始终挂载，不以顺次切换或三图拼接代替同屏。仓库只产生 green-02.run.json 和 green-02.archive.json。red-02 与 T-078 的 CLI 为 2.1.296，不能补称它们验证了 2.1.302。

## 回归执行顺序

五个 case 的独立清单在 [run_regression.py](run_regression.py) 开头；每次都须有本轮批准引用，输出目录不得已存在。下列命令是完整入口，内部原始子命令与退出码逐项保存到外置 commands.jsonl。

**四份 core 原件已由主控加入稀疏 checkout。** worker 不带 --restore 的检查为 PASS；无须运行恢复脚本。core -01 卡在旧 T-076 范围审计的方法名；现包装器按 T-091 任务卡起点 44bbb7828 逐字节核对三份 acceptance 源码和 task-cards 测试，不屏蔽方法，不改业务断言。缺件与审计问题仍不能算业务红态。

```sh
python3 -B evidence/2026-10-16-batch16/T-091/run_regression.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --case core --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/core-regression-02 --label core-regression-02 --approval-ref '<本次 core 批准引用>'
python3 -B evidence/2026-10-16-batch16/T-091/run_regression.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --case window --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/window-regression-02 --label window-regression-02 --approval-ref '<本次 window 批准引用>'
python3 -B evidence/2026-10-16-batch16/T-091/run_regression.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --case runtime --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/runtime-regression-02 --label runtime-regression-02 --approval-ref '<本次 runtime 批准引用>'
python3 -B evidence/2026-10-16-batch16/T-091/run_regression.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --case input-failures --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/input-failures-regression-02 --label input-failures-regression-02 --approval-ref '<本次 input-failures 批准引用>'
python3 -B evidence/2026-10-16-batch16/T-091/run_regression.py --source /Users/luckye/Documents/Code/a2a-wt-t091 --case worker-inbox --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/worker-inbox-regression-02 --label worker-inbox-regression-02 --approval-ref '<本次 worker-inbox 批准引用>'
```

core 运行原 coop／recovery／run／CAS 的 8／9／18／1 方法，要求 0 failures／errors／skipped；fence／CAS／lock 单处错误实现须分别触发原业务断言，由原 business_mutant 验证，不能把环境失败或任意 rc 1 算反例。其内部精确 suite／method 参数另见 [REGRESSION-PLAN.md](REGRESSION-PLAN.md)。没有使用旧 --probe all／--validation 包装器。

window 精确跑现有 test_electron_e2e.py --stage window，预期四项检查；运行时／输入失败／worker 收件箱分别精确跑现有 test_t078_input_entry.py 的 --runtime-probe／--input-failures／--worker-inbox，要求 12／11／14 项全部通过。它们只用受控 receiver，无 Claude／真 Codex／真实模型；runtime 会发三次合成 Stop，input-failures 一次，worker-inbox 四次。runtime 的 UI Esc 和显式放行、迟到 Stop 保持队列、已有注入不算用户输入等，是 T-074 固定合同在当前生产输入路径的回归；不补称重新做了 T-074 的供应商模型实验。

GUI 回归原 capturePage 小帧只含自己的 renderer；本票同屏主证据使用上方已核对 owner 的 -l 原始帧。新客户端删除自动强杀路径；ready 或退出未确认就暂缓后台收尾与归档，主控从 driver 记录里的原 PID／启动时间／命令处理现场。wrapper 不信任顶层 rc 单独成立，另核对业务结果／数量、登记进程消失与归档比较；没有修改原业务 oracle 来凑通过。

五类回归逐场运行，不并行打开窗口。每个 GUI case 最多 400 次探测 RPC、读屏上界 1200 次；stdout 达 64 MiB 后停止下一次探测，允许一份在途回复跨过阈值。正常 close 不占探测额度，仍核对 ready 和进程归属；本地限额反例确认额度耗尽后可以发关闭请求。各 case 的完整 stdout／stderr 直接写外置文件，不复制到顶层命令 JSON 或 Terminal。摘要记录实际 Electron、窗数、读屏、截图、请求数及 stdout 字节数；core 为 Electron 0，其他场景各 1。受控 receiver 不是真 Codex，会话总数由主控在每场开始前核对。

每个 case 全部成功为 PASS／rc 0、archive_complete=true。原始输出和 fixture 副本留外置盘，仓库仅留对应的 run.json 摘要／archive.json 清单。失败时保持 INCOMPLETE、原件不删；不要把旧候选的 PASS 沿用给当前三格版本。

## 已有本地证据与未验证边界

本地已跑的纯检查包括：pane-ipc-unit-04（11 项路由合同，含三格独立声明）、launcher-unit-01（起点丢失重复 --launch 的反例）、driver-selection-unit-02、client-cleanup-unit-01，以及使用主控恢复原件的 t078-window-binding-01（13 项）。它们替换了外部边界，不能证明真实 Electron／PTY 运行已通过。

baseline-bridge-assertion-01 在起点 44bbb7828 取出原 preload 与原断言，实际执行模块并原样执行那条断言：六方法被旧“只允许两方法”断言拒绝。这是纯接口断言的起点结果，未运行完整旧 window suite；候选 window case 才取得真实窗口结果。现断言精确列出 beginComposition、input、observeFocus、output、paneKeys、releaseQueue、snapshot，没有宽松数量判断。

三格真实截图、三份进程读回、实际拒绝和五类回归均尚未运行。缺屏幕录制／辅助功能权限时停报，由用户在系统设置处理；脚本不打开系统设置、不请求升级、不使用真实登录替代假 API。

接手复验：`pane-ipc-takeover-01` 11 项、`launcher-takeover-01` 2 项、`driver-selection-takeover-01` 5 项、`client-cleanup-takeover-01` 4 项、`t078-window-binding-takeover-01` 13 项及 `observer-cleanup-takeover-01` 6 项均 PASS；资源限额以 `run-budgets-red-01` 保留红态，`run-budgets-green-02` 在两种实际客户端上拒绝旧实现，并验证计数／stdout 阈值与关闭额度。`product-parse-takeover-01` 和 `script-parse-takeover-01` 仅证明内存转换／语法，未构建或运行产品。

冻结候选 03b80c4 的只读工具审查为 FAIL，发现凭据删除失败仍可能 PASS；原报告见 `three-pane-acceptance-audit-01.md`。此后已将完成标记移至删除成功后，且最终判定检查 cleanup_errors 为空。`cleanup-verdict-green-02.json` 三项纯逻辑检查 PASS，并拒绝该坏候选；最终脚本没有新的独立通过结论。交主控实跑时仍须逐项核对 cleanup_complete、错误列表、外置归档与进程退出，不以旧审查或本地逻辑检查替代实际收尾。
