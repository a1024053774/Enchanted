# T-219 基线失败调查与测试修订

结论：**INCOMPLETE**。九项均已在给定基线的产品源码上复现到票面失败点；其中八项是测试过时，已修订并取得绿态与相关错误实现的红态。第 6 项是产品缺陷，按授权边界未修产品。初轮构建还发生了临时目录边界偏差，见“需要主控决定”；不能把本轮的路径边界记为 PASS。

## 范围与证据读法

- worktree：`/Users/luckye/Documents/Code/a2a-worktrees/T-219`；分支：`t219-baseline-tests`；基线/HEAD：`a09da15f93d949eff9f81b46b071e58b9ba28af6`。
- 工作分支没有 commit、push；`.project-map/`、产品源码和用户的全局配置没有被本次补丁修改。变更为 12 个测试及其夹具文件，见 [candidate.patch](candidate.patch)、[冻结候选](candidate.json)。
- 验收预期取自下列票/决定；历史原文及 `git show` 已保存为 [contract-history.log](contract-history.log)，重跑见 [contract-history.command.txt](contract-history.command.txt)。没有用实现常量生成预期。
- [RUNS.md](RUNS.md) 索引所有运行，包括脚手架失败和中间失败；各次 `.log`、`.meta.json`、`.command.txt` 保存输出、退出码、时间、完整 argv 和重跑命令。每个运行目录中的 `REPLAY.md` 指回完整命令。不要覆盖原件，重跑时换输出名和运行标签。
- 第 2、3 项的给定入口本来就是纯逻辑/PTY spy 测试（L1）；第 4 项是真 daemon/socket/CLI/relay，PTY 为 spy；第 7 项是真 CLI/Git/SQLite/故障中断，worker 和 reviewer 的外部过程为受控夹具。这些绿态不证明真实供应商模型能力，也不证明尚未实现的 hc 受管运行时。
- 第 1、5、9 项使用实际安装的交互 Claude CLI 与真实 Electron；模型接口是仓库已有的本地脚本化 Messages API。第 8 项没有模型。第 6 项使用实际交互 Codex，模型接口改为仓库 `t112_native_api.py` 的本地 Responses API，实际记录到两次 `/v1/responses`，见 [接口记录](baseline-06c.json.api.jsonl)、[配置适配记录](baseline-06c.json.transport.json)。没有调用供应商模型。
- 顶层 runner 和测试后台服务均脱离调用者进程组。没有连接、重启用户的 Herdr server 或 hc default core。
- **Tracer bullet**：本票沿既有端到端入口恢复薄切片，不做产品分层重构。**Deep modules**：只补足测试依赖的现行协议字段与外部事实，没有新增产品包装层。**Ubiquitous language**：卡片保留任务名，门禁身份使用“项目 + 任务”的完整任务 id。

以下命令可直接复跑；先执行：

```sh
cd /Users/luckye/Documents/Code/a2a-worktrees/T-219
E=/Users/luckye/Documents/Code/a2a-worktrees/T-219-evidence
```

`run.py` 强制 `TMPDIR`、`TMP`、`TEMP` 为 `/private/tmp`；它记录被测命令退出码，判断结果请读 `.meta.json` 和摘要，而不是只看 runner 自身的 shell 退出码。

## 1. T-176 `home_terminal_header_known`

**结论：测试过时；当前 PASS。**

依据：T-191，提交 `e39357ae688c9240db02a40f737f46917db24b0c`。票中用户原话：“我刚刚新建了终端,还没开 agent 任务这个状态就动起来了,我我想要这个状态是监控 agent 状态的.”；Resolution 明写“普通终端状态取前台 CLI（无 CLI 为空闲，agy/opencode 取 OSC 7501，Claude/Codex 获批角色前未知）”。该提交将 `sidebar.ts` 中无前台 CLI 的普通终端从 running 改成 idle。旧测试要求家目录空 shell 显示“运行中”，与此契约冲突；T-176 要求的各处同源、一致仍然保留。本基线尚未包含后续 hc 状态统一切片，不以未来行为推翻现行 T-191。

修改：家目录终端头断言改为“空闲”，检查仍必须命中。另修审批同步点：等待行的角色文字成为“执行主控”，再检查空闲和父子关系。

新暴露失败：首次基线 [baseline-01.json](baseline-01.json) 在 `executor_under_ideation` 提前失败：行仍是“普通终端”。这是测试同步竞争，不是角色树回归：普通终端在 T-191 后本来就可以 idle，原来的“有行且 idle”并不证明批准已完成。未改测试的第二次 [baseline-01-repeat.json](baseline-01-repeat.json) 完成角色树检查，并只在票面目标失败，实际家目录头为“空闲”。同步修订未删除父子关系断言。

- 原红态：[baseline-01-repeat.json](baseline-01-repeat.json)，`home_terminal_header_known` 实测“空闲”。
- 绿态：[green-01.json](green-01.json)，18 项通过。
- 区分度：[mutant-01.json](mutant-01.json) 将无 CLI 的 shell 伪报 running；其余检查通过，准确在同一条头状态检查失败，实测“运行中”。
- 重跑：

```sh
python3 "$E/run.py" replay-01 python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary "$E/replay-01.json"
python3 "$E/run.py" replay-red-01 python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --mutant empty-shell-running --summary "$E/replay-red-01.json"
```

## 2. T-078 domain 紧急中断两项

**结论：测试过时；当前 PASS（L1）。**

依据：T-124，提交 `28a0550ccf`。票面“实现中发现”原文：“门禁把没有附加会话的线程一律当成 Codex：Claude Code worker 的 issue 和 run 回收 worker 都被拒（identity_conflict）。改为按任务卡的 CLI 判断。”其 diff 将 emergencyStop 的 provider 判定改为 `threadProvider(...attempt)`，从绑定的任务卡快照取 CLI。旧合成 attempt 没有 `card_snapshot_id` 和对应快照，SQLite 绑定 undefined 导致 `invalid_request`，并非紧急停止权限被取消。

修改：给合成 attempt 加快照 id，并插入该 attempt 的 Codex executor 快照。没有改调用者、两分钟阈值、ack 拦截、actor 防伪或“不关会话、不改门禁状态”的预期。

- 原红态：[baseline-02/results.json](baseline-02/results.json)：`executor_honors_stop_immediately`、`late_stop_actor_comes_from_caller` 均为 `invalid_request`。
- 绿态：[green-02/results.json](green-02/results.json)：11 项全部通过。
- 区分度：[mutant-02/results.json](mutant-02/results.json)：产品吞掉 `interruptThread` 调用，立即停止检查因真实 spy 的 interrupts 为空而失败。
- 重跑：

```sh
python3 "$E/run.py" replay-02 node workbench/tests/test_t078_inbox_domain.ts "$E/replay-02"
python3 "$E/run.py" replay-red-02 python3 "$E/mutate.py" 02b
```

## 3. T-078 pane `interrupt_only_esc_not_reclaim`

**结论：测试过时；当前 PASS（L1）。**

除第 2 项的 T-124 快照契约外，还受 T-187 提交 `fcb740a34` 影响：`Panes.readThread` 从“非 Claude 一律 Codex”改为按启动记录 `cli` 判定 provider。T-187 的现行目标是 agy、opencode 也可作 worker/reviewer；缺 CLI 的启动记录不再能冒充 Codex。

修改：合成 attempt 补绑定卡快照，合成启动记录明确 `cli: 'Codex'`，拒绝时附完整回执作诊断。仍逐一检查只写 Esc、零 kill、未停止、未归档、busy、门禁 claimed 和实际 actor。

- 原红态：[baseline-03/results.json](baseline-03/results.json)。
- 中间红态：[green-03/results.json](green-03/results.json)：只补快照后仍失败，因此不能计为通过；后续定位到缺失 CLI。进度消息曾误报这轮通过，已更正，以实际输出为准。
- 绿态：[green-03b/results.json](green-03b/results.json)：11 项全部通过。
- 区分度：[mutant-03b/results.json](mutant-03b/results.json)：产品将 Esc 改为 CR，在同一检查明确读到 `['\r'] != ['\x1b']`。较早 mutant-03 尚未补齐 CLI，只复现夹具失败，不计区分度。
- 重跑：

```sh
python3 "$E/run.py" replay-03 node workbench/tests/test_t078_pane_runtime.ts "$E/replay-03"
python3 "$E/run.py" replay-red-03 python3 "$E/mutate.py" 03c
```

## 4. A13 第一条 UPS 被拒

**结论：测试过时；当前 PASS（默认场景）。**

依据：T-108，提交 `f3a4a5416213e912076437cfd8ce6f69a0e3091f`，把各类 hook 的共同来源校验统一为 `validateHookEnvelope`。票中审查 03 原文：“缺 cwd、transcript_path、prompt_id”；Resolution：“当前回合可信度统一判定：字段缺失、无法核实、非法响应、其他工具的权限请求，一律显示‘未知’，撤销作答资格，PTY 零后续写入”。旧夹具的 UPS/Stop 没有 cwd、transcript_path，第一条 UPS 正确被 `question_origin_unverified` 拒绝。

修改：为合成主控提供工作区、隔离 HOME、本会话 transcript 文件，UPS/Stop 携带对应来源字段。失败时保留 scratch。

新暴露失败：[candidate-04/failure-context.json](candidate-04/failure-context.json)：UPS 通过后，没有 stop entry；数据库中明确为 `invalid_relay_request`。原因仍为测试过时：T-123 提交 `f0188d7720` 后 relay 的 `taskIdPattern` 要求完整任务 id，旧合成主控及 task 仍用裸名。已统一为 `a13-rehearsal-project+a13-rehearsal-task`，不绕过 relay 校验。

- 原红态：[baseline-04/command-1.json](baseline-04/command-1.json)。基线使用 `retain-rehearsal.cjs` 只拦该测试 scratch 删除，以保留失败现场，未替换业务行为。
- 绿态：[candidate-04b/result.json](candidate-04b/result.json)：6 项通过，包括旧 Stop 不转交、合法 Stop 一次转交、错误 launch 不新增 entry。
- 区分度：[mutant-04c/result.json](mutant-04c/result.json)：保留来源与身份校验，丢掉合法 relay perform，准确在 Stop entry 数量 0/1 失败。mutant-04 定位失败、mutant-04b 缺复制 `workbench/bin` 的失败均保留，不计业务红态。
- 重跑：

```sh
python3 "$E/run.py" replay-04 node workbench/tests/test_t078_a13_rehearsal.ts "$E/replay-04"
python3 "$E/run.py" replay-red-04 python3 "$E/mutate.py" 04d
```

未运行 `--recipient-offline`、`--recipient-ambiguous`、startup materials 扩展场景，不声称这些场景通过。

## 5. T-184 `shim_claude_state_known`

**结论：测试过时；当前 PASS。**

依据同第 1 项：T-191、`e39357ae6` 明确 Claude/Codex 获批角色前未知。T-184 原来的“不绕过包装脚本就没有未接入提示”仍成立，但包装已接入不等于已有角色回合状态。

修改：该条检查改为 `shim_claude_without_role_state_unknown`，严格要求 unknown。绕过 Claude/Codex 的提示、未知状态，正常包装无提示、退出后提示撤下等检查全部保留。

- 原红态：[baseline-05.json](baseline-05.json)：仅旧 `shim_claude_state_known` 失败，实际 unknown。
- 绿态：[green-05.json](green-05.json)：8 项通过。
- 区分度：[mutant-05.json](mutant-05.json)：将获批前的 hooks CLI 伪报 running，仅新的 unknown 检查失败。
- 重跑：

```sh
python3 "$E/run.py" replay-05 python3 workbench/tests/test_t184_unwired_cli_e2e.py --summary "$E/replay-05.json"
python3 "$E/run.py" replay-red-05 python3 "$E/mutate.py" 05b
```

## 6. T-195 `managed_codex_unsearchable_day_grey`

**结论：产品缺陷；当前 NO_GO，未修改产品或原测试。**

依据：T-195，首次实现提交 `4d8115865`，票面 Resolution 原文：“后台 native_link 只给‘现在这个会话’的原生号与记录路径……Codex 记录读不了即置灰”。这个要求没有被后续票取消。

根因：`workbench/src/nativeLink.ts` 的 `codexRootThreads` 从 `new Date(record.created_at)` 开始，按本地 `setDate(day.getDate()+1)` 递增，但循环终点是 `Date.now() + 86_400_000`。America/New_York 在 2026-11-01 回拨：2026-10-31 晚间启动后，到次日同一墙钟时间是 25 小时。实际扫描没走到明天，而测试把明天目录指到不可搜索的祖先目录。`readdirSync` 没有执行，native_link 因而仍返回 available=true。

- 原测试真实入口：[baseline-06c.json](baseline-06c.json)、[baseline-06c.log](baseline-06c.log)：前 15 项通过，目标断言失败；before 和 during 均 available=true。
- 实际启动时刻：[baseline-06c.native-launch.json](baseline-06c.native-launch.json)。[dst-america-02.log](dst-america-02.log) 用该时刻作算术诊断，显示日历次日相隔 25 小时、不在扫描内；[dst-utc-02.log](dst-utc-02.log) 的对照为 24 小时、包含次日。它们是根因诊断，不冒充修复绿态。
- 两个更早的适配尝试：[baseline-06.json](baseline-06.json)、[baseline-06b.json](baseline-06b.json)，因 Python/脚本包装改变预期前台二进制身份，被 `foreground_codex_required` 挡住，最终等链接超时。这是夹具适配失败，不计票面复现。最终 `safe-t195-native.py` 只改测试写入的隔离 home 模型 provider 配置，不改原二进制、生产身份检查或测试断言。
- 影响：在本地日历跨回拨的窗口内，次日已有记录或权限不可核实时，可能把未知的当前线程显示成可复制的确定链接。没有证据支持将它归为“测试过时”。
- 最小修法选项：按本地日历的日期边界建立扫描范围（显式包含契约中的次日），而非把本地日历步长与固定 24 小时混用；独立补春进、秋退、月末/年末及权限错误的日期案例。是否同时核对 `panes.ts` 内类似日期扫描，应由主控另票定范围。
- 重跑（需处于相同本地回拨日期条件；其他日期未必失败）：

```sh
python3 "$E/run.py" replay-06 python3 "$E/safe-t195-native.py" --summary "$E/replay-06.json"
python3 "$E/run.py" replay-dst env TZ=America/New_York node "$E/dst-diagnosis.mjs"
```

没有改时区掩盖原断言，没有绿态，没有声称产品已修复。

## 7. daemon recovery 五场景

**结论：测试及共享夹具过时；当前 PASS，五场景全部通过。**

初始依据：T-123，`f0188d7720`。票原文：“任务和任务卡的身份带上项目。同名任务可以分别存在于不同项目”；实现方案：“写任务名时，项目取终端角色的项目或请求的 project”。`resolveTask` 在接了 runtime、没有已建任务的情况下不能猜新任务的项目。原夹具 `card_save` 没有 project，五场均在该处 `unknown_task`，见 [baseline-07/run.json](baseline-07/run.json)。

修订：共享 `test_task_cards_e2e.py.save_card` 明确 `--project fixture`；register_task 断言新建任务返回 `fixture+<卡片任务名>`，其后把完整 id 用于尾注、SQLite 查询、引用与恢复命令。卡片内的 id 仍是任务名。

后续逐项暴露并处理的失败：

| 新失败 | 分类与依据 | 修订 |
|---|---|---|
| reviewer 等 `fixture-turn-1` 超时，队列仍 queued | 测试过时，T-141 `bf3d00a82`：不再以信任选择代替原生 ready；现行票要求“Codex 跟随用户配置”，提交明确首任务等待原生就绪包 | controlled PTY 在受限打开之后报 OSC 7501 ready；随后 CR 写真实夹具 turn 记录并发输出，让生产 scan 读取，未直接设置 pane ready/state |
| `review_template_unreadable`，文件内容为 undefined | 测试过时，T-203 `30ee51d30`：“身份字段……与 review_requirements 由门禁在开审查时写进……模板” | 测试 runtime adapter 转交 createReview 的第 4 个 template 参数 |
| 仍把结论放 `last_assistant_message` | 测试过时，T-203 同一提交：“原来‘最后一条回复必须是 JSON’的协议删掉，不并存” | QualityDriver 经真实 `reviewResult.ts submit` 入口只交 verdict/findings/report，再发带 cwd/transcript_path 的 Stop；不直接写门禁状态，不自行拼身份模板 |
| 杀后要求 `daemon_start` 拒绝 stale socket；实际旧端点已清，随后旧测试凭据导致 EEXIST | 测试过时，T-096 `a8fbc72bdf`，Resolution：“只有能证明已经死掉的旧端点才允许重启” | 把拒绝检查放到被核实的原 host **仍活着**时，要求 live-owner 错误、socket/PID 保留；杀掉且 wait/ps 确认退出后，只清理本夹具旧端点与该 epoch 的 bootstrap 凭据，再启动原受控 host |

中间输出均保留：[candidate-07](candidate-07/run.json)、[candidate-07b](candidate-07b/run.json)、[candidate-07c](candidate-07c/run.json)。candidate-07 末段跨过了共享夹具修改时间，作为探索记录，不用于最终通过判定。

- 绿态：[candidate-07d/run.json](candidate-07d/run.json)、[candidate-07d.log](candidate-07d.log)：CAS 前中断、CAS 后中断、外部 X、引用已删、验收中断与操作锁五场全过。重启前后保留同一任务/attempt、原验收变 interrupted、孤儿结果不得满足新 oracle、CAS 至多一次等检查均未删。
- 区分度：[mutant-07/run.json](mutant-07/run.json)：前四场通过，产品不把原验收置 interrupted 时，第五场准确以 `running != interrupted` 失败。
- 重跑：

```sh
python3 "$E/run.py" replay-07 python3 workbench/tests/test_daemon_recovery_e2e.py --output "$E/replay-07"
python3 "$E/run.py" replay-red-07 python3 "$E/mutate.py" 07b
```

共享 `test_task_cards_e2e.py`、QualityDriver、runtime adapter、controlled PTY 的修订已由这五场真实门禁入口覆盖；未运行它们所有历史调用者的完整测试集，不以本票替那些套件背书。

## 8. Electron 夹具 `card_save`

**结论：测试过时；当前 PASS，真实窗口已运行。**

初始原因同第 7 项：T-123、`f0188d7720`。修改为 `card_save --project <project>`，create 后后续请求及 SQLite 读回使用完整任务 id。原红态见 [baseline-08/verdict.json](baseline-08/verdict.json)，尚未启动窗口。

修后继续暴露两类旧断言：

1. 项目 id 必须出现在窗口正文。T-200、提交 `2286a2379`，票原文：“界面上项目的名字改用目录名，项目号只在需要时作为辅助信息”。[candidate-08/verdict.json](candidate-08/verdict.json) 的窗口显示 repo 目录名，后台 snapshot 中仍是正确 project id。改成严格检查目录名和只读文字，并另核对 snapshot 的 project_id。
2. IPC 完全相等清单仍含 `creationRepository/creationSubmit/creationCancel`，且漏掉 T-107 后的合法功能。`3070bbe1a0` 在 T-119 的“先添加项目，像普通终端一样启动 CLI、再申请角色/派发”的方向下删除新任务表单，切到 openProject；T-108、112、119、133～137、140、171、180、190、192、195 等继续增加接口。[candidate-08b/verdict.json](candidate-08b/verdict.json) 保存缺项/多项的完整比较。现行 sidebar 档位的清单据这些功能更新，继续使用**精确集合相等、无重复、无 Node require**检查，没有改成包含关系或忽略未知接口。历史 creation 档位保留其历史预期，未声称它在当前产品通过。

- 绿态：[green-08-final/verdict.json](green-08-final/verdict.json)：构建、真实 snapshot、缺失 launch 拒绝、真实 Electron 窗口四项全过；只读输入不记用户输入、看窗口不改门禁状态仍核对。`window/` 保存观察输出和截图。
- 区分度：[mutant-08/verdict.json](mutant-08/verdict.json)：后台 snapshot 错报 registered，真实 CLI 的 claimed 断言失败；此红态覆盖后台查询契约，没有宣称在变异下继续运行了窗口。
- 重跑：

```sh
python3 "$E/run.py" replay-08 python3 workbench/tests/test_electron_e2e.py --source "$PWD" --stage window --output "$E/replay-08"
python3 "$E/run.py" replay-red-08 python3 "$E/mutate.py" 08b
```

## 9. T-142 跨已打开项目开终端

**结论：测试过时；当前 PASS。**

先核对了决定：T-189 原文“主控可管多个项目——身份绑终端，不绑启动目录”；T-193 原文“主控身份绑终端，不再由启动目录决定项目；建卡、派发、验收时指定项目，限已打开的项目”。提交 `d832f38d321e2fcfd54ef383a99f022dca598a4e` 的 daemon diff 明确删除 terminal_open 的 `role_project_mismatch`，按请求项目找 opened project。因此“跨已打开项目必须拒绝”的两条断言均已过时，不是权限回归。

修改：两个方向都必须成功并指向正确项目；增加实际 pwd 读回；未打开项目必须 `project_not_opened`，指定项目后的 cwd 越界仍拒绝。未获批拒绝、同前缀兄弟目录与 symlink 逃逸拒绝、普通项目终端不混入任务布局等原检查均保留。

- 原红态：[baseline-09.json](baseline-09.json)：backend-only 真实 CLI/PTY 入口在 `approved_foreign_project_refused` 失败，回执为目标项目的真实 shell launch。
- 绿态：[green-09.json](green-09.json)：完整实际 Claude + 本地脚本接口 + Electron 场景，33 项通过。
- 区分度：[mutant-09.json](mutant-09.json)：恢复旧跨项目拒绝分支，准确在 `approved_opened_project_allowed` 失败。
- 重跑：

```sh
python3 "$E/run.py" replay-09 python3 workbench/tests/test_t142_terminal_open_e2e.py --summary "$E/replay-09.json"
python3 "$E/run.py" replay-red-09 python3 workbench/tests/test_t142_terminal_open_e2e.py --backend-only --mutant cross-project-denied --summary "$E/replay-red-09.json"
```

## 现场保留、清理与最终检查

失败夹具路径完整列在 [FIXTURES.md](FIXTURES.md) 与机器可读的 [retained-fixtures.json](retained-fixtures.json)，均由本次输出关联，未清理失败目录。关键原失败根目录：

| 项 | 原失败现场 |
|---|---|
| 1 | `/private/tmp/t133t-p23hx701`，及 baseline-01-repeat.json 中的 fixture |
| 2 | `/private/tmp/t78-domain-BnaUMV` |
| 3 | baseline-03 各 `*.json` 的 root，见 FIXTURES.md |
| 4 | `/private/tmp/t078-2-a13-rehearsal-EDEWas` |
| 5 | `/private/tmp/t184-u7mmoyzh` |
| 6 | `/private/tmp/t195-plybrfmk`；原测试按凭据保护流程删除了独立 Codex home，摘要如实记录 removed=true，未归档 auth 副本 |
| 7 | `/private/tmp/a4r-pheklh77/` 下五个 case |
| 8 | `/private/tmp/a2a4-4yng1egf` |
| 9 | `/private/tmp/t142-9ct1bnqe` |

成功运行已先保留摘要/命令/必要归档，再删除所关联的 `/private/tmp` 根目录，清理记录见 [cleanup.jsonl](cleanup.jsonl)。第 4 项成功场景由测试自身清理 scratch。第 8 项最终运行的构建槽也已删除。失败的反例源码副本保留，不沿 node_modules symlink 删除共享依赖。

`git diff --check`：PASS，见 [final-diff-check.log](final-diff-check.log)。项目地图 status：Problems 0、Stale living docs 0，见 [final-project-map.log](final-project-map.log)。没有更新票面 Resolution；由主控处理。

## 需要主控决定

1. **另开产品缺陷票：第 6 项 DST 日期扫描。** 当前 NO_GO，最小修法和影响见第 6 节；本票未改产品。是否顺带审计 collector 相同日历循环由主控决定。
2. **初轮临时目录边界偏差：INCOMPLETE。** 我漏设初轮 TMPDIR，UI 构建继承系统临时目录，确实写到了 `/var/folders/7v/58svbpnj5k91zdnm5zggb38h0000gn/T/`，不符合本次只写 worktree、指定证据和测试自身 `/private/tmp` 的边界。发现后 runner 已固定 `/private/tmp`，第 8 项最终窗口复验和清理亦在该目录内完成。已核对的旧构建槽有四处残留，精确路径见 [build-locations.json](build-locations.json)（candidate-08、candidate-08b、mutant-08、green-08）。其他初轮 Electron 测试自己的 stop 已删除其构建槽；未全面审计 CLI/Chromium 在系统 temp 下的所有临时文件。没有继续到授权范围外清理这四个残留，也没有把它们移走以隐藏偏差；由主控决定清理及是否接受该轮证据。
3. **后续 hc 受管切片的验收范围。** 第 7、8 项给定入口在当前基线已修好并通过，可以在后续切片中继续使用；换运行时后必须重新取得同版本红绿态，不能复用本票结果替 hc 运行时背书。第 1 项目前按 T-191 判定，后续“状态统一取 hc 事件”若改变用户契约，再据新票修订。
4. **未扩大到历史套件和旁支模式。** 共享夹具的其他调用者、A13 三种扩展、全部历史 IPC 档位未完整回归；本报告只给上述实际命令的结论，不宣称整个 workbench 测试集通过。

独立只读验收复核结果另见 `acceptance-review.md`；不把自动审查代替主控决定或产品发布许可。


## 第二轮

**对照与索引更新：PASS；测试集合整体仍为 INCOMPLETE。** 按本轮要求完成 23 个非历史测试的基线/候选对照，共 46 次；每次上限 1800 秒，无超时。5 项两边都通过，1 项由基线失败变为候选通过，0 项出现“基线过、候选不过”；另外 17 项仍失败或被前置条件阻断，没有上调为 PASS。本轮没有需要修复的新增回归，因此未再改测试、共享夹具或产品源码。

第一轮正文逐字保留。本轮用户已确认第一轮引用与 preload 通道，并已删除系统临时目录的四个旧构建槽、接受该次偏差；这是本轮收到的处置，不改写第一轮的原始记录。第 6 项按用户要求完全留给主控，本轮没有继续处理。

### 索引与范围

`workbench/tests/HISTORICAL.md` 已将 `controlled_quality_pty.ts` 从历史辅助表移入“已迁移到现行契约”，写明 T-219、T-141 native idle 与 scan 输入的迁移内容，以及直接导入 host 的实际复验边界。除这一个文件的条目、剩余辅助文件计数和迁移表标题外，其他表项、T-154 用户裁定原文、六份整测历史处置全部不变，见 [局部差异](round2/HISTORICAL.patch)、[逐项保真核对](round2/historical-scope-check.json)。

导入方核对使用 Python AST 本地 imports、TypeScript imports 及明确 host 引用，沿 Python 基类与 host 继续查找；另保存了要求的 [grep 原件](round2/import-grep.txt)。[完整 23 项与导入链](round2/import-audit.json) 包括用户点名的全部 12 项；额外 11 项是 daemon recovery、multiturn readback、bad worker、protected acceptance、quality widen、review worktree lifecycle、s3 quality joint、T-081 duplicate input、T-082 review boundary、T-090 review worker boundary、T-156 quality host credentials。

不把仅在字符串中读取源码、没有执行这些共享依赖的静态检查算调用方；不运行 `run_*.py` runner，不沿 runner 入口扩展任务。历史列表中的 `test_quality_tracer_e2e.py` 整套未运行，其仍可被现行测试导入的基类被上述实际调用者使用；这不改变它的历史处置。其他历史条目也未运行、未迁移。

基线按指定方式从 `git archive a09da15f9` 导出到 `/private/tmp/t219-r2-base-oia3s6yh`，再以 `cp -cR` 克隆当前 workbench/node_modules，没有创建 Git worktree，没有借用主 checkout、T-212 或 T-216 的源码或证据。来源、完整 argv 和克隆记录见 [baseline.json](round2/baseline.json)。候选运行当前 T-219 worktree，两个变体各运行各自版本的测试与产品源码。 worktree lifecycle 两边都用 `--phase candidate` 检查现行场景；它自己的 `--phase baseline` 要求另一个旧历史提交，不能用来代表本轮 a09da15f9。T-084 两边同用 `--phase green-05`；质量链/扩展套件通过显式 case 参数列出对应分组，精确选择见各次 COMMAND.txt。

所有测试固定 TMPDIR/TMP/TEMP=/private/tmp，后台服务保持原测试的独立进程组；监督器也对每个入口使用 start_new_session，并设 30 分钟硬上限。全部只用受控脚本化运行时/版本桩或离线逻辑，没有调用供应商模型，没有连接用户 Herdr/hc default core。没有写用户全局配置、产品源码或 `.project-map/`，没有 commit/push。

### 基线与候选对照

每个结果链接均指向该次完整命令；同目录的 stdout.log、stderr.log、meta.json 与 result/ 保留输出和内部测试收据。[机器可读总表](round2/table.json)、[详细失败提取](round2/comparison-details.json)、[重跑说明与 30 分钟监督器](round2/REPLAY.md) 一并保留。表内 BLOCKED 表示入口已实际运行但未进入业务路径，不是跳过或通过。

| 测试 | 基线结果与失败点 | 候选结果与失败点 | 判定 |
|---|---|---|---|
| `test_task_cards_e2e.py` | [INCOMPLETE：14 tests / 53 failures；无 daemon，`card_save/card_template` 连接 control.sock ENOENT](round2/runs/test_task_cards_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同为 14 / 53；同一缺 daemon 失败](round2/runs/test_task_cards_e2e/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_daemon_gates_e2e.py` | [INCOMPLETE：首项卡字段反例预期 invalid_task_card，实际 unknown_task](round2/runs/test_daemon_gates_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同一直接 card_save 反例仍缺 project，实际 unknown_task](round2/runs/test_daemon_gates_e2e/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_worktree_lifecycle_e2e.py` | [BLOCKED：git archive 副本无 .git，Preflight command failed](round2/runs/test_worktree_lifecycle_e2e/baseline/COMMAND.txt) | [BLOCKED：snapshot_source 缺 `evidence/2026-10-11-batch13/T-077/PLAN.md`](round2/runs/test_worktree_lifecycle_e2e/candidate/COMMAND.txt) | 两个运行前置条件不同，业务对照不完整；不能判为产品/夹具回归 |
| `test_t082_parent_launch_e2e.py` | [BLOCKED：exit 2，要求夹具位于外置盘，拒绝本次 /private/tmp 路径](round2/runs/test_t082_parent_launch_e2e/baseline/COMMAND.txt) | [BLOCKED：同一外置盘路径检查](round2/runs/test_t082_parent_launch_e2e/candidate/COMMAND.txt) | 既有运行边界冲突；未绕过，不修 |
| `test_t084_trailer_record.py` | [INCOMPLETE：card_save unknown_task → dispatch 无 attempt → KeyError](round2/runs/test_t084_trailer_record/baseline/COMMAND.txt) | [INCOMPLETE：相同链路；脚本自身直接建卡未带 project](round2/runs/test_t084_trailer_record/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_t078_cards_host_bootstrap.py` | [PASS：两代实际 cards host 凭据探针](round2/runs/test_t078_cards_host_bootstrap/baseline/COMMAND.txt) | [PASS：两代探针仍通过](round2/runs/test_t078_cards_host_bootstrap/candidate/COMMAND.txt) | 保持通过 |
| `test_conflict_trailer_proofs.py` | [INCOMPLETE：host 缺操作员凭据，operator_credential_required；随后 cleanup host exit 非 0](round2/runs/test_conflict_trailer_proofs/baseline/COMMAND.txt) | [INCOMPLETE：同一 host 凭据错误](round2/runs/test_conflict_trailer_proofs/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_relay_conflict_e2e.py` | [INCOMPLETE：host 缺操作员凭据，operator_credential_required；随后 cleanup host exit 非 0](round2/runs/test_relay_conflict_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同一 host 凭据错误](round2/runs/test_relay_conflict_e2e/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_multiturn_identity_e2e.py` | [INCOMPLETE：4 场 host 均未 ready，operator_credential_required；收尾又缺 state_readback](round2/runs/test_multiturn_identity_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同一启动与收尾失败](round2/runs/test_multiturn_identity_e2e/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_quality_chain_e2e.py` | [INCOMPLETE：red_manifest_missing 过；red_base_not_failing 在 card_save unknown_task](round2/runs/test_quality_chain_e2e/baseline/COMMAND.txt) | [INCOMPLETE：前 5 个场景过；red_feedback_idle 调 pane_release 时 CLI exit 2](round2/runs/test_quality_chain_e2e/candidate/COMMAND.txt) | 前置建卡被本票修好，后续旧 CLI 调用暴露；仍非整套通过，见 F1/F3 |
| `test_quality_legacy_e2e.py` | [INCOMPLETE：manual_claim_reviewed_score_refused 在 card_save unknown_task](round2/runs/test_quality_legacy_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同场景越过建卡，verify 为 review_launch_config_required](round2/runs/test_quality_legacy_e2e/candidate/COMMAND.txt) | 前置建卡被本票修好，后续旧 reviewer 配置暴露；见 F2 |
| `test_legacy_driver_readiness.py` | [PASS：5 个 readiness 检查](round2/runs/test_legacy_driver_readiness/baseline/COMMAND.txt) | [PASS：5 个检查仍通过](round2/runs/test_legacy_driver_readiness/candidate/COMMAND.txt) | 保持通过 |
| `test_daemon_recovery_e2e.py` | [INCOMPLETE：5 场均在 card_save unknown_task](round2/runs/test_daemon_recovery_e2e/baseline/COMMAND.txt) | [PASS：5/5，含 CAS 前后中断、外部 X、删引用、验收中断/锁](round2/runs/test_daemon_recovery_e2e/candidate/COMMAND.txt) | 本票补项目身份、native idle、模板转交与按字段审查提交，修复原夹具 |
| `test_multiturn_readback.py` | [PASS：5 项夹具读回反事实](round2/runs/test_multiturn_readback/baseline/COMMAND.txt) | [PASS：5 项仍通过](round2/runs/test_multiturn_readback/candidate/COMMAND.txt) | 保持通过；仅夹具读回证据 |
| `test_bad_worker_e2e.py` | [INCOMPLETE：oracle_test 在 card_save unknown_task](round2/runs/test_bad_worker_e2e/baseline/COMMAND.txt) | [INCOMPLETE：oracle_test 越过建卡，在 pane_release CLI exit 2](round2/runs/test_bad_worker_e2e/candidate/COMMAND.txt) | 原前置解除，后续既有问题；见 F1/F3 |
| `test_protected_acceptance_e2e.py` | [INCOMPLETE：oracle_modified 在 card_save unknown_task](round2/runs/test_protected_acceptance_e2e/baseline/COMMAND.txt) | [INCOMPLETE：oracle_modified 越过建卡，在 pane_release CLI exit 2](round2/runs/test_protected_acceptance_e2e/candidate/COMMAND.txt) | 原前置解除，后续既有问题；见 F1/F3 |
| `test_quality_widen_e2e.py` | [INCOMPLETE：widen_red_rules_success 在 card_save unknown_task](round2/runs/test_quality_widen_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同场景越过建卡，在 pane_release CLI exit 2](round2/runs/test_quality_widen_e2e/candidate/COMMAND.txt) | 原前置解除，后续既有问题；见 F1/F3 |
| `test_review_worktree_lifecycle_e2e.py` | [INCOMPLETE：cleanup_after_persisted_result 在 card_save unknown_task](round2/runs/test_review_worktree_lifecycle_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同场景越过建卡，在 pane_release CLI exit 2](round2/runs/test_review_worktree_lifecycle_e2e/candidate/COMMAND.txt) | 原前置解除，后续既有问题；见 F1/F3 |
| `test_s3_quality_joint_e2e.py` | [INCOMPLETE：same_candidate_reuses_review 在 card_save unknown_task](round2/runs/test_s3_quality_joint_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同场景越过建卡，在 pane_release CLI exit 2](round2/runs/test_s3_quality_joint_e2e/candidate/COMMAND.txt) | 原前置解除，后续既有问题；见 F1/F3 |
| `test_t082_review_boundary_e2e.py` | [INCOMPLETE：tracer_review_copy 的 T082-REVIEW-VERDICT，未变 verified](round2/runs/test_t082_review_boundary_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同一断言；仍用 last_assistant_message 交审查，review_result_missing](round2/runs/test_t082_review_boundary_e2e/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_t090_review_worker_boundary_e2e.py` | [INCOMPLETE：worker_head_changed 等不到 review_reclaimed，原审查已因 review_result_missing 暂停](round2/runs/test_t090_review_worker_boundary_e2e/baseline/COMMAND.txt) | [INCOMPLETE：同一审查协议失败](round2/runs/test_t090_review_worker_boundary_e2e/candidate/COMMAND.txt) | 既有问题，同点；不修 |
| `test_t156_quality_host_credentials.py` | [PASS：真实两代 QualityCase/host 凭据检查](round2/runs/test_t156_quality_host_credentials/baseline/COMMAND.txt) | [PASS：仍通过](round2/runs/test_t156_quality_host_credentials/candidate/COMMAND.txt) | 保持通过；serve 被探针替换，不是 PTY 全流程 |
| `test_t081_duplicate_input.py` | [PASS：矛盾尾注输入与真实 git interpret-trailers 检查](round2/runs/test_t081_duplicate_input/baseline/COMMAND.txt) | [PASS：仍通过](round2/runs/test_t081_duplicate_input/candidate/COMMAND.txt) | 保持通过；只证明输入构造 |

### 两边都失败、但失败点不同的依据

这类结果没有硬塞进“同点失败”，也没有因候选推进了几步就判通过：

- **F1，旧 pane_release CLI 入口。** bad worker、protected acceptance、quality chain、quality widen、review worktree lifecycle、s3 quality joint 在基线先被缺 project 的 card_save 挡住；候选补齐项目后，执行到 QualityCase.release_worker 的旧 pane_release 调用，CLI exit 2。基线产品本来就没有该命令；本轮对两个 CLI 做同一窄探针，均 exit 2。产品、QualityCase.release_worker 和相关调用者在基线/候选之间无差异，见 [诊断原件](round2/unmasked-existing-failures.json)。因此是被前置修复揭露的既有夹具问题，未修改该路径。
- **F2，旧 reviewer 配置。** quality legacy 越过建卡后，verify 返回 review_launch_config_required。它继承的旧 QualityCase 仍写 reviewers 数组，未提供现行单个 reviewer_role_card 配置；这段配置及产品检查同样在基线已存在，未被本票改动。未扩大修复范围。
- **F3，收尾捕获失败。** 部分 F1 场景还记录 Unexpected non-regular request evidence；完整 cleanup_failures 保留，没有屏蔽。既有套件未完成，不能只按前置建卡修复对它们给绿态。
- **worktree lifecycle 的环境阻断。** git archive 副本没有 .git，旧 preflight 执行 git rev-parse/git diff 失败；候选可以通过该检查，但其源码归档要求的历史 `evidence/2026-10-11-batch13/T-077/PLAN.md` 在当前 checkout 未展开，报 FileNotFoundError。两边都没有进入业务场景，不能据此评判 worktree 功能或判定共享夹具回归。没有创建额外 Git worktree、伪造 Git 版本、补造历史证据或改 preflight 来制造通过。

同点失败的其他测试只记录失败位置，不在本轮修复。T-082 parent launch 的外置盘硬限制与本轮写入边界相冲突，实际命令在两边均被路径检查拒绝；未到后续逻辑的两个 sibling case 也不补称已验证。各套件自身因首个 harness failure 停下的后续场景没有算作通过。质量链在候选上前 5 场通过、基线仅第 1 场通过，是局部推进，不是整个套件变绿。

### 实际覆盖、清理与收尾

直接导入 controlled_quality_pty 的五个 host 中：daemon_acceptance_host 已由 recovery 五场通过；quality_chain_host 被质量测试及凭据探针执行，但质量串仍有上述旧入口/配置失败；t152_review_host 被 T-082/T-090 调用，仍在旧审查提交协议处失败；multiturn_identity_host 尝试启动后因缺操作员凭据退出，未证明 PTY 行为；conflict_acceptance_host 的 worktree 调用者在前置步骤失败，未实际触及该 host。索引据此区分“已实跑”“通过”和“未触及”，没有宣称全部导入方都完成业务复验。

成功运行保留收据后清理其自身 `/private/tmp` 夹具，见 [清理记录](round2/cleanup-passed.json)；测试自行使用 TemporaryDirectory 清理的在原收据中保留说明。所有失败目录及基线导出目录继续保留，见 [失败夹具清单](round2/retained-fixtures.json)。T-084 因异常未写最终摘要，其 host argv 与逐条 commands.jsonl 已保留，并据此补录失败夹具位置。最后未发现仍运行的本轮测试 host，见 [进程核对](round2/owned-host-process-check.json)。

最终 git diff --check 与 project-map status 的原件见 [diff 检查](round2/final-diff-check.log)、[地图检查](round2/final-project-map.log)。两项均 PASS；地图 Problems 0、Stale living docs 0。第二轮只新增 HISTORICAL.md 的授权局部修订及外部证据/报告追加，未改第一轮代码候选和正文。
