# T-148-1 / a1 交付

状态：INCOMPLETE。夹具修复和本地检查已完成；真实 Electron、T-127/T-141 原生 CLI 回归及独立审查等待执行主控。不得据此关闭 ticket 或宣称 main 全绿。

分支 `exec/t148`，起点 `cca4f8beb`；产品代码未改。用户派发身份为 worker `b23-t148`，task `T-148-1`，attempt `a1`。最终代码版本以本报告所在提交为准，未手写 A2A 尾注。没有启动 Electron、调用供应商模型、修改用户全局配置、集成或 push。

## 夹具前后对照

| 文件 | 修改前 | 修改后与契约依据 |
| --- | --- | --- |
| `test_t146_reviewer_hooks.mjs` | 手写 Claude argv：strict MCP、无开放网络、PreToolUse 缺 MCP 权限 hook | 调用真实 `Panes.createPane`，在 launch 持久化边界截取 argv，先于 PTY spawn 停止。模型和 effort 固定为原夹具值，仅归一化随机 launch/native session id。由 T-141 的真实启动来源提供取消 strict MCP、网络全开、MCP hook。门禁、断言和八种坏输入仍是原实现。 |
| 同上 `changeSettings` | 固定读写 argv[15] | 从 `--settings` 定位夹具 JSON；删除 strict 参数后不再偏移。只改变变异的目标定位，不改变任何变异、拒绝条件或检查名。`changed_cli_flag` 的 argv[11] 仍指向固定 CLI flag，原变异不动。 |
| `t145_mouse_receiver.c` | 输出 Open restricted 和 bracketed-paste 开启，没有 native ready 包 | 模拟已信任 Codex 正常启动：保留 bracketed paste，发送 `ESC ]7501;state=idle:app=codex ESC \\`。与 T-141 已信任启动信号一致，后续原生字节接收、session metadata 和鼠标模式逻辑不动。 |
| `legacy_quality_driver.py`、`t112_reviewer_record.mjs` | 注释暗示选择 restricted 后即可派发 | 注释明确审查员候选副本可受限打开，但派发还需要 native readiness。 |
| `run_t112_native.py` | 注释把 worker 的 restricted 事件当作当前启动契约 | 注释标明这是历史观察条件，T-141 已信任 worker 不需要该事件；保留原检查并上报。 |

`test_t145_mouse_reports_e2e.py` 未改。所有原断言、检查名、变异和超时均未修改。`oracle-preservation-local-01.json` 记录了 Python AST、JS 注释外文本，以及 T-146 断言和完整变异块的对照检查。

## 本地证据

下列命令均在本 worktree 运行，摘要路径都位于本目录；运行夹具保留在摘要记载的 `/private/tmp` 路径，由执行主控按 T-088 归档。本地 Node 为 `/opt/homebrew/Cellar/node/26.5.0/bin/node`。

| 检查 | 命令与结果 |
| --- | --- |
| T-146 旧夹具红态 | `node workbench/tests/test_t146_reviewer_hooks.mjs evidence/2026-10-23-batch23/T-148/t146-before-01.json .`，exit 1，`review_launch_boundary`，checks 为空；与合并回归失败一致。 |
| T-146 修后 | 同命令换为 `t146-after-01.json`，exit 0，PASS；批准启动和全部八种拒绝检查通过，包含 `changed_cli_flag_rejected`。 |
| T-141 启动 argv | `node workbench/tests/test_t141_launch_contract.mjs evidence/2026-10-23-batch23/T-148/t141-launch-local-01.json .`，exit 0，PASS。 |
| T-141 reviewer | `node workbench/tests/test_t141_reviewer_contract.mjs evidence/2026-10-23-batch23/T-148/t141-reviewer-local-01.json .`，exit 0，PASS。两种 CLI 的生产启动与边界变异均通过。 |
| T-141 ready 信号 | `node workbench/tests/test_t141_startup_signal.mjs evidence/2026-10-23-batch23/T-148/t141-startup-local-01.json .`，exit 0，PASS；含 captured untrusted/unset 反例。 |
| T-145 协议方法 | `node workbench/tests/test_t145_protocol_input.mjs evidence/2026-10-23-batch23/T-148/t145-protocol-local-01.json .`，exit 0，PASS；不代表 Electron E2E。 |
| T-145 完整修复还原 | 在临时生产副本中逆向应用 `7494d167c` 对 `panes.ts` 的完整差异，保留 T-141；同一协议方法测试以该副本为 source，exit 1，原断言 `terminal report must not become user input` 失败。`t145-revert-check-local-02.json` 记录确切命令，`.revert.json` 与 `.revert.patch` 记录来源和实际反向补丁。此项仅验证还原器和方法反例，不冒充真实 E2E 红态。 |
| C 编译 | `/usr/bin/clang -Wall -Wextra -Werror -std=c11 -fsyntax-only workbench/tests/t145_mouse_receiver.c`，exit 0。 |
| 脚本与差异 | `zsh -n evidence/2026-10-23-batch23/T-148/RUN-OUTSIDE-01.sh`、`git diff --check`，exit 0。 |
| project-map | session 开始和交付前运行规定的 `project_map.py status --root .`，Problems 0、Stale living docs 0。结束结果见 `project-map-final.txt`。 |

首次调试新还原器时，仓库根目录计算多上一层，出现 `ModuleNotFoundError: No module named 'scripted_claude'`，未生成业务摘要，不算红态；改正根路径后完整反向补丁成功，保留 `02` 编号与本记录，不把首次结果改称通过。

T-145 旧夹具的真实 E2E 红态沿用执行主控提供的 `../merge-1/run-20261023T170406Z/t145-green-rerun-alone.json`：exit 1，超时“受管 receiver 就绪并收到派发”，checks 为空。这是夹具失配证据，不是 T-145 鼠标业务修复的红态。

## 沙箱外验证

运行：`zsh evidence/2026-10-23-batch23/T-148/RUN-OUTSIDE-01.sh`。每次建立新 `outside01-*` 目录，逐项保存命令、stdout、stderr、exit 和摘要，前项失败仍收集后项。只在全部满足时 MANIFEST 报 PASS。

包含 T-146 绿态与原八种坏输入、T-145 绿态、完整还原 T-145 修复的 E2E 红态、record/drop 两个原变异、T-127 绿态、T-141 绿态与三个契约检查。红态及变异必须失败在原检查，且先通过 receiver 身份、适用的坐标字节和完整报告检查，不能把启动失败当作业务红态。

`t145_reverted_fixture.py` 仅在 `/private/tmp` 的 HEAD 产品副本中逆向应用原 T-145 产品修复，再执行未修改的 E2E；不使用整个 T-145 前版本，因为那会丢失 T-141 的新启动契约。它不改 checkout，不新建或移动 Git 分支，不改门禁或断言。外部脚本未在本沙箱执行；真实边界和独立审查结论待主控补充。

## 其他旧契约清点

搜索命令：`rg -n 'Open restricted|restricted_open|network_access=false|network_proxy=false|strict-mcp-config|CODEX_HOME.*!=' workbench/tests`，原始列表见 `stale-contract-search.txt`。

| 分类 | 文件与处理 |
| --- | --- |
| 已修夹具或注释 | T-146 argv、T-145 receiver；legacy_quality_driver、run_t112_native、t112_reviewer_record 的旧叙述。 |
| 已确认旧断言，未改 | `test_t112_execution.mjs`、`diagnose_t112_reviewer.py`、`test_quality_tracer_e2e.py`、`test_t082_review_boundary_e2e.py` 要求关网络；quality tracer 另要求独立 home。`run_pane_lifecycle.py`、`run_worker_delivery.py` 检查 context 网络关闭。`test_t122_claude_worker_e2e.py` 要求 strict MCP 且旧变异定位失配。`run_t112_native.py` 要求 worker restricted-open 事件。断言修改超出授权。 |
| 需要联动旧测试的夹具，未改 | `controlled_quality_pty.ts` 对所有角色只发 restricted 屏，无 native ready，第一条 Enter 被吞作受限打开。其调用方含旧启动/权限断言，交主控另卡迁移；不在本卡单独改到半可用状态。 |
| 现行契约或有意反例，保留 | T-141 的 launch/reviewer/startup/E2E、`test_t141_t127_oracle.py`、`test_t082_parent_launch_e2e.py`；T-127 的旧事件仅作为观察列表记录，实际启动判断已覆盖 native ready，不是必须产生旧事件的断言。T-141 startup probe 中 Open restricted 是真实不可信目录探针，有意保留。 |
| 日期探针/能力夹具，保留且未重跑 | `prepare_t081_capability*.py/ts`、`run_t081_capability_recheck.py`、`run_t081_commit_scope.py` 固定历史能力 profile；`probe_t093_normal_login.py`、`probe_t108_claude_hook.py` 使用 strict MCP 做隔离探针；`run_t078_p1.py` 检查 CLI 是否支持该参数，没有要求当前启动继续带它。没有将这些历史通过结论当作本候选证据。 |

范围外问题已通过 `scripts/inbox send` 报 triage，id `20261023T172046Z-worker:b23-t148-issue-001`，正文见 `ISSUE-stale-oracles.md`。按卡片不修改 `.project-map`；该命令生成的追加式 inbox 条目保留在工作区，未纳入本交付提交，供主控接收。当前产品仍选择不持久化的 Open restricted，任务释放改等 native ready；这一点与原合并 NOTE 的根因表述有差异，也已一并上报。

后续由执行主控运行沙箱外脚本、收取范围外问题、取得新候选的独立 behavioral-acceptance-review，再走验收与集成。本 worker 不代替主控给出通过结论。
