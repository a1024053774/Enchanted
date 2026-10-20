T-110/a1 启动 status 在稀疏 worktree 中报 8 项缺失链接/文件，stale 0；缺失为 findings 与 .grilling 的非检出文件。票据要求 status 0 问题，当前环境不能证明；不修改地图或扩大稀疏范围。建议执行主控在完整 checkout 的最终候选复跑 status，并保留 worker 的结果。
另 npm ci --ignore-scripts 成功，npm 报 3 个 high 依赖漏洞；本票不升级锁定依赖，建议主控另行确认依赖维护范围。
