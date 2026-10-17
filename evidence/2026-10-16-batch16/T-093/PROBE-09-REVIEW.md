# T-093 probe-09 固定路径只读审查（2026-10-17）

审查员 `/root/terminal09_path_review`，gpt-6.1-sol / xhigh，新上下文、只读。

```text
STATUS: PASS
TARGET: T093-terminal09-v10；基于 16791d6debf730cf9ed56bc77d5f2447bdb3ca88 的冻结未提交 diff，仅限路径替换与不新增按键。
EVIDENCE:
- workbench/tests/probe_t093_normal_login.py:32,880 仅修改 terminal-07→terminal-09 和帮助文案；route、按键、profile、脱敏、扫描及 onboarding 状态代码无变更。
- 独立核对新固定路径与任务合同完全一致。新增测试直接调用 run，期望值来自合同字面值，未导入生产路径常量。
- 已运行 PYTHONDONTWRITEBYTECODE=1 python3 workbench/tests/test_t093_probe_safety.py ProbeSafety.test_terminal09_is_the_only_approved_export_destination：退出 0，1 测试通过、未跳过；09 进入私有准备阶段，07 和 .extra 路径提前拒绝。
- PROBE-09.md:16 保留 --prepare-onboarding-state 并添加指定 --terminal-output；第 22 行明确禁止新增自动输入。
- 审查前后 diff 未变；project-map status 均为 0 problems、0 stale。
FINDINGS:
- 无本次范围内缺陷。
COUNTEREXAMPLE:
- check-probe.py:104 将固定路径变回 terminal-07。已保存的红态和 probe-helper-checks-19.json 均显示该变异被两条业务断言拒绝。
- 现有检查记录包含 19 测试、33 个断言拒绝的变异；本审查未重跑整套。
LIMITATIONS:
- 证据限于 L0 静态差异与 L1 隔离路径逻辑；不证明真实终端导出、登录、路由或屏幕结果。
- 未运行真实 probe、CLI、auth/security/ps，未访问指定终端文件；未重新审查原脱敏算法。
- 已有文件拒绝及独占创建代码保持原样，本次未重新执行这些场景。
RULE:
- 无新增重复失败类别；无需新增规则。
```
