# 主控执行交接：冻结及沙箱外回归

2026-10-14，授权来自主控 #143 当前派工：重跑沙箱内能执行的部分，沙箱外写阶段脚本；新材料绑定 ff3708d0 之后的提交。当前沙箱内证据已取得，完整说明见 REBASED-REPORT-09A3.md；整票与实际 Claude 场景仍 INCOMPLETE。

执行顺序：

1. 先执行前一 report `20261014T142134Z-worker:t078-09a3r-report-001` 的 cleanup 阶段，停止本轮八个隔离 Node 后台；本轮原件与根保留。
2. 以本 worker 的真实启动身份及提交钩子执行代码／证据提交：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-rebased-code-09a3.sh
```

此提交纳入五个停点、首次失败、当前反例与本地检查，更新 receiver 和域夹具的 HOME/cwd，加入新 `09a3r` 材料代的生成与调用参数。只改测试／夹具／生成工具，不改 gates/core.ts／taskCards.ts；九项尾注仍由钩子生成。脚本在提交后写入 rebased-source-freeze.json/txt，供下一阶段固定版本核对；这两份作为后续材料提交内容，不自称工作树全干净。

3. 在沙箱外执行已经备好的单一阶段脚本：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/rebased-stage-09a3.py --mode regression
```

要求 cleanup PASS、冻结提交不变、workbench 无未提交差异、外置盘已挂载。串行运行实际 Electron／daemon／PTY（仅本次隔离窗口与原受控 native receiver），runtime 12、input-failures 11、worker-inbox 14，现有业务 8/9/18、CAS 1，再四项 worker 权限反例。各自有输出与原件，失败就停并保留；无自动重试、不改断言、不启动真实 Codex／Claude／供应商 API／模型，不切换日常门禁。窗口由此夹具自己创建并关闭，不操作用户应用。

请把 cleanup、代码提交号及 regression 结果直接回到 worker；worker 接着生成两个全新 09a3r 隔离实例及来源快照、静态核对，最后交新 launch 审批与材料提交脚本。当前交接没有 launch 授权，也没有启动它。
