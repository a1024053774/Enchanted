## T-121 第 7 轮复审（候选 7 = 48a4f130b，对比 85c775817，只看 workbench）

**结论：可以合并，没有阻塞，没有应修。** 本轮声明的改动都成立。有 3 条建议：一处测试覆盖缺口（已用变异体证实），一处注释说错了，一处界面仍会误导。仓库没有任何修改，`git status --short workbench` 为空。产物都在 /private/tmp/t121-rev07/。

### 逐项核对
- **S1，同一终端再次申请后不再显示失效提示**（sidebar.ts:198-201）：成立。green 中 `void_notice_cleared_when_terminal_asks_again` 通过；stale-notice 变异体被抓到。
- **asker_gone 作废的授予也提示**：成立，没有误伤“待批准撤回”。
  - 待批准申请撤回时只写 ended，`decided_at` 为 null（roleRequests.ts:42-48），被 `decided_at !== null` 筛掉。
  - `asker.gone` 只在 `role_request` 等待期间挂着，返回后在 finally 里清除（daemon.ts:197-213）。所以已批准（approved）的角色不会被记成 asker_gone，也就不会被误报为“没有生效”。
  - 探针实测：unreceived 循环刚结束时，提示只有最后一条 asker_gone 授予（id 8c8fb5e6…，带 decided_at）。之前 3 次待批准撤回和前 2 次授予都没有出现。
- **授予等待确认时显示“已批准，等待确认”**（renderer.tsx:756-758）：成立。granted 行没有编号也没有按钮；窗格框和“申请 N”标签只按待批准列表编号，两者不会混。
- **类型与运行时字段**：一致。`granted_role_requests` 用的是 requestView；`unconfirmed_role_requests` 多带 `decided_at`，筛选后一定非空，与 `(RoleRequest & { decided_at: string })` 对得上。
- **定时器回调**：`all()` 和 `store.event` 都包进了 try/catch。
- **按钮暂停**：改为 useLayoutEffect，成立。
- **README**：措辞与实现一致。

### 阻塞
无。

### 应修
无。

### 建议
1. **“asker_gone 也提示”没有测试守护。**（sidebar.ts:199；workbench/tests/test_t121_role_request_e2e.py）我写了一个变异体 `asker-gone-unnoticed`，把 `['not_confirmed', 'asker_gone']` 改成 `['not_confirmed']`，全部 48 项检查仍然 PASS。原因是 green 只在 b 再次申请之后才看提示，这时 asker_gone 那几条已经被“同终端再次申请”的规则隐藏了。建议在 `unreceived_approval_ends` 之后断言提示恰好是最后一条 asker_gone 授予（探针已证实实现会给出这个结果）。
2. **catch 里的注释说错了，处理也和连接关闭时不一致。**（roleRequests.ts:91-93）
   - 注释写“授予在终端关闭前一直没有权限”，但 `confirm()` 只检查 `state === "granted"`（roleRequests.ts:100）。到期事件没写进去时，15 秒后迟到的确认仍会让角色生效。
   - 连接关闭时的结算（daemon.ts:653-659）还会调用 `gates.setUserInputObserverStatus("failed")`，这里只打 console.error。
   - 只在 SQLite 写入失败时才会触发，所以不是阻塞。建议把注释改成符合实际，或者让 confirm 也按 15 秒拒绝。
3. **授予期间对手的“批准”按钮仍然可点。**（renderer.tsx:756-758 与 776-777）granted 行写着“届时仍可批准”，但对手那一行的按钮没有禁用，点了只显示原始错误“批准没有生效：Error: role_taken”（renderer.tsx:606）。review-06 建议 1 的后半没有处理。
4. **“再次申请”是按墙钟时间比较的。**（sidebar.ts:200）`Date.parse(requested_at)` 遇到墙钟回拨，后来的申请时间反而更早，旧提示就不会隐藏。`all()` 本来就按事件 seq 排序，改用顺序比较更稳。只影响显示。

### 实际运行的命令和结果
运行目录为 /Users/luckye/Documents/Code/a2a，HEAD 是 48a4f130b，本机负载约 2.4。

| 命令 | 结果 |
|---|---|
| `python3 workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev07/green.json` | exit 0，PASS，48 项检查，`shown_as_granted=[first]`，`notice=[first]` |
| `… --mutant stale-notice --summary /private/tmp/t121-rev07/mutant-stale-notice.json` | exit 1，INCOMPLETE，变异被抓到，但失败的是更早的 `grant_needs_confirmation`（提示有 4 条，多出来的 3 条是旧的 asker_gone 授予），没有跑到专门的 `void_notice_cleared…` 检查 |
| `… --revision 44220954e --summary /private/tmp/t121-rev07/rev-44220954e.json` | exit 1，INCOMPLETE，`grant_needs_confirmation` 失败（`shown_as_granted=[]`），父版本为红态 |
| 探针 `/private/tmp/t121-rev07/probe/t121_probe.py --mutant asker-gone-unnoticed`（测试副本，ROOT 指向本仓库，只新增一个变异） | exit 0，PASS，48 项检查，说明存在建议 1 的覆盖缺口 |
| 探针 `/private/tmp/t121-rev07/probe/t121_probe.py`（green 加一处快照） | exit 0，PASS；asker_gone 提示只显示最后一条授予，granted 为空 |
| `node /private/tmp/t121-rev07/parse.mjs`（在内存里用 vite 的 transformWithOxc 转换 renderer.tsx） | ok，只证明语法正确，不是类型检查 |

### 没跑的
- TypeScript 类型检查：本机没有 tsc，也没有 tsconfig。
- 渲染端构建、Electron 界面实测和截图。
- 其他变异体，以及 T-107、T-109、T-111、T-118 的回归。
- 墙钟回拨实验。
- 定时器写入失败的注入实验：建议 2 的迟到确认只读了代码，没有实测。

日志和 summary 在 /private/tmp/t121-rev07/（green.*、mutant-stale-notice.*、rev-44220954e.*），探针在 /private/tmp/t121-rev07/probe/。