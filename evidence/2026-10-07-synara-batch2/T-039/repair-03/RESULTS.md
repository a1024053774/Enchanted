# T-039 决定02阶段记录（2026-10-08）

**BLOCKED，待主控授权修改一个服务注册点。** ticket保持open，待主控关闭。原repair-02与两次独立审查FAIL原样保留；本轮没有新模型调用，不宣称完成。

机制调查见 [对照](projection-settlement-comparison.md)。domain high-water和日志重放不能独立证明native事件已进入投影。现有 `ProviderRuntimeIngestionService.drain` 消费捕获的runtime前缀并核对ACK；snapshot序号是必需projector的最小已处理序号。stop回执是意图，须由已有ProviderCommandReactor处理并ACK，再核对序号和实际状态。

授权内工作：仅改 `apps/server/src/a2a/service.ts` 与测试 `service.test.ts`；未改纯分类规则、门禁合同、上游文件或T-038。实现先采provider快照，再复用ingestion前缀、捕获domain H、检查snapshot P>=H，最后读shell。stop/archive等待已有provider intent ACK，再核对同一投影前缀。没有新观察重试循环；预算取自原run phase的submit期限与60秒回收窗口，非run原生读使用已有native命令45秒限度，超时用既有错误码。实现仍在工作区，不能当作可运行交付。

| 检查 | 结果 |
| --- | --- |
| 父版缺陷红态 `settlement-red` | 2项业务失败：closed先于running投影导致原run回收失败；stop意图先于投影导致stop_unconfirmed；旧6项通过 |
| 新服务测试 `settlement-green-02` | 10/10通过；含明确序号拒绝、原submit deadline、真实turn更换等反例 |
| 最终父版反事实 | 3失败/7通过，见 `settlement-final-parent-red.log`、`counterfactual.json`；固定工作区service按原字节恢复 |
| 全图typecheck | FAIL，见 `typecheck.log`：serverLayers.test.ts:26的Effect仍要求ProviderCommandReactor和ProviderRuntimeIngestionService，不是never环境 |
| 35项、新根真实run、前后核对、新独立审查 | NOT_RUN / INCOMPLETE；须先完成真实服务图注册，不把受控替身提供依赖当作生产接入成功 |

根因：`serverLayers.ts:270`当前只给A2AGateServiceLive提供基础runtimeServicesLayer。两个新消费的服务已在同一函数里有既有layer，但当前注册点没有提供它们。最小修复见 [proposed-server-layer-wiring.patch](proposed-server-layer-wiring.patch)：复用 `runtimeIngestionLayer` 与 `providerCommandReactorLayer`，没有新增生产worker、第二套路径或依赖。补丁的 `git apply --check`通过，见 [检查](proposed-wiring-check.json)，**未应用**。

停止依据为主控决定02首段：“授权范围仍限 `apps/server/src/a2a/orchestration.ts`、`service.ts` 及其测试；改门禁合同或上游文件先问主控。”真实组合根位于另一个上游文件。没有通过类型强转、可选服务、noop或在门禁内复制整套producer图来绕过这个缺口。

当前fork HEAD仍为 `fc9e36c75af3bbcf701551abbb911883b94217c2`，新增工作区改动保存在 [in-progress-approved-files.patch](in-progress-approved-files.patch)与 `working-service-before-counterfactual.txt`，未提交fork、未push。每次命令的argv、cwd、退出码及输出保存在相应JSON/日志。测试夹具位于外置盘缓存tmp，未创建真实CODEX_HOME，不读写用户凭据或用户Synara数据。

主控授权注册点后：应用该已核对补丁，完成typecheck/lint/fmt、35项重跑，冻结完整候选，再用新隔离根取得原自动run的completed收据和用户前后核对，最后做一次新的fresh-context独立审查。本轮不为这一待完成候选背书。

收尾status记录为exit1：主控同期关闭的T-038仍有一项未勾选，见 `project-map-status.txt`；stale living docs为0。该ticket不归本worker，未修改。受控夹具完整归档已读回验证，共2626个成员；原目录保留，归档未登记为gitlink。没有把这个地图结构问题写成健康检查通过。
