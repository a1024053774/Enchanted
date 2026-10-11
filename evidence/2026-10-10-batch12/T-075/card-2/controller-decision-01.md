# T-075-2 执行主控决定 01：批准 PLAN（2026-10-11）

`card-2/PLAN.md` 整体批准，按它的第 7 节顺序做。以下几点是批准时附带的要求，与 PLAN 冲突时以本决定为准。

1. **先跑第 3 节的 Git 探针。**
   - 用 `update-ref --stdin` 事务加 `read-tree -m -u` 双树快进，要通过 PLAN 列出的全部条件。其中需要 ps 或要人为终止进程的窗口，按沙箱外交接流程交给我执行。
   - 探针一旦失败或结果不明，立即停下写 needs-decision，不换路线，也不写兜底实现。
   - `symref-verify` 先确认本机 Git 2.52.0 真的支持。不支持就停下报告，不要自行降级。
2. **任务卡格式采用 JSON 加 argv。** 完成条件里的 `{worktree}` 只允许作为一个完整的参数元素做替换。
3. **删除 `--oracle`、`--instructions`、`--base`。** 不保留两套入口，旧的 `refs/a2a/integration` 不再写入，这些都同意。
   - 公开错误码继续沿用 `oracle_failed`。事件里写明是第几条完成条件失败。
   - RESULTS 里写明：这个错误码名字保留下来，只是为了不改动公开的错误预期。
4. **尾注的归属**按 Task、Attempt、Session、Role 四个字段判定，同意。
   - 旧测试里的候选提交没有尾注，按 D26 会被记成人工介入，这是预期行为。RESULTS 里给出它们在三套测试中各产生了多少条这类记录。
5. **断言白名单 A1–A10 批准。** 一旦需要改动白名单之外的断言，先停下报告。
6. **任务卡命令**的名字（`card_template`、`card_validate`、`card_save`、`card_show`）和 13 个字段的拆法，同意。
   - 执行器的 CLI 只允许“Claude Code”或“Codex”两个值，大小写和写法在 RESULTS 里固定下来。
7. **规模。** 本卡是 L。PLAN 里的 tracer bullet（第 7 节第 2 步）跑通后，回一行 `T-075 TRACER READY`，然后继续往下做，不用停下等我。我会抽查。
8. **沙箱外交接**照旧：写好 `card-2/outside-sandbox.sh`，回一行 `T-075 OUTSIDE-SANDBOX READY`，然后停下等我执行。
