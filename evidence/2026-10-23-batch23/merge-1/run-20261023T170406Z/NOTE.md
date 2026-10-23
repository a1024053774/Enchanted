# 合并后回归 05（main edd8a7cad，含 T-147、T-141、T-142）

命令：`zsh evidence/2026-10-23-batch23/merge-1/RUN-MERGE-REGRESSION-05.sh edd8a7cad`（分离 worktree `a2a-merge-check`）。

- 31 项中 28 项 exit=0，含 T-121（T-147 后恢复绿）、T-127、T-141 绿态与 launch/reviewer 契约、T-142 绿态、T-133/T-107、T-144、T-146 绿态、构建。
- `t141-startup-contract` exit=1：ENOENT，读 `evidence/2026-10-23-batch23/T-141/probe-codex-start-01/untrusted.json`，检查 worktree 是稀疏检出、没展开本批证据目录。执行主控补 `sparse-checkout add` 后单独重跑 PASS（`t141-startup-contract-rerun-alone.json`）。回归脚本以后先展开本批目录。
- `t146-reviewer-hooks` exit=1（单独重跑同样）：`review_launch_boundary`。根因：该测试手写的 Claude 审查员 argv 仍是 T-141 前的形状（`--strict-mcp-config`、沙箱无 network、PreToolUse 无 MCP 权限钩子）；T-141 按用户裁定有意改了审查员启动契约，门禁正确拒绝旧形状。测试夹具过时，产品无误。
- `t145-green` exit=1（单独重跑同样）：超时“受管 receiver 就绪并收到派发”。根因：夹具的原生 receiver（`workbench/tests/t145_mouse_receiver.c`）模拟 Codex 启动时打印“Open restricted”信任选择屏；T-141 起 a2a 不再替 worker 选（用户裁定“不自动选”），记 `codex_folder_trust_requested` 并停在启动屏。夹具过时，产品行为符合裁定。
- 后两项交缺陷 ticket T-148（ready_by executor）：只改夹具到 T-141 后的契约，断言、检查名与超时不变；并清点其他仍按旧启动契约写的夹具。

## 更正（T-148 worker 上报 20261023T172046Z）

上面 `t145-green` 的根因写错了。`src/panes.ts` 仍允许选择不持久化的“Open restricted”，T-141 只是把任务释放改成等 Codex 发出 native idle 就绪包。旧 receiver 只打印“Open restricted”、从不发就绪包，所以任务一直不放行。T-148 改的是让 receiver 按真实新契约发就绪包；产品无误这一结论不变。原文保留，不改写。
