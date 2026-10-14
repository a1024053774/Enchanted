# rebase-final-01：run 清理例的夹具就绪判断错误

结论：**夹具错误**。不是 candidate 或 attempt 换绑，也没有证据表明产品把错误的审查绑定交给 run。原失败保持 `INCOMPLETE`，本结论不补称该 run 已通过。

原错误：`outside-rebase-final-01/s3-all/13-test_integrated_run_cleanup/unittest.txt`。实际 status 与时序来自 `s3-all/readbacks/t-u4fpxxg8.json` 和原现场 `/private/tmp/s3-4pjxf_ih/t-u4fpxxg8/quality-control/driver.jsonl`：

- 所有 driver status 的 attempt 都是 `ea016d4b-ead4-4b77-b4f9-88ba3f45dc04`，C 都是 `65c1ad734a955aad452ea1a73365777d7e753ad7`。
- 最后一次 status 是 `state=reviewing`、verification 已 passed，但 `review=null`。此时没有审查记录可供比较，不能将 null 解释为一个不同的绑定。
- 事件 73 `verification_result` 在 02:53:07.235Z；82/85 的 verifier 清理意图与完成在 07.515Z/07.598Z；86 的 `review_requested` 在 07.600Z；91 的 `review_started` 在 08.353Z。
- 后两条事件的 review id 都是 `461020fb-6328-4912-a522-89926456c2b0`，候选、attempt 与 verification `47b1de16-1659-4c3f-9500-86965f7df9b0` 均与这次交付相同。没有“取错候选”的记录。

生产 verify 会在完成机械检查后保存 reviewing 状态，随后做已完成 verifier 的清理，最后才保存 review_requested。新增清理使原本就存在的可观察时间窗更容易命中。产品 run 不把 reviewing 本身视作有效审查结论；它仍等待显式 reviewer 交付和执行主控集成。

最小修正只在 `legacy_quality_driver.finalize_run`：沿用原 12 秒就绪期限，在 review 尚为 null 时继续原来的状态读取；一旦有记录，原样核对 C、attempt、review id、requested/running 状态和 runtime facts。没有重发命令、重新建审查、延长超时或接管新 attempt。业务断言未改，产品代码未改。

夹具客户端的局部测试（不是产品通过证据）记录了这一个真实时间窗以及必须继续拒收的反例：

```sh
python3 -B workbench/tests/test_legacy_driver_readiness.py --case transient --expect-red --output evidence/2026-10-11-batch13/T-077/driver-readiness-red-01
python3 -B workbench/tests/test_legacy_driver_readiness.py --output evidence/2026-10-11-batch13/T-077/driver-readiness-green-01
```

修前为 1 failure / 0 errors，red_confirmed=true；修后 5 项、0 failures/errors。覆盖缺记录至原期限、错误 attempt/C/审查绑定、审查 id 改变、未知状态及缺 runtime facts。`rebase-final-02` 仍须通过真实入口重跑原 run 清理例与完整回归，不能用这个局部测试替代。
