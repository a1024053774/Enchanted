# A-11 I1 failure与 A-12 重建计划

A-11 ideation 的协议预算独立于 A-10 管道回合。B1 onboarding 没有 `/v1/messages`，但本次 I1 dispatch 已登记 1 root；Claude 在 Bash `tool_use` schema 错误后重试，`09b-a11-i1-scene-01/requests.ndjson` 共 12 条请求，故按 Messages 计 12，不能只按 API 成功响应数 1 计数。

冻结上限是 ideation 4 roots/6 Messages：本次已用 1 root/12 Messages，Messages 超限 6；剩余可用为 3 roots/−6 Messages，I1–I4 无法在 A-11 继续完成。必须重建 A-12；A-11 的现场、首次错误 schema、12 条请求和 1 条响应保留为失败证据，不重试、不回收现场。

修复内容：假 API 与共享协议核心把冻结 `protocol.commands` 的 argv 用 `shlex.join` 转成 Anthropic Bash 的 `input.command` 字符串；真实 Claude 2.1.296 的 `tools[].input_schema.properties` 由 scene-01 第一条请求读回，只有 `command`，没有 `argv`。工具历史和 tool_result 仍逐字绑定 command、tool_use_id、实际 stop entry、身份和预算。

A-12 顺序：先提交修复与红绿离线证据；用 `prepare-09b-executable.py --label 09b-executable-materials-12 --protocol` 生成新静态 root；新 Stage A、新 ideation B1 和逐屏 onboarding；再生成新的 protocol I1 approval。A-11 root、Claude、API、target 不复用；任何真实启动或 I1 发送都另经批准。

预期 A-12 I1 仍为 1 root/2 Messages、1 PermissionRequest；I1–I4 总预算回到 4 roots/6 Messages。A-11 的失败重试不计入 A-12 新现场预算，但必须保留在证据中。
