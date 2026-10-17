# 主控 #341：合并 main 6d85482ff 的冲突处理

主控已建 backup/t078-pre-merge-main-4=acf8b8a3f，并在沙箱外执行固定目标的 no-ff/no-commit 合并。worker 仅解决以下三个测试文件；未重写 main 的产品修复或验收方法，未运行回归/现场。

- daemon_acceptance_host.ts：保留 mkdirSync 和 createOperatorCredential 的 T-078 引导顺序（serve 前建立 0700 state、创建 operator）；ready 由 T-090 的 publishReady 发布。旧直接 writeFileSync(final) 不保留，去掉无调用的 writeFileSync import。
- quality_chain_host.ts：同样保留 mkdirSync/root、createOperatorCredential、原受控 PTY 与动态产品加载；ready 只走 T-090 的完整写入后硬链接发布，不保留非原子出口。
- run_s3_rebased_regression.py：合并为一个 action=append 的 --case，保留 T-090 的去重/原方法成员检查和排序，保留 T-078 的 --mutant-core、original_results、方法身份检查、readbacks/失败与错误原文。记录完整 suite_membership 与既有 complete_original_suite_size；selected_case 只记录单个选择，selected_cases 记录全部选择，供既有单例对照及 T-090 多例调用分别读取。没有改变原验收断言、次数或期限。

自动合并的 core.ts 保留 T-090 在 review_requested 保存 worker_boundary，以及按 review_id 找原边界核对 HEAD/分支/status 的结束条件；T-078 收件箱 pending/delivered、I2 与 startup 队列路径不改。没有恢复 HEAD==候选的错误约束。实际运行结果仍 INCOMPLETE，待主控沙箱外完整复验。

此前主控实跑的 rev2-tools-outside-01 六段 PASS 是 acf8b8a3f 的测试工具证据，不上调为本次合并后业务回归 PASS；原输出保持不变，随后续材料提交保存。
