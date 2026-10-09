# T-053 执行主控决定 01 补验收（2026-10-09）

**PASS：只对 open ticket 检查就绪字段，区分“未标就绪”与“不合规”。** ticket 保持 open，待主控关闭。

依据 [执行主控决定 01](controller-decision-01.md)，`ready_rev: 1`。代码提交：`8e260461f32e49c3b1bce50bedeceb4fad38aa8a`；fork none。改动限 `scripts/inbox` 的 ready 判定和两个真实 CLI 回归用例；未改 ticket 的授权、状态或角色卡。

ready 先过滤非 open 状态，再检查就绪字段。open 且完全没有三个就绪字段的列为“未标就绪”，不导致错误退出；部分缺字段的仍列“不合规”、退出 1。closed/superseded/out-of-scope 不产生就绪诊断，仍保留为依赖解析来源。

| 验证 | 结果 |
| --- | --- |
| 修复前两个新用例 | FAIL；已结束 ticket 被报缺字段，完全没有就绪字段的 open ticket 被误报不合规；各以真实 CLI 退出 1 复现。 |
| 修复后相关套件 | PASS，14/14，退出 0；覆盖三种已结束状态、已结束依赖、未标就绪、两种部分缺字段及原有全部用例。 |
| 真实仓库修复前 | 3 条 READY、52 条不合规、0 条未标就绪，ready 退出 1。 |
| 真实仓库修复后 | 3 条 READY（T-053～T-055）、5 条未标就绪（T-010～T-014）、0 条不合规，ready 退出 0。 |
| 只读验证 | 修复前、修复后各次运行 ready/list，Git 状态和 .project-map 文件字节前后均完全一致。 |
| 编译与差异检查 | PASS；两个源文件 compile() 通过，git diff --check 通过。 |
| 本次修正的 fresh-context 只读独立审查 | PASS；陌生 sentinel 通过候选、拒绝父修订，范围仅为决定 01，见 [审查记录](decision-01-REVIEW.md)。 |

原始输出、完整 argv 和退出码：

- [红态](decision-01-red/output.txt)、[红态命令](decision-01-red/commands.json)。
- [绿态](decision-01-green/output.txt)、[绿态命令](decision-01-green/commands.json)。
- [真实仓库修复前](decision-01-real-before.json)、[真实仓库修复后](decision-01-real-after.json)，均包含运行前后的完整 git status 和地图文件清单。
- [版本与计数绑定](decision-01-candidate.json)；完整夹具及失败现场在 `decision-01-raw.tar.gz`，本机原目录内容保留在已忽略的 `raw-artifacts/decision-01-*`。
- 独立审查的输入、预期、候选与父修订源码、原始输出和判定在 `decision-01-independent-raw.tar.gz`；探针原样保存在 `decision-01-review-probe.py`。

重放使用新的输出目录/文件，保留已有证据：

```sh
python3 -B acceptance/test_inbox_e2e.py --artifacts /tmp/T-053-decision01-replay-01
python3 -B evidence/2026-10-09-batch8/T-053/check-real-readonly.py --output /tmp/T-053-decision01-real-replay-01.json
```

没有扩大到其他入口、fork 构建或外部运行；旧报告的真实 ready 退出 1 是当时结果，本补验收保存新的结果。
