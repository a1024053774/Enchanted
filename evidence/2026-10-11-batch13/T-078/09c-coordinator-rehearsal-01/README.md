# 主控 #359：协调器真实链排练入口

状态：**静态预检／辅助路径红绿 PASS；完整协调器真实链实跑 INCOMPLETE，待主控沙箱外执行**。没有用旧排练的PASS替新协调器背书。本轮没有起daemon/API、PTY、角色CLI或Electron，没有发键或调模型；只写入口与做不启动现场的检查。

[沙箱外完整命令](RUN-OUTSIDE-COMMAND.txt) 使用全新 `real-chain-outside-01`。它不复用第1场或前面三次排练的root、PID、claim、角色launch或session。真实场景只用本次新scratch与唯一build slot，供应商CLI0、模型0。

## 新入口如何复用真实路径

`test_t078_09c_coordinator_chain.CoordinatorScene` 复用原CScene的真实daemon／受管目标dispatch/claim／角色PTY seam／API／所有权绑定与cleanup；原入口保留。只把源快照制作与最终只读oracle抽成可复用方法，原入口的操作顺序、条件式时钟与结束判据不变。

新入口把协调器接进已有的 **Tracer bullet**，只替换原排练里的阶段编排：

1. 两个确定性PTY peer通过真实controller_start启动，实际API为phase_plan HTTP。供应商CLI不启动。原host的进程识别seam仍按实际PID/完整argv/lstart核对，不伪造Claude进程或用户动作。
2. packet冻结实际常规文件及source_paths，逐字节读回；不含目录条目、依赖缓存或假源码。协调器仍运行自己的完整source-closure检查，没有mock Timed.check_policy/execute/early/late/observe。
3. 根据真实peer的两次 `ps pid/lstart/comm` 与门禁pane_process_info生成P1所需的实际manifest/launch-binding；声明是peer，不是Claude。完整argv所有权仍由原REHEARSAL owner独立核对。
4. 五阶段按明确排练签名批准/ARM，initialize初始release一次，start只派发C-I1。只读等到真实PermissionRequest，保存完整许可框，并生成本次C-I1许可。此时尚未Enter。
5. 用真实独立CLI调用 **t078_09c_timed_run.py**。`--signature-ref` 直接沿用外层主控给定的文本，预批准policy保存相同值，并明确含 `REHEARSAL ONLY`。协调器执行C-I1 check/一次Enter，再独自执行C-I2 observe／完整P1读屏cmp／模板核对签字／check／实际Electron单Enter／实际Stop结算，C-I3 observe/cmp／后台条件式driver／核对签草稿／原子发布／真实等待，最后C-I4与C-E1 collect。
6. 父进程不替协调器写成功relay、发送工具结果或补发业务输入。阶段Bash由peer实际执行，UPS/PermissionRequest/Stop都经真实signal CLI；Stop/relay/inbox/中断均由产品路径产生。

## 独立于协调器PASS的读回

新入口沿用原排练的HTTP/SQLite/目标字节oracle，要求：

- 实际POST ideation **7**、executor **1**，各请求meta/wire完整且HTTP200，逐阶段为2/2/2/1与1；roots **4/1**。
- 原stop始终同一created_at/request/entry，无ack；C-I2真实 `stop_too_early` 且目标零增量；C-I3实际daemon中断actor ideation、thread/stop为原对象，事件年龄 **>120000且<150000ms**。
- C-I3 Enter wall>120000、mono≥120100；父进程独立monotonic观察>120秒，场景与包含末尾拒绝探针的总观察都<150秒；目标相对真实baseline恰一个 **1b**，仍是原attempt和活目标。
- 实际PermissionRequest与Enter控制字节intent各3次，不增提示提交意图。

只在完整协调器第一次PASS且上述oracle通过后，做一次**重复入口拒绝探针**：同argv/同输出目录必须在独占mkdir处exit1/FileExistsError；对协调器与全部phase输出逐文件比较原字节，门禁事件/POST/按键增量均0。它不是第二次业务执行，也不是重试失败阶段；报告分别记录complete execution=1、refused invocation=1。旧result绝不覆盖。

## 结束与故障

完整输出有traceback、真实coordinator stdout/stderr、独立flow-readback、拒绝探针字节核对、HTTP/hook/peer与SQLite一致备份。420秒外层硬超时，协调器进程最多等待180秒（含C-I1 Enter前的准备）；原stop的150秒限制不变。

成败均沿用停前SQLite backup（包含WAL，integrity检查）、保留clock-origin原字节、HTTP/hook/peer原件，再认证daemon_stop、原API各一次SIGTERM、确认退出后删自有scratch与专属worker请求目录；停机后活SQLite读0，build slot另留。父进程只可中断自己启动的协调器harness以执行finally，不能向角色/目标直接发信号；若内部窗口/driver关闭未核对，root保留并报INCOMPLETE，不猜清理成功。

首次失败立即停并保留原目录，不覆盖或复跑；只有实跑result PASS、POST7/1、单Esc、无ack、重复拒绝与cleanup PASS都存在，才满足本次完整排练要求。当前只有 [preflight-02](preflight-02/preflight.json) 与 [307个常规源码成员／字节／命令路径检查](static-source-02/result.json)，不能写完整PASS。静态归档仅为当前工作候选的文件检查，实跑会重新冻结提交后的HEAD。

## 本轮修复与范围

协调器曾按packet.parent找两个辅助脚本，在排练的临时packet下路径必不存在。通过实际方法调用边界的 [旧Git源码红态](helper-path-red-01/result.json) 已复现两项不存在；统一改为仓库TICKET规范路径（没有fallback），[同一入口绿态](helper-path-green-01/result.json) 两项通过。该局部探针明确替换后续业务transport，零进程/按键，不冒称真实链通过。

产品workbench/src、app、acceptance不变。新协调器和base测试入口的源码闭包有变化，因此 **09c-executable-materials-03现已过期／NO_GO**；不改写其原快照，须本次协调器排练PASS后再重冻第2场并绑定新收据，之后才可签Stage A。
