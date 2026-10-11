# 冲突流程的窗格边界检查

2026-10-11，主控 #47 后。核心冲突流程已经取得七项起点红态。`ConflictContracts` 替换原生会话边界，无法证明生产 Panes 的行为，所以在改 Panes 前补充以下隔离检查。它们直接调用被测版本的 Panes 和 OrchestrationStore，仅替换外部 `ps` 的返回和 PTY 对象；不启动 shell、Codex、socket 或真实子进程信号。真实原生场景仍须另验。

预先列出故障方式：

1. 已归档且已停止的旧 pane 仍占活跃名额，导致新 attempt 无法创建；相反，未归档的旧 pane 若被释放，则会扩大为未经授权的并行窗格。
2. 隔离 home 中保留的旧 rollout 被绑定到新 attempt，产生身份误认或歧义；必须按 rollout 的工作目录归属选择日志，同一工作目录出现第二个 CLI 会话仍须拒绝。
3. 已知领导进程退出、进程树仅剩原 shell、上一回合已空闲时，应记录会话结束；辅助进程出现不能视为结束，领导进程被替换或观察不明不能视为正常结束。
4. 门禁反馈必须进入原 pane 的队列并标记 gate 来源，忙时不直接向 PTY 提交；空闲投递仍经现有 drain 和总回合预算，不能另写终端通道。

起点运行命令（输出名不得已存在）：

```sh
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_conflict_panes.ts --product /private/tmp/s3-base-wf0ea6cj --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/panes-conflict-red-01.json
```

`/private/tmp/s3-base-wf0ea6cj` 是 conflict-red-01 主控创建的冻结起点，来源绑定见 `baseline-conflict-red-01.json`。脚本逐文件与起点归档核对由后续准备检查记录；本测试自身在输出中记录实际 product 路径和四项行为结果。退出 1 只表示检查失败，须核对保存结果中的 assertion failures；环境或夹具错误不算红态。

候选同一信号：

```sh
node /Users/luckye/Documents/Code/a2a-wt-t077/workbench/tests/test_conflict_panes.ts --product /Users/luckye/Documents/Code/a2a-wt-t077 --output /Users/luckye/Documents/Code/a2a-wt-t077/evidence/2026-10-11-batch13/T-077/panes-conflict-green-01.json
```

这些检查不证明 `ps` 的真实 macOS 输出、真实终端或模型理解。受控边界的结果与七项 CLI 场景、后续真实冲突场景分别报告。
