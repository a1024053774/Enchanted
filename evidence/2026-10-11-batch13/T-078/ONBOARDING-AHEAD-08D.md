# Security notes 之后可能的引导：官方依据与未知

供主控逐屏审批比对，依据本轮查阅的官方在线文档；文档没有绑定 CLI 2.1.296 的完整逐屏顺序。**不把下列推断当作已看到的界面，不据此自动按键。** 08c 的实测到 Security notes 为止，未确认该屏，随后已清理。

| 可能界面 | 依据与本实例的预计情况 | 处理 |
| --- | --- | --- |
| 目录信任 | 官方说明交互会话在未信任目录启动时显示信任对话框，hooks 在接受信任前不运行。新隔离 repo／HOME 没有预置信任，因此预计仍须遇到它；**出现在 Security notes 后哪一步是推断，顺序未知**。 | 保存新实例原文，主控单独审批实际显示的信任选项；只在明确对应时用 workspace-trust／Digit1，一次，不补 Enter。 |
| 登录／账户／API key 批准 | Quickstart 说明首次通常要求登录；设置 ANTHROPIC_API_KEY 时还须批准 key。本实例使用已验证能取得本地请求的公开 Bearer，未设置 API_KEY；**不预计照抄 key 批准流程，但文档未保证此固定版本不再出现认证界面**。 | 任何认证、账户或 key 选择均停下交主控；不自动登录、不读取凭据、不用 notice 用途通过。 |
| 项目 MCP 批准 | Security 文档说明项目 `.mcp.json` 中的 server 有独立批准提示。本 repo 只有 value.txt，启动 strict MCP 配置为空，因此没有已配置的项目 MCP 可批准；这是本配置下的推断。 | 若仍出现 MCP 选择，停下报告，不批准。 |
| 正常提示符 | Quickstart 描述认证后出现显示版本、模型和工作目录的提示符。它是文档中的一般就绪表现，不证明本实例的信任／hooks 已完成。 | 逐屏读回实际状态，另填本实例 readiness.json、另批 continue；不把提示符自行等同于后台 idle。 |
| 其他引导 | 本次查阅的官方文档未列出 Security notes 后完整的主题／终端设置／遥测／数据共享等屏幕序列，也没有此版本每屏完整文本。不能断言“接下来只有信任”。 | 未授权用途、权限、遥测、数据共享或其他新选择，一律保存原文、停下交主控。 |

目录信任及项目 MCP 的依据：[官方 Security](https://code.claude.com/docs/en/security#prompt-injection-protections)。交互 hooks 暂缓的依据：[官方 Workspace trust](https://code.claude.com/docs/en/hooks#workspace-trust)。首次认证与正常提示符的依据：[官方 Quickstart 第 2 步](https://code.claude.com/docs/en/quickstart#step-2-start-your-first-session)；[官方 Advanced setup 认证段](https://code.claude.com/docs/en/setup#authenticate) 也说明环境 key 的批准要求。

这些文档支持界面类别及条件，不支持一个精确、穷尽的引导顺序。假服务只允许独立批准的主题、逐字相同的固定 Security notes，以及实际读回的目录信任；真登录阶段用户 HOME 出现任何引导屏一律停下，不沿用本假服务机制。
