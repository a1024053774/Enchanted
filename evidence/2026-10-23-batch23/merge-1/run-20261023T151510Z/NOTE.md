# 合并后回归 04（main fd4d9ac13，含 T-144 与 T-146-4）

命令：`zsh evidence/2026-10-23-batch23/merge-1/RUN-MERGE-REGRESSION-04.sh fd4d9ac13`（在分离 worktree `a2a-merge-check` 中运行）。

- 25 项中 24 项 exit=0，含 T-133/T-107（回归 03 的失败已由 T-146-4 修好）、T-140、T-144 两项、T-146 全部 6 项、T-127、构建。
- `t145-green` exit=1：`motion_bytes_match_coordinates_exactly`。期望的三条 SGR 移动上报（12;4、14;4、17;4）都在实际字节里，中间夹着另一串连续坐标（54;40 → 53;39 → … → 42;36），形态是一次真实指针滑动。根因假设：回归并行开着多个真实 Electron 窗口，屏幕上的真实鼠标划过 T-145 窗口，产生了额外的移动上报，不是候选代码回归。
- 验证：同一提交上单独重跑 `python3 workbench/tests/test_t145_mouse_reports_e2e.py --summary .../t145-green-rerun-alone.json`，PASS。
- 遗留：该测试会受真实指针干扰（测试稳健性缺陷，不改断言），记入执行主控自建的测试缺陷 ticket。
