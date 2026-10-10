# T-057 rev3 的探针现场与修正

旧文件不改不删。本轮命名包含 `rev3`。

- `notifications-rev3-red01`：不完整 desktopBridge 在应用初始化之前出现，浏览器上下文随后关闭；未取得可用结果文件，不算业务红态。
- `notifications-rev3-red02`：在应用主界面就绪、首批真实 issues 响应返回前安装通知接收端。首次既存 blocking 提醒期望 1 次、实际 0 次；close 的软件内通知缺失，均符合父修订的缺失能力。后半段浏览器关闭，原输出保留，后半段不计通过。
- `notifications-rev3-green01`：沿用红态夹具造成既存 waiting 从 3 个变为 4 个，启动计数预期不适用；其余七项通过。没有删除原数据来制造通过。
- `notifications-rev3-green02`：首次启动五项通过，后续浏览器关闭，保留失败。`green03` 使用新夹具，测试进程以 `start_new_session` 脱离调用者，八项全部通过。前后台与 bridge 接收端是控制输入，不能证明 macOS 显示。
- `notification-routes-rev3-01/02`：接收端缺少 `setTheme`，真实应用进入错误界面，通知组件被卸载；定时器输出与页面文字保留，不算产品通知缺陷。补上这个既有桥接方法后，`03` 又暴露接收端在初次 effect 后才出现、未触发前后台变化的夹具问题，既存提醒直到新条目到达才发送，计数预期错误。`04` 显式从前台切后台、确认既存提醒后再清空接收端记录，四项路由断言全部通过。没有为这些夹具故障修改产品代码。
- `panel-geometry-rev3-01`：Role 查询漏掉 content-visibility 跳过的屏幕外按钮，只有 8 张图。`02` 改为遍历每题 form 的 submit 按钮，先滚动再检验真实命中与边界，六个单题按钮加一个打包按钮，在两个尺寸共 14 张截图。

源代码只修改 `apps/web/src/a2a/IssueNotifications.tsx`。200 ms 合并窗口属于通知消费者；没有自动重试、内容含义判断、新设置字段或权限变更。问题状态、追加记录与用户动作权限仍归既有核心。

真实 Native 探针的失败同样保留：01 使用 Bearer-only 而非既有 CLI 的 query token + Bearer 方式，被正常鉴权拒绝；02 把 `/tmp` 别名当作 canonical workspace，被身份 guard 拒绝；03/04 的额外软件内断言被首次使用引导和读取时机混淆，未作为软件内业务失败；05/06 的前后台检查受到 Playwright 默认 `Emulation.setFocusEmulationEnabled=true` 影响。禁用自动焦点模拟后，07 取得真实 show 事件、macOS 通知中心记录和进程重启去重；其余设置断言因桌面使用 hash history 而失败。08 沿用 07 的隔离 profile，经 CUA 的已有 Settings→Notifications 入口关闭开关，读回 false，新 needs-user 零 IPC/原生调用，退出 0。所有 Native 窗口与 backend 已退出，未强杀、未打开系统设置、未点击系统授权。

`notifications-parent-rev3-02` 的长探针后半段浏览器关闭，因此另保留短探针 `startup-parent-rev3-03`：在相同真实入口、完整接收端下，由 Vite 前置 transform 仅加载 Git `e94a0efc` 的通知组件。真实主界面仍可见、不是错误页，三个 blocking 的首次观察期望一次，实际零次，取得确定的业务反事实。插件只改变测试服务器加载的这一模块，不修改任何 checkout 源码；去掉插件后同一输入用 `startup-green-rev3-03` 重放。
