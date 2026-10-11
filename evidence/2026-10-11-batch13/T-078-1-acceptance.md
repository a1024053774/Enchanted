# T-078-1 执行主控验收记录（合流待定）

时间：2026-10-11 17:20 左右。

- 交付：exec/t078 `b3fb998c`（产品与测试，已变基到 main 532c51f4）+ `38a7eeed`（证据、RESULTS、独立审查）。尾注来自 worker 会话（gpt-6-astra、xhigh、launch-08dfb896…）。
- 最终验收 `outside-final-01`（执行主控沙箱外运行）：checkpoint PASS；coop 8、recovery 9、run 18、cas 1 全过；输入、worker 收件箱 14 项、窗格状态、主控启动骨架、运行时入口均过；4 个权限规则变异体与 cas/fence/lock 3 个业务变异体按预期失败；无 >5MB；真实模型回合 0，Claude 未启动。
- 独立只读审查 `independent-review-01.md`：PASS（仅 T-078-1 非 Claude 范围）；逐字比对归档源码与冻结候选一致；未发现行为违约或结构性阻断；局限如实列出（IME 为合成事件、两分钟无 ack 等为 L1/静态证据）。
- 结论：T-078-1 子范围验收 **PASS**；T-078 整票 **INCOMPLETE**——真实 Claude 启动/认证/hook 接线、主控互相唤醒、同任务三窗格仍待 needs-decision `20261011T101958Z`。
- 合流：**未执行**。main checkout 上有 T-076-2 worker 未提交的改动，与 exec/t078 同改 workbench/README.md、src/contracts/a2aGates.ts、src/daemon.ts、src/gates/cli.ts、src/gates/core.ts 等；此时快进 main 会动到他人工作区。待 T-076-2 提交后，再把 exec/t078 变基到新 main、重跑最终验收、快进合入。评分在合入时一并记录。
- worker `s13-t078`（wF:p37）保留，供合流前变基与真实 Claude 部分使用。
