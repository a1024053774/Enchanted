STATUS: PASS
TARGET: 4b64e4cdd43e1e8e4c1f7bfaa2c66776f3985fa8（仅离线策略修复）
EVIDENCE:
- `controller-decision-01.md` 独立定义：固定用量 origin 仅放行 IPv4 `198.18.0.0/15`，其他保留地址与默认出站策略不变。
- `fix/offline-red-20261009T064128195524Z` 实际为候选绿态：记录冻结提交、干净 worktree、完整 argv、exit 0；生产 batch 入口在外部输入 17／47 下，三家 provider 均返回 `ok` 与对应额度。DNS／transport 替换位于真实策略之后，未兑换 token。
- `fix/boundary-20261009T064048141186Z`：18 项通过；保存的生产 patch、测试均与冻结候选一致。覆盖子网端点、其他保留地址、非白名单、混合 DNS、不同端口及默认非用量请求。
- 默认地址策略源文件未修改；`fix/shared-20261009T064048129086Z` 13 项通过。
FINDINGS:
- 未发现所声明离线契约的可达违规。
COUNTEREXAMPLE:
- `fix/counterfactual-20261009T063904298627Z`：已知坏生产路径 exit 1，三家快照均为 `error`、额度为空、transport 0；同一离线输入 fixture 在冻结候选通过。
- `fix/mutant-20261009T064028657229Z`：删除 origin 限制后，5 项业务拒绝断言失败，明确捕获越权放行；其测试与冻结测试仅格式不同。
LIMITATIONS:
- PASS 只覆盖离线 policy／生产解析链路，不证明真实代理、TLS、provider 鉴权、正式工作台或 UI 成功；这些边界仍为 INCOMPLETE。
- counterfactual 首个失败断言是 transport 次数；业务红态来自保存的快照独立核对。该早期目录未保存 runner 副本或替换后源码，精确反事实来源追溯弱于候选绿态。
- 目录名称不作为结果依据；没有重跑测试、联网、使用真实凭据或修改文件。
