---
id: T-127
title: 产品里的 Codex worker 与 reviewer 直接用用户的 ~/.codex
type: build
status: closed
blocked_by: [T-122]
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：用户 2026-10-21 在本会话中的裁定。用户原话：
- “1.直接用我的~/.codex,因为这些 session 我还有用,别隔离,然后我也会更新一些 skill 之类的,这都是有帮助的”。
- 被告知其 `~/.codex/rules/default.rules` 有 30 多条 allow 规则（含 `git push origin HEAD`、`ssh win`、`docker exec …`、`python3 -m pip install`），这些规则与 `hooks.json` 的钩子都会在 worker 里生效之后，选“完全照用 ~/.codex”。
- Codex reviewer 选“reviewer 也用 ~/.codex”。
- 同一轮 Claude worker 选“Claude 保持现状”（继续 `--setting-sources ""`）。

现状：
- `panes.ts` 用 `isolated_codex_home_required` 拒绝 `~/.codex`。
- 产品启动配置（`app/desktop.mjs`）没有 `codex_bin`、`codex_home`，所以产品里派 Codex worker 会被拒。
- Codex reviewer 用预建的空 home，门禁核对 `review_home_was_empty`；产品里没有这类 home。

要做的：
- 产品启动配置：用 `zsh -lic 'command -v codex'` 取 `codex_bin`，`codex_home` 为用户的 `~/.codex`；去掉 `isolated_codex_home_required`。
- 原生记录扫描：`~/.codex/sessions` 含用户全部历史会话，只看本 launch 开始后写过的文件，以及已在读的文件。草稿留在 session scratchpad 的 `t127-panes-hunks.txt`。
- Codex reviewer 用同一个 home。“干净会话”不再靠空 home 证明，门禁改为核对：argv 不含 resume/fork，原生会话号是新的（不同于 worker，也不在其他启动记录里），会话元数据的 cwd 是一次性候选副本。删除 `reviewers` 预建 home 这条路径，不留兼容分支；依赖它的测试改为新做法。
- 未定事实，需先探针：
  - 用户的 `hooks.json` 钩子与我们经 `-c hooks.*` 传入的钩子如何共存（是替换还是叠加），会不会干扰回合结束与交付；
  - 未信任过的项目在 worktree 里会不会弹信任框（若弹，由用户在窗格里回答，写入是 Codex 自身行为）。
- 不改：真实 Codex 验收测试仍用 /tmp 隔离 home（AGENTS.md 的验收规则），产品与验收的差别写进 README。

## Acceptance

- [x] 真实入口：打包测试版里，终端主控派一个 Codex worker，worker 与 reviewer 的会话都出现在用户 `~/.codex/sessions`，交付、审查、集成走通；a2a 不写 `~/.codex/config.toml`、`rules`、`hooks.json`。
- [x] 门禁拒绝：reviewer argv 带 resume/fork、会话号与 worker 相同或已被其他启动记录用过、cwd 不是候选副本，各一个反例，并留记录。
- [x] 修前版本（`isolated_codex_home_required`、预建空 home）在同一场景上失败。
- [x] 扫描只读本 launch 之后的会话文件：`~/.codex/sessions` 里有大量旧文件时，派发与交付的耗时不随旧文件数增长（用夹具 home 放入大量旧文件对照）。
- [x] README 写明：产品 Codex 会话加载用户的规则、钩子、skills，worker 可不经批准执行用户 allow 过的命令（含 `git push origin HEAD`），门禁管不到 push。

## Resolution

2026-10-22 PASS，最终候选 e161476d6。真实入口 `gui-02`（18e290411，用户的 `~/.codex`，主控 Haiku 5.5，Codex gpt-6.1-sol low）走完派发、交付、独立审查、集成到 main，worker 与 reviewer 的会话都在用户 `~/.codex/sessions`，a2a 没有改用户 home 的配置。候选 3 在 e161476d6 上经 e2e 与回归复验。门禁结果处的 cwd 与会话号核对端到端走不到（后台更早拒绝），以及期间修复的终端恢复慢（用户指出），见 [RESULTS.md](../../evidence/2026-10-22-batch20/T-127/RESULTS.md)。
