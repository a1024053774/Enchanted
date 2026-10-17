# 09B／09C 原生角色入口前置

2026-10-14，主控 #157 的计划审稿。**非 blocking 当前读回／计划交接；09B/C launch NO_GO。** 未更改下列产品文件，没有新 launch 材料。

- `workbench/src/daemon.ts:235` 对 Claude 非空 relay_files 明确 controller_relay_not_enabled；launch 凭据也只允许直接 signal。实际角色 send/list/ack 不能靠这个入口完成。
- `workbench/src/gates/cli.ts:203` 附近的会话排队名单没有 stop，随后非 signal 直接 worker_command_forbidden，不能以真实角色工具执行停止。
- `workbench/src/panes.ts:783` 附近 caller 要求 worker attempt，Claude controller 无 attempt；`workbench/src/relay.ts:7` 类型仅 worker/reviewer，attempt 字符串／SQL NOT NULL，也没有角色 stop 协议。
- `workbench/src/claudeLaunch.ts` 把同 root 的 state/repo/home/config 绑在一起，不能在同一 broker 下给两个角色独立 HOME；实际角色 membership 唤醒、tool_use 许可／工具结果与多回合反馈预算也未在 P1 证明。

若直接进入 09B/C，会把入口整体拒绝误当权限反例，或被迫用 operator 写入冒充真实角色。建议主控先审 [PLAN-09BC-01](PLAN-09BC-01.md)，分配最小单角色转交／工具切片的权限和文件所有权，尤其协调 T-080 对 core.ts 的独占；不得只是删拒绝条件或伪造 attempt/null 字段。本 worker 按当前授权只交计划，不实现这些前置、不改地图／新 ticket／他人 attempt。
