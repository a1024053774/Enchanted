---
id: T-185
title: Codex 终端装上开局钩子（SessionStart 等价物）
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

用户 2026-10-25 逐字：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”

T-181 只给 Claude 插件加了 SessionStart 开局说明，Codex 主控仍只靠 developer_instructions 与 skill。先读当前 Codex CLI 的文档与 `--help`/源码，确认支持的钩子事件；支持 SessionStart 则在 `terminal/bin/codex` 包装脚本里经 `-c hooks.SessionStart=...` 装上，与 Claude 侧给出同一份开局说明；不支持就写明证据并给出最小替代（不写用户全局配置）。

通用：先留真实入口的红态再修根因；真实 Claude 用 claude-haiku-5-5、尽量少；不写 ~/.claude、~/.codex 等全局配置，钩子只经每会话启动参数；agy 独立审查。

## Acceptance

- [x] 真实 Codex（用户 ~/.codex，gpt-6.1-sol high，按现有规则）在 Enchanted 项目终端启动，开局说明进入上下文（证据：会话记录或钩子事件）；对同一句“你来当执行主控，派两个 worker…”直接执行 a2a request。
- [x] 用户自己传的 -c 或配置仍优先。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch26/T-185/RESULTS.md)。Codex 0.164 支持 SessionStart 与 hookSpecificOutput.additionalContext；包装脚本在用户参数之前加 -c hooks.SessionStart（a2a session-context），session-context 改为两家都认的 JSON，开局说明措辞对两种 CLI 都准确。机械检查：修前 main 开局说明不进 Codex 上下文，修后 PASS 4/4（含用户 hooks.json 的开局钩子照常运行、用户自己的 -c hooks.SessionStart 优先），变异被拒。真实 Codex（gpt-6.1-sol high，隔离 CODEX_HOME，只复制 auth.json、结束删除）对“你来当执行主控，派两个 worker…”先 a2a help 再直接 a2a request executor，界面批准；首次评分因解析失误为 INCOMPLETE，改解析后用保存的 rollout 重评 PASS，改坏的 rollout 三种均被拒。回归 T-133 Codex、T-181 通过。agy 审查 PASS。观察：Codex 主控多次换参数调 card_template（a2a help 写得不清楚）。
