---
from: "worker:t078-review-followup"
to: "triage"
kind: "issue"
reply_to: ""
refs: ["ticket:T-078"]
created_at: "2026-10-16T14:28:44.683852Z"
schema: 1
title: "T-078 真登录材料受fake-only入口与真实HOME写集/调用计数前置阻塞"
blocking: false
id: "20261016T142844Z-worker:t078-review-followup-issue-001"
---

# 真登录准备的实际入口缺口

主控 #335要求按已批准PLAN-2准备真实HOME的两回合复核；认证路线不需重问。只读发现claudeLaunch.ts:39只接受loopback，:50固定隔离HOME/config，:51强制假token，:65固定fake authentication。现有controller_start没有正常登录profile；Panes.screenKey:652也只准fake profile，符合真HOME提示不能自动按键的原限制。

本轮仅准备F4/F6/F7和真登录材料，未获本轮产品normal-profile实现指令；不能用直接zsh起Claude、删掉根校验或把正常HOME当fallback绕过去。P3-REAL-LOGIN-MINIMAL-01.md已给出拟议argv/env、两真实回合＋第三次另批、原生send→report唤醒、唯一门禁命令模板与停止条件，但没有假称当前可以live启动的manifest。

建议执行主控安排同票normal-login profile的最小实现/入口红绿切片：新profile显式身份、用户HOME的写入仅本次会话历史、不动settings/权限/认证，hooks/capability仍逐launch登记。同样先验证固定CLI正常登录实际写集和包含重试/失败的可靠调用计数。当前不能证明CLI自己不会写非会话历史缓存/索引，或仅从成功assistant段落数出实际调用；这些前置未证实时不启动，若必须扩大真实HOME写入或放宽2～3次调用预算，再经用户决定。

这是P3 launch的阻塞，不阻塞本轮其他准备与交接；未启动CLI或读取用户认证。下一实现范围由主控裁定，不向用户弹确认，也不重新请求已选认证路线。
