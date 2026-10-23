# RUN-OUTSIDE-01 两项失败的根因与修复

状态：**INCOMPLETE**。现场来自执行主控提供的 `outside-20261023-062012-785427/`，对应交付 bffd3ca12。
原始夹具与日志保留；诊断读取没有启动 CLI、修改夹具或改写旧记录。抽取的事件与启动信息见 `diagnosis-outside-01.json`。

## 移除后的 Claude 仍能写 X

真实后台 SQLite 记录如下（green 夹具 `/private/tmp/t140-hvpnt4ns`）：

| seq | 事件 | 额外目录 |
| --- | --- | --- |
| 29 | 操作员 `project_settings_save` 请求 | `[X]` |
| 30 | `project_settings_saved` | `[X]` |
| 544 | 操作员第二次 `project_settings_save` 请求 | `[X]` |
| 545 | `project_settings_saved` | `[X]` |

第二次保存没有提交空列表。T-RC 的真实启动记录也仍带 `--add-dir X`，`allowWrite` 包含 X；因此写 X 成功符合收到的授权。
这份现场不能证明“已经保存空列表后权限仍残留”。

旧驱动在一次 `electron.evaluate()` 中连续执行移除按钮的 `.click()` 和保存按钮的 `.click()`。
移除调用 React `setSettings`，但 React 尚未提交下一次渲染，保存按钮仍运行旧渲染绑定的处理函数，提交的是 `[X]`。
根因是驱动把两个独立用户动作塞进同一浏览器 JavaScript 任务，跳过了两次点击间的界面状态更新。

修复只在测试：点击移除 → 等真实对话框中的目录行消失 → 另一次 CDP 调用点击保存。
保存后先断言追加事件为 `[[X], []]`，再启动新 worker；X/Y 的原有写入断言保持不变。
新 RUN-OUTSIDE-02 还会从 bffd3ca12 提取旧驱动，针对相同产品代码复现同回合点击红态；必须同时观察到两次保存 `[X]` 才认定是此根因。

## shell 变异没有在 shell 断言失败

`mutant-shell.json` 与真实启动记录表明：旧变异把 `allowWrite` 清空，但 worker 的 X 写入实际成功，之后在 reviewer 的 `review_launch_boundary` 才被拒绝。
因此旧变异不证明 shell 写入断言的敏感性。Claude 原生 `--add-dir` 与 Edit allow 都会给 shell 授予写入范围，单独清空一个授权来源不足以撤销授权。
这与 [Claude 官方 sandbox 文档](https://code.claude.com/docs/en/sandboxing#how-sandboxing-relates-to-permissions-and-permission-modes)的授权合并规则一致；判断依据同时包含当前 CLI 的真实运行结果。

替换为 `claude-shell-deny-extra`：只在 Claude worker 的 `filesystem.denyWrite` 里追加 X，保留文件工具授权、`--add-dir`、`allowWrite` 和 reviewer 配置。
这直接构造 shell 写边界错误，预期在首个 worker 的 `T-C_shell_boundary` 处以 `{'x': False, 'y': False}` 被拒绝。
测试即使提早失败也保存实际启动记录；RUN-OUTSIDE-02 必须同时看到 X 的 shell deny、实际写入结果及 0 个 reviewer 启动，才认可该变异。

首轮 `mutant-remove` 虽被旧脚本记为 PASS，但普通绿态也在同一断言失败，故不把它当作独立变异证明。
新脚本要求普通绿态先通过；移除变异还须先观察到真实保存事件 `[[X], []]`，然后才接受 T-RC 写 X 成功的反例。

## 验证边界

- 本地：驱动路由检查 `driver-green-02.json` 通过；Python、zsh 与内嵌 Python 语法、变异唯一定位、`git diff --check` 通过。
- 原生：尚未运行 RUN-OUTSIDE-02，两个根因的修复仍待同一真实入口确认，不宣称绿态。
- 本轮没有修改产品代码、验收文件或默认临时目录权限。执行主控已接收临时目录问题并交 T-141；本 worker 不扩展处理。
