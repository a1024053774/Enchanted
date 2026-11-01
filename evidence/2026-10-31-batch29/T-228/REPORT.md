# T-228 报告（主控在会话里写，2026-11-01）

基线 `03ba1cf54`（main），当前候选 [candidate.patch](candidate.patch)（第三轮），前两轮为 [candidate-round1.patch](candidate-round1.patch)、[candidate-round2.patch](candidate-round2.patch)。改在 main checkout 的工作区，未提交。

## 改动

- `workbench/src/hc.ts` `HcRuntime.start()`：去掉“core 父进程必须是 1”；保留“core 不在后台的进程组里”。新增判据：后台连上的那个 core（第三轮起经同一连接的 `server.status` 取 pid）打开着本会话私有状态目录里的 `core.lock`。第二轮起把锁路径作为参数交给 `lsof -a -p <pid> -Fp -- <lock>`，由 lsof 按文件身份匹配，输出含 `p<pid>` 才算；lsof 退出非 0、超时、没有输出都拒绝，错误里带 pid、锁路径和 lsof 的 stderr。
- `workbench/src/daemon.ts`：启动时 `hc.start()` 失败，先记 `hc_start_failed` 事件（含原因），再照旧抛出，后台不启动。第二轮起事件写入也失败时，抛出同时含两个错误的 `AggregateError`，不让写入错误盖掉原来的启动错误。
- `workbench/README.md`：写明认 core 的规则。
- `workbench/tests/test_t212_shell_hc_e2e.py` 的 `--core-crash`：新 core 的环境标记原来只许 `restarted-daemon`。这实际是把“后台在 holder 重拉前重启”的时序写死了（T-220 已指出）。现在也接受 `initial-daemon`，即 holder 用首个后台的受控环境重拉的 core；私有 XDG 目录的要求不变。
- 新增 `workbench/tests/test_t228_core_identity_e2e.py`，失败方式 1–9 写在文件开头。

判据怎么来的：探针用固定版本 hc 0.1.15 在一次性目录起私有 core，`lsof` 显示它一直打开着 `XDG_STATE_HOME/herdr-core/<session>/core.lock`（锁里写的是 socket 路径）和 `core.log`。`core.json` 里只有机器级的 id 与名字，不能区分。外来 core（同 session、同 socket、默认 XDG）的锁在 `$HOME/.local/state/herdr-core/<session>/`，用例里已确认它存在。

## 运行

命令都在 `/Users/luckye/Documents/Code/a2a` 执行，T-228 用例另加 `ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache`：

```sh
TMPDIR=/private/tmp python3 workbench/tests/test_t228_core_identity_e2e.py --case holder|foreign --output <dir>
TMPDIR=/private/tmp python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output <dir>
TMPDIR=/private/tmp /Applications/Xcode.app/Contents/Developer/usr/bin/python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output <dir>
```

| 运行 | 结果 |
| --- | --- |
| [修前 holder](red-holder-01/run.json) | 退出 1：`daemon_accepted_holder_core` 失败，后台 stderr `private hc core did not detach` |
| [修前 foreign](red-foreign-01/run.json) | 退出 1：`daemon_refused_foreign_core`、`refusal_event_with_reason` 失败，外来 core 被接受 |
| [修后 holder](green-holder-01/run.json) | 退出 0：holder 重拉的 core 被接受且没另起，shell 进程号不变，`shell_reattached` 与状态都是 `screen: inexact` |
| [修后 foreign](green-foreign-01/run.json) | 退出 0：后台拒绝启动，`hc_start_failed` 的原因含锁路径，外来 core 上的终端数不变 |
| [变异：任意 core.lock 都算](mutant-any-lock-foreign-01/run.json)（[diff](mutant-any-lock.diff)） | 退出 1，同修前 foreign 两项失败 |
| [T-212 core-crash，旧断言](t212-core-crash-old-assert/run.json) | 退出 1：其余检查全过，只有环境探针断言失败，新 core 标记为 `initial-daemon`、私有 XDG，即 holder 重拉的 core 被接受。见上文对断言的修改 |
| [T-212 core-crash，改后](t212-core-crash-02/run.json) | 退出 0，记录由 holder 拉起，原终端 shell 进程号不变，用户 core 前后不变 |
| [T-212 electron mismatched-screen](t212-electron/run.json) | 退出 0 |

以上是第一轮候选。T-228 用例的 run.json 记 `user_core.unchanged`，T-212 core-crash 同名；electron 场景记的是 `user_core_directory_unchanged`、`user_core_processes_unchanged`，各次都是 true。

## 第二轮（GPT 审查 [REVIEW-01.md](REVIEW-01.md) 之后）

审查结论 FAIL，两条意见主控都核对属实：

- P1：`lsof -Fn` 输出的路径会被转义。主控用一次性 core 实测：`LC_ALL=C` 下 `测试 目录` 输出成 `\xe6\xb5\x8b…`。改为把锁路径交给 lsof 匹配；实测打开着时退出 0、输出 `p<pid>`，没打开时退出 1、没有输出。
- P2：事件写入失败会盖掉原启动错误。改为 `AggregateError` 同时带两个错误。

测试加 `--non-ascii`：数据目录带 `测试 目录`，后台与 hc 都在 `LC_ALL=C` 下跑。

| 运行 | 结果 |
| --- | --- |
| [第一轮候选 + `--non-ascii` holder](r2-red-holder-non-ascii/run.json) | 退出 1：第一次启动后台就失败，后台 stderr 为 `hc core 1812 does not hold this session's …测试 目录…/core.lock; refusing it`，后台自己拉起的 core 被误拒 |
| [holder `--non-ascii`](r2-green-holder-non-ascii/run.json)、[foreign `--non-ascii`](r2-green-foreign-non-ascii/run.json)、[holder](r2-green-holder/run.json)、[foreign](r2-green-foreign/run.json) | 都退出 0 |
| [变异：忽略 lsof 结果](r2-mutant-ignore-lsof-foreign/run.json)（[diff](r2-mutant-ignore-lsof.diff)） | 退出 1：`daemon_refused_foreign_core`、`refusal_event_with_reason` 失败 |
| [T-212 core-crash](r2-t212-core-crash/run.json)、[electron mismatched-screen](r2-t212-electron/run.json) | 都退出 0，用户 core 前后不变 |

P2 没有端到端用例：启动阶段让 SQLite 写入失败而后台又能走到 `hc.start()`，需要专门的注入点，本轮没有做，只做了代码修改。

## 第三轮（GPT 审查 [REVIEW-02.md](REVIEW-02.md) 之后）

审查确认第二轮的 P1、P2 已解决，另提一条 P1：先用 `server start` 报的 pid 核对、再连 socket，两步之间 core 若崩溃并被外来 core 顶替，连上的是没核对过的那个。时序成立，主控照改：

- `HcRuntime.start()` 先连 socket、`hello`，再在同一连接上调 `server.status` 取 pid 与版本，进程组与锁都对这个 pid 核对；任一项不过就关掉这条连接再抛错。连接建立后对方进程若再死，连接断开，窗格记 `hc_connection_lost`（T-212 的已有行为）。
- `server.status` 经同一连接返回 pid，主控先用一次性私有 core 实测过：返回的 `pid` 与 `server start` 报的一致。

| 运行 | 结果 |
| --- | --- |
| [holder](r3-green-holder/run.json)、[foreign](r3-green-foreign/run.json)、[holder `--non-ascii`](r3-green-holder-non-ascii/run.json)、[foreign `--non-ascii`](r3-green-foreign-non-ascii/run.json) | 都退出 0；foreign 的拒绝原因为 `hc core <pid> does not hold this session's …/core.lock; refusing it` |
| [变异：忽略 lsof 结果](r3-mutant-ignore-lsof-foreign/run.json)（[diff](r3-mutant-ignore-lsof.diff)） | 退出 1：`daemon_refused_foreign_core`、`refusal_event_with_reason` 失败 |
| [T-212 core-crash](r3-t212-core-crash/run.json)、[electron mismatched-screen](r3-t212-electron/run.json) | 都退出 0，用户 core 前后不变 |

顺序记录 [r3-runs.log](r3-runs.log)。“核对期间换 core”没有端到端用例：要在 `hello` 与 `lsof` 之间可控地杀 core 并抢先拉起外来 core，需要产品里加测试专用的暂停点，本轮没加；现在的核对对象就是连接的另一端，不再有两个 pid。

## 偏差与没做的

- 第二轮的非 ASCII 红态现场 `/private/tmp/t228-holder-测试 目录-xgsuq2_2` 也被主控删掉了，删之前读过后台 stderr 的拒绝原文（见上表）；run.json 与日志都在。
- 旧断言那次失败后，主控删掉了它的现场 `/private/tmp/t212-crash-itqemlik`，原本应先保留。删之前读过其中的 `new-core-environment.json`：`{"starter": "initial-daemon", "xdg_state": ".../state/hc/state"}`；run.json 与日志都在。
- 运行中的后台在 core 断开后不自动重连（T-220 建议第 2 条的后半），不在本票验收里，没做；断开时仍记 `hc_connection_lost`、侧栏显示未知（T-212）。
- 类型检查没跑成：`npx tsc` 取到的不是 TypeScript，结果作废。
