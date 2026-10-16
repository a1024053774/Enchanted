# #331 完整只读分页的失败方式与完成条件

Tracer bullet：真实 P1 screen 参数入口 → 逐页 pane_output → 连续完整字节/范围收据 → E4 原前缀核对与追加恢复收据 → Enter 前同一 reader 再完整核对。Deep modules：只新增一个共享分页 reader，三个既有调用共用；业务输入、Stop/relay、protocol、预算不改。Ubiquitous language：旧截断前缀、完整原件、完整恢复收据分别记录，不把前缀一致写成完整批准。

预先列出的失败方式：

- 只读首个 64 KiB 页就返回；必须被完整字节/范围断言检出。
- 中途 total_bytes 变化；必须拒绝，不追随增长或重试。
- total 之前零进度、缺页、起始 offset 不连续、next_offset 与解码字节数不符、跨过 total、launch 错误或无效 base64；必须拒绝。
- 最后一页之后仍有新增字节；末端只读确认也须拒绝 total 变化。
- 截断元数据被标成 complete，或者完整文件的长度与范围不符；Enter 前必须拒绝。
- E4 新原件不是旧参考的严格前缀扩展，或者 launch/session/dispatch/permission_event 不对应；恢复脚本不得生成新许可批准。
- 新 harness 里任何非授权旧文件发生字节变化；冻结和执行前核对必须拒绝。
- 已有输出、旧 dispatch/reference、旧 screen -01 或旧未签 permission-approval-01 被覆盖；必须拒绝。
- 分页、恢复与核对过程中出现任何非 pane_output 的业务命令、窗口、按键或进程启动；测试夹具拒绝并记录。

红态保留 #330 的实际门禁页（0→65536，总计76125）及前一提交的三个原调用。测试走真实 P1 screen 参数入口，确定性的只读 pane_output 传输夹具提供长字节流；不启动 Claude、API 或 A-15 daemon。期望字节由独立夹具 nonce 构造，首个页、每个 offset 和最后 EOF 均核对。另以只读一页的已知坏 reader 验证同一测试会失败。mock 只替代输出传输，不替代分页逻辑；这不声称已实跑 A-15 恢复。

完成条件：候选入口绿；首个页、变化 total、零进度至少三个反例被拒；三个调用均使用同一 reader；历史原屏按当时 total 审计；新源冻结逐字核对其余旧文件不变；E4/E5 命令只交主控，不执行现场。
