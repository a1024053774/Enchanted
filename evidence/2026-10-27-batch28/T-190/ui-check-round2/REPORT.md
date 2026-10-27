# T-190 / T-191 界面实操验收报告

总结果：INCOMPLETE。项目移除和恢复的指定场景通过；opencode 的完整名称在当前侧栏宽度下被截断，且本次未验证回合状态变化。

验收对象：Enchanted Test（org.a2a.workbench.test），隔离项目 beta、epsilon、gamma。按说明先在 epsilon 新建普通终端。

1. **PASS** — gamma 显示“目录不存在”；epsilon 普通终端为 zsh、空闲，状态图标为静止的勾号。依据：01.png。
2. **PASS** — 移除 epsilon 时提示还有 1 个运行中的终端，需要先关闭；底部只有“取消”，另有关闭对话框的按钮。已点取消。依据：02.png。
3. **PASS** — beta 对话框列出 T-1、claimed，以及“取消 / 保留并移除 / 回收并移除”；选择“保留并移除”后 beta 从侧栏消失。依据：03a.png、03b.png。
4. **PASS** — gamma 的对话框列出 T-1、claimed；选择“保留并移除”后 gamma 从侧栏消失。依据：04a.png、04b.png。
5. **PASS** — 通过项目选择器重新打开 /private/tmp/t190/beta 后，beta 回到侧栏，任务格仍显示 T-1、已认领。依据：05.png。
6. **FAIL** — 输入 opencode 并等待 10 秒后，终端进入 opencode，侧栏出现图标，辅助功能树将 CLI 名称标为 opencode、状态标为空闲；但当前窗口宽度下侧栏可见名称截断为“op...”，未完整显示 opencode。按 Ctrl+C 两次并等待 10 秒后，图标消失，辅助功能树和侧栏显示 zsh、空闲。未发起 opencode 回合，故未验证运行中与空闲的状态跟随变化；不把这一部分视为通过。依据：06a.png、06b.png。
7. **PASS** — 已分别截取浅色和深色侧栏。依据：07a-light.png、07b-dark.png。

未遇到登录、系统授权或付款弹窗。截图只反映本次隔离测试界面，不证明其他场景或完整发布验收。
