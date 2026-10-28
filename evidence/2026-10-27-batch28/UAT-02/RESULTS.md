# 真实用户式试用 第 2 轮（2026-10-27）

用户：“Allowed, run round 2”（已允许 Enchanted Test 访问“文稿”文件夹）。

状态：NO_GO。主路径最终走通：主控申请（先拒后批）→ 建卡 → 派 worker → 人工介入 → 交付 → 审查 → 集成，`notes-cli` 的两个毛病修好；但中途审查两次卡死、补交两次被拒，靠回收重派才走完，普通用户自己很难弄明白怎么继续。

## 做法

同第 1 轮的打包（`37b17192b`，uat01）与隔离状态目录；Codex `gpt-6.1-terra` high 用 Computer Use 按 `BRIEF.md` 操作，报告原文 `REPORT.md`，截图在外置盘（`ui-check2.archive.json`）。主控是终端里的 Claude Code（haiku）；它为任务卡选的 worker 与审查员是 Claude Code `claude-sonnet-5-5`（启动记录里 5 次都是这个模型）。试用者按边界只对夹具目录的 Claude 信任框选了信任。本轮没有代批任何授权。

## 结果

集成到 `refs/heads/enchanted/notes-cli` 的是第二个 attempt 的 `428a6bd`，`main` 仍是 `ede9bf2`（`notes-cli-git-log.txt`）。试用者在集成分支上：`python3 -m unittest -v` 4 项 OK；`done 99` 与不带文字的 `add` 都报错并以 1 退出。

## 发现

| # | 现象 | 判断 | 去向 |
| --- | --- | --- | --- |
| 1 | 审查两次停在“审查结论协议无效”，问题页两张卡都叫“问题 1” | 审查员（Sonnet 5.5）手写的回包 JSON 两次都在末尾少一个 `}`（`review-protocol-failures.json`，与 Claude 自己的会话记录逐字相同，不是截断）；门禁按协议拒收是对的，但要模型手写深层嵌套 JSON 的协议脆弱，失败后用户只能重开审查 | T-203 |
| 2 | 交付后在 worker 窗格补要求，worker 两次补交都被 `stale_turn` 拒绝 | 按门禁设计：已交付的 attempt 只在“交付被打回”的修复流程里才能再交；审查卡死不算打回，要改卡、回收、重派。界面只给代码，主控（haiku）也先给了错的建议 | T-205（说明与下一步） |
| 3 | 任务卡门禁拒绝只显示 `oracle_not_found` 之类的代码 | 同上，拒绝原因没有人话说明 | T-205 |
| 4 | 关闭一个有待批申请的终端，窗格顶部报 `Error invoking remote method 'a2a:resize': Error: Window is not available for input` | 缺陷：关闭后界面仍调用 resize，把内部错误当“输入尚未确认”显示。申请本身按设计随终端关闭而结束（`role-requests.txt` 里该申请没有后续事件，读取时因终端已不在判为 ended / terminal_gone），批不了 | T-204 |
| 5 | “复制深度链接”复制的是“Claude Code 会话 <号>，记录 <路径>”，不是可点的链接 | 按 T-195 设计如此；菜单名“深度链接”让用户以为是 URL。是否改名留给用户 | — |

顺利的：Claude 自己从自然语言找到主控申请办法；拒绝后如实报告被拒；第二个 Claude 申请同一角色得到 `role_taken`；worker 窗格提示“在此窗格输入会记录为人工介入”，消息与回车都记成人工介入；任务进行中关窗再重开，worker 窗格接上、后台继续；流程、问题、记录、指标页都能打开，旧 attempt 显示在“未归属”并说明原因。

试用者记下的越界：主控把验收草稿写在 Claude 自己的 scratchpad（`/private/tmp/claude-501/...`），超出 BRIEF 限定的 `/private/tmp/uat/`；试用者发现后让它迁回，外部残留未核实。

## 没测到

Codex、agy 作 worker 的重派；第 1 轮的问题本轮没有复测。
