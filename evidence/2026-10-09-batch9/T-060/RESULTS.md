# T-060：ack 是终结

**INCOMPLETE：实现与端到端验证已通过，独立审查返回 INCOMPLETE，需主控判定其局限。** ticket 保持 open，待主控关闭。

执行依据：[任务书](../brief-T-060.md)、T-060 `ready_rev: 1`。本票明确替代日期 spec 第 5 节的 ack 判定，日期 spec 不改。代码候选：`c4ce31d73914fd5afa9eae59b5cb76a1fa5c1331`；T-053 最终行为基线：`8e260461f32e49c3b1bce50bedeceb4fad38aa8a`；fork none。

`list` 对所有角色跳过 `kind: ack`。`ack` 和现有的 `send --kind ack` 都拒绝确认 ack：退出 1，说明“ack 是终结”，不创建条目或暂存文件。确认普通条目的行为保持原样，包括顺序重复确认无副作用。没有增加新入口、依赖或兼容路径。

| 验收条件 | 结果与证据 |
| --- | --- |
| 先红后绿 | PASS；新用例先在 T-053 最终入口运行，构思、执行主控均看到终结 ack；再次 ack 返回 0，产生三条新确认。两个用例共有 9 个失败断言，退出 1。[红态输出](red-01/output.txt)、[完整命令与输出](red-01/commands.json)。 |
| 终结 ack 不列出、不能再确认 | PASS；覆盖 ideation、executor、user，以及 ack/send 两个现有写入入口；拒绝前后项目地图全部文件字节一致。 |
| 其他条目的判定保持 | PASS；T-053 原 14 项用例与预期未改，新增用例核对 assign、revise、cancel、stop、report、needs-decision、issue、disposition、answer 的确认前后清单及非收件人的 ack 不算确认。 |
| 相关套件 | PASS，17/17，退出 0。[绿态输出](green-01/output.txt)、[完整命令与输出](green-01/commands.json)。 |
| 已知坏实现 | PASS，四个 mutant 被业务断言拒绝、均退出 1、没有测试 setup 错误。完整旧行为 mutant 与 T-053 最终入口字节一致；另外三个分别去掉 list、send、ack 的终结检查。[反例记录](mutants.json)。 |
| 真实收件箱只读 | PASS；真实 ideation、executor、user 的 list 均退出 0、无 ack 条目；Git 状态与 `.project-map/` 全部文件字节前后一致。[原始记录](real-readonly-01.json)。 |
| fresh-context 独立审查 | INCOMPLETE；功能探针通过、父行为被拒，但审查者把其他任务的并发改动视为快照变化，且未核验允许写在 RESULTS 的行为说明。原结论保留，见 [REVIEW](REVIEW.md)。 |
| 静态检查与地图状态 | PASS；两个改动源文件及两个证据工具 compile()、范围内 git diff --check、中文文件 UTF-8/无 BOM/LF 和本地链接核对；项目地图 Problems 0、Stale living docs 0。[检查记录](static-checks-final.json)、[最终地图状态](project-status-final.json)。 |

## 行为说明

front matter 的行内列表接受两种写法：JSON 数组（例如 `refs: ["ticket:T-060", "ticket:T-054"]`）和无引号方括号列表（例如 `refs: [ticket:T-060, ticket:T-054]`）。后者按逗号拆分、去除首尾空白；不支持一般 YAML 的多行列表、嵌套结构。refs 的元素仍须是字符串；blocked_by 沿用相同的列表读取方式。

`send`、`ack` 先读取整个收件箱，发现任何损坏条目就拒绝写入，包括损坏 front matter、非 UTF-8、缺失字段和悬空 reply_to。这是有意的：确认和引用依赖完整条目流；跳过损坏记录后继续写入，可能漏掉既有确认或引用链，造成错误判断。应先核对损坏记录；本脚本不删除、修补或覆盖它们。`list` 保留原行为：列出可读的有效条目，同时报告损坏条目并退出 1。

## 复现与证据

以下输出目录或文件须尚不存在，避免覆盖历史运行：

```sh
INBOX_SCRIPT="$PWD/evidence/2026-10-09-batch9/T-060/snapshots/parent/scripts/inbox" \
  python3 -B acceptance/test_inbox_e2e.py --artifacts /tmp/T-060-red-replay-01 \
  InboxCLI.test_ack_is_terminal_in_all_role_lists \
  InboxCLI.test_ack_terminal_rejects_both_write_entry_points
python3 -B acceptance/test_inbox_e2e.py --artifacts /tmp/T-060-green-replay-01
python3 -B evidence/2026-10-09-batch9/T-060/run-mutants.py --out /tmp/T-060-mutants-replay-01
python3 -B evidence/2026-10-09-batch9/T-060/check-real-readonly.py --output /tmp/T-060-readonly-replay-01.json
```

[版本、命令与 skill 版本](candidate.json)、[运行环境及 worker 启动参数](environment.json)绑定本票。启动记录请求 `gpt-6.1-sol`、xhigh、fast，不把请求配置当作供应商实际 tier 证明。任务书未提供受管 attempt/session/fence，本报告只交付 Herdr 期指定 worker 的本地候选，不宣称已完成工作台门禁验收或集成。

完整失败输出、夹具、写入中断的暂存文件与 mutant 源码保存在 [原始运行归档](raw-runs.tar.gz)；归档内 260 个文件与原文件直接逐字节比较一致，无哈希，[归档核对记录](archive-verification.json)。可在新的空目录解包查看。日志保留在 red-01、green-01；原始夹具还保留在本机 raw-artifacts 下，只归档入 Git。独立审查的输入、完整命令、输出、错误命令现场及探针另存于 [独立审查归档](independent-review-raw.tar.gz)。

## 需主控判定

本票六项验收均有实现者证据，独立探针也确认功能行为；独立审查总状态仍为 INCOMPLETE。冻结候选及两个源文件未改变的补充证据、文档位置和审查局限见 [REVIEW](REVIEW.md#证据保存与实现者补充)。主控需判定这些证据是否足够关闭票据，或另行授权补审。任务书要求一次审查，本次没有追加第二次审查，也没有把该结论上调为 PASS。

本次未运行 fork 构建、Synara UI、模型任务或跨会话唤醒，这些不属于 T-060 的 CLI/文件系统验收。没有操作正式工作台或写入真实收件箱。
