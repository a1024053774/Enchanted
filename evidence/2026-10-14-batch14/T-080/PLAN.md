# T-080 执行计划（2026-10-14）

状态：INCOMPLETE。计划与首个主控运行脚本已准备；红态尚未运行，产品代码尚未修改。

目标：任务卡必填 `oracle_paths`，认领核对起点存在性，候选改到验收文件即以 `oracle_modified` 拒收；沿用回写、三次打回上限和 attempt 绑定，打分单列 `rejections.oracle`。

范围：独占 `workbench/src/gates/taskCards.ts`、`core.ts`，更新相关测试及 `.project-map/templates/task-card.md`。不改 `cli.ts`、`panes.ts`、`daemon.ts`、`app/`、角色卡、地图或术语表。若必须改 `cli.ts`，先停下报告。沙箱外运行和提交均交主控脚本；不调用真实模型、不启动子代理、不 push。

失败方式清单：

1. 缺字段、空数组、错误类型、`.`、绝对路径、通配符、`..`、`.git` 等非法路径被误收；目录前缀误匹配相邻目录；与红态测试重叠未被识别。
2. 验收文件在认领起点不存在，或目录下没有受控文件，却创建了 attempt/worktree；错误地按工作区或候选判断存在性。
3. 候选修改、删除、重命名验收文件，或在受保护目录下新增文件，仍执行完成条件并通过；路径边界先后顺序不正确。
4. 拒收未保存具体路径，未回写原 worker，未计入三次上限，或误计 `path_boundary`；拒收后工作分支、集成记录发生变化。
5. 正确交付误拒；重交、冲突整理、CAS 重验或新 attempt 绕过检查；卡片快照或 fence 绑定被破坏。
6. 变异体只因夹具、导入、schema 或基础设施故障失败，无法证明业务拒收断言有效；旧夹具留兼容路径而掩盖必填字段。

红态：固定当前 `main@87e954a2f4059d471e3e240872b565217e29b0b5`（与指定起点 `cdf8fe9b0eebfacf9f8d2ffeff3aecebf1e6eb37` 的门禁和所用夹具相同）。隔离仓库在起点预置 `acceptance/criterion.py`，断言 `src/value.txt` 为 `worker\n`，实际仍为 `base\n`；先直接运行证明断言会失败。任务卡 `allow: ["."]`、deny 空；候选只把该测试改成恒过，不修产品。真实 CLI → daemon → relay → 门禁 → Git/SQLite，受控 PTY、进程和原生输入，明确合成 reviewer 结论。记录门禁验证通过及带打分的集成、原始事件、工作分支引用和候选差异，再以独立业务断言 `ORACLE-MODIFIED` 报红。旧 schema 不支持新字段，声明的验收文件另存输入证据，不向产品提供兼容路径。

采用 **Tracer bullet**：红态成立后，先打通“卡片 → 认领 → 候选拒收 → 原窗格反馈 → 打分事实”一条生产路径，再扩展反例。按 **Deep modules** 在现有任务卡与门禁层直接处理，不另建入口或包装层；按 **Ubiquitous language** 统一使用“验收文件”。

实施与回归：

- 新检查前取红态；收到主控结果后实现必填字段、路径/红态交集校验、认领存在性、完成条件前拒收、oracle 分类，模板只加本字段行。
- 同场景修复后断言 `oracle_modified`、具体路径事件、原窗格反馈、无完成条件执行及无集成；补正确交付、无效字段、起点不存在、目录新增、删除/重命名、三次上限和修复后打分的正反例。
- 一次性产品副本去掉候选验收文件检查，保留 schema/认领/反馈/评分逻辑；同一拒收测试必须以 `ORACLE-MODIFIED` 业务断言失败，不能把 harness error 算红态。
- 更新现有任务卡夹具及评分预期，不保留旧格式兼容。回归 T-075 任务卡/daemon 卡套件；T-076 tracer、质量 red/control/widen/legacy/recovery 套件；T-077 worktree 生命周期、CAS 重验、冲突、review worktree、relay/conflict trailer 套件。按现有入口串行运行，保留每套成员、退出码和产物；具体重放命令随下一份沙箱外脚本给出。
- 最后保存 diff、所跑检查、未知与跳过项，重新运行 project-map status；提交脚本交主控，提交说明不手写 `A2A-*`。

证据：全部运行输出在本目录，每次新建标签，隔离原始仓库留在 `/tmp` 并归档，避免顶层 gitlink。脚本检查单文件 5 MB 上限，超限停止并报告，不删除现场。当前仅做过读取、Node 版本和状态核对；socket、Git 元数据写入、红态与回归尚未运行。外置盘挂载与受控 daemon 可用性由主控运行时核对。

首个脚本：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/run_red_outside.py --output evidence/2026-10-14-batch14/T-080/red-01
```

运行成功表示“缺口已复现”，不代表 T-080 产品通过。主控检查 `receipt.json` 的 `status: PASS`、`product_status: INCOMPLETE`，以及 `cases/run.json` 的 `contract_failure` / `ORACLE-MODIFIED`；基础设施失败必须保留原样返回，不能当作红态。
