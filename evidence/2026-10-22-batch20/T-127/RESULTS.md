# T-127 结果：产品里的 Codex worker 与 reviewer 直接用用户的 ~/.codex

2026-10-22。最终候选是 e161476d6（候选 3）。真实入口 GUI 02 跑在 18e290411（候选 2）上；候选 3 只多了一条失败路径，已用真实 Codex 的 e2e 和回归在 e161476d6 上复验，GUI 没有重跑。实现与验收都由本 session 完成，本票没有另开独立审查会话。

**结论：PASS**。逐项见“验收对照”。门禁结果处的两项核对（`review_native_session_folder`、`review_native_session_reused`）端到端走不到，见“限制”。

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 真实入口：打包测试版里，终端主控派一个 Codex worker；worker 与 reviewer 的会话都出现在用户 `~/.codex/sessions`；交付、审查、集成走通；a2a 不写 `~/.codex/config.toml`、`rules`、`hooks.json` | PASS | `gui-02/`：`ui-driver.json` 的 checks 为 `role_request_approved`、`sidebar_worker_under_controller`、`sidebar_reviewer_shown`、`task_accepted`、`hello_on_main`，failures 为空，任务状态经过 ready→claimed→submitted→reviewing→verified→integrating→accepted。`user-codex-sessions.txt` 列出用户 home 里的两份 rollout，cwd 分别是 worker worktree 和一次性候选副本。`git-main-log.txt` 里 main 上的提交带 `A2A-Native-Session: 01a1621c-…`。`user-config-compare.txt` 为 `same`：`~/.claude` 两份 settings 和 `~/.codex` 的 config.toml、rules、hooks.json，大小与修改时间前后一致。`codex-config-changed-keys.txt` 为空，config.toml 没有新增键。`codex-config-fixture-mentions.txt` 为 0，config.toml 里不出现夹具路径。主控是 Claude Haiku 5.5，worker 与 reviewer 是 Codex gpt-6.1-sol low |
| 门禁拒绝：reviewer argv 带 resume/fork | PASS | `e2e-case-resume-worker-in-argv-01.json`：`verify` 返回 `review_launch_boundary`，门禁写 `rejected` 事件 |
| 门禁拒绝：会话号与 worker 相同 | PASS（由后台拒绝，不是门禁结果检查） | `e2e-case-resume-worker-hidden-05.json`：只在实际命令里 resume worker 的会话，启动记录看起来是新会话。Codex 自己拒绝打开（“open in another app”），会话始终没有绑定，审查没有通过。120 秒后后台记录 `native_session_unbound`，窗格转为失败。变异 `unbound-unrecorded` 去掉这条记录后被检出（`e2e-case-resume-worker-hidden-unrecorded-mutant-01.json`） |
| 门禁拒绝：cwd 不是候选副本 | PASS | 两种形态。①untrusted 指向别的目录：`e2e-case-trust-other-folder-01.json`，`verify` 返回 `review_launch_boundary`；去掉门禁这条核对的变异 `gate-trust-unchecked` 被检出（`e2e-case-trust-other-folder-gate-mutant-01.json`）。②实际在审查 worktree 里跑：`e2e-case-session-folder-differs-07.json`，会话始终没有绑定，审查没有通过。reviewer 的每个 hook（包括 Stop）都以 `hook_native_session_mismatch` 被拒，记录里有它实际用的 cwd（`-06`）；120 秒后记录 `native_session_unbound` |
| 修前版本在同一场景上失败 | PASS | `e2e-red-head-01.json`（64f9c24d2）：派发即被 `isolated_codex_home_required` 拒绝 |
| 扫描只读本 launch 之后的会话文件；旧文件多时，派发与交付耗时不随旧文件数增长 | PASS | 见“耗时”：修后放 400 个和 20000 个旧会话，交付分别用 4.0 秒和 4.1 秒；同一测试换回修前的整目录扫描，20000 个时交付要 26.9 秒 |
| README 写明：产品 Codex 会话加载用户的规则、钩子和 skills，worker 可以不经批准执行用户 allow 过的命令（含 `git push origin HEAD`），门禁管不到 push | PASS | `workbench/README.md` 的“用户的 Codex home（T-127）”一节 |

## 用户在本票里的裁定（逐字）

- “1.直接用我的~/.codex,因为这些 session 我还有用,别隔离,然后我也会更新一些 skill 之类的,这都是有帮助的”
- 被告知 allow 规则与钩子都会生效之后，选“完全照用 ~/.codex”。
- “reviewer 也用 ~/.codex (Recommended)”
- “Claude 保持现状”：Claude worker 继续隔离，本票不动。
- GUI 验收的 home：“用我的 ~/.codex”。
- GUI 验收的 Codex 模型：“gpt-6.1-sol low (Recommended)”。
- 用户在 GUI 01 运行中指出：“这恢复终端内容应该是秒出的吧,这要等……这么久,这是不可接受的”。已在候选 2 修复，见下文。

## 候选

| 候选 | 提交 | 内容 | 依据 |
| --- | --- | --- | --- |
| 1 | 282906b9e | 产品启动配置取 `codex_bin` 与用户 `~/.codex`；删除 `isolated_codex_home_required` 与 `reviewers` 预建 home。每次启动传 untrusted 配置（worker 指向仓库根，reviewer 指向候选副本），后台代按 “Open restricted”。扫描只读启动当天起、启动后写过、`cwd` 等于本会话目录的 rollout。门禁核对 reviewer 的 untrusted 配置、会话号不复用、`session_meta.cwd` 是候选副本 | probe-01；e2e 绿态 03、04；红态 `e2e-red-head-01` |
| 2 | 18e290411 | ①Codex reviewer 的 `TMPDIR`、`TMPPREFIX` 指向候选副本里的 `.a2a-tmp/`，here-document 与 tempfile 可以用，不新增可写目录。②终端回放的写入器只在含 1004 的模式序列处分段等待 | GUI 01（真实 reviewer 写不了 here-document）；红态 `e2e-red-reviewer-tmp-01`；回放探针红 78.5 秒、绿 6 毫秒 |
| 3 | e161476d6 | Codex worker 或 reviewer 第一个回合提交后 120 秒内，若本目录里没有它的会话，记录 `native_session_unbound`，窗格转为失败 | 隐藏 resume、别处运行两个反例；变异 `unbound-unrecorded` |

## 终端恢复慢（用户在 GUI 01 期间提出）

原因：工作台的写入器为了拦截焦点模式 1004，遇到每个 DEC 私有模式序列（`ESC[?…h/l`）都切一段，单独等一次 xterm 写完。Claude Code 和 Codex 重绘时会大量输出光标显隐、同步输出这类序列，GUI 01 的主控终端录到 880KB 时已有 15,960 个。daemon 读输出很快，一次往返约 0.07 秒，慢在渲染进程。

修复：只有含 1004 的序列才单独成段，其余序列留在同一次写入里。T-078 输入来源探针里原有的 1004 用例（单独、混合、跨块切分、前导零）全部仍然通过。

| 测量 | 修前 | 修后 | 证据 |
| --- | --- | --- | --- |
| 探针：16,000 个非焦点私有模式 | 78.5 秒 | 6 毫秒 | `replay-probe-red-01.results.json`、`replay-probe-green-01.results.json`（完整目录已归档，见 `*.archive.json`） |
| 真实录像：GUI 01 主控终端 1.8MB，按界面方式以 64KB 分块回放 | 149 秒 | 0.25 秒 | `replay-trace-before-01.json`、`replay-trace-after-01.json`；脚本 `replay-trace.mjs` |

录像用 `/private/tmp/t127-ui-mDe9/state/traces/12f40a1c-…/pty.raw`。它是 /tmp 下的夹具，不入库。

还没做的：在打包好的应用里实际点开窗格计时。上表是同一个 xterm 和写入器在 Electron 里的测量，没有经过 IPC 与 daemon。

## GUI 各轮（真实入口，用户的 ~/.codex）

重现：`zsh evidence/2026-10-22-batch20/T-127/t127run.sh "<测试版 app>" <端口> <输出目录> claude-haiku-5-5`。测试版用 `cd workbench && node app/package.mjs --variant test --slot <新槽>` 构建。

| 轮 | 版本 | 结果 | 原因归类 |
| --- | --- | --- | --- |
| gui-01 | 282906b9e | 失败：独立审查判“需修复”，任务停在 submitted | 产品缺陷：reviewer 的沙箱排除了 /tmp 与 `$TMPDIR`，zsh 写不了 here-document（`can't create temp file for here document: operation not permitted`），变异检查一个都没跑成。审查员如实报告“未执行，不能声称被拒绝”，判断正确。候选 2 修复 |
| gui-02 | 18e290411 | PASS | 主控催促 0 次 |

## 变异与反例（e2e：真实 Codex 0.163.0 TUI，本地脚本化 Responses 接口，不调用模型）

e2e 的夹具 `$HOME/.codex` 里放了 rules、hooks.json、一个 skill、400 个旧会话，还有一份写在当天目录、cwd 指向别处的外来 rollout。最终绿态 `e2e-green-06.json`（e161476d6）共 19 项检查。

被检出的变异：

| 变异 | 失败在 | 证据 |
| --- | --- | --- |
| `restricted-unanswered`（不代按 Open restricted） | `worker_startup_unrecognised` | `e2e-mutant-restricted-unanswered-01.json` |
| `untrusted-config-missing`（不传 untrusted 配置） | `codex_folder_trust_requested`：出现会保存信任的对话框 | `e2e-mutant-untrusted-config-missing-02.json` |
| `project-trusted`（传 trusted） | `restricted_folder_screen_missing` | `e2e-mutant-project-trusted-02.json` |
| `scan-any-folder`（不按 cwd 过滤） | 外来 rollout 被读进 2 行 | `e2e-mutant-scan-any-folder-01.json` |
| `gate-trust-unchecked`（门禁不查 reviewer 的 untrusted 配置） | 指向别处的 reviewer 被放行 | `e2e-case-trust-other-folder-gate-mutant-01.json` |
| `unbound-unrecorded`（不记录未绑定） | `reviewer_elsewhere_unbound_recorded` | `e2e-case-resume-worker-hidden-unrecorded-mutant-01.json` |
| 修前 reviewer 沙箱（无临时目录） | `reviewer_shell_has_temporary_files` | `e2e-red-reviewer-tmp-01.json` |
| `scan-whole-home`（修前的整目录扫描） | 不判失败，只用于耗时对照 | 见“耗时” |

没有检出的变异：`gate-folder-unchecked`、`reviewer-folder-unbound`。原因见“限制”第 1 条。

## 耗时（测量值，不作断言）

| 扫描 | 旧会话数 | 会话绑定（秒） | 交付（秒） | 证据 |
| --- | --- | --- | --- | --- |
| 修后 | 400 | 2.1 | 4.0 | `e2e-green-04.json` |
| 修后 | 20000 | 2.7 | 4.1 | `e2e-timing-fix-20000-01.json` |
| 修前整目录扫描 | 400 | 1.7 | 4.0 | `e2e-timing-whole-home-400-01.json` |
| 修前整目录扫描 | 20000 | 26.9 | 26.9 | `e2e-timing-whole-home-20000-01.json` |

## 回归

- e161476d6 上：T-127 e2e 绿态（`e2e-green-06`）、T-112 原生（`regress-t112-native-03`）、T-112 执行（`regress-t112-execution-04`）、T-122 e2e（`regress-t122-e2e-03`）、T-084 尾注（`regress-t084-03.summary.json`），全部 PASS。
- 18e290411 上：T-112 原生 `-02`、T-112 执行 `-03`、T-122 e2e `-02`，全部 PASS。
- 282906b9e 上：t118、t107、t109、t111 `--daemon`、t121、T-112 执行 `-02`、T-122 e2e `-01`、T-084 `-02`、T-112 原生 `-01`，全部 PASS。
- 早已存在的失败（在 64f9c24d2 的副本上结果相同，不是本票引起）：test_daemon_gates_e2e 1 个 error（“Reviewer input did not reach its bounded turn”）、test_daemon_recovery_e2e 1F/4E、test_multiturn_identity_e2e 4F/4E；test_startup_shutdown_e2e、test_relay_conflict_e2e、test_quality_tracer_e2e 在 HEAD 上就失败。`run_daemon_acceptance` 的预检拒绝运行，因为 test_task_cards_e2e.py 与冻结基线不同（T-122 的改动）；这是验收基线，本票没有改。

## 限制

1. 门禁在审查结果处的两项核对端到端走不到：`review_native_session_folder`（`session_meta.cwd` 必须是候选副本）和 `review_writer_conflict` / `review_native_session_reused`（会话号不复用）。后台只认 cwd 等于候选副本的 rollout，别处跑的会话从来不会绑定，它的 hook 在后台就被拒了。所以这两项只是第二道防线，去掉它们的变异 `gate-folder-unchecked` 检不出。窄化后的变异 `reviewer-folder-unbound`（后台按审查 worktree 绑定）也停在后台：Stop 以 `question_origin_unverified` 被拒，到不了门禁。
2. Codex worker 能写 /tmp，因为请求目录在那里。夹具放在 /tmp 下，所以沙箱边界这一项在本 e2e 里观察不到，已从检查里去掉，并在测试里注明。
3. `native_session_unbound` 让窗格转为失败，但门禁里的审查状态不会自动改；审查仍显示 running，失败要看窗格和事件记录。
4. 用户的 `hooks.json` 里有 herdr-agent-state.sh 和 vibe-island 的钩子，产品里的 Codex 会话会触发它们。这符合“完全照用 ~/.codex”。
5. 恢复路径上的 `nativeSessionFile` 仍会遍历整个 home，但先按文件名过滤，不读内容。
6. 过时、未更新的测试：test_initial_worker_release 测的是 dated `run_t076_real.py` 里已删除的 release；其他旧运行器也还在用 `pane_release`。
7. 两份探针目录（`replay-probe-red-01`、`replay-probe-green-01`）在候选 2 里误入库，本次删除，改为 T-088 归档清单加 `results.json`。
