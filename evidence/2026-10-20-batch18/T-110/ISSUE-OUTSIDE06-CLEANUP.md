T-110 第六轮另有一条清理异常，不属于本轮序号修复。

原件 `/private/tmp/t110-outside-06.json`，green 夹具 `/private/tmp/t078-2-t110-gwxadlvy/fixtures/t110-native-turn-d0baljiw`。daemon PID 34819 已由测试确认退出；native PID 34879 的原 owner 记录包含完整 CLI session 与启动命令，但最终 ps 观察的 command 变成 `(2.1.304)`、stat 为 `?E`。原清理函数因身份不一致拒绝继续发信号，记录 `Process identity changed; refuse signal`。

worker 没有尝试放宽身份检查、向不确定进程发信号或删除原夹具。建议主控核对该旧 PID 当前是否已退出；若还存在，由主控按运行记录核对身份再处理。本轮测试继续保留原清理检查，此异常不能计为业务红态，也不能作为已完成清理的证据。不阻塞准备新候选。
