# T-093 probe-04 独立只读审查

STATUS: INCOMPLETE
TARGET: T093-port-profile-v5；相对 `f8c1fb7015274bcc729c4ef5bb6eebc307795ca5` 的冻结候选。

来源：干净上下文 reviewer，gpt-6.1-sol / xhigh，按 behavioral-acceptance-review 执行。
未编辑文件、执行真实 CLI、读取凭据、应用沙箱或运行系统追踪。

EVIDENCE:

- 编译与凭据前停止两项定向检查通过。
- 独立调用本机 sandbox_compile_string：额外端口 42、49152 的 localhost TCP4 规则均编译成功；
  对应数值主机规则均被拒绝。未调用 sandbox_apply。
- 版本与权限前检均早于首次凭据操作；网络规则修改保留原文件、Mach、fork 和 deny network* 限制。
- 归属方案保留全部清单差异，区分权限边界与进程归属；实施监控或修改验收均留待批准。
- reviewer session 首尾项目地图检查均为 0 problems、0 stale living docs。

FINDINGS:

- 无阻断性交接发现，可提交 probe-04 命令与归属方案供主控审阅；不能据此宣布运行验证通过。

COUNTEREXAMPLE:

- 数值主机反例被真实系统编译器拒绝。
- 内存中跳过版本失败门禁的变体，被退出码 65 和错误版本两项合同断言拒绝；未执行真实 CLI 或读取凭据。

LIMITATIONS:

- 修正 profile 下真正 --version、端口限制及读/写/fork 拦截仍为 INCOMPLETE。
- 修正候选认证路由尚未实跑；probe-03 五项 HOME 差异仍缺独立归属证据。
- 未执行 --run、Claude、security、凭据读取、sandbox_apply、sudo 或系统追踪。
