# T-076-2 执行主控决定 03：F05–F12 迁移清单

时间：2026-10-11；审阅对象：`F05-migration-list.md`（HEAD 07c596fe）、`migration-list-checks.json`。

## 结论：F05–F11 批准；F12 批准 W07 与双场景保留方式

| 编号 | 决定 | 条件 |
| --- | --- | --- |
| F05 | 批准 | 只迁移表中标明的准备步骤；`ManagedDeliveryCLI.claim()` 不改；`test_baseline_change_after_verification_rejects_integration` 的成功前置迁到受控 dispatch，纳入决定 02 范围；不改 oracle 与候选参考实现 |
| F06 | 批准 | `acceptance/test_recovery_e2e.py` 不编辑；只按表中 method＋owner 匹配迁移；stale_after_interruption 的旧 attempt 仍真实 claim，仅 replacement 改受控 dispatch；屏障、CAS 计数、9 项断言不变 |
| F07 | 批准 | 合计 18 项不变；old-guard-owner 仍真实 claim 后 revoke，仅 current-guard-owner 改受控 dispatch；其余 7 项不运行集成 driver |
| F08 | 批准 | 只改列出的 6 个调用点；`create()` 仍真实 claim；尾注恶意模式、外来 middle commit、无尾注人工介入预期不变 |
| F09 | 批准 | 受控运行时的 CLI/model/effort 在报告中标为 fixture 事实；不向生产库预填 launch/delivery/passed；接口容纳不了就交回，不加 test mode |
| F10 | 批准 | 编号 MANUAL-CLAIM-SOURCE；变异体只删 integrate 的 `score_provenance_required` 前置，须因 Git 已变而命中预写断言，不能只凭非零退出 |
| F11 | 批准 | runner 的"acceptance diff 必须为空"改为逐 hunk 核对已批准范围，Recovery 仍须逐字不变；新 `legacy-green` 为一个阶段，第一处异常即停；不重跑 wide-green 与 reviewer-green |
| F12 / W07 | 批准 | `test_submit_requires_clean_head_and_cannot_replace_frozen_candidate` 直到 verified、candidate=C 的全部原 claim 检查保留；`:509–511` 的末尾改为"带合法 review 与评分仍因来源被拒、ref 不动"。原"集成 C、不集成 later_bad"的证据移到新 `managed_frozen_candidate_integrates_original`，以受控 dispatch 重放 dirty/head/冻结 C/C2 拒绝/verify 冻结 C/独立 review/集成 C 全过程。8 项旧套件计数不变，新场景单列；`assertion-hunks.md` 写明 W07 的旧断言、新断言与规格依据（决定 02、PLAN §5.2），不得称"未改原断言" |

依据：决定 02——没有受管启动来源的手工 claim 不能产出合规评分（T-070、PLAN §5.2），所以原 W07 末尾的成功集成在新契约下不再成立；冻结候选的保护内容在受管路径上完整保留。

## 下一步

按清单实施，更新 `assertion-hunks.md`，写 `legacy-green` 单阶段沙箱外脚本，回复 READY 后停下。F10 与 W07 的新断言须先在起点或已知坏变异体上取得业务红态。真实回合仍 0/8；P-review 另行逐次批准。
