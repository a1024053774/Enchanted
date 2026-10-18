# T-093 单层 profile 重设计 01

**REALITY GATE: INCOMPLETE：单层部署方向已明确，转发层的网络权限边界待裁定。**
本文件是可审的设计，不是已实现、已运行或已获授权的 profile 清单；不代替最后的独立审查／门禁。

## 已确定的事实和授权

- 主控 #82 回传 [parent-profile-01.json](parent-profile-01.json)：父 PID 60365 在 H 下独占新建真实 HOME 新文件被 errno 1 拒绝，created=false、absent_after=true；两个清单 helper 继承 H；临时根已删除。
- 已继承 H 的 sandbox-exec 子进程 60700 不能再施加 C：exit 71、Operation not permitted、无 child 结果。第二层 C 没有生效，不能把它列为实际 profile。
- 主控 #82 已授权凭据复制独立于后续 profile：只做一次精确来源读取，不在受保护业务链里再读钥匙串。后续不嵌套 profile。
- 主控 #79／main c06a73179 的裁定 A 继续有效：OS 禁写整个真实 HOME；清单差异只报告，不能决定通过；其他断言不放宽。

已读回的实际进程只有本次 probe，不能为尚未启动的产品进程填造 profile：

| 实际 PID | 角色 | 实际 profile／结果 |
| --- | --- | --- |
| 60365 | probe 父进程 | H，真实 HOME 新文件拒写，errno 1 |
| 60637 | before 清单 helper | 继承 H |
| 60700 | 请求再次施加 C 的 sandbox-exec | 继承 H；C 请求以 71 失败，C 未生效 |
| 60702 | after 清单 helper | 继承 H |

R、F、新单层 C 业务进程和合成删规则变异都未运行。原 probe 的清单 5555→5555、无差异，pass_condition=false；没有把零差异当作 OS 保护的证明。

## 尚不能自行决定的矛盾

用户要求后续整条链只使用一个 profile，网络只允许本地转发端口。现有转发器与 daemon 同一个 Node 进程；claudeForwarder.ts 的 receive 在先写请求原件并 fsync 后，实际调用 http/https.request 连接 upstream_url。

若该 Node 也只能连接本地端口 P，它就不能连接真实上游 HTTPS，也不能连接另一个端口 U 的假上游。保留原约束时，转发调用只能失败；这不是再跑一次探针能消除的实现细节。
凭据准备的外部例外已获授权，**转发层的外部／独立 profile 例外尚未获授权**。不能把前者自动扩展到后者。

## 建议方案：按职责独立启动，每棵树最外层只施加一次

建议由执行主控／构思主控确认新增 F 边界。以下方案尚待批准，产品未按它修改。

| 阶段／进程 | 拟使用的实际 profile | 权限及限制 |
| --- | --- | --- |
| 凭据准备父进程、精确 security 子进程 | 独立阶段 R；不在 C 内施加 R | R 禁写真实 HOME、禁网络；仅此阶段允许所需 Security 服务。一次 `find-generic-password -s Claude Code-credentials -w 指定 login.keychain-db`；无枚举、无第二次预查、无自动换来源。副本只写私有 /tmp 根的 0600 文件，不输出内容 |
| 文件来源的凭据准备 | 同一独立 R 阶段 | 只读指定来源一次，只复制 claudeAiOauth；不复制设置、历史或其他认证对象；结束 R 阶段后不再读取原件 |
| 转发进程及其日志／清单 helper | 独立平级树 F，最外层一次 | F 禁写真实 HOME、禁止 Security；只读取私有凭据副本，逐条先记后转。需要额外上游外连；OS 可表达的具体目的地址限制需实测，不能静默采用更宽泛的规则 |
| 无模型假上游 | F 侧测试进程／同一 F 宿主 | 假上游另端口 U；仅测试所需本地连接，不接真实模型。CLI 的 C 不允许直连 U |
| 业务启动器、Gate CLI、daemon 父进程 | 业务树 C，最外层一次 | 禁写整个真实 HOME、禁止 Security、TCP 只到转发端口 P；保留既有精确 daemon Unix socket。原 controller_start 入口不变 |
| node-pty spawn-helper、zsh、版本检查、auth status、交互 CLI | 直接继承 C | 不再在 shell 或 execFile 外包 sandbox-exec；不在这里读原始 Keychain／auth 文件 |
| CLI 的原生 hook、tool、Bash、Node 子进程 | 继承 C | 同一 UserPromptSubmit／PermissionRequest／Stop 和身份／prompt／去重路径，不新增门禁 |
| ps、测试 clang、业务树辅助子进程 | 继承 C | 输出和所有运行数据在真实 HOME 外；不另套 profile |
| 事实脚本及其子进程 | 继承 C | 重数私有运行原件、读已收集的元数据摘要；不重新读取原始凭据，不自动批准模型调用 |
| 真实 HOME 前后元数据收集 | R/F 的受保护 helper；不在 C 新开更宽权限 | 仅四个既定范围的目录／stat 信息，清单可交给事实命令；不读 HOME 文件正文，差异全部保留、不作通过条件 |

R、F、C 是独立阶段／平级树，不是 H→C 或 C→F 的嵌套。需要写入的 state、私有 HOME、角色目录、工作区和报告均在真实 HOME 以外；不增加 repo/state/roles 的 HOME 写入例外。
启动器只在 exec 之前处理固定参数与 FD，进入相应 profile 后才做阶段工作；不留下无保护的后台监督进程。既有操作者不是新启动的受管进程，不重配用户现有会话。

## 需要明确列入授权的变化

1. **已授权：** 原始凭据读取移到业务 C 之前／之外，Security 可用仅限这一次精确读取；更安全的实现仍可让该独立 R 阶段禁止写真实 HOME和联网。后续 C/F 只能读取副本。
2. **待授权：** F 不属于“仅本地转发端口”的 C 树，具有转发所需上游网络权限；F 自身仍有 OS HOME 禁写和 Security 禁止。不能把整条链仍描述为一个相同 profile。
3. **设计边界：** 元数据 helper 放在 R/F 的受保护阶段，C 保留原 CLI 的真实 HOME 正文读取限制；需要的目录/stat 权限必须只为已批准清单范围，不把 CLI 的 HOME 读取权限整体放开。
4. **维持原权限：** C 的精确 Unix socket 是原生 hook／Stop 已有通道，不增加任意 TCP 或 Mach 通信。R/F/C 都禁止 HOME 写入；不用缓存／遥测排除来替代 OS 约束。

如果必须坚持整个转发层也与 CLI 共用同一个仅本地 P 的 profile，则本地转发不能实现原票要求的上游连接。另一条路是给全树增加上游网络权限，但 CLI 也会得到直连能力，改变调用计数的保证；这不是本方案建议或已获授权的动作。

## 授权后才进行的产品改动与验证

- 保留 ClaudeForwarder 的先落盘／fsync／失败和重试记录行为，将服务生命周期移出 C 的 daemon 进程；不能加一个保留未用的平行转发实现。
- 正常登录只消费 R 生成的私有副本和已启动的转发端点；删除业务路径内的 security/sandbox-exec 及 CLI 再套 profile，不绕过 controller_start/hook/Stop。
- 验证启动和结束的每个 PID、父子关系、profile 来源；实际 runtime 权限靠 OS 拒写／拒连反例证明，不靠环境变量自报。
- 真实 HOME 拒写继续只用不存在的唯一文件名，O_CREAT|O_EXCL|O_NOFOLLOW；不能覆盖既有文件。删规则变异选择合成 HOME，真正创建后立即删除、记录删除，并由同一业务断言拒绝。它不冒称已删除真实 HOME 规则做过写入。
- 新版完整链只连假上游，重数原件、比对独立上游、验证失败／重试和三个既有反例；清单差异保留但不决定通过。真实模型、真实上游请求仍为 0。

本轮没有启动这些新阶段、没有读 auth 或跑模型。当前只有设计与前次 probe 原件读回；F 边界明确获批前，不实施权限扩张，也不把某个无效单 profile 绿态当作完整能力。
