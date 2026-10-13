# Recovery cleanup重复审查驱动修复

状态：**INCOMPLETE（完整Recovery待跑）**。04的coop为8/8，两个新候选场景通过，F10/W07反事实有效；Recovery第一项通过，第二项在cleanup报error，后续未运行。原04目录保留。

## 原因与证据

第二项task为`check-a453958532e4405a90e5cf6a98a2cf03`，attempt=`b4d6e91f-9c4e-42e4-a535-693b4772b20c`，C=`d0d193b9f8958042dc4b10de3fb519c8eb1d16b9`，review=`2d72000a-0334-42b4-9086-6eb368143c3f`。

事件70保存一次review_result，72完成一次review_reclaimed，113集成、114记录评分；最终task=accepted、review=passed。失败不是审查未完成，而是`RecoveryCLI.cleanup_fixture()`再次调用同一个verify handle的`complete()`。adapter读回的是原CLI保存的历史响应（task=reviewing），据此第二次调用driver；driver随后看到当前accepted而非reviewing/verified，报错。

修复放在重复动作的入口`DaemonLifecycle.complete()`：每个成功verify handle仅发起一次审查后续动作，保存task、attempt/session/fence、spec/card、C、verification、review的明确绑定。再次读取相同handle只返回原响应并记fixture重读事件，不再查询或驱动reviewer。绑定变化或前次动作仍未完成时拒绝，不重试。首次动作也显式传原attempt/C给driver，不能接管当前的新attempt。

这是fixture的动作去重，不是生产review通过标志：未写生产库，不伪造review/delivery/launch，不改变CLI响应字节，不把accepted当作一个新review。`QualityDriver`原严格检查保留，Recovery文件、屏障、CAS次数与9项断言逐字不变。

## Recovery 9项setup/cleanup静态核对

| method | setup／中途handle | cleanup应做什么 |
| --- | --- | --- |
| `test_live_verify_excludes_verify_and_integrate` | 手工claim；一个成功verify，两个忙锁拒绝 | 成功handle的review已完成，重读无动作；失败handle不驱动review |
| `test_live_integrate_excludes_verify_and_integrate` | 受控dispatch；setup的verify已审；后续integrate完成及忙锁拒绝 | setup旧verify只重读，不能因当前accepted再审；其余handle只读 |
| `test_interrupted_verify_gets_new_id_worktree_and_full_oracle` | 原verify被杀、客户端失败；新verify绑定新V并完成review | 原失败handle不驱动；新成功handle重读不再驱动，原/新屏障不变 |
| `test_before_CAS_recovers_same_intent_once` | setup verify完成；integrate在CAS前中断，显式恢复同intent | verify重读无动作；中断integrate仍保留失败响应；不额外写Git/评分 |
| `test_after_CAS_recovers_bookkeeping_without_Git_write` | setup verify完成；Git已变后中断，再补账 | verify重读无动作；不把cleanup变成CAS或新review |
| `test_after_CAS_external_X_requires_reconciliation` | setup verify完成；CAS后外部ref改为X，恢复拒绝 | 当前integrating不影响历史handle重读；不驱动review或接受未知ref |
| `test_after_CAS_deleted_ref_requires_reconciliation` | 同上但ref被删除 | 同上，保留needs_reconciliation与原CAS计数 |
| `test_interrupted_verify_revoke_reclaim_rejects_old_identity` | 旧claim verify中断后revoke；replacement受控dispatch、新verify | 旧失败handle不驱动；新成功handle缓存绑定replacement，cleanup不接管旧身份 |
| `test_interrupted_verify_spec_change_rejects_old_candidate` | 旧verify中断后revise；replacement的新spec/卡绑定verify | 旧失败handle不驱动；新成功handle按新绑定重读，不复活旧候选 |

同步CLI verify的后续动作也显式绑定其响应内的attempt/C；每次process是一次真实命令，不从旧stdout重复驱动。异步complete的缓存范围限同一handle，不复用到新请求或另一个verification。

## 离线复放与限制

`offline-01/run.json`为PASS：从原源码AST提取精确complete方法，用保存的CLI响应及review-result/accepted快照复放。旧方法第二次调用确实抛相同driver错误；新方法只读driver一次，cleanup重读原响应；另验证变更C/attempt/review会拒绝、incomplete动作不重试、operation_busy响应不驱动review。

替换的只有进程结果读取和status传输；没有后台/socket、Git写入、ps、信号或模型。它证明fixture修复与输入绑定，不代替Recovery端到端绿态。原文件为`*.before`，diff在`offline-01/fixture-fix.diff`。

首次只读汇总误将同label的operation_busy回复当作带task的成功回复，出现KeyError；正式复放按exit_code和结构化state选择记录，未修改旧产物或产品。该读取错误不计为产品红态。

再生成命令（换新输出目录）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/recovery-cleanup-repair-01/replay.py --output evidence/2026-10-11-batch13/T-076/card-2/recovery-cleanup-repair-01/offline-02
```

下一次完整阶段使用legacy-green-05。真实仍0/8，原03/04证据不覆盖。
