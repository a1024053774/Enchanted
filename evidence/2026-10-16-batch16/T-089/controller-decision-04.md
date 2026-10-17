# T-089 修复后沙箱外执行回执（2026-10-17）

来源：主控 #6。主控已执行 `controller_review_fix_01.sh`，rc 0。日志路径：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t089-fix-01.log`。

- `reclaim-external-green-01.json` 为 PASS，errors/skipped 为空，九个真实归档入口场景均按预期。
- `s3-main-02.json` 为 PASS，基线与候选实际调用 `run_s3_regression.main()`，没有用 rebased runner 或直接函数调用替代；两个调用处变异由独立 oracle 判 NO_GO。
- `t086-external-02.json` 为 PASS，10,064 文件、107,177,272 字节，归档 35 项，原仓库不变。
- 主控核对真实外盘 T-077 目录运行前后都不存在，没有写入该目录；运行结束没有残留进程。

worker 随后只读核对当前源码与外盘被测命令快照、实际 main 候选源码逐字节一致；读回回收失败的阶段与剩余原件、summary 中归档清单和实际归档字节，结果见 `repair-final-readback-01.json`。worker 的 T-077 检查仅是事后观察，事前状态和全局进程清点来源为主控回执。

按本条指示，修复与原文 reviewer 文件一起提交，九项尾注由既有 hook 自动追加；新候选的独立 reviewer 由主控另开，不用本轮 worker 自检代替。
