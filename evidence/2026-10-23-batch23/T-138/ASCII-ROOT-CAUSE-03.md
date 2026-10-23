# RUN-OUTSIDE-02 的 ASCII 同处失败根因

状态：PASS（根因定位）；INCOMPLETE（修正后的真实入口复验待运行）。本记录先于本轮测试修改写入。

## 三份原始结果

目录：`outside-02-20261023-132813-22749/`，被测候选 `b3b6d520b38bf341f26bf06b97ca58066a57bb23`。

| 结果 | 读屏开启的 ascii-seed 预期 PTY | 实际 PTY | textarea 最终内容与选区 |
| --- | --- | --- | --- |
| red | prefix-tail | 空字节 | prefix-tail，11..11 |
| green | prefix-tail | 空字节 | prefix-tail，11..11 |
| mutant | prefix-tail | 空字节 | prefix-tail，11..11 |

这一步的断言比较的是 PTY 字节，并未要求 textarea 保留 prefix-tail。三份均在该断言中止，导致最终可信事件检查及读屏模式的新词场景未执行，不能把这些退出码当作有效红态/变异拒绝结论。

三份 JSON 的该步均有 11 个可信 input 事件；输入从 p 累积到 prefix-tail，没有新一轮 keydown/keyup，因为测试的 type_ascii 只发送 CDP type=char。旧观测没有记录 keypress，下轮补齐。

已有截图仅生成了 screen-reader-False 版本，三张都已查看；中止前没有生成 screen-reader-True 截图。这些截图显示正常的 raw receiver 和默认模式输入，只能辅助证明此前默认模式走通，不能作为失败时读屏模式的截图证据。下轮在断言失败时也保存截图。

## 根因链

依赖源码：`workbench/node_modules/@xterm/xterm/src/browser/CoreBrowserTerminal.ts`，只读核对，未修改。

1. `_keyDown` 第 1022 行才重置 `_keyDownHandled=false`。
2. 前一个 Enter 在读屏模式下发送数据后，第 1102 行把 `_keyDownHandled=true`；非读屏模式会在第 1098～1099 行取消事件并提前返回。
3. `_keyUp`（1119～1132 行）不重置 `_keyDownHandled`。
4. 测试后续只发 char，没有下一次 keydown。`_keyPress` 第 1145～1146 行因 `_keyDownHandled=true` 返回，不发送字符。
5. 浏览器原生插入仍产生 input、更新隐藏 textarea。`_inputEvent` 第 1196 行排除 screenReaderMode，因此不从 input 补发数据。
6. renderer 没收到这次字符的 onData，故不会安排 setTimeout 清空。这不是定时器执行后被读屏同步覆盖；三份实际 PTY 为空也不能支持这种解释。默认模式可从 keypress/input 发送，因此原驱动只在该模式凑巧工作。

同时，green 的两种模式中，四次“打出”的实际字节均正确、隐藏 textarea 都已清空；red/mutant 在读屏模式下仍把四次“打出”变成“怪了”。这说明原 IME 修复已在这些已执行场景中生效，但整次测试被新增 ASCII 驱动缺陷截断，尚无完整绿态。

## 本轮变更方向与不变的期望

修测试驱动，生产代码保持不动：用包含 text/unmodifiedText 的 CDP keyDown 让 Chromium 按是否取消默认动作处理字符，再发匹配 keyUp；不在 keyDown 后无条件另发 char，避免非读屏模式已处理 keyDown 后重复输入。

外部核对依据：[CDP 官方协议定义](https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/browser_protocol.json) 将 text 定义为按键布局生成的文本；[Puppeteer 官方 CdpKeyboard 实现](https://github.com/puppeteer/puppeteer/blob/main/packages/puppeteer-core/src/cdp/Input.ts) 的 down/press 同样在有文本时发送 keyDown 与 text/unmodifiedText，随后发送 keyUp。这里只复用相同的 CDP 调用方式，不新增依赖。

保留 ascii-seed 必须精确收到 prefix-tail、两种模式、中间随机新词、已知坏实现拒绝及原“打出”断言。增加 keypress/beforeinput 和 capture 事件观察，失败时截图；不改输入框值、不补发 IPC、不放宽期望。

T-139/T-143 已在该候选上 PASS；t091 与起点同样失败。主控明确确认 T-145 的 native 就绪包超时属于 T-148 旧夹具问题，下轮单独注明跳过，不作为 T-138 通过条件，也不把它改称 PASS。
