# T-007 恢复验收（2026-10-06）

状态：PASS，限 macOS/POSIX 的真实本地 CLI、SQLite、Git 恢复。
固定候选：95cc3a25cf31f56dde85728c5798888d1e311de8。

- 父版本 aca370a：9 项中 4 项业务失败、5 项通过；最终父版运行无夹具错误。
- 修复版本：恢复 9/9（117 条断言）、T-006 回归 8/8。
- 真实故障：核对自建 CLI 身份后 SIGKILL；oracle、Git 包装器是外部屏障，真实 Git 未被 mock。
- 已证实：活跃操作拒绝重入；中断验收新 ID 完整复验；pendingG 同意图继续一次 CAS；
  pendingM 只补记，零重复 Git 写入；第三值/删引用拒绝且保留；旧身份与旧规格不复活。
- 反事实：信任 intent.M 而不核对真实引用的 mutant 出现 3 项业务失败、0 夹具错误。
- 独立审查 PASS：[review.txt](review.txt)。没有为该本地恢复声明重跑模型或假装测试了 Herdr server 崩溃。

## 重现

```sh
python3 -B acceptance/test_recovery_e2e.py
python3 -B acceptance/test_coop_e2e.py
```

两条命令新建隔离 repo/state 并保留产物。父版本命令见 red-ready.json；故障原始记录：
check-20261006T060615.461887Z-464eb642.json（父版本）、
check-20261006T061047.540153Z-cc60e8f8.json（修复）、
check-20261006T061642.829217Z-0f8e9a24.json（mutant）。
最初夹具观察错误留在先前文件中，未算作产品红态。
模型配置只观测请求/UI，不声称供应商实际 tier。无成本、吞吐或可靠性收益结论。
