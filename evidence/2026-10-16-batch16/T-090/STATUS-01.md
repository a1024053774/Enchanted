# T-090-1 开始状态

状态：INCOMPLETE。task `T-090`，attempt `a1`，worker `s16-t090`，session `b799f9d6-67fa-4ae2-8cb0-e97906f4f4ad`，启动记录 `launch-b4da324aa23d48eda3c1cfcee621a6c5`。起点 `f08a280bdf6142443efd52d4897d2305fd68987f`，工作树初始干净。

目标：以审查开始时 worker 的实际 HEAD、分支和干净状态为结束核对基准。继续核对冻结候选、审查目录、共享 refs 和结束核对后才可集成。非目标及写入边界按当前对话的 T-090-1 任务卡；不改 `acceptance/`、冻结协议、地图、全局配置或审查启动边界。

验收：原冻结候选用例先红后绿；审查期间 worker HEAD、脏状态及分支变化仍拒绝；原交付 8、恢复 9、编排 18，以及 T-082 结束核对与四启动变异通过。受控宿主检查由执行主控运行；本 worker 不请求沙箱升级。真实模型回合为 0。

使用技能：`project-map`、`evidence-first-testing`、`document-writing`。开始时已读取项目地图、术语表、intent、角色卡、T-090、T-082、T-078 诊断与两版本对照。诊断支持结束核对比错对象；旧版本证据不替代本起点红态。

`project_map.py status --root .` 退出码 1：1 problem，0 stale living docs。唯一 problem 为 `.project-map/MAP.md` 的 `../.grilling/a2a-gui-client.md` 断链；这是起点已存在的问题，超出本卡写入范围，请执行主控处理或核对稀疏检出。未修改地图。

Tracer bullet：先沿原验收的真实 CLI → 编排后台 → 审查结束核对取得红绿证据，再执行其他边界与整组检查。Deep modules：在现有门禁里修正绑定，不增加入口或兼容路径。Ubiquitous language：沿用候选、worker worktree、审查目录、共享 refs、review_reclaimed。

宿主命令（从本 worktree 执行）：

```sh
python3 -B evidence/2026-10-16-batch16/T-090/run-host.py --phase red --label red-01
```

脚本将起点源码与当前测试选择器复制到外置盘隔离 checkout，补齐夹具，并只借用既有依赖，不安装、不构建、不链接构建输出。原始现场直接保存在 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/red-01/`。临时运行夹具复制到该归档，核对文件数和字节数一致后才清理原目录。源码不做 reset，不伪造审查结果或回收事件。
