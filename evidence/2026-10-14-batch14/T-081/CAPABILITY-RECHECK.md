# T-081 第 7 项能力复测（无模型）

状态：A 项生产布局复测 **PASS**（无模型）。B 项规则语义仍为 **PASS**。`git commit` 在沙箱外的写入范围见同目录 [COMMIT-SCOPE.md](COMMIT-SCOPE.md)。C 项代码核对仍为 **PASS（事实确认）**。本轮没有启动模型、daemon、Herdr pane 或真实 worker 回合，也没有修改 `workbench/src/gates/core.ts`。CLI 帮助、规则判定、产品启动参数和 CAS/集成代码已核对。主控第一次沙箱外运行的 A 项被驱动错误地记为 `PASS`，但两组命令均是 Codex CLI 缺少 `--permission-profile` 的 exit 2，Git 根本没有执行；该原件保留为 `CAPABILITY-RECHECK-02/run.json`，明确为 **INCOMPLETE / CLI 用法错误**，不作为 A 项结论。

证据目录：[CAPABILITY-RECHECK-01](CAPABILITY-RECHECK-01/)，驱动为 [`run_t081_capability_recheck.py`](../../../../workbench/tests/run_t081_capability_recheck.py)。本目录的 `run.json` 是无 `--run-sandbox` 的静态预检，状态 `READY`；它没有冒充 A 项生产布局结果。

## A. 生产布局复测准备

当前 CLI 为 `codex-cli 0.162.1`。`codex --help` 列出 `sandbox`，但没有 `sandbox macos`；`codex sandbox --help` 的用法是：

```text
Usage: codex sandbox [OPTIONS] [COMMAND]... [COMMAND]
Run commands within a Codex-provided sandbox
```

因此本版本的等价入口是 `codex sandbox --permission-profile :workspace --cd <worker> ... -- <command>`。`codex sandbox --help` 明确要求 `--permission-profile <NAME>` 和 `--cd <DIR>`；`codex sandbox macos` 不是子命令。0.162.1 的官方配置参考把内建 profile 列为 `:read-only`、`:workspace`、`:danger-full-access`，并说明 `:workspace` 是 permission-profile 形式的 workspace-write 等价物（[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)，第 1033、1837 行）。无模型 profile 探针的原始回执保存在 [permission-profile-probe-01.json](permission-profile-probe-01.json)。在当前受管沙箱中试跑 `:workspace` 会进入嵌套 Seatbelt 并得到 `sandbox_apply: Operation not permitted`；这是环境限制，不是外置盘或 `/tmp` 的业务结果。

产品窗格实际传给 Codex 的 worker 参数见 [`workbench/src/panes.ts:155-161`](../../../../workbench/src/panes.ts:155)：`--no-daemon --no-alt-screen -C <attempt.workspace> -a never --sandbox workspace-write -m <model>`，以及：

```text
-c model_reasoning_effort="xhigh"
-c service_tier="default"
-c check_for_update_on_startup=false
-c tui.notifications=false
-c sandbox_workspace_write.network_access=false
-c features.network_proxy=false
```

`scripts/launch-worker:54-60` 是 Herdr 旧入口，另有 `--ask-for-approval on-request`；本复测按用户指定的生产窗格 `panes.ts` 策略，使用 `codex sandbox` 子命令表达同一 sandbox boundary。`codex sandbox` 本身不接受顶层 `--sandbox workspace-write`，它就是直接进入 Codex sandbox 的命令入口；所有上述 `-c` 覆盖仍逐项传入。

`panes.ts` 还动态加入 `hooks.UserPromptSubmit`、`hooks.Stop`、`hooks.PermissionRequest` 三个 `-c` 值。直接 sandbox 子命令只执行 Git argv，不启动 Codex 会话，也不会产生这些生命周期事件；驱动不注入 signal hook，避免把 hook 投递问题混入文件系统边界复测，并在 `run.json` 的产品配置清单中明确这一边界。

驱动现在显式要求 `--codex-home`，创建只含 `[permissions]` 空表的隔离 `CODEX_HOME`，并把该环境变量传给每一个 help、policy 和 sandbox 子进程；它不读取用户 `~/.codex`，也不复制 auth。任何 stderr 含 `required arguments were not provided`、`Usage: codex sandbox`、`sandbox_apply`、`sandbox-exec` 或 permission-profile 错误的探针都分类为 `INCOMPLETE`，不得升级成 `PASS`。

驱动在每个位置创建三个 Git 对象：共享仓库 `repo`、本地裸仓库 `local.git`、脱离 HEAD 的 `worker` worktree。它先建立 G/T 两个提交，并把共享 `refs/heads/main` 和裸仓库置于 G；随后在 worker cwd 中分别执行：

```text
git update-ref refs/heads/main T G
git push <fixture>/local.git T:refs/heads/t081-probe
```

每条命令都以独立 argv 调用，无 shell 拼接，保存退出码、stdout、stderr；命令后在 sandbox 外独立读回共享仓库的 main/reflog 与裸仓库 refs。默认位置正是用户要求的：

```text
/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/sandbox-probe-01/
/tmp/t081-capability-recheck-01/
```

主控在沙箱外运行（使用新输出目录，避免覆盖本次静态预检）：

```sh
CODEX_HOME=/private/tmp/t081-recheck-codex-home-02 \
python3 -B workbench/tests/run_t081_capability_recheck.py \
  --run-sandbox \
  --codex-home /private/tmp/t081-recheck-codex-home-02 \
  --external-root /Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/sandbox-probe-02 \
  --tmp-root /tmp/t081-capability-recheck-02 \
  --output evidence/2026-10-14-batch14/T-081/CAPABILITY-RECHECK-03
```

`CAPABILITY-RECHECK-02/`、`sandbox-probe-01/` 和 `/tmp/t081-capability-recheck-01/` 是失败原件，不能覆盖或复用；下一轮夹具使用 `-02`。若任一目标目录或 home 已存在，驱动会停止并保留现场；它不删除夹具，不读写 `auth.json`，不启动模型。

### A 项实测（主控沙箱外运行）

原件是 [CAPABILITY-RECHECK-03/run.json](CAPABILITY-RECHECK-03/run.json)。顶层 `status` 为 `PASS`，`model_turns_started` 为 0，`permission_profile` 为 `:workspace`，`codex_home` 为 `/private/tmp/t081-recheck-codex-home-02`。两组夹具的 `G` 都是 `b28512458604bb404fb57ae80736cb693f037f05`，`T` 都是 `ac5ec0949a846875403f7f40b2a0e153391fddc6`。命令在 worker worktree 里经 `codex sandbox --permission-profile :workspace` 执行，读回在沙箱外用独立 `git -C` 完成。决策记录写明该隔离 home 运行后已删除；本会话核对 `/private/tmp/t081-recheck-codex-home-02` 与 `/tmp/t081-recheck-codex-home-02` 当前都不存在。夹具目录仍在。

| 位置 | 命令 | 退出码 | 沙箱外读回 |
| --- | --- | --- | --- |
| 外置盘 `sandbox-probe-02` | `git update-ref refs/heads/main ac5ec0949a846875403f7f40b2a0e153391fddc6 b28512458604bb404fb57ae80736cb693f037f05` | 128 | `refs/heads/main` 仍为 G。stderr：`cannot lock ref 'refs/heads/main': … main.lock：Operation not permitted` |
| 外置盘 `sandbox-probe-02` | `git push …/local.git ac5ec0949a846875403f7f40b2a0e153391fddc6:refs/heads/t081-probe` | 1 | 裸仓库 `show-ref` 只有 `refs/heads/main` = G，没有 `t081-probe`。stderr：`unable to create temporary object directory`，远端拒绝 unpacker error |
| `/tmp/t081-capability-recheck-02` | 同一条 `git update-ref` | 0 | `refs/heads/main` 变为 T |
| `/tmp/t081-capability-recheck-02` | 同一条 `git push` | 0 | 裸仓库新增 `refs/heads/t081-probe` = T。stderr：`[new branch] … -> t081-probe` |

因此，先前 run-04 里 worker 能移动共享分支并 push，对应的是夹具放在 `/tmp`（workspace-write 默认可写）。同一沙箱策略在外置盘生产布局上拒绝 `update-ref` 和 `push`，工作分支与裸仓库探针引用都不动。

## B. `prefix_rule` 与共享 `.git`

官方 Codex sandbox 文档明确区分两个控制面：sandbox 是命令的技术边界，approval policy 决定何时请求批准；并明确“sandbox applies to spawned commands”，也就是 `git` 等子进程继承 sandbox 边界（[Sandbox 文档](https://learn.chatgpt.com/docs/sandboxing)，现行页面第 927-935 行）。同页列出 `workspace-write`、`on-request` 和 `danger-full-access` 的关系（第 1032-1049 行）。

官方规则文档的标题与原文直接回答了执行位置：`prefix_rule` 用来控制 Codex “can run outside the sandbox”；`decision = "allow"` 的定义是 **“Run the command outside the sandbox without prompting.”**（[Rules 文档](https://learn.chatgpt.com/docs/agent-configuration/rules)，第 917-977 行）。所以 `git commit` 被 `prefix_rule(pattern=["git", "commit"], decision="allow")` 命中时，规则的作用是允许该命令越过 sandbox 边界执行，不是把它限制在 worker worktree 内。

本地无模型实证由驱动的 `codex execpolicy check` 完成，原始 JSON 在 `CAPABILITY-RECHECK-01/run.json`：

| argv | 判定 |
| --- | --- |
| `git commit -m probe` | `allow`，命中 `git commit` |
| `git -C /other commit -m probe` | 无匹配；规则是参数前缀，不会跨过 `-C` |
| `git config --local ...` | 无匹配 |
| `git update-ref ...` | 无匹配 |
| `git push ...` | 无匹配 |

因此当前两条 allow 规则不会授权 `update-ref`、`push` 或 `config`。它们也没有对一个已获 allow 的 `git commit` 声明 refs、objects、config、hooks 的路径白名单。能确定的范围如下：

| 对象 | 本次证据能确定的事实 |
| --- | --- |
| refs、objects、index、logs | `git commit` 的正常 Git 写入由该命令自身决定；规则没有额外的 Codex 路径白名单。官方文档只保证该命令可在 sandbox 外运行。 |
| config | `git config` 不匹配 `git commit` 规则；本次没有证据说 `git commit` 本身会写 config。 |
| hooks | `git commit` 会按 Git 语义调用 hook，但本次没有用 hook 改写 `.git/hooks` 的实证；规则文档没有把 hook 目录单独限制为 worker worktree。 |

“allow 后整个 `.git` 任意文件都可写”不是本次文档或无模型探针直接证明的结论；若要测 hook/config 的子进程副作用，需要在主控批准的、沙箱外的独立夹具中新增明确命令和读回。当前可以确定的是：`git commit` allow 不是 sandbox 内执行，且产品 worker 的两条 allow 规则本身不匹配 `update-ref`/`push`。这段只描述本复测当时的范围；写入范围的后续实测见 [COMMIT-SCOPE.md](COMMIT-SCOPE.md)。

## C. CAS 发现工作分支移动后的实际路径

代码结论是：**首次发现工作分支已移动时，门禁不会立即拒绝；它会清除集成意图、重新验收并重新发起审查。若重新验收/审查通过，被移动分支已有的提交可能作为新 G 的祖先进入最终工作分支；该提交不出现在审查 prompt 的候选 diff 中。**

关键路径：

1. [`core.ts:1713-1742`](../../../../workbench/src/gates/core.ts:1713) 的 `integration()` 读取当前 `integration_ref`。`revalidateForIntegration()` 先确认外来头存在，绑定原 verification，递增 `misses`，保存 `integration_compare_failed`，清除 `integration_intent`，把任务退回 `submitted`，然后调用 `verifyCandidate()`。前三次 miss 会重验；第四次进入 `paused` 并拒收 `integration_revalidation_limit`。
2. [`core.ts:1510-1619`](../../../../workbench/src/gates/core.ts:1510) 的重验把当前分支头作为新 `G`，仍把 `task.candidate_commit` 作为 `C`；若 `G` 与 `C` 不是祖先关系，就在验证 worktree 中以 `G` 和 `C` 生成新的 `M`。完成条件、路径检查、oracle 检查、质量链和尾注检查均在这次验证中重新执行。
3. [`core.ts:3426-3483`](../../../../workbench/src/gates/core.ts:3426) 在 `actual !== v.G` 时调用上述重验；重验后循环继续。随后 [`core.ts:3484-3538`](../../../../workbench/src/gates/core.ts:3484) 以新的 `G` 建立 CAS 集成意图，事务更新工作分支到 `M`。
4. 独立审查看到的 diff 在 [`core.ts:2129-2134`](../../../../workbench/src/gates/core.ts:2129) 是 `attempt.base_commit..v.C`。它没有把新的 `v.G..v.M` 或外部移动提交放进审查候选 diff。与此同时，路径与 oracle 检查的 `G→M` 只把新 G 之后的变化计入；新 G 已经是外部移动提交的祖先头。

所以，若 worker 把工作分支从旧 G 移到含有额外提交 X 的新头 X，并且 X 可被门禁接受、重验与新审查通过，最终 M 会以 X 为父提交或祖先，X 会随工作分支前进而保留；审查 prompt 只审查 `attempt.base_commit..C`，X 本身不在该 diff 中。这是“重验后集成”路径的实际语义，不把它写成拒绝。

已有 CAS 补证支持“移动被发现后不能盲写旧值”的部分，但不改变上面的重验语义：[cas-01/run.json](cas-01/run.json) 记录唯一变异删去 `update-ref` 的旧值参数；变异红态的三个业务断言失败，候选绿态保留外部 writer 内容并重新执行 oracle。该补证 `real_codex_turns=0`，没有模型因素。

## 结论边界

- A 项为 **PASS**：第一次外部运行是 CLI 用法错误，原件保留在 `CAPABILITY-RECHECK-02/`，不计入结论。修正后的主控沙箱外运行见 `CAPABILITY-RECHECK-03/run.json`：外置盘 `update-ref` exit 128、`push` exit 1，引用不动；`/tmp` 对照两条都是 exit 0，main 变为 T，裸仓库出现 `t081-probe`。
- B 项静态与 `execpolicy check` 为 **PASS（规则语义）**。`git commit` 的 host 写入范围与 hook 子进程副作用见 [COMMIT-SCOPE.md](COMMIT-SCOPE.md)。
- C 项代码核对为 **PASS（事实确认）**：CAS 发现移动后走重验/再审查；若通过，外部移动提交作为新 G 的祖先可进入工作分支，且不出现在审查候选 diff 中。
- 6a 的新正向人工介入套件、以及 T-084 合入后的 6e 拒收案不在本次复测中实施；在 T-084 前不改 `workbench/src/gates/core.ts`。

T-081 RECHECK READY
