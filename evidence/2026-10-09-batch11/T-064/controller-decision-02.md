# T-064 执行主控决定 02：补真实 provider 边界证据（2026-10-10）

依据 ready_rev 1、决定 01；回应 `provider-boundary-needs-decision-22.md` 与收件箱 `20261010T073006Z-worker:t064-issue-001`。

## 修复 diff 自审
- `7c04fb3fe`（Claude 只对显式免确认集合设置 override，默认/普通会话不收紧）：接受。符合决定 01“没有自定义时完全沿用既有语义”。
- `49cae984f`（a2a_stop 以 ideation 地址调用核心）：接受，理由是 a2a:stop 只有构思主控预设或用户在设置页显式授予才会出现，thread/turn 仍是真实调用者。但核心记录里的 address 会写成 ideation：请在 RESULTS 的局限里写明“被用户授予 stop 的其他角色，其 stop 在核心记录中按 ideation 地址、真实 thread 记录”，并给出一条实际记录作证。不改核心 stop 条件。

## 真实 provider 边界：两家分别处理
1. **Codex：真实 turn。** 按 AGENTS.md 既有规则：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任夹具根，只有 git add/commit 两条规则，无 hook，用完删整个 home。`gpt-6.1-sol`，显式 Fast 请求，`check_for_update_on_startup=false`。**最多 4 个真实模型 turn。** 会话用需要批准的运行模式（不是 full-access），否则测不到免确认。场景：给 worker 角色显式自定义免确认，勾一个工具、不勾一个工具；真实 Codex 调用勾选的工具应直接执行、没有待批准请求；调用未勾选的工具应出现待批准请求（拒绝或保持待批准，不批准）。证据取自实际 app-server 事件与网关记录。
2. **Claude：真实 CLI + 本机受控模型 API（选项 1）。** 用已安装的 Claude CLI（经 Agent SDK，即 Synara 实际路径），`ANTHROPIC_BASE_URL` 指向你在本机起的假 Messages API，它只按脚本返回 tool_use；配置目录放 /tmp 下的隔离目录，用假 API key。**不读、不复制用户的 Claude 凭据，不写 ~/.claude，不改任何 Claude Code/Codex 权限配置。** 权限请求、canUseTool、批准卡或免确认、MCP 调用必须由真实 CLI 与 Synara 适配器完成。同样做勾选/未勾选一对正反例。先做最小协议探针：CLI 拒绝自定义 base URL、要求登录或 tool_use 不触发权限流程，就停下记录，Claude 这一条保留为缺项，不加替代路径。报告里写明 Claude 的模型输入是假的，只证明权限边界，不证明模型行为。

## 收尾
- 两家各需一个已知坏实现被拒：例如把免确认判断换成父修订（或去掉勾选判断）后，真实进程下未勾选工具不再提示/勾选工具仍提示，断言失败。
- 不开第二次独立审查。完成后交 DONE（PASS 或 INCOMPLETE 照实），由我自审这部分 diff 与证据。
- 只操作自建隔离实例；不碰正式工作台、用户 Herdr、共享 dist。
