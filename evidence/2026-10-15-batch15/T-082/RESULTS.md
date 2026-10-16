# T-082-1 RESULTS

已有检查点：`0dd00d09dcdd4a6ae9c3b633e678419037485875`。本轮其上新增报告协议修复，尚未冻结新提交。已消耗 **1/4** 个真实 Codex 回合，剩余 **3**；第 2 回合未运行。整票 **INCOMPLETE**。

## Acceptance 逐条结果

1. **红态在先：INCOMPLETE（请求缺项已证明；旧只读证明待核对读回）**

   命令：`python3` 静态红态探针（见 `red-state/static-red.json`）。

   结果：起点 reviewer 请求没有完成条件充分性/2～5 变异要求，启动仍是 `read-only`，reviewer 工作目录仍是审查 worktree。

2. **受控入口与四种拒收：PASS**

   命令：`OUTSIDE-COMMANDS-02.sh`，输出 `outside-command-02-02/`。

   结果：tracer、旧只读 argv、错误工作目录、网络开启、`/tmp` 可写五案均 PASS；四个变异均由 `review_launch_boundary` 拒收。`real_codex_turns=0`。

3. **真实 Codex 边界证明：PASS（检查点 0dd00d09 的权限边界；不代表整条门禁完成）**

   `real-codex-round-1/` 在 reviewer 启动前被 `isolated_codex_home_required` 拒收；`real-codex-round-1-02/` 未释放任务提示。第三次 `real-codex-round-1-03/` 通过产品路径启动并完成 **1 个**真实回合，原生模型 gpt-6.1-sol / xhigh；sandbox workspace-write、network=false、exclude_slash_tmp=true、exclude_tmpdir_env_var=true。

   `REAL-BOUNDARY-READBACK-01.md` 与 `real-boundary-readback-01/` 保留实际工具输出：副本写入/测试成功；审查目录、worker worktree、共享 `.git` 写入均 Operation not permitted；共享 update-ref exit 128；curl 域名 exit 6、直连 IP exit 7。三个 before 哨兵与后续只读内容相同。主控已停 daemon，隔离 home 删除读回 absent。后续主机读回不替代门禁当时的结束核对。

   受控副本探针：`OUTSIDE-COMMANDS-01.sh`，`outside-command-04/` PASS；内部 symlink 按内容复制，外部 symlink 拒绝。

4. **结束核对：PASS（原受控候选）/ INCOMPLETE（本次真实正常结束）**

   命令：`OUTSIDE-COMMANDS-03.sh` 的 `end-check`，输出 `outside-command-03-01/`。

   原受控结果：审查 worktree 外部改动使结论作废并上报；正常路径删除候选副本。T-077 reviewer worktree 生命周期同批 PASS。真实第 1 回合因报告协议失败，未进入门禁结束核对、未删副本；后续只读 Git 读回 HEAD、两个 worktree 干净、共享 refs 未变（`host-git-readback.json`），不回填成门禁已完成。

5. **真实交付审查与完成条件/变异报告：INCOMPLETE**

   第 1 回合已有完整对象报告和 3 个变异，实际工具输出可复核；模型将完成条件评为够格。但原解析器拒收报告，未成为有效门禁结果；本回合不代替第 2 回合的偏弱完成条件交付审查。报告见 `real-boundary-readback-01/report-from-rejected-stop.json`。

   本票产品缺陷及离线修复见 `PROTOCOL-REPAIR-01.md`：模板含 `review_requirements`、没有 report 栏，解析器仍只接受 12 个字段。真实 raw 在修前 `review_request` 红态、修后严格解析/relay 10 项绿态；结果在 `protocol-red-green-01/`。Stop→入库→回收的受控全路径已由 `outside-command-09-01/` 证明 PASS。主控 #47 要求只查报告节键存在，新增 `report.section` 红绿和不判键值内容的正例后，共 12 项绿态，证据 `protocol-section-01/`。

6. **真实回合预算：PASS（当前 1/4）**

   原生归档读回主回合数为 1，剩余 3。第 1 回合经逐次签名 JSON 批准；启动记录保存完整 argv。隔离 home 仅复制 auth 并生成 fixture 信任配置/两条 Git prefix rule；主控在协议失败超时后停止 daemon、删除整个 home，读回 absent。未启动第 2 回合，也未重放真实回合。

7. **T-076/T-077 回归：PASS（性质级）/ INCOMPLETE（旧 runner）**

   T-076 三项性质命令：`OUTSIDE-COMMANDS-07.sh`，输出 `outside-command-07-01/t076-property-tracer`，三案全 PASS：

   - `tracer_wrong_candidate` → `TRACER-REVIEW-CANDIDATE`；
   - `tracer_reused_native` → `TRACER-REVIEW-REUSE`；
   - `tracer_writer_cannot_review` → `TRACER-WRITER-REVIEW`。

   报告协议修复后，T-076 三项性质及严格 JSON、T-077 reviewer lifecycle 已由 `outside-command-09-01/` 复验全 PASS，real_codex_turns=0。此后仅加必需报告节的键存在检查，离线红绿见上。

   旧 `run_t076_quality_green.py` 审计拒收另列，不改审计、不改 `a7f4cc30`。先前将拒收归因为 dirty diff 的说明不准确：代码记录当前 diff，但拒收条件看的是命令退出码及原 acceptance 文件相对锚点的 diff，不是当前 diff 是否为空。锚点迁移已由主控交待决，本票不处理。旧 launch-policy 的快照缺 `oracle_paths`，在 `card_save` 阶段报 `invalid_task_card`，main 上同样失败（`outside-command-08-01/`）；属于既有夹具问题。

## 当前限制

- 报告协议修复的受控全路径 OUTSIDE-09 已通过；第 2 回合仍未运行。执行草稿/读回说明见 `ROUND2-READY.md`。
- 旧 T-076 launch-policy 快照不迁移；锚点迁移留待上游待决问题。
- main checkout 既有 launch-policy 失败已由 `outside-command-08-01/` 复现。
- 原始 `outside-command-*` 日志现场保留；大于 5 MB 的目录不在本文件中重复展开。
- `real-codex-round-1/` 与 `real-codex-round-1-02/` 两次未消耗回合的失败现场可随本票提交，细目和凭据字段扫描见 `failed-run-scope-readback.json`，不覆盖历史失败。
