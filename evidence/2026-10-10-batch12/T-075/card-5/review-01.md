STATUS: INCOMPLETE

TARGET: 固定候选 [review-candidate-01/manifest.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-10-batch12/T-075/card-5/review-candidate-01/manifest.json)，base HEAD=`2d7d416790e59b2082c9c5bd531b8505c3b4ac6f`。**T-075-5 限定业务 claim：PASS；全卡收尾：INCOMPLETE。**

EVIDENCE:

- 标准来自候选内任务卡、T-075 Acceptance 第 4 条、三份冻结契约、分页 CONTRACT/oracle，以及 controller-decision-01 的 D1/D2/D3。三份原验收文件与 `7bcfe7d9` 逐字节一致。
- 独立读取 outside-full-01 各子运行的 run/test-result、stderr、请求记录、状态读回和归档。交付 **8/8**、恢复 **9/9**、编排 **18/18**、CASRace **1/1** 绿态成立，均无 errors 或 skipped。入口红态覆盖原 35 项，错误均为 socket 路径超限；它只证明生命周期缺口，未被当作业务红态。
- 请求经过产品 CLI→Unix socket→同一个 `serve` 请求处理器→真实门禁。产品差异仅为导出 `serve` 和默认行为不变的构造参数；默认启动路径未使用测试注入。编排五项使用默认 Panes，十三项使用明确标注的受控线程服务。
- 恢复证据核对了后台 PID、代次与屏障父 PID；七次故障均针对本夹具后台，客户端真实退出 1、报告连接中断，没有伪造 `-9`。新 verification 使用不同 ID/worktree；旧输入保留，旧退出结果仍为 unknown。旧 oracle 完成不能解除新 oracle 屏障。
- CAS 前恢复只补一次 Git 副作用；CAS 后恢复不增加 reflog；第三值和删除引用均拒绝恢复，保留原 intent。CASRace 的真实 Git 报告旧值不匹配，并保留外部写入。
- 直接在内存中读取归档的 39 个已 checkpoint SQLite 数据库，与停服前读回核对：业务表一致，仅追加正常停服事件及其序号变化。未发现读回修复吞错或伪造通过。
- 受控 submit 的审计请求与后台接收请求一致；host 原样调用 `super.call(raw, supplied)`。无绑定线程的手工 claim 提交直接进入原门禁，不需要模拟 caller。
- 原运行命令为 `python3 -B workbench/tests/run_daemon_acceptance.py --validation --label outside-full-01`；重新运行须使用新的证据目录名。本审查没有运行测试或后台。

FINDINGS:

- 未发现限定业务 claim 的确认违规，无新增 P1/P2/P3 修复项。
- 已知交付收尾限制仍存在：实际仓库 `project_map.py status` 为 **0 problems、1 stale living doc**，涉及 `workbench/README.md`。此项已交执行主控处理，超出 worker 写入范围；不能据业务 PASS 宣布全卡完成。

COUNTEREXAMPLE:

- **Fence：有效。** 实际归档变异体只删除 fence 检查；错误 fence=32 被接受，原测试的拒绝断言失败。
- **CAS：有效。** 只删除 Git 期望旧值；真实 Git 覆盖外部引用，原断言发现错误接受、引用丢失和 accepted 状态。
- **操作锁：有效。** 只删除锁事务；第二个 verify 启动第二个 oracle，并发 integrate 成功，原业务断言失败。
- 三项均在业务断言上失败，**0 errors**；归档源码与所述单点变异一致，未以环境错误充数。

LIMITATIONS:

- 全卡仍需执行主控处理 README stale，并取得实际仓库的收尾证据。
- 十三项受控线程场景不证明真实 PTY、Codex 或 B 转交通道；本卡不覆盖 UI、S2–S5、真实模型回合、生产发布、可靠性或成本。
- 编排/状态、异步、身份/范围、CLI、文件、Git 副作用和本地恢复适用；检索/RAG、模型理解及生产部署为 N/A。
- 本次仅做一次 API 新上下文只读审查；没有真实 CLI reviewer 的 argv/tier 证明，不能声称实际 Fast tier。资源退出结论基于保存的原始记录，未查询当前进程。

RULE:

- 沿用现有 `project_map.py status` 收尾门禁：业务验收 PASS 不能替代 living doc 收尾完成。
