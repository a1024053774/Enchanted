# T-082 needs-decision：两项验收口径（2026-10-16）

T-082 第二轮独立审查（independent-review-02.md，冻结候选 5f7f9816e）：未发现产品缺陷，第一轮五条全部解决，审查员自建四个错误实现均在指定断言处被拒；整票 INCOMPLETE 只因下面两项验收口径，执行主控无权自行豁免。

## 1. Acceptance 2"每种先见红"的时间顺序
票据第 28 行要求四种启动参数（旧只读 argv、工作目录非副本、网络开、/tmp 可写）"每种先见红"。实际：wrong-workspace 有修前的真实红绿顺序；readonly-argv 有修前读回；network-enabled、tmp-writable 及 wrong-workspace 的起点红态（outside-command-10-01）是修复之后在起点版本 451be8462 上重建的反事实（run.json 原文 `reconstructed after the fix on the starting revision; not an earlier chronological run`）。旧门禁对这三种参数确实放行（ok:true），新门禁确实拒收，但时间顺序无法事后补出。
选项：A. 接受"修复后在起点版本重建的红态"等价满足"先见红"（推荐：反事实对照与修前运行证明的是同一事实，补不出历史顺序）；B. 不接受，T-082 保持 INCOMPLETE 或改写该验收条件。

## 2. T-076 质量 runner 的源码审计锚点
T-076 的 run_t076_quality_green.py 自带源码审计：验收文件相对 T-076 冻结提交 a7f4cc30 不得变化。D3 必须替换其中"reviewer 只读"断言（票据写明"T-076 的只读证明随本票换成新边界的证明"），所以该 runner 按设计会一直拒收。T-076 的三项性质（审查绑定、不续接会话、写入会话不能审查）已在候选上直接跑通（outside-command-07-01 与审查 02 的 R/07）。
选项：A. 把审计锚点迁到 T-082 合入后的新基线，并在 T-076 记录中留痕（改的是 T-076 的验收锚点）；B. 不迁，T-076 完整 runner 保持"被审计拒收"的已知状态，以三项性质直跑作为 T-082 的回归证据（推荐，改动最小）；C. 其他。

其余：P3（launch-policy runner 两个状态字段不同步）已交 worker 修；真实回合用 2/4。
