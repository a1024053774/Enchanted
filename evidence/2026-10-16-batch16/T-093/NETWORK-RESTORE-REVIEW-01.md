STATUS: FAIL
TARGET: e1177a02d5a5ffa8d636298a3ed4a065294aece0；基线 64c6456de2b7c0111628defce442d999a26734db

EVIDENCE:
- 审查前后 HEAD 均为冻结候选，受控文件无未提交差异；project-map status 两次均为 0 problems、0 stale。
- 独立原件在 `/private/tmp/t093-r16-review-ebfq0kdt/`。`node --experimental-vm-modules host-independent.mjs` 使用新随机 hostname、路径及请求体，实际 handler 配给定 transport：四场 PASS。两次输入分别得到 409／200，每次 transport 前已有持久化 request；错误 IP、错误 lookup hostname 均拒绝并记账，307 未触发第二次请求。没有实际网络调用。
- `python3 -B port-independent.py`：新增端口 1、442、444、65535、0 均以 `upstream_port_443_required` 拒绝；auth、OS 与私有目录分配边界均设哨兵，未触发。
- 作者现有 host 五场、port 五场、restore 三种身份及变异、counts-selection 十场均 rc 0。它们仅为 L1 补充证据，不作为独立 oracle 或原生验收。
- 独立新增 V 收据输入：缺 network_boundary、虚称 OS 主机过滤、被拒主机仍连接、缺 lookup 场次，均得到 INCOMPLETE；V 对未知权限、活 writer、错误主失败、错误候选和缺六场仍严格拒绝。
- 静态调用核对：`claudeForwarder.ts:80–119` 保留先记账再传输、固定目标、入站 Host 过滤与主机拒绝分类；`claudeLoginSession.py:104–112` 仅改 F 出站为 `*:443`，C／其余权限未放宽。`claudeLogin.ts:100,153` 和 README 明确披露 OS 不再限制主机。
- `panes.ts:252–277` 先核对 argv、task、版本和原生 session，再核对／补齐运行时规范身份并启动 PTY；原历史记录及完整 argv 保留。`:299–307` 仍以 processInfo 取得 leader；worker 提前拒绝。未确认新增异常吞并、fallback、重试、平行 API 或身份捷径。

FINDINGS:
- [P2] `evidence/2026-10-16-batch16/T-093/T093-OS-16.sh:17` — `verify-six` 在 macOS `/bin/bash` 下不能启动 V。第 16 行保留空 `flags` 数组，`set -u` 下展开 `"${flags[@]}"` 报 `flags[@]: unbound variable`。独立执行实际脚本、以 `exec` 函数哨兵阻断委派，得到 rc 1、零委派；verify-rehearsal／verify-counts 对照均成功。原件为 `wrapper-independent.json`。最小修正：用位置参数追加可选模式参数，去掉空数组展开；保持 V 的全部六场要求。

COUNTEREXAMPLE:
- 独立单处删除连接前 hostname 校验后，错误 IP 绕过 lookup，给定 transport 观察到一次连接；明确命中 `non-configured host must not start a connection`，不是环境错误或单纯非零退出。未改候选同输入零连接。
- 恢复检查中的缩短实际 PTY argv、删除已有身份一致性校验、固定 leader 三种坏实现均被业务断言拒绝。合法缺 executable_path 的旧记录正例仍保留。
- 实际 verify-six 交接反例失败发生在 V 启动之前，不能记为 V 已拒绝坏业务结果。

LIMITATIONS:
- 当前候选的 macOS profile 编译、F→443 正链及 F→非443 OS 拒连均未运行；旧编译红态只证明旧候选失败。
- T-096 原生 tracer、three、四故障、empty-reopen 七场均未运行；现有检查使用给定 PTY／进程边界，不能替代真实恢复验收。
- 未运行真实进程查询、sandbox-exec／编译器、CLI、daemon、服务、网络、auth、Keychain 或模型；未操作旧夹具、修改仓库或请求升级。没有整体 GO。

RULE:
- 本项未确认属于已重复的同类缺陷。可执行预防检查是在 macOS `/bin/bash` 下逐分支运行交接 wrapper，并用 `exec` 哨兵核对完整委派 argv；该检查应放在交接脚本检查入口，尤其覆盖不带可选参数的 verify-six。
