# #331 完整只读 reader 修复与 A-15 续行材料

本轮仅修测试 harness：run_t078_p1 的 snapshot、phase_driver 的许可截图、permission 的 Enter 前核对，共用 p1_output。业务输入、Stop/relay、protocol、预算、产品 src/app/bin 不改，A-15 的 daemon/API/角色未重启或被操作。

reader 固定起点 0 和首次 total，逐页校验 launch、连续 offset、解码字节数、范围与进度，最后再读 total 处的空页确认 EOF；total 变化、零进度、截断、缺页或错误范围立即拒绝，不重试。完整性由 capture 的所有页与文件字节数一起核对，不能靠 complete=true 单字段放行。正常截图、许可截图、Enter 前校验都经过同一实现。

## 证据范围

- P1 真实参数/screen 入口：旧代码对 90,137 和 155,701 字节流只读首个页，报原 screen_exceeds_review_limit；候选 6/6 通过，包括变化 total、零进度、截断和 EOF 时变化；只读一页的已知坏 reader 在同一入口被检出。
- permission 真实 CLI 的 check-only 入口：7/7，包括缺少完整 capture 的旧截断参考被拒；该模式在 build/窗口/按键前返回，不新增业务输入。
- phase execute 的真实许可截图分支：原代码保存 65,536/155,701 字节，候选完整保存 155,701 字节并留页范围。身份、事件和输出传输为隔离夹具，未声称启动真实 Claude。
- 恢复器 5/5：前缀、complete、launch/session 与已有输出反例均拒绝；删掉前缀校验的坏实现被同一检查检出。
- 冻结器 3/3：批准的只读差异通过；工作副本变化、把产品变化一起藏入新 archive 都被拒。三个旧调用的 AST 在批准的只读段落以外完全相同。

沙箱禁止 /bin/ps；本地入口检查的身份探测用 spy，其余分页逻辑未替换。输出传输使用确定性只读夹具，所有非读命令均拒绝。独立的真实 gate 现场恢复尚未运行，不能把这些夹具结果上调为 A-15 恢复 PASS。

主控可在沙箱外运行 OUTSIDE-RECHECK-COMMAND.txt：用自己前台 Python 的真实 ps 身份重跑 9 组隔离检查，负例同时核对具体错误/截断长度，不只看 exit=1。它不访问 A-15 root，不起 Claude/API/daemon/窗口，不发键；创建的 /tmp fixture 用完即删。当前该外侧复验 INCOMPLETE／未运行。

保留的准备期失败：permission-entry-green-01 使用了未被夹具替换的固定 node，因隔离 root 没有 operator.json 而失败；修正传输夹具后 green-02/03/04 通过。frozen-scope-green-01 是 /tmp 与 /private/tmp 的夹具路径差异，被已有校验拒绝，修正夹具后 -02/-03 通过。这些都不算产品红态。

## 新只读冻结与命令顺序

源码先由本 worker 提交，再运行 freeze-and-write-commands.py 的 check-only 与生成模式。新冻结位于 `../09b-a15-reader-harness-01/`，实际 harness revision 由 git rev-parse HEAD 读取；业务加载源码继续记录 dedd4f66bc424610183cbff2d7114e991483e1c6。原 58 文件中只允许三条 reader 改动，其余 55 文件逐字节相同；新 helper、恢复器、源校验入口与测试显式入包。所有新命令先验证该冻结，再执行既有 harness；P1 另显式传 --source-materials 指向新包，不放宽旧冻结检查、不修改旧 archive 或旧批准。

主控按 `../09b-a15-reader-harness-01/commands/` 顺序逐条运行，不整包批量执行：

1. E4-01-READ-02：新 -02 只读完整屏幕。
2. E4-02-RECOVER-REFERENCE：只读取原 dispatch/event 与新完整原件，核对旧参考是严格前缀；追加 screen-recovery-02 的完整独立参考、结果与恢复收据，并生成未签 permission-approval-02。旧 65,536 字节参考、screen -01 和未签 approval-01 均不改。所有 dispatch、seq、permission_event 原样保存，没有重新 dispatch。
3. E4-03-READ-03-CMP：另一次新 -03 完整读屏，与恢复目录里的独立完整参考逐字节 cmp。不是把文件与自己比较；不相同就停。
4. 主控读完整原件、核对实际 Bash command 和 ❯ 1. Yes 后，签新 approval-02。包内 template 只供预审；真实 approval-02 必须在步骤 2 验证后生成，不能提前补造完整原件。
5. E4-04-CHECK-ONLY 可在已签后只读核对；E4-05-ENTER 才经原 Electron 路径送一次 Enter；E4-06-READBACK 仅读回。只有 Enter 是输入动作，仍由主控另签执行。
6. E5-01-START 在主控签原 E5 phase approval 后才运行；许可截图已用完整 reader。E5-02-READ-01-CMP（备用 -02）完整读屏/cmp；E5-03 生成实际未签 permission；签后 E5-04 可只读核对，E5-05 一次 Enter，E5-06 collect。E5 参考自始完整，不沿用截断版本。
7. E6 的 START/READBACK 也给出显式新冻结命令，无工具、无 Enter；继续使用原阶段批准/真实反馈根，预算不变。

E4/E5 后的实际 POST 仍按真实请求计数，未获 SSE 的待批准 POST 也算；180 秒超时即整场 INCOMPLETE，不重试。本轮没有执行上述任何现场步骤。

## 历史审计与 issue 依据

HISTORICAL-SCREEN-AUDIT.md 如实列出 E1/E2/E3/I3 的完整 gate 样本；I1 没保存直接 total，只能报告 16,322 字节与 Electron offset 相同，直接完整性证明 INCOMPLETE，交主控判断旧 PASS。原结论文件一律不改。

blocking issue 20261016T113401Z 的范围阻塞已由 #331 裁定；可关闭依据是三处完整 reader、入口红绿/已知坏实现、追加式恢复和源冻结范围检查。本轮未代关该 issue，也不把“范围修复完成”写成“现场已恢复”。真实读屏/恢复/Enter 待主控执行。

另已非阻塞上报 20261016T120838Z：下一次标准场景 prepare 需要纳入新增 reader 源闭包。本次新包已显式包含，当前 A-15 不受影响；为满足“其余原包不变”，没有顺手改旧 prepare。

全新独立审查尚未运行，见 REVIEW-REQUEST.md；worker 的检查不替代独立 PASS。
