# T-080 FINAL-01 交接（2026-10-14）

状态：INCOMPLETE。实现和运行脚本已准备；本 worker 未运行沙箱外绿态、变异体、回归或提交。`red-01` 与 `red-02` 原样保留。

红态 PASS：主控 #138 运行 `red-02`，且本 worker 读回 `receipt.json`、`hole-observation.json` 和 `git-readback.json`。候选 `4f2649abc191193d660a0203c4e35ee47b19fffc` 只改 `acceptance/criterion.py`，产品仍为 `base\n`，原始独立断言退出 1；门禁仍 verified、integrated，夹具 main 指向候选。

实现：

- `taskCards.ts` 的接口、模板和严格字段校验增加必填、非空 `oracle_paths`；只允许确切文件或目录前缀，拒绝非法路径及与红态测试的交集。未增加旧卡格式的兼容路径。
- `core.ts` 在认领时查当前起点 Git tree，缺失项以 `oracle_not_found` 拒收，尚未创建 attempt/worktree。路径边界通过后、完成条件执行前检查冻结起点到候选以及 G→M；冲突整理仍使用原认领起点保护验收文件。有改动写 `oracle_check` 与 `oracle_modified`，列出路径，走现有原 worker 反馈和三次上限，打分单列 `oracle`。
- Markdown task-card 模板只增加验收文件行。更新现有任务卡夹具、字段集合和打分预期；接受已有文件的声明，不新建生产兼容入口。旧分页验收只迁移 `setUp`/`create` 夹具，测试方法和独立业务逻辑未改；回归运行器用 AST 核对除这两处夹具以外的完整原验收逻辑。
- 新套件 `test_protected_acceptance_e2e.py` 经真实 CLI/daemon/relay/Git/SQLite 检查 12 个场景：原场景篡改、目录新增、删除、重命名、正确交付与相邻目录、修复后计分、三次上限、字段/路径/红态交集、起点不存在、认领时新基线、检查顺序和卡片快照。

主控需先处理的依赖：本 worker 明确没有修改 `workbench/src/gates/qualityProtocol.ts` 与 `scripts/score`（主控答复“暂不授权，交主控处理”）。前者 `scoreRecords` 的严格 `checks` 集合、后者 `CHECKS` 及其错误/帮助文本需要同步新增 `oracle`；否则新打分记录无法通过 T-076 双向格式校验。全量脚本会以真实格式输入做只读预检查，不通过则停止并保存两个校验器的原始输出，不自动修补。旧历史分数的格式处置亦由主控负责，本 worker 不做兼容或迁移。

结束前 project-map status 为 0 problems、1 stale：`workbench/README.md` 的 covers 包含改动的门禁源码，而本票未获该共享文档的写入分配。主控需同步任务卡必填验收文件、认领存在性、拒收顺序和 oracle 打分说明，再运行全量阶段；本 worker 不改 README 或地图的 verified 字段。该缺口已上报，不把状态检查写成 PASS。语法、纯任务卡校验与 diff 检查已通过，见 `local-final01-checks-02.json` 和 `final01-readiness.json`，均不代表业务绿态。

全量阶段（在此 worktree 的主控 shell 运行）：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/run_final01_outside.py --output evidence/2026-10-14-batch14/T-080/final-01
```

脚本保存完整候选源码归档、起点与 diff、逐条命令和原始输出，串行执行，任何失败不重试、不覆盖。先跑新套件，再在一次性副本中只删除 `oracle_modified` 的拒收检查；字段、认领、反馈、评分及测试不变。原篡改与目录新增两项都必须以 `ORACLE-MODIFIED` 业务断言失败；harness error 或其他失败不算红态。

随后跑 T-075 任务卡以及既有交付/恢复/运行/CAS，T-076 tracer、质量正反例、原交付边界、widen、审查故障、启动/停止和附着窗口，T-077 生命周期/CAS/冲突、原窗格冲突、审查 worktree、联验、relay 与提交尾注冲突。每套保存重放命令与产物，结束后核对源码仍与冻结归档相同并运行 project-map status。原始夹具保留 `/tmp`，归档进入证据，不登记 gitlink；证据单文件超过 5 MB 停止报告。无真实模型，也不运行已迁移字段的真实模型或 Electron 验证脚本。

提交另交主控，在全量阶段 PASS 后运行：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/commit_outside.py --validation evidence/2026-10-14-batch14/T-080/final-01 --output evidence/2026-10-14-batch14/T-080/commit-01
```

提交脚本核对分支、冻结版本、原 worker 的启动记录和钩子；已有暂存工作则停止保留。只暂存列明的 T-080 文件与本票证据；消息不手写 `A2A-*`，钩子自动添加后再读回身份，不 push。失败保留暂存区、提交及证据，不 reset。提交读回收据在提交后生成，需由主控的收尾记录保存，避免自引用。

未完成证据：沙箱外业务绿态、变异红态、全部回归、共享格式同步和本地提交。独立审查按 `behavioral-acceptance-review` 交主控新开干净只读 reviewer，绑定全量阶段冻结归档与最终候选；本 worker 不充当自己的 reviewer、不启动子代理。受控 reviewer 输入只证明机械协议，不是模型审查质量的证据。
