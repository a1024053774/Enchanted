# T-265 worker 最终验证记录（2026-11-09）

PASS（本票修复与验证范围）。native-cli-06 完整运行退出 0：父版真实超长拒绝，候选完整读取与只读边界通过，两例自有 PTY 均由同一 Popen.wait 确认退出，隔离夹具已删除。当前产品与驱动逐字节等于主控 native-06 冻结快照。native-01–05 的原整轮 INCOMPLETE 与候选 05 的独立行为 PASS 原样保留。本报告不代表门禁已受理、独立审查已完成、标准打包安装或 T-249 大候选已接回；这些由主控接续。

任务 `a2a+T-265-1`，attempt `45faed18-54a4-4312-99d9-6547f6c20782`，session `f08a986a-0c4b-4ebd-b437-4bd747bb128e`，fence `1`，spec_rev `1`。父版 `80a6304225cdd567737362dd045dabf97a625c56`。请求模型为 Codex `gpt-6-astra`、xhigh、普通速度；配置不是实际供应商 tier 的证明。没有额外可写目录，也未修改额外目录。

版本与绑定：真实交互 CLI 为 `codex-cli 0.167.0`；Node `v26.5.0`；`/usr/bin/python3` 为 `3.9.6`。native-06 运行时本次修改尚未提交，因此结果中的 code_revision 是父版 HEAD，候选内容由 native-06 源码快照及运行前后逐字节比较绑定；worker 收尾时再次比较相同。最终交付绑定本报告所在 Git 提交的完整 SHA 与同一次显式 submit，不把父版 HEAD 冒充候选版本。小型汇总见 `native-final-summary.json`。

人工介入记录：主控经工作台正常输入通知 native-06 全部 PASS，要求读取 `native-06-final-feedback.txt` 后立即补报告、Git 提交及显式 submit 一次。worker 已完整读取该反馈并回读原始结果、退出记录、两例原生事件与清理结果。本轮只补报告和小型汇总，不改产品/测试，不重跑已有大组，不另开 issue。旧问题 #4 已由后续人工输入处理，不重复执行旧 native-04 修正；README stale、独立审查、安装和接回由主控负责。

## 修改与边界

小目标是“短入口、完整审查材料、原有门禁”的 Tracer bullet。Deep modules 沿用已有 `PaneManager` / `Panes.createReview` 的投递所有权；Ubiquitous language 使用“审查材料”“候选副本”。未改门禁、CLI 限额、权限、MCP、公开接口、schema、依赖或其他任务。

`GateCore.requestReview` 仍生成原任务卡、完整 diff、完整 verification、上一轮问题及提交说明。`createReview` 仍先写模板、处理既有只读 checkout、追加 agy 提交命令，再将 `role_text + 两个换行 + 最终 prompt` 写入该 launch 的 `request_dir/review-materials.md`。UTF-8、`wx`、0600；所有大小走同一路径。同步写入成功后才经原 `dispatch` 投递短入口。写失败向既有审查创建失败路径传播，不发送材料路径，不删除半写失败证据。

`createPane` 每 launch 创建独立 `request_dir`，启动记录保留它及 review/session/attempt 身份。审查员现有写根排除 request_dir；本次没有添加写根。`archiveThread` 只归档窗格状态，`TrajectoryArchive` 归档原生会话记录，不是 request_dir 的归档器。本次沿用 review-template/result 的临时目录生命周期，不新增清理或归档所有者。若临时材料在读取前丢失，入口要求停止并报告；原提交门禁仍适用。

## 红绿与变异

完成条件命令：

```sh
/opt/homebrew/Cellar/node/26.5.0/bin/node --test workbench/tests/test_t265_review_materials.mjs
```

父版红态见 `parent-red-confirmed.json`（退出 1）：真实 `createReview` 与 `dispatch` 在长输入断言上发送 1620225 字符。原始线上拒绝在主仓库 `evidence/2026-11-09-batch35/T-265/controller/native-rejection.txt`、`reproduction.json`：Codex 0.167.0 拒绝 1318486 字符，限额 1048576。

当前绿态见 `four-cli-candidate.json`（退出 0，5/5）。测试执行真实方法与文件系统，只替换原生进程创建和终端 drain；不据此声称已验证原生沙箱。输入含动态随机标记、长 diff、长 verification、组合字符、emoji、CRLF 和短中文材料；字节期望直接来自输入。覆盖 Codex、Claude Code、opencode、agy 的材料路径、两个 launch 隔离、EEXIST、半写 ENOSPC 不投递、角色保留、agy 命令、只读 checkout 和结果模板身份。

变异复现方式（每个 `T265_MUTANT` 单独运行相同完成条件）：

| `T265_MUTANT` | 业务断言 | 结果与证据 |
| --- | --- | --- |
| `inline-again` | 原生入口必须短，短材料也不得继续内联 | 退出 1，`four-cli-inline-again.json` |
| `truncate-materials` | 全部输入字节必须保留 | 退出 1，`four-cli-truncate-materials.json` |
| `overwrite-materials` | 旧材料必须拒绝覆盖且不投递 | 退出 1，`four-cli-overwrite-materials.json` |
| `omit-agy-command` | 原角色、完整 prompt 与 agy 提交命令必须同时保留 | 退出 1，`four-cli-omit-agy-command.json` |

变异由 Node loader 作用于加载的真实模块，不改生产文件；拒绝来自业务断言，不以源码正则作为行为证明。

早期 `candidate-green.json` 实为退出 1：新夹具 request_id 不符合现有协议。`green-v2.json` 也是退出 1：agy 将夹具目录设为只读后清理失败。这两个是测试夹具问题，不是生产绿态。记录名称不能覆盖实际退出码；全部早期记录保留。修正新夹具身份及清理后才获得上述绿态。

## 回归与证据限制

现有 `test_t082_review_protocol.ts` 首次用仓库 `t152_real_review_submit.json` 回放，因旧 task 值 `t082-real-03` 不符合现行 task 格式而拒绝，见 `protocol-regression.json`；未改该测试或原载荷。另存独立输入 `protocol-current-task-input.json`，只将 task 换为 `project+T-265`，其他身份与报告字段保持原样。相同现有检查通过 12 项严格解析/relay 条件，见 `protocol-current-task-regression.json`。这是现行 task 格式下的协议回归，不宣称原历史载荷通过。

生产 diff 为 5 行新增、1 行替换，未改 `createPane` 参数、Stop、提交协议或门禁。未运行全仓、真实完整门禁或打包测试；集成点由主控执行。

结束前 project-map status 返回 1：Problems 0，stale living docs 1（`workbench/README.md` 覆盖 `panes.ts` 未提交改动）；证据在 `checkpoint-before-native.json`。主控已在答复 #128 接管集成点的 README 说明与地图 Verified；worker 不改卡外文档，不因此等待或重复上报。旧 task 格式载荷失败同样按该答复作为已有历史测试问题保留，不改旧载荷。

## 外部验证与审查

第一版脚本的准备检查见 `native-preparation-check.json`，初次方案见 `native-plan.json`、`RUN-NATIVE.md`。主控用 `/usr/bin/python3`、Codex 0.167.0 外部执行 native-01：`os.killpg(pid, SIGTERM)` 报 EPERM，遮盖先前结果，终端与原生事件未落盘，cases 为空，夹具随后被旧脚本删除。主仓库 controller 下的 `native-cli-01.json`、`native-cli-01-exit.json`、`native-01-test_t265_review_cli_e2e.py`、`native-01-panes.ts` 及 artifacts 均保留原样。`native-cli-01-cleanup-check.json` 记录主控事后只读核对没有残留进程或夹具；不据此补称原轮业务通过，也没有权限弹窗证据。

按答复 #128，当轮只修测试驱动的创建诊断、异常保存与清理：沿用既有 openpty/Popen 方式；先存终端/原生事件和 PID/PGID/阶段，先 poll/reap 已退出子进程，核实活进程组后清理；EPERM 不忽略、不换权限；异常 case 保留，未确认退出的夹具不删除。`driver-green-03.txt` 为 8/8 离线故障注入通过，`driver-native01-counterfactual-02.txt` 为相同断言在 native-01 脚本上的 8/8 失败。全部 OS 进程调用均为 mock，未启动 CLI 或实际发信号。

第二轮精确命令、结果路径与保留策略见 `RUN-NATIVE-02.md`，argv 见 `native-plan-02.json`。`driver-scope-02.json` 证明产品代码逐字节未变、argv 与业务断言 AST 未变；第二轮使用无 `.git` 的候选副本，不把旧轮证据视为覆盖这个最终脚本。当时等待主控真实结果，worker 未在沙箱重试原生 CLI/进程权限。

主控答复 #130 的 native-02 结果为 INCOMPLETE：父版 Folder access 已显示选中的 Open restricted，驱动立即排入 `1+CR` 后等待 240 秒仍停留原界面；sent=false、native_started=false、rejected=false，候选尚未开始。原 opened_restricted=true 只证明排入按键，不能称为成功打开。PID/PGID 97536 正常 SIGTERM/wait 回收，exit=-15，cleanup.complete=true，隔离 CODEX_HOME 已删除；结果及 terminal/process/native-events 在主仓库 controller 的 `native-cli-02.json`、`native-cli-02-exit.json`、`native-cli-02-artifacts/`。没有系统文稿弹窗或权限拒绝证据，原结果不变。

第三轮仅修新驱动 onboarding：沿用 `openCodexRestricted` 的去 ANSI/空白、观察选择、安静 800ms/上限 5 秒、单次 CR；待完整 native ready 包后投递。选择观察、按键排队、按键实际写出、native ready、粘贴实际写出和提交 CR 实际写出分别记录；sent 仅在写出提交 CR 后为真。原有 8 项驱动诊断/清理检查与新增的一个时序检查合计 9/9 通过（`driver-green-onboarding-03.txt`）；同一时序检查拒绝 native-02 的 `1+CR` 行为（`onboarding-native02-counterfactual-03.txt`）。不以这项离线检查代替真实启动。`driver-scope-03.json` 核对产品、argv、业务断言、清理函数和 main/等待期限未变。新命令与事实阶段定义见 `RUN-NATIVE-03.md`。worker 不操作 native-02 失败夹具，剩余缓存由主控记录并清理。

主控通过正常输入继续并要求保留人工介入记录；worker 已完整读取主仓库 controller 下的 `native-03-feedback.txt`。native-03 确实观察到 native ready、完整任务写出与原生拒绝：`Message exceeds the maximum length of 1048576 characters (1665447 provided).`，原生事件为 `[]`。这是真实父版红态；本轮清理中 TERM 后 wait 超时，随后 getpgid(7878) 报 ESRCH，整体仍 INCOMPLETE，候选未开始。原生终端、process 和结果见 controller 的 `native-cli-03.json` 与 `native-cli-03-artifacts/`，本 worker 未改原证据。主控已核对无残留并记录约 549MB 后清理原夹具，worker 不操作它。

第四轮仅修 `stop_owned`：每轮信号前重新 poll；getpgid/killpg 的 ProcessLookupError 必须由同一 Popen.wait 的退出状态确认，wait 无证据继续 INCOMPLETE；EPERM/身份不一致保持拒绝。时序不变式与 9 场景检查见 `EXIT-RACE-04.md`。`driver-green-exit-race-04.txt` 为现有 10 个检查方法通过，`exit-race-native03-counterfactual-04.txt` 为 native-03 冻结脚本上同一退出表的 6 个业务断言失败。`driver-scope-04.json` 核对只改该驱动函数，产品、argv、业务断言、onboarding、240 秒期限与其他驱动函数不变。外部命令见 `RUN-NATIVE-04.md`；当时真实候选尚待验证，未上调结论、未发新 issue。

主控再次经工作台正常输入继续，本次人工介入及完整命令记于 `RUN-NATIVE-06.md`。worker 已完整读取 controller 的 `native-05-feedback.txt`。候选独立证据 `native-candidate-05-behavior.json` 为 PASS：入口 186 字符；全部材料 2150771 字节、1665471 字符，55000 行 diff、50000 行 verification 与头中尾随机标记均等于生成输入；原生工具执行未改 probe.py，材料写入 errno=1，task_started/task_complete 均存在。Codex 版本为 0.167.0。原生先 cat 的输出被截断，后续 Python 完整读取并运行 probe 才提供完整读取证明；没有把截断输出当成读完。native-04 整轮和 candidate-05 原始结果仍为 INCOMPLETE，不改写。主控已核对其自有进程消失并记录文件数/字节后清理相关夹具，worker 未操作这些夹具。

主控 `process-wait-probe-02-events.jsonl` 保存直接退出证据：TERM 三秒后 PID 25165 的 getpgid=ESRCH、poll=None，ps 仍显示该退出中进程；只关闭本次自有 PTY master 后，同一 Popen.wait 返回 -15。这个父版窄探针不覆盖业务验收，也不能推出 ESRCH 都代表成功退出。第六轮只调整 interact.finally：终端和原生诊断先保存，关闭自有 master 并清空 fd，再调用原 stop_owned；关闭错误仍记录并标 INCOMPLETE，原异常保留。新增一个顺序检查覆盖 EOF、超时、交互异常和关闭失败，旧顺序四个场景全部失败（`pty-order-red-06.txt`、`pty-order-native04-counterfactual-06.txt`）；当前所有 11 个检查方法通过（`driver-green-pty-order-06.txt`），全部 OS 调用均为 mock。`driver-scope-06.json` 核对产品逐字节未变、所有驱动函数除 finally 外不变、240 秒/onboarding/业务断言/权限不变，且本地 mock 夹具无残留。

第六轮完整命令（主控已执行，收尾不重跑）：

```sh
/usr/bin/python3 -B '/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1/workbench/tests/test_t265_review_cli_e2e.py' --codex /Users/luckye/.local/bin/codex --node /opt/homebrew/Cellar/node/26.5.0/bin/node --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-265/controller/native-cli-06.json
```

主仓库 controller 下 `native-cli-06.json`、`native-cli-06-exit.json` 与 `native-cli-06-artifacts/` 为原始证据，worker 只读核对后保存 `native-final-summary.json`：

| 检查 | native-06 观察 |
| --- | --- |
| 父版业务红态 | 实际投递 1665447 字符，被 1048576 字符上限拒绝；native_started=false，原生事件为空。 |
| 候选短入口与完整材料 | 入口 177 字符；原生完整读取 2150753 字节 / 1665453 字符，55000 行 diff、50000 行 verification，三处随机标记全部等于生成输入。 |
| 原生工具与只读边界 | 原生工具实际执行原 probe.py；其输出与结果 JSON 相同，materials_writable=false、write_error=1；task_started/task_complete 均存在。 |
| 两例退出 | 父版 PID/PGID 34581，候选 34704；均 pty_master_closed=true、cleanup.complete=true、reaped=true，同一 Popen.wait 得到 exit_code=-1，signals=[]。退出结论来自 wait，不从 ESRCH 推测。 |
| 夹具清理 | `/private/tmp/t265-cli-54wyafyz` 在删除前记录 676 文件 / 1203963649 逻辑字节，removed=true；worker 回读时确认目录已不存在，隔离 CODEX_HOME 随夹具删除。 |

native-06 的初次 cat 输出也被截断；后续 Python 完整读取和原 probe 的字节、行数、随机标记才是完整性证据。原生 Python 留有 xcrun 缓存写入 EPERM 文本，但工具退出 0 并完成上述读取及材料只读检查，未修改权限。完整文本保留在主控 artifacts，不以清理成功删除失败或诊断文本。

behavioral-acceptance-review 证据自查 PASS，详见 `behavioral-review-final.txt`：本地输入 oracle、字节比较、失败时不投递与已知坏实现证据已列明；native-06 补齐真实 CLI 完整读取、只读边界和最终脚本整轮清理证据。该探针覆盖真实 createReview/dispatch 生成的材料和原生交互 CLI，不覆盖完整工作台 Stop/review_submit。独立审查由主控另开干净只读会话，本报告不冒充独立审查。本 worker 遵守任务“不启动额外 agent”。

生产修改未增加异常捕获、fallback、retry、兼容分支或平行 API；小文件和大文件共用一条路径。新测试驱动的清理异常处理已按仓库规则做 design-integrity-review 自查，见 `design-review-driver-02.txt`；本轮 finally 关闭顺序的有界自查见 `design-review-pty-order-06.txt`，不把实现者自查称为独立审查。

## 清理与回退

自有本地夹具已清理；早期清理失败目录的文件数、字节和删除说明见 `fixture-cleanup.json`。协议 SQLite 夹具删除前的状态在对应回归 JSON；原生材料准备夹具的状态在 `native-preparation-check.json`。worker 未启动后台、hc、Electron 或外部模型，未复制凭据；主控 native-01 的清理状况按上节外部证据报告。保留所有失败文本和必要小输入。新离线故障注入夹具无残留，见 `driver-scope-02.json`。

回退只需撤销 `panes.ts` 的材料文件投递改动；回退会恢复原长输入失败。当前真实验证已通过，收尾按原身份提交本次代码、测试与文本证据，再显式 submit 一次。提交钩子自动添加身份尾注；请求文件留在本 attempt 的 A2A_REQUEST_DIR，不进入 Git。queued 只表示排队，受理及后续门禁结论由主控核对。README stale 与地图 Verified 由主控在集成点更新，worker 未改卡外文档。

暂存范围核对为本卡允许的 79 个文件。证据目录因稀疏检出被首次 git add 拒绝后，使用 git add --sparse 纳入同一允许目录，未改配置或权限。暂存空白检查提示三份原始红态日志含尾随空格；按保留失败证据要求不修改原输出，详见 `git-stage-observation.json`。这些诊断不记为测试或生产检查通过。

**Works**：本地 5 项材料行为检查通过，4 个已知坏实现被业务断言拒绝；native-06 父版真实超长拒绝、候选完整读取及只读边界、两例退出和夹具删除全部 PASS，整体退出 0。

**No regression**：现行 task 格式下 12 项审查协议/relay 检查通过；本轮 11 项离线驱动检查通过，含原诊断、onboarding、身份和退出竞态约束。产品与全部业务断言未变，原历史载荷失败保留。

**Risk / undo**：门禁受理、唯一新独立审查、标准打包安装与 T-249 接回由主控接续，不计入本报告完成项。产品可撤销上述 6 行 diff，代价是恢复原长输入故障；保留原材料与各轮失败文本。
