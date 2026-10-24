# T-160-1 / a1：红态准备

状态：INCOMPLETE。产品代码尚未修改，正在等待修前真实入口红态。

范围：reviewer 的裸 JSON 输出约束、协议错误保留与拒绝、同一次交付的新审查恢复路径。不增加自动重试，不剥围栏，不改任务卡或他人测试。

已新增 `workbench/tests/test_t160_review_recovery_e2e.py`：真实后台、门禁、原生 Claude CLI 与 Electron；模型回复来自本地脚本化 Messages 接口，不消耗供应商模型回合。失败方式先列在文件头，期望来自 T-160。支持 `--summary` 新文件、`--revision` 修前源码，以及 `--mutant accept-fenced` 反例。

本地命令：

```sh
python3 workbench/tests/test_t160_review_recovery_e2e.py --summary evidence/2026-10-23-batch24/T-160/sandbox-preflight-01.json
```

环境阻断：真实 worker 的交付命令返回 `Exit code 71`、`sandbox-exec: sandbox_apply: Operation not permitted`；测试最终退出 1（交付等待超时）。运行摘要为 `sandbox-preflight-01.json`，真实模型使用 0 回合，测试后台已按正常清理流程停止；运行现场 `/private/tmp/t160-e305nd6b` 保留。不能把这一结果当作 reviewer 缺陷红态。初次夹具的文件内容含换行，随后将夹具收窄为无换行文本，避免原生 CLI 对工具输入的转义影响本票的协议检查；未覆盖原运行证据。

交回主控：运行 `zsh evidence/2026-10-23-batch24/T-160/RUN-OUTSIDE-01.sh`。脚本固定在修前 `3aea74368a020109027c6113a161f32db8614102` 跑同一测试，核对围栏被拒、原文保留、不能集成，并且真实问题页因缺少恢复说明而失败；只在这些条件同时成立时报告红态成立。输出写新路径，截图入本票目录，原现场保留供主控归档。

静态诊断：`qualityProtocol.ts` 已严格 JSON.parse；`core.ts` 将协议失败记录为 `unknown` / `paused`，但 `verify` 只允许 `submitted` / `verifying`；`IssuesPage.tsx` 只展示原始问题正文，缺少明确恢复说明。以上是源码诊断，尚未取得修前 Electron 红态。

待办：取得指定红态后才修根因；同一测试绿态、接受围栏变异反例、相关已有质量链/审查生命周期/问题页回归；真实 haiku reviewer 3 次（上限 9 回合，另写 RUN-OUTSIDE 交主控跑）；完成检查与最终提交。真实模型当前使用 0 回合。

准备阶段检查：Python 编译、zsh 语法、UTF-8 回读及暂存差异空白检查通过。项目状态复核见 `project-map-before-red-handoff.txt`：Problems 0、Stale living docs 0。没有运行或通过产品绿态、变异与真实模型验收。

约束提示：COMMON-FIX 要求界面文案前读 `frontend-less-ai-tone`，在 `~/.codex/skills` 与 `~/.claude/skills` 均未找到；当前可用目录只有 `frontend-production`。本轮未改界面，续作时需主控确认适用替代技能或提供原文件。

已按 worker 角色卡用 `scripts/inbox send` 上报：`20261024T013750Z-worker:b24-t160-issue-001`（非 blocking）。生成的收件箱条目保留在本 worktree，未纳入本票提交的 `.project-map/**` 禁改边界；正文副本为 `skill-issue.md`。
