# T-242 结果（2026-11-03）

结论：**INCOMPLETE**。已复现并查明原因：这是 T-191 设计上的显示，不是状态不同步。是改文案还是改设计，要用户决定。

## 复现

`probe_shell_claude_state.py`：隔离夹具和真实 Electron 窗口，普通项目终端里经包装脚本运行 `claude --model claude-haiku-5-5`（模型由夹具的脚本化 API 应答，没有真实模型回合），发一句话，回复出现后每秒采样一次，共 20 秒。

| 文件 | 结果 |
| --- | --- |
| `probe-2.json` | 回复出现在提交后 0.21 秒；20 次采样都是：标题栏“未知”（`data-state=unknown`），输入焦点标签“正在输入”，侧栏行 `unknown`，后台 `sidebar_snapshot` 为 `unknown`、前台 CLI `claude`；终端的钩子报出了原生会话（`shell_native_session`） |
| `probe-1-invalid-wait.*` | 第一次运行作废：等待条件被输入的提示词本身满足（`reply_seen_after_s` 为 0），不能证明已经回复 |

## 原因

- `workbench/src/sidebar.ts` 普通终端一段（T-191）：前台没有 CLI 时为空闲；agy、opencode 取它们自己的 OSC 7501；Claude Code、Codex 只有获批角色后才报告回合，之前为未知。
- `workbench/src/daemon.ts` 的 `terminal_hook`：没有获批角色时，钩子只用来记下会话号（T-195），回合事件丢弃、不记录（T-133：普通终端的提示词不进记录）。
- `test_t184_unwired_cli_e2e.py` 的 `shim_claude_without_role_state_unknown` 正是断言这一点。
- “正在输入”是输入焦点的标签（`app/renderer.tsx`），和状态无关。

标题栏、侧栏和后台三者一致，所以票面“修后显示与后台一致”现在已经成立；问题在于后台按设计就给出未知。

## 待用户决定

1. 保持设计，改文案：例如没有角色的 Claude/Codex 显示“未接入状态”，并在提示里说明获批主控角色后才有回合状态。
2. 改设计：没有角色时也只在内存里取钩子的回合状态（运行中/空闲），不记录提示词。这样会改变 T-191/T-133 定下的边界。
