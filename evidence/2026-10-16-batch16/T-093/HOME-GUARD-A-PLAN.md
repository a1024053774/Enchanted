# T-093 裁定 A：进程保护边界与待核对事实

**REALITY GATE: INCOMPLETE。** 清单判定已按裁定修正；所有产品进程的 OS 禁写尚未落地，先等父／子 profile 兼容性探针。不得把本表的计划当作运行证据，也不得用旧完整链 PASS 验收裁定 A。

GOAL：由 OS 禁写整个真实 HOME，覆盖本轮应用入口、父进程及全部后代；新增拒写反例和删规则反例；清单只报告事实。
NON-GOALS：不跑真实模型，不改全局配置、不动现有用户会话、不新增策略引擎，不取消 CLI 的既有网络或 Security 限制。

## 裁定依据

main c06a73179 的 T-093 票“裁定”节，用户选择 A，选项原文：

> 由 OS 沙箱强制禁止写真实 HOME，再加一个试图写真实 HOME 被拒的反例。前后清单照实报告但不作通过条件。证明的是“写不进去”，比“碰巧没写”更强。

交接来源为主控 #79 与 20261018T004018Z-ideation-answer-001。当前 worktree 的地图禁止由 worker 改写，因此引用该 main 版本及本次用户消息，不自行改票。

## 每个进程的 profile

H 表示拟由最早入口施加的 `(deny file-write* (subpath 实际HOME))`，不设 repo／state／roles 写入例外。
C 表示原 CLI 的额外读权限、Security Mach、仅本地转发端口与精确 Unix socket 的限制；R 表示现有精确 Security 读取的只读／无网络／禁 fork 限制。
这里的实际 HOME 取 OS 账户信息，不得拿合成认证源 HOME 或隔离 HOME 冒充。源码可以读取；任何需要写入的运行数据、state、role 根、报告及工作区须在实际 HOME 以外，不自动搬移现有数据、不放宽写入例外。

| 进程／组件 | 当前实现由本产品施加的 profile | 裁定 A 下必须达到的 profile |
| --- | --- | --- |
| 最早应用启动器／复验父进程 | 现有 Python／shell 复验父进程没有统一 H | 同 PID exec 进入 H，再做应用工作；不能留下无保护的后台监督父进程 |
| 原生 Gate CLI 操作客户端 | 没有统一 H | H，仍调用唯一原有入口，不改 gates |
| Node daemon | 没有统一 H | H |
| 本地转发器 HTTP server | 与 daemon 同一个 Node 进程，没有统一 H | 与 daemon 同一个 H |
| 无模型假上游 | 与测试宿主同一 Node 进程，没有统一 H | 测试宿主 H |
| 私有文件／清单 Python helper | 没有统一 H | 继承 H，inventory 只读元数据，auth 只读指定来源 |
| 精确 Keychain 的 security 子进程 | 现有 R | H 与 R；不枚举其他条目，不放宽 Mach |
| CLI --version／auth status | 现有 C；其配置 HOME 与实际 HOME 在合成测试中不是同一目录 | H 与 C，实际 HOME 禁写不得被 C 的其他规则抵消 |
| node-pty spawn-helper／启动 shell | 进入 C 之前没有统一 H | 从宿主继承 H，再进入更严格 C |
| 交互 CLI | 现有 C，包含 repo／state／roles 写入例外 | H 与 C，真实 HOME 整体禁写；原端口／Security／认证约束保留 |
| CLI 产生的 shell／tool／原生 hook Node | 继承现有 C | 继承 H 与 C |
| daemon 的 ps 等辅助命令 | 没有统一 H | 继承 H；真实执行仍由主控在沙箱外安排 |
| 测试 clang、Git 导出／复制／清理 helper | 没有统一 H | 从最早复验入口继承 H，输出到 /private/tmp |
| 事实命令 Node 及它的后代 | 独立调用没有统一 H；链内继承其父环境 | 从保护入口／已保护父进程继承 H；不只保护被测 CLI |
| 前后清单 helper | 当前外层父进程未统一 H | 继承 H；差异不作通过条件，但采集失败不能补称成功 |

既有操作者／开发 agent 不属于本轮新启动的应用进程树，不重新配置它们的权限或会话；本轮不启动 Electron，也不外推到未运行的 UI 进程。
这里所说的 bootstrap 只做参数／OS 账户与描述符元数据检查，使用隔离 Python 模式且不加载用户 site；在创建 /tmp 夹具、应用、auth、模型或 helper 工作前 exec 进入 H。
已打开的可写描述符不会被文件沙箱自动撤销。探针拒绝指向真实 HOME 的 stdout/stderr 常规文件、关闭其余额外 FD，stdin 改为 /dev/null；运行日志应在 /private/tmp。

## 为什么先做小探针

observed：安装的 Apple SDK sandbox.h 注释说明，已在 sandbox 的进程再次 sandbox_init 会报错；同机 sandbox(7) 又说明新进程继承父沙箱、已打开 FD 不随规则自动撤销。
来源为 /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/sandbox.h、/usr/share/man/man7/sandbox.7。F_GETPATH=50 来自同 SDK sys/fcntl.h。
unknown：sandbox-exec 当前实际实现能否在 H 后代中施加现有更严格的 C／R，不能仅由这些旧 API 注释推定。若不能，不能以移除 C 的网络或 Security 规则来“跑通”。

最小可证伪探针为 [probe_t093_parent_sandbox.py](../../../workbench/tests/probe_t093_parent_sandbox.py)：

1. 最早 Python bootstrap 同 PID exec sandbox-exec H；不留无保护监督进程。H 下的父进程与两次 inventory helper 记录各自 PID／profile。
2. H 下尝试独占创建真实 HOME 的全新 `.a2a-t093-deny-随机值`，必须 EPERM／EACCES 且文件未出现。不会打开既有文件；若意外创建，只删除自己以 inode/dev 核对过的独占创建，记录 created/deleted。
3. H 子进程请求 C-probe：保持真实 HOME 禁写、禁网络、禁 Security Mach，另禁止写合成 HOME。合成 HOME 拒写证明附加规则确实生效，不能仅靠继承的 H 拒写误称第二个 profile 已施加。
4. 若叠加可用，再以相同其他约束做合成 HOME 的对照和删规则变异。变异只删合成目录禁写，真实 HOME 规则仍保留；必须实际独占创建合成文件、立即删除，并由 `home_write_must_be_denied` 业务断言拒绝。
5. 真实 HOME 的四范围清单仅在 H 下读元数据，完整列表只在内存比较；记录条目数和全部差异，pass_condition=false，绝不因差异改失败。

选择合成 HOME 做变异，避免主动移除真实 HOME 的保护。它证明反例能在该合成路径检出缺失禁写规则，并证明创建／删除确实执行；**不证明移除实际 HOME 规则后实际 HOME 会写入成功**。实际 HOME 只有保持规则下的拒写正例，不伪造这个未做的反事实。

若 nested_profile_unavailable／did_not_enforce，保持 INCOMPLETE，先交主控处理约束冲突，不写产品的父层保护实现、不改用更宽松的 CLI profile。若 PASS，才把 H 启动入口接回同一 controller_start/hook/Stop，并重新取得整个受管进程树的证据。

## 已完成与未完成

- 清单判定已改：旧实现遇到差异且 child=0 会退出 2；新实现对有无差异都保留 child 退出码，失败 child 不变。inventory-policy-red-01／green-01 保留有效红绿态，属于提供元数据／子进程结果的 L1 分类检查，不是 OS 沙箱证据。
- parent-probe-safety-02 为合成路径的 3 项安全检查：独占创建后删除、遇到既有文件拒绝且内容保留、无 guard 的合成写入命中业务断言。没有真实 HOME 写入尝试、没有子进程或 OS profile 运行。
- 真实父层 H、H/C 兼容、实际 HOME 拒写、OS 下删规则变异，以及产品全进程树保护，均等主控运行新探针。旧 EVIDENCE-RECHECK-02 完整模式已停止，不能对新合同给出 PASS；原 native 完整链也不能作为 A 的验收入口，尚无全进程保护证据。
