# cleanup-recovery-154：修复 ps 日期语言混入 command

2026-10-14，主控 #155。**局部红绿 PASS；实际恢复清理 INCOMPLETE，worker 未执行。** 原 cleanup-recovery-153 的 BLOCKED、signals_sent=[] 和全部原字节保留。

原始 `ps` stdout 是：

```text
48954 三 10月/14 14:14:35 2026   /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_fake_messages.py /private/tmp/t078-2-p1-09a3r2-block-093154n0
```

脚本没有固定 ps 的语言；消费端按 C locale 的五个 lstart token 切列。中文日期只有四个 token，导致 Python 解释器路径被当成 started 的最后一段，传给 owns_api 的 command 只剩 `-B script root`。owns_api 的四段比较本身正确：主控提供的完整 command 与 api-owner argv 在原规则下匹配；失败来自 probe 的列错位，不是 PID/root 实际不符。

[局部红态](cleanup-probe-locale-red-154/results.json) 直接执行实际 probe 闭包，读原失败 row、主控给的完整 command 和 owner argv。完整文本匹配通过；producer 没有固定 C locale、command 丢解释器以及未拒绝非规范日期两项失败。修改后 [同探针 5/5 PASS](cleanup-probe-locale-green-154/results.json)。probe 的 ps 子进程显式 LC_ALL=C／LANG=C，消费端严格验证固定日期协议，非规范输出直接拒绝；不猜日期列、不加多语言 fallback，也不改 owns_api 的尾参数规则。一般 runner 的 probe_process 同样固定语言，避免启动记录与清理观察依赖会话 locale。

之前修复的“同 PID/lstart 下 comm 改变必须继续等实际退出” [5/5](cleanup-lifetime-locale-regression-154/results.json) 与原清理 [6/6](cleanup-original-locale-regression-154/results.json) 均保持 PASS。PID/lstart 改变仍拒绝；当前 locale 探针模拟 ps 的规范输出，不冒称在本机实际执行了 ps。

恢复脚本还是 [cleanup-block-recovery-09a3r2.py](cleanup-block-recovery-09a3r2.py)，改用新目录 `p1-materials-09a3r2-block/cleanup-recovery-154`，外置归档同名；不会覆盖旧结果。固定 PID 48954、脚本及根路径，第一次完整身份核对后，再读同 PID/lstart/command，只有完全相同才发送一次 SIGTERM。随后确认退出；不发送第二信号、不信号进程组或 CLI／壳／后台／Electron。原 PID 复用、命令／根错配与不明状态都保留根并 BLOCKED。归档及删除仍只针对 #153 已授权的本实例根，两 slot 不动。

主控在沙箱外执行：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078/cleanup-block-recovery-09a3r2.py --approval-ref '主控 #155'
```

真实模型、CLI／API／UI／后台启动均 0；未提权、未运行 main、未发送信号或执行归档／删除。09A 两场景读回、收尾提交及 09B/09C 计划仍在原 #153 工作范围内，等待这个实际资源收尾结果后继续；不把脚本 READY 写成实际 cleanup PASS。
