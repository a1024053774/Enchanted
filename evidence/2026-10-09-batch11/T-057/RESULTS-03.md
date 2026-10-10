# T-057 ready_rev 3

状态：**PASS，独立审查 PASS；ticket 保持 open，待主控关闭。**

fork `1bcf20720483ab944a49ca20f56be776eb2f9b6c`，基线 `e94a0efc395c26bedb6cbf65f8fdf7f5c2125a58`，未 push。依据 rev3 brief、执行主控决定 01/05、ticket ready_rev 3、spec 第 4 节及本轮用户修订。前两轮文件原样保留。

| 验收范围 | 当前结果与证据 |
| --- | --- |
| 通知两路 | PASS（受控桌面接收端）：一般变化进入既有 toastManager；只有问题派生状态“等你决定”和收件箱 `kind=needs-decision` 加走系统提醒。普通 report 的标题、正文含等待词语仍不走系统；无等待含义的 `Ω-17` needs-decision 走系统。关闭与送达只发软件内通知。见 `notification-routes-rev3-04.json` |
| 启动、前后台、去重、设置 | PASS（消费者合同）：首次读取三个既存 blocking 合并一次；刷新不重复；前台新待决定不发系统，转后台提醒一次；关闭设置仍保留软件内通知，重新开启后补提醒未提醒项。注入时钟与前后台状态，见 `startup-parent-rev3-03.json`（健康主界面、父通知组件零调用）、`startup-green-rev3-04.json`（同一输入一次调用）、`notifications-rev3-green03.json` |
| 同批合并与静音 | PASS（消费者合同）：三个启动项、两个新待决定均各一次；bridge 参数 `silent=true`、`suppressWhenForeground=true`。OS 是否显示和是否静音尚不能由此推断 |
| 七个 MCP 动作 | PASS（决定 05 的组合）：真实 HTTP MCP、凭据注册、活跃主控身份、同一核心、SQLite 追加记录。close、needs-user、forward、已确认 delivered 成功追加；reopen、snooze、dismiss 被拒、零追加、状态不变，再经 HTTP 用户入口分别追加。delivered 在确认前先拒；blocking close 被拒。原 issue 与门禁 task 均未变。`mcp-actions-rev3-01/oracle.json`、逐次原始回执 |
| 两种尺寸的按钮 | PASS（可见、滚动及点击命中；外观由用户判断）：1600×1050 与 1280×900，各六个单题按钮和一个打包按钮，14 张图及完整矩形、实际 hit-test、Playwright click trial。`panel-geometry-rev3-02.json` 与同名前缀 PNG；未发送这些几何测试草稿 |
| 已结束会话的未确认转交 | 引用用户同意并入的 T-058 证据：`../T-058/serial-final-26/transport-oracle.json` 的 ended_forward，配套 `transport-entry-07.py`、原始 HTTP/MCP 控制输出；见 `../T-058/RESULTS-02.md`。本轮不重做 |
| 集中检查 | PASS：核心 issues/inbox 16/16；全 workspace typecheck、lint、fmt 退出 0。lint 877 warnings、0 errors，server sync-fs budget 通过。`final-rev3-{core,typecheck,lint,fmt}.command.json` 与日志 |
| 真实 macOS 系统通知 | PASS（协议与通知中心回执）：独立标准构建、隔离 Electron、真实前后台；两题只有一次 IPC/原生调用，macOS 通知中心有一条非空 id 与两题完整正文的回执；真实 Native.silent=true，未做物理音频测量。实际进程重启不重复；既有设置页实际点 off，读回 false，新 needs-user 零 IPC/原生调用。`native-notify-rev3-07-notification-center.json`、`native-off-rev3-08.json`、`native-settings-cua-rev3-08.json` 与 PNG。未观察到授权请求，未点击系统授权、未打开系统设置 |
| fresh-context 独立审查 | PASS：唯一一次 fresh-context 只读审查，冻结 fork 与 a2a `66809044`，没有发现。见 [审查](acceptance-review-rev3-02.md)及原始输出；限制没有上调 |

唯一产品改动是 `apps/web/src/a2a/IssueNotifications.tsx`；本轮没有新增上游文件接入。复用 `enableSystemTaskCompletionNotifications`，与现有“Desktop activity notifications”开关共享开关；关闭它会同时关掉该既有活动通知与 a2a 系统提醒，软件内问题通知继续保留。没有新设置字段、依赖、用户 MCP 身份、权限目录、内容含义关键词/正则、兼容入口或自动重试。

提醒消费者把 bridge 接受的提醒键保存到本机，前台与关闭设置的候选不记为已提醒；同一条目新处置产生新提醒键。bridge 返回接受不能证明 OS 已显示，最终 OS 结论以真实回执为准。存储读写错误会显示错误通知；失败不会改写成成功。

Tracer bullet 是首次读取 blocking → 真实查询 → 合并 → 现有 bridge 接收端；随后扩展前后台、开关、needs-decision 和普通变化。Deep modules：追加、状态、权限仍由既有核心拥有，通知消费者只路由字段和维护本机提醒记录。Ubiquitous language 沿用问题、处置、答复、task/attempt/thread。

本轮验收没有新增真实模型调用；MCP 夹具的 provider 活跃状态明确受控，不冒称真实模型执行。先前异常与探针修正见 [fixture-corrections-rev3.md](fixture-corrections-rev3.md)。MCP 用户动作边界已上报 `20261010T034945Z-worker:s11-t057-issue-001`，执行主控决定 05 同意该证据组合。

独立 checkout：`/Users/luckye/Documents/Code/synara-t057-notify`，提交同上。开工观察内置盘剩 7.5 GiB、外置盘 813 GiB；新安装前测得内置盘 8.4 GiB。原依赖 2.6 GiB、前轮总 checkout 3.4 GiB，预留 4.5 GiB后开始标准 `a2a/scripts/bun install --frozen-lockfile`。完整命令与前后空间留在 `desktop-install-rev3-01.command.json`；安装缓存与临时目录都在外置盘。标准安装退出 0，1635 个包、2033 秒；标准桌面构建退出 0，约 88 秒，产物齐全且输出目录不是链接。所有自建 Native 进程已退出；私有日志与 profile 移到外置盘，不进 Git，索引 `native-retention-cleanup-rev3-01.json`。checkout 在最终证据保存后移除，清理结果另附。

正式工作台、其数据目录、用户 Herdr、`~/.codex`、`~/.claude` 均未操作。本轮不走门禁 submit；交付是 fork 提交、a2a 证据提交及终端 DONE 行，交给执行主控关闭。

六种既定失败方式仍由同一核心处理；本轮当前候选的 issues/inbox 16 项检查覆盖锁与重复答复拒绝、活动 turn 排队、已结束转交、close/answer 交叠、注入时钟回拨及分隔文字/Unicode。真实已结束未确认转交按用户允许并入 T-058。此前真实模型消息接收的证据绑定旧候选，本轮不把它当作新模型执行结论。

独立 checkout 与其标准构建产物已经 `git worktree remove` 删除；路径与提交在 `checkout-cleanup-rev3-01.json`。没有删除旧 worktree；真实服务夹具根目录仍在外置盘保留。`startup-green-rev3-03` 的依赖重新优化导致页面导航销毁，未取到结果文件；04 在优化完成后同输入通过，旧日志保留。未重复全仓测试或旧候选的全部门禁场景，未宣称真实模型理解、物理音频或生产发布已验证。

最终独立审查 PASS，无修复或二次追审。冻结证据提交 `66809044cc1e8f6abe808e85d8284bfe779230cc`；本次收尾提交只追加审查输出、状态、编码检查和地图检查，不改变候选产品或原始运行结论。原始日志的尾空白、警告和失败原样保留，不据此冒称证据目录的 diff whitespace 检查通过。
