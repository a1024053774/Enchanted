# 09B 阶段 A 卡片 preflight 与 #195 cleanup

#195 的原始 `09b-stage-a-03/result.json` 保留为红态：daemon/fake API 已 spawn，随后 card_save 因 `paths.deny=oracle/**` 被 `invalid_task_card` 拒绝；未 dispatch、未 target、未 Claude CLI。原 root/PID cleanup 不覆盖该结果。

runner 现先构造同一 deterministic card，并经真实 `taskCards.validateTaskCard` 入口校验；`paths.deny=[]`，oracle 保护由 `oracle_paths=['oracle/contract-09b.json']` 负责。校验失败时不会创建 root、编译 receiver、启动 fake API/daemon 或创建 target；合法 card 与 wildcard deny 反例均见 [runner card preflight](09b-card-preflight-runner-06/results.json)，spawned=false、root_created=false。

交 [#195 固定 cleanup](cleanup-09b-stage-a-03.py)：只绑定 root `/private/tmp/t078-2-09b-run-576xn98k`、API62217/62218、daemon62220，先核对 stage result、ready PID、argv/root/lstart，并对每个 API 做第二次 lstart 读回；daemon 经认证 daemon_stop，API 各最多一次 SIGTERM。先以 `--dry-run` 输出全量身份核对和计划动作，不发信号、不停 daemon、不归档、不删根；正式运行逐个普通文件比对归档字节，目录核对类型、符号链接核对类型与目标，全部通过后才删除 root。任何命令/root/PID 不符或归档核对失败即 BLOCKED 不动，slot 不处理。脚本未执行。

新的提交脚本会冻结 cleanup、card preflight、runner 修复，并生成 `09b-executable-materials-04`；静态包仍 launch NO_GO。阶段 A 需重新签 approval 后才可运行；本轮没有发信号、没有启动服务或目标。

#197/#198 的正式 cleanup 在 62217 SIGTERM 死锁处 BLOCKED，root 保留；`cleanup-09b-stage-a-03-recovery.py` 使用单独 dry-run/正式输出，按批准各发一次 SIGKILL，归档逐成员读回后才删 root。假 API 已以独立真实进程取得当前停止路径超时红态，再取得 `SystemExit` 修复后的两秒内退出绿态。
