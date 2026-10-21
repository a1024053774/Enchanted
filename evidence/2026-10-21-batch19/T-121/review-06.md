## T-121 第 6 轮复审（候选 6 = 44220954e，HEAD 85c775817）

**结论：可以合并，没有阻塞项。** 本轮声明的行为都实测成立：授予本身没有权限；对手的自动拒绝发生在确认生效时；15 秒没确认，后台用定时器写 `role_request_ended(not_confirmed)` 事件；`all()` 已不再用墙钟推导，没有发现状态回退。有 1 项应修：失效横幅会误报。另有若干建议。仓库没有任何修改，所有产物都在 /private/tmp/t121-rev06/。

### 1. 阻塞
无。

### 2. 应修
**S1：新授予已经生效，横幅仍持续显示旧的“没有生效”，最长 5 分钟。**（workbench/src/sidebar.ts:196-197；workbench/app/renderer.tsx:751-753）
- 横幅只按 `decided_at` 是否在 5 分钟内筛选。不看这个终端后来有没有成功拿到角色，横幅也不能关掉，文字里没有时间。
- 探针 P5：同一终端前面有 3 次授予没确认，随后重新申请、批准、确认，`whoami` 返回 `executor`，侧栏也列出了这个主控。这时 `unconfirmed_role_requests` 仍有 3 条，界面上就是三行“批准的执行主控没有生效”。用户很容易以为刚才这次批准失败了。
- 修法任选其一：这个终端（或同项目同角色）后来有了更新的申请就不再显示；或者显示授予时间并允许关闭；或者同一终端只显示最新一条。

### 3. 建议
1. **授予期间界面看不出“等待确认”。**（renderer.tsx:754-766）被授予的申请从待批准列表消失，对手的“批准”按钮仍可点，点了只显示原始错误“批准没有生效：Error: role_taken”。正常确认只有几毫秒，但申请方在收到授予后、确认前被杀时，这个窗口会持续整整 15 秒。建议显示一行“已批准，等待 X 确认”。
2. **授予期间新来的申请处理不对称。**（roleRequests.ts:71）已有的对手保持待批准；新开的同角色申请却因为 `holder()` 把 granted 也算作占用，当场返回 `role_taken`。授予作废后，这个申请也不会回来。README 写的是“其他申请保持待批准”，应注明只指授予之前已经存在的申请。
3. **`asker_gone` 结束的授予没有横幅。** 后台批准后最多 200ms 才轮询到授予并返回，申请方如果在这段时间内断开，结束原因记为 `asker_gone`（e2e 的 `unreceived_approval_ends` 就是这个情形）。用户点了批准，界面什么也不显示。README 写的“授予后连接关闭……作废”只在这段很短的时间里成立；正常流程中，授予返回后连接本来就会关闭，之后作废只靠定时器。
4. **定时器回调没有 try/catch。**（roleRequests.ts:87-90）回调里 `store.event` 一旦抛错（SQLite 忙、磁盘满），就是未捕获异常，会让后台崩溃。连接关闭时的结算（daemon.ts:653-659）是捕获后继续服务的，两处应该一致。
5. **confirm 中途失败会留下“已生效但客户端看到失败”。**（roleRequests.ts:96-100）确认事件和对手的拒绝事件不在同一事务里。拒绝写到一半失败时，角色已经 approved，确认请求却返回错误。建议放进同一事务。
6. **按钮禁用晚一帧。**（renderer.tsx:433-438）禁用由 `useEffect` 设置，在新列表画出来之后才生效，中间有一帧按钮可点。改用 `useLayoutEffect`，或者在渲染时直接按列表变化时间计算是否禁用。列表在一秒内清空时 `requestsSettling` 会一直是 true，但这时没有按钮，下一次列表出现会重置，没有实际影响。
7. **不在视图的终端仍可能分不清。**（renderer.tsx:757-759）打开时间只到分钟，工作目录是打开时的 `worktree`，不是当前目录。同一分钟在同一目录打开的两个终端分不出来。
8. **终端关闭、后台重启结束的授予不写事件**，只推导为 `terminal_gone`（探针 P4、P6）。这是已有的设计，不影响权限，审计时要结合 `shell_closed` 和 `daemon_started` 来看。

### 4. 逐项核对的结果（探针实测）
- **多个对手、撤回的对手、其他角色、其他项目**（P1）：授予期间对手 q、r 都是 pending，再批准 q 返回 `role_taken`。确认后 q、r 都是 `rejected/role_given_to_other`，各自的 `a2a request` 立即返回。已撤回的 w 只有一条 `asker_gone`，没有被重复写。同项目的 ideation 申请、other 项目的 executor 申请仍是 pending。
- **release 与定时器竞争**（P2）：授予后第 5 秒 release，事件为 decided、ended(released)，定时器没有再写，也没有横幅。
- **确认与定时器同时到达**（P3）：确认在第 14.6、14.9 秒到达，结果是 approved，只有 confirmed 事件。在第 15.0、15.1、15.4 秒到达，结果是 `request_not_granted`，只有 ended(not_confirmed) 事件，role 为 null。两种事件从未同时出现：两者都在单线程里同步执行，先到先生效。
- **授予期间关闭终端**（P4）：推导为结束，定时器没有写事件，没有横幅。
- **授予期间后台重启**（P6，约 1.6 秒后重启）：17 秒后没有 not_confirmed 事件，没有横幅，没有待批准申请；旧终端令牌返回 `invalid_terminal_identity`，重启后后台照常服务。
- **`all()`**：已删除墙钟分支。只剩 sidebar.ts:197 用墙钟决定横幅显示 5 分钟，只影响界面显示，不影响权限。
- **expiry-unrecorded 变异体**：16 秒后迟到的确认仍然成功（late_confirm 为 None）。这说明定时器事件现在是“授予作废”的唯一来源，没有残留的旧推导路径。

### 5. RESULTS.md 必须写明的事实
- granted 没有权限，确认后才变成 approved。对手在确认时才被拒绝；授予期间对手保持待批准，再批准返回 `role_taken`；授予期间新来的申请会被当场拒绝（`role_taken`）。
- 授予作废由进程内定时器写 `role_request_ended(not_confirmed)`。终端关闭、后台重启只推导为 `terminal_gone`，不写事件。
- 失效横幅按墙钟显示 5 分钟，同一终端重新获批后旧横幅仍在（S1，未修时须写明）。`asker_gone` 结束的授予没有横幅。
- review-05 的残余（确认回执丢失；同一终端内其他进程可代发确认）照原样保留，没有消除。
- 界面改动只读了代码，没有跑 GUI，也没有截图核对。

### 6. 实际运行的命令和结果
运行目录 /Users/luckye/Documents/Code/a2a（workbench 工作区与 HEAD 一致），本机负载约 5，没有出现超时。

| 命令 | 结果 |
|---|---|
| `python3 workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev06/green.json` | PASS，47 项检查 |
| `… --mutant expiry-unrecorded` | INCOMPLETE，`grant_needs_confirmation` 失败（expired=[]、notice=[]、迟到的确认成功），变异被抓到 |
| `… --mutant rivals-left-pending` | INCOMPLETE，`confirmed_grant_settles_rivals` 失败（rival=still_waiting），变异被抓到 |
| `… --mutant grant-has-authority` | INCOMPLETE，`grant_needs_confirmation` 失败（role=ideation，调用被放行），变异被抓到 |
| `… --revision 6147b4678` | INCOMPLETE，`grant_needs_confirmation` 失败（rival_pending=0、expired=[]），旧实现为红态 |
| `python3 /private/tmp/t121-rev06/probe/base.py <repo> …/probe-result.json` | 跑出 P1～P5。自写的 P6 段在重启时撞上 `operator.json` 已存在，这是探针本身的问题，不是产品缺陷 |
| `python3 /private/tmp/t121-rev06/probe/restart.py <repo> …/restart-result.json` | 修正后单独重跑 P6，exit 0 |

**没跑的**：其他变异体、T-107/T-109/T-111/T-118 回归、渲染端构建与类型检查（构建会在仓库内写产物，所以没做）、Electron 界面实测、墙钟回拨实验。

日志与 summary：/private/tmp/t121-rev06/{green,mutant-*,rev-6147b4678}.json 和对应的 .log、exits.txt；探针脚本与结果在 /private/tmp/t121-rev06/probe/（base.py、restart.py、probe-result.json、restart-result.json、*.log）。