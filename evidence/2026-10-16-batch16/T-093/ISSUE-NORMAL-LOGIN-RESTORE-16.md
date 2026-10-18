# 新增组合边界：普通 daemon 直接恢复正常登录记录

**历史 NO_GO：该路径在 8771ba58d／67ffe60ad 不可集成。主控 #125 已裁定正常登录记录不续接；当前增加版本／PTY 前的明确拒绝，局部红绿见 [NORMAL-RESTORE-17.md](NORMAL-RESTORE-17.md)。完整受保护恢复另票处理，不扩大 T-096。**
这是 worker 在限定审查结束后追加的给定边界检查，不是 NETWORK-RESTORE-REVIEW-01 的独立 finding，也不是已执行真实 CLI／OS 后观察到的泄漏。
后续一次针对性独立复核已用全新 SQLite／native session 记录确认相同 P1，原文见 [NETWORK-RESTORE-REVIEW-02.md](NETWORK-RESTORE-REVIEW-02.md)。仍为给定进程边界证据；缺 session 的负例也会先执行版本命令。

## 观察

- workbench/src/transport.ts:70–74 从普通入口重启 daemon，会剥离 A2A_* 并直接 spawn daemon.ts，没有 R/F/D/C 启动路径。
- daemon.ts:427 无条件调用 panes.recover；panes.ts:238–277 只核对 controller/Claude 等元数据、argv、版本、session 与规范身份，然后直接 PTY spawn。没有根据 authentication=isolated normal login 要求恢复原受保护 profile 上下文。
- 正常登录启动记录明确保存该 authentication 标记；claudeLaunch.ts:90–98 的 env／shell_argv 本身不携带 OS profile。正常首启由 R/enter_cli 在外层施加 C，权限来自继承，不能只靠复制 env 保留。
- 若正常登录的私有 HOME／session 仍存在（例如清理尚未完成或失败保留），普通 daemon 的恢复可通过上述文件校验。D 一般会删除私有根，但这个时序／保留条件不能作为恢复权限的保证。

## 给定边界复现

原件 normal-restore-boundary-01.json；可复现脚本当前在 /private/tmp/t093-r16-normal-restore-boundary.mjs，基于同一 test_t096_restore 的实际 recover／SQLite/native 文件／给定 PTY 与 processInfo。
只将 ideation 的记录标记为 isolated normal login，给定普通 daemon 上下文（无外层 session），其余版本、session、canonical identity 均合法。
在 recover 返回后，PTY spy 已记录该正常登录记录的启动；断言 normal_login_restore_must_not_spawn_without_outer_profile 失败，true !== false，rc 2。
没有启动真实 CLI、普通 daemon、OS profile、网络或 auth，也没有把 syscall 的真实权限当作已测量。这个信号证明实际恢复路由缺少前置条件，不能冒称已观察到真实 HOME 写入。

独立反例的小型原件已按原字保存为 normal-independent-review-16.mjs／json；不保存其 SQLite／整套夹具。脚本固定审查时的源路径和版本标签，最终归档候选的产品源与 8771ba58d 相同。重放必须先复制到全新临时目录，避免在 evidence 旁边创建夹具：

```sh
probe_dir="$(mktemp -d /private/tmp/t093-r16-review-replay-XXXXXX)"
cp evidence/2026-10-16-batch16/T-093/normal-independent-review-16.mjs "$probe_dir/normal-independent.mjs"
node --experimental-vm-modules "$probe_dir/normal-independent.mjs"
```

预期 rc 2、FAIL，normal-surviving-session 到达版本／PTY，而 fake-control 正常恢复。缺 session 的正常登录对照仍到版本边界后才失败。以上均为替身调用，不是外置 OS 演练；失败夹具保留在该临时目录，不作为整票通过证据。

## 建议与未授权部分

最小安全选项是本票先明确把不能保留受保护上下文的正常登录恢复标为“未恢复”，拒绝在普通 daemon 下执行 CLI（包括版本命令）；完整重建 R/F/D/C 生命周期由重开的 T-096／后续设计处理。
另一选项是在重开的 T-096 统一补完整受保护恢复，本候选在此之前不集成。不能通过重新复制 env、固定 leader、继承普通 daemon 权限或自动补登录解决。
上面是裁定前的建议；主控 #125 已选择先明确拒绝正常登录恢复。worker 仅实现该拒绝，没有增加完整恢复生命周期。F 网络／规范身份修复与 Bash wrapper 修正可独立审查；七项现有假 API 原生回归不覆盖本问题，故另保留本问题的拒绝反例。
