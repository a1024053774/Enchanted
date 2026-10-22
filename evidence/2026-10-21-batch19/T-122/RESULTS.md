# T-122 结果：主控派发 Claude Code worker，worker 与 reviewer 启动即定身份

2026-10-21～22，最终候选 9b0898ccd（候选 8）。实现与验收都由本 session 完成；独立审查 01～03 由新开的只读子会话做，见 `review-01.md`～`review-03.md`。

**结论：PASS**（逐项见“验收对照”；真实入口用 Haiku 而非票面的 Sonnet，是用户的裁定）

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 真实入口：打包测试版里经角色申请批准的真实 Claude Code 执行主控派发 Claude Code worker，经交付、独立审查、集成到夹具工作分支 | PASS（模型用 Haiku 5.5、low，按用户选定“Haiku (Recommended)”，与票面的 Sonnet medium 不同） | `gui-07/`：`ui-driver.json` 的 checks 为 `role_request_approved`、`sidebar_worker_under_controller`、`sidebar_reviewer_shown`、`task_accepted`、`hello_on_main`，failures 为空；`git-main-log.txt` 里 main 上的提交带 A2A 尾注；`readback.json` 是后台库读回；截图在同目录 |
| 同一流程派发 Codex worker 仍然可用（回归） | PASS | `regress-t112-native-11.json`（在 9b0898ccd 上，真实 Codex 0.162.1、本地固定接口，不调用模型） |
| 侧栏自动显示：worker 在派发它的主控下面，reviewer 在任务下面，角色、CLI、模型来自启动记录 | PASS | `gui-07/06-sidebar-worker.png`、`07-sidebar-reviewer.png`；`readback.json` 的 `launch_records`：worker 与 reviewer 都是 `Claude Code`、`claude-haiku-5-5`、`low`，`parent_launch` 是主控终端 |
| Claude Code worker 的权限是强制的：越界写入被拒并留下记录；启动 argv 完整记入启动记录 | PASS | `e2e-green-15.json`（9b0898ccd）；变异矩阵 11/12 全部被检出（见下） |
| 没有已批准角色的会话、worker 自己都不能派发；修前版本跑同一入口失败 | PASS | e2e 检查项；红态 `e2e-red-01/02/03/05`（7a8a6f74f，修前） |
| `project_map.py status` 0 问题 | PASS | 关票提交后运行，见本票 ticket |

## 用户在本票里的裁定（逐字）

- “git add/commit 走沙箱外 (Recommended)”：整个 Git common dir 对 Claude worker 的沙箱 deny，只有单独的 `git add`、`git commit` 走沙箱外（候选 3）。
- “worker 提交不跑项目钩子 (Recommended)”：受管会话的提交只跑 a2a 尾注钩子，门禁记 `project_hooks_skipped`（候选 4）。
- “后台代按确认”：a2a 新建的 worktree 由后台代按 Claude 的信任对话框。
- “Haiku”：真实入口验收的 Claude 用 Haiku。
- “Claude 保持现状”：Claude worker 继续用 `--setting-sources ""`。
- Codex worker 与 reviewer 用用户自己的 `~/.codex`（“直接用我的~/.codex……别隔离”）另立 T-127，本票不做。

## 候选与关键修复

| 候选 | 提交 | 内容 | 依据 |
| --- | --- | --- | --- |
| 1、2 | c952a9d46、c6120a562 | 终端主控派发 Claude worker；同 CLI reviewer；产品启动配置；处理审查 01 | `review-01.md`、probe-01～04 |
| 3 | c13befd85 | Git common dir 整体 deny；只放行独立 add/commit | `review-02.md`、probe-05；红态 `e2e-red-07/08-candidate2` |
| 4 | 47f0b3534 | 不跑项目钩子并记录；reviewer 可执行文件只记录不比较；reviewer 模型、强度、Fast、信号命令的核对加反例 | `review-03.md`；红态 `e2e-red-11-candidate3`（husky 钩子移动 main）、`e2e-red-11-reviewer-other-executable-path` |
| 5 | bdf2743d4 | 真实登录的 Claude 把长粘贴包成 `<pasted_content id="X">`，提交核对接受这一层包装 | `gui-01/`（红：`injected_prompt_blocked`） |
| 6 | 8557579c6 | 任务卡拒绝原因写出期望字段；hooks 路径不是目录（`core.hooksPath=/dev/null`）时按 Git 视为没有钩子 | `gui-02/`（主控猜了六种完成条件形状）；`cards-daemon-red-02-old-messages`、`cards-daemon-red-01-hookspath-devnull` |
| 7 | 932379311 | `source` 的拒绝原因写明可以为 `null`；skill 写明 `source` 与 argv 形状 | `gui-03/`（主控编造 ticket 文件）；`cards-daemon-red-03-source-null` |
| 8 | 9b0898ccd | skill：主控批准后等用户交代任务，按用户给的工作分支，不另建分支 | `gui-06/`（主控按 check.py 自编 T-1、集成到自建分支 `t-1-hello`） |

## GUI 各轮（真实登录、Haiku 5.5）

重现：`zsh evidence/2026-10-21-batch19/T-122/t122run.sh "<测试版 app>" <端口> <输出目录> claude-haiku-5-5`；测试版用 `cd workbench && node app/package.mjs --variant test --slot <新槽>` 构建。

| 轮 | 结果 | 原因归类 |
| --- | --- | --- |
| gui-01 | 失败：worker 的任务被当作注入拦下 | 产品缺陷，候选 5 修 |
| gui-02 | 失败：主控存不下任务卡 | 产品缺陷（拒绝原因不说形状），候选 6 修 |
| gui-03 | 失败：主控为 `source` 编造 ticket | 产品缺陷（候选 6 的措辞漏了 `null`），候选 7 修 |
| gui-04 | 失败：驱动 40 秒后停止后台 | 测试驱动缺陷：只认 "esc to interrupt"，不认 Claude 2.1.307 的转圈行；驱动已修 |
| gui-05 | 失败：独立审查判“需修复” | 夹具缺陷：`check.py` 只查文件存在，审查员的变异（空、goodbye、无换行）都能过；审查判断正确，夹具改为核对字节 |
| gui-06 | 链路走完但不算通过 | 模型行为加产品提示缺口：主控未等派发请求就自编任务、集成到自建分支；候选 8 修 skill，驱动加两条检查 |
| gui-07 | PASS | — |

gui-03 结束后夹具后台仍在运行（主控在执行 `find /`），由测试者停止，见 `gui-03/cleanup-note.txt`。

## 变异与反例（e2e，本地脚本化接口驱动真实 Claude Code 2.1.307，不调用模型）

矩阵 11/12 共 17 个变异全部被检出：`card-model-ignored`、`codex-provider-only`、`gate-reviewer-executable-compared`、`gate-reviewer-fast-unchecked`、`gate-reviewer-hook-includes`、`gate-reviewer-model-unchecked`、`git-deny-missing`、`git-excluded-broad`、`inbox-tasks-only`、`no-initial-release`、`no-terminal-parent`、`requested-model-as-fact`、`reviewer-codex-only`、`reviewer-shell-writable`、`submit-provider-codex`、`trust-unanswered`、`user-settings-loaded`；另有 07 轮的 `dotgit-file-writable`（证实 worktree 的 `.git` 文件不必另 deny）。reviewer 反例 `model-differs`、`fast-differs`、`hook-prefixed` 都被门禁以 `review_launch_boundary` 拒绝；正例 `other-executable-path`（硬链接到另一路径的同一 Claude）通过。

## 回归

- T-084 尾注记录：`regress-t084-05-summary/`（归档清单 `regress-t084-05.archive.json`）。
- T-107、T-109、T-111、T-112 执行、T-118、T-121：同目录 `regress-*` 各轮。
- 钩子环境与回合事实：`regress-hook-environment-01`、`regress-hook-turn-facts-02`。
- 任务卡（经后台）：`cards-daemon-03` 通过新加的断言后停在 verify 等审查回合；修前基线 `cards-daemon-baseline-224f2f38c` 同样停在这里，属 T-122 之前的旧问题，未在本票修。

## 限制与未覆盖

- Claude worker 的提交尾注 `A2A-Model`、`A2A-Effort` 为 `unknown`：Claude 的钩子拿不到实际模型；请求的模型与强度在启动记录里，门禁按 T-084 的 Claude 豁免放行。
- `$TMPDIR` 对 Claude worker 仍可写（收回会让每条 shell 命令失败）。
- 沙箱外的 `git add`、`git commit` 仍执行用户 `~/.gitconfig` 里的 filter（如 git-lfs）。
- reviewer 角色设置对 Claude 审查者暂不生效（审查 01 第 9 条）。
- `/clear` 与自动压缩换会话号后，不修正也不记录。
- 启动期限与“启动后不再代按信任”没有专门测试。
- 门禁在主 checkout 里的操作是否会触发主仓库自己的钩子，未调查。
- 任务卡经后台的旧回归套件在 verify 一步超时（见上），未修。
