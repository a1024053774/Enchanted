# T-076/T-077 衔接：新 worker 的原生记录归属

状态：INCOMPLETE；静态推断，未做真实CLI复验，不阻塞本卡当前的同attempt修复/审查/评分路径。

观察：`workbench/src/panes.ts` 的worker从后台`LaunchConfig.codex_home`启动，`scan`遍历该home中的原生记录，遇两个不同的根CLI session_meta会拒绝为ambiguous_native_session。reviewer已各用独立home；worker的新attempt复用同一home时，旧根记录是否被排除仍未证明。

T-077计划中有“已归档pane不占活跃名额”和“旧worker已结束则开新attempt”。本卡首条slice曾把createThread限制放宽为“没有活跃worker”；该放宽并非支持reviewer所必需（reviewer走自己的createReview），属于T-077的生命周期衔接。因此本轮已恢复原S1的single_worker_slice条件，不把名额释放顺手并入本卡。

建议：执行主控在T-077合流时联验第二个worker的独立home或原生日志归属，不能仅证明pane名额已释放。需要同时检查“多个历史根CLI记录不会被当成本次新worker的身份”，以及旧记录原样保留。不要删除历史日志或放宽原生身份检查来绕过。

来源：`workbench/src/panes.ts`的createThread、createReview与scan；`.project-map/tickets/T-077-worktree-lifecycle-conflicts.md`第4项。这里只上报衔接未知，不修改T-077分支、ticket、spec或全局配置。
