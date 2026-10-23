---
id: T-146
title: 已结束的会话在 Reflect 页仍显示运行中
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 在本 session 逐字（第 9 条）：“9.这个都结束了还在运行中”

现状：侧栏对同一执行主控与 worker 显示已结束（✓），Reflect 页显示“运行中”。`src/reflect.ts` 对经角色申请的主控把 `state` 设为“非 ended 即 running”（约第 34 行），对启动记录用 `lifecycle(record)`；两处与侧栏的 `agentState` 不是同一个事实来源，也没有把“批准后终端关闭”算作结束。

目标：Reflect 页、侧栏、流程页对同一会话显示同一个状态，来源同一处；终端关闭或 CLI 退出后为已结束。
先在真实 Electron 里复现（关掉终端后各页状态），红态入证据；再统一来源，不在 Reflect 里另算。

## Acceptance

- [ ] 真实 Electron：关闭终端/CLI 退出后，三处页面都显示已结束；仍在运行的显示运行中。
- [ ] 红态：修前 Reflect 显示运行中而侧栏已结束。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

