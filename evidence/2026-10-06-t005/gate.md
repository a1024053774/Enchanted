# Reality gate：首个交付闭环

REALITY GATE: PASS（只对进入 T-006 的方向成立）

GOAL / NON-GOALS：验证旧会话与未验收候选不能集成；不做成本收益结论、不升级 Herdr。
DECISION：公开 Herdr CLI 配合本地事务账本是否足够开始第一个受管交付切片。
OBSERVED：安装版 start/prompt/get 可操作真实 Codex；运行服务协议兼容；本地上游固定源码可读；
Python 3.9 的 sqlite3/subprocess 和 Git 均已可用；分页 oracle 的参考与坏 starter 有独立输出。
MEASURED：starter 2/10、reference 10/10（原始结果见相邻 JSON）；这是 oracle 区分力，不是产品收益。
INFERRED：首个闭环可以先使用 Herdr 扩展入口，无需改内核；适用范围为可信但会出错的同用户 worker。
UNKNOWN：模型能否按新交付提示自行恢复、首个门禁的运行缺陷；由 T-006 的真实运行核验。
PROBE：输入为独立分页 fixture；先 CLI 多进程负例，再真实 Herdr Codex 候选；
通过条件是冻结候选的独立验收和 CAS 结果均可回读；失败条件为旧结果接受或实际引用与记录不符；
停止条件为不可核对的副作用/越界权限；owner 为 controller，证据为 evidence/2026-10-06-managed-01/。
DECISION CONSEQUENCE：T-005 可关闭，T-006 实现与独立验收按同一冻结契约并行。
NEXT ACTION / OWNER：a2a-build 实现，a2a-check 写独立验收，a2a-monitor 只读采样，controller 集成。
