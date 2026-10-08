# T-039 真实闭环记录（2026-10-08）

**BLOCKED，待主控决定；ticket 保持 open，待主控关闭。** 固定候选 `fa3fc3352805d00e41c454fa6f810807528de3a9` 的真实门禁 run 在 `waiting_submit` 暂停。未修产品、未重新调用模型、未 push；没有 accepted 结论。

## 三项验收

| 条件 | 结论与证据 |
| --- | --- |
| 真实 run accepted、引用等于 worker 提交、完整记录 | BLOCKED。[create-01](create-01.json) 成功；[run-01](run-01.json) exit 1、`identity_conflict`、`paused`；没有 submit / candidate / verification / integration intent。记录已保存，但完整闭环未完成 |
| 隔离 home 删除、用户数据不变 | INCOMPLETE（整体条件）。home 删除与临时隔离边界有证据：[配置](isolated-config.json)、[overlay 核对](home-isolation-01.json)、[实际 argv](processes-live-01.json)、[清理](cleanup.json)；源 home 与 overlay 均不存在，仅停止 PID 39162 和它的原生子进程。没有操作 Herdr 或用户 Synara 实例；auth.json 仅复制到隔离 home。但没有用户数据的独立前后快照/审计，不能把这一整项写为通过 |
| 权限或问题对话停下，不批准、不计通过 | PASS（本次运行遵守此边界）。[原生读回](native-live-01.json) 与[中断后读回](native-after-interrupt-01.json) 无 pending interactions；run 非通过。没有回答对话或输入第二条任务。人工输入事件为空，observer healthy；中断为显式清理事件 |

## 真实问题与最小选项

`run-01.json` 的拒绝发生于 `2026-10-08T06:07:16.233Z`。provider 与 shell 的 thread、cwd、provider 均一致，但两个来源的 turn 状态不同：

| 来源 | 当时的观察 |
| --- | --- |
| shell 投影 | session.status=`ready`，activeTurnId=null，latestTurn=null；updatedAt=`06:07:10.522Z` |
| provider 当前状态 | status=`running`，activeTurnId=`01a11a1f-8399-74c2-a3fd-a583a7ddc520`；updatedAt=`06:07:16.212Z` |
| 后续原生读回 | latestTurn 与 session 的 activeTurnId 均出现同一 turn；startedAt=`06:07:16.211Z` |

实际拒绝点为 fork `apps/server/src/a2a/orchestration.ts:32`：将 provider activeTurnId 与 shell 的 null turn 直接判为冲突。服务在 `apps/server/src/a2a/service.ts` 先读 shell 再读 providers，没有一个共同快照。上述时间线支持“投影滞后触发身份误拒绝”的判断；尚未实现或验证修复。

发现后停止业务推进，原生 `thread.turn.interrupt` 只取消本次 turn：[请求与返回](cleanup-interrupt-01.json)。中断后 session.status=`interrupted`，activeTurnId=null，archivedAt=null。绑定原 attempt 的[门禁 reclaim](reclaim-01.json) 又以 `run_external_unknown` 拒绝；拒绝点为 `orchestration.ts:23` 对 interrupted 的统一分类。未直接 stop/archive 修改门禁业务事实；保留“原生中断完成、门禁回收未完成”。随后只向核对过的隔离 server PID 发 SIGTERM，运行进程组已为空。

主控最小决定：是否授权修复原生观察接缝，区分尚未投影的 turn 与真实身份更换，并处理已中断 thread 的受控回收；修复取得反事实和独立验证后，另用全新隔离根重跑 T-039。也可把修复另分 ticket，再恢复本 ticket。未授权前不修、不重试、不绕过 run 手工验收或集成。

## 身份、配置与边界

| 字段 | 值 |
| --- | --- |
| task / run | `t039-pagination` / `974277a4-97f7-427c-8308-aef073d29b4a` |
| attempt / session_id | `0f1e8e39-76ca-492b-a415-56f91186a076` / `282d257b-944a-48cb-8b85-2db6416c9cf8` |
| fence / spec_rev | 1 / 1；规范 `synara-m1-2026-10-07` 验证接缝 2、T-039 与当前 brief |
| Synara thread | `c407de98-2455-49f4-9340-4deb49ab833a` |
| Codex 原生会话 / turn | `01a11a1f-5c40-70b3-be48-7a92f4c99e79` / `01a11a1f-8399-74c2-a3fd-a583a7ddc520` |
| fixture / integration / worker HEAD | `99cfd8d4b9347f7b570a3f2f1dd69d9d2dbefb47`，均为原始 faulty starter；无 worker 交付提交 |
| Codex | CLI 0.161.0，固定 standalone 绝对路径；`-c 'service_tier="fast"' -c check_for_update_on_startup=false` |
| 原生请求 | gpt-6.1-sol、xhigh、fastMode=true；thread settings 实际报告 serviceTier=`priority`，不证明供应商计费或收益 |
| runtimeMode | full-access；按 brief 沿用 T-035，避免其 approval-required 首轮进入权限等待；原生报告 approvalPolicy=never、dangerFullAccess |
| worker / 主控 | s2-t039 / Claude Code `wF:pM`（任务书身份，未连接 Herdr 核实） |

本 worker 自身的受管 attempt/fence 未由任务书提供，保持未知；上表为真实夹具子会话身份。实时观察由执行者完成，不称为独立 monitor。结束后的独立审查判 FAIL，范围与来源见 [冻结清单](frozen-manifest.json)、[审查](acceptance-review.md) 和 [review-provenance](review-provenance.json)。审查时原稿保存在 `review-frozen-docs/`；此后仅取消第二项勾选并更正文档相应结论，产品候选和原始运行证据未变，未再进行第二次独立审查。

服务直接由 Bun 执行固定 checkout 的 `apps/server/src/index.ts`，没有使用可能过期的 server bundle。[源码绑定](candidate-binding.json) 和 `candidate-sources.tar.gz` 保存版本；结束时 tracked diff 仍为空。Bun/Node 运行均经外置盘检查入口；无 rebuild，不把 T-037 既有测试或旧 T-035 闭环复用为通过。

隔离 CODEX_HOME 只复制 auth.json；新配置只信任已核对的夹具 repo，只设 git add / git commit 两条 allow 规则，无 hook。overlay 的六个链接全部留在本次 `/private/tmp/a2a-t039-e5qgcehx`。删除了源 home、整个 overlay 与 bootstrap token；凭据不入 Git 或归档。fixture、worktree 和门禁状态保留原目录并归档为 `retained-fixture.tar.gz`，不登记 gitlink。含私有认证状态的 Synara userdata 不归档、不提交。

## 命令和证据

所有 CLI 调用的精确 argv、cwd、时间、原始 stdout/stderr、退出码见 `preparation.jsonl`、`commands.jsonl` 与各请求 JSON；server 的独立进程组见 `server-start.json`。原始 app-server 记录见 `provider-*.log` 与 `rollout-*.jsonl`。人工介入记录见 `events-01.json`；清理控制请求独立保存。

首次执行从 a2a 根目录使用以下命令。准备脚本拒绝覆盖旧 runtime 与证据；重跑必须另建新的证据目录和隔离根，当前已删除凭据，不能原地继续。

```sh
python3 -B evidence/2026-10-07-synara-batch2/T-039/prepare.py
python3 -B evidence/2026-10-07-synara-batch2/T-039/start.py
python3 -B evidence/2026-10-07-synara-batch2/T-039/gate.py run-01 '{"command":"run","task":"t039-pagination","runtimeMode":"full-access","wait_seconds":600}'
```

create 的完整输入与输出在 `create-01.json`；必须先 create 再 run。回收实际命令：

```sh
python3 -B evidence/2026-10-07-synara-batch2/T-039/gate.py reclaim-01 '{"command":"reclaim","task":"t039-pagination","attempt":"0f1e8e39-76ca-492b-a415-56f91186a076"}'
python3 -B evidence/2026-10-07-synara-batch2/T-039/collect-cleanup.py
```

独立 oracle 对原始 starter：12 项中 10 项失败，exit 1，见 `oracle-known-bad.json`；冻结 oracle 与合同按原字节保存，未向模型提供答案。`diagnostic-checks.json` 只核对失败诊断、引用不变与清理的一致性，其 PASS 不代表闭环通过。已保留启动未 ready 的 health 连接拒绝与中断后进程环境捕获失败，见 `session-incidents.jsonl`；它们不是产品业务红态。

本轮没有产品变更，不运行全仓 fmt/lint/typecheck/test；未完成 worker submit、候选 oracle、CAS 或门禁业务回收。Windows、UI、发布、M1 切换、性能与成本收益均不在本轮通过范围。项目 status、文本与归档检查见 `project-map-status-final.txt`、`delivery-checks.json`；a2a 交付提交号以最后 `T-039 DONE BLOCKED` 回执为准。
