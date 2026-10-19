# T-104 / a1 第一段交接

状态：**INCOMPLETE**。后台普通终端的真实端到端场景已通过；两项既有回归的夹具问题已定位并修正，基线和候选对照均通过。完整检查等待 `backend-03`；提交、独立审查及第二段 Electron 验证尚未完成。本文不作为整票通过结论。

## 绑定与范围

- 日期：2026-10-19；task / attempt：T-104 / a1；ticket ready_rev：1。
- 分支：`exec/t104`；起点：`cc18d93dbbcf2ee641dc92befe68e5b0609b4807`。
- worker：`s17-t104`；session：`8fbb58f9-18ea-43e8-a0e3-facbc7edcaad`；原生会话：`01a1527f-e702-7c20-9ee3-6758a25c911c`。
- launch：`launch-04f00c94021d4e9c9618c151af840bde`；Herdr pane：`wF:p60`。启动记录为 Codex CLI 0.163.0、gpt-6.1-sol、xhigh、请求 default；不据请求配置推断实际供应商 tier。
- 当前派发逐字引用用户：`选"A 先补功能再打包"`。主控随后明确本阶段按 Herdr 提交交接，不调用 submit，没有门禁 state、fence、spec_rev、结构化任务卡或 oracle_paths；不伪造这些字段。
- 目标：**Tracer bullet** 先贯通真实 CLI／daemon／PTY／用户 zsh／关闭与恢复；第一段不改 UI。**Deep modules**：复用现有窗格、窗口身份、事件流与 transport，不增加另一套门禁。**Ubiquitous language**：沿用项目、任务、窗格、launch、attempt；普通终端以 `role: shell` 区分。
- 非目标：模型调用、门禁核心或操作锁改造、用户全局配置、push、问题面板、多标签管理、自动续接普通 shell。
- 分段边界：未改 `app/renderer.tsx`、`app/preload.ts`、`app/main.ts`、`app/start.mjs`。等待 T-103 合入及主控明确通知后才开始第二段。

## 实现

`panes.ts` 增加项目级 shell 窗格，启动 `/bin/zsh -l -i`，cwd 取现有绝对目录的规范路径；只注入 `A2A_PROJECT`，不传模型参数、launch 凭据或受管身份。launch 的 task、attempt、session、fence、spec_rev 为空。SQLite 启动记录的 task 列随既有事务迁移为可空，保留旧记录及追加式约束。

新增 `shell_start --project ID --cwd ABS`、`shell_close --launch ID`；`pane_layout --project ID` 查询项目打开集。后台处理仍经现有 transport／daemon；未改 `gates/core.ts`、操作锁、claim、submit、验收或集成语义。`shell_created`、`shell_closed` 记在既有事件流，数据带 `role: shell`。

输入复用窗口凭据与单调序号，但 shell 分支直接送到 PTY，不进入 agent 的输入记录器、派发队列或人工介入。通用窗口请求日志只保存命令、序号、request_id，避免在成功或拒绝路径先把输入载荷写入事件流。agent 的专用用户输入记录、原生身份核对和人工介入路径保持原有逻辑。PTY 输出 trace 仍可包含 shell 回显；本票承诺的是不采集输入正文到事件流。

显式关闭沿用窗格停止路径，并核对关闭前观察到的 shell、前台与后台子进程退出；不能核对则拒绝确认。后台重启不拉起普通 shell，保留打开集，历史快照返回 ended。窗口凭据关闭只断开视图；界面入口与中文“已结束”显示留给第二段。

## 红态、绿态与反例

来源：主控在沙箱外运行 `RUN-OUTSIDE-01-BACKEND.sh backend-02`；worker 读取本地摘要及外置盘原件核对。预期来自 ticket 与派发，不从实现生成答案。运行使用隔离 HOME，无供应商 CLI、真实登录凭据或模型。

| 验收项 | 红态／反例 | 绿态与证据 | 当前结论 |
| --- | --- | --- | --- |
| 普通 zsh 入口、echo/pwd/cwd | `known-bad.json`：同一场景在 cc18d93db 的真实 CLI 于 shell_start 被拒，`Unknown option '--cwd'`；不是环境失败 | `backend-02/candidate.json`：两个项目，含中文和空格的 cwd；真实登录／交互 zsh 读取隔离 `.zprofile`，命令输出、pwd、唯一 A2A_PROJECT 均符合独立输入 | 后台 PASS；真实 Electron 点击和截图 INCOMPLETE，等第二段 |
| 输入不记为 agent 输入或人工介入 | 无效编码、错误凭据、已失效窗口身份都带独立 nonce；匿名创建、窗口越权、跨项目、agent 派发与伪造 shell launch 身份均拒绝 | 整个事件流无 nonce／命令标记；user_inputs、user_input_ingress、dispatch_records 均为 0 | 本场景 PASS |
| 关闭结束子进程 | 创建前台与后台两个 `/bin/sleep`，关闭前真实 libproc 树包含 shell 与两个 sleep | shell 45162、前台 45309、后台 45292；关闭后独立 `/bin/ps` 均无记录，另一项目仍运行 | 本场景 PASS；不外推为任意信号处理程序的保证 |
| 重启显示结束、不拉起 | 另一个打开的 shell 随 daemon_stop 结束，重新启动同一状态目录 | shell 45188 退出；重启后历史快照 ended、shell_pid 为空、打开集仍含原 launch、旧窗口凭据无效；无 shell 恢复事件 | 后台 PASS；界面文字／截图 INCOMPLETE |
| 创建／关闭事件，无输入正文 | `backend-02/privacy-mutant.json`：隔离源码故意恢复原始请求日志，同一完整场景到隐私断言失败，错误为“shell 输入内容泄漏进事件流” | 每个 shell 恰有一条角色为 shell 的创建和关闭事件；候选事件流无输入正文 | 本场景 PASS；坏版本被有效拒绝 |
| 不动门禁与受管输入；地图健康 | 未改 acceptance/ 或门禁核心；既有回归问题见下节 | controller-window、restore 在 backend-02 退出 0；夹具修正后两项回归在基线和候选均退出 0 | 相关回归局部 PASS；地图要求 INCOMPLETE：稀疏检出仍有 8 个缺失项，0 stale |

`entry-red-01.json`／`entry-green-01.json` 只检查真实 CLI 的参数接纳，不当成 PTY 证据。`backend-01` 因依赖中的 spawn-helper 缺执行位而在 daemon_start 失败，保留为环境失败，不算业务红态。主控按现有 README 手工改为 755；产品未自动 chmod、重装或添加 fallback。

## 两项既有回归的根因与修复

主控报告 backend-02 的 worker-dispatch、conflict-panes 各退出 1。先将 cc18d93db 的 src 放进隔离目录，用原测试运行：两项均出现与候选相同的失败，见 `regressions-original-01.json`；所以不是本票产品退化。

| 回归 | 基线与候选原始失败 | 最小夹具修正 | 对照结果 |
| --- | --- | --- | --- |
| worker-dispatch | PTY 是假 PID 123，进程观察却调用真实 libproc 查询系统 PID 123，返回 EPERM | 与既有 PTY 边界配套供应合成进程树；版本脚本仍走真实 exec，不启动供应商程序 | `regressions-fixtures-02.json`：基线 0、候选 0 |
| conflict-panes | 合成 Codex launch 只给可执行文件，没有任何配置参数；扫描原生日志调用当前 resumeArgv 合同，拒绝 restore_argv_missing | 夹具 argv 增加已有 `-a never` 参数 | 同上：基线 0、候选 0 |

原断言未删除、未改写、未放宽；只修夹具输入与进程观察边界。两次探针的原始目录仍在 `/private/tmp`，由下方归档命令复制到外置盘、核对文件数与字节数后才删除。完整检查需用新编号复跑，不改写 backend-01／02。

## 复现与主控待运行命令

先完整复跑：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-01-BACKEND.sh backend-03
```

归档 worker 在沙箱内取得的夹具对照现场：

```sh
python3 evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-02-ARCHIVE-PROBES.py local-probes-01
```

提交第一段（Git 元数据和现有尾注钩子的记录写入在沙箱外；worker 不申请升级）：

```sh
bash evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-03-COMMIT.sh
```

提交脚本核对分支、完整起点与空暂存区，只暂存列明的本票文件及小型文本证据，以真实 worker 启动绑定运行既有 hook，不手写 A2A 尾注，不 push。提交号待主控回传，不能把起点号当成交付号。主控按本次明确指示负责独立审查和合入，worker 暂不 submit。

本地语法／地图检查可复现为：

```sh
python3 evidence/2026-10-19-batch17/T-104/CHECK-LOCAL.py /绝对路径/新摘要.json
```

`local-checks-01.json`：Node 语法、Python AST、bash 语法、git diff --check 均通过；地图退出 1，8 个稀疏检出缺失项、0 stale。没有擅改地图、术语表或 ticket。README 已补后台接口与当前分段限制。

## 依赖、证据与剩余工作

主控首次 npm ci 增加 `179532 KiB`，约 **175.3 MiB 内置盘**；node_modules 为 worktree 内普通目录，未链接或移动构建输出。npm 缓存、Electron 下载缓存及原始运行归档都在 `/Volumes/WD-Elements`。本阶段没有 Electron 构建输出。脚本在外置盘未挂载时直接失败。

backend-01／02 原始现场在 `/Volumes/WD-Elements/a2a-evidence/2026-10-19-batch17/T-104/`；本仓库仅保留摘要、命令、报告和 archive 清单。归档没有校验值；核对文件数和字节数。所有被创建的实际后台均经生产 detached 启动器与独立进程组验证，退出由 socket 和 PID 消失确认。

尚未完成：backend-03 完整重跑、提交号及尾注核对、主控新开只读会话的独立 behavioral-acceptance-review、T-103 合入后的 UI 接线、真实 Electron 操作与截图、最终地图在完整 checkout 的核对。设计完整性检查按 skill 路由到独立验收审查；本实现会话不自称独立 reviewer。没有根据首轮运行宣称可靠性、性能或成本收益。
