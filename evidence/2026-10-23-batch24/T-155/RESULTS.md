# T-155-1 / a1：真实使用运行记录

状态：INCOMPLETE。截止于实例 1 派发失败后的准备脚本修订；完整多 agent 流程、审查与集成、困难场景和新实例复现均未完成。

## 版本与启动

- 产品基线：`f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697`；分支 `exec/t155`。本票只改证据目录，没有产品改动。
- 原计划提交：`ad72bc2ec2f1c2c49f4b5be721e6306d55287144`。
- 实例 1：`/private/tmp/t155-dogfood-lv2rm2nt`。主控在沙箱外运行 `START-APP.sh` 成功并于消息 #17 交接；Electron PID 73231、daemon PID 73230。
- Computer Use 用完整路径 `/Users/luckye/Documents/Code/a2a-wt-t155/workbench/node_modules/electron/dist/Electron.app` 绑定。首屏 AX 中的 renderer URL 指向该实例构建目录，窗口标题 Enchanted。
- Claude 启动命令：在界面项目终端中输入 `claude --model claude-haiku-5-5`；屏幕显示 Claude Code v2.1.309、Haiku 5.5、Claude Pro。

## 当前结论

项目打开、终端启动、执行主控申请与界面批准已走到。两个受管任务 T-A / T-B 已注册，但派发报 `launch_config_required`，没有 worker 窗格或启动记录。两任务仍显示准备中；流程页为阶段未知，任务页为空的只读窗格。

事后只读核对发现本票启动脚本遗漏 `--launch-config`。正式桌面入口 `workbench/app/desktop.mjs` 会配置 CLI、角色卡、版本、hook 授权和回合上限；原脚本仅 daemon_start，默认空配置。这是测试准备缺陷，不能据此认定正式产品无法派发。原始实例和失败截图完整保留，没有修复、恢复或清理其 attempt。

修订只补本票脚本的启动配置，按产品入口字段只配置 Claude、每会话 6 回合；不读取 Codex auth、不改用户配置。新准备实例 `/private/tmp/t155-dogfood-ohzs_78v`，配置字段、可执行路径、角色卡存在性及脚本语法检查通过。尚未启动，因此真实绿态仍为 INCOMPLETE。继续命令：

```sh
bash evidence/2026-10-23-batch24/T-155/STOP-APP.sh /private/tmp/t155-dogfood-lv2rm2nt --all
bash evidence/2026-10-23-batch24/T-155/START-APP.sh /private/tmp/t155-dogfood-ohzs_78v
```

以上停止与启动由主控沙箱外执行；旧实例停止后继续保留现场，不删除。原始 run 目录不纳入 Git，最终按 T-088 归档，当前尚未归档。

## 截图索引

图片在 `screenshots/`。截图内容优先于文件名；动作后即时截图偶有前一帧，已显式标明，不据此声称对应步骤完成。

| 图 | 画面 / 证明范围 |
| --- | --- |
| 01-window-ready.png | 隔离窗口空项目首屏 |
| 02-project-open.png | 测试 repo 已出现在项目侧栏 |
| 03-cli-launch-input.png | 指定 Claude 命令与测试 repo 的 workspace trust 提示 |
| 04-fixture-trust-selection.png | 只选择信任该一次性 repo，尚未确认 |
| 05-cli-ready.png | 实际为初始化过渡帧，不能证明 CLI 已就绪 |
| 06-role-request-progress.png | Claude 申请执行主控；编号卡片与窗格框对应 |
| 07-role-approved.png | 界面批准后显示等待 CLI 确认 |
| 08-flow-before-workers.png | 无任务时流程页空状态与未归属解释 |
| 09-records-after-role.png | C2 需求已完整记录，1 条主控终端提交 |
| 10-reflect-before-tasks.png | 主控会话树、复盘入口与默认关闭的定期复盘 |
| 11-dispatch-progress.png | 实际仍为 Reflect 切页前一帧，不作为派发证据 |
| 12-task-registration.png | T-A / T-B 准备中，主控正在轮询派发错误 |
| 13-dispatch-errors-expanded.png | preparing 状态；Claude 的 sleep 45 被其工具规则拒绝后改用 read 轮询 |
| 14-worker-start-failure.png | 实际为展开的任务状态与任务卡，不包含首次错误，不能单独证明失败原因 |
| 15-launch-config-required.png | C3 解释 preparing 与无 worker；首次错误全文在同回合上方，精确错误另由事后源码核对 |
| 16-preparing-without-worker.png | T-A 准备中、尚未启动窗格、只读未知；没有启动失败原因入口 |
| 17-flow-after-start-failure.png | 两条任务泳道均阶段未知、无 worker，主控未归属 |
| 18-first-dispatch-error-text.png | 实际为 C3 尾部，只看到 already_claimed 与 preparing 解释，未滚到首次错误 |
| 19-dispatch-error-details.png | 去掉 max_turns 后的派发仍为 already_claimed；其余为 C3 解释 |
| 20-error-commands.png | 快捷键尝试后的相同终端位置，不提供额外证明；完整保留 |

## 回合、输入与介入

界面中实际提交 3 个主控提示：C1 申请身份；C2 拆分和并行派发；C3 停止轮询并只读报告错误。C2 经界面 Escape 中断。原文或摘要见 `SESSION-NOTES.md`；C2 原文在记录页截图 09 中可核对。

尚未有应用内 worker / reviewer / Reflect 回合，未开应用内 Codex。当前“3”是可见根提示提交数；完整后台事件与原生回合统计尚未在停止后的只读证据中核对，不能将此升级为完整精确计数。全局上限仍是应用内 60 回合。

只对屏幕明确指向测试 repo 的信任提示操作 Down、截图核对后单独 Enter；执行主控卡片的批准也是本票计划内操作。没有系统隐私授权、登录、付款或越界操作请求；没有需要主控代批的系统权限。没有经 shell、CDP、DOM 或数据库驱动业务流程。

## 尚未完成

两个 worker 真正并行、worker 问题页答复、受控打回与重交、worker 窗格人工介入、多窗格滚动切换、独立审查、集成、带结果的指标与 Reflect、UI REOPEN、新隔离实例复现、正式中文发现报告、最终证据归档和独立接受性审查均待后续运行。

项目地图在本阶段交接前检查：Problems 0、Stale living docs 0。此结论只证明地图结构，不证明多 agent 能力通过。
