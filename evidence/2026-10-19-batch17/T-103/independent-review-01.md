# T-103 第一轮独立审查

STATUS: INCOMPLETE

TARGET: `1acfeccf86e7b7b6962cc289b8af48037627ef8e`，起点 `cc18d93dbbcf2ee641dc92befe68e5b0609b4807`，分支 `exec/t103`，T-103 / a1。

本轮在无作者会话历史的 reviewer 会话中完成。按主仓库 reviewer 角色卡、AGENTS.md、main 上 T-103 ticket、RESULTS.md 的顺序阅读；用 `git show`、`git diff cc18d93db 1acfeccf8` 核对原文。没有实现、修复、调用模型、开子 agent、提交、切换分支、申请升级或写问题面板。候选开始时工作区干净，结束时只新增本报告和 `REVIEW-OUTSIDE-01.sh`。

**结论：已查范围内未确认产品代码缺陷，原有测试检查没有因本票改动而削弱。三种独立单处变异均被拒绝。但 ticket 的“任务被门禁移除后刷新”没有真实门禁入口证据，不能把直接 SQL 删除代替该条，因此整票保持 INCOMPLETE。**

EVIDENCE:

## 合同与范围

预期来自 T-103 ready_rev 1，而不是从产品输出或 RESULTS 反推：两个命令读取已有 SQLite；项目、任务及任务状态与任务表一致；无 `--task` 时显示选择页；显式 `--task` 保留直达行为；跨项目切换更换窗格；空库正常显示；移除后刷新消失；不改认领、验收和操作锁语义。

**Tracer bullet**：任务表 → 编排后台命令 → main/preload IPC → 项目与任务列表 → 现有 SessionPane。**Deep modules**：查询留在门禁已有数据库所有者，窗口绑定与凭据生命周期留在 main；没有新增存储或第二套窗格托管。**Ubiquitous language**：沿用项目、任务、窗格、启动记录、编排后台。

非目标为创建/删除功能、模型行为、打包、全站前端审查、性能和真实可写 agent 会话。主要未知是“门禁移除”的实际入口；本次已核对的命令表中没有删除任务命令，`revoke` 保留任务。

## 七项必审结果

### 1. 列表只读及门禁边界：PASS（本轮已查范围）

- `workbench/src/gates/core.ts:325`、`:329` 直接 SELECT 当前 `tasks` 表；项目从 `project_id` 去重，不读取可能残留的历史 membership/launch 来构造列表。项目参数经现有 ID 检查并以 SQL 参数绑定。
- `workbench/src/gates/cli.ts:19`、`:138` 只增加两个不要求 task 的命令。`daemon.ts:114`、`:115` 在原门禁状态迁移前返回查询结果；没有进入 `A2AGates.request` 的操作锁、claim、submit、acceptance 或 integration 分支。原状态迁移、fence、CAS 和 attempt 处理未变。
- `daemon.ts:389` 起对列表成功和失败均豁免请求事件写入，与本票“命令不改库”的合同一致。错误仍作为失败返回，没有转为空列表。
- 已检查真实运行原件 `run-20261019T063741Z/readonly-bytes.json` 和对应脚本 `run_t103_picker.py:286-304`。测试在后台运行期间，执行正常列表、未知项目、非法项目后比较完整文件名集合与字节：`state.sqlite3` 4,096 字节、其 WAL 1,388,472 字节；`membership.sqlite3` 4,096 字节、其 WAL 57,712 字节，全部相等。排除的是 SQLite 共享内存锁文件，没有用校验值代替比较。
- reviewer 另用四条未见过的输入、两个项目、`ready/paused/accepted/claimed` 四种状态和倒序插入，在实际 SQLite 上直接调用候选查询方法：列表、排序、标题、状态、未知/非法项目、删除后的内容、空库，以及主库/membership 库和 WAL 字节比较均通过。此局部检查不冒称 CLI/socket 复验。

### 2. 选择页与切换：PASS（已有真实入口证据）；门禁移除见缺口

`main.ts:224-254` 无任务时建立空选择；指定任务时先向后台验证，再读取原有保存布局。`renderer.tsx:228-249` 读取目录及当前选择，刷新时发现任务不在当前目录便清空选择。`main.ts:100-123` 在分离旧视图之前准备目标；切换期间旧 pane 操作被拒；分离等待已接收的输入/释放/凭据申请并撤销输入凭据，没有关闭后台会话或删除保存布局。

已核对真实旅程九项结果、原始命令与观察记录。两项目各两任务；五次往返切换包含原生 Enter 操作；逐次按独立任务 ID、launch 和终端随机标识验证，没有用“出现一个窗格”代替正确身份。旧 key 的 snapshot/input 被拒，不存在任务被拒且原选择保留。显式启动核对 task、标题、launch 和对应输出；空库核对中文提示、零任务、零窗格和无 alert。

这些终端字节来自明确的历史记录夹具，不是实际模型输出。它们足以检查本票的视图路由，不能证明可写 agent 的输入、撤销或中断恢复。

### 3. IPC 安全：PASS（源码和实际 main/preload 模块检查）

- 新四接口都经 `main.ts:45-50` 的窗口注册表、webContents 对象身份及主 frame 检查。项目/任务列表访问当前窗口的固定后台目录；选择状态只来自该窗口绑定；renderer 不能指定后台目录或 operator 身份。
- 扩大的是本票需要的“已登记窗口可以列目录并切任务”能力。没有让 iframe 或未知窗口获得该能力，也没有把 operator 凭据传到 preload。
- 原七个 pane 接口继续按窗口查找随机 pane key；跨窗 key 拒绝先于 transport。四个窗口级接口本来就不接受 pane key，未把其不需要 key 当成漏洞。
- reviewer 实际运行 `test_t091_pane_ipc.mjs --contract picker`，候选通过，包含全部 11 个接口的 iframe/未知窗口拒绝、原七接口的跨窗 key 拒绝、独立序列/凭据、输出绑定、旧布局反例、新窗口级合同。另删除 frame 检查的变异在 iframe 断言处被拒。
- 真实 Electron 使用隔离 renderer；源码仍保留 `nodeIntegration:false`、`contextIsolation:true`、`sandbox:true`，拒绝开新窗和导航。本轮没有在真正 iframe 中另跑攻击脚本；frame 参数拒绝来自执行实际 main 模块的 VM 测试，层次不混用。

### 4. 两个旧测试逐项 diff：PASS

| 修改 | 核对结果 |
| --- | --- |
| IPC handler 数量 6/7 改为名称集合 | legacy 明列原 6/7 个接口，picker 明列 11 个；另检查注册无重复。不是从实际输出生成预期。 |
| preload 键集合 | legacy 保留原 8 个，picker 明列 12 个；空窗格 preload 同样核对完整接口。 |
| 跨窗 pane key 遍历 | 仍覆盖原七个 pane 接口，使用其余参数有效的调用；每次均断言请求数不变，见 `test_t091_pane_ipc.mjs:160-168`。窗口级接口单独使用正确合同。 |
| iframe 拒绝 | 从全部旧接口扩为全部 11 个；新增未知窗口拒绝；每次检查请求未到达 transport，见 `:170-176`。 |
| transport 夹具 | 只增目录响应和不存在任务拒绝；原输入、序列、凭据、输出及布局检查保留。 |
| 空布局重开 | legacy 保持原 pane_layout-only 合同；picker 允许两次明确的 snapshot → pane_layout 只读序列，仍不允许选 launch 或申请输入凭据，见 `:279-284`。 |
| 既有坏版本与关闭变异 | 原四类反例继续要求命中原指定业务断言。reviewer 本次候选测试实际跑到并拒绝它们，不只读取摘要。 |
| `test_electron_e2e.py` 的窗口合同 | 原 8 键改为显式 legacy/picker 集合并查重；标题、项目、claimed、只读、unknown、offset=0、无 Node、零 user_inputs 和门禁任务前后完全相等的断言均保留，见 `:175-193`。 |
| `--runtime-source` | 只改变 Electron 安装位置与观察驱动，构建仍取 `--source`。既有观察驱动文件本票未改；基线/候选共用同一内置盘 43.4.1。 |

四组合同摘要均为 exit=0、PASS：baseline-ipc、baseline-window、candidate-ipc、candidate-window。真实窗口原件仍保留。没有发现删断言、跳检查、异常转成功或用新接口数量提前截住旧关闭反例的问题。

### 5. 红态、版本绑定与截图：PASS（上述已证明范围）

已对原归档基线的 main、renderer、start、build、daemon、core、锁文件与 `git show cc18d93db:<路径>` 逐字节比较，全部一致。原红态分别证明：真实 start.mjs 无 task 退出 1；相同 Electron 运行基线 run 无 task 拒绝；显式任务窗口能显示独立终端输出但没有项目/任务列表。不是拿安装失败、权限错误或握手超时充当业务红态。

真实旅程的 15 个 `source_files` 均与当前候选字节一致。合同测试及观察客户端/驱动快照也一致。唯一不相同的是提交脚本 `RUN-OUTSIDE-03-COMMIT.sh`；其变化正是主控已授权的 sparse 暂存修订，不属于产品或测试输入，未拿它给产品补证。运行时 HEAD 还在起点而产品未提交的事实保留；当前绑定依据上述完整源码比较。

已逐张查看原件目录 `/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-103/run-20261019T063741Z/` 下的七张截图：

| 截图 | 可见证据 |
| --- | --- |
| `red-fixed-task/red-missing-list.png` | 旧固定任务窗口、历史输出、没有项目/任务目录。 |
| `green-no-task/green-picker.png` | 两项目四任务、正确标题与状态、无已选窗格。 |
| `green-no-task/green-switched.png` | 所选任务、标题、launch 与历史终端标识对应。 |
| `green-no-task/green-narrow.png` | 900×650 下侧栏纵向滚动，长中文换行；终端沿用横向滚动。 |
| `green-no-task/green-removed.png` | 被直接 SQL 删除的任务不见，所选窗格清空；并不证明删除来自门禁。 |
| `green-explicit-task/green-explicit-task.png` | 指定任务及对应历史输出。 |
| `green-empty/green-empty.png` | 零项目、中文空状态与后续操作提示。 |

截图证明当时内容与布局；切换、键盘输入、拒绝及副作用结论结合原始驱动请求/响应和 SQLite 读回，未由截图独自推出。

### 6. 界面文案：PASS（新增选择页文案）

新增操作和状态为“刷新列表”“正在读取列表…”“选择任务”“正在切换任务”“还没有项目”等中文。空状态说明到编排后台创建任务后刷新；错误有明确动作/对象，没有营销承诺、空泛赞语或技能名称。项目/任务 ID 和原有 CLI、worker、attempt 等诊断术语按原样显示。长中文和 `<标签>` 按文本显示，截图中未变成 HTML。

### 7. 结构完整性：PASS（本轮已查范围）

按 design-integrity-review 的可达性、责任归属、架构和比例检查，并对固定 diff 调用扫描器的 `scan_unified_diff` 定位；没有调用其摘要/指纹计算。定位记录为 `/tmp/t103-review-01-foe1ykpo/structure-locator.json`。

新增读取和切换异常都进入可见错误，没有空列表/旧任务作为成功回落；`prepareSelection` 验证目标失败即拒绝。`detachPanes` 是切换和关窗两个真实调用点共享的凭据清理，撤销失败在切换路径抛出 AggregateError，未假称切换成功。关窗路径记录错误后销毁视图延续原有语义，本票把原分散清理集中起来；输入结果不明仍有诊断记录，不作为验收成功。未引入重试、兼容产品路径、平行存储或绕过根因的浅包装。legacy/picker 是测试对不同历史合同的显式选择，产品没有两套实现。

## 地图检查

会话开始及结束，在本稀疏目录直接运行规定的 `project_map.py status --root .` 均为 exit=1：8 个 sparse 缺文件项、0 stale。没有把这个原址结果报成通过。

reviewer 进一步在 `/tmp/t103-review-01-foe1ykpo/candidate` 用 `git archive` 恢复候选的完整地图、规范文档及 covers 所需受控路径，并只读使用候选现有 Git 对象/索引，设置 `GIT_OPTIONAL_LOCKS=0`，没有登记或创建 Git worktree。该候选文档树检查 exit=0、Problems(0)、Stale(0)，详见 `map-archived-candidate-git.json`。这是当前候选的独立检查，没有用主仓库 main 的通过替代它。原址 sparse 的 8 项仍存在。

FINDINGS:

## 尚未满足的验收证据

1. **INCOMPLETE：经门禁移除。** `workbench/tests/run_t103_picker.py:337-343` 直接 `DELETE FROM tasks`，验证了当前任务表删除后刷新及历史记录不复活，但没有调用门禁移除。已读命令表及 `revoke/revise` 实现，未找到删除任务入口；本轮也没有收到更改这条验收的裁定。最小收口方式是由执行主控指出真实门禁移除入口并复验，或取得对“隔离 SQL 删除验证当前库”的验收裁定。reviewer 不自行改题，也不要求本票擅自新增删除功能。
2. **INCOMPLETE：本轮新增真实入口复验尚未运行。** 已审阅主控提供的真实旅程与四组合同原件；本轮自己的新输入检查已经跑到实际 SQLite 和 main/preload 模块，但未启动新的 Electron/socket 后台。已把具体复验脚本交出。此项不否定已存在的真实运行结果，也没有把脚本语法检查上调成运行通过。

未发现需要作者立即修复的已确认产品缺陷；以上为证据/验收口径缺口。没有另行发现需要越范围处理的问题。

COUNTEREXAMPLE:

## 独立变异与复现

一次性副本根目录：`/tmp/t103-review-01-foe1ykpo`。有效副本经 `git archive 1acfeccf8 workbench AGENTS.md CONTEXT.md intent.md .project-map` 解出，没有创建 worktree。三个变异各从未变异归档独立解出，不叠加，不修改候选。

先运行未变异候选：

```sh
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs /tmp/t103-review-01-foe1ykpo/candidate-ipc.json --source /tmp/t103-review-01-foe1ykpo/candidate --contract picker
node --experimental-vm-modules /tmp/t103-review-01-foe1ykpo/ipc-candidate-only.mjs /tmp/t103-review-01-foe1ykpo/ipc-good-focused.json --source /tmp/t103-review-01-foe1ykpo/candidate --contract picker
node /tmp/t103-review-01-foe1ykpo/probe-core.mjs /tmp/t103-review-01-foe1ykpo/candidate /Users/luckye/Documents/Code/a2a-wt-t103 /tmp/t103-review-01-foe1ykpo/core-good-state-02 /tmp/t103-review-01-foe1ykpo/core-good-02.json
```

三条均 exit=0、PASS。`ipc-candidate-only.mjs` 保留被审测试的实际 exercise 函数及全部断言，只移除外层历史坏版本/内置变异调度，使本次错误直接命中业务断言，避免被另一个变异的元断言提前截住。`probe-core.mjs` 的四任务输入、预期字段及字节 oracle 来自本轮合同重建，不导入产品常量；只将 effect 解析到已安装依赖，不写依赖或全局配置。

| 变异 | 单处改动 | 命令与拒绝结果 |
| --- | --- | --- |
| `write-on-list` | 在 `listProjects()` 开头增加 `UPDATE tasks SET data=json_set(data,'$.review_marker',1)`，返回列表仍正确。 | `node /tmp/t103-review-01-foe1ykpo/probe-core.mjs /tmp/t103-review-01-foe1ykpo/write-on-list /Users/luckye/Documents/Code/a2a-wt-t103 /tmp/t103-review-01-foe1ykpo/write-on-list-state /tmp/t103-review-01-foe1ykpo/write-on-list.json`；exit=1，“列表命令改变 SQLite/WAL 字节”；WAL 由 383,192 增至 387,312 字节。 |
| `accept-absent-task` | 把 prepareSelection 的 snapshot 失败抛错改为返回伪造 task_id 与空 panes。 | `node --experimental-vm-modules /tmp/t103-review-01-foe1ykpo/ipc-candidate-only.mjs /tmp/t103-review-01-foe1ykpo/accept-absent-task.json --source /tmp/t103-review-01-foe1ykpo/accept-absent-task --contract picker`；exit=1，`:317` 不存在任务拒绝断言 Missing expected rejection。 |
| `allow-iframe` | 从 windowTarget 条件删除 `event.senderFrame !== event.sender.mainFrame`。 | `node --experimental-vm-modules /tmp/t103-review-01-foe1ykpo/ipc-candidate-only.mjs /tmp/t103-review-01-foe1ykpo/allow-iframe.json --source /tmp/t103-review-01-foe1ykpo/allow-iframe --contract picker`；exit=1，`:172` iframe 拒绝断言 Missing expected rejection。 |

变异记录、完整替换文本、argv、退出码、断言栈在 `mutations.json`；各次 JSON、stdout、stderr 和隔离 SQLite 均保留。错误运行的原始 JSON 使用测试自身的 INCOMPLETE 状态；本报告只将指定业务断言命中判为“变异被拒”，没有把环境失败计为拒绝成功。重复复现须给输出/状态目录新名字，原文件不覆盖。

LIMITATIONS:

## 沙箱外复验交接与现场

执行主控运行：

```sh
bash evidence/2026-10-19-batch17/T-103/REVIEW-OUTSIDE-01.sh
```

该脚本已通过 shell 语法和内嵌 Python AST 检查，**未执行真实运行**。它检查候选及既有快照绑定，使用内置盘同一 Electron 43.4.1 和已保存候选构建；以新的两项目四任务/随机终端标识复验 CLI、库/WAL 字节、操作锁目录、选择、跨项目切换、旧 key/不存在任务拒绝、显式启动和空状态。它复用观察驱动，不替换 IPC 或后台响应。所有输出只写新建的 `/tmp/t103-review-outside-01-*`，结果在其 `review.json`，含原始命令、截图和进程身份；不安装、不构建、不提交、不调用模型、不写外置盘或全局配置。后台和 Electron 均脱离调用者进程组；退出未确认就保留现场，不自动发终止信号。

脚本中的删除场景仍明确标为隔离 SQL 删除，不能据其 PASS 自动关闭上述验收缺口。现有历史输出夹具也不能证明可写输入和故障时凭据撤销的实际 Electron 生命周期；这些没有被上调为本轮通过。

本地检查过程的非业务失败保留在同一 `/tmp` 根目录：首次全仓 `git archive` 约 4.5 GiB 已生成，但系统 Python 3.9 不支持 `tarfile.extractall(filter=...)`，未解出，随后改用约 5.4 MiB 的范围归档与系统 tar；首个原 archive 保留为 `candidate.tar`。初版独立依赖解析 hook 递归失败，修正 hook 后换新状态目录取得绿态，原 `core-good.json` 仍保留。地图无 Git 上下文及不存在 covers 路径的两次诊断失败也未计为通过，最终采用上文只读 Git 上下文检查。没有删改失败现场使结果看起来干净。

RULE:

本轮没有确认新的重复产品故障，不新增治理规则。现有完整字节比较、11 接口 sender 拒绝及不存在任务拒绝断言已经分别拒绝本轮三个错误实现；门禁移除的缺口应在验收入口/合同处收口，不能用模型自评补证。

T-103 REVIEW INCOMPLETE
