# T-191 第 3 轮：只复验第 6 项（Computer Use）

只操作应用 **Enchanted Test**（bundle id `org.a2a.workbench.test`）。不要操作用户自己的 Enchanted（`org.a2a.workbench`）或其他应用；不改文件，截图和报告只写进 `/private/tmp/t190/ui-check3/`。遇到登录、系统授权、付款就停下报告。

上一轮的问题：普通终端运行 opencode 时，侧栏副标题被截成“op…”。已改为终端行副标题只显示 CLI 名。

步骤（每步截图，文件名带编号）：
1. 点侧栏 epsilon 下的普通终端（若已结束，先选 epsilon 再点“新建终端”）。截图：侧栏这一行应是 zsh、静止的空闲图标。
2. 在终端里输入 `opencode` 回车，等 10 秒。截图：这一行应显示 opencode 图标和完整的“opencode”字样，不截断。
3. 在 opencode 的输入框里输入 `只回复 ok 两个字母` 回车，**立刻**截图（1～2 秒内）：侧栏状态应为运行中（转圈）；再等它回答完、过 5 秒截图：应回到空闲（勾）。
4. 切到深色外观（窗口左上角太阳图标或系统设置都不要改；若应用内没有切换入口就跳过并写明），截图看 opencode 图标是否清楚可见。
5. 在终端里按 Ctrl+C 两次退出 opencode，等 10 秒截图：图标消失，回到 zsh、空闲。

报告写到 `/private/tmp/t190/ui-check3/REPORT.md`：每步 PASS / FAIL / BLOCKED 加截图依据；第 3 步若状态变化太快没截到，写“未截到”，不要写 PASS。最后一条回复给出同样结论。
