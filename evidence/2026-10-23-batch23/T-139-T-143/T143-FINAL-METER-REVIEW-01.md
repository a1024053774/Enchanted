# T-143 最终候选计时与依赖移除审查

状态：**INCOMPLETE**。
冻结候选：1c6bfbb4b9552eef0a3d72831c2d71fa402bf587，比较 117045d00e74bc317c95e4f2bd14a7426e5b9bc3。
来源：新鲜只读会话 `/root/t143_final_meter_review`；审查结束时候选及受审文件未变。
限定范围未发现已复现的行为违约，不替最终真实性能/联合验收宣称通过。

- package.json、package-lock.json 与起点 ebbae7bd09cee3a8220b948029f9033dc2906c90 完全一致；当前生产 renderer 和 e2e 均无 WebGL 路径。
- 独立读取 COMPARISON.json 并由原始样本重算：读屏关闭 99.45→89.30 ms；保留连接 83.90→75.00 ms；整体 108.40→75.00 ms。RESULTS 数字准确，明确未证明滚动改善。
- 实际计时表达式要求输入确认、onRender 覆盖 BENCH_04999、可见且恢复完成，再等两次 rAF；随后核对完整 5000 行。
- 新鲜运行 test_t143_output_meter.py，七项边界和实际 JS 的 node --check 均 PASS（meter-review-current-01.json）。
- /tmp 副本中删去 rendered 或 visible 条件，分别被业务断言拒绝，NO_GO（meter-review-ignore-render-01.json、meter-review-ignore-visibility-01.json）。
- RUN-OUTSIDE-05 使用同一工具/夹具定义/5000 行命令测候选和基线；把两份缺新指标的旧真实报告送入实际前置检查，均退出 1（meter-review-candidate-preflight-01.json、meter-review-baseline-preflight-01.json）。

原检查目录：/private/tmp/t143-review-gt9os0e3/，保留两份坏表达式副本与日志。
未运行整个 Electron 批次，未重审其他产品能力。新版真实 output_to_visible 基线/候选均未取得；模拟边界只证明完成合同，不证明性能。

冻结候选的地图检查为 0 problems，但 README 因 package.json 变化 stale；worker 在审查结束后补明当前采用 xterm 默认渲染器；提交前 status 仍按旧提交判 stale（session-status-06.txt），提交后再核对。

README 提交后复核为 0 problems、0 stale docs，见 session-status-07.txt。
