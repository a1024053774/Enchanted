# Codex 钩子信任探针（T-133 方案 A 的 Codex 一侧）

- **问题**：用 `-c hooks.UserPromptSubmit=…` 给用户自己的 Codex 传提交钩子、不用 `--dangerously-bypass-hook-trust` 时，钩子会不会运行，会不会写用户配置。
- **做法**：`codex-cli 0.163.0`，`/tmp` 下的隔离 `CODEX_HOME`，只复制 `auth.json`，空 `config.toml`；真实 TUI 在伪终端里运行。三个 home 用完都已删除，没有碰用户的 `~/.codex`。
- **结论**：会写用户配置，按 T-133 的用户决定停在这一步，Codex 一侧没有实现。

| 运行 | 做法 | 结果 |
| --- | --- | --- |
| probe-01 | 启动后不选信任（选第 3 项“Continue without trusting”） | 启动时弹“Hooks need review … Hooks can run outside the sandbox after you trust them”；钩子没有运行；`config.toml` 里没有信任条目 |
| probe-02 | 选“Trust all and continue” | 钩子运行（收到 `UserPromptSubmit` 载荷，含 `session_id`、`prompt`）；Codex 往 `CODEX_HOME/config.toml` 写了 `[hooks.state."/<session-flags>/config.toml:user_prompt_submit:0:0"] trusted_hash = "sha256:…"`。产品里 `CODEX_HOME` 是用户的 `~/.codex`，即写用户配置 |
| probe-03 | 用 `-c 'hooks.state."/<session-flags>/config.toml:user_prompt_submit:0:0".trusted_hash="…"'` 传入 probe-02 写下的同一个信任值 | 仍弹审查框，钩子没有运行：会话参数里的信任条目不被承认 |

用户 `~/.codex/config.toml` 里已有同类 `[hooks.state."…"]` 条目（只读查看，未修改），与 probe-02 写入的形式一致。

可选方案（等用户定）：A 由用户在自己的 Codex 里点一次信任（Codex 自己写用户配置；钩子命令路径变了要重新信任）；B 用 `--dangerously-bypass-hook-trust`（用户此前已否决）；C Codex 主控不记、状态保持“未知”（现状）。

复现：`python3 codex_hook_probe.py <新的隔离home> <工作目录> <输出前缀> noaccept|accept`；probe-03 用 `codex_hook_probe_flagtrust.py`，第 5 个参数是信任条目。屏幕文本是去掉控制序列后的摘录。

## 用户定 A 之后的探针（2026-10-22）

用户逐字：“1. A 2. 一二都要.”（第 1 条回答 Codex 钩子怎么办：选 A，由用户在自己的 Codex 里信任一次）。随后摸清接法所需的事实。做法同上：隔离 `CODEX_HOME`，只复制 `auth.json`，用完删除。

| 运行 | 做法 | 结果 |
| --- | --- | --- |
| probe-04（`codex_hook_probe_events.py`） | 挂 SessionStart、UserPromptSubmit、PreToolUse、PostToolUse、Stop、PermissionRequest；让模型执行 `echo $CODEX_THREAD_ID`，再让它用提问工具问用户 | 载荷见 `probe-04-hooks.jsonl`。<br>- 钩子的 `session_id` 等于模型 shell 里的 `CODEX_THREAD_ID`，也就是 `a2a request` 记下的 `native_session`。<br>- UserPromptSubmit 带 `prompt` 和 `turn_id`，没有 `prompt_id`。<br>- 回合结束发 Stop。<br>- 提问工具名为 `request_user_input_async`：PreToolUse 时问题出现；PostToolUse 紧接着返回 `{"accepted":true}`，这时用户还没答；之后模型调用 `clocksleep` 等待。<br>- 钩子进程的环境里没有 `CODEX_THREAD_ID`。 |
| probe-05（`codex_hook_probe_answer.py`） | 同上，用 ⇧← 打开问题，回车选第一项 | 载荷见 `probe-05-hooks.jsonl`。用户的答复作为一次 UserPromptSubmit 到达。<br>- `prompt` 为 `<send_user_message_question_reply>` 包着的 JSON 数组，每项有 `question`、`answer`、`questionItemId`（`["request_user_input_async","<call id>",0]`）。<br>- `turn_id` 与原提问的回合相同，因此 `turn_id` 不能当作每次提交的唯一键。 |
| probe-06（`codex_hook_probe_matcher.py`） | PreToolUse 加 `matcher="request_user_input_async"`；执行 `echo hi` 与 `sleep 30`，期间按 Esc；再用同一 home、同样的钩子定义第二次启动 | `probe-06-hooks.jsonl`、`probe-06-screen-*.txt`。<br>- 只有 UserPromptSubmit 触发：matcher 把 shell 工具挡在外面。<br>- Esc 打断后显示 “Conversation interrupted”，但没有 Stop。<br>- 第一次启动要求信任；第二次启动不再要求：钩子定义不变时，信任一次就一直有效。 |
