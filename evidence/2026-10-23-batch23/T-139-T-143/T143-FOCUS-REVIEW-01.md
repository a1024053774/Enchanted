# T-143 保留窗格焦点修复独立只读审查

状态：**INCOMPLETE**。
冻结候选：cd28996cba5ac24a25bc2aaeb67ebe93db74e404。
来源：新鲜只读会话 `/root/t143_focus_review`。审查前后 HEAD/候选未变，仓库文件未修改，地图 0 problems、0 stale docs。

限定范围未发现候选的可复现违规；证据不足以关闭真实 Electron 焦点与切换验收。

- 独立新跑实际焦点回调：父版本 6c44695ff47a1d2e1d035bf9f4b2f92f9889e5f6 为 NO_GO，过早消耗聚焦请求；候选四项 PASS。证据 focus-review-parent-01.json、focus-review-candidate-01.json。
- 独立请求值 1、37、126 均通过旧可见性拒绝、失败聚焦不消耗请求、揭示后聚焦、不抢回焦点和隐藏窗格拒绝。证据 focus-review-boundaries-01.json。
- 经 Python AST 提取切换 JS，node --check 退出 0。原文件仍要求目标可见、可输入、恢复完成、textarea 实际获得焦点，期限仍为 12000ms。
- 将缺少切换指标的报告交给 RUN-OUTSIDE-04 实际前置检查，退出 1、INCOMPLETE，在批量运行前停止。新目录为 outside-04-XXXXXXXX。证据 focus-review-summary-01.json，原检查目录 /private/tmp/t143-focus-review-hjvvhjku/。

复跑示例（摘要路径需为新路径）：

```sh
node workbench/tests/test_t143_retained_focus.mjs /private/tmp/t143-focus-review-parent-20261023-01.json 6c44695ff47a1d2e1d035bf9f4b2f92f9889e5f6
node workbench/tests/test_t143_retained_focus.mjs /private/tmp/t143-focus-review-candidate-20261023-01.json cd28996cba5ac24a25bc2aaeb67ebe93db74e404
```

局限：独立查看旧失败截图，目标 worker 已显示，不能认定为“目标未显示”。旧日志与报告缺少逐项条件值，
无法确认历史 timeout 完全由焦点竞态导致，也不能由此确认测量标记不符。隔离回调的 hook/DOM 边界不证明 React
实际调度、Electron 聚焦或耗时。未启动 Electron 批次，新候选真实非空切换指标仍未取得。
