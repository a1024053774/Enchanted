---
id: T-095
title: 把"worker 在提问面板里等主控回答"识别成独立状态，不再显示为 working
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

2026-10-17 T-094 的 worker 用 Codex 的提问面板（默认折叠，按 shift+← 展开）在等执行主控回答，Herdr 却显示 `working`，执行主控漏看了（执行主控报告，用户先发现）。AGENTS.md 要求"任务失败、权限等待、业务阻塞……分别记录，不能用一个 blocked 或 done 掩盖差异"；"等待主控回答"目前没有独立状态。

1. 先读回：提问面板出现时，Herdr 的 `agent_status`、屏幕读取与工作台里该 worker 的状态各是什么；折叠与展开两种形态都要覆盖。
2. 把"等待主控回答"作为独立状态记录和显示（Herdr 期的监视脚本、工作台任务视图二者以哪个为准，执行时按现状定，不双写）。
3. 识别靠屏幕或事件里的机械事实（面板标记），不用正则猜用户意图（见 `feedback-intent-classification-no-regex`）；识别不到时报"未知"，不报 working。

## Acceptance

- [ ] 红态：在折叠与展开两种形态下，当前状态读出为 working，保留读屏原件。
- [ ] 绿态：两种形态都读出"等待主控回答"，并带 worker 与 launch 身份。
- [ ] 反例：普通 working（模型在思考或跑命令）不被误报成等待；面板被关闭或已回答后状态回落。
- [ ] `project_map.py status` 0 problems。

## 说明

- 来源：执行主控 2026-10-17 消息与 triage issue；构思主控裁定另开票、不并入 T-094（T-094 是启动失败，本票是运行中状态识别，验收与写入范围不同）。**未标就绪**，用户尚未说开工。
