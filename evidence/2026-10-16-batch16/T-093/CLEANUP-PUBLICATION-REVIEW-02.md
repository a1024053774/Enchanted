STATUS: INCOMPLETE
TARGET: 965560422036ae4382036a9e68758abe0fd74baf；比较基线 de956c2de70ee0e5f8a564cad961bb132a20de40
EVIDENCE:
- 限定复核前两项发现及直接修复；相关文件与冻结候选无差异。
- 实跑 `python3 -I -S -B workbench/tests/test_t093_prepare_failure.py /private/tmp/t093-followup-review-2ZwSlM/prepare.json`：PASS，3 项。
- 实跑 `python3 -I -S -B workbench/tests/test_t093_chain_cleanup_oracle.py /private/tmp/t093-followup-review-2ZwSlM/oracle.json`：PASS，12 项。
- prepare 在内部 rmtree 前调用发布器；清理 OSError 单列，原异常保留。生产入口使用不可覆盖的主错误 JSON 和独立清理收据。
- V 绑定登记身份，并分别探测全部组、子进程和 reporter。
- project_map.py status：0 problems、0 stale living docs。
FINDINGS:
- 本次限定范围无遗留发现；前两项 P1 的 L1 逻辑缺口已关闭。
COUNTEREXAMPLE:
- 原准备失败叠加 ENOTEMPTY：当前保留 RuntimeError，清理错误保持次要。
- 活组／子进程谎报 exited=true、身份错配、遗漏子进程：当前均被拒绝。
- 已检查 red-03 原件：旧实现分别未通过准备前发布检查、活组／子进程及身份错配检查；本轮未重跑旧版本。
LIMITATIONS:
- 真实 OS 探针、D unlink／正文拒读、同 profile 两场演练及正式六场仍为 INCOMPLETE。
- 本轮仅运行合成失败和模拟 PID 探针；未运行 sandbox-exec、真实认证、网络、进程清单或现存夹具操作。
- 两项局部修复通过不构成完整链验收通过。
RULE:
- 无新增规则；前轮要求的准备失败及虚假退出收据反例已纳入对应测试。
