# T-110 重连界面修复

INCOMPLETE。本轮起点 `e1c7b5c275eaca7e342da44cb2582cf81f56ca17`。第五轮两个旧红态成立，green 在恢复后未看到原问题；现已修复产品的选择身份丢失，并让测试走现有的手动重连入口。本地红／绿、IPC、快照、T-108 与构建通过，新的完整原生入口待主控运行。

## 判断依据

- 原件 `/private/tmp/t110-outside-05.json`，夹具根 `/private/tmp/t078-2-t110-jmj14bo5`。green 的窗口帧 95 显示重载后项目／agent／问题均为空，侧栏 ENOENT；帧 126 起项目列表重新出现并显示可信的待答状态，catalog error 消失，agent 和问题仍为空。精简状态转换在 `outside-05-summary.json`。这表明侧栏读取已恢复；错误文本留在窗格的停止读取状态中，不代表每一帧仍在向 socket 发请求。
- 测试没有重启 daemon，只把本次夹具的 control.sock 改名并移回。原 daemon PID 12700 在测试最终收尾时才处理 daemon_stop，cleanup 确认其退出。收尾后的 socket／PID 文件缺失符合 daemon shutdown 的清理，不是运行中未恢复的证据。daemon stderr 为空。
- 产品问题：renderer 的 refresh 把 sidebar 和本地 selection 放入同一个 Promise.all；断连中重载时，sidebar 失败会使已经可用的本地选择也不落到界面。后续侧栏轮询只恢复目录事实，没有恢复 selectedProject，agent 树因按所选项目过滤而为空。
- 测试问题：SessionPane 的 read 在失败后停止，界面提供“重新连接”按钮；原测试只恢复 socket，随后等待自动继续读取，没有操作这个既有入口。按当前规则不增加自动重试，也不能把测试中的自动恢复假设变成产品新策略。

## 变更与证据

产品只调整 renderer.tsx 的 refresh：先从主进程读取并应用本窗口已绑定的任务、项目、paneKeys、布局和名称，再请求侧栏；侧栏失败仍显示原错误，只有成功读取并确认任务移除才清空任务。没有新 fallback、重试或 API，没有改信号、通知中心、门禁或权限。

- `node workbench/tests/test_t110_reconnect_view.mjs <新摘要>`：修前有效红态 `reconnect-view-red-02.json` 在“断连中重载须保留本地项目”失败；修后 `reconnect-view-green.json` PASS，也保留真实错误、原布局／名称及确认任务移除的旧行为。首个 `reconnect-view-red.json` 是 TS 非空断言未剥除的探针配置错误，已保留，不能计为业务红态。
- `reconnect-ipc-green.json`：原 IPC 身份／越权／只读／布局／断连错误合同 PASS；`reconnect-snapshot-green.json`：可选字段 JSON 契约 PASS；`reconnect-questions-green.json`：T-108 的 429 个 hook 异常案例、14 个作答生命周期案例 PASS。
- `reconnect-local-checks.json`：构建 PASS，临时构建与缓存已清理。上述本地证据不冒充新的真实 Electron 通过或独立审查。

真实入口现在在恢复时核对原 socket inode 和 daemon PID，并经实际 main/preload/sidebar 读取确认原 launch 仍在等待同一个问题，核对主进程仍绑定原项目和 paneKey。界面必须自行保留所选项目，不能靠重新选择项目掩盖缺陷。随后在原 paneKey 对应的窗格点击可见“重新连接”按钮，再执行原有“同一原生问题回来、通知为空”的断言；刷新／重载后的去重、原 PTY 作答及回执断言均保留。

脚本还新增 `red-reconnect-view`：把产品的 main／center／renderer 切回 e1c7b5c27，必须先证实后端原问题已恢复，再在“界面重载保留所选项目”业务断言失败。依赖、socket 恢复失败或导入错误不能算作该红态。

```sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-COMMIT-04.sh
zsh evidence/2026-10-20-batch18/T-110/RUN-OUTSIDE-NO-MODEL.sh /private/tmp/t110-outside-06.json
```

共五个场景：隐藏通知坏变异、c5ac40c0b 断连坏候选、e1c7b5c27 选择丢失坏候选、修后正常闭环、修后禁用通知。仍不调用模型或供应商、不保存截图、不自动重试；只操作测试自己的 socket、应用与原窗格。旧现场没有覆盖或删除。
