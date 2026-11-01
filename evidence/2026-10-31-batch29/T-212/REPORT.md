# T-212 worker 报告

状态：**BLOCKED**。候选未完成，不能验收或提交。未 commit、未 push。代码基线是 `4cb88bba7e36bd3e42a5ebc7815e8aa7c99a5ce3`，修改留在 `t212-private-core-shell-panes` 工作区。

## 需要主控决定

### 1. hc 会持久化 terminal.run 的明文 token

已经实测确认，不能只靠后台自己的 token 哈希文件消除：hc 0.1.15 将 `terminal.run.env` 原样保存在私有 `terminals.json` 的 `restart_env` 中，其中有 `A2A_TERMINAL_TOKEN`。上游源码 `crates/herdr-core/src/api/run.rs:158` 赋值 `restart_env = p.env`，随后第 161 行保存 registry。实测摘要见 [hc-token-storage-fact.json](hc-token-storage-fact.json)，只记录“存在”和条数，不包含 token 值；原 registry 留在测试私有目录，没有复制进证据。

当前任务书同时要求 token 经 `terminal.run.env` 传入，以及恢复凭据只保存核验所需的信息、明文不得进入可能复制为证据的文件。后台自己的凭据文件已经改为只保存 SHA-256 校验值，但上游 registry 仍有明文副本。若把 hc 私有状态纳入完整现场归档，这份明文也会随之进入归档。不能宣称当前候选满足凭据要求。

最小选项：

- 明确允许 hc 在后台私有运行目录保留这份环境副本，并把该目录永久排除在证据复制之外；后台自有凭据仍只存哈希。这需要主控确认是否符合新增约束。
- 维持严格的明文不落盘要求，批准把 token 从 `terminal.run.env` 改为在终端启动后经一次性的私有引导通道注入；后台继续只存哈希。这改变任务书指定的 token 传入方式，需要主控裁定后再实现、重新取得反例和绿态。

没有改 hc 源码，没有擅自采用第二种引导方案。发现此事实后停止实现和后续测试，只做本票测试清理、证据脱敏和报告。

### 2. T104 的环境断言与现有终端引导不一致

`test_t104_shell_e2e.py` 在 `shell_io` 阶段失败：第 209 行附近要求 `/usr/bin/env` 的所有 `A2A_*` 输出严格等于一行 `A2A_PROJECT=…`，实际还有现有 a2a 包装命令必需的 `A2A_TERMINAL_*` 和 `A2A_NODE`。T-212 前的 `startShell` 同样会注入这些变量；因此从代码看，这个断言在 T-120/T-126 后已过时。但尚未在完整父版本源码上独立复跑，**不能把“既有失败”写成已证实**。

本轮只按 T-209 的新契约更新了 T104 的重启断言；没有修改这个环境断言去获得通过。请主控决定是否修订这一旧测试的环境断言，以及凭据输出的测试方式。失败现场保留在 `t104-01.*` 与 `t104-01-fixture/`。

## 已改文件与原因

| 文件 | 修改 |
| --- | --- |
| `workbench/src/hcDistribution.mjs`（新增） | 在一处固定 hc 0.1.15、下载 URL、SHA-256。开发、测试和打包共用取用函数；缓存存在时先核验，不符直接报错；没有缓存才下载。不把二进制放进 Git。 |
| `workbench/src/hc.ts`（新增） | 私有会话、显式 HC_SOCKET、私有 XDG 目录；核对 holder 后缀后的 socket 长度；启动后核对 core 的 ppid/进程组；framed hello/RPC/attach、DATA、CREDIT、RESIZE 和终端 kill。连接丢失记录失败，不自动重试。 |
| `workbench/src/panes.ts` | 只把项目终端换成 hc；DATA 追加既有 trace；pid 取 hc 终端记录；追加式事件记录 hc 地址与 session；重启接回原终端；后台停机只 detach 项目终端；显式关闭用 terminal.kill。受管窗格的三处 node-pty 启动保持不动。 |
| `workbench/src/daemon.ts` | 三处直接调用 startShell 的入口改为 await；终端专用 socket 的随机私有目录通过后台私有 manifest 固定下来，后台重启复用地址；存活或未知 endpoint 不被替换。 |
| `workbench/app/package.mjs` | 打包 hc 二进制、LICENSE、THIRD-PARTY-NOTICES；核对其 ad-hoc 签名；构建缓存改放该次临时构建目录；成功后移除中间目录，只保留应用。 |
| `workbench/tests/test_t212_shell_hc_e2e.py`（新增） | 先列失败方式；真实后台、窗口输入、项目终端和重启；独立 pid/计数文件；中文历史、离线输出、流控、原样输入、查询应答、OSC 7501、恢复后 a2a 命令。两个隔离反例分别丢弃 token 校验值或 socket 地址。真实用户 home 经 pwd.getpwuid 获取。 |
| `workbench/tests/test_t104_shell_e2e.py` | 依据 T-209 更新“后台退出即结束 shell”的旧断言，检查原 pid 仍在；允许调用者指定本票证据目录；归档排除 hc 私有运行数据，测试结束停止自己启动的 core。环境断言的失败保留，未放宽。 |

没有改主 checkout、T-216 worktree、项目地图或票的状态。

## socket 与 token 如何恢复

- `terminal-endpoint.json` 只保存终端专用 socket 的随机私有目录地址。地址不包含后台数据目录；停机删除 socket 和空目录，下一次在同一地址重建。
- 后台私有 `shell-credentials/<launch>.json` 以 0600 保存 `{tokenHash}`，目录为 0700。恢复加载同一校验值；核验请求时计算 SHA-256 并作定长比较。这样恢复不需要保存或重发 bearer token。
- `shell_created`、`shell_reattached` 事件包含终端地址、session、pid、screen，不包含 token。普通项目终端输入继续不进入 agent 用户输入或人工介入记录。
- 仍存在前述 **hc 自己保存 terminal.run.env 的明文副本**，这正是停止点。

## 命令与结果

以下命令均从 T-212 worktree 运行。输出路径不可复用；重跑请使用新后缀。完整命令也保存在各 run.json 或 driver.json 中。

| 命令 / 证据 | 结果 |
| --- | --- |
| `python3 workbench/tests/test_t212_shell_hc_e2e.py --output ../T-212-evidence/red-01` | INCOMPLETE：沙箱禁止 ps，不作为红态。 |
| `python3 workbench/tests/test_t212_shell_hc_e2e.py --output ../T-212-evidence/red-02` | **PASS（红态证明）**：未改实现上，后台停止后原编号程序进程消失，按预期失败。见 `red-02.log`、`red-02/run.json`、`before.raw`。 |
| 同入口，输出 `green-01` | INCOMPLETE：Node strip-only 不支持参数属性，已修复；日志保留。 |
| 同入口，输出 `green-02` | INCOMPLETE：程序已跨后台退出存活，但测试重用了操作员凭据文件，第二次启动被拒绝；已修复夹具。残留专属 core 已按主控指示停止。 |
| 同入口，输出 `green-03` | **PASS**：原 shell/program pid、数百行中文历史、离线编号输出、接回后的 `a2a whoami`。 |
| 同入口，输出 `green-04` | **PASS**：上述场景及逐字输入、bracketed paste、中文、CR、Esc、raw Ctrl-C、93×31 resize、恰好一次 DA 应答、OSC 7501 补发、6000 行超过 512 KiB 输出完整到达、普通终端输入未进 agent 用户输入表。 |
| `python3 workbench/tests/test_t212_shell_hc_e2e.py --mutant forget-token --output ../T-212-evidence/token-negative-01` | **PASS（反例被拒绝）**：原程序和终端已接回，`a2a whoami` 返回 invalid_terminal_identity。 |
| `python3 workbench/tests/test_t212_shell_hc_e2e.py --mutant forget-socket --output ../T-212-evidence/socket-negative-01` | **PASS（反例被拒绝）**：原程序已接回，但终端内的 a2a 命令无法收到回执。 |
| `python3 workbench/tests/test_t104_shell_e2e.py --archive ../T-212-evidence/t104-01-fixture --summary ../T-212-evidence/t104-01.json` | **INCOMPLETE**：前述 shell_io 环境断言失败，未走到重启断言。 |
| `python3 ../T-212-evidence/run-regressions.py` | T118、T126、T121、T107 各自测试结果 **PASS**；回归驱动在 T107 期间遍历变化中的目录触发 FileNotFoundError，驱动本身 **INCOMPLETE**。T107 原始 summary 已补收，专属 core 另行停止。 |
| `node workbench/app/package.mjs --slot t212-hc-01 --variant test` | **PASS（构建、资源与签名）**：3 个 hc 文件存在，Apache 许可存在，hc 及应用通过现有 codesign 核对。**没有验证打包应用启动私有 core**。 |
| `git diff --check` | **PASS**。 |
| 项目地图 status | Problems 0；**Stale living docs 1**：workbench/README.md 尚未同步候选运行时变更。见 `project-map-final.log`。本票处于 BLOCKED，没有宣称完成。 |

单项回归的直接命令如下；测试输出保存在相应 `*-regression-01/`。回归驱动另负责读取新夹具身份并停止这些测试专属 core；单独重跑时同样需要清理，不能仅停止编排后台。

```sh
python3 workbench/tests/test_t118_shell_env_e2e.py --summary <新路径>.json
python3 workbench/tests/test_t126_terminal_socket_e2e.py --summary <新路径>.json
python3 workbench/tests/test_t121_role_request_e2e.py --summary <新路径>.json
python3 workbench/tests/test_t107_live_sidebar_e2e.py --summary <新路径>.json
```

打包产物现位于 `/private/tmp/t212-package-4djtaqrx/a2a-build-t212-hc-01/Enchanted Test.app`。原命令沿用了系统 TMPDIR，先在 `/private/var/folders/.../T/` 的本次构建目录产生安装产物；已将本票目录迁入自己的 `/private/tmp` 夹具。原构建日志保留原路径，迁移关系见 `package-location.json`。这次未显式设定 TMPDIR；后续应使用 `TMPDIR=/private/tmp node workbench/app/package.mjs ...`，以严格符合本轮限定的临时写入位置。构建中间目录已由标准打包命令清理，未链接或替换构建输出目录。

## 票面验收逐条状态

| 票面条目 | 状态 | 证据 / 缺口 |
| --- | --- | --- |
| 修前真实入口的重启红态 | **PASS** | red-02；程序原 pid 消失。 |
| 修后程序跨后台重启存活，窗格接回，屏幕与历史完整 | **INCOMPLETE** | 进程、原 pid、中文编号历史与离线输出 PASS；没有完成 xterm 渲染屏幕的专门复核。 |
| 应用启动用固定打包 hc 私有 core；不影响用户 core | **INCOMPLETE** | 开发后台私有 core、固定实际版本和 detached 检查 PASS；目录只读前后核对未变化；未从打包应用启动验证。按要求没有连接用户 default core，因此没有声称实查过它的终端列表。 |
| 打字、粘贴、中文、Esc、Ctrl-C、输入记录 | **PASS（后台真实入口）** | green-04；另有运行中的 Python 被普通 Ctrl-C 中断。尚未完成专门桌面按键验证。 |
| Claude Code 经 a2a request 申请、界面批准，侧栏无回归 | **INCOMPLETE** | T121 脚本化 Claude 包装与角色申请 PASS；T107 真实 Electron 侧栏与脚本化 Claude 工作流 PASS；T184/T195 未跑，不能宣布全范围无回归。 |
| 包内 hc 二进制与 Apache-2.0 声明 | **PASS** | package-01.log、package-resources.json，签名已核对。 |
| 项目终端没有第二条 node-pty 启动路径 | **PASS（代码）** | startShell 只调用 hc.run；受管窗格原三处启动没有迁移。 |
| agy 只读独立审查无阻塞意见 | **INCOMPLETE** | 未启动；留主控安排。本报告不是独立审查。 |

## 证据与清理

- 所有测试使用自己的私有 session；没有连接或重启 default core、用户 Herdr server。新测试的用户目录查询采用系统账户 home，测试 HOME 是独立夹具。
- red-02、green-03、green-04、两个身份反例的只读目录检查均记录为未变化。T118、T126、T121 的回归驱动也保存了前后目录比较。
- 这批测试未调用真实供应商模型；Claude 行为由现有本地脚本化入口提供。未写用户的 `~/.claude`、`~/.codex` 或 hc 配置与状态目录。
- 已停止 green-02 留下的专属 core；新测试及两个反例都记录 core_cleanup exit 0；回归驱动停止 T118/T126/T121 的 core；T107 的补清理见 `t107-cleanup.json`。T104 也已清理。未删除失败夹具。
- T104 主动执行 env，使测试 bearer token 出现在原 trace 和 base64 传输输出中。证据副本已只移除该敏感字段；不输出其值。见 `credential-evidence-scan.json`：已知终端 token 在证据文本中明文匹配数为 0。hc registry 没有被复制进来。
- 脱敏后 T104 输出偏移和归档字节统计仍保留原运行值，**不能再拿来证明现在证据文件的大小一致**；没有重算数字掩盖变化。其他失败输出、异常和结果未覆盖。

## 未完成与未知

- 因凭据存储冲突停止：T184、T195、test_daemon_recovery_e2e.py、test_electron_e2e.py 未运行。
- 未验证打包应用的真实启动与私有 core 启动链；未进行 agy 独立审查或 behavioral-acceptance-review 的独立验收。不得把本人的测试和报告当成写审分离。
- 未跑 core 崩溃/inexact 场景，未实测“终端内 agent 在 core 崩溃后率先拉起新 core 导致环境继承”的已知风险。代码会在恢复时记录并返回 hc 的 screen 属性，但未取得该失败场景的运行证据。
- 未专测用户原有 XDG_STATE_HOME/XDG_CONFIG_HOME（含空值）的还原分支、损坏缓存拒绝、超长 socket 拒绝，以及 macOS 已知系统二进制逃逸清理情形。
- workbench/README.md 是 stale living doc；未关闭 T-212。只有上述决定明确、候选补完、剩余检查与独立审查完成后，才能进入主控验收与提交。

## 第二轮

当前总状态：**INCOMPLETE**。本轮要求的实现补充和实测已完成；四项旧回归在候选与父版本上均未通过，agy 独立审查仍未进行。不能宣布整张票 PASS。第一轮正文保持原样；本节给出当前状态，第一轮的两个停止点已有主控裁定。

### 已采用的取舍

主控在本轮明确批准“hc 在私有 terminals.json 的 restart_env 里保存明文 token：采用你的第一个选项”。因此保留任务书的 `terminal.run.env` 传入方式，不增加一次性引导通道。

- 后台自有 `shell-credentials/<launch>.json` 仍只存哈希，文件 0600、目录 0700。
- hc 私有运行目录在后台私有数据目录下，实际 session 目录模式已核对为 0700；其中 registry 的明文 token 是同一用户可读的运行数据。
- **整个 hc 私有运行目录永久排除在证据复制之外**。新增 `tests/hc_evidence.py` 作为测试的证据检查入口，核对目录及归档内没有 hc 状态文件，并检查已知 token 的文本和 base64 传输字段。
- `round2-evidence-boundary.json` 检查的是整个本票证据目录，不只一个绿态目录：hc 私有状态文件数 0、已知 token 明文匹配数 0。合成的“复制私有状态”“泄漏 bearer token”两个坏产物也被拒绝；它们只在 `/private/tmp` 的测试夹具中创建，没有复制真实 hc 状态。

### 本轮修改

1. **T104 环境断言**：先按要求将 `4cb88bba7` 用 `git archive` 导出至 `/private/tmp/t212-parent-iomubhjr`，用 `/bin/cp -cR` 克隆 node_modules。生产 `src/`、`terminal/` 来自父版本；同一份当时的 T104 测试用于两边，环境断言未放宽。父版本同样在 `shell_io` 的“只有 A2A_PROJECT”断言失败，见 `parent-t104-02.json`、`parent-t104-02.log`、`parent-t104-command.json`。没有给主 checkout 加 worktree。

   随后把断言改为精确允许 8 个导出变量名：`A2A_PROJECT`、`A2A_NODE`、`A2A_TERMINAL`、`A2A_TERMINAL_BIN`、`A2A_TERMINAL_CLI`、`A2A_TERMINAL_PLUGIN`、`A2A_TERMINAL_SOCKET`、`A2A_TERMINAL_TOKEN`；出现其他任何 `A2A_*` 仍失败。只输出变量名，不再把 token 值输出到 trace。候选最终 `t104-03` PASS。

2. **屏幕重绘修复**：真实 Electron 检查在 `round2-screen-02` 暴露旧 trace 后追加 hc 完整重绘导致滚动历史重复。`attachShell` 现在在完整重绘前追加终端 reset；trace 仍追加写入，不截断原记录。最终 `round2-screen-04` 中，实际 xterm buffer 与独立 `hc terminal.read` 的 **457 行**中文编号逐行相等，首行是 `编号-000001-中文`，最后为 `编号-000457-中文`，没有缺行或多行。测试只暂停夹具程序的输出，Python 仍是原来的前台程序；恢复输出后继续核对 Ctrl-C、输入和流控。截图为 `round2-screen-04/reattached-terminal.png`，实际文本分别在 `xterm-buffer.txt`、`hc-terminal-read.txt`。

   `--mutant no-reset` 在隔离源码副本删除该 reset，同一 Electron 检查失败，见 `round2-screen-negative-01`。这不是只检查 trace 文本的绿态。

3. **启动失败修复**：新增的坏缓存探针先暴露出后台在 hc 初始化完成前公布就绪、恢复拒绝后停机也被拒绝的问题。现在 `serve` 在公布就绪端点之前等待私有 hc 启动；损坏缓存会明确使 `daemon_start` 失败，不留下“已就绪”的后台。第一次失败现场 `round2-boundaries-01` 保留，其测试专属后台经核对 state argv 后停止，见 `boundary-01-failed-daemon-cleanup.json`。

4. **新检查**：扩展 `test_t212_shell_hc_e2e.py`，增加真实 Electron buffer 对照、用户 core 的目录与 pid/启动时间前后比较、证据隔离断言；新增 `test_t212_hc_boundaries_e2e.py`，从真实后台和项目终端入口核对坏缓存、holder 路径长度、XDG 与 HC 环境边界。

5. **文档**：更新 `workbench/README.md`，说明项目终端与受管窗格的不同运行路径、重启接回、完整重绘、固定 hc 分发、构建临时缓存、凭据存储与证据排除规则。最终项目地图 status 为 Problems 0、Stale living docs 0，见 `project-map-round2.log`。

生产代码的本轮额外改动只有前述启动顺序与完整重绘 reset；没有迁移受管窗格，没有增加 fallback、自动重试或一次性 token 通道。

### 真实入口检查与重跑命令

以下命令从 T-212 worktree 运行；重跑应换新的输出目录和构建槽，保留现有证据。

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output ../T-212-evidence/round2-screen-04
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mutant no-reset --output ../T-212-evidence/round2-screen-negative-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output ../T-212-evidence/round2-boundaries-02
TMPDIR=/private/tmp python3 workbench/tests/test_t212_hc_boundaries_e2e.py --mutant leak-xdg --output ../T-212-evidence/round2-boundaries-negative-01
TMPDIR=/private/tmp python3 workbench/tests/test_t104_shell_e2e.py --archive ../T-212-evidence/t104-03-fixture --summary ../T-212-evidence/t104-03.json
TMPDIR=/private/tmp node workbench/app/package.mjs --slot t212-hc-03 --variant test
TMPDIR=/private/tmp python3 ../T-212-evidence/round2-package-probe-04.py --app '/private/tmp/a2a-build-t212-hc-03/Enchanted Test.app' --output ../T-212-evidence/round2-packaged-runtime-04
TMPDIR=/private/tmp python3 ../T-212-evidence/evidence-boundary-check.py
```

| 检查 | 当前结果 | 证据 |
| --- | --- | --- |
| 重启、原 pid、中文历史、离线输出、恢复后 a2a 命令、实际 xterm 屏幕 | **PASS** | round2-screen-04/run.json、两份文本、截图。 |
| 去掉 reset 的坏实现 | **PASS（按预期被拒绝）** | round2-screen-negative-01，失败于实际 xterm/hc 文本对照。 |
| 损坏 tarball | **PASS** | round2-boundaries-02：报 SHA-256 mismatch，没有下载替换，没有备用二进制，没有发布后台 control socket。 |
| socket 超长，含 holder 后缀 | **PASS** | 同上：core socket 自身为 98 字节，holder 后缀使其超限，启动明确拒绝，不另选路径。 |
| 用户 XDG 未设置、原有非空值、显式空值 | **PASS** | 三种真实终端分别读回 set/value；非空值场景还在用户夹具配置位置放了无效 hc 配置，私有 core 没有读它。 |
| 继承的 HC_SESSION/HC_SOCKET/HC_SCOPE 不进入新终端基础环境 | **PASS** | 同上：新终端使用记录的 enchanted 会话、私有 socket、新 scope。 |
| 去掉 XDG 还原的坏实现 | **PASS（按预期被拒绝）** | round2-boundaries-negative-01：在 xdg-unset 场景观测到泄漏的私有目录，断言失败；不是夹具启动错误。 |
| 打包资源、许可、签名 | **PASS** | package-03.log、package-03.json；TMPDIR=/private/tmp，成功后本次 work/ 已清理，仅保留应用。 |
| 真正启动打包应用，包内 hc 启动私有 core | **PASS** | round2-packaged-runtime-04：实际 core pid 80071，ppid 1，版本 0.1.15，ps 的进程路径为 `/private/tmp/a2a-build-t212-hc-03/Enchanted Test.app/Contents/Resources/app/hc/herdr-core`，真实 Electron page 已就绪。 |
| 打包探针清理 | **PASS（强制退出夹具应用）** | 同上：SIGTERM 期限内未退出，按既有 Electron 测试的有界清理方式 SIGKILL 自己的应用，再停止该后台与私有 core。**没有证明正常交互退出**。 |
| 用户 core 的替代三项证据 | **PASS** | screen-04、boundaries-02、packaged-runtime-04 均有前后完整观测：用户状态目录只读列表相同；用户 herdr-core 的 pid/启动时间相同；私有 socket 在 /private/tmp，位于用户 home 之外。未连接 default core。 |
| 整个证据目录不含 hc 私有状态与已知 token 明文 | **PASS** | round2-evidence-boundary.json；扫描器的两个坏产物对照也被拒绝。 |
| 项目地图、差异格式 | **PASS** | project-map-round2.log；git diff --check。 |

打包探针的早期记录也保留：`round2-packaged-runtime-01/02` 因调试端口参数写为两个 argv，未能取得页面；改为 `--remote-debugging-port=…` 后页面正常。`round2-packaged-runtime-03` 已证明 core 路径与页面，但 SIGTERM 退出等待超时，其补清理见 `packaged-runtime-03-cleanup.json`、`packaged-runtime-03-forced-ui-cleanup.json`。最终 -04 将有界强制清理显式记录，未掩盖退出方式。没有修改产品的退出行为。

### 九项旧回归的当前结果

所有要求列出的旧回归都已实际运行。四项未通过的测试又在同一父版本独立副本上复跑；没有通过修改范围外代码或放宽断言把它们改绿。

| 回归 | 候选当前结果 | 父版本对照 / 说明 |
| --- | --- | --- |
| T104 | **PASS**，t104-03 | 父版本在旧环境断言同样失败；按本轮授权修订后候选通过。 |
| T118 | **PASS**，t118-regression-04 | agent 标记过滤与用户普通配置保留。 |
| T126 | **PASS**，t126-regression-04 | 终端专用 socket、身份及越权拒绝。 |
| T121 | **PASS**，t121-regression-04 | 脚本化 Claude 包装、角色申请、批准及边界；无供应商模型调用。 |
| T107 | **PASS**，t107-regression-04 | 真实 Electron 侧栏、两个 worker 与 reviewer 的脚本化流程。 |
| T184 | **INCOMPLETE**，t184-regression-02 | `shim_claude_state_known` 读到 unknown；父版本 parent-t184-01.json 在同一检查同样失败，其他检查结果保留。未把它判为 T-212 新增未知，也没有宣称该旧检查通过。 |
| T195 | **INCOMPLETE**，t195-regression-02 | `managed_codex_unsearchable_day_grey` 失败；父版本 parent-t195-01.json 在同一检查同样失败。未查定其根因，未改 nativeLink 或权限判断。 |
| test_daemon_recovery_e2e.py | **INCOMPLETE**，recovery-regression-03 | 5 个测试都在 card_save 阶段报 unknown_task；父版本 parent-recovery-01.json 同样 5 个测试在同阶段报 unknown_task。没有取得这套旧门禁恢复场景的通过证据。 |
| test_electron_e2e.py | **INCOMPLETE**，electron-regression-03 | 窗口测试前的 card_save 夹具准备报 unknown_task；父版本 parent-electron-01.json 同样失败。本轮 screen-04 的真实 Electron 恢复检查独立通过，但不替代该旧测试的通过结论。 |

候选第一批 recovery/electron 还曾先遇到 daemon_recovering，见 regression-02。hc 初始化移到发布就绪之前后，最终 -03 达到与父版本相同的 unknown_task 失败点；早期失败未覆盖。

重跑入口：

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t184_unwired_cli_e2e.py --summary <新路径>.json
TMPDIR=/private/tmp python3 workbench/tests/test_t195_native_link_e2e.py --summary <新路径>.json
TMPDIR=/private/tmp python3 workbench/tests/test_daemon_recovery_e2e.py --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_electron_e2e.py --source "$PWD" --stage window --output <新目录>
```

本轮 `run-regressions-round2*.py` 保存了底层命令、私有原件位置、测试退出码和自己启动的 core 的清理结果。它只把摘要/文本复制进本票证据，原始 tar 及 hc 运行目录留在 `/private/tmp` 的私有夹具。独立重跑也要停止测试自己的 core，不能只停编排后台。父版本的 recovery/electron 为运行依赖补用了同版本 `git archive` 中的 acceptance；没有连接真实供应商。

### core 崩溃风险

结论仍为 **未知 / INCOMPLETE**。两次隔离探针保存在 `round2-crash-01/02`；命令脚本为 `round2-crash-probe*.py`。只对经过路径核对的、本夹具创建的 hc core 发 SIGKILL，终端内是 Python 脚本化 agent，不调用真实模型。

第二次探针确认后台记录 `hc_connection_lost`，状态为 unknown，见 `round2-crash-observation.json`。随后终端内脚本调用 `hc server start` 没有在期限内返回，未取得新子终端环境，**不能据此声称没有环境继承风险，也不能声称已经复现继承**。主控应另行登记。没有把 core 崩溃说成普通后台重启，也没有取得 `inexact` 屏幕重新接回的完整运行证据。

### 票面验收当前状态

| 条目 | 当前状态 |
| --- | --- |
| 修前真实入口重启红态 | **PASS**，第一轮 red-02。 |
| 修后原程序存活、接回，屏幕与历史完整 | **PASS**，round2-screen-04；真实 xterm 与 hc 文本对照，no-reset 反例被拒绝。 |
| 打包固定 hc、私有 core、用户 core 隔离 | **PASS**，package-03 与 packaged-runtime-04；采用主控本轮批准的目录、进程和 socket 三项替代证据。 |
| 打字、粘贴、中文、Esc、Ctrl-C、输入记录 | **PASS（后台真实输入入口）**，screen-04 同时重跑原输入与流控场景，T104/T126 当前也通过。不是一次独立桌面键盘自动化全覆盖。 |
| Claude 角色申请、批准与侧栏 | **INCOMPLETE（全项）**：T121/T107 当前通过；T184 的已知状态检查在父版本和候选都失败。不能宣称所有 CLI 状态检查通过；没有另加一次真实 Electron 点击批准按钮的完整旅程。 |
| 包内 hc 与 Apache-2.0 声明 | **PASS**，package-03。 |
| 项目终端没有第二条 node-pty 启动路径 | **PASS（代码与入口）**；受管窗格未迁移。 |
| agy 只读独立审查无阻塞意见 | **INCOMPLETE**，未执行，留主控安排。本人新增测试和报告不算独立审查。 |

### 需要主控处理与交接

- 四项旧回归的父版本对照已经补齐；失败属于当前既有验收缺口，不能算通过。是否登记、修复或调整其夹具，由主控处理；本 worker 没有修改范围外的门禁身份、nativeLink、CLI 状态规则或这些旧断言。
- 打包应用的 SIGTERM 退出在期限内未确认，已安全清理本票进程；正常交互退出未验证，未对产品退出路径作修补。
- core 崩溃后由终端内 agent 首先拉起新 core 的环境风险仍未知，按本轮指示交主控另行登记。
- agy 独立审查待主控安排，T-212 保持未关闭。
- 最终候选为基线 `4cb88bba7e36bd3e42a5ebc7815e8aa7c99a5ce3` 加 `candidate-round2-final.patch`；较早的 `candidate-round2.patch` 保留，不能替代最终候选。没有计算候选指纹，没有 commit 或 push。
- `round2-process-cleanup-final.json` 核对本轮测试范围内的 hc 与打包应用运行进程已无残留；各个测试保留自己的 core_cleanup 记录。所有失败夹具和前两轮异常证据均保留，hc 私有状态没有归档到这里。

## 第三轮

当前总状态：**INCOMPLETE**。主控本轮指定的崩溃侧栏修复已取得红态和绿态，崩溃后重启的 `inexact` 记录、T104 外置盘归档、边界、T107、T121 均通过；但原真实 Electron 画面对照两次失败，不能把整张票上调为 PASS。前两轮正文未改写。

### 对审查的处理与改动

已读取主控提供的 `REVIEW-agy-r1.md` 和 `REVIEW-agy-r1-controller-check.md`，以实际代码、实测与主控本轮裁定为准，没有采用审查中不存在的规格原文或不对应的文件引用。

- `workbench/src/sidebar.ts`：普通终端行与已批准主控行都优先检查 `pane.failed`；有 failed 就投影为 unknown。未改 lifecycle，未改 `terminalAlive` 或角色是否结束的规则。
- `workbench/src/roleRequests.ts`：先核对 `all()` 通过构造时传入的 alive 回调判断身份、该回调是 `Panes.terminalAlive`；随后改正后台重启必然结束身份的旧注释。接回原终端时身份保持，终端关闭或接不回时才结束。
- `workbench/README.md`：更新指定的身份、普通终端重启描述，以及运行中 failed 的侧栏状态；接回后 lifecycle 仍为 running。未将 core 崩溃描述为完整恢复。
- `workbench/src/panes.ts`：删除 shell 分支 return 之后的两条不可达 `confirmShellExit` 调用；保留升级前 node-pty 记录的 pid 核对路径，补上原因与移除条件——受支持的数据目录全部迁移或归档这些旧记录后才能删除。没有改 attach 的 `\x1bc` reset，没有增加 inexact 的 UI 提示或拒绝挂载逻辑。
- `workbench/tests/test_t212_shell_hc_e2e.py`：在文件头补列崩溃场景的失败方式，新增独立 `--core-crash` 场景。经真实后台入口建立普通终端和已批准主控，核对崩溃前分别为 idle/running，再只向本测试私有 core 发 SIGKILL；同一场景随后重启后台检查两份终端的 inexact 记录和原 pid/身份保持。主控身份部分使用真实 request/decide/confirm 传输入口的夹具，不调用模型，也不冒充实际 Claude 旅程。
- `workbench/tests/test_t104_shell_e2e.py`：原样恢复两条外置盘断言。继续排除整个 hc 私有运行目录，并在复制归档后、删除私有夹具之前，用本次真实 token 集合调用 `hc_evidence.assert_public_evidence`。

最终候选是基线 `4cb88bba7e36bd3e42a5ebc7815e8aa7c99a5ce3` 加 `candidate-round3-final.patch`；之前的候选 patch 保留。未 commit、未 push，未改主 checkout、T-216 或 T-212-controller。

### 崩溃场景：红态、绿态和清理

精确入口（从 T-212 worktree 执行，现有输出不复用）：

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output ../T-212-evidence/round3-crash-red-03
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output ../T-212-evidence/round3-crash-green-01
```

- **红态证明 PASS**：`round3-crash-red-03/run.json` 在修复前失败，失败项恰好是 `ordinary_unknown` 和 `controller_unknown`。两份窗格的 failed 都以 `hc_connection_lost` 开头；普通终端侧栏仍是 idle，主控仍是 running。其余恢复断言已通过。该运行清理 PASS。
- **修后绿态 PASS**：`round3-crash-green-01/run.json` 的所有断言为 true。普通终端和主控在连接丢失后都为 unknown；主控身份仍有效。重启后，两份终端均有 `shell_screen_inexact` 事件，`status.screen` 为 inexact，`shell_reattached.data.screen` 也为 inexact；原 shell pid 保持，原 token 身份仍能调用 terminal_whoami，角色仍为 executor。
- **新 core 的来源和环境**：本场景没有终端内 hc 客户端；旧 core pid 50536 被杀后，重启编排后台得到新 core pid 50589。新 core 的子终端实际读回 `T212_CORE_STARTER_MARKER=restarted-daemon`，XDG_STATE_HOME 是该夹具后台的私有 `state/hc/state`。这证明本场景新 core 使用了重启后台的环境；**终端内 agent 抢先拉起的情形仍未知，未据此补称 T-220 风险已解决**。
- **无残留 PASS**：绿态记录两份 holder pid 50559、50620 及所有观察到的 core/shell pid 都退出，私有 socket 目录没有 `.sock` 残留。最终另对本轮全部崩溃尝试的已知 pid 作只读复核，均不存在，见 `round3-crash-final-cleanup.json`。

早期 `round3-crash-red-01/02` 的夹具错误保留，不当作合格红态：-01 错把只展示待处理申请的列表当作已生效角色列表；改为核对 terminal_whoami。-02 错把 hc CLI 的简化 run 输出当作含 pid 的 API 记录；已移除该不成立的读取。-01 曾因尚未重启 core 而无法清掉 holder，后经本夹具显式私有 session/socket 启动 core 并停止完成补清理，记录在 `round3-red-01-restart-cleanup.json`。没有操作 default core。

### 本轮要求的回归与结果

| 命令 / 入口 | 当前结果 | 证据 |
| --- | --- | --- |
| `test_t212_shell_hc_e2e.py --core-crash` | **PASS**，修复前反例被拒绝 | round3-crash-red-03、round3-crash-green-01。 |
| `test_t212_shell_hc_e2e.py --electron-screen`，原画面场景 | **INCOMPLETE**，两次失败 | round3-screen-01：hc 479 行、xterm 478 行，缺 `编号-000478-中文`；round3-screen-02：hc 459 行、xterm 458 行，缺 `编号-000458-中文`。两份实际 buffer、hc 文本和截图均保留；两次清理 PASS。 |
| `test_t212_shell_hc_e2e.py`，不附加画面对照的原输入/流控场景 | **PASS** | round3-io-01；原 pid/中文历史、离线输出、a2a、OSC 7501、打字/粘贴/中文/CR/Esc/Ctrl-C、resize、一次 DA 应答、6000 行流控与输入记录都通过。此项不替代失败的 Electron 画面对照。 |
| `test_t212_hc_boundaries_e2e.py` | **PASS** | round3-boundaries-01；坏缓存、holder 路径超限、XDG 未设置/原值/空值、私有环境、用户 core 前后比较。 |
| T104 | **PASS** | t104-round3.json、t104-round3.log；已使用指定外置盘新目录。 |
| `test_t107_live_sidebar_e2e.py` | **PASS** | round3-t107/summary.json、driver.json；真实 Electron 与脚本化模型流程，专属 core 清理退出码 0。 |
| `test_t121_role_request_e2e.py` | **PASS** | round3-t121/summary.json、driver.json；角色、身份、接线与越权检查，专属 core 清理退出码 0。 |
| project-map status | **PASS** | project-map-round3-final.log：Problems 0、Stale living docs 0。 |
| `git diff --check` | **PASS** | 最终候选执行通过。 |

原画面场景的缺行不能解释成通过。第二轮也曾留有类似的画面对照失败，本轮没有把它们覆盖，也没有删改断言去获得绿态。本轮的侧栏修复不改变终端输出和 reset 路径；**缺行的根因尚未查定**，是否交 T-220 处理需主控决定。本轮遵守指定范围，没有修改界面历史提示或 reset 行为。

各命令的完整 argv/退出码保存在对应 run.json、driver.json；回归驱动是 `run-regressions-round3.py`。主要重跑入口：

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t107_live_sidebar_e2e.py --summary <新文件>.json
TMPDIR=/private/tmp python3 workbench/tests/test_t121_role_request_e2e.py --summary <新文件>.json
```

### T104 的外置盘归档与凭据边界

本次实际命令：

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t104_shell_e2e.py --archive /Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-212/t104-round3 --summary ../T-212-evidence/t104-round3.json
```

运行前两条外置盘断言成立，指定归档目录尚不存在。归档现有 17 个文件、501092 字节；保留 `t104-round3.archive.json`，不含校验值。该命令是本次运行记录；重跑需主控另行指定未存在的新归档目录，不能覆盖此目录。

复制时排除 hc 私有目录；在仍持有本次真实 token 集合时，`hc_evidence.py` 已检查归档：**私有状态文件 0、已知 token 明文匹配 0**，结果在 t104-round3.json 的 `archive_evidence_boundary`。随后只读复查了归档的 hc 状态文件排除情况；原 token 未为了复查再保存到证据里。没有把空 token 集合的复查当作真实 token 检查的替代。

### 引用主控补充的条目 5 证据

主控已明确要求引用、不必重做：

- [t133-ctl-01/summary.json](/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller/t133-ctl-01/summary.json) 中实际 Claude 的 a2a 请求结果带 `cli: claude`、非空 native_session，状态 approved；`observed.ideation_pane` 的 row/header 均为 idle，headerText 为“空闲”，回合检查包含 running。
- [t133-ctl-01/driver.json](/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller/t133-ctl-01/driver.json) 记录私有 `enchanted-e4fe29fa-…` 会话清理退出码 0。
- 这份整套测试的 status 仍是 **INCOMPLETE**，reported error 为 `home_terminal_header_known`；主控核对将该既有问题记入 T-219。这里只引用它实际证明的 Claude→a2a request→界面批准→主控状态旅程，不将整套测试改称 PASS，也不采用审查原文中不对应的“通过”理由。

未修改或复制 T-212-controller 内的文件；本人本轮没有调用真实供应商模型。

### 票面验收条目的当前状态

| 条目 | 当前状态与证据范围 |
| --- | --- |
| 修前真实入口的后台重启红态 | **PASS**：第一轮 red-02；本轮另有定向崩溃侧栏红态 red-03。 |
| 修后同一终端存活，屏幕与历史完整 | **INCOMPLETE**：pid、后台历史/输入流以及崩溃后的 inexact 标记通过；本轮实际 Electron 画面对照两次缺一行，不能称屏幕完整。 |
| 固定打包 hc、私有 core 与用户 core 隔离 | **INCOMPLETE（完整条目）**：本轮私有 core 与用户目录/进程隔离通过；包内启动仍是第二轮事实，本轮未重新打包或启动包内的新候选，不拿旧候选替新候选背书。 |
| 打字、粘贴、中文、Esc、Ctrl-C、用户输入记录 | **PASS（后台真实入口）**：round3-io-01，另有当前 T104/T121。未补称桌面按键自动化全覆盖。 |
| 实际 Claude 经 a2a request、界面批准，侧栏状态 | **PASS（主控已核对的该旅程证据）**：引用 t133-ctl-01；本轮 T107/T121 通过，新增崩溃侧栏检查通过。t133 整套 INCOMPLETE 的既有 header 项未上调。 |
| 包内 hc 二进制与 Apache-2.0 声明 | **PASS（已保存构件的静态事实）**：第二轮 package-03 的三个文件和许可；本轮打包/分发代码未改，未生成新安装包。 |
| 项目终端不再经过 node-pty 启动，没有第二条路径 | **PASS（代码与真实入口）**；保留的 pid 核对仅服务升级前记录，不是启动路径。 |
| agy 独立审查无未处理阻塞意见 | **INCOMPLETE**：第一轮 agy 结论为 INCOMPLETE；本轮已按主控核对修复并提供证据，最终候选尚待主控复审。 |

### 交接与未解决事项

- 本轮指定的侧栏修复、文档同步、不可达代码清理、升级记录说明和外置盘断言恢复已完成；六项要求的回归入口都已运行。
- 需要主控决定正常后台重启后的 xterm/hc 缺一行问题如何处理；本 worker 没有扩大到 T-220 的界面/reset 方案，也没有通过只保留绿态来宣布完成。
- 终端内 agent 抢先启动新 core 的环境继承仍为未知。新增绿态只证明本场景由重启后台启动的 core 使用其新环境。
- 最终证据检查、进程清理和项目地图结果附在第三轮证据中。前两轮的报告正文与异常现场保持原样；本轮失败与补清理同样保留。


## 第四轮

本轮指定的画面修复与收尾：**PASS**。确定性尺寸错配红态已转绿，原画面场景在本轮最终运行时代码上连续五次全部通过；新包启动与指定回归也全部通过。整张 T-212 仍为 **INCOMPLETE**，仅保留“最终候选经 agy 独立审查”的交接项，不能由 worker 自审代替。前三轮正文和失败证据原样保留。

### 根因核实

主控提出的尺寸错配机制成立。不是编号程序漏输出，也不是 hc 的历史少一行；错误发生在把按大尺寸生成的控制序列回放进小尺寸 xterm 时。

- 确定性场景在重启前经真实 `window_resize` 设为 193×120；后台 detach 后，hc 转为 headless 尺寸，接回时实测为 **200×120**。真实 Electron 自行拟合的 xterm 是 **159×49**，测试没有把两边预先调成相同尺寸。
- `round4-screen-red-01/after.raw` 最后一次 reset 后存在两组 home/clear，包含 `ESC[120;1H`，最大绝对光标行号为 120。实际 xterm 光标最后位于第 49 行（cursorY=48）。hc 文本含编号 1–460，xterm 只有 459 行，恰好缺 `编号-000459-中文`，最后的 460 仍在。这符合第 120 行光标被夹到第 49 行、随后实时编号覆盖原末行的机制；120−49=71 行也解释了空行区。
- 字节与尺寸摘要在 `round4-root-cause.json`，可用 `python3 ../T-212-evidence/round4-root-cause-probe.py` 重建。这里结合保存的控制字节和真实两端尺寸核实机制，没有声称运行了独立终端模拟器回放。
- 已核对 hc 0.1.15 的实际源码 `viewers.rs`：`viewer_resize` 改变尺寸但不发完整重绘；`attach` 先 `apply_size`，再 `first_paint`，其后才跟实时输出。T-211 没有证明“仅 resize 已保存的重绘就能跨尺寸回放”，不能由其正常接回结论推出这一点。未改 hc 源码。

### 根因层改动

本轮只修改了以下六个文件，之前轮次已接受的侧栏、角色和打包代码未再改变：

- `workbench/src/hc.ts`：RESIZE 后重新 attach，使用新尺寸取得完整重绘。先建立新 channel，再关闭旧 channel，避免先断开 viewer 导致中间转为 headless 尺寸。只有当前 channel 的 DATA 进入 trace；旧 channel 只归还 CREDIT 并等 CLOSE，应答不会被当作终端退出。连接失败/脱离按终端去重通知。
- `workbench/src/panes.ts`：每次新重绘开始，在追加式 trace 中记录 reset 偏移，再追加 reset；shell resize 与输入按既有写入队列排序，返回该重绘的偏移。已有 trace 不改写。
- `workbench/src/daemon.ts`：沿用唯一的 `window_resize` 入口，为 shell 返回 `output_offset`。受管窗格的 node-pty resize 路径不变。
- `workbench/app/renderer.tsx`：打开或再次显示项目终端时，即使拟合尺寸恰好相同，也请求当前尺寸下的新重绘；改变尺寸时同样处理。等待尺寸请求完成后，从返回的 reset 偏移继续用原 `pane_output` 读取。丢弃尺寸变更前已发起但尚未显示的旧块，重建 UTF-8 decoder，避免旧字节或半个字符拼入新重绘。没有新增显示接口、重试或兜底。
- `workbench/tests/test_t212_shell_hc_e2e.py`：文件头列出尺寸错配失败方式；新增 `--mismatched-screen`，保留真实 Electron 拟合尺寸，核对实际 hc 记录与 xterm 尺寸、完整编号历史。既有画面对照断言没有放宽。
- `workbench/README.md`：说明尺寸、重绘、偏移之间的顺序，并列出防止同类缺行再次出现的检查命令。

所有画面仍走 hc attach → 同一份追加 trace → `pane_output` → xterm。没有保留第二条显示路径。reset 仍服务完整重绘；本轮未增加 inexact UI 提示或改变 core 崩溃后的身份规则。

最终候选：基线 `4cb88bba7e36bd3e42a5ebc7815e8aa7c99a5ce3` 加 `candidate-round4-final.patch`。五连跑、回归和新包使用相同的运行时代码；之后只补了 README 中的检查入口说明。未 commit、未 push。

### 红态、绿态和五次连续原场景

以下命令从 T-212 worktree 执行。命令是对应历史运行的原入口；重跑须换成尚不存在的新证据目录，不能覆盖现有结果。

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output ../T-212-evidence/round4-screen-red-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output ../T-212-evidence/round4-screen-green-04
python3 ../T-212-evidence/run-screen-series-round4.py
```

- **红态证明 PASS**：`round4-screen-red-01` 在修复前退出码 1，失败原因是 xterm/hc 历史不一致，缺 459；清理 PASS。原始字节、两端文本、实际截图与完整 stdout 都保留。
- **同场景绿态 PASS**：`round4-screen-green-04` 退出码 0；打开前 hc 200×120，打开后真实 hc 记录和 xterm 均为 159×49；两边均为 **464 行**，无缺行、无多行。原 pid、离线输出、a2a 身份、OSC 7501、输入字节、查询一次应答和超过 512 KiB 的流控检查均通过。
- `round4-screen-green-01` 是更早的一次有效绿态。补充尺寸诊断时的 -02（误用不存在的 CLI `list`）与 -03（误以为 CLI `ls` 简化结果包含 cols）属于夹具错误，均原样保留，不当作产品红态或连续通过结果。改用固定版本支持的 `hc get` 读取实际终端记录后得到 -04。
- **原画面场景五连跑 PASS**：`round4-screen-series-01` 至 `-05` 顺序运行，中间没有修改运行时代码，退出码全为 0。两端逐行一致的行数依次为 **473、468、476、474、503**；每次 missing/extra 均为空。各目录保留 xterm buffer、hc read 文本、截图、run.json，stdout 位于同名 `.log`。`round4-screen-series.json` 记录每条完整 argv 与退出码。没有挑选通过运行，也没有跳过失败；这个五连跑序列没有失败。
- **运行中改变尺寸补测 PASS**：`round4-live-resize-01` 在真实 Electron 内只改变夹具窗格的布局尺寸，让产品 ResizeObserver 正常处理；程序继续输出 15 行以上再暂停。xterm 从 159×49 变为 **123×19**，hc/xterm **485 行**逐行一致。此项是实际布局缩小的补测，不冒称人工拖动原生窗口；它也不替代上述五连跑。重跑入口为 `TMPDIR=/private/tmp PYTHONPATH=workbench/tests python3 ../T-212-evidence/round4-live-resize-probe.py --electron-screen --output <新目录>`。

### 最终候选打包与包内启动

**PASS**。本轮重新打包，而非沿用第二轮产物：

```sh
TMPDIR=/private/tmp node workbench/app/package.mjs --slot t212-hc-round4-01 --variant test
TMPDIR=/private/tmp python3 ../T-212-evidence/round4-package-probe.py --app '/private/tmp/a2a-build-t212-hc-round4-01/Enchanted Test.app' --output ../T-212-evidence/round4-packaged-runtime-01
```

- `round4-package-01.log/json`：构建与 codesign 校验通过。包内包含 `herdr-core`、`LICENSE`、`THIRD-PARTY-NOTICES`；hc 和现有原生模块均为 ad-hoc 签名。产物在内置盘 `/private/tmp`，工作缓存/中间目录及 UI 中间 slot 均已由构建清理，没有链接构建输出目录。编译器和图标格式 warning 保留在原日志，不当作构建失败隐藏或另行扩大修复。
- `round4-packaged-runtime-01/run.json`：在隔离 HOME、数据目录和 UI 目录下启动实际打包 Electron，页面真实就绪。私有 core **pid 12966、ppid 1、版本 0.1.15**；`ps` 的进程路径准确指向 `/private/tmp/a2a-build-t212-hc-round4-01/Enchanted Test.app/Contents/Resources/app/hc/herdr-core`。
- 私有会话 `enchanted-6181fd54-2cbe-49aa-bfe4-f93b5d64f479`，socket `/private/tmp/enchanted-hc-MdkO10/core.sock`，都不连接用户 default core。
- 应用通过 `window.close` 正常窗口生命周期退出；随后停止隔离后台和该私有 core，清理 PASS，没有动用户应用。未使用 SIGKILL 代替本次正常退出证明。

### 指定回归、外置盘和收尾

| 入口 | 结果 | 本轮证据 |
| --- | --- | --- |
| `test_t212_shell_hc_e2e.py --core-crash` | **PASS** | round4-crash-01；两类侧栏 unknown、身份保持、两份终端的三个 inexact 断言与 core/holder 清理均通过。 |
| `test_t212_hc_boundaries_e2e.py` | **PASS** | round4-boundaries-01；损坏缓存报错不回退、含 holder 的长路径报错、XDG 未设置/原值/显式空值、环境隔离均通过。 |
| T104 | **PASS** | t104-round4.json/log，恢复的两条外置盘断言保持。 |
| T107 | **PASS** | round4-t107/summary.json、driver.json；脚本化 Claude 与真实 Electron，私有 core 清理退出码 0。 |
| T121 | **PASS** | round4-t121/summary.json、driver.json；私有 core 清理退出码 0。 |
| project-map status | **PASS** | project-map-round4-final.log：Problems 0、Stale living docs 0。 |
| `git diff --check` | **PASS** | diff-check-round4-final.log，退出码 0。 |
| 最终进程与 socket 核对 | **PASS** | round4-final-cleanup.json/log；本测试 core/holder 没有残留，包内应用后台/core socket 均不存在，用户 core 只读观察未变。 |
| 整个证据目录凭据边界 | **PASS** | round4-evidence-boundary.json/log；hc 私有状态文件 0、已知 token 明文匹配 0，扫描器拒绝合成的状态文件/明文 token 负例。 |

精确入口与日志：

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output ../T-212-evidence/round4-crash-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output ../T-212-evidence/round4-boundaries-01
TMPDIR=/private/tmp python3 workbench/tests/test_t104_shell_e2e.py --archive /Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-212/t104-round4 --summary ../T-212-evidence/t104-round4.json
python3 ../T-212-evidence/run-regressions-round4.py t107 t121
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
python3 ../T-212-evidence/round4-final-cleanup-check.py
python3 ../T-212-evidence/evidence-boundary-check-round4.py
```

T104 使用主控指定、运行前不存在的外置盘新目录 `t104-round4`，**17 文件、500932 字节**，清单见 `t104-round4.archive.json`。复制排除整个 hc 私有运行目录；夹具删除前以本次真实 token 集合检查该归档：私有状态文件 0、token 明文匹配 0。没有为了交付再保存明文 token，也没有用空 token 集合替代该检查。此归档不能覆盖重跑，新一轮需另行授权一个新路径。

用户 core 的证据仍严格使用三项：只读列出真实 home 的 hc 状态目录前后不变；用户 herdr-core 的 pid/启动时间不变；私有 socket 在用户目录之外。未连接用户 core，也未读取其终端列表。后台自身凭据仍仅存哈希；hc 的私有 restart_env 可能含明文 token，沿用主控已批准的取舍，私有运行目录永不进入证据。

### 票面验收条目的当前状态

| 条目 | 当前状态与依据 |
| --- | --- |
| 修前真实入口的后台重启红态 | **PASS**：第一轮 red-02；另有本轮确定性尺寸错配红态。 |
| 修后原程序存活，接回屏幕与历史完整 | **PASS**：确定性错配转绿，原场景连续五次完整对照；运行中缩小窗格补测也通过。core 崩溃仍诚实记为 inexact，不冒称历史完整。 |
| 固定包内 hc 启动私有 core，用户 core 隔离 | **PASS**：本轮新包的实际 core 进程路径与 0.1.15 版本；用户目录/pid/启动时间不变，私有 socket 在用户目录外。依主控裁定不连接 default core。 |
| 打字、粘贴、中文、Esc、Ctrl-C 与输入记录 | **PASS（真实后台输入入口）**：本轮错配场景和五次原场景均跑完字节、resize、查询、流控和输入记录检查，T104/T121 也通过。没有补称全部由桌面键盘自动化发送。 |
| 实际 Claude 的 a2a request、界面批准和侧栏 | **PASS（主控已核对的特定旅程）**：继续引用第三轮列明的 T-212-controller/t133-ctl-01，只引用它证明的旅程；其整套测试 INCOMPLETE 不改称 PASS。本轮 T107/T121 和崩溃侧栏检查通过，未调用真实模型。 |
| 包含 hc 二进制、Apache-2.0 和第三方声明 | **PASS**：本轮新包实际文件、许可正文与签名校验。 |
| 项目终端没有 node-pty 第二条启动路径 | **PASS**：本轮沿用单一 hc 路径；受管窗格不动，旧记录 PID 核对不是启动路径。 |
| 最终候选 agy 独立审查无未处理阻塞意见 | **INCOMPLETE**：主控已接受第三轮列明项目；本轮最终候选仍需主控安排 agy 复审。worker 不代替独立审查宣布此项通过。 |

### 未知、未跑与需要主控决定

- 本轮没有新增需要主控决定的范围、权限或验收条件。画面对照缺行已在本票范围内修复；最终候选与本轮证据交主控复审。
- core 崩溃后终端内 agent 率先拉起新 core 的环境继承风险仍是**未知**，不声称已解决；留给 T-220。当前崩溃场景只证明重新启动后台创建的新 core 继承它的环境。
- 未重新运行本轮未要求的 T184、T195、旧 daemon_recovery、旧 electron 全套；前轮已证明的父版本同样失败及 T-219 归属不因本轮绿态上调，也没有触碰 T-219 worktree。
- 未做真人供应商调用、发布、公证、安装到 /Applications、commit 或 push。未写主 checkout、T-216、T-219、T-212-controller 或用户的全局 CLI/hc 配置。只保留授权的源文件改动、证据、外置盘归档和隔离测试夹具。


## 第五轮

本轮三项修正与指定收尾：**PASS**。连续布局变化的真实 Electron 红态已转绿；项目终端才隐藏并等待重绘，受管窗格恢复即时 resize；后台每次重绘都重建 UTF-8 decoder 并清空 OSC carry。整票仍为 **INCOMPLETE**，第五轮候选的 agy 独立审查由主控安排，worker 未执行或替代该审查。前四轮正文原样保留。

主控本轮消息提供的独立证据另作来源标注：`T-212-controller/r4-mismatched-01` 491 行一致、`r4-screen-01` 502 行一致；`r4-mutant-no-reattach-01` 恢复为只发 RESIZE 后缺 `编号-000501-中文`。这是主控运行 `run-ctl-r4.sh` 的结果，本人没有在该目录写入或重新运行它。

### 先列失败方式，再写断言

修改生产行为前，已在 `test_t212_shell_hc_e2e.py` 文件头追加以下失败方式，并先运行连续改尺寸红态：

1. 连续布局变化每次都取含全部历史的重绘，导致 trace 随拖动像素级增长。
2. 合并时丢掉最终尺寸，或只记住第一次尺寸，最终 hc 与 xterm 不同。
3. 旧块、旧重绘和随后实时输出交错，造成缺行、多行或顺序错乱。
4. shell 的隐藏、重绘偏移等待和 decoder 重建误用于受管窗格，改尺寸时闪“恢复中”。
5. 新重绘沿用旧流的半个 UTF-8 字符或未结束的 OSC carry，污染新流的解析状态。

连续变化场景经真实 Electron 改动夹具窗格布局 24 次，每次间隔 25 ms；观察实际 xterm 尺寸，要求至少 20 个不同尺寸。之后在最后一次重绘可能尚未完成时恢复程序输出，继续至少 20 行，再暂停做完整对照。预先设定重绘预算至多 3 次（24 次变化的八分之一），不是从修复结果反推阈值；测试同时核对最终尺寸和逐行文本。

### 生产改动与范围

- `workbench/app/renderer.tsx`：以启动记录的 shell 角色限定重绘处理。受管窗格继续沿原路径立即调用 resize、异步处理失败，不设置隐藏、不等重绘偏移、不重建 decoder。项目终端的 fit 只更新最新待处理尺寸，布局稳定 150 ms 后由原读取循环发送；同一循环保证最多一个尺寸请求在途，期间的新尺寸覆盖待处理值。尚未稳定或已有更新时不显示旧块，最后从当前重绘偏移继续读取。没有加入重试、兜底或第二条显示路径。
- `workbench/src/panes.ts`：`paint` 开始时重新创建 `StringDecoder("utf8")`、清空 `pane.oscCarry`，然后记录偏移、写 reset。没有清掉既有 CLI 回合状态，也没有改变角色、生命周期、关闭或凭据行为。
- `workbench/tests/test_t212_shell_hc_e2e.py`：新增 `--resize-burst` 真实 Electron 场景及失败方式；成功且清理确认的主场景、崩溃场景在证据与 token 检查完成后删除自己的夹具，失败现场保留。
- `workbench/tests/test_t107_live_sidebar_e2e.py`：真实可写 worker 窗格连续改变布局 24 次，用 MutationObserver 核对 `data-restoring` 无变化；增加 `managed-resize-hidden` 反例，恢复受管分支的隐藏行为，证明该检查会拒绝坏实现。变异副本显式使用现有 hc 缓存，不访问用户 core。
- `workbench/tests/test_t212_hc_boundaries_e2e.py`：成功、清理和凭据检查完成后删除本次边界夹具。
- `workbench/README.md`：同步 shell 的稳定尺寸合并、单个在途请求、重绘解析状态和受管窗格即时 resize 的实际规则。

本轮未改 hc.ts、daemon.ts、打包脚本、分发 pin、角色或侧栏实现。`candidate-round5-final.patch` 保存基线 `4cb88bba7e36bd3e42a5ebc7815e8aa7c99a5ce3` 上的完整最终候选；之前候选保留。未 commit、未 push。

### 连续改尺寸：真实入口红态与绿态

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --resize-burst --output ../T-212-evidence/round5-burst-red-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --resize-burst --output ../T-212-evidence/round5-burst-green-01
```

- **红态证明 PASS**：在第四轮运行时代码上，24 次布局变化观察到 24 个不同 xterm 尺寸，trace **新增 24 个 reset**。最终两端尺寸 149×19，483 行逐行一致；唯一失败是“24 次变化产生 24 次全历史重绘，要求至多 3 次”。退出码 1，清理 PASS，失败夹具保留。
- **同场景绿态 PASS**：24 次布局变化、24 个不同尺寸，trace **只新增 1 个 reset**。最终 hc 与 xterm 都为 **149×19**，继续输出后的 **507 行**逐行一致，无缺行、多行；退出码 0，完成全部输入/流控/a2a 检查，成功夹具已删除。
- 记录来自实际 trace 的 reset 计数、真实 xterm 对象、hc get/read，不是生产代码里的计数器。两份运行都保留实际 buffer、hc 文本、截图、run.json 和 stdout；没有改变尺寸来掩盖错配。

### 受管窗格：反例与回归

`round5-t107-mutant/summary.json` 使用隔离副本恢复受管 resize 的隐藏行为：实际可写 worker 窗格 24 次布局变化，观察到 12 次 `data-restoring` 属性转换，即 6 次进入恢复状态；测试恰好在 `managed_resize_does_not_hide_or_restore` 拒绝。它是定向坏实现反例，不冒称重新运行了整个第四轮候选。

`round5-t107/summary.json` 在最终候选上 **PASS**：同样 24 次变化、24 个不同宽度，`restoring_changes: []`。原有两个 worker、审查员层级、运行/空闲、角色状态、分支计数和点击聚焦流程也全部通过。两次测试只调用本地脚本化供应商接口；两份专属 core 清理退出码均为 0。

实际驱动入口：

```sh
TMPDIR=/private/tmp python3 ../T-212-evidence/run-regressions-round5.py t107-mutant
TMPDIR=/private/tmp python3 ../T-212-evidence/run-regressions-round5.py t107 t121
```

对应完整 argv、退出码与清理记录在各目录 driver.json。变异运行的失败夹具保留；正常 T107/T121 和驱动私有副本清理后已核对不存在。

### 后台解码边界：证据及限制

本轮**没有构造出确定性的 hc 真实传输入口坏状态**。hc 的 Relay 会暂存尚未完成的 escape 序列，DATA 帧/credit 的分片时序又会影响旧流具体停在哪里；不能将隔离注入的边界当作真实 core 已复现“吞掉报告”。

改用 `round5-decoder-boundary-probe.mjs` 对生产 `attachShell` 注册的真实回调做隔离探针，只有终端 transport 和最小 store 被替身替代。先送入未结束的 OSC 前缀及 UTF-8 首字节，再触发 paint，随后送入独立的新重绘及完整 working 报告。探针观察真实 StringDecoder 的返回值、carry 和解析出的回合：

- `round5-decoder-red-01`：重绘后 carry 仍为旧前缀，新流解码混入旧半字符的替换字符；`osc_carry_cleared`、`utf8_decoder_fresh` 均 false。
- `round5-decoder-green-01`：carry 为空，新重绘字节独立解码，两项均 true，完整报告解析也为 true。
- **原实现对该探针里的完整新 OSC 报告本来就能解析成功**；没有把此项说成已复现报告被吞。PASS 的范围是解码状态在边界归零及新的完整报告仍能解析；真实传输下具体污染后果仍无确定性复现。

重跑入口如下；输出目录需换成新目录：

```sh
TMPDIR=/private/tmp node ../T-212-evidence/round5-decoder-boundary-probe.mjs ../T-212-evidence/round5-decoder-red-01
TMPDIR=/private/tmp node ../T-212-evidence/round5-decoder-boundary-probe.mjs ../T-212-evidence/round5-decoder-green-01
```

红态命令记录的是修复前候选上的历史运行，不能把修复后的同一命令误当作仍应失败。探针源码在运行前已列失败方式，红/绿 stdout 和 JSON 都保留；红态的微型夹具保留，绿态已删除。最终候选还通过下述真实入口 OSC 7501、输入和画面回归，未以隔离探针替代端到端验收。

### 最终候选复验

| 入口 | 状态 | 实际结果与证据 |
| --- | --- | --- |
| 尺寸错配场景，连续三次 | **PASS** | round5-mismatched-01/02/03，**458、459、461 行**分别一致，missing/extra 全空。 |
| 原画面场景，连续三次 | **PASS** | round5-screen-01/02/03，**461、481、482 行**分别一致，missing/extra 全空。 |
| 第四轮运行中缩小窗格脚本 | **PASS** | round5-live-resize-01；159×49 → 123×19，**479 行**一致，程序继续输出。 |
| `--core-crash` | **PASS** | round5-crash-01；两类侧栏 unknown、身份保持、inexact 事件/status/reattach 与 core/holder 清理均通过。 |
| 边界测试 | **PASS** | round5-boundaries-01；损坏缓存不回退、长 holder 路径报错、XDG 未设置/原值/显式空值与隔离检查通过。 |
| T104（本轮补跑） | **PASS** | t104-round5.json/log；因改到它覆盖的 attach 回调而补跑，没有使用豁免跳过。 |
| T107、T121 | **PASS** | round5-t107、round5-t121；各 driver 清理退出码 0。T107 含新增受管窗格无闪动检查。 |
| project-map status | **PASS** | project-map-round5-final.log：Problems 0、Stale living docs 0。 |
| `git diff --check` | **PASS** | diff-check-round5-final.log，退出码 0。 |
| 夹具、后台服务与用户 core | **PASS** | round5-final-cleanup.json/log；成功夹具均不存在，本轮失败现场保留，本轮 core/holder/后台无残留；用户目录及 pid/启动时间只读比较未变。 |
| 证据与 token 边界 | **PASS** | 每次成功夹具删除前已用真实 token 集合扫描本次证据；最终 round5-evidence-boundary.json/log 再检查整个证据目录，状态文件 0、已知 token 明文匹配 0，合成负例均被拒绝。 |

六次画面复验在最终运行时代码上顺序执行，没有失败或挑选。每次均完成原 pid/离线历史、a2a 命令、OSC、输入字节、resize、查询一次应答、超过 512 KiB CREDIT 流控与输入记录断言；实际 buffer、hc 文本和截图保留。汇总见 round5-screen-series.json、round5-screen-summary.json。

主要入口（当前已有输出均不可覆盖，重跑应使用新输出名）：

```sh
TMPDIR=/private/tmp python3 ../T-212-evidence/run-screen-series-round5.py
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output <新目录>
TMPDIR=/private/tmp PYTHONPATH=workbench/tests python3 ../T-212-evidence/round4-live-resize-probe.py --electron-screen --output ../T-212-evidence/round5-live-resize-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output ../T-212-evidence/round5-crash-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output ../T-212-evidence/round5-boundaries-01
TMPDIR=/private/tmp python3 workbench/tests/test_t104_shell_e2e.py --archive /Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-212/t104-round5 --summary ../T-212-evidence/t104-round5.json
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
python3 ../T-212-evidence/round5-final-cleanup-check.py
python3 ../T-212-evidence/evidence-boundary-check-round5.py
```

T104 使用指定、运行前不存在的外置盘目录 `t104-round5`，**17 个文件、501096 字节**，清单 t104-round5.archive.json。外置盘断言保留；整个 hc 私有运行目录排除，归档以本次真实 token 集合核对状态文件 0、明文匹配 0，再删除私有夹具。现有归档不可覆盖，后续新路径须另行授权。

### 成功夹具清理与失败现场

成功主场景、崩溃、边界与解码探针在自己的证据检查后删除夹具；T104 自带归档后清理；回归驱动在停止专属 core、复制选定文本证据及扫描 token 后删除成功夹具和原始驱动副本。第四轮 live-resize 脚本仍保留它原有的成功现场行为，本轮已在检查其 PASS/清理退出码后单独删除该成功夹具，没有改写第四轮脚本。

本轮仅保留以下失败现场（服务均已停止，不复制其中 hc 私有状态到证据）：

- `/private/tmp/t212-juw1pmy1`：第四轮候选的连续改尺寸红态。
- `/private/tmp/t212-decode-3ZuAVp`：隔离解码边界红态。
- `/private/tmp/t107-_cfs8l99`：受管窗格隐藏变异被拒绝的完整夹具。
- `/private/tmp/t212-regression-w8d03_yh/t107-mutant`：该变异的原始驱动日志/私有清理副本。

成功夹具完整清单与只读复核在 round5-final-cleanup.json；没有清理或改写前轮失败现场。没有操作用户 default core，只比较用户状态目录列表、进程 pid/启动时间和本轮私有 socket 的目录边界。

### 票面验收条目的当前状态

| 条目 | 当前状态与证据范围 |
| --- | --- |
| 修前后台重启导致原程序结束的真实入口红态 | **PASS**：第一轮 red-02；本轮另有重绘次数真实红态与受管隐藏坏实现反例。 |
| 修后原程序存活，屏幕和历史完整 | **PASS**：错配三次、原场景三次、连续变化及运行中缩小均通过；core 崩溃仍明确标 inexact。 |
| 固定包内 hc 启动私有 core、用户 core 隔离 | **PASS（主控已接受的第四轮打包事实及本轮隔离回归）**：本轮未改打包相关文件，依本轮指令不重新打包；未声称已有包含第五轮改动的新包启动证据。 |
| 打字、粘贴、中文、Esc、Ctrl-C、输入记录 | **PASS（真实后台入口）**：六次画面场景均运行全部字节/输入记录检查，T104/T121 通过；未补称全部来自桌面键盘自动化。 |
| 真实 Claude 的角色申请、界面批准、侧栏状态 | **PASS（主控已核对的指定旅程）**：继续引用第三轮 t133-ctl-01 的限定证据；本轮脚本化 T107/T121、崩溃状态及受管 resize 无闪动均通过。未将 t133 整套测试上调。 |
| 包内 hc、Apache-2.0 许可与第三方声明 | **PASS（第四轮实际构件静态事实）**：本轮未改打包文件或许可，按指令不重包。 |
| shell 无 node-pty 第二条启动/显示路径 | **PASS**：仍经同一 hc/trace/pane_output；受管 node-pty resize 已恢复第三轮行为。 |
| agy 独立审查无未处理阻塞意见 | **INCOMPLETE**：主控正在安排第四轮审查、第五轮另行送审；本人未代审或宣称该项通过。 |

### 未知与未跑检查

- 解码边界没有确定性的 hc 真实传输红态；隔离探针证明的范围与未复现的报告吞失已在上文区分，未把它写成端到端通过。
- core 崩溃后终端内 agent 首先拉起新 core 的环境继承仍未知，留给 T-220；本轮没有扩大到该风险或修改其恢复规则。
- 未重新打包，依据主控本轮明确豁免；未改 package.mjs/hcDistribution。第四轮应用包仍是第四轮内容，不冒充第五轮构件。
- 未重跑本轮未要求的 T184/T195/旧 daemon_recovery/旧 electron；既有 T-219 问题不因本轮通过而上调。本轮未触碰 T-216、T-219、T-221 或 T-212-controller。
- 本轮没有新增需要主控裁定的范围或权限问题。全部授权工作已完成，剩余是主控组织的独立审查。没有真实供应商调用、全局 CLI/hc 配置写入、主 checkout 修改、commit 或 push。


## 第六轮

本轮两项修正与最终收尾：**PASS**。真实入口的 trace 写失败红态转绿，初次 attach 与 resize 均明确拒绝且不拖垮另一个终端；意外 RPC 回调异常也不再留下悬挂的调用。尺寸错配、原画面、连续改尺寸各两次及全部指定回归通过。最终候选重新打包、包内启动、正常退出与私有 core 清理均通过，核验后的应用包已依指令删除。整票仍为 **INCOMPLETE**，仅剩由主控安排的最终独立审查，worker 未代审。前五轮正文原样保留。

本轮只读了 `T-212-controller/REVIEW-agy-r2.md` 及主控核对记录，以代码和原始运行结果为准。不采用核对记录已指出的不成立的游标并发、尺寸与行号引用；没有重做第五轮已经接受的方案，也没有写入 controller 目录。

### 失败方式清单与根因

生产修复前，新建 `workbench/tests/test_t212_trace_failure_e2e.py`，在文件头先列明：

1. paint 回调抛错时，attach 已离开 pending 表，却既未 resolve 也未 reject；resize 请求和写入队列悬挂。
2. trace IO 异常逸出到共享连接的接收处理，另一个项目终端也被标为 hc_connection_lost，失去输入能力。
3. 仅捕获 IO 错误却仍返回成功或旧重绘偏移，没有明确标记目标窗格失败。
4. 初次 attach 的 paint 出错时仍悬挂/误报成功，或损害别的终端。
5. 后续输入继续卡住，以及测试没有恢复权限、清理自己的后台/core/holder。

原因核实：`HcConnection.reply()` 先清 timer、删除 pending，再执行同步 accept 回调。paint 内无保护的 stat/append 一旦抛错，调用不在 pending 中，后续 fail 无法拒绝它，而 socket 接收处理会销毁整条连接。不是 core 自身退出：红态里私有 core socket 仍在，坏的是后台共享 viewer 连接与悬挂的 Promise。

### 最小修复与返回类型

本轮改动：

- `workbench/src/panes.ts`：paint 的 stat/reset 追加按既有 DATA 写入的规则捕获 IO 错误，调用 `recordFailure(pane, "trace_write_failed", error)`；只有 reset 真正写入后才发布新的偏移。`attachShell` 在初次 attach 后、`resizeShell` 在 resize 后检查 failed，失败就返回标准 `pane_unavailable` 拒绝，不返回成功或旧偏移。写入队列仍用既有结算规则释放。
- `workbench/src/hc.ts`：accept 回调若意外抛错，先 reject 当前已经离开 pending 的调用，再继续抛错使连接按既有规则失败。这里不把未知回调 bug 当作正常连接；正常 trace IO 异常已由窗格层处理，不会走到这条共享连接失败路径。这样既不吞掉未知协议/内部错误，也不会留下无法被 fail 结算的 Promise。
- `workbench/app/renderer.tsx`：`resize` 声明改为 `Promise<{ ok: true; output_offset?: number }>`，与实际成功回执一致；没有改变第五轮的布局合并与显示行为。
- `workbench/tests/test_t212_trace_failure_e2e.py`：两个真实项目终端，分别覆盖现有窗格 resize 和新终端初次 paint；3 秒请求上限，权限恢复、独立终端执行命令、后续拒绝、后台/core 清理和凭据边界检查。
- `workbench/README.md`：同步 trace IO 的窗格隔离、初次 attach/resize 拒绝和 RPC 调用结算规则。

没有增加重试、兜底、平行显示 API 或受管窗格的新路径；没有修改打包流程或固定版本 pin。最终候选是基线 `4cb88bba7e36bd3e42a5ebc7815e8aa7c99a5ce3` 加 `candidate-round6-final.patch`，本轮所有绿态和新包对应相同的最终运行时代码。未 commit、未 push。

### 真实入口红态与绿态

以下为实际运行命令，从 T-212 worktree 执行。对应目录已存在，重跑需使用新目录，不能覆盖失败证据。

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t212_trace_failure_e2e.py --case resize --output ../T-212-evidence/round6-trace-resize-red-02
TMPDIR=/private/tmp python3 workbench/tests/test_t212_trace_failure_e2e.py --case initial --output ../T-212-evidence/round6-trace-initial-red-03
TMPDIR=/private/tmp python3 workbench/tests/test_t212_trace_failure_e2e.py --case resize --output ../T-212-evidence/round6-trace-resize-green-02
TMPDIR=/private/tmp python3 workbench/tests/test_t212_trace_failure_e2e.py --case initial --output ../T-212-evidence/round6-trace-initial-green-02
```

**红态证明 PASS**：

- resize 红态在第五轮候选上把第一个终端的 pty.raw 设为 0400，再经 `window_resize` 触发新 paint。请求 **3.001 秒**超时；目标和另一个终端的 failed 都为 `hc_connection_lost: ... EACCES`，另一个终端输入被拒绝，目标后续输入也在 **3.001 秒**超时。私有 core socket 仍存在。
- 初次 attach 红态用夹具内的文件监视线程在新 trace 创建、尚为 0 字节时设置 0400，不改产品代码；确认初次 paint 没有抢先写入。`shell_start` 同样在 **3.001 秒**超时，新窗格和另一个已有窗格都失效。
- 两种坏候选的挂起队列也阻止正常 shutdown；测试先恢复原 0600 权限，发 daemon_stop 等待自己的 3 秒清理期限，仍未退出才仅 SIGKILL 本次 detached daemon，随后显式停止自己的私有 core。红态的这种强制清理不被写成“正常后台退出”。最终清理均 PASS，无残留服务。

**同场景绿态 PASS**：

- resize 和初次 attach 均在请求上限内返回 `{ok:false,error:"pane_unavailable"}`；目标 status.failed 以 `trace_write_failed:` 开头，另一个窗格保持 running 且 failed 为 null，并真实执行 `print` 写出 intact 文件。
- resize 场景里，目标的后续输入也及时返回 pane_unavailable，说明队列不再悬挂；没有返回旧 output_offset。共享 hc 连接保持可用，而非另拉一个 core 或重连兜底。
- 权限恢复为 0600；两种绿态都通过正常 daemon_stop 和私有 core 停止完成清理。成功夹具在检查真实 token 集合后的证据边界后删除。
- 最终有效绿态是 `*-green-02`。`*-green-01` 也有相同功能通过，但其新测试的扫描顺序是在写 run.json 前检查空目录；已纠正为先写实际结果、再用真实 token 检查，重跑 -02，checked_files 为 1。未拿空目录扫描替代最终证据，也未覆盖早期结果。

早期夹具错误保留、不计为合格红态：两个 `*-red-01` 错把 zsh 的 prompt 格式串当作字面 `TRACE%` 等待；改为经真实窗口输入准备命令确认终端就绪。`initial-red-02` 在权限注入后错取事件里不存在的 thread 字段；改为按事件的 launch id 从本夹具追加式启动记录只读取身份，再经真实 pane_status 查询。它们没有被删除或改称产品通过。

本次注入的是 **trace 文件 EACCES**，没有把用户内置盘实际写满。stat 和 append 都在同一个保护范围内；未额外注入 stat 的 ENOENT，也未检验整盘 ENOSPC 导致事件库自身写入失败的情况。事件记录自身失败仍沿用原有规则，本轮没有扩大到存储故障恢复方案。

### RPC accept 异常的结算探针

为核对 `reply()` 的判断，补充 `round6-reply-settlement-probe.mjs`：用真实隔离 hc core，直接调用内部 RPC 的 terminal.list，并让 accept 抛出已知 sentinel。它不是用户入口的替代，只核对这一次 Promise 的可观察结算。

- `round6-reply-red-01`：修复前 **1 秒**观察期限内未 resolve/reject，outcome 为 timed_out。
- `round6-reply-green-01`：修复后 outcome 为 rejected，错误准确为 `T212_CALLBACK_SENTINEL`，没有伪装成 success。未知回调 bug 仍会触发原有连接失败规则；普通 trace 写失败已由上面的真实入口证明不会破坏其他终端。
- 两次都显式停止自己的私有 core；红态现场保留，绿态夹具已删除。

```sh
TMPDIR=/private/tmp node ../T-212-evidence/round6-reply-settlement-probe.mjs ../T-212-evidence/round6-reply-red-01
TMPDIR=/private/tmp node ../T-212-evidence/round6-reply-settlement-probe.mjs ../T-212-evidence/round6-reply-green-01
```

红态命令是修复前候选的历史入口，不代表在最终候选上仍应失败。

### 最终候选复验结果

| 入口 | 状态 | 证据与观测 |
| --- | --- | --- |
| 尺寸错配场景两次 | **PASS** | round6-mismatched-01/02，**490、466 行**分别逐行一致，missing/extra 全空。 |
| 原画面场景两次 | **PASS** | round6-screen-01/02，**487、535 行**分别一致，missing/extra 全空。 |
| 连续改尺寸场景两次 | **PASS** | round6-burst-01/02；各 24 次变化只新增 **1 次重绘**，最终两端 149×19；继续输出后的 **531、506 行**分别逐行一致，无缺行、多行。 |
| `--core-crash` | **PASS** | round6-crash-01；侧栏 unknown、身份保持、inexact 事件/status/reattach 及清理均通过。 |
| 边界测试 | **PASS** | round6-boundaries-01；坏缓存、长 holder 路径、XDG 未设置/原值/空值、私有环境与用户 core 比较均通过。 |
| T104 | **PASS** | t104-round6.json/log；指定新外置盘路径，外置盘断言与 trace/token 排除保留。 |
| T107 | **PASS** | round6-t107/summary.json、driver.json；包含 24 次受管布局变化、restoring_changes 为空的检查；私有 core 清理退出码 0。 |
| T121 | **PASS** | round6-t121/summary.json、driver.json；私有 core 清理退出码 0。 |
| project-map status | **PASS** | project-map-round6-final.log：Problems 0、Stale living docs 0。 |
| `git diff --check` | **PASS** | diff-check-round6-final.log，退出码 0。 |

六次画面场景按固定顺序执行，没有失败或挑选。每次都跑完原 pid、离线历史、a2a 命令、OSC、输入字节、改尺寸、一次查询应答、CREDIT 流控与用户输入记录检查。实际 xterm buffer、hc read 文本、截图、stdout 与 JSON 都保留；汇总见 round6-screen-series.json、round6-screen-summary.json。

实际入口：

```sh
TMPDIR=/private/tmp python3 ../T-212-evidence/run-screen-series-round6.py
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --resize-burst --output <新目录>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output ../T-212-evidence/round6-crash-01
TMPDIR=/private/tmp python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output ../T-212-evidence/round6-boundaries-01
TMPDIR=/private/tmp python3 workbench/tests/test_t104_shell_e2e.py --archive /Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-212/t104-round6 --summary ../T-212-evidence/t104-round6.json
TMPDIR=/private/tmp python3 ../T-212-evidence/run-regressions-round6.py t107 t121
```

T104 使用主控指定、运行前不存在的新外置盘目录 **t104-round6**，17 个文件、**500998 字节**，清单 t104-round6.archive.json。复制排除整个 hc 私有目录，夹具删除前用本次真实 token 集合扫描归档，状态文件 0、token 明文匹配 0。现有归档不可覆盖，重跑需要另行授权的新归档路径。

### 最终候选重新打包、包内启动与产物删除

**PASS**。本轮重新构建与打包，未复用第四轮产物：

```sh
TMPDIR=/private/tmp node workbench/app/package.mjs --slot t212-hc-round6-01 --variant test
TMPDIR=/private/tmp python3 ../T-212-evidence/round4-package-probe.py --app '/private/tmp/a2a-build-t212-hc-round6-01/Enchanted Test.app' --output ../T-212-evidence/round6-packaged-runtime-01
python3 ../T-212-evidence/round6-remove-verified-package.py
```

- `round6-package-01.log/json` 记录构建、hc 0.1.15、三个随包文件和 ad-hoc 签名校验；包含 herdr-core、LICENSE、THIRD-PARTY-NOTICES，许可正文核对含 Apache License。编译器/图标格式 warning 保留，不冒称没有 warning。构建缓存、中间 work 目录和 UI slot 均在内置盘临时目录并已清理，没有链接构建输出目录。
- `round6-packaged-runtime-01/run.json` 记录隔离 HOME/数据/UI 目录内的真实打包 Electron 页面。私有 core **pid 10600，ppid 1，版本 0.1.15**；实际进程路径为 `/private/tmp/a2a-build-t212-hc-round6-01/Enchanted Test.app/Contents/Resources/app/hc/herdr-core`，socket `/private/tmp/enchanted-hc-XlyXPC/core.sock`，位于用户目录之外。
- 应用经 `window.close` 正常窗口生命周期退出，随后正常停止本次后台和私有 core，没有用 SIGKILL 冒充本次正常退出。用户 core 的目录列表、pid/启动时间前后不变。
- 删除前逐字比较包内 src/hc.ts、src/panes.ts 与最终 worktree 源码，两份都一致；没有用旧包为最终候选背书。
- 只在上述 PASS、正常退出、core pid 不存在、包内进程无残留后删除整个 `/private/tmp/a2a-build-t212-hc-round6-01` 和本次隔离启动夹具。`verified_artifact_removed`、`build_slot_removed`、`successful_fixture_removed` 均为 true；删除日志见 round6-remove-verified-package.log。历史命令中的应用路径现在不存在，复验需重新用新 slot 打包，不能将它当作仍保留的可启动应用。

### 清理、证据边界与失败现场

成功夹具全部清理，最终核对见 round6-final-cleanup.json/log；本轮 core、holder、编排后台没有残留，包内 core 和应用进程均退出。新故障测试在任何停止/删除操作前把权限恢复为原 0600。没有删除前轮现场。

本轮保留的失败现场：

| 路径 | 原因 |
| --- | --- |
| `/private/tmp/t212-trace-mlp0i9g3` | 有效 resize 红态；悬挂请求及跨窗格连接故障。 |
| `/private/tmp/t212-trace-83cm6qpn` | 有效初次 attach 红态。 |
| `/private/tmp/t212-reply-f34y13` | 内部 RPC accept 异常悬挂红态。 |
| `/private/tmp/t212-trace-gmq7mf92`、`/private/tmp/t212-trace-vud88ux_` | 两次早期 prompt 字面等待错误，不计为合格红态。 |
| `/private/tmp/t212-trace-dvsk8oth` | 初次注入后误取 thread 的夹具错误，不计为合格红态。 |

这些目录的私有 hc 运行状态不进入证据。各测试/回归在仍持有实际 token 集合时检查自己的文本证据，再删除成功夹具；最终 `round6-evidence-boundary.json/log` 再检查整个交付目录，私有 hc 状态文件 **0**、已知 token 明文匹配 **0**，两项合成坏产物均被拒绝。用户 core 只做真实 home 的只读列目录及进程 pid/启动时间比较，不连接 default core，不读其终端列表；私有 socket 均在用户目录外。

最终核对入口：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git diff --check
python3 ../T-212-evidence/round6-final-cleanup-check.py
python3 ../T-212-evidence/evidence-boundary-check-round6.py
```

### 票面验收条目的当前状态

| 条目 | 当前状态与证据范围 |
| --- | --- |
| 修前真实入口的后台重启红态 | **PASS**：第一轮 red-02；本轮追加了 trace 故障的真实入口红态。 |
| 修后原程序存活，屏幕和历史完整 | **PASS**：最终候选的错配、原画面、连续尺寸场景各两次；trace 故障仅拒绝坏窗格，另一个终端可用。core 自身崩溃仍记 inexact。 |
| 打包固定 hc 启动私有 core，与用户 core 隔离 | **PASS**：本轮最终候选重新打包并核对包内实际进程路径、0.1.15 版本及三项用户 core 隔离证据。核验后产物按指令删除。 |
| 打字、粘贴、中文、Esc、Ctrl-C、输入记录 | **PASS（真实后台输入入口）**：六次完整场景及 T104/T121；未冒称全部由桌面键盘自动化输入。 |
| 实际 Claude 角色申请、界面批准及侧栏状态 | **PASS（主控已接受的指定旅程证据）**：继续引用第三轮 t133-ctl-01 的限定事实，不上调其整套结果；本轮脚本化 T107/T121、崩溃与受管 resize 状态检查通过。 |
| 包内 hc、Apache-2.0 许可、第三方声明 | **PASS**：本轮新包实际文件、许可内容和签名校验，删除前已核实。 |
| shell 没有 node-pty 第二条路径 | **PASS**：仍是唯一 hc/trace/pane_output 路径，受管窗格保持 node-pty，本轮未新增兼容或回退路径。 |
| agy 最终独立审查无未处理阻塞意见 | **INCOMPLETE**：按主控本轮要求修正两处并完成最终证据；最终候选的独立审查由主控安排，worker 未替代。 |

### 未知与未跑检查

- 未实际填满磁盘，也未注入事件库同时写失败；本轮证明 trace 文件的 EACCES 路径与请求结算，不扩大成对所有存储故障的保证。
- 第五轮已接受的解码边界仍只有隔离探针，未补称新的真实传输确定性红态；本轮没有改那套解码方案。
- core 崩溃后终端内 agent 率先拉起新 core 的环境继承仍未知，留给 T-220；没有扩大处理范围。
- 未新增全仓 tsc 检查或依赖；本轮修正声明，实际应用构建和运行通过。不将 Vite 构建当作全仓严格类型检查。
- 未重跑本轮未要求的 T184/T195/旧 daemon_recovery/旧 electron 全套；旧问题不因本轮绿态上调。未调用真实供应商模型、安装到 /Applications、发布、公证、commit 或 push。
- 本轮全部授权工作已完成，没有新增需要主控决定的范围或权限事项。只写 T-212、T-212-evidence、指定 t104-round6 外置盘归档与自身 /private/tmp 夹具；未写主 checkout、T-216、T-221、T-222、T-224、T-212-controller 或用户全局 CLI/hc 配置。
