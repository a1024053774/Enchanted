---
id: T-135
title: 轨迹归档：后台启动的会话原生记录增量复制、压缩，设置页显示占用
type: build
status: closed
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

- [x] 真实入口：一个 Claude worker 跑两个回合，归档在第一回合后有前半，第二回合后补齐，内容与原生记录的完整行一致；半写入的末行不进归档；用户配置目录前后一致。修前没有归档。
- [x] 设置页显示占用，与归档目录实际大小一致；截图入证据。

## 不做

不做归档清理策略；不进 Git；不读未批准角色的终端。

## Resolution

2026-10-22 关闭，PASS。

- 代码：`e0330f663`（候选 1：增量归档、后台接线、设置页）、`0383b3cb1`（测试等待条件）、`01e0effd7`（候选 2：单个来源失败不再挡住整轮扫描，审查 01 的 P2；同一提交里复盘会话也纳入归档）、`338c51b4f`（Codex 复盘会话按工作目录找到 rollout）。
- 证据：`evidence/2026-10-22-batch20/T-135/`。候选 1：green 6 项 PASS，修前 `e4d45c511` 红态与 2 个变异（半行被复制、非增量）失败，T-122 回归 PASS。候选 2 的证据在 T-136 候选 1 的正式运行里：不可读来源检查 PASS、`archive-source-not-isolated` 变异失败、t135-green PASS。截图在归档夹具的 `out/` 里。
- 独立审查（agy gemini-3.8-flash-high）：review-01 PASS（1 条 P2、4 条 P3）；P2 的修复由 T-136 review-01 第 7 节核对。
- 未覆盖：Codex 会话与终端主控的归档没有端到端；四条 P3 未改，理由见 `candidate-2/RESULTS.md`；没有清理策略（ticket 不做）。
