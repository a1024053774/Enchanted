# T-109 / a1：应用未激活时的键盘驱动修复

状态 **INCOMPLETE**。第二次提交为 `a88604853e266649b72aad9401b6390961d866c6`。真实入口第二轮仍在发送 Enter 前失败；本次保留拒绝检查，只修测试应用的激活顺序，尚未运行第三轮真实 Electron。

## 实际焦点事实

`outside-02.json` 对应现场 `/private/tmp/t109-real-i5xsd6vn`。`green/driver.ndjson` 的 id 11 记录：

```json
{
  "target": "90d5264c-041e-4d99-ba88-280deaba98fc",
  "focus": {
    "target": "90d5264c-041e-4d99-ba88-280deaba98fc",
    "documentFocused": false,
    "expanded": false,
    "windowFocused": false,
    "contentsFocused": false
  }
}
```

`document.activeElement` 已是目标折叠按钮，表明这次 DOM focus 成功。失败的直接条件是原生窗口、页面及 webContents 都没有键盘焦点，而不是目标按钮拒绝 DOM focus。尚未完成真实 Tab 遍历或 Enter 激活，不能据此宣布完整键盘可访问性通过。

上轮驱动合同把 `window.focus()` 模拟为无条件成功，漏掉“应用仍在后台”的实际情况。此次先用第二轮真实记录建立该反例：只有应用已激活时，模拟窗口才允许获得原生焦点；修前 `a88604853` 的实际驱动分支被该反例拒绝。

## 最小修复与证据

Electron 43.4.1 的本地类型声明提供 `app.focus({steal:true})`。官方文档说明该选项可在 macOS 上将应用设为活动应用；`BrowserWindow.focus()` 是窗口层操作。[app.focus](https://www.electronjs.org/docs/latest/api/app/#appfocusoptions)、[BrowserWindow.focus](https://www.electronjs.org/docs/latest/api/browser-window/#winfocus)

驱动在键盘步骤中只激活它自己启动的测试应用一次，调用窗口 focus，并等待该窗口的 `focus` 事件；3 秒没有获得焦点则记录原生状态并失败，不重试、不发按键。随后再定位 DOM 按钮，核对目标 launch、document、窗口、webContents 与非负 tabIndex，再发原有 Enter down → CR char → Enter up。

产品代码未修改；没有给按钮强行改 tabIndex，没有把键盘操作换成 click，没有删除“worker 展开后必须可见”或任何焦点拒绝断言。新增 tabIndex 检查将继续拒绝不在正常 Tab 顺序内的按钮。

[keyboard-proof-03.json](keyboard-proof-03.json) 保存本地合同结果：候选通过；旧 `a88604853`、删除应用激活、删除 CR char、删除焦点拒绝的变异均失败。应用无法激活、窗口未聚焦、页面未聚焦、webContents 未聚焦、目标错误和负 tabIndex 时均不发送输入。这只证明驱动合同，不替代真实 macOS 激活与产品键盘效果。

## 第三轮命令

1. 运行 [RUN-OUTSIDE-COMMIT-03.sh](RUN-OUTSIDE-COMMIT-03.sh)。要求 `exec/t109` 当前 HEAD 为 `a88604853` 且没有其他已暂存改动，沿用本 worker 启动绑定和自动尾注钩子提交。
2. 运行 [RUN-OUTSIDE-03.sh](RUN-OUTSIDE-03.sh)。仍跑完整原场景，输出 `outside-03.json`；前两轮 JSON 和现场不覆盖。真实激活成功后若产品仍不能键盘展开，原断言会继续失败，届时按产品问题处理。

本轮 project-map status 仍为稀疏 checkout 的原 8 条缺失链接、0 stale living doc，未修改地图、票据或产品。第三轮真实入口与最终独立审查均待执行主控完成。
