# T-077-1 白名单迁移与完整回归交接（2026-10-11）

状态：**INCOMPLETE**。已读回 check-02：green-02 两项 R8 为 PASS；red-03 五项均为业务红态、0 errors，失败数依次为 3、1、2、4、1。原始结果未覆盖，真实回合仍 0/4。

本轮未修改产品代码。按红态完成 W05/W07/W09/W11 断言迁移，并在 W13 指定的三个调用点提供并核对并行理由；保留恢复文件、通用 `unchanged()`、旧 run 归属以及外来身份拒绝等保护。全量引用比较仅增加点名的 A(N)/V(N,K)，不忽略整个引用命名空间。逐 hunk 见 [assertion-hunks.md](assertion-hunks.md)。

执行命令：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/outside-sandbox.sh check-03
```

顺序与预计产物：

| 顺序 | 输出目录 | 检查范围 |
| --- | --- | --- |
| 1 | `outside-green-03` | 与 red-03 相同的 W05/W07/W09/W11 四个 focused cases；R8 上限已在 green-02 通过，本次不重复 |
| 2 | `outside-regression-01-coop` | 原交付 8 项，按白名单采用 S3 新契约 |
| 3 | `outside-regression-01-recovery` | 原恢复 9 项，断言文件未改 |
| 4 | `outside-regression-01-run` | 原编排 18 项；13 项受控线程边界、5 项默认 Panes 路径，不能称真实 Codex |
| 5 | `outside-regression-01-cas` | 实际 Git 写入前发生竞争的 R8 补充 |
| 6 | `outside-regression-01-cards` | T-075 任务卡正反例及追加表检查，共 15 项 |

任一阶段失败即停止；套内也 fail-fast。报告同时列 expected_tests/tests_run，未运行的测试不算通过。请保留完整控制台 stdout/stderr。真实协议/产品失败或无法判定时交回，不自动修改业务预期。

新入口 `workbench/tests/run_s3_regression.py` 直接调用既有后台适配类和原测试方法，检查方法对象未被覆盖及完整用例数 8/9/18/1/15。它不修改或绕过旧 T-075 runner：旧 runner 的“对旧版本断言零 diff”门槛仍保留为当时记录；新入口用决定 02 的范围审计替代该不再适用的门槛。

每套保留原始命令 gzip、测试输出、独立 SQLite 读回 gzip、源码快照、Git diff、所有 fixture 的 tar 和 readback 身份。运行前后逐字节比较被测源码，变化即 INCOMPLETE。大于 5 MB 的文件会逐字节核对后归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-077/<输出目录>/`，旁边留 `.archive.json` 指针，最终 run.json 列出全部外置归档；不压掉失败、不覆盖旧文件。

已完成离线检查：范围审计 PASS，受保护断言改动反例被拒；AST/模块导入/用例计数通过；恢复断言文件与起点一致。新回归尚未执行，不能把这些离线检查写成 8/9/18 通过。

仍待完成：冲突流程红/绿、真实 Codex 冲突整理和重交、必要反事实、一次独立审查、T-076-1/T-076-2 合流及最新 main 变基后重跑、带尾注提交与最终 RESULTS/Resolution。本卡当前没有最终提交，未 push。
