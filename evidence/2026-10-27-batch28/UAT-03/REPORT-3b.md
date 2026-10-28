NO_GO：`clear` 修复经交付、验收、审查和集成后通过实际测试，但审查员在限定目录外写入临时文件；人工介入后交付也一度停在已认领，需再次让 worker 提交才能继续。部分产品声明尚未验证。

## 产品页声明逐条检查

| 声明 | 结果与证据 |
| --- | --- |
| 四种官方 CLI 在交互终端运行，均可当主控、worker、审查员 | 部分能用：本轮 Claude Code 成功作为项目终端执行主控、worker 和审查员，模型为 `claude-haiku-5-5`；其他三种及其角色组合本轮未验证。`03-claude-start.png`、`25-project-review.png`、`32-metrics-model.png`。3a 的 OpenCode 要求连接，按边界未登录，见 3a 报告。 |
| 侧栏 agent 树、分支、领先落后数、折叠汇总 | 部分能用：执行主控下有 worker、审查员；折叠后显示 `子会话 2 · 运行中 1 · 空闲 1`。分支显示 `main · 无上游`，切到集成分支后显示 `enchanted/todo-cli · 无上游`；无上游，未验证领先/落后数字，也未创建构思主控或监视器。`25-project-review.png`、`26-collapsed-tree.png`、`31-integration-tests.png`。 |
| 项目视图每张票一格，显示门禁状态和 agent | 能用：T-1 一格显示 `reviewing` 和 `2 个 agent`，集成后显示已集成。本轮只有一张票。`25-project-review.png`。 |
| 任务页窗格、门禁记录、无窗格详情、打开 worker、普通终端和右键操作 | 部分能用：任务页窗格在上、门禁在下；右键向右分出普通终端并放大，普通终端输入未新增介入；关闭审查窗格后可见任务卡、时间线及“打开 worker 会话”按钮。未逐项核对无窗格页的审查报告、打分和集成提交展示。`13-task-worker.png`、`17-context-menu.png`、`18-split-shell.png`、`19-maximized.png`、`20-shell-record.png`、`29-task-no-pane.png`。审查中状态显示有问题，见问题 3。 |
| 主控申请、批准、身份跟随终端 | 部分能用：自然语言要求后 Claude 申请执行主控，批准后侧栏显示执行主控。3a 终端结束后本轮需重新申请；本轮没有再次关闭运行中的主控验证身份结束。`04-request.png`、`05-approved.png`、`06-controller.png`。 |
| 原生提问、侧栏标黄、右上通知、界面作答写回并记录 | 部分能用：侧栏出现黄色 `1 个等你`；在原终端的原生选项界面选择并提交，终端显示答复，记录页出现完整答复。未观察到右上通知，且未验证独立面板点选作答，不能断言通知不存在。`08-question.png`、`09-answer-record.png`。 |
| 流程泳道、回线、展开收起 | 部分能用：T-1 有一条泳道，显示认领、交付、机械检查、独立审查、集成阶段；标题可收起。没有产生可验证的打回回线。`21-flow.png`、`22-flow-collapsed.png`。 |
| 问题页上报、答复、阻塞卡关闭 | 部分能用：页面可打开，说明范围外问题和阻塞权限；本轮没有问题卡，未验证答复或关闭。审查越界由主控记在打分备注，未作为问题卡上报。 |
| 记录页记录输入、答复、审批，worker 介入和任务筛选 | 能用：批准和答复有记录；对 worker 输入 `Please check mixed itemx`，退格改成 `Please check mixed items`，按左右方向键、回车及 Esc 后，记录只增加一条完整消息，Esc 没有单独成行；按 T-1 筛选只显示该条。随后“输入框已空，放行”另记为一次操作，普通终端的 `echo ordinary-terminal-check` 未记为介入。`09-answer-record.png`、`14-intervention.png`、`15-filtered-intervention.png`、`20-shell-record.png`。 |
| 指标页模型使用、一次到位率、打回原因、注意力和打分、unknown | 能用：项目主控模型为 `unknown`，页面解释未接入计数来源；worker 和审查员显示模型及回合数；集成 1 个、一次到位 0%，注意力显示介入 2、叫停 1，打分 3/3。unknown 与未覆盖的解释可理解；未独立重算所有指标。`10-metrics-unknown.png`、`32-metrics-model.png`、`33-metrics-score.png`。 |
| 回看主控、会话、worker 打分和建议批准 | 部分能用：列出历史及当前主控、worker、审查员和 worker 的结果与分数；无建议可批准或不采纳，也未启动复盘。`34-reflect-score.png`。 |
| 按角色设置模型、强度、Fast，影响新会话；浅深色 | 部分能用：Worker 设置为 `claude-haiku-5-5`、`high`、Fast 关闭并显示 `已保存，下次启动生效`；深色、浅色均可切换。本次主控显式在任务卡及调用中指定 `medium`，worker 实际为 medium，因此不能证明默认设置在新会话生效，也未验证旧会话不受影响。`07-settings-dark.png`、`32-metrics-model.png`。 |
| 交付门禁核对 worktree HEAD、分支、Git 配置和钩子 | 没试：本轮没有对这些对象作受控篡改，不能从正常交付推断各项篡改均会被拒绝。 |
| 全部检查通过才集成工作分支，不 push | 部分能用：本次交付后路径、验收文件、完成条件、红态与独立审查通过，集成到 `enchanted/todo-cli`，未 push；没有制造检查失败后试图集成，因此未验证“只有全部通过才集成”的否定路径。`29-task-no-pane.png`、`30-integrated.png`、`31-integration-tests.png`。 |

## 问题清单

### 1. 审查员在限定目录外写临时文件（严重；本轮边界未满足）

- 复现：在任务要求所有写入限于 `/private/tmp/uat3/` 后，派发 Claude worker 并进入独立审查；打开审查员会话，观察其变异测试命令。
- 期望：审查执行及临时文件写入遵守指定范围，或在不能保证时给出可操作的阻挡。
- 实际：审查会话命令显示 `SP=/private/tmp/claude-501/.../scratchpad`，随后 `mkdir -p "$SP"`、`cp todo.py "$SP/todo.py.candidate"`。完整路径可在截图中辨认；该路径位于限定目录外。回看备注亦记录审查报告使用 scratchpad。关闭审查窗格后会话很快结束，不能确认关闭窗格是否终止了进程。主控随后表示不删除外部文件；未独立清理或核验外部残留。不能断言产品本身支持强制执行用户用自然语言提出的路径限制，但本轮严格边界已被打破。
- 截图：`28-review-outside-boundary.png`、`34-reflect-score.png`。

### 2. 人工输入后放行，已排队的交付未自动进入门禁（严重；触发机制未确定）

- 复现：worker 工作时输入并发送一条消息，紧接着按 Esc；worker 完成并请求交付后，任务页出现 `输入框已空，放行`，确认输入框空并点击；等待并让主控查询状态。
- 期望：用户确认放行后，已排队交付能继续处理，或者界面清楚说明恢复交付的下一步。
- 实际：worker 显示 `queued=true, delivered=false`；点击放行后仍是 `已认领`、`尚未交付`，主控查询显示队列为空、状态 `claimed`，verify 返回 `not_submitted`。再次向同一 worker 请求交付已有提交后，门禁才显示 `已交付`。不能确定是 Esc、排队消息、Stop hook 或其他原因；没有独立复现第二次。
- 截图：`16-input-hold.png`、`23-delivery-stalled.png`、`24-delivered.png`。

### 3. 审查中任务页的门禁状态显示“未知”（一般）

- 复现：T-1 完成验收，审查员正在运行时打开其任务窗格。
- 期望：门禁状态与任务当前审查阶段一致，或说明未知的具体对象。
- 实际：任务标签和门禁记录均为 `reviewing`，底部却显示 `门禁 未知`；旁边验收显示 `passed`。用户难以判断门禁本身是否出了问题。
- 截图：`27-review-gate-unknown.png`。

## 交付验证与限制

- T-1 修复 README 的 `clear` 条件，候选 `300ca37` 集成到 `enchanted/todo-cli`。在应用内普通终端执行 `git switch enchanted/todo-cli && git --no-pager log -1 --oneline && python3 -m unittest -v test_todo && python3 /private/tmp/uat3/a2a/check_clear.py`，显示 `Ran 2 tests`、`OK` 和 `PASS clear keeps only unfinished items`。截图 `31-integration-tests.png`。项目工作目录现在停在该集成分支；main 未改、未 push。
- 主控报告验收脚本在未修复基线上失败，在候选上通过；门禁时间线显示红态基线退出 1、候选退出 0。独立审查报告“可合并”，本次没有复现前轮 JSON 协议错误；未单独核对 `review_submit` 工具调用的完整原始记录。
- 两个指定项目已存在并来回切换；未操作先前误加入的 landing-page。由于审查过程发生目录外写入，未继续启动额外 CLI、复盘或第二次 worker 来验证默认设置，避免再次越界。没有问题卡和复盘建议可操作；未测试人工篡改门禁、领先/落后数、右上通知、其他 CLI 角色矩阵或未批准派发。不能把未试视为通过。
- 保存了本轮编号 03 起的截图；01、02 是用户叫停前的 3b 证据，3a 保留在 `/private/tmp/uat3/ui-check/`。未修改系统设置、登录或接受系统隐私授权；未删除越界文件。Worker 默认设置现为 `claude-haiku-5-5` / `high` / Fast 关闭，外观浅色。
