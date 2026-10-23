# T-147-1 / a1 交付记录

状态：**INCOMPLETE**。授权的一行修改与沙箱外运行脚本已完成；真实后台的候选绿态、旧行为反例和独立审查尚未运行，不宣称验收通过。

范围：worker `b23-t147`，分支 `exec/t147`。实际起点为 `2e36efb7c6edccb59f543aff325a1cf141d463ac`；派发消息提到 `fda7d194dc3ee40efd382ce8f10f6f9d68e77fdf`，已用 `git diff 2e36efb7c fda7d194d -- workbench/src workbench/terminal workbench/tests/test_t121_role_request_e2e.py` 核对，三处范围无差异。未切换或重置分支。task/attempt/session 等提交身份由现有 Git 钩子记录，未手写尾注。

## 修改前后

期望来自任务卡与 ticket 所引用户裁定“保留并标已结束 (Recommended)”。`workbench/tests/test_t121_role_request_e2e.py:515` 原本要求关闭主控后找不到该条目；现在要求匹配该终端的状态列表等于 `['ended']`，同时证明条目存在且状态已结束。保留原检查名 `sidebar_drops_closed_controller`，并保留前面的 `closed_terminal_identity_refused`。产品代码、其他断言、超时与其他验收文件均未修改。

## 证据

- 已有红态（执行主控来源，非本 worker 新运行）：[合并回归记录](../merge-1/run-20261023T151510Z/NOTE.md) 与 [t121-main.json](../merge-1/run-20261023T151510Z/t121-main.json)。`fd4d9ac13` 的原测试在 `sidebar_drops_closed_controller` 失败，身份拒绝检查已通过；[旧行为原测试](../merge-1/run-20261023T151510Z/t121-before-t146-3.json) 在 `045e8cfb1` 为 PASS。这些记录只证明原断言与裁定 B 的冲突，不证明本候选通过。
- 本地静态检查：PASS，见 [local-checks.json](local-checks.json)。AST 解析成功，字节对照确认仅授权行发生变化，UTF-8 无 BOM、LF 保持；直接求值断言表达式时，匹配条目为 ended 通过，缺失、running、仅其他终端 ended 均被拒绝，其他终端存在不影响目标 ended。合成输入不构成真实后台变异证据。
- `zsh -n evidence/2026-10-23-batch23/T-147/RUN-OUTSIDE-01.sh`：PASS。
- `git diff --check`：PASS。
- 真实运行：未运行，按派发要求交主控在沙箱外执行。受影响的既有 e2e 是完整 T-121；脚本保留其全场景回归，不另改测试。

## 沙箱外复跑与剩余检查

运行 `zsh evidence/2026-10-23-batch23/T-147/RUN-OUTSIDE-01.sh`。脚本在本 worktree 下创建唯一的 `outside-<UTC>-<随机串>/`，记录提交、工作区、命令、退出码和两个 summary/log：

1. 候选完整 T-121：应退出 0、status PASS，身份拒绝与侧栏检查均通过。
2. 同一新测试加 `--revision 045e8cfb1`：应退出 1，且只在目标 `sidebar_drops_closed_controller` 失败，之前的身份拒绝检查通过；环境或其他断言失败不算反例通过。

`run.json` 的 PASS 仅表示上述两项运行结果符合预期，独立审查仍由执行主控在交付后安排。真实“已关闭仍标 running”变异未运行；本地合成输入已核对表达式拒绝该值。未扩展受保护测试的 mutant 选项。

项目地图 status 在开始时为 Problems 0、Stale living docs 0；交付前再次运行并保存至 [project-map-status.txt](project-map-status.txt)。未修改地图、术语表或 ticket。
