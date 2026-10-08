# T-039 决定02/03交付记录（2026-10-08）

**真实原自动run已completed；完整交付结论以新的独立审查和最终DONE回执为准，ticket保持open、待主控关闭。** 新候选 `8aba12a4911ce6bc682dbb75d343b3ae08529202`，父版 `fc9e36c75af3bbcf701551abbb911883b94217c2`。没有手工补回收、重新投递任务或再启动模型turn。原repair-02 BLOCKED、旧审查FAIL和本轮注册阻断记录均保留。

## 三项验收证据

| 条件 | 已取得证据 |
| --- | --- |
| 完整真实run、显式交付、oracle、CAS、自动回收 | [run.json](real-01/run.json) exit0、ok=true、outcome=completed、reclaimed=true；同一attempt。`status-final`为accepted，`native-archived`为stopped/archived；[独立读回](real-01/independent-readbacks.json)确认worker HEAD=C=M=集成引用，oracle12/12且原字节不变 |
| 隔离home删除、用户前后核对 | [清理](real-01/cleanup.json)确认源home及overlay不存在、原进程组无存活成员、token删除；[用户比较](user-data-comparison.json)的config/rules大小与mtime、Synara顶层元数据、herdr status全部相同。仅证明主控指定核对范围，不外推为全机逐文件审计 |
| 无人值守不批准权限/问题对话 | 无pending interactions、human_intervention为空、observer healthy；无第二条输入、权限回答或人工补回收，见native快照与events-final |

## 根因修复与单一实例

调查见 [序号机制对照](projection-settlement-comparison.md)。原先先读shell后读provider，将两个时刻的状态拼在一起；domain high-water本身也不能证明尚未转成domain事件的native前缀已处理。

本轮在现有原生接缝采provider快照后，复用 `ProviderRuntimeIngestionService.drain` 的runtime前缀ACK，再捕获domain H、核对snapshot必需projector最小序号P>=H，最后读shell分类。stop命令回执只表示意图；复用现有ProviderCommandReactor的ACK drain，再核对投影。没有新增重试循环或改GateRuntime合同；原submit期限及回收窗口来自原run phase记录，超时保留既有错误码。error、两个非空turn不同、活跃provider与interrupted矛盾仍拒绝。

上游仅改 `serverLayers.ts` 的一处A2AGateServiceLive注册，提供该组合根已有的两个layer常量；授权为 [冻结决定03](frozen-controller-decision-03.md)，改动清单见 [upstream-file-manifest](upstream-file-manifest.json)。其他改动在a2a service与测试，未改门禁核心、T-038或其他上游文件。

[共享检查](sharing-proof.json)使用真实serverLayers组合，仅给两个producer工厂分配可区分的构造标记：ingestion构造一次、command构造一次，原orchestration reactor各启动一次，gate drain也落在同一标记实例。故意将注册改成Layer.fresh后，出现ingestion-2并被断言拒绝，见 `sharing-mutant.log/patch/provenance`；原注册已按原字节恢复。它证明服务图共享，不将受控producer当作真实provider成功；真实闭环另有下面的独立证据。

## 红绿、版本和检查

| 检查 | 实际结果 |
| --- | --- |
| settlement-red | 父版2项业务失败：完成/关闭先于投影、stop意图先于stopped读回；旧6项通过 |
| settlement-green-02 | 10/10，通过序号拒绝、deadline及身份反例 |
| 最终父版反事实 | 3失败/7通过，`counterfactual.json`确认工作区原字节恢复 |
| sharing-check / sharing-mutant | 正例通过；重复实例反例业务断言失败，不以崩溃判红 |
| frozen-related | 三文件12/12，包括真实production composition启动；没有模型调用 |
| frozen-typecheck / lint-after-wiring / fmt-owned-after-wiring | PASS，typecheck8/8；自己的4个文件格式通过。旧缺注册typecheck失败保留 |
| orchestration-18 + delivery-recovery-17 | 35/35，新候选绑定在各command.json；原T-037/T-036套件、边界替身、oracle未改 |
| 全仓test | NO_GO：desktop两文件3失败使Turbo中止，5/7 workspace完成；server全仓未完成。不能写成全仓通过 |
| 范围外失败复核 | desktop AppSnap与browser pipe两文件在外置盘短tmp槽t39下67/67通过；原长路径EINVAL、目录清理与5秒超时失败保留。不外推全仓通过，也未改这些产品文件 |

原35项夹具保留目录并完整归档于 `retained-35-fixtures.tar.gz`；受控服务夹具归档保留，未登记Gitlink。原格式检查 `.grok` 失败仍在旧记录内；本轮按主控决定检查自己的文件，不清理他人的未跟踪文件。Windows运行、UI外观、迁移、完整M1、切换和发布不在此通过范围。

## 新根真实原自动run

隔离根 `/private/tmp/a2a-t039-r03-c6ls9k43`。服务经外置盘入口、独立进程组直接执行冻结checkout的 `apps/server/src/index.ts`，没有使用可能过期的bundle。[源码绑定](candidate-binding-03.json)逐字节核对1677个归档源码文件，tracked diff为空；不计算指纹。

| 身份 | 值 |
| --- | --- |
| task / run | `t039-pagination-r03` / `5866aa6c-db6e-4f6d-b137-d76d16fc03d8` |
| attempt / session_id | `3fb08360-c88e-40f6-b94c-34383c6449d1` / `487b2778-dd98-446b-9e98-7946088b72ae` |
| fence / spec_rev | 1 / 1；synara-m1验证接缝2、T-039及决定02/03 |
| Synara thread | `6f3474a1-f9b2-4c13-9e77-86b8a10ba8db` |
| Codex原生会话 / turn | `01a11b0d-d117-72b0-94ce-510981fdf694` / `01a11b0d-e0da-7dd0-a5cd-3ca38bb42df6` |
| G / worker C=M=集成引用 | `75c1d3e477044810fc02cf67c1aa7c8839eee32a` / `8ea88d43ae99c7d805347aa06edff6ad43105594` |
| run开始 / 结束 | 10:27:29.180Z / 10:29:26.934Z；submit期限600秒 |

仅一次真实Codex turn，显式a2a_submit的原始通知、工具activity与返回保存在 `native-submit-raw/activities`、完整provider与rollout日志；submitted→verified→integrated→reclaimed→run_finished保存在 [delivery-events](real-01/delivery-events.json)。独立oracle在新的detached worktree运行，12项含unseen sentinel；原starter红态保留。没有以模型自报、idle或done替代交付。

模型gpt-6.1-sol、xhigh、fastMode=true；runtimeMode full-access沿原brief/T-035。固定Codex CLI 0.161.0，启动wrapper含 `-c 'service_tier="fast"' -c check_for_update_on_startup=false`。原生设置报告priority、never、dangerFullAccess，只证明配置，不证明供应商实际tier、计费或收益。

backend与gate CLI的精确argv、时间、版本、stdout/stderr及退出码在启动记录、commands.jsonl和每轮JSON。模型进程在ps捕获前已退出，所以 `live-identity-isolation.json`没有模型PID或环境观测；[codex-launch-binding](real-01/codex-launch-binding.json)只记录冻结wrapper/spawn的精确请求输入及真实原生version/settings，不谎称OS进程表argv捕获。这是证据方式的明确限制。

## 隔离与审查交接

源CODEX_HOME只复制auth.json；新配置只信任核对的夹具根，只放行git add/commit，无hook。临时执行链接只指向固定Codex二进制，数据链接留在本次隔离根；未读写用户配置正文。自动门禁回收完成后，只停本次server PID 17197及其原生子进程，再删除整个source home、overlay和私有token。原fixture/worktree保留并归档；含私有认证的Synara userdata不归档、不提交。

执行和实时观察由s2-t039完成，不称为独立monitor。主控身份沿任务书Claude Code wF:pM；本worker自身的受管attempt/fence未提供，保持未知，表中是夹具子会话身份。新审查范围见 [冻结清单](frozen-manifest-final.json)，来源及最终结论见 [review-provenance-final](review-provenance-final.json)、[acceptance-review-final](acceptance-review-final.md)。首次审查意外读取排除段，已停止为INCOMPLETE并保留 `acceptance-review-aborted.md`；不会作为通过证据。

ticket保持open，待主控关闭。旧失败、阻断、权限界限及当时的地图结构异常保留，不以本轮通过倒改历史。最新status与提交号绑定最终DONE回执；未push。
