# T-160-1 / a1：reviewer 协议错误与同一次交付恢复

状态：INCOMPLETE。RUN-OUTSIDE-02 的真实 Electron 绿态、端到端变异和现行回归已通过；真实 haiku 段在模型启动前因隔离登录缺失失败。已修测试的凭据准备并提供只跑真实段的 RUN-OUTSIDE-03。当前核对的真实模型使用 **0 回合**，3 次真实 reviewer 尚未完成，不能宣称整票通过。

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
| 修后真实 Electron 绿态 | PASS。主控 #51 返回并逐项核对 `green-20261024T020931Z-t160-verify-outside-U5psYJ.json`：16 个检查通过，覆盖闭合问题后仍能从按钮恢复、同候选/同 attempt/同验收的新会话、停止归档清理、原文留存与过期/重复恢复拒绝；两张 PNG 保留，已查看恢复后的页面。测试使用真实原生 CLI 与脚本化模型，不作为真实模型输出证明。 |
| 端到端已知坏实现 | PASS（坏实现被拒）。同一批 `mutant-accept-fenced`、`mutant-unbound-review`、`mutant-reuse-failed` 摘要分别在 `fenced_output_rejected`、`unbound_recovery_rejected`、`same_delivery_new_review` 的指定业务断言失败，无环境/超时冒充捕获。 |
| 现行问题页与审查集成回归 | PASS。同批 `regression-issues` 的 6 项、`regression-review-integration` 的 10 项通过，摘要与截图保留。 |
| 本地初次真实入口 | 环境阻断，不能算缺陷红态。`sandbox-preflight-01.json`：真实 worker 交付命令返回 `Exit code 71` / `sandbox-exec: sandbox_apply: Operation not permitted`，最终交付等待超时；现场 `/private/tmp/t160-e305nd6b` 保留，后台已停止。初次夹具含换行，后将夹具收窄为无换行文本，未覆盖旧证据。 |
| Codex Stop 状态级修前反例 | PASS（红态成立，仅状态级）。`idle-red-parent-01.json` 在明确修前版本 `3aea74368a020109027c6113a161f32db8614102` 失败于匹配协议错误不能回收、旧 Stop 清除了替换后的提交；`idle-red-01.json` 是本地首次定位运行。 |
| Codex Stop 状态级绿态 | PASS（仅状态级）。`idle-green-01.json` 的 7 案全通过：对应提交已匹配完成的解析失败可停止；未匹配 Stop、替换提交、其他 unknown、其他审查错误、其他角色、转交抛错均不可停止。 |
| 已知坏实现：允许任意 unknown 回收 | PASS（坏实现被拒）。`idle-mutant-any-unknown-01.json`：未匹配 Stop、替换提交及其他 unknown 等案以“缺少预期拒绝”业务断言失败，且记录错误停止次数。 |
| 已知坏实现：忽略提交替换 | PASS（坏实现被拒）。`idle-mutant-ignore-submission-01.json` 在 `different_submission_not_reclaimable` 失败，证明测试不是只查一个失败标记。 |
| 构建与语法 | PASS。标准 `node app/build.mjs --slot …` 的 `build-03.json` 是当前界面/运行时代码构建；临时构建输出已清理。`build-01.json`、`build-02.json` 是较早候选，不替后续改动背书。三次均有现有的大 chunk 提示，无构建错误。Python 编译、Node TS 语法、zsh 语法、UTF-8 回读与 diff 空白检查通过。 |
| 旧协议回放诊断 | INCOMPLETE。`protocol-regression-01.json` 保留 `test_t082_review_protocol.ts` 使用 `t152_real_review_submit.json` 的失败：旧输入 task=`t082-real-03` 不符合当前项目限定 task id，报 `Error: task`。未修改他人测试或输入，也不将这次运行计入当前回归通过。 |
| RUN-OUTSIDE-02 真实登录失败 | INCOMPLETE（夹具登录缺失，非审查协议失败）。`real-haiku-3-20261024T020931Z-t160-verify-outside-U5psYJ.json` 报 `isolated_login_ready`，auth 返回 1 / loggedIn false / authMethod none。`outside-02-audit.json` 核对该运行 trials 为空、原生 transcript 数 0，现场无启动配置、daemon pid、数据库、回合账本：真实消耗确认 0 回合。 |
| 新凭据准备的合成检查 | PASS（仅本地复制逻辑，不是登录证明）。`login-copy-check-01.json` 的 6 项核对来源选择、access token 保留/refresh token 移除、0600、源对象不变、已有副本不覆盖、过期登录拒绝；读取器输入为合成数据，未访问 Keychain 或模型。新 Python 与 zsh 语法、diff 检查通过。 |

状态级夹具只替换外部进程/原生记录收集，实际运行 `Panes.signal`、信任/身份信封检查、`readThread` 与 `stopThread`；假 PTY 只提供退出事件。它不能证明真实 Codex CLI、进程退出或沙箱行为。真实进程与界面恢复已由 RUN-OUTSIDE-02 的 Claude 端到端路径验证。

RUN-OUTSIDE-02 的候选为 `788df01fea0b6fadbdf3a650e91c63d71ac259f0`，日志目录 `/private/tmp/t160-verify-outside-U5psYJ`。本轮只改本票真实运行测试、脚本和证据；`git diff 788df01fea0b6fadbdf3a650e91c63d71ac259f0 -- workbench/src workbench/app workbench/roles` 为空，未改变已验证的产品路径。旧失败与原始现场均保留。

主控 #51 授权沿用 T-163 的凭据准备。本票复用现有 `claudeLoginFiles.read_auth` 的精确文件/Keychain 读取路径，在一次性 HOME 的 `.claude/.credentials.json` 以 0600 写入去掉 refreshToken 的副本；登录剩余有效期不足 10 分钟即拒绝，不刷新用户共享登录。受管 Panes 当前不透传 CLAUDE_CONFIG_DIR，因此预检和实际受管 CLI 都使用其相同的默认 HOME/.claude 目录，不用仅预检生效的环境覆盖，也不改产品启动参数。停止所有自有资源后保存脱敏的原生 transcript，再删除整个隔离 HOME，包含可能的登录备份；回收未知时保留现场。凭据不进入命令行、报告或 Git。

## 授权扩展与最小改动

原卡未列 `workbench/src/panes.ts`。静态诊断发现 Codex 的匹配 Stop 在 reviewer 解析失败后仍将运行状态置为 unknown，导致 readThread 判为 running、stopThread 拒绝回收。已通过角色规定的 inbox 上报 `20261024T014902Z-worker:b24-t160-issue-001`，正文副本为 `runtime-scope-issue.md`。

用户在当前会话选择“允许这一处最小运行时修改”；执行主控 #48 进一步限定：“只在‘该 reviewer 的审查提交协议解析失败，且该次提交对应的 Stop 已匹配完成’时补 idle/可回收事实；其他 unknown 一律照旧拒绝。”

实际仅改 `panes.ts:1549–1556` 附近的局部 Stop 完成分支：检查 reviewer + invalid_review_result，核对仍是原 active 对象、原 native turn、原 session；替换提交保持 unknown，不清除新提交；完全匹配才在保留失败/阻塞标记的同时记录 idle。**未放宽 stopThread 对 unknown 的拒绝条件**。此局部补丁供主控与之后的 T-157 合并时核对。

技能缺失问题 `20261024T013750Z-worker:b24-t160-issue-001` 已由主控 #46 裁定：frontend-less-ai-tone 已整合进 frontend-production。本次按 `references/look-and-copy.md` 执行，不再等待此项。两条按角色卡生成的 inbox 文件留在本 worktree，未提交 `.project-map/**`；本票正文副本均在 evidence 内。

## 交回主控

```sh
zsh evidence/2026-10-23-batch24/T-160/RUN-OUTSIDE-03.sh
```

当前脚本只运行第 5 项的真实 haiku 段，不重复前四项。先核对已有真实摘要的总消耗为 0 且无观察未知，再预留完整 9 回合；每次写新的 summary 与日志路径，不自动重试。以下前四项已由 RUN-OUTSIDE-02 完成：

1. 状态级修前/绿态及两个坏实现；不请求模型。
2. 真实后台、原生 Claude CLI（本地脚本化接口）与 Electron：围栏拒绝、原文保留、不能集成、按钮恢复、绑定不变、新审查身份、旧审查停止归档与清理、旧错误留存、过期和重复恢复拒绝。
3. 同一端到端测试的 `accept-fenced`、`unbound-review`、`reuse-failed-review` 三个坏实现，必须在指定业务断言失败，环境错误或超时不算捕获。
4. 现行 `test_t132_issues_panel_e2e.py`（问题页）与 `test_t137_reflect_e2e.py`（正常独立审查回收、评分、集成）回归。不将历史 controlled-quality host 与当前产品混跑。
5. `test_t160_real_reviewers.py`：真实 haiku reviewer 3 次。为了保留真实生产启动路径，使用 3 个独立真实 haiku worker，各至多 2 回合（含交付 ACK），加 3 个 reviewer 各 1 回合，总上限 9。独立 HOME 先做原生登录预检；不写用户配置；记录完整 reviewer argv、版本、身份、原生模型事实与实际回合数。输出须有有效门禁结果，或被拒后原文与恢复按钮都存在。不自动点击真实恢复按钮。复制的登录文件仅在进程停止后删除，认证不就绪则在模型回合开始前失败。

3 次真实 reviewer 的逐次结果、独立候选审查和最终状态待 RUN-OUTSIDE-03 返回后填写。没有可靠性、成本或吞吐收益主张。
