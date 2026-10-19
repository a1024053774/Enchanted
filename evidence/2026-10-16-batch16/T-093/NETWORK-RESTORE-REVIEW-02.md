STATUS: FAIL
TARGET: 8771ba58d71a3fc025b09e32c45096b39858572e；基线 e1177a02d5a5ffa8d636298a3ed4a065294aece0；范围为一次 targeted recheck：原 P2 修正及明确追加的正常登录恢复边界。

EVIDENCE:
- 冻结前后 HEAD 一致，受控文件无未提交差异。产品 src 与 V 判定文件相对基线均无变化；project-map status 为 0 problems、0 stale。
- 原 P2 修正 PASS：`T093-OS-16.sh:15–18` 已改用位置参数。实际 `/bin/bash` 七分支检查 rc 0；独立新增随机文件名、含空格路径及完整六个 receipt 参数，verify-six／verify-rehearsal／verify-counts 的完整委派 argv 均精确符合合同。verify-six 未添加模式参数，V 六场要求未减弱。
- 新证据位于 `/private/tmp/t093-r16-review-targeted-ao242l5q/`：`wrapper-author.json`、`wrapper-sentinel.json`、`normal-independent.json` 及对应脚本。
- 独立恢复探针使用全新 SQLite、原生 session 文件及实际 `Panes.recover`，所有 subprocess／PTY 边界均由替身提供。普通 context、合法版本／身份、`authentication="isolated normal login"`、session 存在时，依次观察到 `cli-version`、`pty-spawn`、给定 process snapshot，随后写入 `pane_restored`；历史记录未改变。
- 对照：同类正常登录记录缺 session 时，仍先调用版本边界，再以 `restore_session_missing` 拒绝 PTY；假 API 正例正常恢复。因此缺 session 不能保证 CLI 从未在普通 context 执行。
- 直接路径为 `gates/cli.ts:210–211` → `transport.ts:70–75` 普通 spawn → `daemon.ts:427` recover。`daemon.ts:436–441` 只在环境变量存在时核对 session，不要求它存在。正常首启的 C 来自 `claudeLoginSession.py:302` 的外层 sandbox-exec；`claudeLaunch.ts:90–98` 保存的 env／argv 不施加 OS profile。`claudeLoginProcessTrace.ts:4–8` 只记录继承标签，也不施加保护。

FINDINGS:
- [P1] `workbench/src/panes.ts:259`、`:273` — 已上报的正常登录恢复边界缺陷得到独立确认。在普通启动者未受 C 保护、旧正常登录记录和 session 仍可读取的条件下，recover 无正常登录保护前置条件，先执行 CLI 版本命令，随后直接提交 PTY 启动。直接调用链中未找到能重建或强制要求 R/F/D/C 的保护；首次启动时的 `ClaudeLogin.prepare` 不覆盖此恢复路径。该路径 NO_GO。修正责任在恢复入口，必须在首次 CLI 执行前处理受保护上下文；拒绝恢复还是重建完整生命周期，继续交主控重开 T-096／裁定，本审查不选择策略。

COUNTEREXAMPLE:
- 原 Bash 空数组红态保留；修正后的同类 argv 哨兵及完整六收据输入均通过。
- `node --experimental-vm-modules /private/tmp/t093-r16-review-targeted-ao242l5q/normal-independent.mjs` 返回 rc 2；业务合同“普通 context 不得启动正常登录恢复”被实际版本／PTY 调用记录否定。不是缺依赖、超时或空集合导致失败。

LIMITATIONS:
- 新恢复证据为 L0／L1：证明调用路径与缺失前置条件，未运行真实 daemon、CLI、OS profile、PID 查询、网络、auth、Keychain 或模型；没有宣称观察到真实 HOME 写入或实际越权联网。
- OS profile 编译、443 链及非443 OS 拒连，T-096 原生七场仍未运行；原七场假 API 合同也不能覆盖本次正常登录组合风险。
- 原 P2 已关闭；新增阻点仍待主控裁定。未修改仓库或旧夹具，不给整体 GO。

RULE:
- 未确认该问题属于已重复的同类 finding。应由 T-096 的恢复验收加入“正常登录记录＋普通 context”反例，在版本执行和 PTY 两个边界观察拒绝；后续真实保护证据仍须来自获批的原生入口。
