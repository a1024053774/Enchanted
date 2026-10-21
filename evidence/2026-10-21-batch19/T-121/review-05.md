T-121 第 5 轮复审（候选 5，提交 6147b4678）

**结论：可合并。** 没有阻塞项。下面的应修和建议都不会让没有确认的申请拿到权限，也不会让同一项目的同一角色同时落在两个终端上。但"agent 不知道自己已被批准"这个窗口只是缩小了，没有消除。RESULTS.md 不能写成"已消除"，必须照实写（见第 4 节）。

其后的提交 17b5e4f89 只改了 README、style.css（窗格标签改为居中），并新增 T-123～T-125 三张票。`workbench/src` 与 6147b4678 完全一致，所以我对当前 HEAD 跑的测试也就是对候选 5 跑的。README 新增的段落与代码行为一致。标签居中后的界面效果我没有看截图核对。

## 1. 阻塞
无。

## 2. 应修

**S1：确认能缩小窗口，但没有消除窗口；而且确认只证明"终端里有进程回了话"，不证明"agent 收到了"。**（daemon.ts:216-219，terminalCli.ts:41-44）
- 确认回执丢失时，角色照样生效。探针 S2 的做法：拿到授予后发出 `role_request_confirm`，不读回执就关闭连接。结果状态是 `approved`，whoami 返回 `executor`。确认这条连接没有绑定 `asker.gone`，所以 CLI 如果在确认生效之后、打印结果之前被杀（Ctrl-C、Bash 工具超时、进程被杀），角色仍然有效，agent 却没看到输出。窗口从"整个回执"缩小到"确认回执"这一小段，但还在。
- 确认可以由同一终端里的别的进程代发。探针 S1：申请方读到授予后不确认，另开连接调用 `terminal_whoami`，它会列出 granted 申请的 id；拿这个 id 调 `role_request_confirm`（也就是 `a2a call '{"command":"role_request_confirm",...}'`），结果 `ok`，角色生效。这在"身份就是终端"的信任模型之内，不算越权。但它说明确认表达的是"这个终端认了"，不是"发起申请的那个 agent 进程认了"。
- 处理办法二选一：在 RESULTS.md 和 README 里写明这两点残余；或者让确认走原来那条申请连接（申请方在同一条连接上回确认），并且确认回执没有送达就结束角色。

**S2：授予在冲突结算时提前生效，没确认的授予会让同角色的其他申请全部白丢。**（roleRequests.ts:90-91）
- 用户批准 A 的那一刻，B、C 就被记为 `role_given_to_other`。如果 A 在 15 秒内没有确认（CLI 被杀、后台负载高），A 结束为 `not_confirmed`，这个角色就空着，B、C 已经被拒，只能重新申请。
- 探针 S3 的结果：winner `granted`；对手 `rejected/role_given_to_other`；授予期间对手重新申请得到 `role_taken`；16 秒后 winner 为 `ended/not_confirmed`，两个终端的 role 都是 null。
- 对手在授予期间被拒是对的（holder 已把 granted 算作占用）。问题在于拒绝发生在"授予"时，而不是"确认"时。处理办法二选一：把对手的自动拒绝挪到 confirm 成功之后；或者如实写明并经用户认可。用户的原话是"批准其中一个，其余自动拒绝"，现在的实现字面上符合，所以挪到确认之后算设计取舍，应交构思主控或用户判断，不是缺陷修复。

**S3：`not_confirmed` 只是推导出来的，没有事件记录；用户也看不到"批准没有生效"。**（roleRequests.ts:56-57）
- 探针 S3 中，`not_confirmed` 相关事件为 0 条。审计记录里只能看到 decided(approved)，看不到这次授予已经作废。
- 界面上横幅只列待批准申请，侧栏只列已生效的主控。用户点了批准，结果什么也没出现，也没有任何提示。
- 修法：到期时用定时器写一条 `role_request_ended(not_confirmed)` 事件，并给界面一条提示。

## 3. 建议

1. **过期判定用墙钟。**（roleRequests.ts:52-57）`decided_at` 取自 `new Date().toISOString()`，判定时与 `Date.now()` 相减，两者都是墙钟。如果系统时间往回调（NTP 校时），已推导为 `not_confirmed` 的申请会退回 `granted`：role_taken 再次挡住别人，迟到的确认也可能成功。S3 改成写事件后，这个问题随之消失；否则应改用进程内的单调时钟期限。后台重启后，granted 会因终端不再存活变成 `terminal_gone`，这一点核对过，没有问题。

2. **e2e 检查 `unreceived_approval_ends` 依赖时序。** 申请方在批准后约 100ms 内关闭连接，结果是 `asker_gone`。如果晚于后台下一次轮询（200ms）才关闭，后台已经返回授予并清掉了 `asker.gone`，状态停在 `granted`，15 秒后变为 `not_confirmed`（探针 2：延迟 0/0.05/0.1 秒都是 asker_gone，延迟 0.3 秒是 granted）。这两种结果都是安全的，但这项检查在高负载下可能误报失败。另外，`approved-not-ended` 变异体是被这一段里的前置断言"后台没有出现待批准的申请"拦下的，不是被这项检查本身拦下的。

3. **申请编号用的是全局待批准列表的下标**（renderer.tsx:740、762），横跨所有项目。某个申请被撤回（比如 asker 断开）后，后面的申请全部改号，横幅行的位置也会移动。用户鼠标正移向"批准"时，按钮可能已经换成另一个申请的；同角色有冲突时，这一点会把本来想批准的那个自动拒掉。建议用稳定编号（例如按申请的事件序号），或者在列表变化后短暂禁用按钮。

4. **终端不在当前视图时，横幅只显示"一个终端（这个终端不在当前视图）"。** 同项目同 CLI 的两个申请无法区分，而这时又提示"批准其中一个，其余自动拒绝"，用户很容易选错。建议由后台下发终端名（或启动时间、工作目录），或者提供跳转到对应窗格的操作。"第 N 个窗格"用的是 `paneKeys` 的顺序，不一定等于布局上的视觉顺序；窗格放大时，被隐藏窗格上的标签也看不到。

5. 连接关闭时结算失败，现在复用 `setUserInputObserverStatus("failed")`，与第 695 行事件写入失败的处理一致，后台不会再退出。代价是用户输入记录器整体被标记为故障。我认为可以接受，但应在 RESULTS.md 里写明这个连带影响。

**核对后没有问题的：**
- 不同角色、不同项目都不受自动拒绝影响（S3：同项目 ideation 仍 pending，other 项目的 executor 仍 pending）。
- 两个批准同时到达：第二个返回 `request_not_pending`，被拒一方的 `a2a request` 返回 `role_given_to_other`。批准与拒绝同时到达，或先拒后批，都按到达顺序处理，两者互不影响（S4，3 种组合）。
- release 与 confirm 竞争：先处理 release 时，confirm 返回 `request_not_granted`，状态 ended，role 为 null（S5，5/5）。
- `all()` 的推导：rejected 和 ended 之后的事件全部跳过；confirm 只对 granted 生效；对手拒绝不会重复写；推导中没有发现状态回退，墙钟回拨的情况除外（建议 1）。
- 结算失败后后台继续服务（探针结束时 `daemon_alive: true`）。

## 4. RESULTS.md 必须写明的事实
- 批准后的状态是 `granted`，没有权限；确认后才是 `approved`。没确认的授予会推导为 `not_confirmed`，但**不写事件**，界面也没有提示。
- "批准生效但 agent 不知道"的窗口缩小到确认回执这一段，**没有消除**（探针 S2）。确认可以由同一终端里的别的进程凭 whoami 列出的 id 代发（探针 S1）。
- 自动拒绝发生在授予时：授予之后没确认，角色会空着，对手已被拒（探针 S3）。
- 过期判定依赖墙钟。
- `approved-not-ended` 是被前置断言拦下的。`unreceived_approval_ends` 依赖关闭时机早于 200ms 轮询。
- 界面编号是全局下标，撤回后会改号；本轮没有做界面实测（截图 ui-08 是作者提交的，我没有核对）。

## 5. 实际运行的命令和结果
运行目录为 /Users/luckye/Documents/Code/a2a，HEAD 是 17b5e4f89（src 与 6147b4678 相同）。本机负载约 12，以下各项没有出现超时。

| 命令 | 结果 |
| --- | --- |
| `python3 workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev05/green.json` | PASS，47 项，21 秒 |
| `--mutant grant-has-authority` | INCOMPLETE，`grant_needs_confirmation` 失败（role=ideation，call 放行），变异生效 |
| `--mutant rivals-left-pending` | INCOMPLETE，`granting_one_settles_rivals` 失败（rival 仍在等待），变异生效 |
| `--mutant approved-not-ended` | INCOMPLETE，前置断言"后台没有出现待批准的申请 ('proj','ideation')"失败（上一轮的 granted 没有结束），变异生效，但不是被具名检查拦下 |
| `--mutant foreign-owned-save` | INCOMPLETE，`other_terminal_draft_refused` 失败（card_save_next 为 None），变异生效 |
| `--revision 06276f2a8` | INCOMPLETE，第 13 项后的断言失败（批准后状态为 approved 而不是 granted），旧实现为红态 |
| 探针 `python3 /private/tmp/t121-rev05/probe/probe.py <repo> /private/tmp/t121-rev05/probe/probe-result.json` | S1～S5 结果见上文 |
| 探针 `python3 /private/tmp/t121-rev05/probe/probe2.py <repo> /private/tmp/t121-rev05/probe/probe2-result.json` | 授予后关闭时机测试，结果见建议 2 |

**没跑的：**其他变异体（pending-authority、no-withdraw、history-in-zdotdir、zdotdir-dropped、refusal-unrecorded、task-widens-scope、drafts-unowned）、T-107/T-109/T-111/T-118 回归、Electron 界面实测（编号、标签、多项目显示都只做了代码阅读）、墙钟回拨实验（只做了推理）。

所有测试日志和 summary 都在 /private/tmp/t121-rev05/ 下（green.json、mutant-*.json、red-06276f2a8.json、对应的 .log 文件、runs.txt、run.sh），探针脚本和结果在 /private/tmp/t121-rev05/probe/。仓库没有任何修改。