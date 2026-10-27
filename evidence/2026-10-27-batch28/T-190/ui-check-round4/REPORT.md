# T-190 / T-191 第 4 轮 Computer Use 验收报告

总状态：INCOMPLETE。项目移除界面通过；普通终端的两个回合均未截到侧栏转圈，指定的 opencode 命令被当前 CLI 拒绝。

1. **PASS**：zeta 历史显示 T-5 的 Codex 图标与名称；T-6 显示 agy 图标与名称，T-7 显示 opencode 图标与名称。T-6、T-7 显示“空闲”，侧栏为静止勾号。截图：`01-zeta.png`、`02-lcu.png`。名称以无障碍树的完整标签核对，部分历史行在截图中被截断。
2. **PASS**：lcu 历史 T-2 的 Claude Code worker 显示 Claude 图标；完整无障碍标签为“worker T-2 · Claude Code 已结束”。截图：`02-lcu.png`。
3. **PASS**：新建普通终端后显示“普通终端 zsh 空闲”。截图：`03-zsh-ready.png`（`03-zsh.png` 为打开过程）。
4. **INCOMPLETE**：agy 启动后显示 agy 图标。出现 `Do you trust the contents of this project?`，对 `/private/tmp/t190/zeta` 选择了 `Yes, I trust this folder`；截图：`04-agy-start.png`、`04-agy-trust.png`。提交“只回复 ok 两个字母”后立即截图，终端显示 `Generating...`，侧栏仍是空闲勾号，**未截到转圈**；不能判定是否曾短暂转圈。回答 `ok` 后等待 8 秒，侧栏显示空闲。截图：`04-agy-working.png`、`04-agy-after.png`。随后 Ctrl+C 退出。
5. **FAIL / INCOMPLETE**：指定命令 `opencode -m opencode/glm-5.3-flash-free` 未启动，原文：`Unrecognized flag: -m in command opencode`；截图：`05-opencode-start.png`。补充运行 `opencode`，显示 opencode 图标，实际模型为 `DeepSeek V4.1 Flash Free`，并非指定模型；截图：`05-opencode-plain.png`。提交同一提示后立即截图，终端显示处理中及 `esc interrupt`，侧栏仍是空闲勾号，**未截到转圈**；不能判定是否曾短暂转圈。回答 `ok` 后等待 15 秒，侧栏空闲。截图：`05-opencode-working.png`、`05-opencode-after.png`。随后按 Ctrl+C 两次。
6. **PASS**：点击窗格的“关闭普通终端”后，终端窗格关闭。截图：`06-exit.png`、`06-close.png`。
7. **PASS**：zeta 右键菜单有“从列表移除”，直接出现移除对话框，未提示先关闭终端。截图：`07-menu.png`、`07-remove-prompt.png`。
8. **PASS**：对话框原文：“移除只是从列表隐藏，任务和记录都留着，重新打开这个目录就回来。下面的任务还有没回收的 attempt：”；列出 `T-6 submitted`、`T-7 submitted`，有“保留并移除”和“回收并移除”。已选择“回收并移除”。截图：`07-remove-prompt.png`、`08-reclaim.png`。
9. **PASS**：操作完成后 zeta 不在侧栏，未见错误提示。截图：`09-result.png`。此结论仅依据界面，未另行核验后台 attempt 状态。

项目地图 status：Problems 0，Stale living docs 0。仅操作 Enchanted Test；截图和本报告保存在本目录。
