# T-029：coop.py 改接 Muster（2026-10-07）

状态：**INCOMPLETE：四项当前候选验收均 PASS，独立审查待执行。** 当前业务 task 已 accepted；这不代表 M1、GUI 或生产发布通过。

## 当前验收与证据

| Ticket 条目 | 当前结论 | 命令与原始记录 |
| --- | --- | --- |
| 只调用 Muster；版本和启动规则保留 | PASS | coop.py 只通过显式绝对 MUSTER_BIN 调用 Muster，缺失/不可执行即拒绝，无 Herdr fallback。Codex 0.160.1、gpt-6.1-sol/xhigh/显式 fast、check_for_update_on_startup=false 和原 submit/oracle/CAS 门禁保留；实际启动 argv 见 final-runtime-04/delivery-checks.json、final-runtime-04-live_run/events.json。 |
| 交付 8、恢复 9、编排 18 | PASS | 从独立 Muster shell pane 内调用 run_checks.py，final-runtime-04/suites/result.json 为 8/9/18、0 failure、0 error，开始/结束版本均绑定当前候选。三份 *.trace.json 与 artifacts.tar.gz 保留真实 CLI/Git/SQLite、故障屏障及所有 repo/worktree。编排负例为隔离 Muster/Codex 替身，不能替代真实模型边界。 |
| 真实 Codex run 完整闭环 | PASS | 只驱动一次 coop.py run，600 秒显式 submit 等待期限。worker 在 Muster pane 中创建 commit、显式 submit；独立 oracle 退出 0，CAS 集成，idle 后回收 owned pane。独立 Git 引用读回和另一个 detached worktree 的 oracle 12 项均通过；原 repo HEAD 未移动、父 pane 保留。见 final-runtime-04-live_run/run.json、commands.jsonl、events.json、result.json；归档 runtime-artifacts.tar.gz 保留完整原/新 attempt、Git repo、验证和读回 worktree。 |
| fence 反事实 | PASS | final-runtime-04/fence-correct/result.json 拒绝 fence+31、task/ref 不变。删除唯一 submit fence 校验的 mutant 接受错误 fence 并改变 task，两个业务断言失败；fence-mutant/result.json 的错误候选仍为 INCOMPLETE。变异只在隔离文件中执行，生产文件未被改坏，不以导入/环境失败充数。 |

## 冻结、身份与运行命令

真实运行代码候选为 `66565453cf3f188c7b368fc91a512222b6cab0bc`。构建命令及退出 0 见 build-git-rules-result.json / build-git-rules.log：

```sh
MUSTER_BUILD_SLOT=worker-t029 ./scripts/build build --locked --manifest-path muster/Cargo.toml
python3 -B evidence/2026-10-07-m1-batch3/T-029/runtime_probe.py --checks --isolated-codex-home \
  --fixture-repo /private/tmp/t029-2uoclfw5/fixture \
  --existing-state /Users/luckye/Documents/Code/a2a/.runtime/final-runtime-01-live_run/state \
  --binary /Volumes/WD-Elements/dev-cache/a2a/target/worker-t029/debug/muster \
  --output evidence/2026-10-07-m1-batch3/T-029/final-runtime-04
```

复跑须用新输出目录和符合当时许可的夹具/状态；本次已 accepted 的 task 不能当新模型运行复用。探针运行期间新建目录，旧失败目录不覆盖。Rust 构建、Cargo/Zig cache 仍经外置盘入口，未改引擎。早期红态复用 T-027 二进制；最终证据使用 worker-t029 在本 ticket 冻结候选构建的二进制。33 条引擎 warning 原样保留，未额外重跑引擎自带单元套件。

- 主控 Claude Code（Herdr wF:pM），本 worker Codex（wF:pT）；没有把事后自查补称为独立监控。
- task=automatic-pagination；attempt=`afa79f067af44952b5d03d70c76051fa`；session_id=`4c7de00a450947678a472069b0ffe121`；fence=4；spec_rev=1。
- run_id=`c3f9cbfd77884d1e9efd81690a63f3be`；accepted commit=`47976b1538721d9d58fa6787c23f48a2c2e72b37`；closure agent_status=idle。
- 引擎会话、PID、socket、父 pane 和版本见 final-runtime-04/context.json；模型启动请求和全部精确 argv 在 CLI 事件中。fast 是请求配置，供应商实际 tier 未验证；无吞吐/成本/可靠性收益主张。
- 原生 metadata 有两个同 cwd 的 CLI 记录；未保留 parent/auxiliary 链接和辅助配置，不把它们当两名独立 worker，也不替代外部 reviewer。其 CLI 版本和分配 cwd 可核对。可选 native 工具筛选器未选出记录，空数组保留并明确不作证据，见 native-tool-trace-limitation.json；该不可靠筛选器已移除，不为可选日志重复模型实验。

**Tracer bullet** 是真实 Muster CLI→server→pane→Codex→显式 submit→独立 Git/oracle→CAS→idle 回收。**Deep modules** 保留同一持久门禁与现有 CLI，不另造 runtime 适配器或平行 API。**Ubiquitous language** 沿用 CONTEXT 的 task/attempt/session_id/fence；引擎保留 spec 允许的 workspace/tab 字段。

## 授权、生产前提与清理

无人值守 run 依赖 worker 的 Codex 允许 `git add` / `git commit`。主控第三份决定给出沙箱探针：Git worktree 元数据有专门保护，额外可写根不能解决 index.lock；生产路径靠用户 default.rules 中两条 allow prefix_rule 在沙箱外执行这些命令。独立原文见 controller-decision-03-used.md；worker 未重复已提供的探针，也未擅自增加授权。

本次只在新 /tmp/t029 隔离 home 中复制 auth.json（600），只给已核对夹具设置项目 trust，并从用户文件逐字选取：

```text
prefix_rule(pattern=["git", "add"], decision="allow")
prefix_rule(pattern=["git", "commit"], decision="allow")
```

其他用户 rules/config/hooks 均不复制，不改沙箱模式，不回答任何正向权限选项。规则原文、源路径及许可在 selected-git-rules.json、isolated-home-scope.json。启动 writable root 仅为 state root；Git common dir 改动已从生产和当前测试回退，无双路径或 fallback。

所有继承 HERDR/MUSTER 变量与旧 CODEX_THREAD_ID/CODEX_HOME 在 server 启动前剥离；只控制自己创建的含 t029 名称的会话，不修改或重启用户 Herdr。实际 server 用 start_new_session=True 和文件 stdio。验收、集成、回收走持锁 CLI，不直接改 SQLite、不替用户移动工作分支或 push。final-runtime-04/result.json 核对用户 config.toml、hooks.json、Herdr hook、default.rules 原字节均未变。

成功后 worker/owned server 均退出，再删整个隔离 home；isolated-home-cleanup.json 与 delivery-checks.json 在工具调用结束后确认不存在。归档成员检查不含 auth.json 或该 home，认证副本没有进入 evidence/Git。前次 blocked 客户端重建临时缓存的现象保留；其客户端在本次恢复前拒绝/idle/reclaim 后已结束，对应 home 最终完整清理，不把此前瞬时 absent 当永久清理。

## 红态、被拒候选和恢复记录

- red-suites-01：产品改动前，仅迁移外部可执行名/上下文到 Muster，业务断言不变。交付 8、恢复 9 通过，编排 18 中 13 失败；旧产品要求 HERDR_ENV，是新的运行时合同红态，不称原 Herdr 缺陷。
- red-live-02：真实 Muster pane 内，旧 dispatch/run 均 herdr_context_required；没有转发到用户 Herdr。red-live-01 错把 pane run 空 stdout 当 JSON 的夹具失败单独保留，不算业务红态。
- red/green-hook-review-01：T-027 真实 Hooks need review 被检测成 idle，旧实现会自动 prompt/关闭。精确界面外部替身的两个业务断言红态保留，startup 保护后绿态；不自动批准 hook。
- final-runtime-01：正常 home 下 Folder access 许可等待；未 prompt，task paused。随后 server 随工具进程组结束无日志退出。lifetime-attached/detached 最小对照证实启动方式影响；具体回收信号未跟踪，机制推断不当作 kernel trace。只修夹具，不改引擎；原 layout/PID 缺席证据、同 namespace 权威清单与原 attempt reclaim 在 reclaim-old-01。
- final-runtime-02：隔离 home 信任生效，fence=2 的模型修改 pager，但缺 Git 命令规则，停在审批 UI。主控不批准；只按一次 Esc、确认 idle 后 CLI reclaim，dirty worktree/历史保留，见 refuse-and-reclaim-02。
- common dir 尝试：red-git-common-01 的 argv 断言来源是独立 Git 元数据，旧参数失败；参数追加后的 green-git-common-01 只证明声明，不能证明沙箱生效。final-runtime-03 的实际前台 Codex argv 有 common dir，仍到 Git 审批；旧未知结论与完整 UI 保留。主控独立 codex sandbox 探针确认 Git 元数据保护后，此改动按决定回退，不能复用它的参数绿态为当前行为背书。
- final-runtime-03 当前请求按一次 Esc 拒绝，idle 后原 attempt CLI reclaim，dirty worktree/历史保留；owned server 退出后 home 整目录删除，见 refuse-and-reclaim-03。
- AGENTS 66fa604 要求回收前已 idle。red-idle-reclaim-01 保持已提交/accepted worker 为 working，旧自动回收提前关 pane；业务红态保留。现在只读、有界等待 idle/done，blocked/unknown/身份变化/期限结束保留现场；green-idle-reclaim-01 通过。当前真实 run 的 idle 最终权威观察也已核对，业务门禁未改。
- focused-check-artifacts.tar.gz 保留所有相关局部红/绿 Git/worktree/屏障。全部旧 run 的原始输出、数据与失败 archive 未覆写；当前原事件前缀保持，证明不是重建一个 task 数据库抹去旧 attempt。

## 独立审查与主控交接

四项已具备当前证据，待冻结后进行一次 fresh-context 独立只读审查，记录模型与冻结提交。不得拿 T-027 审查替本候选背书；审查期间不修改跟踪文件。

worker 未改根 README、MAP、AGENTS、CONTEXT。README 需要改为 MUSTER_BIN / live_muster.py 入口，并说明上述 Codex Git 规则前提、single-user trusted-collaborator 边界和当前验收范围；README Covers 替换已删除的 live_herdr.py；CONTEXT 术语未变，由主控核对后更新 Verified。结构问题为 0，根 living doc stale 按任务书交主控处理。范围不含 GUI、第二 CLI、生产发布、完整 run 进程自动恢复或长期收益。
