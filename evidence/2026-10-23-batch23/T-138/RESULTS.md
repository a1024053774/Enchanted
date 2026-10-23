# T-138-1 / a1：修复候选与 ASCII 驱动修正

状态：**INCOMPLETE**。RUN-OUTSIDE-02 已证明候选在两种模式下的四次“打出”均正确，但新增 ASCII 场景的驱动缺陷让整次测试中止。本轮只修测试驱动和取证；生产代码、ASCII 字节期望及原 IME 断言保持不变。完整绿态和有效红态/变异结论待 RUN-OUTSIDE-03。

## 身份与范围

- worker：b23-t138；task：T-138-1；attempt：a1；分支：exec/t138；任务卡 ready_rev 1。
- 起点：`b99f4869bbe087946017716a5a8479c0cb47e6c8`；上轮被测候选：`b3b6d520b38bf341f26bf06b97ca58066a57bb23`。
- 生产修复在 `eb4f6bad1`，仅涉及 `workbench/app/renderer.tsx` 的终端输入/composition：xterm 发出 onData 后，下一事件轮次清空隐藏输入框；组合中不清空，新组合开始与卸载时取消定时器。沿用原有 admitInput、IPC、PTY 路径，不改 xterm，不另发 compositionend.data，不关闭读屏模式。
- 本轮只改本任务新增的 `test_t138_ime_e2e.py` 和 T-138 证据。既有验收文件、后台、README、地图、ticket 均未改。

## 已有真实证据

`outside-01-20261023-131559-9292/red.json`：起点在读屏开启时，隐藏输入框选区 2..2，四次“打出”均收到“怪了”（预期 `e68993e587ba`，实际 `e680aae4ba86`）；默认模式正确。主控已确认原样执行脚本，没有修改或补发事件。compositionstart/update/input 可信，但 CDP 结束事件 isTrusted=false；原始标志保留。新版检查可信开始/更新/输入及实际结束事件，不伪造结束事件或可信标志。

`outside-02-20261023-132813-22749/`：

- green：两种模式各三次中间插入、回车后再次插入，“打出”的 PTY 字节全部正确，隐藏输入框清空。
- red、mutant：默认模式仍正确，读屏模式四次“打出”仍收到“怪了”。
- 三份均在读屏开启的 ascii-seed 中止：预期 PTY 为 prefix-tail，实际为空；textarea 却为 prefix-tail，选区 11..11。因此三份整体都是 INCOMPLETE，不能把中止当成有效拒绝反例。
- T-139/T-143 联合 e2e：PASS；t091：与起点同样的 IPC 名单断言失败，没有新增失败。
- T-145：native 就绪包超时。主控明确确认是 T-141 后旧 receiver 不发就绪包的夹具问题，由 T-148 修。本轮按主控要求不再运行、不计入 T-138 结果，明确标记 NOT_RUN，不称 PASS。

## 本轮根因与最小修正

修改前先写 `ASCII-ROOT-CAUSE-03.md`，逐项核对三份 JSON、三张已有截图和 xterm 源码。旧截图仅有默认模式，没有失败时读屏模式截图。

旧 type_ascii 只发送 CDP char，遗漏 keydown。读屏模式下，前一个 Enter 令 xterm 的 `_keyDownHandled=true`，keyup 不重置，只有下一次 keydown 才重置；后续 char 被 `_keyPress` 忽略，`_inputEvent` 又排除读屏模式。浏览器仍插入 textarea，PTY 却没有这次输入，renderer 也没有收到 onData 来安排清空。这是驱动没有模拟完整按键的缺陷，不能解释为清空定时器被读屏同步覆盖。

驱动改为每字发送带 text/unmodifiedText 的 keyDown，再发匹配 keyUp；不额外无条件发送 char，避免重复。保持 ascii-seed 精确收到 prefix-tail、随机新词、两种模式及全部原断言。事件观察补上 keypress/beforeinput、按键码和取消状态，使用 capture；增加 ASCII 可信 keydown/keyup 序列断言，失败场景立即截图并记录路径。

CDP 参数和调用方式已核对官方协议及 Puppeteer 官方实现，链接见根因记录；没有新增依赖。真实运行复验尚未进行。

## 检查与局限

- PASS：Python 语法、RUN-OUTSIDE-03 zsh 语法、嵌入 Python 语法、git diff 空白检查；输出见 `static-checks-03.txt`。
- 生产代码本轮未变；隔离构建见 `build-02.json`。t091 原比较见 `t091-comparison-03.json`，上轮沙箱外新比较也相同。没有把 t091 失败改称通过。
- 原始失败现场全部保留。沙箱首次 CDP 拒绝连接见 `sandbox-red-01.json`；t091 遗漏 VM 参数的配置失败见 `t091-*-02.*`，有效比较为 `t091-*-03.*`。
- 地图仍报 README stale，超出 worker 修改范围，已上报 `20261023T172307Z-worker:b23-t138-issue-001`；见当前 `project-map-status-04.txt`，需主控集成时处理。
- 先前辅助审查为 INCOMPLETE，见 `behavioral-review-02.md`；本轮没有复用该结果宣布候选通过。真实 macOS 输入法/读屏软件未测，CDP 场景不能代替这部分结论。

## 下一步

```sh
zsh evidence/2026-10-23-batch23/T-138/RUN-OUTSIDE-03.sh <本次交付的完整提交号>
```

脚本开始/结束核对传入提交与 HEAD、workbench 受控文件；每次建立新证据目录。依次运行起点红态、候选绿态、移除清空动作的 retain-input 变异、T-139/T-143、t091 基线/候选。红态/变异必须完成测试、通过事件检查且确实观察到读屏模式把“打出”变成“怪了”，不接受启动失败或 ASCII 断言中止作为有效反例。T-145 在汇总中单列排除原因和 T-148。

请回传 run-summary.json。截图不提交，夹具保留由主控归档。完整候选仍需主控正式独立审查与验收。
