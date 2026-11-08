# T-257 v3 候选转入与交付交接

状态：INCOMPLETE。卡内候选已原样转入本 attempt，静态核对通过；本 attempt 的真实入口、门禁红绿态与独立审查尚未执行。本文是 2026-11-08 的追加记录，旧报告及其当时的状态保留。

## 身份与候选来源

- task：`a2a+T-257-1`；attempt：`6ca3622b-b0e7-41ad-a21f-7ff810441994`。
- session：`df429446-05ca-46a3-8106-2d0f1eec943b`；fence：3；spec_rev：3；thread：`a6e14bca-e992-4989-923a-c7a787a9d466`。
- 本 attempt 基线：`ec68e0539f886bdbe37df79d085ba85946e3870e`，开始时工作区干净。
- 导入范围：`ebd155141668da18cb2dc09238c5312e1804223a..5484315a5e318bce557dcc32e429f5d251453e84` 中的 `panes.ts`、两个 `test_t257_*` 和本 worker 证据目录，共 25 个文件。使用限定路径的 `git diff --binary`，`git apply --check` 与 `git apply` 均退出 0；未 cherry-pick 旧身份提交。
- 主控真实绿态源码：`a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c`。暂存后 `git diff --cached --exit-code a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c -- workbench` 退出 0，整个 workbench 差异为空。
- 本交接随新身份候选提交；最终完整提交号由提交记录与显式 submit 请求绑定，不把来源提交当成本 attempt 的交付提交。A2A 尾注由钩子生成。

## 范围与行为核对

REALITY GATE: PASS，仅针对“转入已验证来源的相同候选”这一方向；整体业务验收仍为 INCOMPLETE。目标是精确转入并重新交付；非目标为重新设计、改动断言、其他票、权限或门禁契约。转入前已确认本基线与旧基线在导入路径上无差异，没有需要另行决定的合并冲突。

observed：行为由 `workbench/src/panes.ts` 的 `Panes.signal` 和 `noteSubmission` 维护，调用者为 `workbench/src/daemon.ts` 的 `signal` 分支。已认领的 Codex UserPromptSubmit 绑定当前提交的 `active.nativeTurn`，随后 Stop 仍走原匹配条件。生产差异只有这一行赋值和三行原因注释；daemon、hook、门禁和配置无变化。

measured（来源为主控，非本 worker 运行）：[候选检查点](../controller/candidate-a2-checkpoint.md) 及下表的真实入口记录。本 worktree 未包含 controller 文件，本轮从主仓库 `/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-257/controller/` 只读取得这些记录，没有复制或修改它们。

| 主控历史记录 | 来源版本与结果 | 适用边界 |
| --- | --- | --- |
| [green-a2-01.json](../controller/green-a2-01.json) | `a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c`；10 项前提、9 项业务检查通过；检查点记退出 0 | 真实后台、门禁、Codex 0.167.0、本地 scripted Responses；续跑结束 idle，排队消息只发送一次，结束后 reclaim 成功，两个实际工作阶段拒绝回收 |
| [red-a2-parent-01.json](../controller/red-a2-parent-01.json) | 同一测试对 `ebd155141668da18cb2dc09238c5312e1804223a`；10 项前提成立、5 项目标失败；检查点记退出 1 | 命中 busy、队列未继续及 reclaim=worker_working；不是依赖或初始化失败 |
| [regression-a2-t252-codex-01.json](../controller/regression-a2-t252-codex-01.json) | 检查点绑定上述候选工作区；7 项通过，退出 0 | 不可信请求拒绝、回合结束、问题记录、旧 attempt 回收与重派；不宣称全套回归通过 |

unknown：当前 attempt 的完成条件、红态、独立审查和最终门禁结果。下一步由主控/门禁在本候选新验证工作区运行卡内命令，保留新的摘要；v3 命令临时链接同仓库既有依赖，退出只 unlink 自己创建的链接。worker 本轮没有执行该环境准备，也没有在沙箱中重试 `/private/tmp` 真实 CLI。

## 本轮检查与证据边界

命令、退出码及实际输出见 [static-checks-v3.json](static-checks-v3.json)。本机 Python 3.9.6、Node v26.5.0。以下检查仅证明转入与静态性质：

- 25 个导入文件逐文件原始字节一致；暂存后的卡内候选与旧交付一致。旧 `RESULTS.md` 随后仅在末尾追加本交接索引，其余历史证据保持原样。
- `node --check` 检查 panes.ts 与 TS 开发测试，Python AST/compile 检查真实入口测试、内嵌 hook observer 与模块 runner，均退出 0；未生成字节码缓存。
- 冻结文件 `acceptance/`、`REVIEW.md`、既有 T-252 测试相对本 attempt 基线无差异；`git diff --cached --check` 退出 0。
- 暂存前曾运行整体 workbench 比较，退出 1：两个新增测试尚未进索引，Git 将其显示为删除。原始工具输出保留在 JSON（工具已截断），没有把它改写成通过。逐文件检查和暂存后的整体比较确认文件在场且内容一致。
- 开始的 project-map status 退出 0，Problems 0、Stale 0；结束检查退出 1，Problems 0、README stale 1。该问题已在候选检查点指向主控处理（问题 `0d0b44c6-3d69-450a-a893-cbad898a085a`）；不重复 issue，不越界改 README 或地图。

按 `design-integrity-review` 做实现者自查：结构扫描退出 0，findings 与 acceptance_changes 均为空。生产没有新增异常吞噬、fallback、retry、兼容路径、平行 API、定时 idle 或回收放行；绑定仍由现有模块拥有，符合 Deep modules。`REVIEW.md` 的敏感路径中 panes.ts 条目指 agy 信任代码，本改动未触及该代码；回合状态仍属于 What matters 的明确审查范围。本自查不免除任务卡要求的门禁审查及主控负责的集成前证据批准。

按 `behavioral-acceptance-review` 与 agent-products 参考核对证据边界：oracle 来自票据 Acceptance，包含“结束可回收”和“真正在工作仍拒绝”两个方向。真实入口测试用随机排队 marker、原生 task_complete、队列投递和门禁 reclaim 核对结果；已知坏父版本被同测试按业务断言拒绝。编排状态、异步事件、身份范围、CLI 交互和门禁副作用适用；检索/记忆、媒体生成、供应商模型理解不适用本票。历史模块 104 场景的有界排列与种子只证明模块边界，不能替代真实 CLI。本轮自查状态 INCOMPLETE，尚无新 attempt 的独立验收；没有自行派 reviewer 或其他 agent。

Ubiquitous language 沿用 CONTEXT.md 的原生会话、提交、Attempt 和 Submit。此次只是既有候选转入，不增加跨层 Tracer bullet。旧 `behavioral-review-v2.md` 中“尚缺真实绿态”是写作当时的事实，后续主控实测由上表补充，不改写旧报告。

## 交付与主控下一步

worker 以本身份提交后运行任务卡的显式 submit 命令，然后结束回合，由 Stop hook 转交请求。`queued=true` 只表示请求文件已排队，不是 accepted、verified 或 integrated。本轮不发不必要的 status/issue。

主控接续核对本候选与历史实测 workbench 的一致性，经门禁重跑完成条件、坏父版本红态与新开的独立审查。独立 reviewer 按票据重建 oracle，若做模块变异需明确其边界。主控处理已知 README stale 并完成适用的用户证据批准后，才可经门禁集成。本轮没有安装、重启、集成或 push。

额外可写目录：`[]`，没有额外目录改动。请求目录只保存本次移植补丁和门禁请求，不进入 Git。没有产生缓存、大 fixture、数据库或 hc 私有目录；没有需要清理的本轮测试现场，没有删除旧证据。正式后台仍是旧安装版本，submit 回执可能再次触发 busy；由主控跟进，不通过手改状态或共享 Git 元数据修复。

**Works**：候选与原交付逐文件一致，整个 workbench 与主控真实绿态版本一致；本身份真实验收尚待门禁运行，整体 INCOMPLETE。

**No regression**：冻结验收不变、静态检查通过；历史 T-252 的 7 项回归与其版本可追溯，本轮未运行回归或全套测试。

**Risk / undo**：新 attempt 的独立门禁结果未知，正式运行时仍可能卡 busy，README stale 由主控接续。候选未集成；需要回退时在授权流程中撤销 panes.ts 的 4 行新增，保留历史与本轮证据。
