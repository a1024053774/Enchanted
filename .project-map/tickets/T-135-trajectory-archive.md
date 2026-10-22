---
id: T-135
title: 轨迹归档：后台启动的会话原生记录增量复制、压缩，设置页显示占用
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：用户 2026-10-22 逐字：“107 吧多 worker 做出来，早期的调研票关掉，然后还缺的都做”。 native-cli spec 第 8 节“轨迹归档”：后台把它启动的每个会话的原生记录增量复制、压缩，存在工作台数据目录，不进 Git，设置页显示占用空间。原生记录会被 CLI 自己清理（Claude 默认 30 天），复盘要靠这份归档。

- 范围：后台启动的会话（worker、reviewer、monitor）与经角色申请批准的终端主控会话；用户自己没申请角色的终端不归档。
- 只读原生记录（Claude 的 `projects/*/<会话>.jsonl`、Codex 的 rollout），只复制完整行；不写用户配置目录。
- 增量：已归档的部分不重复复制；归档索引进库（只追加）。
- 设置页显示归档占用与会话数。

## Acceptance

- [ ] 真实入口：一个 Claude worker 跑两个回合，归档在第一回合后有前半，第二回合后补齐，内容与原生记录的完整行一致；半写入的末行不进归档；用户配置目录前后一致。修前没有归档。
- [ ] 设置页显示占用，与归档目录实际大小一致；截图入证据。

## 不做

不做归档清理策略；不进 Git；不读未批准角色的终端。
