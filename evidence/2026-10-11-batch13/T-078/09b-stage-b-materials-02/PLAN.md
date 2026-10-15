# 09B 阶段 B 逐角色入口计划

阶段 A-05 的 root、attempt、session、fence、thread、workspace 和四类进程仍由 `readiness.json` 绑定。阶段 B 入口每次先重新读取 readiness，再对 shell、receiver、两个 fake API、daemon 做 PID/lstart/command/root 双读；任何复用或 readiness 与 approval 不同都在 spawn 前拒绝。角色只能按 ideation → executor 顺序启动；前一角色未完成时，第二角色请求拒绝。

B1 只准备 ideation。A-05 绑定的 [P1 材料](09b-stage-b-ideation-p1-01/) 已写入同一 root 的 `roles/ideation`（HOME/config/tmp/shell/requests/hooks/user-data、role.md），input 的 fake API 是实际登记的 `http://127.0.0.1:57534`（PID 70730）；[approval 草稿](stage-b-ideation-approval.json) 除 `approved_by`、`approval_ref` 外已填好，binding 取 readiness 的 `target_binding` 原值。主控签字后才可执行。主题按 `ArrowUp → Auto (match terminal)`、`ArrowDown → Dark mode`、`Enter`；Security notes 必须与 `p1-materials-09/security-notice-text.txt` 逐字相同后才允许 Enter；信任屏只允许 `ArrowDown → Yes, I trust this folder`、`Enter`，不使用 Digit1 或默认 Enter。工具许可仅一次性 `Enter`，并为 I1/I2/E1… 每个阶段另签 approval，阶段末停止。

B1 精确命令（先用 `--dry-run` 预检；获得本次 B1 approval 后去掉 `--dry-run`，runner 会只调用同一 `run_t078_p1.py --phase launch`，启动 ideation 到第一屏并停下）：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/run-09b-stage-b.py \
  --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-executable-materials-05 \
  --stage-a /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-stage-a-05 \
  --role ideation --phase B1 \
  --approval /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/stage-b-ideation-approval-02.json \
  --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-stage-b1-ideation \
  --dry-run
```

真实 B1 命令只删除末行 `--dry-run`；该命令要求 approval 的 `p1_materials` 已绑定 A-05 root、`p1_phase=launch`、逐屏材料齐全。它执行后保存 `run_t078_p1.py` 的 process/PTY 原件并停止，不自动按键或继续。

待批材料：stage-a-05 `readiness.json` 与 `result.json` 原件、同一 root 的 PID/lstart/command 读回、ideation 的 approval（含 screen-key approval 文件、security notice 原字节、trust 两键、一次工具 Yes）、`stage-b-approval-template.json` 填写件及独立 actions/停止清单。spy 输出 `09b-stage-b-spies-03/results.json` 还包含三项去检查变异红态；它只证明入口门禁，不能替真实 Claude 启动或屏幕读回。
