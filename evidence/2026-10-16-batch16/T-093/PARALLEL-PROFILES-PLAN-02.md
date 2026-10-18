# T-093 平级 profile 实施前核对 02

**REALITY GATE: INCOMPLETE。** 主控 #83 已明确转发层权限；新的 OS 组合未实测。这里不再请求转发例外，不把旧链的 PASS 当成新边界的通过。

GOAL：保留 controller_start／hook／Stop，转发进程独立于 CLI 链；所有业务进程由 OS 禁写真实 HOME，F 只能写自己的记录目录、只监听配置端口、只连配置上游、禁止 Security 与 fork；C 只连 F，凭据在此前精确读取一次。
NON-GOALS：不跑真实模型，不连接真实接口，不改全局配置、门禁或原审查报告；不新增 fallback。
ACCEPTANCE：完整假上游链与原反例仍需复验；另加 F 越界出站、C 绕过 F 的拒连反例；清单全部报告但不作通过条件；真实 HOME 拒写与合成删规则变异必须产生业务断言结果。

## 事实与当前未知

- observed：主控 #83 已确认 F 与 C 的独立 profile；精确凭据读取在链外只做一次。
- measured：parent-profile-01 的 H 拒写成立，嵌套 C exit 71；probe-10 的 CLI 可连接一个获准本地端口。
- inferred：独立应用 F/C 可消除嵌套失败；Apple 随系统的 `/usr/share/sandbox/com.apple.smbd.sb` 使用 network-bind／network-inbound 与 local tcp 过滤，但不证明本次更窄的 tcp4 组合已生效。
- unknown：F 的“单监听端口＋单上游端口＋只写记录目录＋禁 fork”组合能否让 Node 正常运行，以及 C 的拒连、子进程继承是否如要求生效。
- unknown：新产品路径尚未改造；当前 CLI 内层 sandbox-exec、daemon 内 auth／forwarder 生命周期仍是旧实现，不能按新权限验收。

## 最小可证伪探针

执行 [PROBE-PARALLEL-01.sh](PROBE-PARALLEL-01.sh)，只使用本地 IPv4 端口，无凭据、无模型协议。输入是冻结版本与一个全新 /private/tmp 输出路径。主控是 OS 实测执行者，worker 只写脚本、不请求升级。

| 进程／阶段 | 本次探针实际将施加的 profile | 操作 |
| --- | --- | --- |
| Python 初始准备 | exec 前固定参数／FD／临时目录准备；不做业务操作 | 不读 auth、不联网、不写真实 HOME；之后同 PID exec C，不留外部监督进程 |
| U/F/S/M 的短脱离 helper | 完成 setsid／fork 后，各自独立 exec 对应 profile 的 true，再退出 | 第一 helper 的 PID、退出码与 profile 单列；不是嵌套 |
| C 父进程 | 单次 C | 禁写整个真实 HOME、保留 HOME 读取屏障、禁止 Security、出站只到 F；负责检查与清理 |
| 合成 CLI 子进程 | 继承 C | 再验证真实 HOME 新文件拒写，以及不能直接连接已活跃的假上游 U |
| F 的 Python 前置检查→Node 端点 | 单次 F，同 PID exec 继承 | 禁写 HOME、只写 F 目录、只监听 P、只连接 U、禁止其他网络／Security／fork；验证越界端口与目录写入被拒 |
| U 的 Python→Node→Python | 单次 U，同 PID exec 继承 | 测试专用假上游；禁写 HOME，只写 U 目录，显式监听两个本地端口，无出站、禁止 Security／fork；只在本进程调用四范围元数据清单函数 |
| S 控制 | 单次 S | 禁写真实 HOME及合成 HOME，真实 HOME 新文件与合成新文件都应拒绝 |
| M 删规则变异 | 单次 M | 只删除合成 HOME 禁写规则，保留真实 HOME 禁写；独占创建后立即删除，要求 home_write_must_be_denied 业务断言拒绝它 |

U 的第二端口是“未配置地址”的活跃哨兵，只有测试专用 U 能监听它；F 和 C 均不能连接。另一个未使用端口验证 F 不能换端口监听。拒连／拒绑定必须是 EPERM 或 EACCES，ECONNREFUSED、超时或端口占用均不算通过。配置端口冲突直接 INCOMPLETE，不换端口重试。

每个实际 PID／PPID／进程组／profile、exec 阶段都写入结果。F/U 与 CLI 不构成父子链，端点被 reparent 后才视作独立。后台服务均脱离调用者进程组；正常退出和失败清理分开，端点另有 60 秒截止，防止 C 启动异常后永久遗留。

真实 HOME 写入只尝试不存在的随机唯一文件名，O_EXCL／O_NOFOLLOW；若 OS 意外允许创建，原安全函数立即按 inode/dev 确认所有权后删除并记录，业务断言仍失败。C 读屏障内的 absence 结果不能独立证明文件不存在，U 在相同 UID、受保护的只读元数据阶段再逐条确认 C 的路径不存在。

M 只在合成 HOME 写入。这证明断言可检出缺失禁写规则，并记录实际创建和删除；不证明删除真实 HOME 规则后的行为。Security 服务查询仅记录 Mach 返回码，不读取 Keychain 条目；无未受限查询对照，不能单靠非零返回码证明服务存在或拒绝原因。

PASS 条件是上述正例与拒绝、M 的业务失败、实际删除、进程清理和清单采集均成立。清单差异数量不参与 PASS。任何 profile 编译失败、非权限类连接失败、业务断言失败或清理不确定，都保留 INCOMPLETE；不通过放宽规则修复。

## 后续产品改动

探针结果回来前不把新的 profile／生命周期组合写入产品路径。这遵循 reality-first-engineering 的“外部边界未知先做最小探针”，不是权限未授权。
若 PASS，沿一个保留在产品里的 Tracer bullet 改造：链外精确复制到私有 HOME，配置固定 F 端点与私有描述文件；F 独立受保护运行；C 最外层一次，daemon／PTY／hook／事实子进程继承；移除现有内层 sandbox-exec 和 daemon 内原始 auth 读取／转发服务。随后用原 controller_start 入口完成全链、旧三反例、新拒连与删规则变异复验。

本探针不证明产品已经可用，也不证明真实域名 DNS／TLS 或真实登录的完整新链。真实上游和模型请求保持 0；命名上游的 OS 地址表示仍须在产品实现中明确处理，不能静默放行任意地址或自动选 fallback。
