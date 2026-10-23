T-142 的必跑回归 T-121 在候选与起点 c113e71203bd37e151241b6ce44bd4bf773e356f 均失败。

位置：workbench/tests/test_t121_role_request_e2e.py 的 sidebar_drops_closed_controller；候选证据 regression-t121-01.json，起点证据 baseline-t121-01.json，均在本目录。终端关闭后身份已被拒，但侧栏仍留该主控。问题涉及 sidebar.ts，与已派的 T-146-4 修改区域重叠，T-142 不改它。

建议：执行主控按 T-146-4 的最终候选复跑该项，确认是否同根因；T-142 的回归当前不能报告 PASS。范围内的 terminal_open 实现与其他验证继续。
