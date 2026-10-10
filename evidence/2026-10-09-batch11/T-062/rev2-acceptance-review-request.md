# T-062 rev2：一次独立只读审查请求

fork 候选：`4ac5ba00e7125279b08c241037d1404450455ff6`；已知坏父修订：`d9fc40a5f8b14d22ec7568c7ccef542572e79102`。a2a 候选是本请求所在的证据提交，由调用者提供完整提交号。审查只针对这两个指定 snapshot，本请求不传递实现者的理由或通过结论。

允许读取：T-062 ticket 的 What to build / Acceptance（停止于 `## 说明`，不得读 Resolution）；候选 diff；`rev2-red02-*.png`、`rev2-green02-*.png` 及其机械观察 JSON；重放脚本、命令 JSON 和原始运行输出。禁止读取任何 `RESULTS*.md`、ticket Resolution、inbox 条目正文、旧的 `acceptance-review-*` 或实现者聊天。

`evidence/2026-10-09-batch11/controller-poll.log`、`dispatch.jsonl`、`panes.txt` 是执行主控持续追加的日志，不属于候选，其变化不使候选失效。其他 ticket、其他 worker 的未跟踪文件或候选外改动也不属于本次指定的 T-062 snapshot；用 Git 指定提交读取即可。

验收范围来自 ticket：来源是否为产品；全新 profile、提示出现期间的真实 dev UI 是否仍压住任务窗口/面板标题；亮暗主题文字是否可读；截图是否涵盖 1600×1050 与 1280×900；上游改动是否只在 Sidebar.tsx 及直接样式；导览其他步骤是否改变。外观由用户判断，不做审美通过判决，也不评真实模型、门禁交付或正式实例。

重放命令见 `rev2-red02-command.json`、`rev2-green02-command.json` 和 `rev2-*-tests*-command.json`。脚本 `rev2-panel-title02.mjs` 与现有 `start-isolated.py` / `stop-isolated.py`；新运行必须改为新 label/profile，不覆盖现场。完整回放需另外启动隔离实例；只读审查可直接核对命令、PNG 和机械观察，不操作共享 checkout 或正式工作台。不得据缺省的正式 provider 访问补足证据。

按 behavioral-acceptance-review 技能输出 STATUS、TARGET、EVIDENCE、FINDINGS、COUNTEREXAMPLE、LIMITATIONS。只审查一次，返回结果，不修复，不另找 reviewer，不重开审查。
