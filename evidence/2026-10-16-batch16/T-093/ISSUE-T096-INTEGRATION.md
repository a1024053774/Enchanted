# 集成前检查：T-096 恢复入口与进程查询接口

状态：**INCOMPLETE，阻塞 T-093＋T-096 的集成通过结论；不阻塞本票提示比对修复的局部检查。**
2026-10-18 主控 #122 更新：main 0e92f78ec（含 T-096 fd5c93e6e）已由主控合并为 64c6456de2b7c0111628defce442d999a26734db。worker 已在恢复路径实现运行时规范身份，旧记录／argv／版本／session 合同保留；原生七项恢复回归仍未执行，故集成通过结论继续 INCOMPLETE。失败按主控裁定重开 T-096。
来源：主控 #111 要求列出全 pane 影响；只读来源为 exec/t096 的 d61876fe29916ccf577da7b9b912cf305d9fdd9d，未修改该分支或其 attempt。

观察到：该版本 `workbench/src/panes.ts:230–246` 在版本校验后创建恢复 PTY，并直接以保存的旧 record 作为 pane.record；原版本 record 没有 executable_path。
T-093 的进程查询使用该字段与内核路径比较。若集成时只替换 processInfo，而恢复入口仍直接复用旧 record，旧记录将无法得到 leader，最后报 restore_process_missing。
另外，T-096 的 test_t096_restore.mjs 仍提供 /bin/ps 文本替身；查询实现替换后，需在测试 IO 边界提供新 JSON 协议，不能将边界拒绝当业务回归通过。

建议由执行主控在受管集成候选协调两票修改：

1. 保留 T-096 全 argv／版本／session／worker 不恢复等检查；在其已有版本校验之后、PTY 启动之前，确定恢复运行的规范可执行身份。
2. 新记录已有 executable_path 时核对其与当前解析路径一致；旧记录缺少该新增元数据时，按原已验收 argv＋版本合同确定运行身份，放入运行时 record 副本。不得修改不可变的原启动记录或改变原 argv。
3. 不在每次查询时重新解析 alias 来替代启动绑定；本票的 alias 改指反例已拒绝这种修法。
4. 更新纯合同测试的 subprocess／realpath IO 替身以对应实际新边界，保留原业务预期和变异断言。不得绕开 processInfo、把 leader 固定为成功或删除旧记录正例。
5. 执行请求 13 中的 T-096 纯合同与原生重启回归；缺任一层证据，整体仍 INCOMPLETE。

以上观察及建议保留为主控 #111 阶段的原始问题。主控 #122 合并后，已在版本／native session 核对之后、PTY spawn 之前 realpathSync(argv[0])；已有 executable_path 不一致则拒绝，合法旧记录仅在运行时 record 副本补齐。
test_t096_restore.mjs 的旧记录正例仍保留，另覆盖已有身份匹配／改变，历史记录不变、完整 argv、worker 未恢复、空布局及原变异断言均保留；IO 替身对应 libproc JSON，不给固定 leader。合并后的纯合同已通过，原生回归入口见请求 16；不 push、不 rebase、不改另一票地图／验收状态。
