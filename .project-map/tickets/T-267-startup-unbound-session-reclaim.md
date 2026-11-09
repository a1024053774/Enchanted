---
id: T-267
title: 启动核对失败且未绑定 native session 的已停止 attempt 无法回收
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
---

## 已观察事实

2026-11-09 本轮按用户“Read evidence/2026-11-09-controller-switch/executor-handoff.md and follow it”执行。T-250 attempt `528c29ab-838f-473f-9d35-5b1ff360fd49` 启动核对出现 JSON 解析错误，runtime_identity.native_session 为 null，任务输入仍排队，worktree 干净。正常后台重启后 shell/leader 已不存在，门禁 readThread 返回 running=false、stopped=true、blocked=false；reclaim 仍返回 identity_conflict。未绕过身份检查，未修改正式数据库。

证据：`evidence/2026-11-09-controller-switch/t250-startup-failure.json`、`t250-startup-process.json`、`reclaim-t250-startup-01.json`、`t250-reclaim-after-restart-02.json`。JSON 启动失败是否与 T-266 同根因尚未证明；本票只记录后续停止状态无法正常回收的缺口。

## Acceptance

- [ ] 从真实入口复现未绑定原生会话的失败启动，保存拒绝与实际进程证据。
- [ ] 原 attempt 确已停止、输入未执行时，正常门禁可完成回收；身份替换、仍在运行及身份未知仍拒绝。
- [ ] 已知坏实现命中反例，独立审查通过，正式数据库没有手改。

## 范围与状态

BLOCKED：T-250 无法回收。身份校验属于门禁边界，修复方案须先明确现有契约与独立反例；本票未授权放宽身份要求，尚未派发。T-266 继续既定审查。

## 2026-11-09 状态

仍 BLOCKED：修复需要改门禁的身份校验边界，属于“验收条件或权限改变”，须用户裁定，本轮不做。a2a+T-250-1 与 a2a+T-266-1 两个 attempt 仍为 claimed（worker 已不在），T-250 已由主控在主线直接完成并提交，T-266 已按根因关闭；两条门禁记录留待本票裁定后回收，没有手改正式数据库。
