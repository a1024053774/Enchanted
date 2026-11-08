# T-257 第二次交付的实测与门禁停点

状态：INCOMPLETE。候选真实行为通过，门禁独立审查尚未开始。

候选为 5484315a5e318bce557dcc32e429f5d251453e84，生产代码提交为 a2d6dbcbbf4c4a43240f89273f1bafb05fc1234c；两者的 workbench 差异为空。生产变化只有 panes.ts 中 Codex 已认领 UserPromptSubmit 分支的 nativeTurn 绑定（1 行代码、3 行注释）。

主控在独立工作区 `/private/tmp/t257-controller-candidate-20261108-01` 跑原样测试，没有改实现或测试断言。仅将该工作区的 workbench/node_modules 链接到同仓库已经安装的依赖；不是构建输出目录，清理只移除链接本身。

- `green-a2-01.json`：真实后台、门禁、Codex 0.167.0、本地 scripted Responses；10 项竞态前提和 9 项业务检查通过，退出 0。结束恢复 idle、排队消息只发送一次、reclaim 成功；两个真实工作中阶段拒绝回收。夹具已清理。
- `red-a2-parent-01.json`：同一测试对 ebd155141668da18cb2dc09238c5312e1804223a，10 项前提成立，5 项目标行为失败，退出 1。没有因缺依赖或初始化失败判红。
- `regression-a2-t252-codex-01.json`：同候选工作区的既有 T-252 Codex 真实入口，7 项通过，退出 0；不可信请求拒绝、回合结束、问题记录、旧 attempt 回收与重派仍成立。脚本自行清理夹具。主控之后的删除检查遇到已不存在目录，退出 1；两份 cleanup 记录保留，不伪造删除成功。

可重跑命令（在上述候选工作区；每次换新的 summary 文件）：

```sh
ENCHANTED_HC_CACHE_DIR=/private/tmp/t257-hc-cache-20261108 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 workbench/tests/test_t257_codex_stop_continuation_e2e.py --summary <新路径>
ENCHANTED_HC_CACHE_DIR=/private/tmp/t257-hc-cache-20261108 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 workbench/tests/test_t257_codex_stop_continuation_e2e.py --revision ebd155141668da18cb2dc09238c5312e1804223a --summary <新路径>
ENCHANTED_HC_CACHE_DIR=/private/tmp/t257-hc-cache-20261108 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 workbench/tests/test_t252_untrusted_turn_other_cli_e2e.py --cli codex --summary <新路径>
```

第一次 verify 被 git_metadata_changed 拒绝：主控在派发后新增 keep/T-257-1-a2，违反共享引用保护。该新引用已撤回；原 worker 分支及门禁候选仍保留提交。这是主控准备错误，不是 worker 改了共享引用。第二次 verify 明确返回 repair_submission_required；没有继续调用或绕过。

正式后台仍是旧安装版本，worker 的 submit 回执又触发同 turn Stop 不匹配。原生 task_complete 已记录，pane busy，门禁退回队列未发送，见 worker-a2-stop-stalled.json。沿用本轮用户“批准重启并经门禁恢复（推荐）”的恢复授权，正常重启，再经 revise/reclaim/dispatch 处理；不改数据库、不手输旧会话、不把重启当作修复证明。

v3 只修订验收环境准备：门禁每个新 worktree 没有 node_modules；此前 preflight-t252-codex-outside-01.json 已记录缺 effect 的启动失败。完成与红态命令先接入本仓库现有依赖，退出时只 unlink 本命令创建的链接。产品、冻结验收和业务断言不变。新 worker 从本候选导入卡内差异，以新身份提交；继续 astra xhigh 普通速度，不启动 Claude。独立 reviewer 经新一次 verify 启动，期间不改变共享引用。

README stale 问题 0d0b44c6-3d69-450a-a893-cbad898a085a 属实：集成后由主控核对文档与地图 Verified。当前没有合入、发布或把业务实测当成整体验收 PASS。
