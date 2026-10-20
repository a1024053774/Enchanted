# T-110 第一轮审查修复

INCOMPLETE。针对 `c5ac40c0b4cf60c30407af1a00953a297eb55005` 的 F1 已修改；本地断连红态与修后合同已取得，真实入口的扩展复验及独立复审待主控执行。前一候选的正常、禁用场景虽然 PASS，独立审查仍为 NO_GO，不据此关闭 F1。

修复只在现有 NotificationCenter 增加 `invalidate()`：清除 active 与 waiting，保留 seen。`a2a:sidebar` 的读取抛错或 `ok:false` 时，使同一个状态目录的所有窗口所用中心失效并重算 Dock，再抛出原始读取错误。不返回成功快照、不增加重试，不改 renderer、panes、启动参数或 T-108 的可信度判定。

证据：

- `review01-disconnect-red.json`：在修改生产代码之前，扩充后的真实 main/preload IPC 合同在 c5ac40c0b 上因 `Disconnected unknown state must clear Dock badge` 失败，实际 1、期望 0。
- `review01-disconnect-green.json`：相同合同 PASS；同时覆盖传输异常原对象传出、后台拒绝原原因、失败只请求一次、前后台变化不复活旧计数、恢复后不重复同一问题、同状态目录的另一窗口共享去重结果。原有 IPC 拒绝检查未减。
- 第一轮独立探针 `/private/tmp/t110-review-local-05.json` 的 `disconnect_probe` 也证实原候选业务失败；本修复不改写它。
- 真实入口新增：有效待答时刷新／重载保持一条；后台断开本次夹具的真实 socket 后通知和角标清除，读取失败可见；断连中刷新／重载保持无提醒；恢复同一个原生问题后刷新／重载仍不重复；仅新可信读取可恢复待答计数；最后继续通过原 PTY 作答并检查原有回执。
- `run_t110_notifications.py` 另用 c5ac40c0b 的原版 main.ts 与 notificationCenter.ts 重跑相同场景，只有在上述断连业务断言失败且实际 badge 为 1 才认作红态；依赖／启动错误不算红态。

权限表述：当前固定版本 Electron 43.4.1 的 `app.dock.setBadge` 不会主动请求权限；不能证明在拒绝通知权限时角标一定可见。测试只通过 `app.dock.getBadge()` 核对标签值，没有修改系统权限。继续使用该 API，没有换成其他通知路径。

主控重跑：

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-04.json
```

四个运行依次为隐藏通知坏变异、c5ac40c0b 的断连坏候选、修后正常闭环、修后禁用通知。新运行的所有夹具集中在 `/private/tmp/t078-2-t110-*`，以满足既有隔离根校验；不复用被清理的 t108／t109／t111 临时目录。模型、供应商调用及截图均为 0。

额外静态发现已按 worker 规则上报 `20261020T133157Z-worker:s18-t110-issue-001`：旧审查脚本的真实入口根目录预计不满足现有原生隔离根校验。没有执行原脚本的真实入口、没有改审查原件或产品允许范围。
