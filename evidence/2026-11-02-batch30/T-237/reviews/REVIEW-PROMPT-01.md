# T-237 只读审查请求（第 1 轮）

你是独立审查员，只读：不改任何文件，不运行会改动仓库或用户环境的命令，不 push。结论写到 `evidence/2026-11-02-batch30/T-237/reviews/REVIEW-01.md`（这是你唯一可写的文件），中文。

## 背景

- Ticket：`.project-map/tickets/T-237-stale-retrospective-shows-running.md`。复盘的 CLI 退出、或后台重启后它的终端已不在，Reflect 页那一行仍一直显示“进行中”。
- 候选改动（未提交，基于 HEAD `82e747f4a`）：`evidence/2026-11-02-batch30/T-237/candidate.diff`，涉及 `workbench/src/daemon.ts`、`panes.ts`、`retrospective.ts`、`workbench/app/RetrospectiveSections.tsx`、`workbench/README.md`，新测试 `workbench/tests/test_t237_retrospective_end_e2e.py`。
- 做法：每分钟的复盘检查（`retrospectiveTick`）在导入之后，对已启动、未导入、未结束的复盘查它的终端（`Panes.shellFront`）：终端不在 → 记 `ended`（`terminal_gone`）；启动满 60 秒后终端回到提示符、前台没有程序 → `ended`（`cli_not_running`）；前台有程序 → 仍是进行中。界面优先级：已完成 > 没能启动 > 导入失败 > 已结束 > 进行中。
- 证据：`evidence/2026-11-02-batch30/T-237/` 下 `green-1..3.json`（候选三次 PASS）、`red-*.json`（修前基线 `2b3b12dac` 与四个变异都失败在对应业务检查上）、`run-red.sh`；回归 `run-regression.sh` 正在跑。

## 请重点看

1. 正确性：`shellFront` 判“程序在前台”的方式（`pid==pgid==tpgid` 且不是 shell 本身）对复盘的 CLI 是否成立；终端不在的各种情形（关掉终端、后台重启后未恢复、`pane_gone_confirmed` 的占位窗格 `stopped: true`）是否都判成 `gone`；有没有会把还在运行的复盘误判结束的情形。
2. 时间：宽限用的是 tick 的 `now` 与 `started` 事件的 `created_at`；后台每分钟用真实时间调用，测试注入 `now`。有没有时区或时钟问题。
3. 一个复盘的 `shellFront` 抛错只记 `retrospective_end_check_failed` 并跳过，会不会每分钟刷一条事件、或吞掉不该吞的错误（项目规则：不加未经证据支持的 fallback、不吞异常）。
4. 测试是否真的能抓住缺陷：失败方式清单、四个变异、修前基线；有没有覆盖不到但应该覆盖的情形（例如界面文字、已结束的复盘之后又导入）。测试里 `pkill -f <夹具目录>` 是否只会杀本夹具的进程。
5. README 与代码是否一致。

每条意见标明：阻塞 / 非阻塞，给出文件与行号、失败场景。最后给结论：PASS（无阻塞意见）或 NO_GO。
