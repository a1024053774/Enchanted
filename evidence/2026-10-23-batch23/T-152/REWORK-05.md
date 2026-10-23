# T-152 第 5 轮：读回修正与全量复跑入口

状态：INCOMPLETE，05 尚待主控运行。主控 #13 授权修正 04 读回并直接准备 05；本轮不改产品、测试文件或业务断言。

04 原始结果保留在 `outside-04-UXB2hit2/`，版本 `971fafbf594046ba38d09d32ad0f9bbc63b922e9`。主控实跑正常 tracer_review_copy 已 passed，7 条业务断言均通过，cleanup_failures=0，模型回合为 0；但旧读回器在第 5 步报 KeyError('id')，原 SUMMARY 为 INCOMPLETE，不能改写为 PASS。

根因与修改：数据库 dispatch_records 的行字段为 seq/id/launch/data，data 对象只有 text/registered_at/source/parent_launch（现场 `/private/tmp/t152-ysuh1k2x/run/tracer_review_copy/database-readback.json`，源码 `workbench/src/store.ts:128–142`）。旧读回器仅解码 data 后错误读取 id。本次从行顶层取 id、从 data 取 text；其余绑定、唯一性、事件顺序、物理副本删除条件不变。为了 04 与 05 使用同一套检查，把读回代码提取为只用于本票的 `read_tracer_flow.py`，04 调它；没有增加字段 fallback。读回输入版本须与 --revision 一致，输出用独占创建，保留原结果。

已离线重读同一个 04 现场，无新后台、无 CLI/模型回合：

```sh
python3 -B evidence/2026-10-23-batch23/T-152/read_tracer_flow.py --run-summary evidence/2026-10-23-batch23/T-152/outside-04-UXB2hit2/tracer.json --summary evidence/2026-10-23-batch23/T-152/offline-04-reread-01.json --revision 971fafbf594046ba38d09d32ad0f9bbc63b922e9
```

结果 PASS，9 项全部为 true：正常 tracer、排队文件绑定、首轮匹配 Stop、relay_result 的 submitted candidate、唯一 source=gate 回执及对应 turn_submitted、ACK 唯一匹配 pane_idle、独立 review_result、copy_removed→review_reclaimed 顺序、副本物理不存在。新文件记录读取时间与原运行版本；它是原现场的事后读回，不是新候选复跑，也不是当时的独立监控。

旧读回器在同一现场失败、新读回器成功构成读回缺陷的红绿对照；这不替代 T-152 保留业务检查的 mutant 红态。孤立报告器反例和语法检查见 local-checks-05.json，05 运行结果尚不存在。

下一步：`zsh evidence/2026-10-23-batch23/T-152/RUN-OUTSIDE-05.sh`。它在全新 outside-05 目录先跑一个新 fixture 正例与完整读回；任一步失败就写 INCOMPLETE、列出未运行部分并停止扩展。前置通过后，依次运行 8 个变异、全部 7 个正常 T-082 场景、T-090 三例和 T-141 reviewer 契约。13 个明确列名的摘要均 PASS、版本相同且 HEAD 未变，聚合才 PASS。变异的指定 failure_id/清理判据继续由原 run_suite 执行，不修改或放宽。

新完整正例、8 个变异及其后完整绿态、T-090/T-141 仍须在 05 取得；在此之前 T-152 总状态继续 INCOMPLETE。
