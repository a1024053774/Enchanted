STATUS: FAIL
TARGET: /Users/luckye/Documents/Code/synara frozen candidate c7aaaa433a064aff032d3d5d511cf496507ecd83 (parent d479dab2a1608c3219b7a4e1c07e9056bfb63a9e)

EVIDENCE:
- 冻结核对：git rev-parse HEAD 返回候选完整提交，工作树无受控文件改动。
- 契约要求非受管记录失败不阻断业务；只有受管 attempt 的输入记录失败才进入 fail-closed：T-056-user-input-coverage.md:26、controller spec :134。
- 真实服务、WS、SQLite 探针 scope-18.command.json:2-8 在候选上退出码为 1；非受管中断先成功且 observer 为 healthy，随后受管线程的元数据命令使 observer 变为 failed。独立 oracle 明确预期 healthy、观测为 failed：scope-18/scope-oracle.json:1-12。
- 其他覆盖证据通过：frozen-13.command.json:4-9、实际 Codex 0.162.0 的 native-frozen-15.command.json:4-9、迁移 migration-frozen-14.command.json:4-12；最终套件命令均记录退出码 0。

FINDINGS:
- [P1] /Users/luckye/Documents/Code/synara/apps/server/src/a2a/orchestration.ts:144,172-185 — flushDeferredUserInputs() 在每个域事件上重试此前失败的非受管输入；失败被包装为当前事件的 event.aggregateId，再由 userInputTarget(event.aggregateId).attempt 判定为受管失败。因此受管线程的无输入元数据事件会错误地把非受管记录故障升级为全局 failed。按待补录输入自身的 target 归因，或仅在相关输入事件上重试，并避免无关元数据事件触发 managed fail-closed。

COUNTEREXAMPLE:
- scope-18.py：SQLite trigger 仅拒绝 target.attempt IS NULL 的输入；非受管 interrupt 成功，随后受管 thread.meta.update 不产生用户输入，却使 observer 从 healthy 变为 failed。该候选被探针拒绝。

LIMITATIONS:
- 覆盖矩阵除原生 Codex 问答外均禁用 provider；结构化回答和审批 request id 是隔离夹具哨兵。原生问题/回答使用实际 Codex CLI 0.162.0。
- 本审查未把部署、用户批准、任务关闭或 submit receipt 计入 T-056 验收。

原始审查由一次 fresh-context、只读的 t056_acceptance_review 返回；FAIL 保留，不替后续修复候选背书。
