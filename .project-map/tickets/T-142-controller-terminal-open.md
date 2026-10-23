---
id: T-142
title: 主控命令 terminal_open：让经批准的主控在项目内直接开界面里的普通终端
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

来源：用户 2026-10-23 在本 session 逐字（第 5 条）：“5.按建议来”

现状：守护进程有 `shell_start`，但经角色申请成为主控的 CLI 只能 `a2a call` 门禁命令，开不了界面终端，只能让用户按 ⌘T（用户 2026-10-23 的截图里主控自己说“我开不了 Enchanted 终端”）。

1. 加主控命令 `terminal_open`：参数 `cwd`，必须在项目主目录或 T-140 的额外目录之内；在界面里开一个该项目的普通终端，返回终端标识。
2. 只对本项目已批准的主控开放，沿用 `role_command_not_scoped` 的范围规则；`a2a help` 与插件 SKILL.md 补上用法。
3. 不为每个 harness 加启动参数适配（用户裁定“按建议来”）。

## Acceptance

- [x] 真实：已批准的主控 `a2a call terminal_open` 后界面出现新终端，cwd 正确。
- [x] 越界目录、未批准会话、其他项目的主控均被拒（各一条反例）。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-23 关闭，PASS。

- 代码：`aeda66327`（`daemon.ts`、`terminalCli.ts`、a2a SKILL 与 README：已批准的主控 `a2a call terminal_open --cwd <项目主目录、子目录或额外目录>` 开一个项目层普通终端，返回 launch；未批准、cwd 越界、他项目主控都拒绝），测试夹具 `f8a185996`、`ff8d7d50e`、`6c47ed883`、`cd8c31b76`，合并 `edd8a7cad`。
- 夹具迭代的原因是 Claude Code 2.1.309 的新对话框：默认 auto 模式会弹计费说明；设 `defaultMode=default` 后又弹“设为默认 auto”选择框（需 `.claude.json` 写 `hasSeenAutoDefaultNudge`）；带输出重定向的 Bash 命令另要确认，探针 PROBE-01 证实 allow 规则与 additionalDirectories 都不覆盖。最终 Claude 只执行不带重定向的命令，测试按 tool_use_id 读取原始工具回执并核对后台 launch。全程没有用按键关对话框。
- 验收（执行主控沙箱外）：第 1 轮 T-124、T-139/T-143 通过，T-091 与起点同样；第 5 轮 `outside-05-20261023T165125Z-GjZtsr`：真实 Claude Code（claude-haiku-5-5）在界面申请执行主控并获批，三处目录开出终端且 cwd 正确；未批准（`approved_role_required`）、他项目（`role_project_mismatch`）、兄弟目录被拒；起点红态 `role_command_not_scoped`；cwd 不检查的变异被 `sibling_refused` 抓住。截图归档在外置盘 `a2a-evidence/2026-10-23-batch23/T-142/`。
- 独立审查：agy gemini-3.8-flash-high，PASS，无发现项。
- 合并后回归 05、06：T-142 绿态通过。
