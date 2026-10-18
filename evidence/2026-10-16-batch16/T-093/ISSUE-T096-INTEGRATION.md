# 集成前检查：T-096 恢复入口与进程查询接口

状态：**INCOMPLETE，阻塞 T-093＋T-096 的集成通过结论；不阻塞本票提示比对修复的局部检查。**
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

本 worker 没有把 T-096 代码合进本 worktree，不 push、不 rebase、不直接修改另一票的文件或地图，也没有把 T-096 旧 PASS 当本候选的非退化证据。
