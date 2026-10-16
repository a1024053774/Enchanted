# T-082 第 2 回合准备与交付范围

当前真实回合已用 **1/4**，剩余 **3**。第 2 回合未运行。主控先将当前产品、测试和脚本冻结为检查点，再创建 fixture-04、核对并签批准 JSON。

## 创建与签字

使用更新后的 `REAL-CODEX-FIXTURE-01.sh` 创建 `/Volumes/WD-Elements/a2a-t082-real-fixtures/fixture-04`。它只建夹具，不启动 Codex。manifest 新增 `card_round2`，指向 `task-card-round2.json`。

第 2 回合使用 `reviewer-role-round2.md`。任务目标同时要求 `src/value.txt=correct` 和 `src/details.txt=ready`（均加换行）；完成条件仍只检查前者。脚本交付候选只完成前者，故机械完成条件会放行，而任务完成条件不足可由 reviewer 指出。reviewer 判断是否正确仅如实记录，不作为门禁机械通过条件。

待签草稿：`REAL-CODEX-ROUND2-APPROVAL-DRAFT.json`，`approved_by` 与 `approval_ref` 留空。签好后保存为 `real-approvals/round-2.approved`。脚本核对 round=2、fixture-04、单回合限制和非空签名字段。

```sh
bash evidence/2026-10-15-batch15/T-082/REAL-CODEX-COMMANDS-01.sh --execute 2 \
  --manifest /Volumes/WD-Elements/a2a-t082-real-fixtures/fixture-04/manifest.json \
  --approval-dir evidence/2026-10-15-batch15/T-082/real-approvals
```

默认无 `--execute` 只打印计划，不启动 provider；上述命令由主控运行。

## 读回

- 产品仍走 card→claim→submit→verify→createReview/Panes，完整 argv 来自 `launch-readback.json`；code_revision 取实际冻结 HEAD。
- `report-readback.json` 直接读取门禁入库的对象报告，保存“完成条件与变异检查”节和 `mutation_checks` 数组的真实元素数。数组拿不到就写明 unavailable，不从文字行数推断。
- `end-readback.json` 保存候选提交不变、门禁删除前的审查/worker Git HEAD 和 clean 原始回执、共享 refs 比较、副本及审查目录已删、review_reclaimed 等结果。
- worker 和共享 `.git` 哨兵做 before/after 直接逐字对比。审查目录哨兵在删除后无法再读取，以运行前内容等于 C 中受控文件内容、门禁删除前 HEAD=C 且 clean 的原始回执证明未变；明确标成间接证明，不伪造 after 文件内容。
- `real-readback.json` 区分读取是否完整与模型 verdict；“需修复”同样可以完整入库、回收和清理，不要求模型给“可合并”。
- 启动首屏不按键；终止的协议失败立即留现场，900 秒超时同样保留 daemon/home/副本，等待主控处置。

## 可提交的失败现场

`real-codex-round-1/` 和 `real-codex-round-1-02/` 均纳入本票可提交证据范围，保留所有原始文件，不覆盖失败。

- 前者为 reviewer 启动前的隔离 home 拒收；后者为 reviewer pane 未释放提示；主控确认两次未消耗真实回合。
- 两目录的 `home-after-delete.txt` 都是 absent。内容为命令/配置回执、身份和本机路径、home 文件名列表，不含 auth.json 实体。
- `failed-run-scope-readback.json` 保存文件数、总字节数、>5 MB 检查和凭据字段扫描结果；扫描不是全面的隐私保证，保留本机路径是本票证据的一部分。
- 签字 JSON、报告协议红绿和报告/边界读回可一同提交；隔离 home、auth 副本和外置完整转录不入 Git。

## 验证状态

OUTSIDE-09 全 **PASS**（report roundtrip、T-076 性质、T-077 lifecycle），0 个真实回合。随后新增的报告节键检查已先红后绿：`protocol-section-01/red.json` 缺节未被拒，修复后 `green.json` 的 12 项检查通过。只查键存在，不限制该键的值。

脚本与内嵌 Python 已做语法检查；读回器离线自检 `round2-readback-smoke-01/` 三案 **PASS**（需修复也能完成、无变异数组不推断条数、共享 refs 改动拒收）。这些是合成的读回器输入，不算真实门禁证据。第 2 回合读回工具尚未在真实第 2 回合执行，因此整票仍 **INCOMPLETE**。
