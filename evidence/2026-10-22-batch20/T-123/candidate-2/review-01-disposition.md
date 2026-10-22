# T-123 审查 01（agy）发现的处置

审查：`../candidate-1/review-01.md`。审查对象：提交 `f0188d772`（候选 1）。审查结论：INCOMPLETE。处置人：执行主控，逐条对照代码核实后处理。候选 2 的证据见本目录 `RESULTS.md`。

| # | 发现 | 核实 | 处置 |
| --- | --- | --- | --- |
| 1 | P1 `contracts/a2aMembership.ts` 的 `taskId` 仍按旧字符集 | 属实。运行时没有任何地方用它解码，目前不会触发失败；但已发布的契约写的是旧格式。 | 修复：`taskIdPattern` 移到 `contracts/a2aMembership.ts`，契约、门禁、中继、审查协议共用同一条。 |
| 2 | P1 两个库分开提交，中途中断后成员资格永久留旧 id | 属实：任务库提交后，`renamed` 只从任务库与卡片构建，下次启动为空即返回。 | 修复：成员资格里没有 `+` 的 id 也进入改名集合，项目取该行自己的 `projectId`。新增 `tests/test_t123_migration_resume.ts`，直接构造中断后的库；去掉修复的变异失败在 `interrupted_migration_finished_on_next_start`。 |
| 3 | P2 `relay_requests.input` 的 JSON 没有改写 | 属实。逐表核对真实库的列：`data`、`details` 之外只有这一列存 JSON。 | 修复：`input` 列纳入 JSON 改写；单元测试覆盖，去掉修复的变异失败。 |
| 4 | P2 CLI 不接受 `--project`，README 却写了“管理凭据用 `--project` 指明项目” | 属实：只有 `card_template`、`create` 允许。 | 修复：所有带 task 的命令都允许 `--project`。端到端 `cli_bare_name_with_project` 经真实 CLI 验证；变异 `cli-refuses-project` 失败。 |
| 5 | P2 `workbench_snapshot` 用原始裸名与 launch 比较 | 属实：裸名经门禁解析为完整 id，launch 记录是完整 id，比较误拒。 | 修复：改为与解析后的 `task_id` 比较。端到端 `snapshot_by_bare_name`；变异 `snapshot-raw-name` 失败。`pane_layout` 的布局键仍按调用者给的 task 字符串：界面只传完整 id，未改。 |
| 6 | P2 迁移没有删除 `card_draft_owned` 事件；`no_draft_ownership_records` 是假阳性 | 前半句：ticket 计划原文“之后删除 `card_draft_owned`”有歧义，但验收要求迁移前后事件条数一致，项目规则要求运行记录追加写入，所以删除的是机制，不删历史事件；已改清计划原文。后半句属实：旧库里没有终端保存的草稿，草稿迁移路径没被测到。 | 修复测试：修前版本的终端保存一个未建任务的草稿 `T-D`，先核对旧库确有一条 `card_draft_owned`；迁移后草稿归入 `legacy+T-D` 且可读，历史事件原样保留；最后核对没有新写入。变异 `migration-ignores-drafts` 失败。 |
| 7 | P3 `locks/` 下旧锁文件不清理 | 属实，但是有意的：门禁的操作锁“保留 inode，从不 unlink”（`core.ts` 操作锁处的注释），删除锁文件会破坏这一不变量；旧文件不再被引用，不影响互斥。 | 不改。 |
