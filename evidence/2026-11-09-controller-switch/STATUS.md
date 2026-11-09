
2026-11-09T14:08:07.715325+00:00 T-249-1 门禁集成返回见 integrate-t249-01.json；下一步核对状态与 evidence。

2026-11-09T14:08:10.606439+00:00 T-266 INCOMPLETE：外部候选/父版/三变异证据 PASS，已回传 #2；等待 worker 提交及独立审查。旧诊断两版失败另留记录。

2026-11-09T14:09:18.070487+00:00 T-249-1 PASS：门禁 accepted、intent completed，本地 main=4164b43a81ac5092ec35d7f881967ec3947bad66，evidence 无删除；下一步安装及证据工具交付。

2026-11-09T14:10:50.228977+00:00 T-250 INCOMPLETE：已注册并派发 attempt 528c29ab-838f-473f-9d35-5b1ff360fd49；写入范围与 T-266 不重叠；下一步观察启动与交付。

2026-11-09T14:11:27.704322+00:00 T-250 BLOCKED：启动核对 Unexpected end of JSON input，输入仍排队；现场 t250-startup-*.json，先完成 T-266 后恢复原任务，不重复输入。

2026-11-09T14:26:34.618074+00:00 T-266 INCOMPLETE：eb5a8968a 已交付；门禁干净副本缺 effect，红态/候选初始化失败。原 attempt 已回收，v2 已派发并绑定 native session 01a1c0b1-88fb-79b0-b354-2144383cdaad，修测试依赖供给。
2026-11-09T14:26:34.618201+00:00 T-250 BLOCKED：正常重启后进程已停止，native_session=null 的身份冲突仍拒绝回收；已开 T-267，未改门禁或正式数据。后台正常恢复 PID 80941。
