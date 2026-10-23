# T-152 冻结候选只读证据审查

状态：**INCOMPLETE**。对象 `dbd82308a3c43b1bdffd4d092736afb08e8b37d4`，父版 `32ffb4e6d`。审查来源：独立干净上下文 `t152_acceptance_audit`，使用 behavioral-acceptance-review；未读取作者 RESULTS/ASSERTIONS，未运行 CLI/Electron/socket/ps。

独立依据：T-152、T-141、T-082 及授权答复 `20261023T185657Z`、`20261023T125315Z`、`20261023T151224Z`、`20261023T153252Z`。有效检查保留，held socket 加明确拒绝码且在释放前检查；产品代码无修改。

发现：

- P1，`test_t082_review_boundary_e2e.py:27`：旧首次 card_save 在创建任务前只有 bare task、无 project，当前 resolveTask 将返回 unknown_task；提交尾注和 review_packet 也使用短名，必须在局部夹具统一完整任务身份、卡片保留短名。
- P1，`t152_review_host.ts:16`：旧 QualityCase 只有 reviewers 数组，缺少当前 createReview 必需的 reviewer_role_card 与 reviewer_role_card_revision；应局部 configure_host 适配。

反例审核：四个有效检查变异要求特定 ContractFailure、退出码和清理成功；四个启动参数变异要求 review_launch_boundary、paused、issue。未发现任意非零就计红的路径，但变异均未执行，不能认定已拒绝。

局限：没有有效红态或绿态；静态审查不是真实入口证据。请求 high、受控观察 xhigh 的差异未被发现是该套件阻断点，不能把它直接认定为故障。审查后两项夹具问题已局部修正，修正后仍待沙箱外运行和执行主控独立审查。
