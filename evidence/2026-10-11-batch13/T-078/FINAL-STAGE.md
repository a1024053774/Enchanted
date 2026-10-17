# T-078-1 变基后最终验收阶段

本阶段已由主控执行，exit 0、checkpoint_status=PASS，原件见 `outside-final-01/`；整票仍为 **INCOMPLETE**。执行依据为主控 #68；固定候选 `b3fb998cf48574821c39440ece3f9ff897f26cf9`，父提交 `532c51f4cc12352bb7cf545ce1e5f824d68bdc4a`。尾注已读回，仍是 worker 原会话。T-076-1 的身份与停机改动已合入，T-077 尚未合入该 main。下文保留本次运行方案；再次运行须用新 label 并满足候选校验，不覆盖本次结果。

执行一次：

```sh
bash /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/outside-sandbox.sh outside-final-01
```

脚本先核对提交、父提交、分支、干净的 workbench、main 祖先关系、原三组业务断言与尾注、外置盘挂载及新证据目录，然后调用候选中已有的 `run_t078_stage2.py --final`。本轮不改 workbench 源码或断言，不重新安装依赖，不恢复或转交会话身份变量。

按以下顺序逐组运行；每个完整组只跑一次，三个原业务变异体只跑其对应的单个测试：

| 组 | 预期证据 |
| --- | --- |
| 收件箱领域逻辑 | 11/11 PASS：只追加、权限、就绪查询、stop/ack 与受控时钟下两分钟条件 |
| 管理 CLI 库客户端 | 8/8 PASS：实际 send/list/ack/ready 入口及参数伪造反例 |
| 窗格状态 | 11/11 PASS：排队、提交顺序、Esc 后放行、重复 Stop／唤醒、unknown 恢复、记录器失败、启动记录迁移 |
| Claude 启动静态骨架 | 2/2 PASS：构造并记录 argv/settings/角色卡，非法配置不留记录；不启动 Claude |
| 窗口与运行时入口 | 12/12 PASS：后台写入 PTY、用户输入及介入、注入区分、唤醒、放行、停止、关闭时长文本写入 |
| 输入失败方式入口 | 11/11 PASS：组合输入占用、请求号复用、二进制输入、关闭凭据、记录失败、重启 |
| worker 收件箱真实入口 | 14/14 PASS：使用 worker 会话身份，包含允许行为及对应规则拒绝 |
| 四个权限变异体 | assign／ready／foreign-ack／revoked 各只让对应检查失败，并实际观察到禁止的读取或写入结果 |
| 原 coop／recovery／run | 分别 8/9/18，failures/errors/skipped 均为 0；原断言不改 |
| CAS | 1/1 PASS |
| 三个原业务变异体 | fence／CAS／lock 的指定原断言拒绝各自单处坏实现，不能以设置错误或崩溃算反例 |
| 证据归档 | >5 MiB 的本轮原始单文件移到外置盘，逐字节读回后保留摘要、重放命令和外置路径 |

前端只构建一次，后续入口及权限变异体复用同一构建；每个后台夹具仍独立。命令、stdout/stderr、源码快照、库读回、PTY 字节、截图和变异评判分别保存在 `outside-final-01/`。原回归仍经实际后台 CLI／隔离受控线程入口；输入入口用确定性原生字节接收器，均不消耗模型。

任何非预期退出或反例不成立即停止，不自动重跑，保留结果交主控判定。`checkpoint_status=PASS` 只代表本卡非 Claude 检查点通过；整票仍为 INCOMPLETE。真实 Claude、主控凭据及 hook 接线、主控互相唤醒和三窗格验收继续等待 needs-decision `20261011T101958Z`，待真实 Claude 复核；系统输入法也不以合成组合事件冒充实测。

阶段通过并读回后，已完成一次新上下文只读独立审查；报告见 `independent-review-01.md`，非 Claude 范围局部 PASS，未确认需要修复的问题。
