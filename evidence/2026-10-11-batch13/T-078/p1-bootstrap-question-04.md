# P1 文档化预置的事实缺口

主控 #89 要求隔离实例中的主题、onboarding、假 API key 确认与夹具 repo 信任都有文档化的预置依据，禁止自动按 Enter／选默认。

已核对当前官方完整 settings-reference 与 env-vars（原件在 p1-onboarding-research-04，HTTP 200）；CLI 固定为 2.1.296。主题 `settings.json` 的 `theme` 是公开设置；`IS_DEMO=1` 公开说明跳过 onboarding。官方认证文档明确交互 ANTHROPIC_API_KEY 需一次批准，记录在 CLI 状态中；settings 文档说明 `.claude.json` 是 CLI 自维护的应用状态与项目信任记录。

未找到把假 key 确认和项目信任预置进去的公开键／格式。常见 `customApiKeyResponses`、`projects[repo].hasTrustDialogAccepted` 不在官方完整设置参考中，问题报告只能证明有内部状态，不能冒称 2.1.296 的公开配置契约。材料 03 的隔离 `.claude.json` 也没有这些字段；未读取用户真实配置或凭据。

来源：

- https://code.claude.com/docs/en/settings-reference#theme
- https://code.claude.com/docs/en/env-vars （IS_DEMO、CLAUDE_CONFIG_DIR）
- https://code.claude.com/docs/en/authentication#authentication-precedence
- https://code.claude.com/docs/en/settings#find-or-create-your-settings-files

建议最小决定：允许仅用已文档化的 theme／IS_DEMO 做下一次零模型探针，并在任何 key／trust 提示处停止；或者明确允许只读核对固定 CLI 的内部状态格式，并把隔离预置标为版本绑定实现依据、不是文档化方式。不得用自动选择 UI、--bare 或换认证路线代替。

cleanup 独立修复已继续：保存 CLI PID／启动时刻／命令到 process-manifest，后台退出后等该 PID 明确消失；缺记录、仍存活或身份变化报 BLOCKED、保留根，不能再按 shell／daemon 消失直接 PASS。尚未运行新进程验证。

材料 04 可准备，但启动应等上述事实／范围决定；本 issue 为 blocking，避免把未完成的预置写成可运行 PASS。
