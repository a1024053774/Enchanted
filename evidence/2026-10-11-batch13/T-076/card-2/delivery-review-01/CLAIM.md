# T-076-2 独立交付审查范围

目标：审查delivery-review-01冻结候选相对baseline a7f4cc30的卡2变更。它实现质量串、三次打回上限、fresh只读reviewer和评分接口；卡1已经完成的缺口不复用旧结论为新变更背书。审查只读，不继承实现会话，不修改文件/分支，不submit/integrate，不再找其他审查者。

独立契约：candidate/requirements/T-076-quality-chain-scoring.md的Acceptance，以及native-cli-orchestration第3/8/9/12节；B通道与已批准acceptance白名单由requirements/controller-decision-01至05约束。用户当前要求gpt-6.1-sol/xhigh、每会话显式service_tier=default。T-077命名/清理/R8、T-078、存储结构修改是本卡非目标。

候选源文件和baseline都在candidate/；manifest.json和CANDIDATE.diff用于定位变化，新文件不能因diff未显示就忽略。不要读实现者的PLAN、RESULTS、聊天或主会话日志。不要把新测试当oracle；从上述独立契约重建验收，检查预期泄漏、已知坏实现/反例，以及异常吞噬、重试/兼容/并行路径、根因所有权与浅包装成本。

原始外部证据在`/Users/luckye/Documents/Code/a2a/evidence/2026-10-11-batch13/T-076/card-2/`以下指定目录（均已停止；只读）：

- outside-red-02：起点契约红态和既有边界对照；
- outside-focused-tracer-01、outside-wide-green-01：受控PTY/原生输入，实际CLI/后台/Git/SQLite，正例与单点产品变异体；
- outside-reviewer-red-01、outside-reviewer-green-01：创建、恢复、回收异常与正常路径；
- outside-legacy-green-06：批准迁移后的8/9/18和T-075/T-076-1回归、F10/W07来源变异体；
- outside-launch-policy-default-01：显式default参数和priority/只读变异体；
- outside-p-review-02：实际模型、只读sentinel拒绝、完整Stop/B结论，1主回合；
- outside-real-delivery-02：实际worker4回合+reviewer1回合，C1→完成条件首拒→自动回写→C2→可合并→缺分拒绝→主控后填评分→集成/回收。直接核对gate-events、events-after-stop、bindings、integration、score-payload、两个native-sessions和Git消息。sentinel不属于这条正例。
- archive-real-log-01：超大日志字节归档PASS；commands.jsonl.gz.pointer.json指向外置盘48,122,290字节日志。原run.json的INCOMPLETE/archive_required原样保留，不能误当业务失败已擦除。
- real-delivery-consistency-01.json：tasks/attempts/verifications一致；membership/session_presets无法重建，空表不代表覆盖。按票报告，不以本卡改变存储。

证据层次必须分清：受控回归不证明真实模型/权限；P-review及真实正例提供实际边界。模型速度只以显式请求和可见原生日志报告，不推测供应商实际tier。冻结候选当前通过的范围是隔离受管交付，不能宣称正式工作台已切换或生产可用。

只运行有界只读检查，不启动socket/后台/其他模型、网络、进程信号或写缓存。完整检查无法在只读模式运行时，指出缺口，不伪造绿态。

最终消息用behavioral-acceptance-review规定的STATUS/TARGET/EVIDENCE/FINDINGS/COUNTEREXAMPLE/LIMITATIONS/RULE格式，必要时加RELEASE。PASS必须有独立行为证据；FAIL须可达或复现违规；未知写INCOMPLETE。结构风险纳入同一次审查，不另开审查回合。
