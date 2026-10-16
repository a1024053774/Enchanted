# T-081 capability-run-02 交接（主控 #173）

状态：INCOMPLETE / 等重新批准。run-01 原件、原 repo/state、原裸仓库和 home 保留，未重试、未清理。full-04 已读回：controlled_status PASS，11 案与变异证据、3 个正例、误拒绝 0、23 个已记录回归阶段全过；该结论不替第 7 项背书。

## run-01 只读诊断

实际失败是 `commands.jsonl` 的 **id 12 dispatch**：exit=1，stdout 是包含 `gate_failure` 的 JSON，details 为 `Actual first turn differs from the approved prompt; dispatch refused.`。**id 18 是本地裸仓库 show-ref**：空输出、exit=1、约 0.01 秒，是空仓库读回。不是第二次 dispatch。数据库只有一次 dispatch 请求、一次 pane_started，没有 turn_submit_intent。

`launch-before-spawn.json` 的 ok=true，真实 PTY spawn 审计已通过；`first-turn-before-queue.json` 的 ok=false，在第一条消息入队前拒绝。实际与预期只有一处差异：

```text
预期：/Library/Developer/CommandLineTools/usr/bin/python3
实际：/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9
```

根因是 T-081 审批材料生成过程忽略了 `validateTaskCard` 的返回值。该函数先 structuredClone，再将命令首项 realpath 化；它不会修改原输入。产品保存的是返回的规范化副本，旧模板却用了原卡。没有产品缺陷需要修改。

`capability-diagnosis-02/run.json` 已在不启动 daemon、PTY 或模型的情况下复现：旧模板不匹配原实际文本；使用规范化返回值重建后，与 run-01 保存的实际文本完全相同。`event-readback.json` 保存命令 ID、事件次数及只读核对；原生实际回合观察数为 0。只有 spawn-helper 的早期进程快照不足以判定 zsh 启动失败；它是在文本拒绝后很快被正常停止。stderr 的 MODULE_TYPELESS_PACKAGE_JSON 警告不是本次拒绝原因。

## 修正

- 新增 [材料生成脚本](../../../workbench/tests/prepare_t081_capability_run02.ts)，使用 `validateTaskCard` 返回的规范化卡生成注册卡与首轮模板。继续严格逐字核对，不按别名替换或忽略差异放行。
- [运行脚本](../../../workbench/tests/run_t081_capability_turn.py) 在派发前核对产品 card_validate 返回值与待批卡完全一致。产品入口失败时报告实际命令 ID、exit 和 JSON，避免把裸仓库空输出与 dispatch 混淆。
- 新任务 `T-081-CAP-02`，新实例 `/private/tmp/t081-capability-01/run-02/`。批准后才从原本地种子仓库克隆新 repo，显式取回 T，移除本地 origin，创建新的本地裸仓库和 state。只读使用原种子，不接管或清理 run-01。
- 复用 `/private/tmp/t081-capability-01/codex-home`，保留已有 auth/config/rules/tmp，不重新 prepare、不改信任目录、不复制凭据。新实例仍在原信任根内。首次失败没有原生会话记录；若出现未知目录或会话，脚本停止。
- 单独写入 `run-02/turn-1-reservation.json` 与 `run-02/owned-pids.json`，不覆盖第一次记录。home 不删除，后续清理仍另批并需核对两次运行的退出记录。

## 待重新批准的材料

提议引用：`T-081 controller-decision-02 capability-turn-1`。该引用目前只是脚本要求的待批标识，本次未据此启动。

| 材料 | 路径 |
| --- | --- |
| 第一回合完整文本模板 | [FIRST-TURN.template.md](capability-review-02/FIRST-TURN.template.md) |
| 角色正文及两条实际命令 | [ROLE-BODY.md](capability-review-02/ROLE-BODY.md) |
| 完整 argv / zsh argv，1 回合上限 | [launch-policy.first-turn.pending.json](capability-review-02/launch-policy.first-turn.pending.json) |
| 启动配置（批准字段仍为 null） | [launch-config.pending.json](capability-review-02/launch-config.pending.json) |
| 规范化任务卡 | [task-card.pending.json](capability-review-02/task-card.pending.json) |
| CLI hooks 全文及 Git hook 清单 | [hook-contents.json](capability-review-02/hook-contents.json) |
| home 来源与动态字段说明 | [review-metadata.json](capability-review-02/review-metadata.json) |

实际观察命令的新路径均限本地：

```sh
git -C /private/tmp/t081-capability-01/run-02/repo update-ref refs/heads/main 16a341ae5f0b65b26c0829b830ca28c938ea9130 4de60dac7fd4b9baebd5c5cb177267673f398d77
git -C /private/tmp/t081-capability-01/run-02/repo push /private/tmp/t081-capability-01/run-02/local.git 16a341ae5f0b65b26c0829b830ca28c938ea9130:refs/heads/t081-probe
```

主控重新批准后才运行；本次不执行：

```sh
python3 -B workbench/tests/run_t081_capability_turn.py --approval-ref 'T-081 controller-decision-02 capability-turn-1' --output evidence/2026-10-14-batch14/T-081/capability-run-02 --turn-timeout 600
```

仍为原产品 CLI → 真实 daemon → 一次 dispatch/release → 匹配 Stop/idle/task_complete → 原生工具回执与 refs → 正常 daemon_stop/PID 退出。不提交、不 submit，不改变 argv/hook 的模型、强度、default tier 或沙箱设置。任何失败保留，不自动追加回合。

`capability-run02-script-check-01/` 的静态与 PTY spy 红绿已通过；它没有启动真实 PTY/模型，也没有创建 run-02 或改变 home。产品代码、工作台门禁和已通过的坏 worker 验收断言未改。

T-081 CAPABILITY-RUN-02 READY
