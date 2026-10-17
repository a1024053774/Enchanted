# controller 入口反馈时序诊断与续跑

主控 #182 的第一提交为 `455696c98e99b73a118886345ab1d83de24e0bdf`，九项尾注。原 [outside-01](controller-green-outside-01/result.json) **INCOMPLETE／exit1**：入口前四项 PASS，第五项在反馈 CR 断言失败，第六项及空框／runtime／input-failures／worker-inbox／实例生成均未运行。原件不改写，不重试旧目录。

## 只读定位与最小信号

[原数据库只读读回](controller-green-2-diagnosis/original-database-readback.json) 用保存的离线 SQLite 副本及 immutable=1，未打开存活库或改原行。seq29 为一次真实 scoped relay result（只有 IDEATION_SENTINEL），seq30 排队 gate 反馈，seq31 原 active 完成并 idle，seq32 Stop 请求成功；seq33～34 paste，seq37～38 登记及回车，seq39 daemon 停止。CR 最终存在，不能把夹具的早读说成产品未写出。

daemon.ts 的 signal 在连接 close 后调用 drain；这避免 Stop hook 等待下一轮派发形成死锁。Panes.drain 在 paste 后等待再登记根提交并写 CR。原入口夹具等 hook 子进程退出便断言 writes[2]，并在尚未写 CR 时进入清理。沙箱内已有 pane 单元显式 await drain，因此并未证明入口夹具也等到了完成。这是夹具等待缺陷，不是环境外行为差异或产品转交失败。

最小复现 [wait-red](controller-green-2-wait-red/results.json) **INCOMPLETE／exit1**：执行生产 drain，等 paste_written 后立即检查 CR，得到同样 undefined !== '\r'；最终 settle 的原字节表明稍后确有 CR。随后 [wait-green](controller-green-2-wait-green/results.json) **PASS**：相同生产代码／输入，改等当前 feedback dispatch 的 turn_submitted，保留 CR、busy、active.dispatch 和根 intent2 的断言。两者无 socket／CLI／后台服务，PTY 是 spy，不替新入口实跑。

## 最小修复与新阶段

本轮不改产品源码。入口夹具只补匹配 dispatch 的有期限等待，并核对 writing 已结束；等待前／后／超时保存原 events、active、state 与 writes。原六项身份、scope、去重、字节断言保留，额外核对反馈对应的 active。没有固定长 sleep 或自动重试，也没有调用 drain 代替真实 close 后派发路径。

README 所有权由 #182 分配，已同步 controller schema2／caller／许可 CR、异步反馈观察条件及实际验证边界，去掉 worker Stop 未完成与只支持单根探针等过期表述。README 仍明确真实 controller 绿态、09B/09C 和日常切换未完成。

按原身份执行 [commit-and-prepare-slice1-green-2.sh](commit-and-prepare-slice1-green-2.sh)：第一提交纳入本轮夹具修复、README、#182 原失败与局部红绿；冻结新 source。然后同一阶段脚本带明确 output/freeze，运行新 `controller-green-outside-02`：controller-entry6 全重跑（原入口未完整通过），之后空框17、runtime12、input-failures11、worker-inbox14。全部 PASS 才生成从未创建的 `p1-materials-slice1-green`，新 ID、绑定本次 source、静态核对并第二次材料提交。任何失败停止，不推进、不重试、不删现场；没有 launch。

当前局部时序修复 **PASS**；outside-02、新实例材料及实际 Claude 绿态 **INCOMPLETE**。代码提交后重新运行 project_map status，预期 README stale 清除；提交前 status 仍依据旧 README Git revision 标 stale，未改地图／Verified 字段。独立 reviewer、09B/09C、整票仍 INCOMPLETE。预算及逐屏／工具许可审批继续按 SLICE-1-GREEN，根2／Messages3／Bash1／模型0。
