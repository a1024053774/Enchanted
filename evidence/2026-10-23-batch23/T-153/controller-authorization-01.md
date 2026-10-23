# T-153 沙箱外真实运行授权（执行主控，2026-10-23）

- 依据：用户裁定 C（`.project-map/inbox/20261023T185657Z-ideation-answer-001.md`）要求迁移 `run_worker_delivery.py` 并在现行代码上取得红态与绿态；AGENTS.md 的真实 Codex 验收规则。
- 本次批准：`RUN-OUTSIDE-01.sh` 一次运行，含 `repeat-feedback` 变异与绿态两场；真实 Codex `gpt-6.1-sol` high、普通速度；每场 worker ≤2 回合、reviewer ≤2 回合，合计 ≤8 回合，失败不自动重跑。
- 隔离：/tmp 下隔离 CODEX_HOME，只复制 auth.json，只信任本次夹具根目录，只加入 `git add`、`git commit` 两条 allow；启动参数 hook 只在本次运行中安装；结束后删除整个隔离 home；不写用户 ~/.codex。
- 不批准：重跑、增加回合、对用户项目或数据的任何操作。
