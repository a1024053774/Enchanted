# T-006 阶段 1 观察记录

结论：INCOMPLETE。本轮完成两次有界可见采样；T-006 的实现与验收仍未完成，未给出产品 PASS 或实现审查结论。观察者 a2a-monitor 仅保存 monitor 证据，没有认领、提交、集成、控制 worker、启动子 agent 或修改 Git。

依据为 `.project-map/tickets/T-006-managed-delivery.md`、冻结执行规格 `.project-map/specs/managed-delivery-2026-10-06.md`、`intent.md`、`CONTEXT.md`、本 run 的 `commands.jsonl` 和 build/check 文件事实。遵循 Tracer bullet、Deep modules、Ubiquitous language 的当前规格；本轮不判断其实现是否满足。开始与结束的 project-map status 均为 Problems 0、Stale living docs 0，T-006 仍由 a2a-build claim；这不等于业务验收通过。

## 采样范围与原始证据

原始命令、UTC 起止时间、退出码、stdout/stderr 和文件事实保存于 [monitor-phase1-samples.jsonl](monitor-phase1-samples.jsonl)。每次仅对 `a2a-build`、`a2a-check` 执行 `herdr agent get NAME` 和 `herdr agent read NAME --source visible --lines 60`。

| 采样 | UTC 时间 | build | check |
| --- | --- | --- | --- |
| 1 | 2026-10-06 04:53:58.863–04:53:58.887 | working；可见红态及环境核对命令 | working；可见契约读取、验收范围声明和版本命令 |
| 2 | 2026-10-06 04:54:21.172–04:54:21.204 | working；新增针对自身 pane/agent 的读取与 process-info | working；正文与采样 1 相同，Working 计时增加 |

两次开始时间相隔约 22.31 秒，没有每秒轮询，没有等待其全部完成。get 与 read 顺序执行，不是同一时刻的原子快照。visible 只能覆盖当前屏幕；折叠内容、屏幕外动作、两次之间瞬变和之后进展均不在证据覆盖内。check 的正文未更新不能证明挂起，Working 计时增加也不能证明业务进展。

两次 live 身份一致，workspace 均为 wF、tab 均为 wF:t1、cwd 均为本项目：

| agent | pane | terminal | Herdr 观察到的原生 session |
| --- | --- | --- | --- |
| a2a-build | wF:p4 | term_65d24ba206b5b3a | 01a10f8e-b1d6-7092-9f75-041108f87a96 |
| a2a-check | wF:p5 | term_65d24bbbde9293c | 01a10f8e-bbc3-7db2-adf4-3e197fe02c46 |

以上 session 来源为 `herdr:codex`，不等于受管理 CLI 分配的 task/attempt session_id。未读取其他项目或会话文件；build 的目标可见屏幕中偶然包含未限 workspace 的全局 inventory 输出，本观察者没有追踪其中目标。

## 声明参数与实际可观察参数

`commands.jsonl` 第 2、4 行首次启动，以及第 18、22 行重启请求 `-m gpt-6.1-sol`、`model_reasoning_effort="xhigh"`、`service_tier="fast"`、`--no-alt-screen`。第 6、24 行 monitor 请求 `gpt-6.1-sol`、`high`，未显式请求 Fast。重启加入 `check_for_update_on_startup=false`。

Herdr 返回的启动 argv 中保留了转义引号；本轮没有读取配置解析器或用私有日志推断。两次 worker 的实际可见 UI 均显示 `GPT-6.1-Sol xhigh fast`；采样 2 的 build 屏幕还显示自身 process-info 的 argv，与所请求参数相符。commands 第 32 行保存的 monitor UI 显示 `GPT-6.1-Sol high`。这些证明本地请求及 UI 声明一致，不能证明供应商实际使用的模型、推理档位、Fast service tier 或费用。Fast 仍仅是请求配置，本轮没有供应商 tier 回执。两个 worker UI 均显示 `3 warnings`，内容未展开，原因未知；不据此推断配置不符。

## 启动瞬变与人工介入

- commands 第 2、4、6 行 start 返回成功且 idle；第 7–9 行 prompt 也返回成功，但没有 wait/activity 完成证据。第 10–12 行在 04:51:55 返回 agent_not_found。
- 第 13–16 行保存了 pane 无 agent 的 unknown 状态及自动更新输出；build 可见 `Updating Codex CLI from 0.160.0 to 0.160.1`，随后要求重启。早先的 idle/start 成功未证明任务开始或完成。版本更新为历史可见事实，本观察者没有执行更新或重启。
- 第 18 行 build 重启返回 agent_not_ready；第 19 行可见目录信任对话。第 20 行记录主控 send-keys enter，第 21 行显示 Codex v0.160.1 首页。此为权限相关人工介入记录，commands 本身不证明该操作的人工授权来源，本观察者不替它判定已授权或越权。
- 第 26–28 行重新投递，随后第 29 行及本轮采样可见 working。pane/terminal 在重启前后保持同一容器身份，不能因此把旧进程与新 session 当作同一执行。

本轮所读取的 commands 截至第 32 行没有 wait 超时记录。因此未观察到“超时但仍有进展”的实例，也不宣称不存在后续超时。idle/done 只属于终端生命周期，不是 submit、acceptance 或 integration。

## 文件与验收边界

04:54:08.222 与 04:54:21.204 的文件事实均显示：`coop.py`、`README.md`、`acceptance/test_coop_e2e.py` 尚不存在；run 中已有 `build-red.json`，尚无 build-result 或 check 运行结果文件。

`build-red.json` 时间为 04:53:50.026 UTC，保存完整 create argv、Python 3.9.6、输入 base `db231087d17f915966e09767aa733f022e94b831` 和原始 stderr。实际 exit 2，因为 coop.py 缺失；文件明确分类为新功能缺失的 expected-red，不冒充旧缺陷，也不满足 known-bad gate mutant 的行为红态要求。两次文件事实中该文件大小、mtime 和内容一致。

当前缺少独立 CLI 验收执行、known-bad mutant 行为拒绝、真实程序 dispatch/submit/verify/integrate/reclaim 证据及最终候选版本。T-006 验收框仍未勾选；这一阶段的缺失是未完成边界，不能当作已验收或发布结论。check 屏幕明确声明其测试不调用 Herdr、不据此声称真实模型调度通过；尚未核实其最终测试产物。

未在本次可见输出及所核对文件中观察到越界写入；未做全仓变更审计、Git diff 或文件写入归因，因此不能证明整个运行无越界写入。build 的可见全局 inventory 读取应记录为读取范围观察，而不是越界写入证据；没有追读其他项目。

阶段 1 到此停止。后续采样须由主控另行给出第二阶段任务，不能用这两次快照代表整个运行。
