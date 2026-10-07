# T-029 主控决定（2026-10-07）

## 1. server 退出：先查清，再恢复
主控只读核对：muster-server.log 最后一条为 04:31:35 的 persist.save，之后没有任何关闭、错误或 panic 记录；status 显示 `detached_server_daemon: false`。
推断（未证实）：server 作为 worker 某次工具调用的子进程运行，调用结束时整个进程组被回收（被 kill，而非引擎自身崩溃或正常退出）。
要求：
- 先用最小复现证实或否定这个推断：在独立会话中用同样方式启动 server，让启动它的命令结束，观察 server 是否随之消失；再用脱离父进程组的方式（例如 start_new_session / setsid，并把 stdio 重定向到证据文件）启动，确认它能独立存活。两次结果都存证。
- 若证实是启动方式问题：修正测试入口的启动方式，不改引擎；把它记为测试夹具缺陷，不算产品失败。
- 若 server 在独立存活的启动方式下仍会无日志退出：停下报告主控，这属于引擎缺陷，需要另开 ticket。

## 2. 目录信任：批准，但只在隔离 Codex home 中
不批准写入用户的 ~/.codex/config.toml。
批准：新建一个 /tmp 下、名称含 t029 的隔离 CODEX_HOME，只复制 auth.json（600 权限）；在该隔离 home 的 config.toml 中只为已核对的夹具根目录
`/private/tmp/t029-2uoclfw5/fixture`（或下一次重建时同样内容、同样核对过的夹具目录）设置项目信任；不安装任何 hook，不复制用户的 hooks.json。
副本不得进入证据或 Git；验收结束后删除整个隔离 home 并记录删除命令与结果。任何其他 trust、hook review 或权限对话不在许可内，再遇到须停下。
Codex 版本、模型参数与启动参数规则不变。

## 3. 恢复顺序
按 APPROVAL-REQUEST.md 的顺序执行：先确认原隔离会话与 pane 的真实状态 → 经 `coop.py reclaim --attempt 593b440eec864a42b853a0898c122679` 核对、撤销并回收（若引擎已不在，用权威记录核对后按既有规则处理，保留 attempt、状态、worktree 与证据）→ 用新 attempt、新输出目录、显式 submit 等待期限做下一次真实 run。不对原 attempt 重新投递。
