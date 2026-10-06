# T-024 独立审查与范围澄清

**STATUS: INCOMPLETE**。双客户端真实探针的结果为 PASS，但独立审查未出具 PASS；交接保守报告 INCOMPLETE。事实问题已经得到回答，不能将这个状态解释为引擎不支持两个项目的独立客户端，也不能把本次研究用于 M1 发布或运行时切换。

原始返回完整保存在 [acceptance-review-01.md](acceptance-review-01.md)，不覆盖。审查指定的冻结候选是 `run-08/` 和只读 `.upstream/herdr@c4653a4f10502601ac110b12b2c45a5f7134082b`。同一审查员随后仅澄清原范围发现，没有第二轮审查、没有重跑探针。

## 审查员的原范围澄清

> 我没有观察到 `run-08/` 文件集或目标源码 `.upstream/herdr@c4653a4f10502601ac110b12b2c45a5f7134082b` 的实际内容、HEAD 或源码工作树变化；上游仍是该提交且状态干净。变化只出现在并行 T-026 的 `MAP.md`、`AGENTS.md` 及其构建治理文件。
>
> 因此，原 P1 不应解释为 run-08 的行为缺陷；它仅记录我当时按技能中“branch/diff 变化”的严格工作区级解读所采用的冻结限制。若将 `diff` 限定为指定候选及目标源码，P1 对目标本身不适用；但按原审查记录保留 `INCOMPLETE`，不将其升级为 PASS。
>
> 其余验收证据已完成审查：真实 Herdr 0.9.3 endpoint generation 1 双客户端、同引擎 boot ID、不同 workspace/task 焦点、独立及共享 PTY 尺寸边界、随机 nonce 输入隔离、公共 CLI 广播负面对照、探针清理，以及默认 server 前后身份/状态/控制进程保持一致。

## 并行变化的范围

实现 worker 只读核对的工作区变化为：`MAP.md` 的 README covers 加上 `scripts/build`；`AGENTS.md` 增加 T-026 的 Rust 构建统一入口规则。仓库 HEAD 当时仍为 `5de427ee924943fbcc034feb96e8b23dd2272429`。这两项未改变 T-024 的 endpoint 合同，也未触发构建；本 worker 未写入它们。

审查任务身份为 `/root/t024_acceptance_audit`，配置角色 `acceptance-auditor`；其原始结论、范围修正和不足都保留。该审查不作为即时 monitor，不补称运行期间存在独立监控。
