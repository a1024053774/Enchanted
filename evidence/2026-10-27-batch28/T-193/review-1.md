# T-193 独立只读审查

## STATUS

**NO_GO**。两处已复现的额外目录授权问题阻断放行；另有产品说明和回归测试未同步。

审查对象仅为 `/private/tmp/t193-dev2`：基线 `33debf82a195ee4c0f421bdc924f56578eb1c89f` 加工作区 T-193 改动。审查结束时，`git diff HEAD --binary` 与候选自带的 `T-193.diff` 逐字节相同（均为 54,490 字节），副本保存在 [reviewed-candidate.diff](reviewed-candidate.diff)。没有修改候选、原仓库或提交；所有新增产物均在本审查目录。

判据来自 T-193、T-189 第 1 条和 T-196 第 3 条：主控身份绑终端，命令限已打开项目；任务仍按项目和仓库隔离；额外目录由主控逐次选择并记录，恢复与替换不得悄悄改变授权对象；仓库和状态数据的保护不能因额外目录而失效。遵循 **Ubiquitous language**，下文区分“项目设置的额外目录”和“本次派发的额外目录”。此次只读审查不实施修复，不扩大架构或新增 **Deep modules**；真实后台探针作为权限链路的 **Tracer bullet**。

## FINDINGS

### F1 · P1：reviewer 启动时重新解析目录，能把状态根变成可写目录

- 位置：[workbench/src/panes.ts:832](/private/tmp/t193-dev2/workbench/src/panes.ts:832)，后续写入沙箱配置的位置为同文件 838、845、855 行。初次校验在 [workbench/src/gates/core.ts:2148](/private/tmp/t193-dev2/workbench/src/gates/core.ts:2148)；reviewer 校验在同文件 2479、2520 行附近，只核对启动记录与 argv 自洽，没有核对它们是否仍是获批目录。
- 失败场景：主控指定两个存在的目录 `shared`、`shared/nested`。派发成功，attempt 正确记录二者的真实路径。worker 对 `shared` 有写权限，因此可把其子目录 `nested` 替换成指向工作台状态根的符号链接。reviewer 创建时对原记录再次执行 `realpathSync`，得到 `[shared, state]`，并把 `state` 写入 `--add-dir` 和 `sandbox_workspace_write.writable_roots`。生产 `reviewLaunch()` 校验也接受该记录。
- 证据：[probe-zJs1nj/results.json](probe-zJs1nj/results.json) 的 `REPRO_guard_bypassed_on_review_launch`：`approved` 中没有状态根，`actual` 中出现状态根，且 `accepted_by_review_gate=true`。探针在 PTY 创建前截获生产启动记录，没有执行对状态根的破坏性写入；已证明的是受保护目录被授予启动参数权限。
- 建议：每次启动 worker/reviewer 前，验证记录路径仍指向原获批真实路径，并重新执行仓库/状态根保护；路径改指、消失或类型变化应明确拒绝。reviewer 门禁应以 attempt 的获批目录为依据核对启动权限，不能仅用启动记录自身生成期望值。补充“可写父目录内替换已授权子目录”的回归场景。

### F2 · P1：run 保存原始别名，重启重派会换成未经再次选择的目录

- 位置：[workbench/src/gates/core.ts:3045](/private/tmp/t193-dev2/workbench/src/gates/core.ts:3045)，重放在 3060、3247 行。
- 失败场景：`extra_directories=[alias]`，初始 `alias → initial-data`。第一次 attempt 经校验记录 `initial-data`，但 `run.dispatch.extra_directories` 保存的是 `alias`。后台停止后把别名改成 `alias → unrelated-data`，再通过生产 `resumeRuns()` 恢复。旧 attempt 被回收，新 attempt 获得 `unrelated-data`，而非原来的 `initial-data`。新目标虽不在硬保护范围，仍不是原先记录并执行的授权对象。
- 证据：[recovery-GzSfzA/results.json](recovery-GzSfzA/results.json)：第一次 attempt 为 `initial-data`，持久化 dispatch 为 `alias`，恢复后的第二次 attempt 为 `unrelated-data`。使用真实 Git、SQLite、run/停止/恢复/回收逻辑，仅 CLI 生命周期与进程身份为模拟边界。
- 建议：run 在首次派发成功后持久化实际获批、规范化的目录列表，恢复重用该列表，并执行 F1 的启动前验证。同步补齐 `A2ARun.dispatch` 的 `extra_directories` 类型（[workbench/src/contracts/a2aGates.ts:329](/private/tmp/t193-dev2/workbench/src/contracts/a2aGates.ts:329) 当前遗漏该字段）。加入“别名换目标后重启”检查，断言权限不漂移，不能只断言 run 恢复成功。

### F3 · P2：项目设置页面仍承诺三种角色自动获得额外目录

- 位置：[workbench/app/ProjectSettings.tsx:34](/private/tmp/t193-dev2/workbench/app/ProjectSettings.tsx:34)。
- 失败场景：用户打开“编辑项目”，仍看到“新启动的 worker、reviewer 和 monitor 可以写入这些目录。移除后只影响新会话。”新代码已改为 worker/reviewer 使用 attempt 的目录，monitor 不获得额外目录。README、角色卡和 help 已改，产品内说明未改，违反 T-193 的产品页同步要求。
- 建议：说明这里的目录只供主控 `terminal_open` 选择普通终端目录；worker/reviewer 的目录由每次 `dispatch`/`run` 指定并记录，monitor 无此授权。

### F4 · P2：原有回归判据仍要求被本票替换的行为

- [workbench/tests/test_t123_project_identity_e2e.py:414](/private/tmp/t193-dev2/workbench/tests/test_t123_project_identity_e2e.py:414) 仍要求 alpha 获批主控对已打开 beta 的完整任务 id 全部返回 `task_project_mismatch`，包括读取和起草任务卡。当前真实后台探针已验证这些调用按新要求成功。该旧断言与 T-193 正面冲突。
- [workbench/tests/test_t140_extra_dirs_e2e.py:208](/private/tmp/t193-dev2/workbench/tests/test_t140_extra_dirs_e2e.py:208) 派发不传目录，却在 215、227 行要求 worker/reviewer 能写项目设置的目录，238 行还要求 monitor 能写。
- [workbench/tests/test_t141_loosened_limits_e2e.py:264](/private/tmp/t193-dev2/workbench/tests/test_t141_loosened_limits_e2e.py:264) 同样未传目录，324 行仍要求额外目录写入成功。
- 建议：按新判据修改这些测试，而非删除权限断言：保留裸任务名的本项目解析、完整 id 与显式 project 矛盾拒绝、身份撤销等保护；需要测试额外目录写入时显式派发授权，monitor 改测拒写。新增 T-193 测试的六项 green 不能代替这些回归更新。本次未运行以上完整旧 e2e，结论是可定位的判据冲突，不冒充整套测试运行结果。

## EVIDENCE

### 本次独立执行

| 检查 | 结果与产物 | 可复现命令 |
| --- | --- | --- |
| 真实后台、Unix socket、shell PTY、终端凭据与角色批准 | **PASS，25 项**；[native-mu3l27dd/results.json](native-mu3l27dd/results.json)、[daemon-run-02.log](daemon-run-02.log) | `python3 /private/tmp/t193-review1/daemon_probe.py` |
| 真实门禁/Git/SQLite、目录边界、生产启动构造与 reviewer 校验 | **完成，21 个记录项，复现 F1**；[probe-zJs1nj/results.json](probe-zJs1nj/results.json)、[probe-run-03.log](probe-run-03.log) | `node /private/tmp/t193-review1/probe.ts` |
| run 停止、持久化、重新打开数据库与恢复重派 | **复现 F2**；[recovery-GzSfzA/results.json](recovery-GzSfzA/results.json)、[recovery-run-01.log](recovery-run-01.log) | `node /private/tmp/t193-review1/recovery_probe.ts` |
| 现有 T-141 启动契约 | **PASS，2 项**；[t141-launch-contract.json](t141-launch-contract.json)、[日志](t141-launch-contract.log) | `node /private/tmp/t193-dev2/workbench/tests/test_t141_launch_contract.mjs <新的摘要路径> /private/tmp/t193-dev2` |
| 候选 diff 空白检查 | **PASS，退出码 0** | `git -C /private/tmp/t193-dev2 diff --check HEAD` |

前三个探针每次新建审查目录内的隔离夹具并保存 `results.json`；没有覆盖旧结果。上述成功执行的命令退出码均为 0。“复现”表示确认缺陷，不能计为产品验收 PASS。

真实后台探针覆盖：未批准、伪造角色字段、申请待批准、已授予未确认和已释放身份均无主控写权限；alpha 批准的终端可在已打开 beta 建卡、建任务和读取 ready ticket；裸任务名落在 alpha，完整 id 或显式 project 正确落在 beta；矛盾 id/project、未打开项目、缺失 create/inbox_ready project、repo 与项目不匹配、未划定项目的收件箱命令均拒绝。未打开项目回执包含目标、已打开项目与下一步。状态根作为派发目录在原生 worker 启动前被拒。

门禁探针另覆盖：相对路径、普通文件、不存在目录被拒；仓库、仓库子目录、指向仓库的符号链接、状态根/子目录及它们的父目录被拒；普通目录按真实路径去重；未传目录的 attempt 为 `[]`，reviewer 使用 attempt 的目录，monitor 为 `[]` 且只读。即使持有 worker/reviewer 自身令牌，伪装成终端仍被 `authenticateTerminal` 拒绝；经门禁直接请求主控写命令同样被拒。这两项是模块级证据，没有替代原生 worker/reviewer 的端到端身份测试。

首次真实后台探针因夹具没有 `.project-map/tickets`，在 `inbox_ready` 返回 ENOENT 后停止，退出码 1，保留于 [daemon-run-01.log](daemon-run-01.log) 和 [native-h5wtua7_/results.json](native-h5wtua7_/results.json)。给新夹具补入 alpha/beta 各自的 sentinel ticket 后，从头执行通过；候选未修改。早期门禁探针结果也完整保留。

### 既有证据与反例

只读查看 `/Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-193/`：

- `green.json` 记录六项 PASS，证明脚本化模型接口下真实 Claude CLI 的跨项目派发、worker 侧栏归属以及目录启动参数/记录。其 `revision` 为 null，单凭该文件不能独立绑定全部未提交字节；本次另外核对冻结 patch 并补做独立探针。
- `red-base.json` 在基线遇到 `role_project_mismatch`，业务断言失败。`mutant-project-extra-dirs.json` 在“未指定仍继承设置目录”断言失败；`mutant-home-project-only.json` 在跨项目建卡/派发断言失败。它们的汇总状态是 `INCOMPLETE`，但记录的 AssertionError 确实拒绝了对应坏行为，不是依赖缺失或启动失败。
- `dev1-*` 来自更早副本，不作为本候选 PASS 的依据。没有把旧夹具路径重叠的失败删掉或算成成功。
- 当前六项 T-193 检查没有覆盖目录在派发后的改指、run 恢复目录漂移、身份生命周期或 reviewer 权限来源。F1、F2 均可在这些六项继续 green 的情况下发生。

## LIMITATIONS

- 没有重跑完整 T-193 e2e、完整旧 e2e、Electron UI 或供应商模型；现有 green 的模型由本地接口脚本化。没有以此证明模型判断能力、原生沙箱实际拒写/允许写的全部边界、完整审查与集成链路，或生产可发布性。
- F1 已执行生产启动构造、真实启动记录持久化和 reviewer 门禁校验；没有启动该越权 reviewer CLI 或实际改写状态根。F2 已执行真实持久化与恢复逻辑，但进程退出、身份与 CLI 生命周期由隔离 runtime 提供。两处违反的都是可直接观察的授权/记录契约。
- 冲突替换路径静态核对：`core.ts:1734` 从原 attempt 复制目录，并经过同一 claim 校验；正常人工改卡重派则由新的 dispatch 指定目录。未动态制造完整 Git 合并冲突并验证原生替换 worker。复用的规范化路径若在启动前被改指，仍受 F1 影响。
- 家目录判断：没有另加“家目录一律拒绝”的要求。T-196 把做事范围交给主控判断；当前实现已拒绝包含任务仓库或状态根的父目录，因此通常位于家目录内的仓库/状态会使整个家目录被拒。两者都在别处时，独立家目录可获显式授权（探针已测同形场景）；仅因其宽泛而拒绝，缺少本票决定依据。这个判断不豁免 Git 元数据与状态保护。
- 另一个 linked worktree 可以被显式授权，探针记录其与任务仓库具有相同 Git common dir。本票允许主控选择项目外范围，没有把“同仓库另一 checkout”自动扩成一条新硬规则；未证明该授权在各原生 CLI 下的 Git 元数据防护效果。
- 没有运行 TypeScript 类型检查或全量构建；仓库未提供 typecheck script，本地未发现 `tsc`。F2 的建议已指出 run 持久化契约的缺失字段。

修复后应针对 F1、F2 的反例重验，并同步产品说明和相关旧测试。新增检查放在目录启动边界与 run 恢复场景中，以外部指定的原获批目录为期望，不能从实际 argv 或恢复结果反推答案。本次审查到此结束，不代改候选。
