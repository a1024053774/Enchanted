# T-160-1 / a1：reviewer 协议错误与同一次交付恢复

状态：INCOMPLETE。修复与 RUN-OUTSIDE-02 已准备；修后真实 Electron 绿态、端到端变异、现行回归和真实 haiku 3 次仍待主控运行。当前真实模型使用 **0 回合**，不能据状态级检查宣称整票通过。

## 范围与实现

- `workbench/roles/reviewer.md` 与门禁生成的启动提示都要求：最终消息为裸 JSON，不带任何代码围栏或说明；输出前自检 JSON.parse、首尾字符、身份与必需报告字段。
- 严格解析器 `qualityProtocol.ts` 保持原样。围栏、自然语言和非法字段仍拒绝；原始错误事件、原文与现有问题正文格式不变。
- 问题页显示格式/字段原因，可展开原文；当前 attempt、当前 review 与问题所属 thread 相符时，显示“为同一次交付新开审查”。旧记录也使用同一存储格式显示，无额外兼容分支。关闭问题不恢复任务；只要交付仍停在这一次审查上，关闭后也保留恢复按钮。
- 按钮经 IPC 调用现有 `verify` 门禁，绑定原 attempt 和失败的 review id。在同一操作锁下验证原协议失败事件、候选、规格、机械验收、启动身份、worker 与审查目录边界；确认原审查空闲、停止、归档后清理临时副本/审查 worktree，再为同一次交付新开独立会话。旧错误与原文事件保留，不追认旧输出，不加自动重试。任何带旧 review id 的恢复都不能落入普通 verify 去验收更新的交付。
- 回收操作写入 intent；若停止或清理中断，后续恢复拒绝 `review_recovery_unknown`，保留未知结果交执行主控核对，不重复外部动作。候选、attempt、机械验收版本不因成功恢复而改变。

## 已取得的证据

| 检查 | 结果与边界 |
| --- | --- |
| 修前真实 Electron 红态 | PASS（红态成立）。主控 #46 返回 RUN-OUTSIDE-01 rc=0；`red-20261024T013902Z-t160-red-outside-cp6P1m.json` 中 `fenced_output_rejected`、`raw_preserved`、`failed_review_cannot_integrate` 成立，`recovery_guidance_visible` 是指定失败；同名 PNG 为截图。现场 `/private/tmp/t160-y3qa2us6` 保留。 |
| 本地初次真实入口 | 环境阻断，不能算缺陷红态。`sandbox-preflight-01.json`：真实 worker 交付命令返回 `Exit code 71` / `sandbox-exec: sandbox_apply: Operation not permitted`，最终交付等待超时；现场 `/private/tmp/t160-e305nd6b` 保留，后台已停止。初次夹具含换行，后将夹具收窄为无换行文本，未覆盖旧证据。 |
| Codex Stop 状态级修前反例 | PASS（红态成立，仅状态级）。`idle-red-parent-01.json` 在明确修前版本 `3aea74368a020109027c6113a161f32db8614102` 失败于匹配协议错误不能回收、旧 Stop 清除了替换后的提交；`idle-red-01.json` 是本地首次定位运行。 |
| Codex Stop 状态级绿态 | PASS（仅状态级）。`idle-green-01.json` 的 7 案全通过：对应提交已匹配完成的解析失败可停止；未匹配 Stop、替换提交、其他 unknown、其他审查错误、其他角色、转交抛错均不可停止。 |
| 已知坏实现：允许任意 unknown 回收 | PASS（坏实现被拒）。`idle-mutant-any-unknown-01.json`：未匹配 Stop、替换提交及其他 unknown 等案以“缺少预期拒绝”业务断言失败，且记录错误停止次数。 |
| 已知坏实现：忽略提交替换 | PASS（坏实现被拒）。`idle-mutant-ignore-submission-01.json` 在 `different_submission_not_reclaimable` 失败，证明测试不是只查一个失败标记。 |
| 构建与语法 | PASS。标准 `node app/build.mjs --slot …` 的 `build-03.json` 是当前界面/运行时代码构建；临时构建输出已清理。`build-01.json`、`build-02.json` 是较早候选，不替后续改动背书。三次均有现有的大 chunk 提示，无构建错误。Python 编译、Node TS 语法、zsh 语法、UTF-8 回读与 diff 空白检查通过。 |
| 旧协议回放诊断 | INCOMPLETE。`protocol-regression-01.json` 保留 `test_t082_review_protocol.ts` 使用 `t152_real_review_submit.json` 的失败：旧输入 task=`t082-real-03` 不符合当前项目限定 task id，报 `Error: task`。未修改他人测试或输入，也不将这次运行计入当前回归通过。 |

状态级夹具只替换外部进程/原生记录收集，实际运行 `Panes.signal`、信任/身份信封检查、`readThread` 与 `stopThread`；假 PTY 只提供退出事件。它不能证明真实 Codex CLI、进程退出或沙箱行为。真实进程与界面恢复仍由 RUN-OUTSIDE-02 的 Claude 端到端路径验证。

## 授权扩展与最小改动

原卡未列 `workbench/src/panes.ts`。静态诊断发现 Codex 的匹配 Stop 在 reviewer 解析失败后仍将运行状态置为 unknown，导致 readThread 判为 running、stopThread 拒绝回收。已通过角色规定的 inbox 上报 `20261024T014902Z-worker:b24-t160-issue-001`，正文副本为 `runtime-scope-issue.md`。

用户在当前会话选择“允许这一处最小运行时修改”；执行主控 #48 进一步限定：“只在‘该 reviewer 的审查提交协议解析失败，且该次提交对应的 Stop 已匹配完成’时补 idle/可回收事实；其他 unknown 一律照旧拒绝。”

实际仅改 `panes.ts:1549–1556` 附近的局部 Stop 完成分支：检查 reviewer + invalid_review_result，核对仍是原 active 对象、原 native turn、原 session；替换提交保持 unknown，不清除新提交；完全匹配才在保留失败/阻塞标记的同时记录 idle。**未放宽 stopThread 对 unknown 的拒绝条件**。此局部补丁供主控与之后的 T-157 合并时核对。

技能缺失问题 `20261024T013750Z-worker:b24-t160-issue-001` 已由主控 #46 裁定：frontend-less-ai-tone 已整合进 frontend-production。本次按 `references/look-and-copy.md` 执行，不再等待此项。两条按角色卡生成的 inbox 文件留在本 worktree，未提交 `.project-map/**`；本票正文副本均在 evidence 内。

## 交回主控

```sh
zsh evidence/2026-10-23-batch24/T-160/RUN-OUTSIDE-02.sh
```

脚本逐项执行，失败即停止，不自动重试，每次写新的 summary 与日志路径：

1. 状态级修前/绿态及两个坏实现；不请求模型。
2. 真实后台、原生 Claude CLI（本地脚本化接口）与 Electron：围栏拒绝、原文保留、不能集成、按钮恢复、绑定不变、新审查身份、旧审查停止归档与清理、旧错误留存、过期和重复恢复拒绝。
3. 同一端到端测试的 `accept-fenced`、`unbound-review`、`reuse-failed-review` 三个坏实现，必须在指定业务断言失败，环境错误或超时不算捕获。
4. 现行 `test_t132_issues_panel_e2e.py`（问题页）与 `test_t137_reflect_e2e.py`（正常独立审查回收、评分、集成）回归。不将历史 controlled-quality host 与当前产品混跑。
5. `test_t160_real_reviewers.py`：真实 haiku reviewer 3 次。为了保留真实生产启动路径，使用 3 个独立真实 haiku worker，各至多 2 回合（含交付 ACK），加 3 个 reviewer 各 1 回合，总上限 9。独立 HOME 先做原生登录预检；不写用户配置；记录完整 reviewer argv、版本、身份、原生模型事实与实际回合数。输出须有有效门禁结果，或被拒后原文与恢复按钮都存在。不自动点击真实恢复按钮。复制的登录文件仅在进程停止后删除，认证不就绪则在模型回合开始前失败。

3 次真实 reviewer 的逐次结果、修后完整绿态、独立候选审查和最终状态待本脚本返回后填写。没有可靠性、成本或吞吐收益主张。
