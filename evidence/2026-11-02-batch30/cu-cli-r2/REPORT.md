# 项目终端三家 CLI 复测报告

**结论：PASS** — 本轮在指定打包应用的隔离项目终端中，三家均对测试消息回复“测试正常。”；这是一次功能复测，不代表长期可靠性或对 T-239 全部行为的验收。

## 环境与方法

- 2026-11-03，Computer Use 操作实际应用窗口；包路径为 `/private/tmp/a2a-build-t239-20261102/Enchanted.app`，项目为新建 Git 仓库 `/private/tmp/a2a-cli2/project`。
- 启动命令：`open -n /private/tmp/a2a-build-t239-20261102/Enchanted.app --args --state /private/tmp/a2a-cli2/state --user-data /private/tmp/a2a-cli2/ui`。启动后 `ps` 核实后台使用指定的隔离 state；界面项目列表仅显示该隔离项目。
- 每家分别新建项目终端，输入“请回复：测试正常。不要操作文件。”；期望收到“测试正常。”，不要求操作文件。截图反映界面结果，不独立证明 CLI 没有对文件执行任何操作。

## 结果

| CLI | 步骤与观察 | 结论与证据 |
| --- | --- | --- |
| Claude Code 2.1.317 | 运行 `claude --model claude-haiku-5-5`，确认隔离目录信任后提交消息；回复“测试正常。”，界面显示处理约 5 秒。Ctrl-C 两次后回到 shell。 | PASS；`shots/claude.png` |
| Codex 0.164.0 | 运行 `codex -c check_for_update_on_startup=false`，确认隔离目录及四个钩子信任；回复“测试正常。”，界面显示处理约 26 秒。Ctrl-C 两次后回到 shell。 | PASS；`shots/codex.png` |
| Antigravity CLI 1.4.12 | 运行 `agy --dangerously-skip-permissions`，确认隔离目录信任；界面显示 Gemini 3.8 Flash high，回复“测试正常。”；提交后约 22 秒时观察到回复，实际完成时间可能更短。Ctrl-C 两次后回到 shell。 | PASS；`shots/agy-reply.png` 仅截取消息和回复，不含账号邮箱。 |

Codex 首次启动到目录信任提示时，发现其默认使用用户配置，未确认信任即退出；随后使用 `/private/tmp/a2a-cli2/codex-home`，仅复制认证文件并复现 `git add`、`git commit` 两条 allow 规则后重新启动。四个钩子的信任在该隔离会话中确认。测试结束后已删除隔离 Codex home；未手工写入用户 CLI 配置。Claude 与 agy 的目录信任由各自 CLI 处理，可能写入其自身配置；未逐文件核验。未出现需要处理的 macOS 系统权限框。

截图 `shots/agy.png` 是首次裁剪范围偏移的记录，不作为回复证据；保留以免丢失异常结果。三家均已回复，未触发无回复时的 `sample` 和 `time cat` 对照，也未重试。

## 收尾

通过应用菜单退出窗口；后台 PID 43128、私有 core PID 43130 和该 core 的 holder PID 43439 在核对其命令行属于指定测试包后结束。随后执行 `ps axww -o pid,ppid,command` 并筛查包路径、隔离路径及本次 CLI 启动命令，未见匹配进程。未操作其他 hc、Herdr 或 `/Applications/Enchanted.app`。保留 `/private/tmp/a2a-cli2/` 测试项目和状态；项目地图检查结果见 `status.txt`，问题和 stale living docs 均为 0。
