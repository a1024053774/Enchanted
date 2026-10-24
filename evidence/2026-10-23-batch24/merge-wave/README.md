# batch24 整批合并回归（T-164 前）

脚本 `RUN-MERGE-REGRESSION-08.sh <rev>`：上一轮 07 的全部检查，加 T-156～T-165 的离线测试与构建，共 46 项；0 个真实模型回合（T-163 需真实 Haiku，不在此列）。在 `/Users/luckye/Documents/Code/a2a-merge-check` 的分离检出中运行。

| 运行 | 版本 | 结果 |
| --- | --- | --- |
| run-20261024T054303Z | 5c2e0df20（T-165 合并 + README） | 43/46；失败 3 项，见下 |
| run-20261024T060045Z | 093b9d515（测试修正后） | 46/46 通过 |

退出码保存在 `exits-5c2e0df20.txt` 与 `exits-093b9d515.txt`；完整运行目录按 T-088 归档，见同目录 `*.archive.json`。

## 第一次运行的 3 项失败及处理（都不是产品缺陷）

- `t143-retained-focus`：在 T-161 合并（ab8cb0fa4）后开始失败，`ReferenceError: snapshot is not defined`；逐个合并点核对，c29615893、fd00ec8f8、167d2c803 都通过。原因是 T-161 让焦点 effect 只对可写窗格生效，测试的 VM 上下文没有 `snapshot`。修正：给上下文补 `snapshot: { input_enabled: true }`（本测试覆盖可写窗格）。修正后的测试在当前 main 与 167d2c803 上都通过。
- `t091-migrated`：07/08 脚本漏传 `--experimental-vm-modules`，测试在加载阶段就失败（batch23 最后一次回归也同样失败，被掩盖了）。补参数后暴露两处测试与合同脱节：T-160 新增 `a2a:review-restart` 未登记；T-159 后从任务视图新开终端留在任务视图，测试仍断言跳到项目视图。按 T-159 用户决定改了期望。修正后在当前 main 通过，在 T-159 之前的 c444fc82e 上按预期失败于“Task terminal creation keeps the task view”。
- `t107`：在 c29615893、fd00ec8f8、167d2c803、ab8cb0fa4 上同样失败，原因是本机 Claude Code 更新到 2.1.310 后拒绝单独一条 `sleep 45`（工具结果“Blocked: standalone sleep 45”）。修正：长命令改为 `python3 -c "import time; time.sleep(45)"`。修正后在 5c2e0df20 上通过。

以上改动只涉及测试与回归脚本，执行主控自行修正，提交 93b9d515d。

## T-166～T-168 合并后（RUN-MERGE-REGRESSION-09）

脚本 `RUN-MERGE-REGRESSION-09.sh <rev>`：08 的 46 项加 T-166（端到端、主机级）、T-167（receipt、dialog-open；真实 Codex CLI 对本地脚本化 Responses）、T-168，共 51 项；0 个厂商模型回合。

| 运行 | 版本 | 结果 |
| --- | --- | --- |
| run-20261024T075759Z | 5380ebb28（T-167 合并后的 main） | 51/51 通过 |

退出码见 `exits-5380ebb28.txt`。
