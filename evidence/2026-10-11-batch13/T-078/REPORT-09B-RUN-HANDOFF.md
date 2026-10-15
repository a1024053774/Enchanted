# T-078 #190：阶段 A runner 与待批材料

已写 [stage-gated runner](run-09b.py)：没有 stage-A approval 时在创建 root 前退出，不 spawn。批准后 A 阶段才创建全新 root，脱离调用者进程组启动两个 loopback fake API 和 daemon，编译确定性 target receiver，经 gate CLI card_save/create/dispatch 取得实际 attempt/session/fence/thread/workspace，再读 pane_process_info，写 `readiness.json` 并停止等待主控批准；不启动 role Claude CLI，不进入 B。

精确命令、审批字段、预计进程／RSS 和 cleanup 计划见 [09B-RUN-PLAN.md](09B-RUN-PLAN.md)。A 阶段预计 daemon 1、fake API 2、deterministic receiver+shell 1 组；runner 退出后只保留 owner manifest/readiness，实际 RSS 从 ps 读回。cleanup 只认证 daemon_stop，核对 API/target PID/lstart/argv，归档读回后删 root，slot 另列。

请以原身份运行：

```sh
sh /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/commit-09b-run.sh
```

脚本首提交冻结 runner、fake API、阶段计划与 runner 证据；随后生成新的 `09b-executable-materials-02`，绑定当前 source，逐文件 Git/tar 读回，target card 含 oracle_paths，approval 字段为空、launch NO_GO。脚本不执行 runner，不启动任何真实 CLI/API/目标。阶段 B 及逐角色屏幕／工具批准在 A readiness 审阅后另行继续。

T-078 09B-RUN READY
