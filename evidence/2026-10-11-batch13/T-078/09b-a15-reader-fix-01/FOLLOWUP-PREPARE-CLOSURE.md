# 非阻塞：后续标准场景 prepare 的 reader 源闭包

#331 约束要求本次新只读 harness 除三条 reader 外，其余原包文件保持逐字节相同，所以本次不改原 `prepare-09b-executable.py`。新 A-15 reader 冻结会显式纳入 p1_output、恢复器、源校验入口及测试，当前续行闭包完整。

但原标准 prepare 在源码清单里仍没有新 reader 模块。未来若为 09C 或新场景重新执行标准 prepare，必须先把这次新增依赖纳入统一源清单并重新冻结，否则只记录改过的调用者、没有记录被 import 的分页 helper，会留下证据闭包缺口。

位置：`evidence/2026-10-11-batch13/T-078/prepare-09b-executable.py` 的 files/source archive 清单；直接依赖见 `workbench/tests/run_t078_p1.py`、`t078_09b_phase_driver.py`、`t078_09b_i1_permission.py` 的 p1_output import。建议主控在下一次标准场景 prepare 前分配该材料生成器修订；不阻塞使用本次显式闭包的 A-15 只读 harness，不改 protocol/预算。本 worker 不顺手改掉受 #331 保护的原包文件。
