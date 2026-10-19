STATUS: PASS
TARGET: 9373a9d448820d951bdd8539a49731136c204e68（exec/t093）

第四轮独立只读审查，按主控 #140 派发。未确认本轮范围内需修复的缺陷；第三轮 P1 已关闭。本结论覆盖 T-093 已批准的无模型合同及本轮增量，可以交回主控继续唯一门禁；不代替 submit、acceptance 或 integration，也不宣称真实上游／真实模型已验证。

审查依据为最新 main 的 T-093、T-092 六点用户决定及 #121、#31、#32、#34、#132、#139 裁定；作者 RESULTS、请求、诊断摘要和测试只作定位及待核实材料。目标是核对默认拒绝、错误保真、真实窗格恢复及证据延续；非目标为实现正常登录恢复、真实模型调用和修改归档规则。所有新探针及变异在 `/private/tmp/t093-review04-03yrjf7g`，候选来自 `git archive`，没有建 worktree。全程没有真实凭据读取、供应商 CLI／模型调用、升级、子 agent、问题面板、全局配置写入、提交或集成。

FINDINGS:

- 无已确认的新缺陷。以下 PASS 均注明证据层次和版本边界。

EVIDENCE:

## 1. 恢复白名单：第三轮 P1 已关闭

`workbench/src/panes.ts:27` 的准入是正面合同：controller／Claude Code／ideation 或 executor、允许的认证类别、精确 P1 角色版本、zsh 及四项 shell argv、公开假 token、规范 loopback HTTP origin 和显式合法端口、规范临时 HOME 与 config 同时成立；额外 API key、OAuth token、NODE_OPTIONS 不获准。authentication 缺省是明确保留的旧假 API 合同，不等于默认允许任意缺字段记录。

正常登录标记先拒绝；缺认证字段仍有 role revision、audit/preflight、hook、process log、私有目录、loader 或 exec shell 标记时不会降级。`:272–274` 的准入及完整 shell 命令逐字核对先于旧 PID 查询、`:290` 的版本执行和 PTY spawn。未知引号、后缀、未知认证或缺少正面证据均不能靠外形猜测放行。历史记录只读取；规范 executable_path 仍只补到运行时副本，原完整 argv、版本、原生会话及前台 leader 校验没有绕过。

独立脚本 `restore-independent.mjs` 使用实际 `claudeLaunch` 生成记录，调用实际 `Panes.recover`、真实 SQLite 和合成原生会话文件；只替代 exec、PTY 和进程身份边界。预期来自用户裁定和合法旧记录合同，不导入产品白名单当答案。

- **39/39 PASS**，见 `out/restore-independent-02.json`。3 个正例为实际假 API、去掉 authentication 的实际旧假 API、去掉 authentication 且无 executable_path 的旧假 API；均 version=1、PTY=1、恢复成功。
- 其余 **36 条均 version=0、PTY=0**，保持未恢复、没有 pane_restored。逐项删除 role、cli、preset、role_card_revision、shell、shell_argv、假 token、base URL、HOME、config；另有 token／revision 后缀、URL 斜杠／userinfo／缩写 loopback／前导零端口／越界端口、非规范目录、命令空白／换行后缀／额外命令／引号破坏／未知中间命令／额外 shell 参数、未知认证、正常登录与假标记混合、额外 key／OAuth／loader／process log。
- 包含实际生成的正常登录、仅删除 authentication 的正常登录，以及正常登录混入假认证／假 token；全部在两个 CLI 边界前拒绝。
- 39 条历史 launch 均逐项原样保留；没有重建 R/F/D/C、读取 auth 或真实运行 `/fixture/claude`。

候选现有 `test_t096_restore.mjs` 另在新副本通过：三种身份模式、正常／未知 profile、合法 legacy／显式 fake、worker reclaim、attempt、完整 PTY argv、身份替换拒绝、保存位置与空布局均保留。它的绿色不是本节唯一依据。

## 2. #132 helper 诊断：保留失败，不重试或回落

`panes.ts:536–588` 只把 process_query 附到原异常，再抛出同一对象；原 schema、行、树、leader 和生命周期判断逐字保留。`:542` 仍仅一次固定 Python helper 调用、5 秒、4 MiB；没有第二查询、缓存成功或失败放行。`daemon.ts:394–398` 仍沿用 Refusal 原码／其他异常 orchestration_failed 和原 String(error)，仅增加诊断，回复与 request_rejected.result 相同。

候选诊断合同 **10/10 PASS**。本 reviewer 在其边界夹具上另加 null JSON、根 PID 不匹配、重复行、不连通树，以及直接 processInfo 调用和原 Error 对象同一性检查，**14/14 PASS**，见 `out/diagnostics-independent.json`。每请求 helper 次数为 1，失败时零终端写入、状态未释放；空／截断 JSON、非零退出、信号、超时、spawn EPERM、既有 Refusal 均保留原失败类别。helper 执行拒绝直接返回的对象就是被抛出的原对象。

诊断键只包含 root_pid、helper_pid、stdout、stderr、exit_code、signal、killed、error_code、elapsed_ms。给原 Error 添加合成 argv、env、credential 哨兵，三者均未进入诊断。实际 `processSnapshot.py` 没有改动，只读进程身份与执行路径，不读 argv、环境、auth；其 stderr 为固定错误结构。没有把这些测试扩大成真实内存压力复现；r20 输出截断的根因仍 unknown。

## 3. #139 runner：早帧诊断成立，产品断言没有放宽

独立比对外置原件与 `r21-two-case-diagnosis-22.json`：

- r21 isolation 的 after-view 与 window-2 协议 id=1 完全相同；三个 DOM pane 无 launch，而 snapshot 已有各自身份及缺 argv／恢复成功／worker reclaim 拒绝。
- r21 empty-reopen 的 after-view 同样是协议 id=1；执行、worker 缺 launch。**协议 id=2 三格 launch 已完整，新就绪谓词接受。** 原 runner 的 second 仍是 id=1，后续查找由此 KeyError。
- isolation 原件只有该首帧，不能单靠它证明当时下一帧何时完成；同一 app／driver 的 r22 isolation 在严格谓词下完成，支持 runner 过早采样的诊断。未把这解释成产品永远不会慢渲染。

直接读取 `electron_driver.mjs:92` 和 `:110` 附近：主进程先记录 IPC snapshot；DOM 在 renderer 独立提交，inspect 又将 latestSnapshots 附到 DOM 观察上。snapshot 到达不能证明该 DOM 已显示身份。

`run_restart.py:275–288` 新增的是同格 DOM 的 pane_key、launch、task、role、preset、thread、input_enabled 与 snapshot 对齐。没有跳过无 launch 的格，没有从 snapshot 补 DOM 字段；空集合仍要求 panes／keys 为空及空窗提示。4 秒、64 RPC 预算、后续身份／argv／nonce／只读／worker／归档断言均未改。r22 isolation 缺 argv 主控和 worker 的 DOM 都保留 launch、未恢复提示及只读；拒绝恢复不等于丢身份。

现有离线就绪合同 **24/24 PASS**；持续占位超时、绑定／状态不同拒绝，合法空窗和已渲染失败窗格接受。变异退回 snapshot-only 后 14 个业务检查失败。

对于另外五场：`git diff 0be3d3ff2 9373a9d -- workbench/src workbench/app workbench/hooks workbench/package.json workbench/package-lock.json` 为空；runner 只有上述加严。五场保存的 after-view 均满足新谓词，原件的业务结果经本 reviewer 重算成立，所以这些 **0be3d3ff2 上的产品证据仍有效**。原协议也显示多个更早帧本来不满足新谓词，随后才完整；version 的首窗没有保存额外完整 inspect 帧。没有据此声称五场已用新 runner 重跑，或保证历史每个首窗都能在新 4 秒等待内完成。新 runner 的真实通过证据是 r22 两场。

## 4. 七场原生原件独立核对

`audit-originals-04.py` 退出 0，`out/original-audit-04.json` 为 PASS。读取 215 份 JSON／命令输出，独立核对实际 command 元数据、内核 argv、processInfo、恢复事件、launch_show、窗口与历史 nonce、task／attempt、计数和归档清单，没有采用 worker 的检查摘要作为答案。

| 原件 | 独立观察 | 判断 |
| --- | --- | --- |
| r21 tracer | 同原 session；完整事件与内核 argv；规范前台 leader；原 launch 不变；nonce 可见；显式关闭最终空集 | PASS，0be3d3ff2 |
| r21 three | 两主控完整恢复；worker 保留身份且未恢复／只读，无成功事件；receiver 一份；attempt 不变；关闭 worker 持久化 | PASS，0be3d3ff2 |
| r21 no-argv | restore_argv_missing；保留身份、未恢复／只读，无成功事件 | PASS，0be3d3ff2 |
| r21 version | restore_version_mismatch；保留身份、未恢复／只读，无成功事件 | PASS，0be3d3ff2 |
| r21 no-session | restore_session_missing；保留身份、未恢复／只读，无成功事件 | PASS，0be3d3ff2 |
| r22 isolation | 构思缺 argv 拒绝；执行完整恢复及 nonce 可见；worker 与 attempt 不变；退出保存原打开集 | PASS，9373a9d44 |
| r22 empty-reopen | 两主控恢复；worker 未恢复；关闭全部后 saved=true；第三真实窗口 panes／keys=[]；task 不变、没有重启 receiver | PASS，9373a9d44 |

七场原 run 均 model_turns=fake_posts=0、cleanup_complete=true、writers_absent=true、cleanup diagnostics=[]。独立重新统计七个外置归档的文件数／字节数（包括链接目标文字的编码长度），与各自 archive.json 相符；另将保留源目录与归档的全部路径及链接目标文字直接比较，链接均相同，DB／WAL 的后续变化见下。最终布局只复制已停止夹具的 DB／WAL／SHM 到本轮私有目录，在副本 query_only 查询开关事件；未打开原 SQLite 连接或 checkpoint 原件。所读原件尺寸／mtime 前后相同。没有重新查询历史 PID，避免 PID 复用造成伪证据。

### r21 isolation 旧归档不一致

旧 run 保持 **INCOMPLETE**、cleanup=false，旧现场 `/private/tmp/t078-2-t096-7mp3b5v6` 和外置归档均保留。当前只读完整清单的差异确实仅为：

| 文件 | 保留现场 | 外置归档 |
| --- | ---: | ---: |
| state.sqlite3 | 499712 | 479232 |
| state.sqlite3-wal | 0 | 4120032 |

本轮独立将归档当前 WAL generation 的 **133 个帧、60 个提交帧**按页应用到归档 DB；最后已提交的 **499712 字节与现场 DB 逐字节完全相同**，没有计算校验值。分别在两个私有 SQLite 副本核对，schema 70 行、orchestration_events 390 行、launch_records 3 行、tasks 1 行完全相同，见 `out/archive-independent-02.json`。

因此，当前两份保留件的数据差异可以还原为 WAL checkpoint／截断前后的物理表示，并非已观察到事件或任务丢失。原件没有记录归档前清单的全部明细，也没有 checkpoint 连接日志；**无法确定是谁、在复制的哪个时点触发，不能把当前等价性补称为当时归档核对通过。** 比较规则不放宽、不删除源现场，旧失败不升级。r22 isolation 的当次严格比较及业务重新通过，已提供本轮所需证据；该旧异常不否定新七场的上述结论。

补充检查没有省略其他源目录的变化：r21 no-argv、version、r22 isolation 的当前源 DB／WAL 也已与归档不同；源 DB mtime 均晚于各自 archive.json 的写入时间。对三场分别应用归档 WAL 后，重建 DB 与当前源 DB 仍逐字节完全相同；事件／launch／task 也完全相同，分别为 182／1／1、184／1／1、416／3／1 行，见 `out/later-checkpoints.json`。其余四场源／归档清单一致。这区分了当时成功归档、后来文件表示变化和真正的数据缺失；不是七场当前源目录逐文件仍与归档完全相同的主张。

进一步定位到 `run_restart.py:438`：两类故障注入用 `with sqlite3.connect(...) as database`，没有显式 close，后续仍经过归档。合成 SQLite 探针证实 with 结束后该连接仍可查询；归档先比较成功，再关闭最后连接，会出现 DB 增长／WAL 清零而数据完全相同（`out/sqlite-lifetime-probe.json`）。这是可见的连接生命周期事实，可解释这些后续 checkpoint 的来源；尚不足以唯一归因 r21 isolation 当时的复制竞争，不能把它当成已复现的那次根因。没有实际数据丢失、错误放行或改写归档原件的证据，因此不将该观察升级成产品恢复缺陷。

## 5. 第三轮其余结论的延续与结构检查

`git diff 788d75f4a 9373a9d -- workbench/src` 仅 panes.ts、daemon.ts。正常登录准备／凭据读取、claudeLaunch、OS policies、claudeForwarder、processSnapshot、hook／Stop、app 和依赖均无改动。本轮只重新判断受影响范围，不把旧结论扩大成新运行：

- 网络仍是 OS 只限 `*:443`，应用锁上游主机；Host 剔除、DNS 给定 IPv4、重定向不追随、无传输重试未改。测试 18443 与生产仍共用生成器。没有重新引入 OS 主机过滤主张。
- 真实 HOME 禁写、R/F/D/C 分工和原始凭据只读一次未改。凭据复制或真实登录的历史探针结论仍限原报告，没有在本轮读取真实凭据复验。
- libproc 树、出生时间／身份复核、规范执行路径、前台 PID=PGID=TPGID、alias 保护未改；processInfo 只是把原逻辑放进保真诊断边界。局部 observer 11、alias 2、T-091 IPC 19、T-096 daemon 7 项通过。
- README 仍披露 OS 不按主机过滤、正常登录不自动恢复、2.1.302 onboarding／cwd 信任内部状态、hello 绕过 BASE_URL、预检不能证明零尝试及重试逐条计数。白名单和诊断披露与实现一致；冻结时文档中的待运行状态不冒充本次主控的新原件结论。

按 design-integrity-review 扫描 src 增量，仅定位到 `panes.ts:575` 新 catch，再沿实际 caller 检查。它附加诊断后抛出原异常，daemon 保持失败；没有吞异常转成功、额外查询／重试／DNS fallback、兼容执行路径或第二套 API／门禁。旧假 API 的可缺认证字段是用户要求保留的既有合同，仍经同一恢复入口，不是另起恢复路径。完整 shell 命令核对归准入层所有，没有用 runner 修复掩盖产品身份缺失。

**Deep modules**：现有 Panes、正常登录生命周期与进程 helper 的责任未拆成浅包装层。**Tracer bullet**：审查沿已有 controller_start → 私有 HOME／转发 → PTY／hook／Stop → 事实／清理链，不实现新切片。**Ubiquitous language**：启动记录、原生会话、attempt、未恢复沿用 CONTEXT，不以进程存在或模型自报替代验收。

## 6. Git 历史 token 特征扫描

在内存执行 `git log --format='commit %H' -p 617863704..9373a9d448820d951bdd8539a49731136c204e68`，扫描 **91 个提交**。OAuth access、OAuth refresh、API key、JWT、长 bearer 五类均 **0 命中**。输出只保存类别、位置、计数，见 `out/history-scan.json`；不输出潜在值，不读真实凭据。这是格式扫描，不证明未知编码／格式不存在。

COUNTEREXAMPLE:

先运行未改候选的恢复、诊断、就绪合同，均通过，再在 `/tmp` 做三个单处错误实现：

| 单处变异 | 未改对照 | 变异结果 |
| --- | --- | --- |
| recover 的白名单调用换回“不是 normal 就放行” | 独立实际 launcher／recover 39/39 | rc 2，缺 role／P1／token／URL／HOME 等记录到达版本或 PTY，违反零调用要求；不是导入／超时错误 |
| processInfo catch 把原错误改为空身份成功返回 | 诊断合同 10/10 | rc 2，9 类原失败变成 ok=true，命中必须保留拒绝的业务断言；健康项仍通过 |
| runner 就绪恢复为只看 snapshot | 就绪合同 24/24 | rc 2，14 项失败，包括 r21 两个早帧、缺／错 DOM 身份与输入状态、持续占位和后续帧等待 |

精确 argv、退出码与 stdout／stderr 在 `out/mutation-commands.json`、`out/mutation-{1,2,3}.{stdout,stderr}`。独立恢复变异脚本未导入白名单逻辑或复用其返回值作为预期。候选生产源码未改。

主要复核命令（已有输出独占创建；重放时另选全新文件／目录）：

```sh
node --experimental-vm-modules /private/tmp/t093-review04-03yrjf7g/restore-independent.mjs 新恢复结果.json
node --experimental-vm-modules /private/tmp/t093-review04-03yrjf7g/candidate/workbench/tests/review04_diagnostics.mjs 新诊断结果.json
python3 -B /private/tmp/t093-review04-03yrjf7g/candidate/workbench/tests/test_t093_t096_renderer_readiness.py 新就绪结果.json
node --experimental-vm-modules /private/tmp/t093-review04-03yrjf7g/restore-independent.mjs 新变异结果.json /private/tmp/t093-review04-03yrjf7g/mutants/panes-not-normal.ts
node --experimental-vm-modules /private/tmp/t093-review04-03yrjf7g/candidate/workbench/tests/test_t093_process_diagnostics.mjs 新变异结果.json /private/tmp/t093-review04-03yrjf7g/mutants/panes-swallow.ts
python3 -B /private/tmp/t093-review04-03yrjf7g/candidate/workbench/tests/test_t093_t096_renderer_readiness.py 新变异结果.json /private/tmp/t093-review04-03yrjf7g/mutants/runner-snapshot-only.py
```

前 3 条预期 rc 0，后 3 条预期 rc 2。原件审计程序固定创建本轮输出及 DB 副本目录；重跑须先复制脚本到新临时根并改输出根，不能覆盖旧结果。

LIMITATIONS:

- 新执行覆盖纯逻辑、实际入口类及真实本地 SQLite／原生文件；OS／真实 CLI／UI 结论来自主控保留原件和准确源码延续核对。本轮未执行真实 helper、沙箱、Electron、真实 auth、官方 DNS/TLS、上游或模型，也不作可靠性／吞吐／成本收益主张。
- r21 旧两场仍 INCOMPLETE；r21 五场不改写成 9373a9d44 的新原生运行。旧归档 checkpoint 的触发进程／时点、r20 helper 截断原因仍 unknown；前者有相同数据的独立证据及严格 r22 替代运行。
- `REVIEW-OUTSIDE-05.sh` 仅提供可选的现候选 F 编译及生产 443 profile 对活跃非 443 端口的拒绝补证，无 auth／供应商 CLI／模型；bash -n、嵌入 Python AST 已通过，**未执行**。现有原件已覆盖本轮需要的边界，不要求主控为本报告再跑七场。
- 审查工具失败原样保留：独立恢复初次遗漏 SQLite 父目录；原件审计初次误把跨窗口 pane_key 当稳定身份、将 UI launch 投影当完整记录；首轮 archive 查询误用 tasks.task_id，初稿状态没有计入查询错误，不能采用其 PASS，最终 -02 无查询错误；IPC 首次 archive 没有 app 文件。修正临时夹具／读取方法后另写新结果，未改生产、旧输入或产品断言。这些不是产品红态。
- 开始与收尾 project-map 均 0 problems、0 stale living docs；HEAD 保持完整冻结 SHA。仓库仅新增本报告和指定脚本；原未跟踪原件、证据及 Git 状态保持，不作门禁或发布结论。

RULE:

第三轮“缺字段使受保护启动降级”的失败类别已有可执行的默认拒绝检查及反事实。保留实际 launcher 生成的缺认证字段正常登录、逐项缺少假 API 证据、混合标记、引号／后缀变形、合法旧假 API 正例，并在 recover 的版本和 PTY 两边界断言调用次数。runner 同样保留早帧、已渲染拒绝窗格、持续占位及合法空窗反例；本候选相应检查有效，无需以新增文字规则代替。

T-093 REVIEW PASS
