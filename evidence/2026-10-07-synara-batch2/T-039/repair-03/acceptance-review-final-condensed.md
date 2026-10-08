STATUS: PASS
TARGET: frozen Synara candidate `8aba12a4911ce6bc682dbb75d343b3ae08529202` (parent `fc9e36c75af3bbcf701551abbb911883b94217c2`)

EVIDENCE:
- 冻结检查：`git rev-parse HEAD`匹配候选；diff仅为service.ts、service.test.ts、layer-sharing.test.ts、serverLayers.ts。
- 合同来自brief-T-039、controller decisions02/03与M1 spec验证接缝2；源码屏障在service.ts:41-46，deadline/error在48-85，stop/archive落定在161-183。
- 原自动run退出0、task accepted、outcome completed；持久事件submitted→integrated→reclaimed→run_finished(completed)，没有手工reclaim。
- native-submit-raw记录真实a2a_submit，task/attempt/session/fence/spec_rev/worker commit一致；native-archived读回latestTurn completed、session stopped、archivedAt非空。
- CAS命令git update-ref C G；事件与独立git rev-parse读回等于worker提交，同一attempt/fence/spec_rev贯穿。
- 独立oracle拒绝starter，对候选12项通过；contract/oracle未变，原始命令与state.sqlite3保留。
- 两个隔离home删除、进程组无残留；用户before/after元数据与只读status相同。
- 生产组合ingestion/command各一实例，gate drain用同实例；重复ingestion-2 mutant被拒绝。
- 有界复核3个相关文件12/12；35项通过，父版反事实3失败/7通过。

FINDINGS:
- 无可达违规。

COUNTEREXAMPLE:
- 父版未通过投影落定测试；重复注册mutant产生ingestion-2而失败；starter被独立oracle判红。

LIMITATIONS:
- 进程在ps捕获前退出；仅有冻结launcher/spawn精确输入和native version/settings，不能声称真实OS argv观察或供应商实际tier。
- 用户核对是元数据与只读status，不是全内容审计；不外推M1发布。
- 全仓test仍因desktop3项失败exit1；此PASS仅覆盖候选相关服务与真实T-039闭环。
