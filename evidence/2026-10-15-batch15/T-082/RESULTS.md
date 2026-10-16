# T-082-1 RESULTS

任务/执行：T-082-1 / s15-t082 / attempt a1；规格为 T-082 ready_rev 1、D3。最新产品与测试检查点为 `7f2bd40611e920cb962ba20f17b58bb12a9acab0`，真实第 2 回合在此版本运行。本次收尾只补文档和证据，没有再改产品代码或启动真实 Codex。

真实第 2 回合完整路径 **PASS**，真实回合累计 **2/4**，剩余 **2**。七条中第 1、3～7 条的下述检查 **PASS**；第 2 条当前四种拒收 **PASS**，但其中三种未保存逐项修前失败证据，因此该条及整票暂记 **INCOMPLETE**，交主控冻结后独立审查。旧 runner 的拒收和待决项单列，均未改写成通过。

除明确写出的主 checkout/外置盘绝对路径外，下列输出路径均相对本目录。命令从本 worktree 根运行；真实命令是主控已经执行的记录，不是再次运行的请求。

## Acceptance 逐条结果

1. **红态在先：PASS**

   命令/来源：`git show 451be8462c85fd08b997cb85453188a8e5751c9d:workbench/src/gates/core.ts`、同修订的 `workbench/src/panes.ts`；起点静态探针输出为 `red-state/static-red.json`。历史只读证明沿用主 checkout 的 `evidence/2026-10-11-batch13/T-076/card-2/outside-p-review-02/`，只读核对其中 `run.json`、`sentinel-result.json`、`launch-before-spawn.json` 和 `fixture-artifacts.tar.gz` 中的哨兵；提取读回为 `red-state/t076-readonly-readback.json`。

   结果：起点 reviewer 请求没有完成条件充分性/2～5 变异要求，启动仍是 `read-only`，工作目录仍是审查 worktree。T-076 实际原生工具回执为 `write_attempts=1, denied=true, errno=1`；归档中的事后哨兵逐字等于事前内容。历史 launch id 为 `aae6f34a-072c-4740-9ba6-5c4452fe110e`，完整 argv 已读回。历史总报告的 `product_status=INCOMPLETE` 原样保留；仅复用该次只读拒写事实，不用旧结论证明新边界，也不计入本票新真实回合。

2. **受控入口与四种拒收：PASS（当前行为）/ INCOMPLETE（逐项先红证据）**

   命令：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-02.sh`；输出 `outside-command-02-01/`、`outside-command-02-02/`。副本复制探针命令为同目录 `OUTSIDE-COMMANDS-01.sh`，成功输出 `outside-command-04/`。

   Tracer bullet 的请求必查项、副本建立/清理、启动核对五案均 PASS：`tracer_review_copy` 验证 `T082-REQUEST-COMPLETION`、`T082-REQUEST-MUTATIONS`、`T082-REVIEW-ARGV`、`T082-COPY-CREATED`、`T082-COPY-REMOVED`；四个启动参数变异均被 `review_launch_boundary` 拒收，断言 `T082-LAUNCH-REFUSED`、`T082-LAUNCH-PAUSED`、`T082-LAUNCH-ISSUE` 通过。副本省略 `.git`，内部 symlink 按内容复制、外部 symlink 拒绝，源目录未变。全部 `real_codex_turns=0`。

   `wrong-workspace` 有真实业务红绿：02-01 中 argv 的 `-C` 被改到副本外，门禁仍返回 `ok:true`，`T082-LAUNCH-REFUSED` 失败；补上实际 argv 工作目录核对后，02-02 拒收。`readonly-argv` 在首次记录已经拒收，`network-enabled` 与 `tmp-writable` 在 02-01 未跑到；三项只有当前绿态，没有保存修前放行导致断言失败的记录。脚本/导入/夹具失败不算业务红态，不宣称满足了四种“每种先见红”。

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

7. **T-076 三性质、T-077 与地图：PASS；旧 runner 另列 INCOMPLETE**

   命令：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-07.sh`、`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-09.sh`；输出 `outside-command-07-01/t076-property-tracer/`、`outside-command-09-01/t076-properties/` 与 `outside-command-09-01/t077-review-lifecycle/`。runner 的 `--source` 均指本 worktree 候选，不用 main 代跑候选。

   - `tracer_wrong_candidate` → `TRACER-REVIEW-CANDIDATE`；
   - `tracer_reused_native` → `TRACER-REVIEW-REUSE`；
   - `tracer_writer_cannot_review` → `TRACER-WRITER-REVIEW`。

   三项性质在干净候选 0dd00d09 已通过；协议修复后同三项及 `tracer_malformed_review` 再次 PASS。T-077 套件四案均 PASS：`cleanup_after_persisted_result`、`names_and_ordinals`、`dirty_review_is_preserved_and_reported`、`changed_review_head_is_preserved_and_reported`。上述受控回归 `real_codex_turns=0`；之后新增的报告节键检查由离线红绿和真实 round-2 覆盖。

   地图命令：`python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`，收尾输出 `final-status-01/`，0 problems、0 stale living docs。

   旧质量 runner：`OUTSIDE-COMMANDS-06.sh`，输出 `outside-command-06-01/t076-quality-source-audit/`，**INCOMPLETE**，报 `Source audit failed or original acceptance assertions changed.`。D3 替换的 reviewer 断言已直接进入候选，明细见 `T076-D3-ASSERTION-MAP.md`；审计机制与 `a7f4cc3033c16d5888de50d8352da516c941f8e9` 锚点均未改。必须区分断言变更与本次实际拒收原因：审计记录当前源码 diff，但不因它非空而拒收；本次命令 4 exit 0、stdout 非空，原 acceptance 文件相对 a7f4cc30 已有差异（包括 oracle 夹具接入），触发原样生效的审计。没有证据把这次拒收直接归因为 D3 的 tracer 断言变更。锚点整体迁移由主控交上游待决，本票按主控 #40 改为直接验证上述三性质，旧 runner 不标 PASS。

   旧 launch-policy runner：`sh evidence/2026-10-15-batch15/T-082/OUTSIDE-COMMANDS-08.sh` 只读在 main 原样运行，输出 `outside-command-08-01/t076-launch-policy-main/`，**INCOMPLETE**。与候选一样报 `Fixture error is not contract evidence: worker-missing-override-red`：real-delivery-01 旧快照 taskCards.ts 不接受当前夹具的 `oracle_paths`，在 `card_save` 阶段 `invalid_task_card`，未到预期业务红态。主控 #43 已确认是基线既有、与本票无关；本票不修改旧快照或绕过校验。

## 未完成与待决项

- **INCOMPLETE，Acceptance 2 证据缺口**：readonly-argv、network-enabled、tmp-writable 未保存逐项修前业务失败；当前四项拒收全 PASS。未用夹具失败或修后绿态替代先红要求，需主控/独立审查核对后决定补证安排。
- **INCOMPLETE，独立审查**：本次为 worker 收尾，主控冻结后另安排独立审查；本报告不是独立验收或集成授权。
- **待决，旧 T-076 审计基线**：是否整体迁移 a7f4cc30 锚点由上游决定；本票未改审计、未改锚点。旧 launch-policy 夹具错误为 main 已有问题，保留记录，未扩大范围修复。
- 第 1 回合的协议失败、初次隔离 home 拒收、第二次未释放提示以及各次 outside 失败现场都保留。第 2 回合正常全路径通过没有把这些历史失败改成成功。删除后的审查哨兵没有直接 after 值，间接证明及范围已注明。

## 可冻结范围

产品/测试已在 `7f2bd40611e920cb962ba20f17b58bb12a9acab0`；本次新增提交仅需本目录内的 `RESULTS.md`、`T076-D3-ASSERTION-MAP.md`、`ROUND2-READY.md`、`REAL-BOUNDARY-READBACK-01.md`、`red-state/t076-readonly-readback.json`、`real-approvals/round-2.approved`、`real-codex-round-2/`、`final-status-01/`。round-2 为 48 个文件、1,213,814 字节，无单文件超过 5 MB。

`real-codex-round-1/` 与 `real-codex-round-1-02/` 两次失败现场已纳入前一检查点的可提交证据范围；细目见 `failed-run-scope-readback.json`。auth 副本、隔离 home 和外置完整原生转录不入 Git。证据保留本机路径；凭据字段扫描只是有限检查，不作全面隐私保证。收尾校验记录见 `final-status-01/closeout.json`。
