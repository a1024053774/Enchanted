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

## 复验实例 r2：第 1 次启动批准（2026-10-11 22:1x）

依据：用户授权 answer `20261012T015257Z-ideation-answer-001`（额外 2～4 真实回合；Codex 一律 gpt-6.1-sol xhigh、普通速度、不传 Fast）。审阅 exec/t077 `f6bc3ed9` 的 `REAL-APPROVAL-02.md`：与已批准的 01 相比只换了实例根 `/private/tmp/t077-cf-20261012-r2`、任务号与 worktree，并去掉 `service_tier="fast"`；隔离 home、信任项、两条 allow 规则、三个 hook、Git hook 环境、停止条件与清理不变。

批准第 1 次启动（只此一次）：Launch 1 `8ee0b73a-c031-46ed-8dd6-5e6490029781`，最多 2 个主 turn（本次新增预算 4 之内），完成后 SIGTERM 自建领导者并在第 2 次审批前暂停。周额度只剩约 1%：额度用尽即停下保存现场，不换账号或模型。批准引用：`T-077 controller-decision-03 r2-launch-1`。

## 复验实例 r3：第 1 次启动批准（2026-10-13 11:0x 本地）

依据：用户授权 answer `20261013T144758Z-ideation-answer-001`（原话"A 再批 2 回合，完整重演 (Recommended)"；r3 共 4 回合）与 `20261013T142903Z-ideation-answer-001`（显式 `service_tier="default"`）。审阅 exec/t077 `2e2291ac` 上的 `REAL-APPROVAL-03-LAUNCH-1.md` 与 `real-plan-03-approved.json`（turn_limit=4）：实例根 `/private/tmp/t077-cf-20261013-r3`（运行前不存在），隔离 home、信任项、两条 allow 规则、三个 hook、Git hook 环境同 r2；argv 含 `--no-daemon` 与 `-c service_tier="default"`；新增 runner 守卫：turn_context/thread_settings 出现非 sol/xhigh/default 立即退出。

批准第 1 次启动（只此一次）：Launch 1 `e9cf7727-772d-41db-bd76-e71ffc2d7e93`，最多 2 个主回合，完成后 SIGTERM 自建领导者并在第 2 次审批前暂停。不批准重试或追加；再不过即停下报告。批准引用：`T-077 controller-decision-03 r3-launch-1`。

## r3 第 1 次启动读回与第 2 次启动批准（2026-10-13 本地 11:1x）

读回 `real-conflict-03/attempt-1`：stage=awaiting_second_launch_approval、observed_root_turns=2；根 rollout 中 model 全为 gpt-6.1-sol、effort xhigh、service_tier "default"；relay_processed=1；SIGTERM 前领导进程 99885 为 0.162.1 Codex，之后 native-ended 只剩原 shell 99883、session_ended=true；无权限请求、无人工介入事件。

批准第 2 次启动（只此一次）：Launch 2 `9b06963e-5718-4286-9dd3-921591a3b339`，worktree `.../T077-real-r3/T-077-12-a2`，argv 按 REAL-APPROVAL-03.md（含 `--no-daemon`、`-c service_tier="default"`）；最多 2 个主回合，r3 累计不超过 4；同一隔离 home，历史 rollout 逐字节核对；结束后归档并删除整个自建 home。再不过即停下报告，不追加。批准引用：`T-077 controller-decision-03 r3-launch-2`。

## 用户决定：选 C，两条受控证明后关票（2026-10-14 UTC 01:16 收到）

依据 answer `20261014T011612Z-ideation-answer-001`（用户原话逐字："C 受控证明后关票，并改角色卡 (Recommended)"，见该条目"## 授权"）。不再跑真实回合（累计 9/10 停在 9）。worker 在真实门禁入口上补：(a) 带不支持尾注（A2A-Fence、A2A-Spec-Rev）的重交被 verify 拒收；(b) 同一重交尾注正确时验收并集成。先有红态：断言须在已知坏实现（放过多余尾注的变体）上失败。之后独立审查、合并（含 R8 与 T-076 审查联合核对），通过即关票，Resolution 按 answer 第 2 条。
