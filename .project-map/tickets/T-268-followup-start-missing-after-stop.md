---
id: T-268
title: T-266 续接输入在原生回合结束后停在回合未开始
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
---

## 事实

T-266 a2 `1e124658-738b-452e-82a1-58d52b70e0fd` 原生14:36:31记 task_complete，但后台 active 输入 nativeTurn=null、start_missing=true，主控外部结果 #174 仍排队。界面显示回合未开始，切换窗格停在正在切换。尚不能区分原生输入、Stop顺序与后台状态问题，不宣称已定位根因。

证据 `evidence/2026-11-09-controller-switch/t266-v2-start-missing.json`；原生会话 `01a1c0b1-88fb-79b0-b354-2144383cdaad`。仅查看公开 assistant 与生命周期元数据，未读取隐藏推理。主控没有盲发 Enter、重复任务或合成 Stop。

## Acceptance

- [ ] 保留真实输入/Stop顺序和状态冲突证据，定位根因。
- [ ] 正常输入续接恢复，未知副作用或重复输入仍拒绝；已知坏实现判红。
- [ ] 独立审查与真实入口复验完成，不手改正式数据库。

## 当前状态

BLOCKED：外部候选16项通过、父版及两变异指定业务红态成立，但当前worker没有完成提交。先恢复可核对的输入与回合身份，不以模型自报或旧候选代替交付。
