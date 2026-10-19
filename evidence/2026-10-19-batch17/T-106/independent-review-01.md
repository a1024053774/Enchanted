# T-106 第一轮独立审查

2026-10-19。**NO_GO，需修复**：确认 1 个保存结果分类缺陷。已持久化的任务卡可能被表单标为未保存，随后仍允许“取消”和重试。普通创建流程、目录信任边界及三个变异检查通过，不抵销此缺陷。

## 审查绑定与判据

- 候选：`24cacef60f9e88103213c0bb93eecb0cb5c41cf3`，分支 `exec/t106`；审查起止 HEAD 相同，产品文件无工作区差异。
- 比较：以固定起点 `b0e12a88cdd601275595c85a4e177801dd58eb46` 执行 `git diff`，以 `git show` 阅读候选原文。审查期间本地 `main` 已指向 `37bc689fc02e4212a3f2609001869021362ff3a3`，没有拿这个移动引用代替起点。
- task `T-106`，交付 attempt `a1`。本 reviewer 未取得自己的门禁 session/fence，不推断其值；按派发只交报告，不 submit、不集成。
- 依次读取指定 reviewer 角色卡、AGENTS.md、ticket 裁定节和 RESULTS-form.md；另读取地图、CONTEXT.md、intent.md、直接调用方、门禁及测试。
- 判据来自用户逐字选择“B 简化表单,不用主控 (Recommended)”与 ticket 裁定：不用模型；项目使用既有最小语义；只走原门禁；确认前无任务；拒收原因可见；取消草稿无残余；目录归主进程；默认字段可见可改。截图不作为验收条件。
- **Tracer bullet**：核对表单 → IPC → 原门禁 → SQLite → 列表。**Deep modules**：持久化与校验仍由门禁拥有。**Ubiquitous language**：沿用项目、任务、任务卡、完成条件，不增加第二套项目概念。
- 本轮不实现、不修复、不开子 agent、不调用模型、不写全局配置、不申请升级、不用问题面板。模型根回合 0。
- 本票适用的能力检查为状态编排、异步确认、身份范围、桌面交互、JSON 文件和写库副作用；检索/记忆与生产发布为 N/A，本票不包含这些功能。CLI 模型理解也为 N/A，裁定已去掉模型调用。

## 确认的缺陷

### [P1] 保存已生效后的失败响应，被误判为未保存

位置：`workbench/app/main.ts:192`。`card_save` 只要返回 `ok:false`，就执行 `draft.persisted = false`，并向 renderer 返回 `persisted:false`。

这个判断不符合现有后台合同。`workbench/src/gates/core.ts:3300` 已提交任务卡版本事务，后台随后仍会在 `workbench/src/daemon.ts:503` 写入 `request_result`。若这个事件写入失败，daemon 的既有 catch 在 `:507` 返回 `orchestration_failed`；若拒收事件也写不下，则在 `:512` 返回 `event_write_failed`。失败响应不保证任务卡没有落库。

独立探针使用候选的实际 main、daemon、门禁、OrchestrationStore 与 SQLite。在隔离库添加一个触发器，仅拒绝 `command=card_save` 的 `request_result` 插入；不阻断任务卡事务，不替换门禁响应。Electron、PTY 和 net 监听由边界夹具提供，输入仍经过实际 daemon 的认证、请求解码和处理函数。

运行：

```sh
node --experimental-vm-modules /private/tmp/t106-review01-ak_ajsde/probe-postsave-02.mjs
```

退出 1，失败是业务断言 `persisted` 应为 true：

```json
{
  "result": {"ok": false, "error": "orchestration_failed", "stage": "card_save", "persisted": false},
  "counts": {"tasks": 0, "task_card_versions": 1, "task_card_snapshots": 0, "attempts": 0, "launch_records": 0},
  "cancelled": {"ok": true, "persisted": false}
}
```

原件：[探针结果](/private/tmp/t106-review01-ak_ajsde/results/postsave-probe-02.json)、[探针脚本](/private/tmp/t106-review01-ak_ajsde/probe-postsave-02.mjs)。夹具与源码副本均保留在该临时目录。初次探针的 net 夹具遗漏 `setEncoding`，其 `postsave-probe.json` 是设置失败，未当作产品红态；修正夹具后才得到上述结果。

实际影响由 renderer 的既有逻辑确定：`workbench/app/renderer.tsx:342` 接受这个 false，`:372` 不显示可能已保存提示，`:373` 仍显示“取消”，`:374` 再次启用确认。重试会撞到已经存在的卡版本；取消后库里仍有该版本。这不是确认前普通草稿取消的问题，而是保存已经开始后的结果被错误分类。

最小修正方向：保存开始后的泛化失败不能撤销“可能已保存”标记，应沿用现有保留记录、禁止重试的状态；不需要新增门禁命令、回滚、删库或自动重试。补充实际后台“提交后写结果失败”的检查，再核对界面显示和按钮状态。当前测试只注入保存前的 `card_version_conflict`，不足以证明所有保存失败均无写入。

## 必审项结果

| 项目 | 结论与依据 |
| --- | --- |
| 唯一创建路径 | PASS。`main.ts:153` 取 `card_template`；显式确认后在 `:185`、`:191`、`:194` 依次调用 `card_validate`、`card_save`、`create`。全部用主进程 operator 身份；临时卡文件路径由主进程生成。生产 diff 没有修改 daemon、gates、schema、校验规则或写库代码。preload 没有通用命令入口。 |
| 项目由首任务隐含 | PASS。已有 `A2AGates.listProjects()` 从 tasks 表的 project_id 投影项目，create 原本就接收 project/title/repo。沿用这个投影是现有最小方式；未新增项目表或命令。`renderer.tsx:354` 和 README“任务卡与交付”“日常启动”均说明首任务成功后项目才出现，不支持独立空项目。 |
| 确认前、格式拒收、取消 | 普通路径 PASS。主进程确认前只取模板；取消只丢弃窗口草稿。原真实 Electron 证据核对了五表零增长与可见拒收。保存开始后的故障路径 NO_GO，见 P1；不能据普通路径通过宣称所有取消均无残余。 |
| 目录信任边界 | PASS。`main.ts:140` 拒绝目录 IPC 的额外参数；主进程调用原生对话框、realpath 和 Git 根目录检查；`creation-submit` 严格核对五个字符串字段，拒绝 repo 字段，create 只取窗口内 draft.repo。三个新 handler 都经 windowTarget，拒绝未知窗口和 iframe，草稿不跨窗口共享。 |
| 命令及文本注入 | 已核实范围 PASS。新代码没有把标题、目标或完成条件拼成 shell 命令；标题作为门禁数据、目标进入 JSON，小文件名由 mkdtemp 固定生成。Git 查询使用 execFile 的 argv。原门禁 commandArgv 只解析及查找可执行文件，注册不执行完成条件。原 Electron 证据含标题/目标 sentinel 与未执行标记。更强的 shell 文本 sentinel 已列入外部复验脚本，本轮未运行该脚本。 |
| IPC 合同只增不减 | PASS。逐行检查旧合同 diff；增加三个 handler/bridge 名称，集合明确为 17/18。保留旧 key、iframe、跨窗口、凭据与序号、关闭恢复及已知坏版本断言；复跑通过。 |
| 默认值与最少输入 | 静态核对 PASS，限制如下。默认非目标、允许整个仓库、禁止 `.git/`、验收文件 tests/、M、Codex/gpt-6.1-sol/xhigh，以及 null source/base_commit/writer 均可见可改；工作分支来自当前分支且可改。paths 与验收文件的仓库适用性仍须用户判断，文案和 README 已提醒。只填名字和目标不能提交：完成条件命令为空且 required。这符合裁定节明确增加“完成条件命令”的要求，不能转述成两项输入即可完成。 |
| design-integrity-review | NO_GO。唯一确认的结构问题是 P1：main 对后台失败的翻译越过了持久化事实，制造了错误的可取消状态。其余新 catch 仍显示阶段、错误和 details；没有静默降级、重试、兼容分支、平行 API 或另建持久化层。扫描器输出 findings=[] 仅是定位结果，未用它代替代码审查。 |

## 行为证据与三个变异

所有副本通过 `git archive 24cacef60 workbench` 解包到 `/private/tmp/t106-review01-ak_ajsde/`，没有建立 worktree。先在未变异副本运行，均退出 0：

```sh
R=/private/tmp/t106-review01-ak_ajsde
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_creation.mjs" "$R/results/candidate-creation.json" "$R/candidate/workbench/app/main.ts"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t091_pane_ipc.mjs" "$R/results/candidate-pane.json" --source "$R/candidate"
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t105_panes.mjs"
```

第二条从原审查仓库 cwd 运行，只读取得旧版本供合同反例使用。前两份 JSON 保存完整检查结果；它们是 main/preload 的边界测试，不是 GUI 或实际后台证明。

每个变异只改变一个生产调用位置，运行未改动的候选创建测试：

```sh
node --experimental-vm-modules "$R/candidate/workbench/tests/test_t106_creation.mjs" "$R/results/<名称>.json" "$R/<名称>/workbench/app/main.ts"
```

| 名称 | 单处错误 | 观察到的拒绝 |
| --- | --- | --- |
| `mutant-early-save-valid` | 目录选完后、返回草稿前，额外调用 card_save。提供非空目标、非目标、路径、验收文件、可执行 argv 和执行器的完整卡，代表提前持久化。 | 退出 1，`:84` 的确认前调用检查发现末条是 card_save，期望 card_template。未以导入或设置失败冒充拒绝。 |
| `mutant-renderer-repo` | create 的 `repo: draft.repo` 改成 `repo: input.project`，把仓库来源错误地交给 renderer 字符串。 | 退出 1，所选仓库断言拒绝错误 repo，候选原本可成功的提交在 `:115` 变为 false。 |
| `mutant-silent-refusal` | card_validate 拒收时返回 `{ok:true, stage, persisted:false}`，丢掉门禁错误。 | 退出 1，`:101` 检查到 true，期望 false。 |

上述 JSON 自身沿用原测试的 `status: INCOMPLETE` 错误格式；这里依据非零退出及具体业务断言判定“变异已拒绝”，没有把该字段改成 PASS。补丁原文保存在临时目录的 `mutations.json` 与 `mutation-early-valid.json`。最初提前保存试验使用了未填完的模板，证据保留，但未拿它证明真实提前持久化；表中采用完整卡版本。

独立 oracle 不来自候选输出：允许的四条命令、确认边界、目录所有权、错误可见性来自派发和裁定。新测试的绿色仅作局部证据；另以实际门禁事务与 SQLite 的提交事实，发现了测试未覆盖的 P1。

## 真实入口与未完成部分

- 已审阅主控提供的 [form-electron-01.json](form-electron-01.json) 原件及其 runner/driver。记录绑定本候选、candidate_diff 为空、Electron 43.4.1、模型回合 0、cleanup_complete=true。真实空库、两次用户原生目录选择、确认/格式拒收/取消、五表计数、列表和 CLI 对照均为 PASS。任务卡预期来自外部输入，另核对保存的整条任务和快照，只排除随机 snapshot UUID；不是只比 UI 与 CLI 同时返回成功。本 reviewer 未亲自观察此前 GUI 运行。
- 原真实 runner 主动填写了其余任务卡字段，未单独证明“保持整份默认卡不改”的 GUI 成功。默认值已静态核对；外部补测同时观察默认卡、缺命令时的表单状态和上述提交后故障。
- [REVIEW-OUTSIDE-01.sh](REVIEW-OUTSIDE-01.sh) 已准备，`bash -n`、内嵌 Python 3.9 语法/编译、UTF-8 回读通过；**本轮未执行**。运行命令：`bash evidence/2026-10-19-batch17/T-106/REVIEW-OUTSIDE-01.sh`。脚本固定 archive 本候选，启动隔离真实 Electron/daemon/SQLite，注入同一个提交后故障，保存新的 `/private/tmp/t106-review-outside01-*/summary.json`；当前候选预期输出 NO_GO 并退出 1。为避免重复人手操作，仅观察 driver 固定主进程 dialog 返回值，不伪称新的原生对话框证明。无截图、无模型、无全局配置写入。确认自有进程退出后清理依赖和构建，保留失败现场。
- `project_map.py status --root .` 起止均退出 1：8 个稀疏 checkout 缺文件/断链诊断，stale living docs 0。“0 问题”在本 checkout 为 INCOMPLETE，没有改地图或把这些诊断消掉。
- `git diff --check` 通过。只新增本报告和指定复验脚本；主控已有未跟踪的 form-electron-01.json 原件保持原样；未 commit、checkout、reset、stash 或 push。

这是对固定候选的一次审查。修复 P1 后需要针对保存结果分类及按钮状态重新取得证据；旧健康路径 PASS 不能替代修复后的证明。

T-106 REVIEW NO_GO
