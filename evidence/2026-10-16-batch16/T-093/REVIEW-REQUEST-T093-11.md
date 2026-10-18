# T-093 daemon 拒绝原因留证交接 11

**INCOMPLETE：修复错误留证，pane_release 的实际拒绝原因仍需沙箱外重新取得；没有宣称完整链已修复。**
候选绑定 worker 最后一行 `T-093 FROZEN <完整 SHA>`。
诊断实现冻结为 d594057a9672e2b7441ca17c4e8632296927f1b4；[DAEMON-ERROR-REVIEW-01.md](DAEMON-ERROR-REVIEW-01.md) 对 L1 诊断留证给出 PASS，真实拒绝原因和 OS 复验仍为 INCOMPLETE。最终冻结仅补审查原件／文本摘要，运行命令使用最终 SHA。
task T-093 / attempt a1，worker s16-t093；受管 session 67f986cc-92e4-4089-9c22-802a1143b645，native session 01a14ae2-a3df-7731-a7b0-1b679b3bce95，launch launch-45148b6732394eccab3b21224b238513。

## 已确认

主控 #103：候选 4533ebeb7 的固定残留清理 PASS，t093-chain-e189ndt0 已删除，permission_changes=[]。
原件为 cleanup-07.json；不要再次执行该旧清理命令。

同候选的 primary 演练在 turns 阶段 pane_release 的布尔断言失败，未到主动 rehearsal_primary_probe。
请求数为 0，边界检查完成；隔离 HOME／源 HOME／夹具全部清理，cleanup_failures=[]，写入组已退出。
摘要和阶段原件为 rehearsal-01-primary-summary.json、rehearsal-01-primary.events.jsonl；原完整结果仍在 /private/tmp/t093-rehearsal-01-primary.json。
绿态与正式六场按约定未执行。

旧断言只保留 AssertionError 文本，没有保存返回的 error／details。daemon 的 event store 随夹具删除，无法从这轮原件恢复实际返回码。
本 worktree 的 Panes.release（workbench/src/panes.ts）检查 unknown、无 active／failed，然后 processInfo 核对前台身份；它没有 T-096 所述的屏幕就绪判定。
processInfo 执行 /bin/ps，而先前 X 下的 4755 ps 曾被拒绝。因此 ps 是一个有依据的嫌疑，但这不是本次 daemon 返回的事实，也没有据此改权限或身份核对实现。

## 本次改动与局部证明

只修改测试的错误留证：controller_start、pane_release、pane_dispatch、daemon_stop 的 not-ok 响应立即抛出命令对应错误。
error_summary.daemon_response 保存实际 command、ok、error、details；message 也保留 daemon.error。没有把它转换为另一种猜测的拒绝码。
pane_release 另外保存调用前后只读 status 与原返回值，包含 queued、active、writing、user_draft、failed 等当时事实。
所有字段仍由原 ChainEvidence 在写盘前脱敏／扫描；原始认证、操作凭据及变体不公开。主失败先落盘、独立 D 清理和退出核对逻辑保持原样。
没有自动重试 release、强制改状态、自动按键或跳过拒绝。

同一实际 release 调用代码块，用三种独立给定的 daemon 拒绝回复测试：initial_release_only、foreground_claude_required、orchestration_failed。
daemon-rejection-red-01 在旧代码上因丢失 error 字段而三项失败，green-01 三项通过，并验证 details 的合成凭据写盘前已脱敏。
chain-publication-green-05 继续通过五项主失败／清理检查。它们是 L1 合成回复，不能证明真实 daemon 本轮返回的是哪一个错误。
产品 src、门禁、全部 OS profile、fake CLI、原始边界／计数／凭据断言均未改变。

## 沙箱外先重跑 primary

沿用已有脚本、相同 OS profile 和严格停止条件，使用全新输出。不要运行嵌套 sandbox，不请求升级。

```sh
repo=/Users/luckye/Documents/Code/a2a-wt-t093
candidate=替换为本次完整冻结SHA
bash "$repo/evidence/2026-10-16-batch16/T-093/REHEARSE-CHAIN-01.sh" \
  "$repo" "$candidate" /private/tmp/t093-rehearsal-02-primary.json primary
```

预期的主动失败仍必须为 rc 2、INCOMPLETE、primary_failure=rehearsal_primary_probe、upstream_requests=2、cleanup_failures=[]、fixture_removed=true。
若仍被 release 拒绝，应得到 primary_failure=pane_release_rejected；请回传 error_summary.daemon_response 的 error／details 及 counterexamples.pane_release 的 before／after，停止后续绿态与六场。
这时原件已能区分初始状态拒绝、前台身份拒绝与执行异常；下一步只针对实际返回原因修复，不根据本次猜测扩展权限。
JSON、同名 .events.jsonl 和日志均保留，不覆盖 rehearsal-01。

只有 primary 达到预期并清理完整，才继续请求 10 的 green／独立核对及正式六场；应改用新的 rehearsal-02-green.json、rehearsal-02-check.json，正式链沿用尚未执行的 chain-07 新路径。
本请求不替代 submit、独立验收或集成，也不授权真实 CLI／auth／上游／模型回合。
