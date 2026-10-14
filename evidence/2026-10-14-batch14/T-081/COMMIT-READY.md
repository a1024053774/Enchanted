# T-081 提交恢复（主控 #179）

状态：**INCOMPLETE / Git 提交待主控运行**。cas-01 PASS、home-cleanup-01 PASS，3/3 真实回合已用尽；6a/6e 仍待裁定。index 没有 reset，原始证据没有修改。本轮仅修提交脚本、增加针对预检的反例并更新说明，没有 add 或 commit。

## 失败与修正

原失败为 `/private/tmp/t081-closeout-commit-01/commands.jsonl` id 7，`git diff --cached --check` exit 2。stdout/stderr 与原脚本副本保存到 [commit-fix-01](commit-fix-01/red.json)。错误来自证据快照 `.py` 的 EOF 空行、原始 PTY 行尾空白等，不能改写这些原件来过检查。

[脚本](../../../workbench/tests/commit_t081_closeout.py) 现仅对 staged 的 `workbench/`、`acceptance/`、`scripts/`、`.project-map/` 代码路径，以及 T-081 顶层 `.md` 说明、full-*/closeout-* 的 RESULTS.md 运行 diff --check。角色正文、首轮输入模板等 `.md` 是原始输入，也与 PTY、源码快照、JSON/SQLite/归档一起排除空白检查。**排除只影响空白检查，原始证据仍保持暂存并进入提交。**

每次收据 `scope.json` 记录 checked_paths、excluded_raw_count、excluded_raw_manifest。排除清单按每 1,000 路径一个 JSON 分卷，保留完整路径，不受 5 MB 单文件限制影响。[只读预检 scope.json](commit-check-01/scope.json) 已列当前 40 个检查路径、27,479 个排除路径及 28 份清单；新说明与测试在主控增量暂存后也会纳入最终范围。

恢复时核对现有 27,519 个 staged 文件的归属及冲突状态，只 add 新增或已审阅的本票代码/说明改动；原件有未暂存改动就停止。现有原始证据在 index 中的 mode/object 必须保持一致；使用 Git 已有对象身份代替重读约 355 MB 字节，不计算新的内容摘要。不会对原件重新 add，不 reset，不覆盖旧日志，不重复生成 closeout-final-01。

## s14-t081 的准确环境

身份来源：主仓 launches.jsonl 中 `launch-517c75701a0443ec9633fb6388e8ad2f`，agent=s14-t081、pane=wF:p3T；原生会话采用主控 #179 / Herdr 给定的 `01a13bc2-d779-7370-88a0-6b71bb434456`。这不是三个能力探针的原生会话 ID。

主控在运行脚本的 shell 设置以下 **11 个**变量；脚本不会自动伪造或补齐。任一缺失会先列出变量名并停止，任一归属或 hook 环境不符也停止，均在 add/commit 之前：

```sh
export A2A_PROJECT='a2a'
export A2A_TASK='T-081'
export A2A_ATTEMPT='a1'
export A2A_SESSION='6962bde6-a95a-4810-b4cf-58f34515d820'
export A2A_ROLE='worker'
export A2A_LAUNCH='launch-517c75701a0443ec9633fb6388e8ad2f'
export A2A_LAUNCHES='/Users/luckye/Documents/Code/a2a/records/launches.jsonl'
export CODEX_THREAD_ID='01a13bc2-d779-7370-88a0-6b71bb434456'
export GIT_CONFIG_COUNT='1'
export GIT_CONFIG_KEY_0='core.hooksPath'
export GIT_CONFIG_VALUE_0='/Users/luckye/Documents/Code/a2a/scripts/git-hooks'
```

脚本只读核对启动记录的 agent/task/attempt/session/role、cwd、model/effort 及以上环境。记录中 native_session 目前为 unknown，允许项目实际 prepare-commit-msg hook 在真实提交时按正常流程追加绑定；本轮没有调用这个 hook 或修改主仓启动记录。若记录已绑定其他原生会话，脚本拒绝，不替换记录。不手写任何 A2A 尾注，不禁用 hook。

## 主控恢复命令

在本 worktree 根目录运行：

```sh
python3 -B workbench/tests/commit_t081_closeout.py
```

新日志目录固定为 `/private/tmp/t081-closeout-commit-02/`，存在即停止，防止覆盖。本次修复的只读预检使用另一个新目录，不占用这个真实提交目录。脚本复核 CAS/清理收据与已生成汇总、地图状态、单文件大小和范围，再增量 add → 限定范围 diff --check → diff stat → 正常 Git commit。失败保留 index 与收据，不 reset；没有 submit、集成或 push。

可先额外做只读检查（每次使用新日志目录）：

```sh
python3 -B workbench/tests/commit_t081_closeout.py --check-only --log-dir /private/tmp/t081-commit-precheck-next
```

只读模式检查**当前 index**中的空白和本次增量计划，不 add；真实提交模式在增量 add 后重新检查最终 staged 代码和说明。已通过的 [commit-check-01](commit-check-01/run.json) 未改变原 index；[commit-contract-check-01](commit-contract-check-01/run.json) 覆盖代码/说明必须进入检查、原件必须排除、缺少所有身份变量、错 native、错 owner session，以及真实 Git 能检出代码行尾空白的反例。没有以空检查集或“忽略全部错误”代替通过。

T-081 COMMIT READY
