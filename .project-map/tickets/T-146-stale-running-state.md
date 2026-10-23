---
id: T-146
title: 已结束的会话在 Reflect 页仍显示运行中
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

来源：用户 2026-10-23 在本 session 逐字（第 9 条）：“9.这个都结束了还在运行中”

现状：侧栏对同一执行主控与 worker 显示已结束（✓），Reflect 页显示“运行中”。`src/reflect.ts` 对经角色申请的主控把 `state` 设为“非 ended 即 running”（约第 34 行），对启动记录用 `lifecycle(record)`；两处与侧栏的 `agentState` 不是同一个事实来源，也没有把“批准后终端关闭”算作结束。

目标：Reflect 页、侧栏、流程页对同一会话显示同一个状态，来源同一处；终端关闭或 CLI 退出后为已结束。
先在真实 Electron 里复现（关掉终端后各页状态），红态入证据；再统一来源，不在 Reflect 里另算。

## Acceptance

- [x] 真实 Electron：关闭终端/CLI 退出后，三处页面都显示已结束；仍在运行的显示运行中。
- [x] 红态：修前 Reflect 显示运行中而侧栏已结束。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-23 关闭，PASS。

- 用户裁定 B（20261023T125315Z ideation answer 问题 3）：侧栏与流程页也列出已结束会话，三处同源；授权改受保护的 `test_t111_flow.mjs`（`['w1','w2']` 改为 `['w1','w2','ended']`，加已结束状态断言）。
- attempt 1：`7f94bb8f6` 合并，Reflect、侧栏、流程页用同一状态来源，终端关闭或 CLI 退出为已结束。合入 T-139 后合并回归 01 的 T-146 绿态失败（侧栏轮询刷新），不是 T-146 自身回归。
- attempt 2：修侧栏跳过已结束 shell 启动，被裁定 B 取代，未合入（分支 `exec/t146-a2` 保留在 git）。
- attempt 3：`65d56a392`、`7f204cb35`，合并 `6af6e3028`：保留确认过角色的主控条目并标已结束。合并回归 03 因此让 T-133/T-107（交回角色后主控条目消失）失败。
- attempt 4：`a2ec0db9d`、`f76805f76`、`c3caced73`，合并 `fd4d9ac13`：按终端 lifecycle 判定——终端已结束才保留主控身份并标已结束；交回角色而终端仍在时按普通终端显示真实状态。
- 验收（执行主控沙箱外）：attempt 1 `outside04-20261023T104746Z-9083`；attempt 3 `outside-20261023T132912Z-1738`；attempt 4 run 02 `outside-02-ej1axUQS`：T-133/T-107 红绿、T-146 绿、两项投影、t111、t107、t139/t143、t137 通过，两个变异（交回后仍是主控、后台对而界面错）被拒。截图归档在外置盘 `a2a-evidence/2026-10-23-batch23/T-146-a4/`。
- 独立审查：attempt 1、3、4 均 agy PASS（attempt 4 仅 1 条说明性 P3）。
- 合并后回归 04（fd4d9ac13）：25 项中 24 项通过，含 T-133/T-107 与 T-146 全部 6 项；`t145-green` 受真实指针干扰失败，单独重跑通过，见 `evidence/2026-10-23-batch23/merge-1/run-20261023T151510Z/NOTE.md`。
