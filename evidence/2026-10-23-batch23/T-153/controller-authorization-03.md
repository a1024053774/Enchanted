# T-153 沙箱外真实运行授权 03（执行主控，2026-10-23）

- 依据：同授权 01、02（用户裁定 C；AGENTS.md 真实 Codex 验收规则）。
- 前情：授权 02 的运行用了 5 个真实回合（变异 worker 2；绿态 worker 2、reviewer 1）：红态有效；绿态被真实 reviewer 以“夹具完成条件不足”判需修复。worker 已按夹具卡合同补强两份 oracle（de726ab67）。
- 本次批准：`RUN-OUTSIDE-03.sh` 一次运行，`repeat-feedback` 变异与绿态两场；真实 Codex `gpt-6.1-sol` high、普通速度；每场 worker ≤2、reviewer ≤2 回合，合计 ≤8 回合，失败不自动重跑。
- 隔离：同授权 01（/tmp 隔离 CODEX_HOME，只复制 auth.json，只信任夹具根目录，只加 `git add`、`git commit` 两条 allow，hook 只在本次运行中安装，结束删除隔离 home，不写用户 ~/.codex）。
- 不批准：重跑、增加回合、修改审查员提示词或审查要求、对用户项目或数据的任何操作。
