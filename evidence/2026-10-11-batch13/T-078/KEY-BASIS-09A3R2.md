# 09A-3R2：一次 Ctrl+C 的依据与验证边界

核对日期 2026-10-14。官方 [Interactive mode / General controls](https://code.claude.com/docs/en/interactive-mode) 的 Ctrl+C 项为 “Interrupt, or clear input”，并说明无操作运行时第一下清空输入、第二下退出；清空后的草稿还可从历史取回，相关恢复功能需 v2.1.288+。官方 [cheatsheet](https://support.claude.com/en/articles/14553413-claude-code-cheatsheet) 同样区分取消当前输入与空框时退出。当前夹具固定 v2.1.296，本轮没有运行 `--version` 或该 CLI；启动阶段仍须实际预检版本。

因此正例只在已取得 Esc 实际写入／退休收据、API1 peer 取消、当前窗格 held／active=null、独立编辑框可见恢复的第一 nonce 后，经该窗口的 xterm 键盘通路发送一次 Control+C，即 UTF-8 控制字节 0x03。后台不删文本，不调用隐藏输入接口。随后必须核对 action→准入→intent→written 与新的 PTY／窗口快照：两条横线包围的 `❯` 编辑区确实无非空白内容，且新 offset 已晚于清空前输出。截图、编辑区观察与同 highwater 的 PTY 字节都保存。

官方文档支持按键选择，不能替代此版本此状态的实测。一次未清空、退出、未知编辑区、残余行／占位提示、缺收据或输入代次改变时停止 INCOMPLETE。不发送第二次 Ctrl+C，不换 Ctrl+U／Ctrl+S／双 Esc，不自动重送。反例完全不发清空键，只保留草稿后执行特意不真实的声明。

所有动作均为 executor 逐项预批的 test-simulated-user，不是用户亲手操作。实际 CLI／PTY 行为将在新 launch 后验证；本轮只有局部契约证据，未启动 CLI／API／Electron／构建。
