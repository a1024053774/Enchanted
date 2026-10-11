# T-077-1 执行主控决定 01：批准 PLAN，答复 B1、B2（2026-10-11）

PLAN（在 worktree 里，路径为 `evidence/2026-10-11-batch13/T-077/PLAN.md`）获得批准，按第 8 节的顺序执行。

## B1：真实场景的 hook
共同规则里写的“无 hook”是从上一批沿用下来的旧条款。按 AGENTS.md，hook 只在执行主控逐次批准后才能安装。本卡的真实运行，我逐次批准以下 hook：
- 产品经每会话启动参数安装的 Codex UserPromptSubmit、Stop、PermissionRequest 三个 hook，只做记录；
- workbench 钩子目录里的 `prepare-commit-msg`，用来写尾注。

完整 argv 写进 outside-sandbox.sh。仍然禁止把用户自己的 hook 复制到隔离 home 里，也禁止把它们落盘。

## B2：与旧断言的冲突，按白名单处理
新契约来自 spec 第 3 节第 7 步、第 4 节的清理表，以及 T-070 的 D25（清理干净的 worktree，取代“保留所有 worktree”）和 R8（CAS 落空时自动重新验收），这些都已经过用户同意。旧断言里写的是被取代的契约。处理方式和 T-075-2 的 A1～A10 白名单一样：
1. 在 PLAN 里新增一节“断言白名单”，逐条列出：文件和行号、旧断言、新断言、对应的 spec 或决定原句。至少要覆盖：
   - `test_coop_e2e.py:456–474`（基线变化后改为 R8 重验）；
   - `test_coop_e2e.py:348`（撤销且干净的 attempt 删除目录、保留隐藏引用）；
   - `test_run_e2e.py:236–247`（已集成且干净的 attempt 删除目录、保留隐藏引用）；
   - `workbench/tests` 下受影响的预期。
2. 白名单交给我批准之后才能改；白名单之外的断言一律不动。
3. `test_recovery_e2e.py:561`（中断验收的目录要保留）是恢复契约，不在白名单里，保持不变。
4. 每改一条断言，都要配一个新的红态：起点上失败，候选上通过。用 `git diff` 逐 hunk 标明它对应白名单的哪一条。

## 其余批准
- 命名放在 `<state>/worktrees/<project_id>/` 下；额外的隐藏引用 `refs/a2a/verifications/...`，用来让已验证的 M 不被回收；路径交集理由的参数（名字由你定，写进 README）；冲突修复的基线记录；R8 的计数规则；与 T-076-2 的衔接方式：以上全部同意。
- 合并顺序：T-076-1 会先合进 main。你交付前要把分支变基到最新 main。PLAN 第 5 节说到“冲突修复基线”和 T-076-1 的身份改动关系很紧，合并时我会逐处看 diff。
- 真实回合上限 4 个，被测 worker 用 `gpt-6.1-sol`。
- 写完白名单后回复 `T-077 WHITELIST READY` 并停下，其他不依赖白名单的部分可以先做。
