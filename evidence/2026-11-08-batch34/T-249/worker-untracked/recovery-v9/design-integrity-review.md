STATUS: PASS
SUMMARY: 恢复一致性与限定结构自查未发现已复现缺陷；这是 worker 自查，不是独立审查。
TARGET: 当前工作树，相对 62faa87b9424e48a4739920b53920d111a057486，恢复 B→C（C=d8f55c958d901d052e79eda1a04dbf0a8fbf5ed5）。
FINDINGS:
- 无已复现的新结构缺陷。
LIMITATIONS:
- 按卡不重审整套旧功能。design-scan.json 的 13 个定位项与 C 的原始代码相同，来源与可达路径已核对上级 stop-hook-check.md；扫描器不是通过证明。
- 文件点击经 CommitDetails→diffArgs→gitRead。精确 no-index 参数与仓库文件约束由实际执行 Git 的宿主拥有；退出 1 且无 stderr 的差异语义转换保留，其他错误不转为成功。未新增包装、重试或平行接口。
- 迟到读取按原 loading 身份更新；错误展示仍属组件。本轮产品和测试未发生新的修改，历史主控窗口证据与原始来源逐字节一致，但新后台窗口尚未运行。
- RUN-OUTSIDE 原样恢复；安全测试 6/6 支持限定清理与红态分类。未在 native sandbox 执行该脚本；新包、限定独立审查及 Terra 由主控负责。
RULE:
- 恢复必须由独立核对的 attempt.base_commit 推导 B→C；逐文件三方合并，保留当前 base，冲突先上报。
