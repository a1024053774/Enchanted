# 09B 分阶段真实入口 runner（阶段 A 待批准）

本 runner 默认不 spawn。只有阶段 A 的 executor approval 文件同时满足 `approved_by=executor`、`stage=A`、`source_revision` 等于静态 launch 包、`allow_role_cli_spawn=false` 且有 approval_ref 时，才会创建 root、启动假 API／daemon、执行门禁 setup 和确定性 target dispatch。缺 approval、旧包、伪造或空 claim 均在 spawn 前拒绝并写 INCOMPLETE。

## 阶段 A 精确命令

主控在审阅并填写新 approval 后才运行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/run-09b.py \
  --materials /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-executable-materials-02 \
  --stage A \
  --approval /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/stage-a-approval.json \
  --output /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/09b-stage-a-01
```

runner 的启动顺序：创建新的 `/private/tmp/t078-2-09b-run-*` root、broker/state/repo/oracle 和 target 目录；编译已有确定性 C receiver；以 `start_new_session=True` 启动 ideation/executor 两个 loopback fake API；通过 gate CLI `daemon_start` 启动脱离调用者进程组的 daemon；用 operator 仅做 card_save/create/dispatch 的后台脚手架；`dispatch` 返回实际 attempt/session/fence/thread/workspace 后再读 `pane_process_info` 核对 shell/leader/native 身份。dispatch 是本门禁的 claim 路径，runner 同时读 status 当前 attempt，绝不构造或写入 attempt 字段。

阶段 A approval 从 [template](stage-a-approval-template.json) 复制并由主控填写；`allow_role_cli_spawn=false` 固定不变。runner 先核对材料 source revision、approval 引用和空 claim 规则，全部通过后才允许上述 spawn。

结果保存 `readiness.json` 后停止在 `READY_FOR_APPROVAL`；阶段 B/C 不从此脚本自动继续。阶段 A 不启动任何 Claude CLI、供应商 API、controller role、tool permission 或 ack。假 API只提供 `/health` 和拒绝业务 Messages 的 409 响应，保留请求字节，模型0。

## 预计进程与内存

| 进程 | 预计数量 | 预计 RSS | 说明 |
| --- | ---: | ---: | --- |
| runner Python | 1（退出后0） | 15–30 MB | 只负责 gate CLI 与 readiness |
| daemon Node | 1 | 45–90 MB | detached，state/control.sock/daemon.pid |
| fake API Python | 2 | 每个 10–25 MB | loopback、无模型、无转发 |
| deterministic receiver + shell | 1 组 | 5–20 MB | target claim 后产生；保存原始 PTY 字节 |

readiness 同时记录 `ps -o pid,ppid,pgid,rss,lstart,command` 的实际读回；预计合计约 80–190 MB，实际读回优先于估计。阶段 A 在本机内存约束下不启动 role CLI，阶段 B 每次只启动一个角色并在每步审批后停止。

## 阶段 B/C 门槛与 cleanup

阶段 B 使用同一 root 的 runtime binding，但每个 role 读取自己 approval、`roles/<preset>/role.md`、独立 HOME/config/tmp/shell/requests/hooks/user-data/debug；先逐屏 theme/notice/trust/readiness，再一次性工具 Yes，I1/I2/E1… 每个阶段单独 approval。缺少实际 UPS/Stop、PermissionRequest、dispatch.seq、request_id 或登记正文就停，不接受 queued 代替执行收据。

cleanup 只接受本 runner 的 root/daemon/API/target owner manifest：先用认证 daemon_stop，确认 target shell/receiver 和两 fake API 的 pid/lstart/argv 未复用；API 各最多一次 SIGTERM，确认退出后逐成员归档、字节读回，再删除 root。任何 PID 复用、命令/root 不符、daemon 状态未知或归档缺盘均 BLOCKED；slot 另列，不由本脚本删除。阶段 B/C 未批准前不执行 cleanup 或任何信号。

当前阶段 A runner、stage-B proposal 和 cleanup 计划仅供审阅；不把 readiness 生成当成真实角色验收，09B/09C 与独立 reviewer 仍 INCOMPLETE。
