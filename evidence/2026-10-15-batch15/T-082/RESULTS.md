# T-082-1 RESULTS

2026-10-16 最终口径更新：依据主控 #59 转交的用户答复 `20261016T051655Z` 及更正 `20261016T051703Z`，采用“接受重建的红态 (Recommended)”与“不迁锚点，三项性质直跑 (Recommended)”。Acceptance 2、7 按下述明确口径记 **PASS**；不改重建证据的时间标注，不迁 T-076 锚点，不再修改 runner 或受保护验收文件。本次只更新此报告，最终验收与合入由执行主控办理。

独立审查 02 对 `5f7f9816eb9a996377c5b255695244d99c0259e7` 确认第一轮五条均解决，四个错误实现被指定业务断言检出，未发现产品缺陷；其原始 **INCOMPLETE** 结论保留。该次剩余的时间顺序口径已由上述用户答复确认；P3 报告字段问题已在 `9fd96145e` 修复，`outside-command-13-01/` 红绿与失败路径检查均 PASS，详见 Acceptance 7。独审 01 的 NO_GO、返工过程及失败现场均保留，不改写为当时已通过。

## 任务与证据范围

任务/执行：T-082-1 / s15-t082 / attempt a1；规格为 T-082 ready_rev 1、D3，验收口径以上述两份用户答复为准。真实第 2 回合在 `7f2bd40611e920cb962ba20f17b58bb12a9acab0` 运行；后续门禁返工由冻结候选 `5f7f9816e` 的独立审查 02 验证，runner 报告修复为 `9fd96145e`。旧真实回合不替新增门禁检查背书。

真实第 2 回合完整路径 **PASS**，真实回合累计 **2/4**，剩余 **2**。下列具体检查及按用户确认口径计算的证据结果为 **PASS**；T-076 完整质量 runner 被审计拒收仍如实记为预期 **INCOMPLETE**，不改写为完整 runner 通过。最终验收与合入尚待执行主控完成。

除明确写出的主 checkout/外置盘绝对路径外，下列输出路径均相对本目录。命令从本 worktree 根运行；真实命令是主控已经执行的记录，不是再次运行的请求。

## Acceptance 逐条结果

1. **红态在先：PASS**

   命令/来源：`git show 451be8462c85fd08b997cb85453188a8e5751c9d:workbench/src/gates/core.ts`、同修订的 `workbench/src/panes.ts`；起点静态探针输出为 `red-state/static-red.json`。历史只读证明沿用主 checkout 的 `evidence/2026-10-11-batch13/T-076/card-2/outside-p-review-02/`，只读核对其中 `run.json`、`sentinel-result.json`、`launch-before-spawn.json` 和 `fixture-artifacts.tar.gz` 中的哨兵；提取读回为 `red-state/t076-readonly-readback.json`。

   结果：起点 reviewer 请求没有完成条件充分性/2～5 变异要求，启动仍是 `read-only`，工作目录仍是审查 worktree。T-076 实际原生工具回执为 `write_attempts=1, denied=true, errno=1`；归档中的事后哨兵逐字等于事前内容。历史 launch id 为 `aae6f34a-072c-4740-9ba6-5c4452fe110e`，完整 argv 已读回。历史总报告的 `product_status=INCOMPLETE` 原样保留；仅复用该次只读拒写事实，不用旧结论证明新边界，也不计入本票新真实回合。

2. **受控入口与四种拒收：PASS（按用户确认的红态口径）**

   命令：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-02.sh`；输出 `outside-command-02-01/`、`outside-command-02-02/`。副本复制探针命令为同目录 `OUTSIDE-COMMANDS-01.sh`，成功输出 `outside-command-04/`。

   Tracer bullet 的请求必查项、副本建立/清理、启动核对五案均 PASS：`tracer_review_copy` 验证 `T082-REQUEST-COMPLETION`、`T082-REQUEST-MUTATIONS`、`T082-REVIEW-ARGV`、`T082-COPY-CREATED`、`T082-COPY-REMOVED`；四个启动参数变异均被 `review_launch_boundary` 拒收，断言 `T082-LAUNCH-REFUSED`、`T082-LAUNCH-PAUSED`、`T082-LAUNCH-ISSUE` 通过。副本省略 `.git`，内部 symlink 按内容复制、外部 symlink 拒绝，源目录未变。全部 `real_codex_turns=0`。

   `wrong-workspace` 保留实际修前红态→修后绿态：02-01 中 argv 的 `-C` 被改到副本外，门禁仍返回 `ok:true`，`T082-LAUNCH-REFUSED` 失败；补上实际 argv 工作目录核对后，02-02 拒收。`readonly-argv` 按原有真实先后顺序采用旧 read-only 启动/拒写证据（`red-state/t076-readonly-readback.json`）和候选拒收绿态，不把它列为此次重建项。

   `network-enabled`、`tmp-writable` 采用修复后在起点 `451be8462c85fd08b997cb85453188a8e5751c9d` 重建的反事实红态，命令为 `bash evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-10.sh`，输出 `outside-command-10-01/`；该批也包含一份额外的 `wrong-workspace` 重建。三案均在确认门禁启动并释放 reviewer 到受控 busy 状态后，于 `T082-LAUNCH-REFUSED` 产生 contract_failure，各自对应候选拒收绿态。网络/tmp 案只证明旧启动边界不检查相应参数，不证明旧 read-only 沙箱实际允许这些操作。

   依据用户答复 `20261016T051655Z` 及更正 `20261016T051703Z` 的“接受重建的红态 (Recommended)”，上述两种反事实满足本条口径。`outside-command-10-01/run.json` 的 `counterfactual_timing` 原文 `reconstructed after the fix on the starting revision; not an earlier chronological run` 保留；不得写成 network/tmp 当时已按时间顺序先运行红态。独立审查 02 的 R/09 另复验四种当前拒收均 PASS。

3. **真实 Codex 边界证明：PASS（第 1 回合边界原文 + 第 2 回合结束读回）**

   命令：`bash evidence/2026-10-15-batch15/T-082/REAL-CODEX-COMMANDS-01.sh --execute 1 --manifest /Volumes/WD-Elements/a2a-t082-real-fixtures/fixture-03/manifest.json --approval-dir evidence/2026-10-15-batch15/T-082/real-approvals`；输出 `real-codex-round-1-03/`。它经 daemon→交付/verify→createReview→Panes 启动 reviewer，工作目录由门禁创建，脚本没有手写 Codex argv。

   读回命令：`python3 -B workbench/tests/collect_t082_real_boundary.py --run evidence/2026-10-15-batch15/T-082/real-codex-round-1-03 --rollout /Volumes/WD-Elements/a2a-evidence/2026-10-15-batch15/T-082/real-codex-round-1-03/rollout-2026-10-15T21-28-02-01a14252-c3dc-7f33-97a1-6213dae979a7.jsonl.gz --output evidence/2026-10-15-batch15/T-082/real-boundary-readback-01`。输出目录已存在，不覆盖重跑。

   `REAL-BOUNDARY-READBACK-01.md`、`real-boundary-readback-01/boundary-readback.json` 和 `native-tool-output-line-39/46/53/62.txt` 保存实际工具原文：副本写文件、读文件与 `./test-command.sh` exit 0；审查目录、worker worktree、共享 `.git` 写入均 exit 1、`Operation not permitted`；共享 `git update-ref` exit 128、`cannot lock ref`；curl 域名 exit 6、`Could not resolve host: example.com`，直连 IP exit 7、`Failed to connect to 1.1.1.1 port 443`。原生 context 为 gpt-6.1-sol / xhigh / workspace-write，network_access=false，两个 tmp 排除标志均 true。三份哨兵事前/事后逐字相同；探针尝试的是新建文件，未声称测过覆盖哨兵。

   第 1 回合在旧协议解析处暂停，没有进入门禁正常结束；其后主机 Git 只读读回不能补称门禁已完成。第 2 回合的 `real-codex-round-2/end-readback.json` 补齐实际门禁结束核对：候选号不变、审查/worker 工作区干净、共享 refs 未变、哨兵未变、候选副本已删除。审查目录删除后的直接哨兵读回不可得，证据明确使用删除前 HEAD=C、clean 和受控文件内容的间接证明；worker/共享 `.git` 哨兵为直接事前/事后对比。

4. **结束核对：PASS**

   命令：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-03.sh` 的 `end-check`；输出 `outside-command-03-01/end-check/`。正常真实路径为下条 `--execute 2`，输出 `real-codex-round-2/`。

   结果：`external_review_boundary_invalidated` 中副本外改动使审查结论作废、task paused/review unknown 并上报，保留异常现场（`T082-END-CHECK-INVALID`）。T-077 生命周期套件另覆盖脏审查目录、审查 HEAD 改变的拒收与正常清理。真实 round-2 的 `real-readback.json` 九项全 true：结果入库、候选提交不变、审查目录删除前干净、worker worktree 干净、共享 refs 不变、副本删除、审查目录删除、review_reclaimed、哨兵未变。原始 Git 回执和生命周期事件见 `end-readback.json`，C=`af586aed2709b46768f90e334156cf9197d0115e`。有效“需修复”报告也正常入库与回收，不要求模型给“可合并”。

5. **一次偏弱完成条件的真实交付审查：PASS**

   命令：`bash evidence/2026-10-15-batch15/T-082/REAL-CODEX-COMMANDS-01.sh --execute 2 --manifest /Volumes/WD-Elements/a2a-t082-real-fixtures/fixture-04/manifest.json --approval-dir evidence/2026-10-15-batch15/T-082/real-approvals`；输出 `real-codex-round-2/`，exit 0。使用 `reviewer-role-round2.md` 和 `task-card-round2.json`；目标要求 value.txt、details.txt 两个文件，但唯一完成条件 `acceptance/weak.py` 只检查前者。

   结果：Stop→严格解析→review_result 入库→回收→结束核对→删副本完整 PASS。`report-readback.json` 从入库报告读取“完成条件与变异检查”节及 5 个变异，各含改动、命令与退出码：value 错内容/无换行两案 exit 1 被拒；details 缺失/错内容/无换行三案 exit 0 逃逸。reviewer 判“需修复”，指出缺少 details.txt，并要求补存在性与精确内容（含 LF）检查。模型判断和缺失检查如实记录，正确性不作门禁条件；门禁机械校验报告对象非空及该节键存在，不评价节内容或模型判断。

   第 1 回合曾因模板/解析器字段不一致报 `review_request`，仍保留为失败，详见 `PROTOCOL-REPAIR-01.md`。实际 raw 的修前红态、修后严格解析/relay 绿态在 `protocol-red-green-01/`；`OUTSIDE-COMMANDS-09.sh` 的 report-roundtrip 全路径 PASS。主控 #47 要求的节键检查另先红后绿：`protocol-section-01/` 共 12 项检查，含缺节拒收和只查键存在、不判键值的正例。round-2 验证的是包含该修复的检查点。

6. **真实回合预算、argv 与隔离 home：PASS（2/4）**

   命令与输出：上述 `REAL-CODEX-COMMANDS-01.sh --execute 1/2`，分别 `real-codex-round-1-03/`、`real-codex-round-2/`。完整产品生成 argv、shell argv、CLI 版本和实际 code_revision 在各目录 `launch-readback.json`；原生 context/事件在第 1 回合外置归档与第 2 回合 `traces/`。两回合各一个主回合，累计 2，剩余 2；初次 `real-codex-round-1/` 被隔离 home 前置检查拒收、`-02/` 未释放提示，均未消耗真实回合。

   启动固定 codex-cli 0.162.1 / gpt-6.1-sol / xhigh；请求 service_tier=default，不把请求当成供应商实际 tier 的证明。reviewer 的 `-C` 指向本次 review-copies/<review_id>，`--sandbox workspace-write -a never`，network/proxy 关闭、exclude_slash_tmp 与 exclude_tmpdir_env_var 为 true。逐回合签名批准见 `real-approvals/round-1.approved`、`round-2.approved`，hook 仅在对应批准后由产品 argv 传入。

   每回合 `/private/tmp` 新建隔离 home，只复制用户 `auth.json`；额外生成的最小配置、两条 Git allow prefix rule 和文件名清单有留证（`home-trust.toml`、`home-rules.default.rules`、`home-before-delete*.txt`），未复制用户其他配置。信任根限已核对外置 fixture 根；daemon HOME 与 reviewer CODEX_HOME 分开。第 1 回合主控处置记录 `home-after-delete-controller.txt=absent`，第 2 回合脚本 `home-after-delete.txt=absent`。auth 实体和隔离 home 不进入证据/Git，未写用户全局配置。

7. **T-076 三性质直跑、T-077 与地图：PASS；完整质量 runner 的审计拒收为预期 INCOMPLETE**

   命令：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-07.sh`、`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-09.sh`；输出 `outside-command-07-01/t076-property-tracer/`、`outside-command-09-01/t076-properties/` 与 `outside-command-09-01/t077-review-lifecycle/`。runner 的 `--source` 均指本 worktree 候选，不用 main 代跑候选。

   - `tracer_wrong_candidate` → `TRACER-REVIEW-CANDIDATE`；
   - `tracer_reused_native` → `TRACER-REVIEW-REUSE`；
   - `tracer_writer_cannot_review` → `TRACER-WRITER-REVIEW`。

   用户答复 `20261016T051655Z` 及更正 `20261016T051703Z` 选择“不迁锚点，三项性质直跑 (Recommended)”。本条 T-076 回归证据为三项性质直接调用候选的 tracer：首次输出 `outside-command-07-01/t076-property-tracer/`；返工后冻结候选的独立复验为审查 02 的 R/07，即 `R=/private/tmp/r82r2-bCfvVo` 下的 `07-t076-properties/`，六案（含这三项、严格协议与两种 default argv）全 PASS。完整命令为 `bash evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-02.sh`，对应报告 `independent-review-02.md`，不以旧完整 runner 的结果代替三项直跑。

   T-077 套件四案均 PASS：`cleanup_after_persisted_result`、`names_and_ordinals`、`dirty_review_is_preserved_and_reported`、`changed_review_head_is_preserved_and_reported`；返工后的独立复验为审查 02 的 R/08（`08-t077-lifecycle/`）。上述受控回归 `real_codex_turns=0`。

   地图命令：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`，收尾输出 `final-status-01/`，0 problems、0 stale living docs。

   完整质量 runner：`OUTSIDE-COMMANDS-06.sh`，输出 `outside-command-06-01/t076-quality-source-audit/`，报 `Source audit failed or original acceptance assertions changed.`，保留 **INCOMPLETE**。按用户已确认的“不迁锚点”口径，这个审计拒收是预期状态，不是尚待修复的 T-082 回归项；本次不改 T-076 runner 或任何受保护验收文件。审计机制与 `a7f4cc3033c16d5888de50d8352da516c941f8e9` 锚点保持原样：记录当前源码 diff 不等于因 dirty 拒收；实际命令 4 exit 0、原 acceptance 文件对 a7f4cc30 的 diff stdout 非空，触发原审计。该拒收不直接归因于 D3 tracer 断言改动，也不标成完整 runner PASS。T-076 ticket 的说明由主控追加，worker 不改票据。

   旧 launch-policy runner：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-08.sh` 只读在 main 原样运行，输出 `outside-command-08-01/t076-launch-policy-main/`，**INCOMPLETE**。与候选一样报 `Fixture error is not contract evidence: worker-missing-override-red`：real-delivery-01 旧快照 taskCards.ts 不接受当前夹具的 `oracle_paths`，在 `card_save` 阶段 `invalid_task_card`，未到预期业务红态。主控 #43 已确认是基线既有、与本票无关；本票不修改旧快照或绕过校验。

   P3 报告字段修复：提交 `9fd96145e`，命令 `bash evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-13.sh`，输出 `outside-command-13-01/`，三段检查均 **PASS**。旧成功报告的字段不一致按预期被检查检出；修后成功路径 exit 0，报告和 stdout 均为 `status=PASS / product_status=PASS`；受控前置失败路径 exit 1，报告和 stdout 均为 `INCOMPLETE / INCOMPLETE`。`check_t076_phase_report.py` 读取最终报告、stdout 并与实际退出码核对，修后两个检查的 errors 均为空。失败路径的一致性检查 PASS 不等于该前置失败业务成功。此修复与完整质量 runner 预期审计拒收分别记账。

## 最终交接

- 两项验收口径已有用户答复与更正，不再列为 worker 待决项；重建时间标注和完整 runner 的预期 INCOMPLETE 均保留。
- 独立审查 02 已完成，原结论不改写；所列时间顺序口径及 P3 后续处理如上。最终验收与合入待执行主控办理，本报告不代替主控操作。
- 第 1 回合的协议失败、初次隔离 home 拒收、第二次未释放提示以及各次 outside 失败现场都保留。第 2 回合正常全路径通过没有把这些历史失败改成成功。删除后的审查哨兵没有直接 after 值，间接证明及范围已注明。

## 可冻结范围

产品返工与独审证据已冻结，P3 修复及 OUTSIDE-13 证据在 `9fd96145e`。本次只提交本目录的 `RESULTS.md`，不改代码、runner、受保护验收文件或票据。既有 round-2 为 48 个文件、1,213,814 字节，无单文件超过 5 MB。

`real-codex-round-1/` 与 `real-codex-round-1-02/` 两次失败现场已纳入前一检查点的可提交证据范围；细目见 `failed-run-scope-readback.json`。auth 副本、隔离 home 和外置完整原生转录不入 Git。证据保留本机路径；凭据字段扫描只是有限检查，不作全面隐私保证。收尾校验记录见 `final-status-01/closeout.json`。
