---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-078"]
created_at: "2026-10-13T18:30:50.643754Z"
schema: 1
title: "T-078 假服务阶段：交互 hooks 需要先信任隔离夹具目录，是否允许执行主控在隔离实例里点一次信任"
id: "20261013T183050Z-executor-needs-decision-001"
---

worker 只读诊断（a2a-wt-t078 evidence/.../T-078/p1-diagnosis-07，issue 20261013T182412Z，blocking）：材料 06 中 AUTH_TOKEN 已让 CLI 连上本地假服务（不再未登录），但 UserPromptSubmit/Stop hook 一次都没触发。原因有官方依据：Claude Code 交互模式要先接受目录信任才运行 settings 里的 hooks（https://code.claude.com/docs/en/hooks#workspace-trust）；IS_DEMO 跳过了引导界面却没有产生'已信任'，隔离 .claude.json 里该夹具 repo 的 hasTrustDialogAccepted=false。另一个夹具问题（标题侧请求占住串行假 API）有文档化解法 CLAUDE_CODE_DISABLE_TERMINAL_TITLE，不需决定。选项：A 允许执行主控在一个新建、只含 value.txt 的隔离夹具 repo、隔离 HOME/CLAUDE_CONFIG_DIR 的实例里，读回信任界面原文后，用明确的按键选择'信任'一次（不设 IS_DEMO 以显示真实界面；CLI 自己把信任写进该隔离目录；不写内部状态、不碰用户 ~/.claude、不扩展真登录阶段权限）——执行主控推荐，否则交互 hooks 无法验证；B 继续禁止任何信任确认，交互 hooks 验证保持 BLOCKED，T-078 无法完成主控窗格的 hook/注入/忙闲/放行验收。注：真登录复核阶段（用户平常的登录、Haiku 5.5、2～3 回合）在用户正常 HOME 下同样要求项目目录已被信任，届时也会遇到同一问题，请一并决定。