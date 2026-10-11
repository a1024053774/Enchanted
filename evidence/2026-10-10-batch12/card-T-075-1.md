# 任务卡 T-075-1

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这一张卡。T-075 一共拆成 4 张卡，串行做，每张卡只有一个写入者：
1. **本卡**：把门禁搬进本仓库，并重新证明；
2. 三项契约改动和任务卡命令；
3. 编排后台、Codex 窗格，跑通一次真实交付；
4. 最小 Electron 窗口和常驻行为。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-075-1 |
| 来源 | ticket T-075，`ready_rev: 2` |
| 目标 | 门禁从 fork 的 `packages/a2a-gates` 搬到本仓库新建的 `workbench/`，用 Node 运行，不再依赖 `@synara/*`。`acceptance/entry/` 里的入口改指新位置，fork 里的门禁不再作入口。交付 8 项、恢复 9 项、编排 18 项在新位置重新取得红态、绿态和反例。 |
| 非目标 | 不改门禁契约：路径边界、尾注核对、集成目标改为工作分支都留给 T-075-2。不做编排后台、窗格、任务卡命令和 Electron。不改 Synara fork。不搬 Synara 的 provider 或 MCP 网关代码。 |
| 修改边界 | 允许：新目录 `workbench/`（门禁源码、它自己的 package.json 和 lockfile、测试）；`acceptance/entry/` 下的入口；本卡证据目录 `evidence/2026-10-10-batch12/T-075/`；ticket T-075 的 Resolution。禁止：`acceptance/test_*.py` 的断言与预期（只允许改它们选入口的那一处）、`scripts/`、`.project-map/specs/`、Synara fork、全局配置。 |
| 完成条件 | 见下方“完成条件”。 |
| 红态命令 | 在起点提交上，把入口指向尚不存在的 `workbench/` 门禁后跑三套测试，必须失败。 |
| 任务类型 | 重构 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求（2026-10-11 用户临时规定） |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t075-1`，经 `scripts/launch-worker` 启动） |

## 我已定的做法
- **来源版本**：以 fork 已推送的 `49cae984f` 为准。fork 当前 HEAD `ddb765956` 是 T-066 未推送、未审查的提交（spec 第 11 节规定保留不推），不搬它的改动。读 fork 用 `git -C ../synara show 49cae984f:<路径>`，不切换 fork 的分支，也不往 fork 写任何东西。
- **替换两处 Synara 依赖**：
  - `@synara/contracts`：只搬门禁实际用到的 schema 和类型，放进 `workbench/`。
  - `@synara/shared/processRuntime`：用 Node 自带的 `child_process` 写一个最小实现。
  - 搬过来的文件保留 Synara 的 MIT 版权声明。
- **运行时**：Node v26（已装），优先用它原生的 TypeScript 类型剥离，不引入 Bun 或打包步骤；确实跑不了再上报，由我定。`effect` 等第三方依赖照旧用 npm 装，`npm --cache` 指向 `/Volumes/WD-Elements` 下的新目录，外置盘没挂载就报错。`node_modules` 放在 `workbench/` 里，不要链接到别处。
- **Synara 线程 runtime 的处理**：门禁里与 Synara 线程 runtime 相关的部分（dispatch、attach、run，以及 `GateRuntime` 接口），保留接口和语义，把实现边界标清楚。编排 18 项沿用现有的“边界替身”做法，并标明是隔离证据。真实窗格 runtime 由 T-075-3 接上。如果某项契约离开 Synara 就无法成立，停下写 needs-decision。
- **只留一套路径**：`acceptance/entry/a2a_gates.py` 和 `native-entry.*` 改指新位置后，本仓库里不再有调用 fork 门禁的路径。fork 自身不动。

## 完成条件（交付前跑一遍并保存输出）
1. **红态**：在起点提交上，入口指向 `workbench/` 时，三套测试失败，失败原因是入口或实现不存在。
2. **绿态**：在候选上分别跑以下三条，全部通过，测试项数分别为 8、9、18：
   - `python3 -B acceptance/test_coop_e2e.py`
   - `python3 -B acceptance/test_recovery_e2e.py`
   - `python3 -B acceptance/test_run_e2e.py`
3. **反例**：至少 3 个变异体，每个都必须让对应测试失败，各留输出。三个变异体分别是：
   - 去掉 fence 校验；
   - 去掉 CAS 的期望旧值；
   - 去掉操作锁。
4. 下面的命令输出为空：
   ```sh
   grep -rn "@synara/\|\.\./synara\|synara/packages" workbench acceptance/entry
   ```
   这里只匹配代码引用，不算 MIT 声明里的“Synara”字样；声明请写成不含这三个模式的形式。
5. `cd workbench && npm ls --depth=0` 正常退出，并记下 npm 缓存目录。
6. `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` 结果为 0 problems。

## 审查与交付
- **审查**：实现完成后，开一次 fresh-context 的只读独立审查，原文存证据目录。审查发现的问题先做红态再修复，不追审，由我审修复部分的 diff。
- **交付**：
  - a2a 提交，提交带 `A2A-*` 尾注，由启动入口自动加上；
  - `T-075/RESULTS.md`，写明来源版本、替换清单、npm 缓存位置和三套测试的项数；
  - ticket Resolution 写“T-075-1 完成，待后续卡”，保持 open；
  - 终端最后一行：`T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 本卡不需要真实 Codex 被测会话；如确需，停下问我。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放本批目录 `evidence/2026-10-10-batch12/T-0xx/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
- 补充（本卡）：`npm install` 需要联网，沙箱默认不联网。只为这一条安装命令按沙箱提示申请升级权限，不换工具绕过；被拒就停下报告。
