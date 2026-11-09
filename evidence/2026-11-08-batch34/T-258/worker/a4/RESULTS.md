# T-258 第 4 次 attempt 恢复交付

**INCOMPLETE（整票验收）**。本卡 worker 的三个文件恢复、模块红绿和定向回归已完成；新基线上的真实 Codex CLI 父版红态、最终候选绿态及正式独立审查仍由主控接续。旧真实入口结果不能替代这些检查。

本记录写于 2026-11-08（纽约时间；测试记录为 2026-11-09 UTC）。task `a2a+T-258-1`，attempt `7043f6b6-95a1-403d-a487-4587e2c02d62`，session `a5b9c655-b08c-4fda-84e2-9fbbcfca0280`，fence `4`，spec_rev `4`。请求配置为 Codex `gpt-6-astra`、xhigh、普通速度；这不是供应商实际服务等级的证明。

## 恢复内容与来源

当前基线为 `172b2f17566f923b2e0be8f7d21fc0b189b83fa2`。三个指定文件从 `49c7b9a9435f68aec38a862125b8f00220b9b3af` 读取并按原字节恢复，逐文件与已测历史版本 `4c93144df22d486a2d9bf3e948b3e7084723ae6e` 相同，见 [来源索引](source-index.json)。没有 cherry-pick 旧提交、复制旧尾注或改写旧记录。

- `workbench/src/panes.ts`：保留原修复。合法原始 UPS 到达时核对根 rollout/current turn、dispatch、当前 attempt/fence/spec、进程身份；reviewer 再核对当前 review、原 worker、candidate/verification 和独立会话身份。异步观察前后复核，成功记录恢复事件后才清除唯一的 `native_session_unbound`。
- `workbench/tests/test_t258_codex_late_start.ts`：原 117 案模块检查，断言和输入未修改。
- `workbench/tests/test_t258_codex_late_start_e2e.py`：原真实入口运行器，按卡恢复但本 worker 未执行。

行为由 `Panes.drain()` 的启动期限产生，真实 hook 经 `daemon.ts` 的身份入口调用 `Panes.signal()`，恢复仍在 Panes 内完成，后续 Stop/relay/门禁保持既有入口。单独 scan 不清错；不重发输入、不延长期限、不弱化不可信 hook。沿用 **Ubiquitous language** 中的 attempt、原生会话与派发记录；这次没有新增跨层 **Tracer bullet**，也没有新增需要按 **Deep modules** 评估的接口或包装层。

恢复前确认新基线的 `panes.ts` 与旧 attempt 基线 `b7cee33c13c32b84ee07048a697d1b938a5d8116` 相同，未见覆盖其他改动的冲突。恢复后 `workbench/src` 与旧已测版本仍有 `workbench/src/gates/core.ts` 差异（T-259），所以整个产品输入不等价。`questions.ts`、依赖、角色权限、公开接口、schema、冻结验收、REVIEW.md、任务卡和 `.project-map` 均未修改。

历史原件只读索引：

| 来源 | 位置与用途 |
| --- | --- |
| 旧 worker 最终报告 | `git show 49c7b9a9435f68aec38a862125b8f00220b9b3af:evidence/2026-11-08-batch34/T-258/worker/RESULTS-FINAL.md` |
| 旧实现者自查 | 同提交的 `evidence/2026-11-08-batch34/T-258/worker/SELF-CHECK-FINAL.md` |
| 旧主控真实入口汇总 | `/Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-258/controller/e2e-mcp-results-01.json`，2026-11-08T16:40:26Z；父版 `6bdc629da2c930ce201632a49bf5476b6b7ed7dc` exit 1，候选 `4c93144df22d486a2d9bf3e948b3e7084723ae6e` 八项通过、exit 0。只作历史来源，不计入本轮验收。 |
| 旧 SIGSTOP 诊断 | 保留原 INCOMPLETE/NO_GO 判断，不算父版红态。 |
| 本轮规范 | 冻结 T-258 ticket 的 Acceptance、任务卡第 4 版及现有 T-257/原生来源契约；新测试自身不是 oracle。 |

## 本轮验证

| 检查 | 结果 | 证据与业务含义 |
| --- | --- | --- |
| 新基线父版，恢复生产文件前执行 | 42 通过、75 预期失败；exit 1 | [parent-01.json](parent-01.json)：晚启动 UPS 身份未绑定或可信原任务仍保留启动失败，reviewer 同样受阻。是模块缺陷红态，没有导入/依赖错误。 |
| 恢复候选 | 117/117 PASS；exit 0 | [candidate-01.json](candidate-01.json)：worker 时序、旧/重复 Stop、异步替换身份与失败、reviewer 两个合法顺序及 11 个拒绝场景。 |
| 不安全恢复变异 | 85 通过、32 预期失败；exit 1 | [unsafe-01.json](unsafe-01.json)：仅在源码副本把恢复核验调用替换为直接清错；21 项拒绝恢复断言、11 项 reviewer 拒绝断言失败，证明不是无条件恢复也能通过的测试。 |
| T-257 定向回归 | 104/104 PASS；exit 0 | [t257-01.json](t257-01.json)：同 turn 回执续跑、0～2 次 scan/旧 Stop 顺序及 24 个异步 Stop 调度。 |
| 原生来源定向回归 | 13/13 PASS；exit 0 | [native-origin-01.json](native-origin-01.json)：工作目录、子目录、额外目录和外来来源边界。 |

每份摘要保存实际 node argv、外层 cwd、版本、环境变量、每案名称/顺序/成败、失败断言、退出码及清理状态。Node 为 `v26.5.0`；依赖沿 worktree 父目录现有 node_modules 只读解析到 `/Users/luckye/Documents/Code/a2a/workbench/node_modules`，未安装、改写或建立依赖链接。父版/变异副本都以新基线为产品输入；变异只改副本中的恢复调用。

模块不变式来自卡与既有契约：扫描不能授权恢复；只有可信原始输入能恢复；观察前后身份必须一致；其他失败和不可信记录继续拒绝；旧/重复 Stop 不结束当前工作或重复转交；恢复不产生额外 paste/Enter。模块替换终端与进程 I/O，不能证明真实 CLI 时序、请求交付或回收。真实入口留给主控，不扩跑无关全套。

重放均从本 attempt worktree 根目录执行，每次换新的 summary 文件名；运行器拒绝覆盖已存在证据：

```sh
python3 evidence/2026-11-08-batch34/T-258/worker/a4/run-check.py parent --summary evidence/2026-11-08-batch34/T-258/worker/a4/parent-02.json
python3 evidence/2026-11-08-batch34/T-258/worker/a4/run-check.py candidate --summary evidence/2026-11-08-batch34/T-258/worker/a4/candidate-02.json
python3 evidence/2026-11-08-batch34/T-258/worker/a4/run-check.py unsafe --summary evidence/2026-11-08-batch34/T-258/worker/a4/unsafe-02.json
python3 evidence/2026-11-08-batch34/T-258/worker/a4/run-check.py t257 --summary evidence/2026-11-08-batch34/T-258/worker/a4/t257-02.json
python3 evidence/2026-11-08-batch34/T-258/worker/a4/run-check.py native-origin --summary evidence/2026-11-08-batch34/T-258/worker/a4/native-origin-02.json
```

## 自查与交接

[实现者自查](SELF-CHECK.md) 不等于独立审查。[定位器](design-scan.json) 无命中、无冻结验收变更；静态结果不能推出业务验收通过。测试创建的 SQLite/rollout 夹具、父版/变异源码副本及重复事件全文摘要均先记目录、时间、文件数、字节数与结果，再清理；逐案断言保留。没有启动真实 CLI、后台或 hc，没有写正式应用或全局配置。额外可写目录为 `[]`，额外目录改动为无。

[提交前地图检查](map-precommit.json) 为 Problems 0、stale 1：`workbench/README.md` 因 `panes.ts` 改动待同步。已按同一门禁入口排队上报，request_id `d0244794-0daf-4405-ad5e-2215639b5086`；queued=true、delivered=false，尚非主控受理。README 与地图同步由主控处理，worker 不越过卡内边界。

本候选提交后用当前 task/attempt/session/fence/spec_rev 显式 submit 完整 SHA 一次；最终完整 SHA 由提交及该请求绑定。请求文件留在本 attempt 的请求目录，不进入 Git。queued 只表示已排队；不运行 verify、integrate、自动 run 或 push。主控须在冻结候选上补真实入口红绿、独立审查及后续门禁。

**Works**：三个指定文件与两份指定历史来源逐字节一致；本轮 117 项绿态，父版 75 项和不安全恢复 32 项预期失败。

**No regression**：T-257 的 104 项及原生来源 13 项通过；范围外产品文件与冻结验收未改。未运行全套，集成检查由主控接续。

**Risk / undo**：整票仍 INCOMPLETE，缺新基线真实入口、独立审查和 README/地图同步。回退时由主控经正常流程撤回本票 `panes.ts` 差异，保留证据；回退会恢复晚启动失败标记不清除的旧行为。
