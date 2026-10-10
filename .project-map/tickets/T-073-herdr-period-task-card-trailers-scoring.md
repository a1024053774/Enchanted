---
id: T-073
title: Herdr 期三样：任务卡模板、worker 提交带尾注、验收打分文件
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

[spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节切片 S0，依据第 10 节"Herdr 期先用三样"与 [T-072](T-072-traceability-scoring-retrospective-metrics.md) 的 D31。切换到新工作台之前，日常派发仍经 Herdr；这三样先在 Herdr 期用起来，切换时再导入后台库。

1. **任务卡模板**：markdown，字段按 spec 第 2 节的表（编号、来源、目标、非目标、修改边界、完成条件、红态命令、任务类型、修复对象、复杂度、执行器、起点、唯一写入者），每个字段写明谁填、怎么填。不写生成或校验脚本（D31："不写脚本"）。
2. **worker 提交带尾注**：执行主控经 Herdr 启动 worker 时，worker 会话的环境里带 spec 第 5 节的变量（项目、任务、attempt、会话、角色、启动记录号），加上为本会话 git 指定钩子目录的 `GIT_CONFIG_*` 三项；提交时钩子追加 spec 第 8 节的 `A2A-*` 尾注，然后接着调用项目原有的钩子。启动参数整串记为启动记录（spec 第 5 节字段的 Herdr 期子集），尾注里只写记录号。模型取启动记录，拿不到写 `unknown`。
3. **验收打分文件**：执行主控在最终验收（集成或放弃）时写一行到追加式文件，字段按 spec 第 8 节的打分表；放弃只记结果与理由，不打分；升级时前一个执行器那次也留一条；用户自己的分另存一条，不覆盖。不另起一轮提问（T-072："包含在验收提问里就行"）。

## Acceptance

- [ ] 模板文件就位，字段与 spec 第 2 节逐项对得上；`AGENTS.md`、角色卡里指向任务卡的地方能找到它（只改路径指向，改规则交构思主控）。
- [ ] 红态在先：在当前 `main` 上，经现有启动方式起一个 Codex worker，在夹具仓库提交一次，提交里没有 `A2A-*` 尾注；保存命令与 `git log --format=%B` 输出。
- [ ] 修复后同一场景：真实 Codex worker 会话（经 Herdr 启动，隔离 `CODEX_HOME`，turn 数尽量少）在夹具仓库里的提交带齐尾注，值与启动记录一致；加 `--no-verify` 提交也带尾注；夹具仓库原有的钩子仍被调用（用一个会留下痕迹的夹具钩子证明）。
- [ ] 反例：不经新启动方式、直接在终端里提交的，不带尾注，也不报错。
- [ ] 打分：用一次真实或夹具验收写出一行，读回字段齐全；缺执行主控必填项时写入命令拒收；放弃只有结果与理由。
- [ ] 不写 `~/.claude`、`~/.codex`、全局或仓库级 git 配置；不改用户的 Herdr server。
- [ ] 每项都保留产物和重新生成它的命令；`project_map.py status` 0 problems。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：
  - Codex 的 `shell_environment_policy` 默认会滤掉名字里带 `KEY`、`SECRET`、`TOKEN` 的变量，`GIT_CONFIG_KEY_0` 可能被滤掉，导致尾注静默缺失。要用每会话启动参数（`-c`）解决，不写 `~/.codex`。
  - Codex 沙箱对 worktree Git 元数据的保护（AGENTS.md）与钩子目录的读写。
  - 项目原本没有钩子，或原有钩子失败（失败要照样传出，不吞掉）。
  - worker 的 shell 里有人手动 `unset` 了变量。
  - amend、rebase、merge 产生的提交。
  - 打分文件并发追加、文件损坏。
- 允许改的：`scripts/dispatch`、`scripts/` 下新增的启动与打分脚本和钩子目录、模板文件（建议 `.project-map/templates/task-card.md`）、相关测试与证据。`scripts/dispatch` 现在只负责发文本，不负责启动 worker；启动入口放在哪里由执行主控定，并在 RESULTS 里写明。
- 执行主控角色卡里"验收时顺手打分"一句由构思主控在本票关闭时加，执行主控不改角色卡。
- 与 [T-074](T-074-pane-signal-and-injection-facts.md) 改的文件不重叠，可以并行。
- 授权来源：用户 2026-10-10 在会话"a2a-构思主控"确认切法（逐字："确认"），在此之前在会话"新思路构思"说："确认，写完文档后，你这边就不用了，全权交给构思主控去安排执行主控安排子 agent 去做。"`ready_by: ideation`，`ready_rev: 1`。

## Resolution
