# T-187 worker 一段的设计（ready_rev 2）

依据：ticket T-187 rev 2；用户 2026-10-25 选“C 两者都作 worker”，选项原文：“agy 用 --dangerously-skip-permissions 全放开，只靠门禁事后检查；Git 元数据可能被改，每次派发写一次 ~/.gemini”；实测事实见 `facts.md`。

## 现状

受管窗格（worker、审查员、监视）的回合全靠 Claude、Codex 的钩子和会话文件：
- 派发写入后，钩子（Claude 的 UserPromptSubmit、Codex 的会话文件）确认回合开始；Stop 钩子确认回合结束。
- Stop 钩子把 worker 写在请求目录里的交付请求转交给门禁；审查员的结果取自 Stop 钩子里的最后一条回复。
- 门禁按调用方所在的原生回合核对身份（`caller`）。

agy、opencode 没有按会话的钩子，但会把自己的回合状态以 OSC 7501 报给终端（facts.md）。

## 做法：第三种回合来源

CLI 的差异只放在一处：`terminalClis.ts` 的登记表加上受管启动所需的事实，`panes.ts` 按 `turns` 分两条路，不按 CLI 名字散落分支。

1. 任务卡与设置：`executor.cli` 增加 `agy`、`opencode`（与包装脚本、登记表同名）。设置页按角色可选。
2. 启动参数：
   - agy：`agy --dangerously-skip-permissions --model <M> --effort <E> [--add-dir <额外目录>]`，环境 `AGY_CLI_OSC7501=on`。运行在用户自己的 HOME（agy 的登录在那里；不复制凭据）。
   - opencode：`opencode --standalone --auto`，模型经 `OPENCODE_CONFIG_CONTENT` 的 `model` 传入；opencode 没有按会话的思考强度参数，记为 unknown。
   - 门禁照常记录完整 argv，按 CLI 核对必须出现的参数（agy 的 `--dangerously-skip-permissions`，opencode 的 `--standalone`）。
3. 回合（OSC 7501）：
   - 启动后第一条 `idle` 是就绪信号，释放首条任务。
   - 派发写入后的 `working` 是回合开始；回合 id 由后台合成（`osc:<submission id>`）。
   - 之后的 `idle`/`done`/`clear` 是回合结束：worker 的交付请求在这里转交（与 Stop 钩子同一条转交路径）；审查员读结果文件。
   - `blocked:kind=question`：worker、审查员按现行规则记录、不显示等待（T-124 1a）。`blocked:kind=permission`、`blocked:kind=auth`：记失败并在界面上显示原样，不按键。
4. 审查员：candidate 副本用 chmod 只读（与现行 agy 审查员一致）。结果写进后台指定的结果文件（opencode 的报告里没有最后一条回复），回合结束时读取，校验与现行 `reviewRequest` 相同。
5. agy 的目录信任：worker 启动后若报 `blocked:kind=permission` 且内容为 “Trust this folder?”，后台核对屏幕上高亮的是 “Yes, I trust this folder” 这一项、目录是本 attempt 的 worktree，然后才确认；确认后核对 `~/.gemini/antigravity-cli/settings.json` 只有 `trustedWorkspaces` 多了这一个目录，其他键不变。写入条数记入事件，完成报告列出。屏幕或文件对不上就停下记失败，不按键。
6. 用户在受管 worker 窗格里直接输入：仍经后台的窗口输入记为人工介入（不依赖钩子）。
7. Git 元数据：门禁的守护已完成（RESULTS“Git 元数据守护”）。

## 不做与限制

- 后台重启后，agy、opencode 的受管窗格不恢复（没有可核对的原生会话），按“会话已不在”处理。
- 回合内的工具调用、提问内容不像钩子那样逐条记录；侧栏状态只到运行中、空闲、等待回答、未知。
- agy 没有按会话的开局说明；worker 的角色卡照常作为首条提示的开头发出。

## 验证

- 替身（`t187_fake_cli.c` 扩展为受管 worker、审查员的行为）走派发 → 交付 → 门禁 → 审查 → 集成，先在修前留红态，再加变异。
- 真实运行：agy 主控派卡给 opencode worker，opencode 主控派卡给 agy worker，各自独立审查后集成，截图与运行记录。
