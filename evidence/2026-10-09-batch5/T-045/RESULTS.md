# T-045：用量与限额显示失败调查（2026-10-09）

**诊断交付：PASS；T-045 的最终用量显示：INCOMPLETE。** 真实日志、DNS 查询、共享源码边界探针与真实 batch 入口的假凭据复现共同确认：三个 provider 的用量请求被保留地址安全检查拒绝。未发现第二个导致当前用量报错的已证实原因。用户已明确“不改变网络配置，如果是这个原因就算了，看看是否有其他原因”。本次按该决定保留现状，没有产品修复；正式界面的通过证据尚未取得，T-045 保持 open。

## 已确认的原因

`workbench-launch.log` 中 Codex、Claude 的真实异常是：`Outbound destination resolved to a private, local, reserved, or invalid address.` 截止 2026-10-09 04:40:16 UTC，该日志累计包含 Codex 617 条、Claude 616 条用量端点不可达警告；没有其他 provider-usage 消息类别。只归档这类不含凭据的白名单摘录，没有复制完整生产日志。

同次只读 DNS 查询得到：

| Provider | 用量域名 | 系统解析结果 |
| --- | --- | --- |
| Codex | `chatgpt.com` | `198.18.0.79` |
| Claude | `api.anthropic.com` | `198.18.0.67` |
| Cursor | `api2.cursor.sh` | `198.18.2.73` |

生产调用链是：用量读取 → `providerUsage/http.ts` 的 `fetchJson` → `outboundHttp.request` → `resolvePinnedAddress` → `assertPublicIpAddress`。用量请求显式要求 public address；共享策略明确阻止 `198.18.0.0/15`。地址检查发生在创建 HTTP/TLS 请求之前。系统解析结果与常见代理 fake-IP 模式一致，但本次没有读取代理配置或核实代理产品；能直接证明的事实是保留地址被安全层拒绝。

这不属于工作台未继承 HOME、凭据路径不存在或端点 HTTP 401 的同一分支。命令行能收到 HTTP 401 只能说明另一套 HTTP 客户端可以发出请求，不能证明 Synara 的地址安全检查会放行。Codex、Claude 的真实日志已直接确认该路径；Cursor 生产代码的 catch 不记日志，需以相同解析结果和离线调用链证据判断，不能把 Codex 的警告冒称为 Cursor 的生产日志。

聊天和用量读取是分开的路径。聊天正常不能排除服务端独立用量 HTTP 层的失败；本次也没有为诊断再次调用模型。

依据：[inspection-01.json](inspection-01.json)、[source-excerpts.txt](source-excerpts.txt)。

## 其他原因排查

| 检查 | 结果与边界 |
| --- | --- |
| 工作台启动环境 | 启动器、source desktop 环境和 backend 环境均保留已有 HOME、PATH 及凭据目录变量，`SYNARA_HOME` 只控制应用数据目录。只读 worker 环境的 HOME 为 `/Users/luckye`。未读取生产进程的完整环境，静态路径不冒称为运行时环境转储。 |
| Codex 凭据 | `~/.codex/auth.json` 存在，字段符合该 reader；仅输出字段名和 JWT 过期时间，未输出 token。当前真实警告发生在取得 OAuth 凭据之后。过期时间不能证明 token 未被上游撤销。 |
| Claude 凭据 | `~/.claude/.credentials.json` 不存在。生产的端点不可达警告证明 reader 已取得候选凭据并进入 HTTP 层；源码允许从 macOS Keychain 读取。本次未读取 Keychain 内容，具体来源和有效期未核实。 |
| Provider 登录状态 | 保存的状态文件均为 ready/authenticated，Claude authType 为 pro；这些记录的 checkedAt 为 02:41:06 UTC，早于调查截止点，只作已有状态线索，不能证明当前上游认证成功。 |
| 不支持的认证方式 | Codex API key、Claude 环境 token 或缺少 `user:profile` 的 token 会返回 unsupported；缺少凭据返回 needs-auth。它们不能解释已记录的 private-address 异常。不能用假认证测试证明用户登录在上游有效。 |
| rateLimitResilience | Claude 的 429 保留上次成功值逻辑在收到 HTTP 响应后才执行。本次地址拒绝在 HTTP 请求之前，不是这套 cooldown 的错误。 |
| 前端显示 | `ProviderUsageSettingsPanel.tsx` 把服务端 status=error 映射为 Unavailable，并直接渲染 snapshot.detail；query 直接调用 `api.server.listProviderUsage`。静态路径与当前提示一致，没有发现额外的前端错误转换原因；未运行正式 UI 验证。 |
| 其他网络错误 | 本次未执行带真实凭据的 usage 请求；DNS 拒绝后是否还会遇到 TLS、401/403、429 或响应格式变化，均未知。 |

**截至当前证据，没有发现第二个导致这些用量警告的已证实原因。** 不能把请求尚未走到的上游行为写成“已排除”。本任务书要求真实请求验证前停下问主控；用户现已选择保持网络配置，因此未提出或执行真实请求。

## 日志位置与独立发现

用量 provider 的 `createLogger` 调用 `console.warn/error`；`server.log` 属于另一套 Effect Logger 文件管道，不收集这些 console 消息。桌面把后端 stdout/stderr 接出，a2a 启动器再追加到 `workbench-launch.log`。因此细节实际被保留，只是不在主控最初查看的文件中。Cursor 的外层 catch 没有记录异常细节，这是静态代码事实，未在本次扩展修改。

另发现启动器 `status` 的 locale 误拒绝：记录的 `ps lstart` 使用中文，worker 当前英文 locale 输出同一 PID、启动时间、可执行路径和 argv 的不同文本；`read_owner` 做全文比较，误报“PID 身份已改变”。只给只读命令设置 `LC_ALL=zh_CN.UTF-8` 后，与原记录完全相等，`workbench status` 返回 running=true、PID 9859。未改系统 locale、生产进程、设置或记录文件。这是独立启动器缺陷，不是用量请求失败的原因；建议主控另行分配，不在 T-045 扩修。

依据：[read-only-status-01.txt](read-only-status-01.txt)、[process-identity-01.json](process-identity-01.json)、[locale-status-01.json](locale-status-01.json)、[read-only-status-02.json](read-only-status-02.json)。

## 复现与验证

依赖安装按任务书执行 `a2a/scripts/bun install --frozen-lockfile`，缓存保持在外置盘，退出 0；1,635 个包安装耗时 2,321.97 秒，postinstall 完成。见 [安装记录](install-result.txt)。安装完成前的一次批量复现尝试缺少 Vitest 依赖 `pathe`，未进入业务代码；该失败保留在 [首次尝试](offline-red-20261009T044446493533Z/output.log)，不计为业务红态。

两次夹具修正也保留现场：[原生 ESM namespace 不允许 spy](offline-red-20261009T051457266093Z/output.log)；[安全 guard 拒绝了 Linux 的无实际 Keychain 访问的 helper 调用](offline-red-20261009T051539890674Z/output.log)，导致 Claude 未到达 HTTP 层。最终夹具改用模块边界的 socket guard，并使用标准 `.claude` 假凭据目录的隔离上下文；没有修改生产行为，也没有弱化用户用量应为 ok 的最终断言。这两次不计为完整三 provider 的业务红态。

已完成的共享源码边界探针不依赖 workspace 安装：Node 24.13.1 的内置 TypeScript 转换只去除类型并调整临时副本的相对 import，未改变生产源码逻辑。三个 DNS 输入均触发 `OutboundPolicyError/private-address`，TLS request 调用为 0；真实本地 HTTP mock 的两次响应分别为 17、47，helper 都按输入返回。去掉临时副本中 `198.18.0.0/15` 阻止项的 mutant 到达 TLS guard，诊断断言退出 1，因此探针能检测策略变化；guard 在建立 socket 前拒绝，未发出真实 TLS 请求。

| 检查 | 退出码 | 结论 |
| --- | --- | --- |
| [源码边界探针](raw-boundary-20261009T045240982288Z/output.log) | 0 | PASS：证明当前地址拒绝及本地 JSON 正例；不是显示修复通过。 |
| [临时 mutant](raw-mutant-20261009T045239719293Z/output.log) | 1 | PASS：反例按预期被诊断断言拒绝，错误来自 TLS guard，不是 import/setup 失败。 |
| [真实 batch 入口的假凭据复现](offline-red-20261009T051643715694Z/output.log) | 1 | 红态成立：三个 snapshot 均为 error，原始不可达提示复现；最终断言期望三个 ok，因此失败。此前的三个 DNS 名、0 socket、0 refresh、0 write、0 Keychain 调用及假文件保持不变断言均通过。缺凭据/API key/Claude 环境 token 的分类用例通过。 |
| [六个相关既有测试文件](baseline-20261009T051457266187Z/output.log) | 0 | PASS：47/47。没有产品修复，这不是“修复后通过”。 |

离线夹具通过真实 `collectProviderUsageSnapshots` 入口，使用新建的假 Codex/Claude 凭据文件、Cursor SQLite 数据库，以及上述三个保留地址的 DNS 替身。共享 HTTP 安全层保持真实；socket、Keychain、凭据刷新、CLI auth nudge 和凭据写入均设置禁止调用断言。真实用户凭据不进入 fixture。

复现命令：

```sh
python3 evidence/2026-10-09-batch5/T-045/inspect.py
python3 evidence/2026-10-09-batch5/T-045/run.py raw-boundary
python3 evidence/2026-10-09-batch5/T-045/run.py raw-mutant
python3 evidence/2026-10-09-batch5/T-045/run.py offline-red
python3 evidence/2026-10-09-batch5/T-045/run.py baseline
```

每次运行生成独立时间目录，记录完整 argv、fork 版本、时间、退出码及 output.log，旧结果不会被覆盖。offline-red 最终按用户验收要求断言三个 provider 为 ok；若实际仍为 error，它应退出 1。这个红态证明环境与现有安全策略不相容，不把安全层正常拒绝称为已修复的程序缺陷。诊断断言本身成功也不是修复绿态。

相关既有测试核对 reader、parser、HTTP policy 和 rate-limit 分支。没有产品改动，未运行全仓 fmt/lint/typecheck、产品构建或正式工作台截图；本次也未发起独立业务验收。诊断中的正例和反例不能取代主控的验收门禁，任务书把重启与最终显示确认交给主控。

UTF-8、JSON、Python 语法和报告链接检查通过。整体 staged whitespace 检查返回 2，提示原始测试日志末尾空行、源码摘录的空行编号后空格；原始证据保持原样，结果见 [raw-whitespace-check.txt](raw-whitespace-check.txt)。只检查起草的文档和脚本时返回 0。结束前项目地图 status 为 Problems 0、Stale living docs 0，fork worktree 干净，见 [checks-final.txt](checks-final.txt)。

## 版本、授权与交接

调查 fork 固定为 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`，worktree `synara-t045`、分支 `a2a-t045`。没有 fork 产品改动或新提交，没有 push。a2a 只交付本证据目录和 T-045 Resolution，保留其他 worker 的脏文件。

上游文件修改清单为空；所有新增源码副本只在外置盘测试目录，构建输出与依赖目录均保持标准布局。没有启动、停止或重启正式工作台，没有读取 `secrets/`、endpoint token、生产数据库或设置，没有运行带真实凭据的 fetch/refresh/nudge。

身份和启动请求见 [identity.json](identity.json)。brief 未提供 attempt、session_id、fence 或门禁收据，本次不声称已完成 submit、验收或 integration。请求的 Fast tier 不作为供应商实际 tier 证明。skills 按本机当前文件执行，不将旧验收结论用于本候选。

下一步按用户决定保留现状。若日后主控重新要求正常显示，需要先决定允许的网络/安全处理方式，再重新验证；本次不将最终用量显示判为 PASS。
