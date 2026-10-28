---
id: T-204
title: 关闭终端后窗格报 a2a:resize 内部错误
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：真实用户式试用第 2 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-02/RESULTS.md) 发现 4）。关闭一个正在待批角色申请的终端，窗格顶部显示“输入尚未确认，已停止发送：Error: Error invoking remote method 'a2a:resize': Error: Window is not available for input”。终端已结束、申请已随终端关闭而失效，这条错误既不准确也吓人。

终端结束后界面不再对它发 resize；若终端结束时有待批申请，可以说一句申请已随终端关闭而作废。

## Acceptance

- [x] 修前版本经真实入口：关闭带待批申请的终端后出现上述错误；修后不出现。
- [x] 关闭终端后再批准该申请仍被拒绝（不变）。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

改申请随终端结束的规则。

## Resolution

2026-10-27 PASS。根因：关闭普通终端要等前台程序退出（最多 5 秒）；这期间 shell 已退出、申请结束、横幅消失，窗格变高，正在关闭的窗格照常发 resize 并轮询快照，被主进程拒绝后当成“输入尚未确认”和连接错误显示。修法：点“关闭窗格”后该窗格暂停 resize 与轮询，关闭失败时恢复并补发尺寸（`renderer.tsx`）。真实 Electron 入口的端到端测试：修前版本 a3ae46cf2 复现试用原样的报错，修后通过；三个变异体（关闭中仍 resize、仍轮询、停掉全部 resize）各在对应检查失败；关闭后再批准该申请仍被拒（`request_not_pending`）。agy 独立审查结论“可合并”，一条 P3（关闭过渡的几秒内用户自己再打字仍会看到输入错误，未改）。可选的“申请已随终端关闭而作废”提示没做。见 [RESULTS](../../evidence/2026-10-27-batch28/T-204/RESULTS.md)、[审查](../../evidence/2026-10-27-batch28/T-204/review-1.md)。
