# T-062 ready_rev 2：Activity 首次使用提示

状态：PASS（产品修复、红绿、相关检查与一次有效独立审查通过）。保持 ticket open，待主控关闭；外观由用户判断。

本轮仅执行 `brief-T-062-rev2.md`，授权引用为“062选B”。原有 rev 1 证据、RESULTS、Resolution 与失败均保留。fork 父修订 `d9fc40a5f8b14d22ec7568c7ccef542572e79102`；产品候选 `4ac5ba00e7125279b08c241037d1404450455ff6`。执行身份与 CLI/Bun/Node 版本见 [rev2-identity.json](rev2-identity.json)，fixture 的启动与进程身份见 [rev2-probe01-launch.json](rev2-probe01-launch.json)。这是 Herdr 期交付，不新建或接管受管 attempt，不走门禁 submit。

## 产品改动

唯一上游文件：`apps/web/src/components/Sidebar.tsx`，4 行替换；完整改动见 [diff](rev2-fork-diff.patch)。未改直接样式文件或其他上游文件。

首次提示改为从铃铛下方展开、右边缘对齐铃铛。选择改位置，是因为无需添加任务路由判断、prop 或状态，提示仍可正常出现；普通悬停 tooltip 保留原来的底部居中方式。移除首次提示指定的白色文字与 accent 背景，复用原有 popup 主题背景和 `text-popover-foreground`；说明文字继承该颜色。没有新增组件、helper 或依赖。

实际背景由现有 `.app-popup-surface` 的 gradient 填充控制，旧的 accent 背景 utility 没有使提示变为蓝底，白色字在亮色主题下几乎消失。初始导览、提示仲裁、8 秒关闭和首次使用记录逻辑均未修改；既有 Activity 与导览 browser tests 覆盖这些行为。

## 界面红绿与独立 oracle

沿用上一轮的隔离 server、seed 和 Vite 夹具。问题初始化的 provider 边界为 setup-only 替身；之后服务端、HTTP、WebSocket、存储和 dev UI 为真实产品路径。fixture task 名为 `t057`，不是本轮 T-062 的受管 attempt。provider 禁用，工作台内真实模型调用 0 次；未访问正式工作台数据或认证。

每个主题/尺寸使用此前不存在的 browser profile，经真实 UI 点 `Not now`、`Skip tour`，在 Activity 提示出现时打开包含 3 条待决定问题的面板。截图前后均确认提示可见，未等待其消失。几何 oracle 来自 ticket：提示与“问题上报”标题和任务窗口的交叠面积为 0，标题三个命中点无遮挡。文字可读性补充检查使用 PNG 空白 inset 的实际背景像素与浏览器计算出的文字颜色，检查 4.5:1 阈值；截图的最终外观仍由用户判断。

| 主题与窗口 | 父修订红态 `rev2-red02` | 已提交候选绿态 `rev2-green02` |
| --- | --- | --- |
| 亮色 1600×1050 | 标题交叠 351 px²；文字对比度约 1.03 | 标题、任务窗口交叠 0；文字对比度约 19.27 |
| 亮色 1280×900 | 同上 | 同上 |
| 暗色 1600×1050 | 标题交叠 351 px²；文字原本可读 | 标题、任务窗口交叠 0；文字对比度约 17.47 |
| 暗色 1280×900 | 同上 | 同上 |

红态 [原始结果](rev2-red02.json)、[命令](rev2-red02-command.json)，exit 1，失败来自遮挡/亮色可读性断言，非夹具启动失败。绿态 [原始结果](rev2-green02.json)、[命令](rev2-green02-command.json)，exit 0，绑定完整 fork 提交且 Sidebar diff 为空。编辑后的首轮 `rev2-green01` 也通过，记录父修订加完整 Sidebar diff。

`rev2-red01` 的几何红态有效，但其透明背景计算把暗色底层当成白色，对比度数据不可作为结论；原脚本与结果原样保留。改用 PNG 像素取样的 `rev2-panel-title02.mjs` 在未修产品的父修订重跑，随后同一脚本跑绿态。

## 检查

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 相关 Vitest 7 文件 | PASS，188/188 | `rev2-related-tests-command.json` 与 `.log` |
| 既有 Activity / FeatureTour browser tests | PASS，最终完整轮 14/14 | `rev2-browser-tests05-command.json` 与 `.log` |
| 全 workspace typecheck | PASS，8/8 workspace tasks，未用缓存 | `rev2-typecheck-command.json` 与 `.log` |
| lint | PASS，0 errors、877 warnings；sync-fs 检查通过 | `rev2-lint-command.json` 与 `.log` |
| fmt:check | PASS，4526 文件 | `rev2-fmt-check-command.json` 与 `.log` |

浏览器套件失败记录全部保留：01 缺少默认 Playwright 浏览器；02 package script 固定 config 与追加 config 冲突；03 外置 `.ts` config 被按 CommonJS 加载；04 运行时 Browser WebSocket 提前关闭，13 项通过但整轮 exit 1；05 同命令完整复跑 exit 0、14 项通过。有效取证配置 `rev2-browser.config.mts` 合并原配置，仅指定已安装的 Chrome；既有测试与上游配置不变。04 的断联未定因，已非阻塞上报 `20261010T025815Z-worker:s11-t062-rev2-issue-001`，不声称本次修复解决了该异常。

原始 stdout 日志含工具输出的行尾空白，完整 staged diff 的空白检查退出 2，诊断保存在 `rev2-raw-log-whitespace-check.log`；原始日志未清理。非日志候选文件的 diff 空白检查退出 0，产品的 fmt:check 另有上述实际通过结果。

未跑全仓完整测试、桌面打包、真实 provider 或发布；本轮不涉及平台进程边界或迁移，未运行相应专项检查。正式工作台未停止、重启或访问，未 push。窄窗口下原有会话空态重叠由 T-063 跟踪，本轮未修。

## 重放

本轮各命令的完整 argv、cwd、时间与退出码均保存在 `rev2-*-command.json`。重新取绿态需 fork checkout 包含上述候选，新 label、新隔离 profile，7977/7978 的 IPv4/IPv6 均无占用。下面从 a2a 根目录执行；运行完成后仅停止该 label 启动的进程：

```sh
python3 evidence/2026-10-09-batch11/T-062/start-isolated.py rev2-replay01
python3 evidence/2026-10-09-batch11/T-062/rev2-run-command.py rev2-replay01-ui ./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-062/rev2-panel-title02.mjs /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-062 /Volumes/WD-Elements/dev-cache/synara/instances/t062-rev2-replay01 rev2-replay01-ui
python3 evidence/2026-10-09-batch11/T-062/stop-isolated.py rev2-replay01
```

红态要求源码为指定父修订；本轮原始运行发生在产品编辑前，不需要撤销共享 checkout 的修复来补证。已存在的 label/profile 会拒绝复用。后台服务脱离调用者进程组；fixture 未包含用户认证。两个自启服务已按 PID、启动时间、完整 argv 核对后停止，见 [stop](rev2-probe01-stop.json)。新 fixture 的 seed、数据库、repo、worktree 与控制请求保存在 `rev2-fixture-state.tar.gz`；浏览器 profile 留在本轮独立外置盘目录，未覆盖或删除旧现场。冻结前地图状态无 problems、无 stale，见 [checks](rev2-pre-freeze-checks.json)。

## 一次独立审查

冻结候选为 fork 上述提交加 a2a 证据提交 `d5d0af3704c3ede71df6b84e539c7b030395ccd9`。审查者只读 ticket 的 What/Acceptance、diff、截图、原始机械观察与重放命令；禁止读取 RESULTS、ticket Resolution、inbox 正文和旧审查。持续追加的 `controller-poll.log`、`dispatch.jsonl`、`panes.txt` 不属于候选，不据其变化判候选失效。以下结论在审查结束后追加，本轮只请求一次。

冻结 a2a 候选为 `d5d0af3704c3ede71df6b84e539c7b030395ccd9`，fork 为 `4ac5ba00e7125279b08c241037d1404450455ff6`。该冻结提交里的报告状态为审查待执行的 INCOMPLETE；以下记录在本次唯一审查结束后追加，不改变审查的代码、截图或原始运行结果。

独立 agent `/root/t062_rev2_acceptance`（acceptance-auditor，fresh context）返回 **PASS**，无 findings；明确确认未读取禁止内容，核对允许证据集与冻结提交 30/30 无差异。已知坏父修订被同一界面检查拒绝。原文完整保存在 [rev2-acceptance-review-raw.txt](rev2-acceptance-review-raw.txt)。本轮未追审；补充提交只加入独立结论、最终状态和收尾检查。

交付条件中的用户外观判断与执行主控关闭 ticket 尚待对应角色完成；本 PASS 限于 ticket 的位置、可读性、真实 dev UI 证据和要求的检查，不代表正式实例、provider 或发布已验收。问题上报共 1 条，browser 首轮断联已记录，后续完整轮通过但原因未定；未自行关闭该问题。
