STATUS: FAIL
TARGET: 116985ec9f14b80cb26c1fd4a4451a409293e768（基线 788d75f4a75a861a7beb23f3f0ac97a6ecc70938）
EVIDENCE:
- 本轮只审 controller #129 的恢复准入合同，未读取候选新增测试或其结果作为 oracle。独立脚本调用真实 `Panes.recover()`、真实 SQLite store、真实 `claudeLaunch()` 记录生成器及新原生 JSONL 文件；版本命令、PTY、旧 PID 缺失与 process snapshot 均由脚本提供边界替身。29 场全部完成，候选 28 场 PASS、1 场 FAIL。原始输入与边界逐条输出保存在 `/private/tmp/t093-r20-independent-K6vIJW/candidate-dccc9613/{inputs.json,boundaries.jsonl,result.json}`。
- 局部 PASS：完整正常登录记录、实际生成后删 authentication 的正常登录记录，以及仅余角色版本、audit、preflight、hook、process log、HOME、config、trace NODE_OPTIONS 各单一标记的 8 场，均在任何 supplied 版本／PTY／进程边界前拒绝，错误为 `normal_login_restore_requires_protected_start`，状态为未恢复并保留中文提示。10 场未知／混合配置均返回 `restore_record_unrecognized`，零版本／PTY／进程调用。
- 局部 PASS：显式 fake ideation 与缺 authentication、缺 executable_path 的 legacy fake executor 均恢复；保留完整 argv 及其引号、中文 nonce，只替换 session selector。原版本检查、原生 session 文件检查、运行时 canonical executable identity 均生效；已有 launch／事件历史原文未改，固定 leader 更换返回 `claude_leader_replaced_or_exited`。缺 argv、版本不符、session 缺失、保存 argv 被篡改、规范身份改变分别拒绝；worker 不恢复，其 attempt 原文不变。没有 prompt write。
- 复现命令：`node /private/tmp/t093-r20-independent-K6vIJW/probe.mjs candidate`，退出 1；`node /private/tmp/t093-r20-independent-K6vIJW/probe.mjs base`，退出 1。命令与原始结果位置见同目录 `commands.json`；脚本和 base 源码快照分别为 `probe.mjs`、`panes-base.ts`。每次重跑生成新 nonce、新 SQLite 和新原生文件，不复用旧夹具。
- 收尾冻结检查：HEAD 仍是本 TARGET，`git diff --stat` 为空；原有未跟踪文件保留。project-map status 退出 0，Problems 0、Stale living docs 0。原始检查输出见同目录 `freeze-final.json`。
FINDINGS:
- [P1] `workbench/src/panes.ts:30`、`:42` — 正常登录标记枚举与 fake 准入都忽略原始 `shell_argv`。`claudeLaunch.ts:91` 明确令正常登录的原始命令以 `exec ` 开头，而已知 fake P1 令完整 argv 后接 `; exec /bin/zsh -f -i`。新输入 `partial-normal-shell-exec-only` 保留 fake 正面字段并删 authentication，仅把 coherent shell_argv 设成正常登录的 `exec <同一完整 argv>` 形态；结果仍为 `restored`，产生 1 次 supplied `--version`、1 次 supplied PTY、1 次 supplied process snapshot，并记录 `pane_restored`。这违反“正常登录的部分标记仍须拒绝／只正面识别已知 fake profile”的合同。最小修正是在版本与 PTY 边界之前识别该正常登录执行形态，并要求 fake 启动形态与已知合同一致；保留显式 fake 与 legacy fake 正例，不靠删除 legacy 支持来通过。
COUNTEREXAMPLE:
- 基线经同一独立脚本完成 29 场、仅 9 场 PASS。实际 `claudeLaunch()` 正常登录记录删除 authentication 后在基线被恢复，触发“应未恢复”和“零版本／PTY／进程调用”的业务断言；不是因崩溃或依赖缺失判红。原始证据在 `/private/tmp/t093-r20-independent-K6vIJW/base-66824813/{inputs.json,boundaries.jsonl,result.json}`。候选已关闭此旧反例，但上面的 shell-only 反例仍失败。
LIMITATIONS:
- 这是 L0／L1 结论。没有执行真实 CLI、daemon、服务、PTY、PID／ps／libproc 查询、sandbox／compiler、认证／Keychain、网络／socket／模型、提权或旧夹具操作；auth 文件打开／读取与 ClaudeLogin.prepare 计数均为 0。替身不证明真实外部边界。
- 新候选 T-096 native7 与门禁尚待主控在授权入口重跑；本轮未完成整票验收，当前受影响范围 NO_GO。review03 的网络两层、其他运行时身份／libproc 等范围未复审，也没有用它们的旧结论替本候选恢复入口背书。
RULE:
- 本次仍属于“缺字段或残留正常登录标记导致 profile 降级”的重复失败类。应在恢复合同检查中，从实际 launcher 生成的 fake／normal 成对记录独立构造逐项残留标记与未知形态，要求全部在版本／PTY／auth 边界之前拒绝；同时保持两类 fake 正例和 worker attempt 不变。此处可用可执行反例检测，不需要再增加一条仅靠提示词记忆的规则。
