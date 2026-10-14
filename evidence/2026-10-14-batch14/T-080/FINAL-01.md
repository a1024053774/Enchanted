# T-080 FINAL-01 交接（2026-10-14）

状态：INCOMPLETE。实现和全量运行脚本已准备；临时 records 的 schema 格式契约已取得红态与绿态，门禁沙箱外绿态、去检查变异体、完整回归和提交尚未运行。`red-01`、`red-02` 与 `history-format-blocker-01.json` 原样保留；格式决定前的交接稿保存在 `FINAL-01-before-score-schema.md`。

红态 PASS：主控 #138 运行 `red-02`，且本 worker 读回 `receipt.json`、`hole-observation.json` 和 `git-readback.json`。候选 `4f2649abc191193d660a0203c4e35ee47b19fffc` 只改 `acceptance/criterion.py`，产品仍为 `base\n`，原始独立断言退出 1；门禁仍 verified、integrated，夹具 main 指向候选。

实现：

- `taskCards.ts` 的接口、模板和严格字段校验增加必填、非空 `oracle_paths`；只允许确切文件或目录前缀，拒绝非法路径及与红态测试的交集。未增加旧卡格式的兼容路径。
- `core.ts` 在认领时查当前起点 Git tree，缺失项以 `oracle_not_found` 拒收，尚未创建 attempt/worktree。路径边界通过后、完成条件执行前检查冻结起点到候选以及 G→M；冲突整理仍使用原认领起点保护验收文件。有改动写 `oracle_check` 与 `oracle_modified`，列出路径，走现有原 worker 反馈和三次上限，打分单列 `oracle`。
- Markdown task-card 模板只增加验收文件行。更新现有任务卡夹具、字段集合和打分预期；接受已有文件的声明，不新建生产兼容入口。旧分页验收只迁移 `setUp`/`create` 夹具，测试方法和独立业务逻辑未改；回归运行器用 AST 核对除这两处夹具以外的完整原验收逻辑。
- 新套件 `test_protected_acceptance_e2e.py` 经真实 CLI/daemon/relay/Git/SQLite 检查 12 个场景：原场景篡改、目录新增、删除、重命名、正确交付与相邻目录、修复后计分、三次上限、字段/路径/红态交集、起点不存在、认领时新基线、检查顺序和卡片快照。
- 按主控 #144/#145 授权同步 `qualityProtocol.ts`、`scripts/score` 和 README。两个读取器按每行 schema 校验：v1 严格使用原七项检查集，v2 评分事实必须含 `oracle` 等八项，未知版本拒收。后台 `score_recorded` 与 `scripts/score` 的新行只写 schema=2；用户分可关联 v1/v2 原记录。launch/review 的 schema 不变，主仓历史分数不改写、不迁移、不补零，不另开日志。

schema 红态在 `schema-red-01`：未改写入端时，真实 CLI 向临时记录追加的用户分仍为 v1，`new-user-for-v1` 业务断言失败。实现后在 `schema-green-01` 和加强落盘核对的 `schema-green-02` 均 PASS：v1 执行主控/用户旧行通过且不补项，v2 缺 `oracle` 拒收、完整通过，未知 schema 拒收；真实 `scripts/score --score-of` 指向 v1/v2 都成功，并验证旧字节前缀保留、每次只追加与回执一致的一行、拒收不追加。两个格式读取器都使用同一组独立输入。所有写入只到 `/tmp` 夹具，原始现场保留。

README 已同步验收文件的必填/起点存在/拒收顺序、oracle 计分和 schema 读写边界。按 project-map 的 living docs 规则，实际编辑文档已构成核对；status 为 0 problems、0 stale，无需改地图的 Verified 单元格。此前 `final01-readiness.json` 的 stale 结果保留为当时的真实记录，不覆盖。

全量阶段（在此 worktree 的主控 shell 运行）：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/run_final01_outside.py --output evidence/2026-10-14-batch14/T-080/final-01
```

脚本保存完整候选源码及本票 Python 运行器、起点与 diff、逐条命令和原始输出，串行执行，任何失败不重试、不覆盖。格式预检要求完整 v2 记录，随后跑混合 schema 新套件与既有 CLI 打分的三项回归（通过/升级/放弃/用户分、并发/损坏记录/启动失败、缺项/未知检查项）；`scripts/score` 的写入仍只到临时 records。然后跑验收文件新套件，再在一次性副本中只删除 `oracle_modified` 的拒收检查；字段、认领、反馈、评分及测试不变。原篡改与目录新增两项都必须以 `ORACLE-MODIFIED` 业务断言失败；harness error 或其他失败不算红态。

随后跑 T-075 任务卡以及既有交付/恢复/运行/CAS，T-076 tracer、质量正反例、原交付边界、widen、审查故障、启动/停止和附着窗口，T-077 生命周期/CAS/冲突、原窗格冲突、审查 worktree、联验、relay 与提交尾注冲突。每套保存重放命令与产物，结束后核对源码仍与冻结归档相同并运行 project-map status。原始夹具保留 `/tmp`，归档进入证据，不登记 gitlink；证据单文件超过 5 MB 停止报告。无真实模型，也不运行已迁移字段的真实模型或 Electron 验证脚本。

提交另交主控，在全量阶段 PASS 后运行：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/commit_outside.py --validation evidence/2026-10-14-batch14/T-080/final-01 --output /Users/luckye/Documents/Code/a2a/evidence/2026-10-14-batch14/T-080/commit-01
```

提交脚本核对分支、冻结版本、原 worker 的启动记录和钩子；已有暂存工作则停止保留。只暂存列明的 T-080 文件与本票证据，范围已包含三个新授权文件及 schema 测试；消息不手写 `A2A-*`，钩子自动添加后再读回身份，不 push。提交后再次核对源码与冻结归档相同，并要求 worker worktree 干净。收据写到上面指定的主仓 T-080 证据目录，不写回 worker worktree；由主控收尾保存，避免自引用。失败保留暂存区、提交及证据，不 reset。

非阻塞的范围外发现见 `OUT-OF-SCOPE-01.md`：旧 T-073 启动/尾注 argv 断言与当前启动策略存在静态差异，未实跑，也未在本票修正；全量阶段仅纳入其中与新打分格式直接相关的三个方法。该记录提供由主控登记主仓收件箱的命令。

未完成证据：沙箱外门禁业务绿态、去检查变异红态、完整回归和本地提交。独立审查按 `behavioral-acceptance-review` 交主控新开干净只读 reviewer，绑定全量阶段冻结归档与最终候选，并核对主控 #145 明确要求的历史 schema 读取分支；本 worker 不充当自己的 reviewer、不启动子代理。受控 reviewer 输入只证明机械协议，不是模型审查质量的证据。
