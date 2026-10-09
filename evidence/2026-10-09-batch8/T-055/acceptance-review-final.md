STATUS: PASS
TARGET: Synara `a2a@2330534b2cf906b9d8f0a0b643adb370683d7fe0`，基线 `6efac8432d7ae37e74b76e42d4e9fd3004d9a0e2`；证据 revision `a2a@3bf426fa535f897ddba0820b31ea68920dfad6bb`

EVIDENCE:
- 冻结核对：候选 HEAD、分支和 11 个冻结文件 diff 均稳定。
- 父修订红态：`red-entry-01.json` 的 `tools/list` 无 `a2a_raise`，面板返回 503；`permission-red-rev2` 退出码 1。候选 `round4/tools-list.json` 和 `panel-final.command.json` 分别证明工具出现、面板真实交互成功。
- 真实 Codex：`round4/unattended-observation.json` 显示 full-access、无 approval 活动，真实 MCP `a2a_raise` 成功；`reply-complete-native.json` 显示用户消息 `dispatchOrigin=user` 且 worker 收到答复。
- 身份与边界：伪造 `thread/threadId` 后，`after-replay-full.json` 仍绑定真实调用线程；unbound、inactive、invalid credential 分别被拒绝；`negative-state-unchanged.json` 证明 task/attempt/fence/events 未改变。
- CLI/HTTP：`boundaries/gate-{status,issues,events}*.json` 均严格解析且退出码 0，链条包含 issue → answer → delivered；membership 证据覆盖 200/409/400/403。
- 面板与消息：`panel-final.json`、三张截图和 `panel-final-answer-receipt.json` 证明标题、正文、blocking、回复框、发送按钮、阻塞优先及 sentinel 问题；`reply-oracle.json` 的实际消息逐字等于 spec 手写预期。
- 去重与恢复：`events-after-answer.json` 有一次 answer、一次 human_intervention；`after-replay-full.json` 重放前后 26 个事件、5 条记录、1 条用户输入均不变。
- P1 修复：`round4/ended-session-green.json` 在原生 archived 会话上保存 answer 后追加 `forward/session-ended`；`reclaim-archive-green.json` 证明重复 archive 后 reclaim 成功、current attempt 清空。候选对应代码为 `packages/a2a-gates/src/core.ts:545`、`apps/server/src/a2a/service.ts:249`。
- 既有证据：编排 18 项、恢复 9 项均无失败；server 68 项、web 4 项、typecheck、lint、fmt、membership 均通过。

FINDINGS:
- 无可复现的 P1/P2/P3 行为违约。

COUNTEREXAMPLE:
- 基线实现缺少 `a2a_raise`，真实 tools/list、面板和权限红态均拒绝通过。
- 空闲 turn、无 task、无效凭据均被拒绝；固定输出或忽略输入会被 forged-thread 与 sentinel 问题证据发现。
- 旧 ended-session 实现未追加 forward、旧 archive 实现重复发送 archive；两条红态均失败，修复后的绿态通过。

LIMITATIONS:
- 证据为隔离 dev server、Codex 0.162.0 和本地浏览器环境，不代表生产部署。
- unknown-delivery 证据使用真实 A2A gate/SQLite 加受控 native unknown 错误，证明核心分支处理；未证明真实 provider 自发产生该错误。
- `raise-permission.test.ts` 引用了生产 matcher/private handler，仅作辅助，未作为独立 oracle；独立 MCP/HTTP/真实 Codex 证据承担验收。

RULE:
- 不适用：本次没有重复性 finding。
