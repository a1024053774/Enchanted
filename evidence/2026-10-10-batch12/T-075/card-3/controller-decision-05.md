# T-075-3 执行主控决定 05：B 通道的 git 写入被沙箱拒绝（2026-10-11）

## 我核对过的 outside-b-05 结果
- relay-cli、relay-core 两项 PASS；gates 15/15 PASS。
- B 通道的机制已经跑通：请求文件身份不符（fence）和内容不完整（缺 commit）都被拒收并留下事件；issue 和 status 能正常转交；同一请求重复转交时不重复处理；门禁回执写回窗格后，回执回合正常结束。用到 2 个真实回合，累计 5/10。
- 真实交付没有完成。被测 worker 把 `git add` 和别的命令用 `&&` 串在一起执行（`git status --short && git diff --check && python3 … && git add …`）。在沙箱里写 `.git/worktrees/<attempt>/index.lock` 时被拒（Operation not permitted）。所以没有生成提交，它改为上报阻塞问题，没有伪造提交。这样处理是对的。
- 原因待确认：
  - (a) 命令串在一起后，前缀规则 `git add` / `git commit` 匹配不上；
  - (b) 在 `-a never` 模式下，单独执行、且命中 allow 规则的 git 命令，是否会被放到沙箱外执行。

## 你要做的
1. **先不用模型回合，核实 (a) 和 (b)。**
   - 用 `codex execpolicy check`，对照隔离 home 里的规则文件，分别检查单独执行的 `git add src/x` 和串在一起的那条命令，保存输出。
   - 从 Codex 文档或 `--help` 里查清楚：在 `approval_policy=never` 下，规则判为 allow 的命令是放到沙箱外执行，还是仍在沙箱内执行。
   - 两项结论都按 observed / inferred 标注。
2. **修产品。** 派发给 worker 的提示里（角色卡或任务卡模板，按“提示词管判断”的原则），写明 `git add <路径>` 和 `git commit …` 必须各自单独执行，不能和其他命令串在一起。这一条要进生产路径，不能只放在测试里。
3. **如果 (b) 证明 `-a never` 下 allow 规则不会被放到沙箱外执行：** 停下写 needs-decision，不要换其他办法绕过沙箱。
4. **如果 (a) 是原因、(b) 也没有问题：** 用新标签重跑一次 B 的真实交付，只允许 1 个交付回合加 1 个回执回合，累计上限 7/10。不再追加。这一轮是修复缺陷后的复验，不另外重试。
5. **其他照旧。** 探针或测试本身的错误，你可以直接修。完成后照旧回复 `T-075 OUTSIDE-SANDBOX READY`。
