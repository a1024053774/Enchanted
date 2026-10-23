# T-150-1 / a1 测试迁移结果（2026-10-23）

PASS（worker 的 VM 合同迁移与红绿验证）。执行主控的独立验收、集成与关闭 ticket 尚未完成。

生产代码固定在起点 `32ffb4e6dcc0472b20bbb64331a355621c9b73a9`，本分支没有改产品。唯一测试改动是 `workbench/tests/test_t091_pane_ipc.mjs`；没有新增测试辅助模块。其余变更都是本目录的中文记录、运行脚本与小型文本证据。task `T-150-1`、attempt `a1`、worker `b23-t150`；session、fence/launch 与完整提交身份由提交钩子保存。规格版本为 T-150 ready_rev 1，用户授权与修改边界见 `card.md`。

## 断言迁移

编辑前逐行清单见 [ASSERTIONS.md](ASSERTIONS.md)：起点全部 189 个含断言的原始行（同一行的多条断言一起处理），包括夹具断言和反例分类器。新期望先由 T-150、现行 ticket 与规格确定；没有从当前运行输出生成名单或答案。`main.ts`、`preload.ts` 仅用于确定实际边界、接口名称和变异位置。

| 原断言或检查 | 现行断言或处理 | 依据 |
| --- | --- | --- |
| 默认第一次启动显示当前 worker | 无选择启动无窗格、无凭据；显式 task 的从未保存布局仍核对 worker 回退及持久化。这条 task 检查仍有效，没有删除 | T-119、T-139；main.ts `prepareSelection` 的无 task 与 task 两条入口 |
| 选择 legacy/picker/shell 等历史 contract；旧全局 IPC 与 bridge 数量/名单 | 只测试现行合同；按 ticket 显式列出 38 个 IPC、40 个 bridge 成员（含 paneKeys/home），核对精确集合和全局只注册一次 | T-119（角色申请）、T-132（问题）、T-134（指标与输入记录）、T-135（archiveUsage）、T-136/137（复盘/Reflect）、T-140（额外目录）；main.ts/preload.ts 的对应入口 |
| iframe/未知窗口在旧名单上拒收 | 扩至全部现行接口，逐接口给有效参数，要求 `Unknown window`，并确认传输请求数不增；所有 10 个 keyed 接口同时拒绝外窗、缺失、空、数字及未登记 key | T-091、T-150；主进程 `windowTarget`/`target` |
| 侧栏查看总是只读；运行中的 ideation 不发凭据 | running worker 复用其 key/凭据且单个 agent 只显示自己；reviewer 与 ended-controller 只读且不发凭据 | T-139、T-146；`select-agent`/`prepareSelection` 的 inspect 与只读判定 |
| 先切 ended 再直接关掉隐藏的 reviewer key | 先重新选择 reviewer，核对 parked key 复用，再关闭；两次只读关闭都不删持久布局 | T-139 的单 agent 视图；T-096 的布局持久化 |
| 侧栏查看结束后直接用原 worker key 写输入 | 先回到 worker 视图，再核对 composition/observation/release 绑定原 window_id | T-139：隐藏窗格不能接收输入；原绑定检查保留 |
| 空 task 布局重开会同时读取项目 shell 布局 | 精确核对两次重开只读 task snapshot 和 task layout，零 launch 选择、零凭据；空 preload、关闭、显式重开检查全部保留 | T-096、T-139（任务视图不混项目终端） |
| 无 task 不能创建终端（旧 shell 模式分支） | 删除过时模式分支，保留原默认已有的未归属终端创建正例，核对 home 目录与独立凭据 | T-119 |
| 从 task 新建终端给原 task 的 paneKeys 加一 | 创建后切到项目终端视图，只见新终端；任务 key 不复用，cwd 来自项目 repo。再走项目概览 → task → 单终端，核对项目概览为空、task 无 shell、parked shell 禁输入、返回复用凭据 | T-139、T-143 |
| 历史 no-key、单窗格、空布局 revision 必须在旧 harness 位置失败；旧 transient 凭据变异 | 换为当前 main 内存变异，分别命中同一有效边界；保留原 close/window-key/notification 变异，history_credentials 改成 ended 主控凭据泄露；再加 late_identity 与 iframe 变异 | T-150：必须在当前代码和保留的有效检查上取得红态 |
| CLI 只有位置式报告路径与 source | 保留位置式路径/source；增加 `--summary`、`--revision`、`--mutant`。revision 同时读取 main、preload、notificationCenter；所有报告 `wx` 创建，拒绝覆盖旧证据 | COMMON.md 的可重放与证据要求 |

未改的有效检查包括：并发 snapshot 只签发一次、各窗各 pane 的 key/window_id/sequence/output 独立、controller 的 nullable attempt 可输入、历史 worker 不可输入、preload 的 frozen keys、问答与配置参数拒收和原样透传、层级透传、通知去重/开关/Dock/断连不重试、迟到身份撤销、关闭 app 保留布局且另一窗口仍可输入、三 pane 同屏合同、foreign task/旧 attempt 在建窗与发凭据前被拒、重复 launch 拒收、reviewer 只读与重命名、单 pane 关闭保留 sibling 凭据、恢复顺序、恢复失败不签发输入凭据、最终空布局反复重开。

## 红绿证据

完整复现命令：

```sh
zsh evidence/2026-10-23-batch23/T-150/RUN-LOCAL-01.sh
```

每次创建新的 `local-01-*` 目录；`summary.json` 保存完整命令 argv、生产 revision、Node 版本、退出码、预期失败断言与判定；每场 JSON、stdout、stderr 都不覆盖。当前正式运行是 [local-01-DgE6Uo/summary.json](local-01-DgE6Uo/summary.json)，Node v26.5.0，13 场均符合预期：绿态与 `--revision 32ffb4e6d…` 绿态各退出 0；9 个独立 mutant 各退出 1，且必须是指定业务断言，不能把 setup/import 失败当红态。

| 变异 | 捕获的有效边界 |
| --- | --- |
| no_key | 未登记 pane key 不能被当作当前窗格使用 |
| single_pane | 三个显式 launch 必须产生三个独立窗格 |
| close | 显式关闭必须从持久布局移除一个 pane |
| empty_layout | 空布局重开不能偷偷复活 worker |
| window_key | 窗口级 projects 读取不需要 pane key |
| notification | 等待用户回答时产生一条应用内通知 |
| history_credentials | 已结束的主控不获得输入凭据 |
| late_identity | 关闭必须等待已接纳的 window_open，随后撤销迟到凭据 |
| iframe | 子 frame 不能调用顶层窗口的 IPC |

默认测试本身也执行绿态和全部变异；每个变异先核对唯一替换位置，再核对聚焦断言。独立 `--mutant` 运行额外证明退出码。绿态 33 个检查组覆盖上述保留检查；检查组不是用例数量或可靠性估计。

相关已有回归：`test_t139_selection.mjs`（视图、parked key、凭据回收）与 `test_t110_window_sequence.mjs`（输入序号与关闭边界）都在同一脚本运行并 PASS。其余历史 GUI/CLI 套件没有重跑，本次未改产品或它们的夹具，不宣称 GUI 或真实后台通过。

探索性失败原件全部保留：`baseline-01.json` 是原测试在旧 IPC 名单处失败；`candidate-01.json` 暴露旧流程向隐藏 reviewer key 发 close，随后按 T-139 重新选择；`candidate-02.json` 的首个 no_key 变异仍被 snapshot 的第二层校验拒绝，却更晚造成跨窗请求，因此聚焦分类器正确拒绝它，随后改为精确复现无 key 路由的变异；`candidate-04.json` 暴露夹具缺终端目录，补的是测试边界里的 terminals。`candidate-03.json`、`candidate-05.json` 为相应检查点的 PASS。没有删除或重写这些结果。

## 边界与交付

此证据为 L1：真实 TS main/preload/notificationCenter 在 VM 中执行，Electron、传输、文件系统由夹具提供。它证明本票测试迁移及纯逻辑边界，不证明真实 Electron sender 身份、socket、原生 CLI 或模型行为。本次模型/API 回合为 0，无后台进程，无用户配置写入，无产品代码改动，无新依赖。

沙箱内完整运行成功，无需 RUN-OUTSIDE。交付后执行主控仍须按公共约定复跑、独立审查、走门禁集成；本报告不关闭 T-150，也不改地图或 HISTORICAL.md。项目状态检查与最终提交见后续交付记录。
