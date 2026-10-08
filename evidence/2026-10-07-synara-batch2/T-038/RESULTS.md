# T-038 交付记录（2026-10-08）

总体 **INCOMPLETE，待主控关闭**。dev Chrome 的任务窗口、真实门禁状态变化、归属保存与重启已取得 PASS 证据；原生 Electron 任务窗口没有有效通过证据。完整 workspace suite 为 NO_GO，不能用局部通过覆盖。按主控决定 05，基线也出现 Electron 空白，可采用 dev Chrome 界面证据；外观仍由用户判断。

候选为 Synara fork `ad13b72c5faeb5fb601c3d40b7090d746f4f2758`，基线 `a9cc30c395af9ffd51476a1841d80bca66568993`，checkout `/Users/luckye/Documents/Code/synara-t038`。没有合并 T-037，也没有修改其独占的 `a2aGates.ts`、`service.ts`、核心或 CLI。版本、worker 身份、四个真实演示 attempt 的 task/session/fence/spec_rev 见 [绑定记录](final-runtime-binding.json)、[启动身份](runtime-start.json)。worker 的业务 attempt 未提供，未编造；请求 Fast 不等于实际供应商 tier 已证实。本 ticket 没有启动模型 turn。

## 实现与行为证据

按照 [主控决定 03](controller-decision-03.md) 使用独立 membership，门禁 task id 为身份，角色仅用于会话分组。原生载体的核实见 [对照页](grouping-comparison.md)。membership 保存到服务端独立 SQLite，使用 revision CAS；门禁状态、验收、集成和回收仍只经现有核心。界面沿用 Synara 的侧栏、字号、Button、Badge、Input、Select 和 ChatView。

| 范围 | 结论与证据 |
| --- | --- |
| membership HTTP Tracer bullet | PASS。基线入口返回 302，不满足预先写定的 200/空数组合同：[红态](membership-red-02.json)；实现后返回 200/ok/tasks=[]：[绿态](membership-green-01.json)。首轮自动跟随重定向的夹具错误另保留，不计合同红态。 |
| 归属与拒绝 | PASS。[真实 HTTP 场景](membership-scenario-01.jsonl)、[跨项目反例](cross-project-01.json) 包含未知项目/会话、重复成员、旧 revision、跨项目 thread 和门禁 project 不一致。 |
| OPTIONS | PASS。[预检](preflight-01.json) 包含可信 origin 的 204、credentials、Content-Type 与不可信 origin 的 403；复用原 owner/origin 检查。 |
| GUI 表单 | PASS。[已知坏候选现场](membership-gui-01.json) 点击后没有任务；根因是既有 Button 默认 type=button。仅在两个自有表单补 submit。[最终 GUI](membership-gui-headed.json) 证明新增、两角色保存与并发 CAS 拒绝，[截图](membership-gui-headed.png) 显示 stale_revision，服务端保留并发保存值。 |
| 并列会话 | PASS。实际 ChatView 在任务窗口中挂接既有 detail subscription；此前两栏停在 Loading conversation 的 [红态](ui-session-red.json) 与 [绿态](ui-session-green.json) 均保留。最终闭环与重启再次核对两栏加载完成。早期未逐次冻结的现场只作诊断，不替最终候选背书。 |
| 真实门禁 GUI | PASS。[第二夹具输入](cycle2/fixture.json) 和 [完整 GUI 记录](cycle2/cycle-gui-headed.json) 在最终候选上核对当前 aria-current step，并回读真实核心。门禁 CLI 的 [claim](cycle2/claim-bad.json)、[submit](cycle2/submit-bad.json)、[oracle 失败](cycle2/verify-bad.json)、[新 attempt](cycle2/claim-good.json)、[验证](cycle2/verify-good.json)、[集成](cycle2/integrate-good.json) 均有完整 argv/输出。 |
| 重启与上游表结构 | PASS。[重启 GUI](restart-gui.json) 从真实服务和新 Chrome context 回读原任务、两角色与 GUI 并发保存后的标题；[任务截图](restart-gui-managed.png)、[编辑结果截图](restart-gui-edited.png)。原生 projection_threads 的 [51 列前记录](thread-columns-before-restart.json) 与 [最终记录](thread-columns-after-gui.json) 相同，没有迁移或结构改动。 |

第二闭环截图：[claimed](cycle2/cycle-gui-headed-claimed.png)、[submitted](cycle2/cycle-gui-headed-submitted.png)、[真实失败原因](cycle2/cycle-gui-headed-oracle-failed.png)、[verified](cycle2/cycle-gui-headed-verified.png)、[accepted](cycle2/cycle-gui-headed-accepted.png)。失败来自既有独立分页合同与 oracle 的 unordered-ties 输入；oracle 没有导入本次实现。初始 ready 见 [截图](cycle2/ready.png)。第一闭环所有输出和中断现场仍保留；旧文件名 desktop-ready/desktop-claimed 实际来自 dev Chrome，不作为桌面证据。

## T-037 协议夹具

T-037 未合并，此分支没有真实人工输入记录器。下列 PASS 只证明界面读取其已发布形状，不证明真实订阅、落盘或故障恢复。

- observer 三态都有有效无遮挡截图：[缺失](observer-missing-clear.png)、[healthy 夹具](observer-healthy-clear.png)、[failed 夹具及原因/拒绝说明](observer-failed-clear.png)，对应同名 JSON/command 记录。缺失明确显示“未安装”。[真实 verified 状态上注入 failed 的截图](cycle2/cycle-gui-headed-observer-failed-FIXTURE.png) 还核对集成按钮禁用；撤掉读响应夹具后，真实 CLI 完成集成。没有自造协议字段，也没有模拟业务状态。
- [人工介入 GUI 夹具](human-gui-fixture-02.json)、[截图](human-gui-fixture-02.png) 将符合 T-037 字段的事件附加到只读 events 响应，核对 event_id 去重、对应 thread、历史 attempt 与正文；真实任务前后保持 accepted。它不证明真实事件生产器。纯读取测试的 [always-empty mutant](human-reader-mutant-01.json) 在业务断言上失败，恢复后相关测试通过。mutant 首次脚本尾部错误检查 stdout 的异常单独保留，源码恢复记录为 true。
- 早期 observer 弹窗等待超时、并行 Chrome 页面关闭、人工介入 exact-text 定位失败都保留为夹具失败，未计 PASS。最终三个 clear 记录与 human-gui-fixture-02 重新取得有效截图。合并 T-037 后的真实复验由主控安排。

## 两个 desktop 测试与 Electron 对照

未改基线 detached worktree 为 `/Users/luckye/Documents/Code/synara-t038-baseline`，保留至主控关闭。依赖仅 APFS copy-on-write 复制已安装树，没有新增依赖或下载；[设置](baseline-setup.json)、[额外构建依赖](baseline-desktop-dependencies.json)、[基线构建](baseline-desktop-build.json) 与干净 git status 已保存。

最初两个指定用例各单跑一次：[cuaDriverHost:2491](baseline-cua-case.json)、[workspaceUpload:441](baseline-upload-case.json) 都 PASS，所以不能据此称为上游原有失败。候选上传用例单跑 PASS；CUA 曾多次 timeout。按 [决定 05](controller-decision-05.md)，停止本 ticket dev 服务，以同一 slot/temp/cache 顺序交替三次：

| 次数 | 基线 | 候选 |
| --- | --- | --- |
| 1 | NO_GO，8.918 秒 | NO_GO，3.509 秒 |
| 2 | PASS，1.846 秒 | PASS，3.411 秒 |
| 3 | PASS，1.937 秒 | PASS，1.676 秒 |

[六次原始记录与结论](paired-cua-conclusion.json) 均保留。两边失败都发生在该用例 1000 ms 请求期限；按主控规则归为不稳定上游用例，未修改上游测试或 CUA 实现。[相关源码逐字节比较](upstream-source-byte-comparison.json) 相同。上传用例的全套失败在单跑基线/候选中未重现，具体原因未确定。完整 suite 的 NO_GO 仍保留。

Electron 诊断只读，没有修补上游。相同 Electron 43.4.1、Vite 根 URL、隔离 home/profile 与分别构建的代码：[基线截图](electron-baseline-compare.png) 空白，buttons=0，桌面桥接存在，日志含 ws negotiate 连接拒绝及 browser vault/Safari 访问拒绝；[候选截图](electron-candidate-compare.png) 根入口有 22 个按钮。两份 JSON 保存日志、请求、身份和清理结果，[对照结论](electron-comparison-conclusion.json) 不推断具体根因。另一次 [候选任务导航](desktop-navigation.json) 的导入/教程等待失败，仅计夹具失败，不能用根入口渲染冒充任务窗口通过。

dev Chrome 使用相同 web 源码、真实服务端 HTTP/WebSocket 和持久数据，但不覆盖 Electron 原生桥接、原生权限、打包资源、签名或安装版。它使用独立 context/profile；Playwright 由用户在 [决定 04](controller-decision-04.md) 明确批准。采用已有 Chrome 和已有 Electron 缓存；没有下载浏览器。最终闭环和表单使用有窗口 Chrome、reduced-motion 偏好；早期 headless 关闭原因未确定，不称为已修复。

## 检查、变更范围与交接

最终候选的 [typecheck](delivery-typecheck.json)、[lint](delivery-lint.json)、[格式检查](delivery-fmt-check.json) 为 PASS；lint 有既有 warnings，没有 error。[相关现有/新读取测试](final-related-web.json) 为 4 文件、27 测试 PASS。[完整 workspace suite](workspace-test-01.json) 为 NO_GO，两处 desktop 失败导致其余部分中止。没有将中止部分写成通过。

19 个改动文件见冻结清单。上游接入仅 `packages/a2a-gates/package.json` 的 membership export、contracts 导出入口、新建 a2aMembership.ts、httpRoute.ts 新增 membership/OPTIONS、web `_chat.tsx` 入口与生成路由注册；原门禁 GET/POST 段及鉴权不改。其余均是新 membership 模块或自有 `apps/web/src/a2a/**`。没有 thread schema、原生 ProjectTask、依赖或上游测试改动。

安装 [记录](install-01.json)：2599.709 秒；checkout 的 du -sk 从 128384 KiB 到 2600984 KiB，最终约 3118188 KiB。缓存、Node 和 Electron 位于外置盘。版本见 [工具记录](tool-versions.log)：Node 24.13.1、Bun 1.4.2、Playwright 1.62.1、Chrome 154.0.8037.98；Herdr 0.9.3、Codex CLI 0.161.0 见启动身份。没有性能收益主张。

[原始夹具归档](retained-fixtures.tar.gz) 与 [目录清单](fixture-archive.json) 包含 ticket 自建 Git repo、门禁状态、工作树、oracle 和 instructions；原外置目录保留，不登记 gitlink。没有归档用户数据、auth、生成密钥或浏览器 profile。[清理记录](owned-process-cleanup.json) 确认本 ticket 服务退出，5811/7771 没有监听。基线 worktree 路径保留。

复现命令见各 `*-command.json`、CLI JSON 和脚本；核心入口均经 fork `a2a/scripts/bun`。例如重建基线用 `A2A_SYNARA_SLOT=t038-baseline ./a2a/scripts/bun run build:desktop`，顺序 CUA 对照用 `python3 paired-cua.py`（新运行需新记录名，脚本拒绝覆盖）。重新 GUI 闭环需新夹具目录，现有 accepted attempt 不回滚；脚本与全部输入在 cycle2 中保存。

冻结后按 behavioral-acceptance-review 做 fresh-context 只读审查；审查结果另存，不用自报替代独立结论。原生桌面任务窗口与 T-037 合并后的真实 observer/人工输入 GUI 仍为 INCOMPLETE。ticket 保持 open，待主控关闭。
