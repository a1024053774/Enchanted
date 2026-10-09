# T-053 执行主控决定 01 独立验收审查

STATUS: PASS
TARGET: 8e260461f32e49c3b1bce50bedeceb4fad38aa8a
EVIDENCE:
- Oracle 来自 controller-decision-01.md，不依赖实现者报告或预期助手。
- 独立 sentinel 经真实 CLI 验证：closed、superseded、out-of-scope 均不输出；无就绪字段的 open 输出“未标就绪”；仅有 ready_rev 的 open 输出缺少 ready、ready_by；依赖 closed、superseded 的就绪记录正常输出 READY。候选全部断言通过，夹具文件未改变。
- 两个新增测试通过独立子进程调用 CLI，预期值未引用生产常量或助手。已有红态分别因业务断言失败，已有绿态两例通过。
- 已有真实仓库 raw：修正前有 52 行诊断、exit 1；修正后有 5 项未标就绪、原 3 项 READY、stderr 为空、exit 0。前后状态保存齐全。
- 原独立目录：/var/folders/7v/58svbpnj5k91zdnm5zggb38h0000gn/T/a2a-t053-decision01-review-p5_405wy/。完整 probe、inputs、expected、candidate/parent raw、judgment 与 end-state 保存在 decision-01-independent-raw.tar.gz。
- 结束时 HEAD 未变，审查的两个文件无候选外修改；project-map status 为 Problems 0、Stale living docs 0。
FINDINGS:
- 无。
COUNTEREXAMPLE:
- 父修订 ae15df747f3838b2d9c1b55f815d55ad7f5144ef 被同一 sentinel 拒绝：诊断三个已结束记录，并把无字段 open 判为不合规；失败来自业务断言。
LIMITATIONS:
- 结论仅覆盖 decision-01 就绪分类修正，不代表完整 T-053 验收。
- 真实仓库结果为已有 raw 的只读核对；未新增生产运行。独立通过依据是从冻结 Git 修订提取的真实 CLI。
RULE:
- 不适用；无重复缺陷发现。

保留的独立探针可重放（使用新目录）：

```sh
python3 -B evidence/2026-10-09-batch8/T-053/decision-01-review-probe.py --repo /Users/luckye/Documents/Code/a2a --candidate 8e260461f32e49c3b1bce50bedeceb4fad38aa8a --parent ae15df747f3838b2d9c1b55f815d55ad7f5144ef --artifacts /tmp/T-053-decision01-independent-replay-01
```
