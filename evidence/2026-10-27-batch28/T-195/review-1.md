# T-195 独立只读审查（第 1 轮）

## STATUS

**NO_GO**。独立探针复现了 3 类错误链接问题，共 6 个失败用例。不能以现有首次启动测试的通过结论验收本候选。

审查对象：`/private/tmp/t195-cand`，基线提交 `28b7136a7941ce1113378526a43449bc9a0d45da`（提交说明：`base: HEAD 6b6be4f01 + T-193.diff`）上的冻结 T-195 工作区改动，以该目录的 `T-195.diff` 为范围。结束时逐文件应用补丁到基线内容并比较实际字节，10 个文件全部吻合，见 [candidate-check.json](candidate-check.json)。未修改候选、原仓库、ticket 或既有证据，未提交。

验收依据为 T-195 ticket、T-189 第 4 条及本轮 brief：复制文本包含 CLI 名、真实原生会话 ID 和对应记录路径；不能确定当前原生会话时置灰并给出原因。沿用项目的 **Ubiquitous language**，区分启动记录、agent 会话和原生会话，不把启动记录身份当成 CLI 身份。本轮只审这些行为及其直接调用链，不审 T-193，也不实现修复。

## FINDINGS

### F1 · P1 · 会话发生变化后，仍把启动时或旧角色申请的 ID 当成当前会话

位置：[`workbench/src/nativeLink.ts:24`](../t195-cand/workbench/src/nativeLink.ts#L24)，尤其第 24–36 行。

终端分支读取最后一条 `role_requested`，没有投影其后的 `role_request_ended`，随后在第 32–36 行直接返回旧记录，甚至不再检查最新 OSC 报告。受管 Claude Code 使用不变的 `record.native_session`；Codex 使用最后一次 `pane_native_session`，不检查此后是否出现了无法重新绑定的新线程。

独立反例见 [probe-01.json](probe-01.json) 的以下用例：

- `shell_claude_released_then_opencode`、`shell_codex_released_then_opencode`：先批准主控角色，再写入 `role_request_ended(reason=released)`，随后同一终端的 opencode 报出新 ID，且该 ID 确实存在于夹具数据库。两次调用仍返回旧 Claude Code/Codex 的 ID、路径及 `available:true`，连 CLI 名都错了。
- `claude_after_clear_new_hook`：夹具中存在旧、新两份原生记录，并有新 ID 的 hook；返回的仍是启动时旧 ID。
- `codex_new_thread_without_rebinding`：同工作区出现新线程记录而没有完成新绑定时，仍返回旧线程的可用链接。这里应至少禁用，不能假装当前线程已经确定。

前两例所需的角色结束事件由实际 `role_release` 路径写入（`daemon.ts:303`），属于产品可达状态。Claude 的 hook 也在校验之前就写入 `hook_received`（`panes.ts:1639`）；Codex 扫描器对不同 ID 抛出 `ambiguous_native_session`（`panes.ts:1227`），而新的查询路径没有利用这些失效或不确定信息。后两例为会话切换后的持久化状态探针，本轮没有操作真实 CLI 的 `/clear` 或新线程命令。

影响：用户复制到可打开、但属于上一次原生会话的记录；“文件存在”无法发现这一错误。`README.md:322` 所说的“已批准角色申请里的会话号”也不足以描述代码，因为代码使用的是最后一次申请及历史归档来源，而非当前有效角色。

修复方向：在会话身份的现有拥有层明确当前绑定及其失效条件；终端读取当前角色生命周期，CLI 切换和原生会话变化后撤销旧绑定。查询仅在当前身份与原生记录能对应时返回可用；尚未重新绑定时给出原因并置灰。不要在复制功能里再增加一套猜测规则。修复后用同一终端完成“批准 → 释放 → 换 CLI”和真实 `/clear`、新线程操作，核对剪贴板与 CLI 记录。

### F2 · P1 · opencode 在同一终端重新启动时继承上一实例的 ID

位置：[`workbench/src/nativeLink.ts:90`](../t195-cand/workbench/src/nativeLink.ts#L90)，关联第 83–93、40–46 行。

`lastReport()` 从整个 `pty.raw` 开始扫描，只要 `app` 相同，无 ID 的报告就继承先前的 ID。终端中第二次启动 opencode 时，新的 CLI 实例和旧实例都报告 `app=opencode`。实测结论文件明确指出开局最早两条报告没有 ID，所以仅凭同一 `app` 不能证明仍是同一原生会话。

反例 `opencode_restarted_before_new_id`：历史报告带 `ses_previous_instance`，库中有该会话；随后记录第二次启动以及新实例的不带 ID 报告。结果仍为 `available:true`，复制的 ID 为 `ses_previous_instance`。对应的首轮正例 `opencode_initial_record` 通过，说明失败来自跨实例继承，不是数据库或夹具未准备好。

影响：新实例尚未上报 ID 的窗口里，菜单能复制上一实例的链接，与“还没报来时置灰”的说明相反。

修复方向：把 ID 保留限定在同一 CLI 实例或已确认的原生会话内；实例边界或新会话身份不明时清空绑定并禁用。若现有信号无法区分实例，应说明不确定性，不能仅凭同名 app 沿用旧 ID。复验需包含同一终端连续启动两次 opencode，以及第二次首次带 ID 报告前、后的两个状态。

### F3 · P1 · agy 将读取失败当作“不匹配”，会从多匹配中错误选出一个会话

位置：[`workbench/src/nativeLink.ts:75`](../t195-cand/workbench/src/nativeLink.ts#L75)，关联第 53–65 行。

`withDatabase()` 的裸 `catch` 把锁冲突、权限、格式及 SQL 错误都变成 `undefined`。agy 的过滤器随后把它当成不匹配文件排除。这样，“没有读懂第二份记录”就变成了“只有第一份匹配记录”。这是本候选新增的吞异常路径，直接破坏唯一匹配判据。

反例使用实际 Node SQLite 和两份实际 SQLite 夹具库，两个库的元数据都指向同一工作目录：

1. `agy_two_matching_records`：两个库均可读取，正确禁用，原因显示有 2 个会话。
2. 保持两个库及内容不变，只在第二个库上持有 `BEGIN EXCLUSIVE`。
3. `agy_two_matching_records_one_locked`：查询错误被吞掉，返回第一个库的会话 ID 和 `available:true`。锁由探针结束时回滚；候选未改动。

影响：当前会话的库暂时被占用时，历史会话可能被误选；菜单无法向用户说明真正的读取故障。同一 helper 在 opencode 分支还会把读取或 schema 故障误报为“库里没有会话”。

修复方向：区分“查询成功且不匹配”与“无法检查”。只要有待检查库无法读取，就不能宣称唯一匹配，应禁用并说明未完成检查的原因。由 `nativeLink` 负责把读取错误转成不可用结果，保留必要诊断；不需要增加重试或后备选择路径。用上述双库加锁反例复验，再覆盖格式损坏或表结构不符的情况。

## EVIDENCE

### 独立探针与结果

所有新增夹具、输出和构建产物均位于本审查目录，且只包含合成记录，没有复制用户真实会话内容。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 直接调用冻结的 `nativeLink()`，使用真实 `TrajectoryArchive` 解析器与 SQLite | 19 项中 13 PASS、6 FAIL；退出码 1 | [探针源码](probe-native-link.mjs)、[原始输出](probe-01.json)、[stderr](probe-01.stderr) |
| 真实后台启动，经 Unix socket 调用 `native_link`，再正常停止 | PASS；启动、停止均退出 0 | [脚本](probe-socket.py)、[原始结果](socket-01.json) |
| 标准 renderer/main/preload 构建 | PASS；退出码 0；有超过 500 kB 的 chunk 提示 | [命令与环境](build-01.json)、[stdout](build-01.stdout)、[stderr](build-01.stderr) |
| 候选与冻结补丁一致性 | 10/10 吻合 | [candidate-check.json](candidate-check.json) |
| project-map 状态检查（开始及结束） | 两次退出 0：Problems 0、Stale living docs 0；T-193/194/195 为 frontier | 下述命令；未改地图 |

直接探针的 PASS 项覆盖不存在的 launch、普通终端、Claude 缺记录与首次记录、Codex 未报 ID 与首次记录、两家已批准主控的首次记录、opencode 库不存在与首次记录、agy 无记录/唯一匹配/两个可读匹配。正例还核对复制文本包含预先指定的 CLI、ID 与路径。所有直接调用前后，编排库 `total_changes()` 均不变。

真实 socket 的不存在会话场景返回了可读的禁用原因。比较全部业务表，只有 `orchestration_events` 增加 `request_received`、`request_result` 两条审计记录；没有 launch、任务或其他业务表变化。因此这里的“只读”是业务状态不变，并非数据库零写入。

复现命令（夹具目录及输出名必须换成未使用的新路径，保留本轮证据）：

```sh
node /private/tmp/t195-review1/probe-native-link.mjs /private/tmp/t195-review1/fixtures-02 > /private/tmp/t195-review1/probe-02.json 2> /private/tmp/t195-review1/probe-02.stderr
```

本轮实际运行使用 `fixtures-01`、`probe-01.json`、`probe-01.stderr`，Node 为 `v26.5.0`。输出中的预期来自场景指定的身份及独立创建的文件，而非被测函数返回值。当前候选直接违反这些断言，构成缺陷反例；未修改候选来做“绿态”。

```sh
python3 /private/tmp/t195-review1/probe-socket.py > /private/tmp/t195-review1/socket-01.json 2> /private/tmp/t195-review1/socket-01.stderr
cd /private/tmp/t195-cand/workbench
TMPDIR=/private/tmp/t195-review1/build-root node app/build.mjs --slot review1
python3 /Users/luckye/.agents/skills/project-map/scripts/project_map.py status --root /Users/luckye/Documents/Code/a2a
```

socket 脚本固定保留 `socket-01`，构建固定保留 `a2a-build-review1`；再次执行须选新名称，不能覆盖。构建目录为 `build-root/a2a-build-review1/dist`。

### 既有验收证据的审计

读取了原仓库 `evidence/2026-10-27-batch28/T-195/` 的五份 JSON，未改写：

- `green-04.json` 的 6 项 PASS 对首次启动 worker 有效。Claude 判据检查记录行中的 `sessionId/cwd`，Codex 判据检查首行 `session_meta.payload.id/cwd`；均来自 CLI 自己写的文件。Claude 使用真实 CLI 和本地脚本化模型接口，Codex 使用真实 CLI/模型及隔离 CODEX_HOME。
- `red-4a5e1f3fc.json` 在命令尚不存在时触发断言，属于新功能契约的红态；它不能证明测试会拒绝“返回另一条旧会话链接”的实现。
- `green-01/02` 保留的是失败；`green-03` 文件内实际标记 PASS，brief 将 01–03 合称失败运行并不完全准确。本报告以各文件内容为准。
- 新增测试 `tests/test_t195_native_link_e2e.py:203` 只检查首次启动的两个 worker，没有 agy/opencode、会话切换、同目录多原生会话或锁冲突断言；也没有经过 renderer 右键、Electron IPC 和剪贴板。因此现有绿态不能覆盖 F1–F3。读取返回路径中的记录虽能验证“该 ID 确有记录”，但还需要独立的当前会话判据来排除同工作区的旧记录。

### 界面、结构与说明

静态检查了 agent 行右键 → preload → main IPC → 后台查询，以及复制按钮 → clipboard 的调用链。禁用项用 `aria-disabled` 和低透明度表示，点击处理函数检查 `available`；原因同时放在 `title` 和菜单下方文本中，具备可读的文本出口。没有把 `osc7501:<launch>` 直接当作 agy/opencode 会话号返回。未发现为复制另建一套门禁或状态写入入口；复用现有归档来源本身没有形成第二套归档 API。已确认的结构缺陷为 F3 的异常吞掉，以及 F2 无法识别实例的 ID 沿用。

README 的三个字段格式与决定一致；opencode 记录路径后附 `（session_v2 表）`，仍保留库路径和原生 ID。关于“当前角色”和“还没报来就禁用”的说明与 F1、F2 的实际行为不一致。另有一处事实表述需随修复核正：README 及 findings 称 Codex ID 来自 hook，当前 `panes.ts:1226` 实际从 CLI rollout 的 `session_meta` 绑定它；ID 来源仍是 CLI 自己的记录，不是自造编号。

建议把本报告的失效绑定、跨实例 ID、双库加锁场景纳入已有 T-195 验收入口；修复后先跑相同反例，再经真实 CLI 与右键复制入口取得当前候选的证据。现有实现和现有绿态不能替修复后的候选背书。

## LIMITATIONS

- 未重跑依赖登录和真实模型的完整 `test_t195_native_link_e2e.py`；既有绿态是外部留存证据，摘要未绑定本次冻结候选的提交或完整源码快照，不能据此独立确认其运行时源码与本候选逐字相同。
- 本轮直接探针调用真实生产函数和归档解析器，但输入是合成持久化记录；不能将它说成真实 Claude `/clear`、Codex 新线程或真实 opencode 进程重启的端到端操作。agy 锁冲突使用真实 SQLite 锁，未启动真实 agy。
- 后台 socket 只运行了无需模型的不存在会话与业务只读检查；没有通过该入口复跑所有直接探针。
- 未启动 Electron 窗口或执行真实右键、键盘、悬停、屏幕阅读器及剪贴板读回；禁用原因与交互结论限于静态检查，构建通过不等于 UI 验收通过。
- agy 的合成 blob 只用于验证匹配与错误处理，不证明其真实 protobuf 内部格式长期稳定，也不证明按目录唯一匹配就必然属于当前 CLI 实例。
- 未读取或复制用户真实 `~/.claude`、`~/.codex`、opencode、agy 会话内容；未修改全局配置。没有做本轮范围之外的修复或第二轮审查。
