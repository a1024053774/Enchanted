# T-077 执行主控决定 03：真实冲突场景第 1 次启动

时间：2026-10-11 16:45 左右；审阅对象：exec/t077 `93094e7b` 的 `evidence/2026-10-11-batch13/T-077/REAL-APPROVAL-01.md` 与 `real-plan-01.json`。

## 批准范围（只此一次）

- Launch 1：`9906fa57-4877-48f9-afb4-c1aceef3edd4`，worktree `/private/tmp/t077-cf-20261011/state/worktrees/T077-real/T-077-9-a1`，Codex CLI 0.162.1，`gpt-6.1-sol`、xhigh、Fast 请求，argv 与三个 Codex hook（UserPromptSubmit/Stop/PermissionRequest → 本 launch 的 `cli.ts signal`）及 Git `core.hooksPath` 环境变量按材料原文。
- 预算：本次最多 2 个主 turn（工作、回执），计入本卡 4 turn 上限。
- 隔离 home `/private/tmp/t077-cf-20261011/codex-home`：只复制 auth.json（0600、不归档）；只信任 `/private/tmp/t077-cf-20261011/repo`；只有 git add、git commit 两条 allow 规则；不复制用户配置、hook、skills、rollout。
- 两回合完成、窗格空闲、领导者身份核对后，向该自建 Codex 领导者发 SIGTERM，并在第二次审批前暂停，保留后台、原 shell 与 home。
- 测试 host 在 createThread 异步上下文内预分配 launch UUID 以提前固定 hook 命令：认可，仅限本测试 host，能力 token 独立随机，attempt/session/fence/原生 UUID 仍由真实门禁与 CLI 产生。

不批准：第 2 次启动（另行审批）、任何权限窗口的代批、重试、补 Enter、额外回合。

依据：ticket T-077 真实冲突验收与任务卡 4 turn 预算；AGENTS.md 真实 Codex 验收的隔离 CODEX_HOME 规则。批准引用：`T-077 controller-decision-03 launch-1`。

## 第 1 次启动读回与第 2 次启动批准（2026-10-11 16:5x）

读回 `real-conflict-01/attempt-1`：run.json stage=awaiting_second_launch_approval、observed_root_turns=2；根 rollout 的 turn_context 两回合均为 cwd=a1、workspace-write、network_access=false，model 记录全部为 gpt-6.1-sol、effort xhigh；relay 交付已处理一次（relay_processed=1，另一次为回执重放）；SIGTERM 前领导进程 51348 为 0.162.1 Codex，之后 native-ended 只剩原 shell 51345、session_ended=true；无权限请求、无人工介入事件。

批准第 2 次启动（只此一次）：Launch 2 `7cb79cbe-a73d-49ce-836a-c43d23f1572c`，worktree `.../T-077-9-a2`，argv、三个 hook 与 Git hook 环境按 REAL-APPROVAL-01.md 原文；最多 2 个主 turn，本卡累计不超过 4；同一隔离 home，历史 rollout 逐字节核对不变；结束后按隔离规则归档并删除整个自建 home（auth.json 不入归档）。不批准重试、额外回合或第三个 attempt。批准引用：`T-077 controller-decision-03 launch-2`。
