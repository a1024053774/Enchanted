# T-062：问题上报标题遮挡

状态：**INCOMPLETE**（聚焦红/绿验证通过，唯一一次独立审查无效）；ticket 保持 open，待主控关闭。依据 brief 与 `ready_rev: 1`，未调用门禁 submit。

本次截图浮层是 Synara 的首次使用 **Activity** 提示，不是问题上报面板残留。它在 `Skip tour` 后出现，约 8 秒自然关闭。隔离夹具使用空浏览器 profile，旧脚本跳过导览后立即拍图，正好拍到提示。该提示并非 dev 专属：正式产品的全新 profile 也可能首次看到它；本轮未访问正式实例，不能声称正式产品从不出现。

按 brief 环境分支，仅修正本任务的截图夹具：先确认真实提示出现，再等它自行关闭才截图。没有隐藏 DOM、写入已看标记、改计时器或改产品代码。fork 保持 `d9fc40a5f8b14d22ec7568c7ccef542572e79102`，fork 提交 **none**，上游文件改动 **无**。

## 验证与证据

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 来源与自然结束 | PASS | `source-evidence.txt`；`red02.json` 的 initial/expired 相差 8.032 秒。后续 reload 失败，整轮不算通过 |
| 修复前聚焦用例 | 预期红态，exit 1 | `red03-command.json`、`red03.json`、`red03-initial.png`：提示覆盖标题左侧 18 像素，面积 351 px²，左侧命中提示正文 |
| 修正等待后的同一标题 oracle | PASS，exit 0 | `green03-command.json`、`green03.json`、`green03-initial.png`：1600×1050，3 条待决定问题，标题无 tooltip 重叠、三个命中点均在标题 |
| 改变视口 | PASS（只判断标题遮挡） | `green03-narrow.png`：1280×900，标题仍无遮挡；下方会话空态重叠已另行上报 |
| Python、最终截图脚本 Node 语法 | PASS | `checks-and-skills.json`；收尾脚本另经 `ast.parse` 检查 |
| 项目地图健康 | PASS | `status-before-review.txt`：Problems 0，Stale living docs 0 |

oracle 来自 ticket 的“该浮层不再遮挡标题”：测标题矩形与真实 tooltip 的交集，并在标题左、中、右采样命中元素。不使用产品计时常量或产品函数作为答案。`panel-title-red03.mjs` 是缺少结束等待的已知坏夹具快照，同一 oracle 明确拒绝它；最终脚本为 `panel-title.mjs`。外观由用户判断，本报告只判断标题遮挡。

来源对应 fork 的 `apps/web/src/components/Sidebar.tsx:1157`（存储 key、8 秒计时、自动关闭）与既有 `SidebarActivityBellButton.browser.tsx`（预期提示出现/消失）。T-055 原 `panel-send.mjs` 跳过导览后立即截图的行号摘录也已保留。旧 T-055/T-057 脚本与截图作为历史证据，未改写。

## 重放

在 a2a 根目录用尚不存在的 label 启动；端口 7977/7978 必须空闲，外置盘必须挂载：

```sh
python3 evidence/2026-10-09-batch11/T-062/start-isolated.py replay01
```

在 Synara fork 根目录运行。红态预期 exit 1，绿态预期 exit 0；每次使用不同且不存在的证据/profile label：

```sh
./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-062/panel-title-red03.mjs /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-062 /Volumes/WD-Elements/dev-cache/synara/instances/t062-replay01 replay-red01
./a2a/scripts/bun run node /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-062/panel-title.mjs /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-062 /Volumes/WD-Elements/dev-cache/synara/instances/t062-replay01 replay-green01
```

最后在 a2a 根目录停止本次启动的两个进程：

```sh
python3 evidence/2026-10-09-batch11/T-062/stop-isolated.py replay01
```

原运行 argv、退出码、时间见各 `*-command.json`，启动 argv、身份与环境见 `probe01-launch.json`。夹具复用 T-057 的五条问题，底层 task id 仍为 `t057`，显示项目/会话为 T062；不代表接管 T-057 的真实 attempt。隔离身份见 `fixture-identity.json`。初始问题创建使用受控 provider 边界，之后 UI、HTTP、WS、服务端均为真实产品。未调用真实模型，provider 全部禁用，认证目录为空。

## 失败与边界

- `red01`：默认待决定视图被错误预期为全部 5 条，实际 3 条；准备失败，不作为遮挡红态。原脚本、日志、JSON 保留。
- `red02`：观察到提示自然结束，后续 reload 等待遇到页面/浏览器关闭；整轮 exit 1，保留原样。
- `green01`：首图、窄图标题清晰，重开错误复用旧页面定位器；已修正定位器，整轮仍记失败。
- `green02`：首图、窄图标题清晰，重开主界面等待失败。`resume01` 六次观察显示停在启动 logo、body 文本为空，已看标记已持久化，无 pageerror；诊断命令 exit 0 **不表示重开通过**。最终聚焦脚本只验本 ticket 的首次启动截图；重开行为没有通过结论。
- 重开问题非阻塞上报 `20261009T223641Z-worker:s11-t062-issue-001`；窄窗口空态重叠非阻塞上报 `20261009T223804Z-worker:s11-t062-issue-001`。正文见 `issue-reopen.md`、`issue-narrow.md`，均未扩大修复范围。

**REALITY GATE：PASS**，范围是截图环境的启动时机问题。事实是新 profile 触发首次提示、提示自然结束；正式实例状态与重开可用性未验证。若用户要求首次使用的产品提示本身也不得覆盖任务窗口，需要按 brief 另批准 Sidebar 等 a2a 目录之外的最小产品修改。

未运行 fork 全仓 fmt/lint/typecheck/测试：产品文件未改，ticket 此项以“若是产品缺陷”为条件。没有重建、停止或读写正式工作台，未访问用户认证数据，未 push。只停止本任务启动的 server/web（`probe01-stop.json`），原隔离目录仍保留。`fixture-state.tar.gz` 保存测试 repo/worktree、服务端状态与控制记录；浏览器 profile、服务器私钥不入 Git，原位置见 `retained-fixture.json`。

Bun 1.4.2、Node 24.13.1、Codex CLI 0.162.0；worker 请求 gpt-6.1-sol / xhigh / Fast，实际供应商 tier 未独立核验，工作台真实 provider 调用 0 次。审查使用配置的 acceptance-auditor（gpt-5.6-luna / max），不涉及工作台 provider 调用。版本与 skill 来源修订见 `versions-and-fork.json`、`checks-and-skills.json`。其他人的 `controller-poll.log` 与 fork `.grok/` 保持原样。

## 独立审查与提交

冻结候选：`45893b7c70b30b2659337875b043795127819686`。唯一一次 fresh-context 只读审查返回 **INCOMPLETE**，原文见 `acceptance-review-raw.txt`，不作为通过证据。

审查者在原文第 15 行自报读入了指令禁止的 RESULTS、Resolution 与 issue 正文，破坏独立上下文；它还把冻结提交之外的主控日志增长认作候选变化。本 worker 未修改该日志，固定候选提交未变。上述是审查过程问题，不能通过改他人的日志修复，也不能据此宣称代码存在 P1 缺陷。已上报 `20261009T224344Z-worker:s11-t062-issue-001`，正文见 `issue-review.md`；最初 ref 的 L16 行号笔误已在报告更正为 L15。

遵守 brief 的“只审查一次”，未自行追审。标题红/绿与截图仍有效，但总体交付 **INCOMPLETE**：缺少有效独立审查结论；正式/普通用户的首次使用状态未验证。提交本报告与证据后交执行主控处理，ticket 待主控关闭。
