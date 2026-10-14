# 原始任务卡 T-077-1 摘录

来源：主控 #18 原始任务卡。这里只摘录任务边界、验收与交付规则，不包含实施聊天、计划或诊断。后续独立审查对象和输入限制由本次审查请求指定。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-077-1 |
| 来源 | ticket T-077，`ready_rev: 1` |
| 目标 | 实现 S3 的 worktree 生命周期与冲突处理，即 ticket T-077 的 What to build 第 1～6 项：命名；按清理表清理并保留隐藏引用；认领时检查路径交集；文本冲突写回 worker；R8 重新验收上限；集成时检查检出工作区里的未提交改动。 |
| 非目标 | T-076 的质量串（红态、规则式检查、独立审查、打回回写、打分）；T-078 的主控窗格与收件箱；面板 UI（S5 之前，上报改用 issue 条目）；不改存储结构（另有切片）。 |
| 修改边界 | 允许：你 worktree 里的 `workbench/src/`（门禁核心、后台、窗格中与 T-077 直接相关的部分）、`workbench/tests/`、`workbench/README.md`、本卡证据目录 `evidence/2026-10-11-batch13/T-077/`、ticket T-077 的 Resolution。禁止：`acceptance/test_*.py` 的断言、`scripts/`、spec、地图、全局配置、Synara fork。 |
| 完成条件 | 见 ticket T-077 的 Acceptance，逐条对应，外加本卡下方的条款。 |
| 红态命令 | 每条新行为都要先在起点（main 当前 HEAD）上取得失败，再在候选上通过。 |
| 任务类型 | 后端逻辑 |
| 修复对象 | — |
| 复杂度 | L |
| 起点 | `main` 的 `14b57d22`（worktree 创建时） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s13-t077`），worktree `/Users/luckye/Documents/Code/a2a-wt-t077`，分支 `exec/t077` |

## 审查与交付（原文）

- 做一次 fresh-context 只读独立审查。审查发现问题，先取得红态再修，修复部分的 diff 由我审。
- 交付物：分支上的提交（带尾注）、`T-077/RESULTS.md`、ticket Resolution（保持 open）。
- 终端最后一行：`T-077 DONE <PASS|INCOMPLETE|BLOCKED> <exec/t077 的完整提交号>`。

## 相关共同规则（原文摘录）

- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-11-batch13/T-077/`（在你的 worktree 里），中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。
- 需要在沙箱外运行的部分（Unix socket、ps、真实 Codex、Electron、自建进程信号），统一写进本卡的 `outside-sandbox.sh`，然后回复 `T-0xx OUTSIDE-SANDBOX READY` 并停下，由执行主控执行。不要申请提权。
- 探针或测试本身的错误可以直接修，但要记录；真实的协议失败或产品失败、无法判定的情况、需要改业务断言的情况，都要停下来交给我。
