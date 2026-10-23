# T-155-1 / a1 实测逐场记录

状态：INCOMPLETE，正在运行；不能视为完成报告。

## 实例 1

主控消息 #17：沙箱外 START-APP exit 0；root `/private/tmp/t155-dogfood-lv2rm2nt`，Electron PID 73231，daemon PID 73230，repo 为其下 `demo-repo`，control socket 为其下 `state/control.sock`。产品基线 f3412fb4a。

- Computer Use 用本 worktree Electron.app 的完整路径绑定应用；AX 的 renderer URL 确认来自本实例构建目录。未操作同机正式 Enchanted。
- 首屏空项目；点“打开项目目录”，通过原生目录选择器定位测试 repo 并打开；项目侧栏出现 `demo-repo main · 无上游`。
- 点项目中的“新建终端”，在终端输入 `claude --model claude-haiku-5-5` 并回车。CLI 显示 `Claude Code v2.1.309`、`Haiku 5.5 · Claude Pro`。
- 只对屏幕明确显示的本次 repo 信任提示按 Down 选择 `Yes, I trust this folder`，截图核对后单独 Enter。此为本票一次性仓库的工作区信任，无系统隐私或登录操作。没有批准真实项目。
- 截图 05 文件名含 ready，但画面实际是初始化过渡期；不以文件名声称已就绪。随后屏幕明确出现 Claude 输入框后才提交 C1。

## 模型回合登记

此表按实际屏幕可见提交登记；真实内部回合数与回执待事后只读核对。应用内全用 Claude Haiku，未启动应用内 Codex。

| 编号 | 对象 | 输入 / 目的 | 当前结果 |
| --- | --- | --- | --- |
| C1 | 项目终端 Claude | 请担任这个一次性项目的执行主控。先按 Enchanted 的 a2a 使用说明申请执行主控身份，等我在界面批准；这轮先不要派发任务。只操作当前测试仓库，不操作其他项目，不 push，不删除文件。 | 已在 UI 提交，等待观察 |
| C2 | 同一执行主控 | 两个受管任务并行：A 按类别库存汇总并含总计；B 零库存补货单。全部 worker/reviewer 用 Haiku。B 先上报分组问题；A 有意漏总计，真实验收打回后补齐；启动两 worker 后暂停让用户观察和人工介入。总预算 60 回合，禁止 push / 删除 / 越界操作。完整原文已在记录页核对。 | 已在 UI 提交，任务栏出现 T-A / T-B 准备中 |
| C3 | 同一执行主控 | 先不要继续轮询或重试派发。请把刚才两个 worker 的首次派发命令和原始错误完整显示出来，只读核对当前是否真的有 CLI 在运行，说明为什么仍是 preparing。不要读凭据内容，不改产品代码，不恢复或清理 attempt。 | C2 多次 preparing 后由 UI Esc 中断，再提交本回合；待观察 |

预算：所有应用内真实模型回合合计最多 60；本表当前登记 3 次用户提交。不能把一次工具调用当作一次模型回合，也不能漏算后台回执或 reviewer / Reflect。

## 已观察的交互

- 角色申请卡按第 1 个窗格编号，窗格同时加框；点击批准后先显示“已批准，等待确认（15 秒）”，然后侧栏成为执行主控。C1 结束时显示空闲。此段未发现阻断。
- 流程页在尚未注册任务时明确显示空状态，把主控放在未归属并解释“没有关联到当前任务 attempt 的派发 worker”；不假造任务。
- 记录页在 C2 后显示 1 条主控终端提交，正文与 C2 一致；C1 在身份批准前，按页面说明不记录。角色批准操作是否应出现在这里待事后核对，尚不下结论。
- Reflect 显示主控会话、模型未知 / 强度未知；定期复盘默认未开启，立即复盘默认 Opus。本轮尚未点启动复盘。
- 截图 11 与刚取得的 AX 更新存在时间差：图片仍为 Reflect，AX 已切回终端；该图按实际画面理解，不把它当作派发截图。后续状态在独立截图中核对，暂不将此归为产品缺陷。
- C2 主控在派发错误后连续查 status；画面显示 T-A、T-B 均 preparing，thread_id 已有但 launch records 为 0。截图 13 展开工具输出可见 sleep 45 被 Claude 自己的工具规则拒绝；之后主控改用 read -t 3 轮询。这里是 Claude 行为观察，不能据此断言产品 worker 已启动。
- 用 ctrl+o 展开 Claude 记录，Page_Up 可翻阅；鼠标滚轮两页在该展开界面只产生很小位移。尚未有足够证据把滚动差异归为产品缺陷。
- 经界面 Escape 中断无进展轮询；随后 C3 要求只读显示首次错误。没有经外部命令或数据库驱动流程。
- C3 已结束：屏幕显示两个首次 dispatch 都为 `launch_config_required`；T-A 重试一次为 `already_claimed`。模型承认自行增加了帮助未列出的 `max_turns:8`，去掉后仍失败。它没有 worker 启动记录。该自报只作为解释线索，当前 UI 仅能确认两任务准备中、空窗格、流程阶段未知。

## 事后只读核对（与界面操作分开）

查看源码 `workbench/app/desktop.mjs` 与 README 的产品启动说明：正式桌面入口给后台传 workerLaunchConfig，包括 CLI 路径、角色卡与版本、hook 授权、回合上限。查看 `workbench/src/panes.ts` 的 createPane 检查可解释 `launch_config_required`。本票原启动脚本未传这份配置，daemon_start 默认空对象。直接触发因素属于测试准备缺陷，不是“正式产品不能派发”的证据。

保留实例 1，不尝试回收或清理其 attempt。只补本票启动脚本的配置参数，新实例继续测试。新的 daemon/Electron 仍交主控沙箱外启动。原始坏实例以后可用于说明失败状态处理，但完整旅程与新实例复现要求均尚未满足。
