# T-093 probe-08 冻结候选独立审查（2026-10-17）

审查员 `/root/onboarding_state_review`，gpt-6.1-sol / xhigh，新上下文、只读。
结论只覆盖探针准备，不是 T-093 产品验收或实际 CLI 跳过结果。

```text
STATUS: PASS
TARGET: T093-onboarding-v9；基于 e5da995988d49409ed8931013197475cb0d8af3e 的冻结未提交候选；仅审查探针准备。
EVIDENCE:
- 只读 mmap 核对 2.1.302：摘要的文件大小、mtime 与全部摘录相符；完成字段控制 Onboarding 加载，状态路径服从 CLAUDE_CONFIG_DIR。
- probe_t093_normal_login.py:293、722：显式选项才生成私有状态，早于 CLI/auth；O_EXCL、O_NOFOLLOW、0600，正文恰为单字段布尔 true。
- 独立运行单项合成状态测试，1/1 通过；未运行真实 CLI、认证或网络。
- probe_t093_normal_login.py:684：正向条件仍要求原 bearer 的本地 POST /v1/messages 和 messages。
- 开始、结束 project-map status 均为 0 problems、0 stale；候选状态未变化。
FINDINGS:
- 无范围内阻断项。文档正确区分内部版本绑定状态、静态推断和待运行事实。
COUNTEREXAMPLE:
- 合成测试拒绝已有文件、祖先链接及额外字段；独立解析文件核对路径、值和权限。
- 已保存变异证据拒绝 false 值、错误路径和忽略显式选项；本次未重跑整套变异。
LIMITATIONS:
- 实际 CLI 是否采用状态、是否跳过预检及是否发出认证本地请求仍为 INCOMPLETE，须主控执行 probe-08。
- 未重新访问官方网页，未运行顺序替身测试、真实沙箱或产品通路；PASS 不表示产品完成或所有网络路径经过 relay。
RULE:
- N/A；未发现需新增规则的重复失败类。
```
