# A-15 ideation B1 待批材料

PASS（文件生成与静态核对）；B1 dry-run / real 均未运行，角色 CLI 未启动，未发送输入。生成命令是 `09b-a15-materials-01/ROLE-MATERIAL-COMMANDS.txt` 的第一条；实际 stdout/stderr 留在本目录。

`09b-a15-b1-ideation-p1-01/stage-b-approval.json` 的 `approved_by`、`approval_ref` 均为 null，供主控核对签字。binding 逐项取自 `09b-a15-stage-a-01/readiness.json`，不是旧场景副本：root 为 `/private/tmp/t078-2-09b-run-yp09xosq`，target attempt 为 `2ec554c4-092e-4c52-bb68-11888049b2ef`、fence 为 1。P1 launch 为 `298e0f0e-3f2c-4a76-89b5-4cd5a12053a0`，session 为 `be13441f-b3da-48aa-8ed4-d7f70dc3d04a`。

P1 的 `api_url` 保留动态模板 `http://127.0.0.1:0`；复用分支绑定本次 readiness 与 `roles/ideation/api-ready.json`。保存的 readiness 指向 API PID 59387、端口 64830。此次仅比较保存的文件，未核对进程当前存活身份；真实 B1 仍须执行完整 argv/lstart 核对。源码绑定 `dedd4f66bc424610183cbff2d7114e991483e1c6`，其后提交只保存本票证据；58 个 source 文件逐字节一致。

主控签字后，按 `09b-a15-b1-ideation-p1-01/B1-COMMANDS.txt` 分别运行两条完整命令：

1. 第一条 dry-run，预期 `READY_FOR_ROLE`、`spawned=false`，新输出 `09b-a15-b1-ideation-01-dry-run/`。
2. 读回 dry-run 后再决定运行第二条 real，输出 `09b-a15-b1-ideation-01/`；只启动 ideation，启动后停止，下一次读屏和每个键另行审批。

两条命令的 runner、materials、stage-a、approval 输入路径均存在，两个输出目录均尚不存在。此次没有替主控签字或执行这两条命令。B1 批准的 `screen_approvals` 与 runner 完全一致（包括 `security-notice` 和完整 `screen_text`）；后续实际 s7 按键批准使用 `onboarding-notice`。本次生成器也输出了后续阶段草稿，它们仍未签，不授权运行。

静态核对实际输出：

```json
{"status":"PASS","source_files":58,"b1_commands":2,"draft_unsigned":true,"dry_run":"NOT_RUN","real_b1":"NOT_RUN"}
```

`static-check.json` 是文件检查结果，不是启动或供应商模型调用的证据。预算保持 ideation 4 roots / 6 Messages、executor 6 / 11；本次生成不消耗回合。
