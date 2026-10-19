# T-093 探针结论与产品落地边界（2026-10-17）

探针范围 PASS，来源为主控 #72 对 probe-10 的读回；产品交付仍为 INCOMPLETE。
probe-10 的三个事实已成立：复制的登录凭据在隔离 HOME 被识别；CLI 采用自定义本地地址；本地请求携带该凭据。
本地记录两个 POST /v1/messages，均含 messages、bearer 匹配，假上游均回 400；真实上游、凭据扫描、清单差异均为零，隔离目录已删除，没有业务按键。

必须保留的边界：

- 成功依赖隔离配置中生成的 hasCompletedOnboarding 和唯一工作区项目信任状态。这两个字段是 2.1.302 的内部状态；正常登录模式固定该版本，换版本先重新核对，不能静默沿用。
- onboarding 预检不经过 BASE_URL。静态代码并发构造 api.anthropic.com/api/hello 与 platform.claude.com/v1/oauth/hello 两个候选；不能把它说成固定一次请求。产品必须准备完成状态，保留版本前检及预检旁路观察；若预检仍触发，事实报告单列，不能将转发层计数冒充全部流量。
- 两个本地请求而非一个，按主控结论说明 400 后存在重试。转发层逐次接收、逐条先记再转，不做自己的静默重试，不把同一输入的多个 HTTP 请求合成一条。
- 2 次假上游请求不是真实模型回合。产品绿态也只连接假上游；本票不执行真实模型回合，合入后仍等用户另说开工。

产品仍走 controller_start、既有 UserPromptSubmit/PermissionRequest/Stop 及转交路径，不另起门禁或绕过身份检查。
正式 hook 需要派生子进程并连接既有 daemon Unix socket；诊断探针的禁 fork 不能照搬成会阻断 hook 的产品权限。
正常模式会保留该进程及 IPC 能力，禁止访问真实全局 Claude 配置/Keychain、禁止 CLI 直接外连，只允许本地转发器和精确 daemon socket。
仓库与任务本来的文件权限仍按既有 CLI/manual/门禁路径运行，不把这些项目操作描述为“整个真实 HOME 不可读写”。事实清单范围及真实 HOME 路径引用照实报告。

Tracer bullet：先用合成凭据、确定性 PTY 客户端和独立假上游穿过唯一 controller_start/hook/Stop 链，再补失败/重试/清理及三个反例。
不读取或修改真实全局配置，不跑真实 CLI 或真实凭据的本地验证；需要沙箱外的真实依赖核对写成脚本交主控。
