# T-136 候选 1 结果

- **候选**：`01e0effd7`（复盘、T-135 审查 01 的 P2、T-132 审查 02 的 P3），测试的提前退出修正在下一个提交里（只改测试）。
- **修前版本**：`1dc2b76c3`（与 `8a8e1720c` 的 workbench 相同）。
- **结论**：**INCOMPLETE**，等真实 haiku 运行与独立审查。

## 改了什么

- **`src/retrospective.ts`**：
  - **周期**：存在工作台自己的库里，只追加。默认每周一 9:00、Claude Code、`claude-opus-5-5`、medium。从首次存在（或每次修改）的时刻起生效，之前的时间点不补跑。每个项目每个时间点只跑一次。
  - **复盘包**：时间范围默认从这个项目上次复盘的结束时间到现在。包里有：
    - 范围内有事件的任务；
    - 门禁逐项结果、打回原因、审查结论、打分；
    - 问题上报、面板问答、用户输入与介入；
    - 范围内提交的 A2A 尾注（没有尾注的提交单独计数）；
    - 指标快照（T-134）；
    - 轨迹归档路径（T-135）。
  - **会话的写入范围**：只能写这次复盘的 `out/`。
    - **Claude Code**：每会话的 `--settings` 只放行 `out/` 的编辑，禁止编辑项目目录；沙箱只许写 `out/`、不许写项目目录。Claude 的沙箱默认允许命令写工作目录，而复盘会话的工作目录就是项目目录，所以这两条禁止是必需的。变异 `out-not-confined` 去掉它们后，shell 重定向写进了项目（`rc=0`）。
    - **Codex**：以 `out/` 为工作目录，workspace-write 沙箱，只在本次会话里把 `out/` 记为信任，不写用户的 Codex 配置。
  - **导入**：`report.md` 与可解析的 `suggestions.json` 都在时，报告复制到项目的 `findings/`（没有这个目录就留在数据目录），建议逐条入库。`suggestions.json` 不是合法 JSON 或不是列表时，记一次 `import_failed`，之后每次检查重试，修好就导入。
  - **建议的处理**：批准或不采纳都只追加记录，不自动写 ticket。
- **后台**：
  - “立即复盘”与周期复盘都开一个普通项目终端，在里面运行所选 CLI；`retrospective_started` 事件记下 argv、原生会话与原生 home。
  - 每分钟检查一次周期，导入写完的复盘；`retrospective_tick` 可注入时钟。
  - 只读命令 `retrospective_list`；操作员命令 `retrospective_start`、`retrospective_schedule_save`、`retrospective_tick`、`retrospective_decide`。
- **轨迹归档**：复盘会话也归档（经 `retrospective_started` 的原生会话找到记录）。
  - T-135 审查 01 的 P2 一并修了：一个读不了的原生记录不再挡住整轮扫描，失败按来源和错误各记一次。
- **界面**：新增“复盘”页签，包括：
  - 立即复盘（选 CLI、模型、思考强度）；
  - 定期复盘的开关、星期与时间；
  - 改进建议（批准 / 不采纳）；
  - 复盘记录（进行中 / 已完成 / 导入失败）。
  - 各工作区页面按项目加 key（T-132 审查 02 的 P3）。
- **已知边界**：Claude Code 复盘会话用用户自己的 Claude 配置，在项目目录启动。用户没在自己的 Claude 里信任过这个项目时，Claude 会在终端里问，a2a 不代答（代答会写进用户配置），定期复盘会停在那一步。测试模拟的是已信任项目的用户。

## 端到端（`e2e/commands.sh`）

正式运行在 `01e0effd7` 的干净分离 worktree 里进行。复盘会话是真实 Claude Code，模型是本地脚本化接口。期望来自 ticket 与场景：

1. T-1 报一个问题，用户答复，审查通过后集成。之后从界面选 `claude-haiku-5-5`，点“立即复盘”。
2. 包里只有 T-1，以及它的问题、答复、审查、打分、尾注。复盘会话先写报告，再试着用 Write 工具和 shell 重定向写项目，最后写建议。
3. 报告进 `findings/`，建议在页面上批准。
4. 复盘前把 T-1 的原生记录改成不可读，复盘会话照样归档，失败只按来源各记一次。
5. T-2 在第一次复盘之后才创建并集成，第二次复盘的包只有 T-2。
6. 第二次复盘的会话留下坏的 `suggestions.json`：导入失败只记一次，页面显示失败；修好后导入。
7. 周期设在两天后，用注入的时钟：到点前不启动，到点启动一次，同一时刻再查不重复；在页面上关掉后，下一周不启动。

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，10 项 | — |
| red-parent（`--revision 1dc2b76c3`） | 失败 | 没有“复盘”页签 |
| mutant-package-ignores-range | 失败 | `second_package_only_in_range`（第二次的包里有 T-1） |
| mutant-out-not-confined | 失败 | `session_writes_outside_refused`（shell 写进项目，`rc=0`） |
| mutant-schedule-fires-when-disabled | 失败 | `schedule_off_does_not_fire` |
| mutant-import-failure-silent | 失败 | 页面上等不到导入失败 |
| mutant-archive-source-not-isolated | 失败 | 复盘会话没有归档（扫描在第一个读不了的记录上中断） |
| t135-green | PASS，6 项 | — |
| t132-green | PASS，6 项 | — |
| t122-green | PASS，23 项 | — |

摸底运行 `probe-01` 至 `05` 原样保留：
- `01`：T-2 的卡在第一次复盘前就建了，按 ticket 理应进第一次的包，是测试场景写错了。
- `02`：打分字段路径写错。
- `03` 至 `05`：逐步加上坏建议文件与不可读来源的检查。

几个失败的运行在恢复权限前就退出了，夹具里留下不可读文件。归档前已恢复这些文件的权限，测试也改成在 `finally` 里恢复。夹具已归档，见 `fixtures.archive.json`；截图在夹具的 `out/` 里。

## 真实运行（`real-haiku/commands.sh`）

用户自己的 Claude Code，`claude-haiku-5-5`、low，从界面“立即复盘”启动；后台、终端、界面都是真实的，HOME 与 Claude 登录是用户自己的。只跑复盘，不派 worker，所以复盘包里只有初始提交和终端主控会话。项目目录放在用户自己的 Claude 早已信任过的路径，a2a 不代答信任、不写用户配置。

| 运行 | 结果 | 说明 |
| --- | --- | --- |
| run-01 | 失败 | 测试环境没带 `USER`，Claude 在钥匙串里找不到登录，终端显示 “Not logged in”，会话没写出文件；900 秒后超时。产品启动后台时传完整环境，不受影响。`claude auth status` 对照：去掉 `USER` 时 `loggedIn: false`，带上时 `true`。 |
| run-02（`a8fd8697a` 之后的 `--detach` 版本，见 commands.sh） | PASS，4 项 | 启动参数里是所选模型；会话只写了 `out/report.md` 与 `out/suggestions.json`，项目里除导入的报告外没有改动；报告进了 `findings/`；建议 0 条，页面也是 0 条。 |

run-02 的真实模型调用：3 次，全是 `claude-haiku-5-5`（读一次复盘包，写两个文件）。报告与建议的副本在 `real-haiku/run-02-report.md`、`run-02-suggestions.json`；报告只写包里有的东西，逐条注明依据。夹具（含截图、移入的项目目录）已归档，见 `real-haiku/fixtures.archive.json`。Claude 自己的会话记录照常写在用户的 `~/.claude/projects/` 下，这是用户的 CLI 正常运行的结果，不是 a2a 写的。

## 未覆盖

- Codex 复盘会话没有端到端，只有代码路径。
- 打包后的应用。
