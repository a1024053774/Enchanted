# 四家 CLI 的原生会话号与记录文件（T-195 实测，2026-10-27）

为 T-195“右键复制深度链接”先查清：每家 CLI 自己的会话号从哪里拿到、记录文件在哪、能不能用会话号续上。只记实测过的；推断单独标出。

## 现状：a2a 记了什么

- Claude Code：启动 worker 时由后台生成 `--session-id`，启动记录 `native_session` 就是 Claude 自己的会话号（`workbench/src/panes.ts`）。
- Codex：受管 worker 的线程号由窗格从 rollout 首行 `session_meta` 绑定，记在 `pane_native_session` 事件；项目终端里的 Codex 由 Enchanted 的钩子报来（连同报告它的进程号），记在 `shell_native_session` 事件。
- agy、opencode：启动记录里写的是 `osc7501:<launch id>`（`reportedSession`），是 a2a 自造的编号，不是这两家自己的会话号。T-195 不能把它当原生会话号复制出去。

## agy（Antigravity CLI）

实测对象：测试状态 `/private/tmp/t190/state` 中 zeta+T-6 的 agy worker，以及同日几个普通终端里的 agy。

- 终端信号：OSC 7501 报告里只有 `state`、`kind`、`app`、`msg`，**没有会话号**（T-6 窗格原始输出里的全部报告：`state=blocked:kind=auth`、`state=blocked:kind=permission`、`state=idle`、`state=working`，都带 `app=antigravity`）。
- 记录文件：每个会话一个 SQLite 文件 `~/.gemini/antigravity-cli/conversations/<会话号>.db`。会话号是 UUID。
- 对应关系：文件里的 `trajectory_metadata_blob` 表含工作目录的 `file://` 地址。T-6 worker 的工作区是 `/private/tmp/t190/state/worktrees/zeta/T-6-a1`，只出现在 `bc8c193b-144b-4661-871f-cc42882485c0.db` 一个文件里；用户真实状态里 github.io T-1 的 worker 也能这样唯一对上（`17a7cfbd-…`）。
- 普通终端：同一目录里开过两次 agy（beta），就有两个文件指向同一目录（`54e94a58-…`、`7bc7398d-…`），只凭目录分不出是哪一次。
- 续上：`agy --conversation <ID>`（`agy --help`：“Resume a previous conversation by ID”）。用会话号续上本轮没有实测。
- 结论：worker 与审查员各有专属工作区，可以按工作区对上唯一的会话文件；普通终端对不上唯一的文件时，应当拿不到、置灰。`trajectory_metadata_blob` 是 agy 内部格式（protobuf），按其中的路径文本匹配依赖它不变，属推断上的风险。

## opencode

实测对象：zeta+T-7 的 opencode worker（opencode 2.1.4，模型 `opencode/glm-5.3-flash-free`）。

- 终端信号：回合开始后的 OSC 7501 报告带 `id=ses_e82f2a9d4ffeAoBZHfaocylpxI`，这就是 opencode 自己的会话号；最早两条 `working` 报告还没有 `id`。
- 记录：所有会话在同一个 SQLite 库 `~/.local/share/opencode/opencode.db`，表 `session_v2`。按上面的会话号查到一行，`directory` 列正是 T-7 的工作区 `/private/tmp/t190/state/worktrees/zeta/T-7-a1`，模型列为 `{"id":"glm-5.3-flash-free","providerID":"opencode"}`。
- 续上：`opencode --session <ID>`（`opencode --help`：“Session ID to continue”）。本轮没有实测续上。
- 结论：会话号可以直接从终端信号拿到；“记录路径”是整个库文件加会话号，不是单独一个文件。
- 报告不带进程号：项目终端里同一个 shell 可以先后跑几次 opencode（`opencode; opencode`、管道、子 shell），只凭输出分不出报告来自哪一次运行（T-195 第 3 轮审查 F1）。受管 opencode worker 一个窗格只跑一个进程，不受影响。

## Claude Code 与 Codex

Claude Code 的会话号由后台指定，记录在该会话配置目录的 `projects/<目录名>/<会话号>.jsonl`（受管 worker 用隔离配置目录，T-127）；
受管 Codex 的线程号由窗格从 rollout 首行 `session_meta` 绑定（项目终端里的 Codex 由钩子报来），记录在 `<CODEX_HOME>/sessions/<年>/<月>/<日>/rollout-…-<线程号>.jsonl`，首行 `session_meta` 的 `id`
就是线程号。T-195 的 e2e 用真实 Claude Code（模型换成本地脚本化接口）与真实 Codex 核对了这两处路径，见
`evidence/2026-10-27-batch28/T-195/`。

会话号会变（T-195 审查 F1）：Claude Code 里 `/clear` 之后是新会话、新 jsonl，钩子输入里的 `session_id` 随之变成新的；
e2e 在项目终端里实测了这一点。Codex 开新线程同理，会写出另一条 `session_meta`。所以“启动时的号”只在第一个会话里对。

## 对 T-195 的影响

- 菜单要复制的“CLI 名、原生会话号、记录路径”四家都能给，但来源不同：Claude Code 启动时就有；受管 Codex 由窗格从 rollout 绑定，终端里的 Codex 等钩子；opencode 等回合开始后的信号；agy 要按工作区去找会话文件。
- 普通终端里的 agy、opencode 一律置灰，并说明原因（见下）。
- 不再用 `osc7501:<launch>` 当会话号展示。
- 会话号绑定报告它的那个 CLI 进程：钩子报来的带进程号，项目终端里 CLI 退出或重启后，旧号不再给出，等新的一次自己报。终端 OSC 7501 不带进程号，所以终端里的 opencode 不给链接；受管 Claude Code、Codex 另要核对窗格里没有换到别的会话或线程。
- agy 在终端里分不出是哪一次（可以 `cd` 到别处再启动，新会话的文件也可能还没写出），只对独占工作区的受管 agy worker 给链接（T-195 第 2 轮审查 R3）。
