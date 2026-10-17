# 任务卡 T-089-1

你是 T-089 的 worker（执行主控派发）。先读 AGENTS.md、.project-map/roles/worker.md、.project-map/tickets/T-089-evidence-archive-tool.md、.project-map/tickets/T-088-evidence-archive-policy.md、workbench/tests/run_s3_regression.py。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-089-1 |
| 来源 | T-089 ready_rev 1（ready_by ideation；assign 20261017T092953Z-ideation-assign-001） |
| 目标 | 一个归档命令：把 evidence/<批次>/<ticket>/ 下归档类别（整个 run/fixtures 目录、*.tar.gz、*.bin、sqlite 与 -wal、监视器日志）搬到 /Volumes/WD-Elements/a2a-evidence/<批次>/<ticket>/，仓库留 *.archive.json（original、archive、bytes、replay，无校验值）；外置盘未挂载报错不回退；删除原件前核对文件数与字节一致；读写带超时。任务卡模板加一句摘要/归档路径规则。T-086 在一次性副本里回放，证明引用不悬空 |
| 非目标 | 不对真实已提交批次搬迁（历史不动）；不瘦身 Git 历史；不改 acceptance/；不加额外提示轮次 |
| 修改边界 | 允许：scripts/ 或 workbench/tests/ 下新归档命令及其测试、workbench/tests/run_s3_regression.py（只抽 archive_large_files 为共用函数，不留两份实现）、.project-map/templates/task-card.md（只加一句）、evidence/2026-10-16-batch16/T-089/；禁止：acceptance/、evidence/ 下已提交的其他批次、.project-map/ 其他文件、AGENTS.md |
| 完成条件 | 见 ticket Acceptance 六条：红态（起点 c544b2904 上无可用入口）；绿态（夹具批次归档后仓库侧只剩摘要与 *.archive.json，外置盘字节一致，清单字段齐）；四个真实入口反例各自失败且原件不删、不回退内置盘：未挂载（用可注入的挂载点参数指向未挂载路径，不得真的卸载外置盘）、目标已存在、截断副本字节不一致、已挂载但读写挂起（用受控挂起的夹具模拟，例如 FIFO 或挂起的子进程，不碰真实盘）；被读取的小文件（run_daemon_acceptance.py 读的三个文件为样本）不归档、类别外文件原样保留；T-086 一次性副本回放并列出每个读 evidence/ 的测试及其结果；改 run_s3_regression.py 之前先在起点取它的绿态并保存命令与结果，抽函数后再跑同一命令 |
| 任务类型 | 构建与基础设施 |
| 复杂度 | M |
| 执行器 | Codex CLI，gpt-6.1-sol，xhigh，service_tier default（launch-27fa492686c840c7b5735426e52a3f8f） |
| 起点 | main c544b29049861998e11eeb7344b457103fab3c98（exec/t089，稀疏 worktree /Users/luckye/Documents/Code/a2a-wt-t089：workbench、acceptance、scripts、.project-map、findings、evidence/2026-10-16-batch16、evidence/2026-10-15-batch15/T-086） |
| 唯一写入者 | s16-t089，task T-089 attempt a1 |

约束：只在本 worktree 写；本 worktree 是稀疏的，核对"哪些测试读 evidence/"时可以只读主仓库 /Users/luckye/Documents/Code/a2a（不写）。外置盘测试只写在 /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089/ 下新建的测试目录，演练完保留清单；T-086 回放用一次性副本（放 /tmp 或外置盘测试目录），不动仓库里的 T-086。沙箱外命令（写外置盘、受控挂起）写成脚本交我跑，不请求升级。可以 git add / git commit 自己的交付（九项尾注，launch 记录号 launch-27fa492686c840c7b5735426e52a3f8f），不 push、不 rebase。语义拿不准就停下报我。
交付：最后一行写 T-089 READY。
