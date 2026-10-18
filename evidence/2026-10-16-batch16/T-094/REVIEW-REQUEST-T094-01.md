# T-094 独立审查请求 01

task `T-094`，attempt `a1`，ready_rev 1；worker `s16-t094`，launch `launch-efca9e180a594c2e98ec594874eaf253`，受管 session `1f06c59c-a447-47e4-8075-9a7571db35d3`，原生 session `01a14ae2-907f-7692-a14d-480a56c947f7`。启动配置为 gpt-6.1-sol / xhigh，codex-cli 0.163.0；配置不证明实际供应商 tier。

请执行主控新开干净、只读的 reviewer 会话，依据任务卡、裁定和原始证据给出独立结论。worker 整票状态为 **INCOMPLETE：待独立审查与最终门禁验收**。本请求不代替验收、submit、integration 或 ticket 关闭。

## 冻结对象与授权边界

实现及验收锚点：`b612e6f68680a5a308f8a91b6bd0e09469b86493`。最终审查对象是**包含本请求的冻结提交**，完整 SHA 由 worker 的 `T-094 FROZEN <sha>` 交接，执行主控逐字传给 reviewer。相对锚点只更新 RESULTS、TEST-PLAN、新增本请求、归档清单和冻结检查记录；请先核对该差异，再绑定最终完整 SHA 写结论。冻结后 worker 不再修改候选。

任务起点：`61786370428c3ec5f894ea60acccf2695d54c2dc`。完整审查范围为起点至冻结 SHA 的 diff，主要文件：

- `scripts/launch-worker`：1500ms 稳定窗口、100ms 目标采样间隔、保持 30 秒 shell 检查总期限；失败 stdout/stderr、错误身份、前台 argv 与半成功分类。
- `scripts/test_launch_worker_failure.py`：命令入口边界测试及旧实现反事实；Herdr / Codex 为显式替身。
- `acceptance/test_launcher_shell_ready_e2e.py`、`acceptance/test_herdr_traceability_e2e.py`：用户裁定放开的两个验收文件，断言就绪行为和启动时实际版本；其他 acceptance 文件未改。
- `README.md`：稳定窗口与误判局限；本目录为任务卡、中文记录、重放脚本和归档清单。

授权依据：原[任务卡](task-card-T-094-1.md)及本对话主控裁定。#57 要求入口保留失败 pane、由主控处置；#63 否决写 shell 回执，裁定稳定窗口并接受其局限，同时授权 README 说明；#78 转达用户选 A，依据 main `c06a73179` 的 T-094“裁定”节和收件箱 `20261018T004018Z-ideation-answer-001`，只放开上述两个 acceptance 文件，不放宽其他断言；#80 明确接受第 2 条用错误记录版本变异体取得红态。

## 需要独立核对的行为

1. 每个合格采样只有本次 pane 的 shell 占据前台组；任一不合格采样重计稳定窗口。至少连续 1500ms 后只调用一次 agent start。全局 30 秒截止点不随重计时延长，查询跨越截止点也不能放行。
2. 超时保存最后一次成功采样的前台 argv，报错退出、保留 pane，不重试。收到 busy 后首次进程查询的 argv 进入错误身份，原始 Herdr stderr 保留；不得将失败后的采样冒称拒绝时刻的精确状态。
3. 进程已起但未命名记录 `outcome=started_unregistered`，不报告成功；成功启动消费入口拒收这种 phase=failed 的记录。注册状态查询失败保持 unknown，不推测名称缺失。
4. 入口不关闭失败 pane。复现脚本只关闭本次 split 返回的 pane，且只启动 Codex 首屏、不发模型提示；不修改 Herdr、用户 `.zshrc`、全局配置或用户已有 pane，不写额外回执命令。
5. 两个修订验收的预期来自独立采样和同一次 --version 的外部回执。不要仅凭新测试全绿接受它们；核对其他断言、九项尾注与配置绑定没有放宽，并检查已知坏实现确实因目标行为被拒绝。

## 条件、红绿与原件

外置根统一为 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-094/`。清单均不带校验值，按文件数与字节数核对；原失败、历史状态不回写。

| 条件 | 证据与原件入口 | 已知结果及边界 |
| --- | --- | --- |
| 真实红态与占用者 | [red-01-summary](red-01-summary.json)、[red-01 清单](red-01.archive.json)、[busy-01-summary](busy-01-summary.json)、[busy-01 清单](busy-01.archive.json) | 起点存在 busy；busy-01 的两次失败后捕获 conda hook / activate 及 zsh 子进程链。先前 Git 提示符推测已更正 |
| 稳定窗口与总期限 | [稳定窗口摘要](stable-contract-summary-01.json)、[绿态](stable-contract-green-02.txt)、[归档](stable-details-01.archive.json) | 同一修正夹具旧红新绿；200ms 空闲后派生子进程，窗口须重计；持续占用在 30 秒报 argv，9 项通过 |
| 真实启动绿态 | [busy-02-summary](busy-02-summary.json)、[busy-02 清单](busy-02.archive.json)；外置 busy-02 的 run.json、herdr.jsonl、原始启动记录 | 10 次首屏启动均成功，均核对至少 1500ms 稳定采样；10 次自建 pane 清理成功，0 模型回合。实现绑定 acf747d948be03df6ea91bb852bdfa545e938ee0，与当前产品及该驱动源码无差异 |
| 半成功反例 | [unregistered 摘要](unregistered-01-summary.json)、[清单](unregistered-01.archive.json) | 真实未命名 Codex 进程加明确错误注入；记录 started_unregistered，成功消费入口拒收。分类代码与当前相同；不冒充自然出现的原始竞态 |
| 修订验收第 1 条 | [18 步命令与结果](revised-acceptance-summary-01.json)、[归档](revised-acceptance-01.archive.json)；外置 old-test_delayed_shell_then_commit、old-test_child_foreground_times_out_with_argv 与对应 new-* | 旧 617863704 在稳定窗口与 argv 两项为红；新候选 LauncherContract 7 项通过 |
| 修订验收第 2 条 | 同一归档中的 old-version、wrong-version、new-test_commit_no_verify_and_plain_counterexample 及 version-receipts.jsonl | **红态来自错误版本变异体，依据主控 #80 裁定**。旧实现正确记录版本，保留其正例；原固定版本断言失败属于环境漂移预期。新候选 Contract 7 项通过 |
| 其他断言与冻结边界 | [断言范围核对](revised-assertion-scope-01.json)、[冻结检查](freeze-checks-T094-01.json) | 非目标原方法及目标剩余断言保持；本次仅文档 / 证据说明变动，未重跑已完成测试 |

版本红态裁定原文来自本对话主控 #80 / 主控 #8：

> 对版本这条，红态改用“记录了错误版本”的变异体来取得，你已经做到了，这个变异体被拒绝，可以接受。

`revised-acceptance-01/run.json` 和仓库摘要仍保存原始 status=INCOMPLETE / rc=1：那次驱动尚要求 old-version 必须失败，实际为 rc 0。主控 #80 已接受变异体替代该项红态；没有把旧版本正例回改为失败，也没有改写原始 requested_exit 或运行状态。归档已核对为 268 文件、864829 字节。

## 限制与审查输出

稳定窗口不证明初始化完成：若初始化空闲超过 1500ms，或子进程只在采样之间运行，仍可能误判。该局限已获主控 #63 接受并写入 README。busy 后的采样有时间差；未知状态保留诊断，不作确定因果推断。10 次实跑是本轮验证，不证明长期可靠性、吞吐或成本改善。

首轮跨进程 monotonic 夹具失真记录保留；正式红绿使用修正后的跨进程 Unix 时间，生产内部始终使用单进程单调时钟。原始时钟输出首行的尾随空格按证据原样保留，未计作完整空白检查通过。README 既有门禁段落过时已另报主控，超出本票范围。

请在干净只读会话中审查最终完整 SHA、原始数据及已知坏实现，按 PASS / INCOMPLETE / BLOCKED / NO_GO 报告，逐项说明依据与缺口。不要把 worker 的测试结论当作独立审查结论；不要修改代码、验收、原件或其状态，不要 submit / integrate 或操作用户 Herdr。需要新运行时交执行主控以新标签安排。审查通过后仍由主控经唯一门禁完成验收和集成。
