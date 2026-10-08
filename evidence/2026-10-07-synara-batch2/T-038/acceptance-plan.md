# T-038 验证输入与失败清单（2026-10-07）

本页在实现前写定输入与预期；预期来自 ticket、M1 spec 和主控决定 03。它不是验证结果。

## 首个接缝

隔离 Synara 服务端启动后，对 `/api/a2a/membership` 发 GET。空目录应返回 HTTP 200、`ok=true`、`tasks=[]`。同一个 `http-probe.py` 分别保存实现前和实现后的原始 body/status；不存在端点的 404 是预期合同红态，缺依赖、服务器没启动或认证失败只记环境/夹具失败。

## 实际入口场景

在本次新建 Git repo、外置盘 t038 数据 home 与独立端口中操作：

1. 用门禁 CLI create 创建受管任务（--state 指向真实服务器的隔离门禁目录），另建同项目下一个未挂合同的任务。通过原生 project.create/thread.create 建立对应项目与 worker、reviewer 两个空会话，不启动 turn，不调用模型。此处只证明界面与归属，不声称原生 provider 运行通过。
2. 经归属 HTTP API 保存同项目、task id、两个 thread 与角色。拒绝未知 project/thread、跨项目 thread、同任务内重复 thread 和旧 revision；拒绝受管任务与门禁 core 的 project 不一致。membership 只分组，不授予门禁权限；不额外施加未经规格要求的跨任务独占约束。
3. 经 CLI claim、submit、verify 推进受管夹具。第一版候选违反预先写定的 oracle 输入，verify 必须失败；界面显示实际失败及 command stderr。修复候选在新的 attempt 中显式 submit，通过 oracle，显示 verified；随后 CLI integrate 显示 accepted。
4. 图像证据至少包含项目下两个任务、所选任务下 worker/reviewer 并列、claimed/submitted/失败/verified/accepted，并关联完整 CLI 输出。运行 dev web 时明确它与打包桌面版的区别；没有桌面证据时不勾选桌面验收。
5. 停止本次启动的隔离服务并以同 home 重启，再从 API 和界面回读两个任务及角色。保存线程表的列清单；不改 upstream migration 或 projection schema。

## 可辨识的失败

- membership 必须存于服务端，不能用 localStorage 或创建关系代替；重启和客户端更换需保持。
- membership 没有门禁业务 state，也不写原生 ProjectTask 状态。界面不从 agent idle/done 或模型报告推断通过。
- 状态/事件请求失败必须可见，旧数据不能继续冒充当前值；切换任务时不显示上一任务的状态。
- 人工介入字段按 [T-037 契约](../T-037/human-intervention-event.md) 读取：只认 type=human_intervention、dispatch_origin=user，按 event_id 去重，在对应 thread 标记。还需拒绝跨 task 归属；历史 attempt 的事件仍跟随原 thread。当前分支无真实事件，明确标注的夹具只验证读取逻辑，不作为真实输入监听证据。没有事件时显示空，不伪造事件。
- UI 的受管业务操作只 POST 既有 `/api/a2a`，绑定所展示的 attempt；迟到结果不能操作新的 attempt。
- 现有主题、组件和字号设置必须沿用；外观仍由用户判断。

## 完成检查点

冻结 fork commit、T-038 自有文件、治理与规格文件清单后执行 fresh-context 只读独立审查。主控仍写的 controller-poll.log、launch-argv.txt、panes.txt 不在冻结清单中。typecheck、lint、fmt:check 和相关现有测试记录真实结果，不以局部通过覆盖全仓异常。ticket 保持 open，结论写待主控关闭。
