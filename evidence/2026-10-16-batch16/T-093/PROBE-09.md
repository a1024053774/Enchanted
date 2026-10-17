# T-093 probe-09：保留状态，读取脱敏屏幕（2026-10-17）

状态：INCOMPLETE，等待主控读回屏幕。主控 #70 已报告 probe-08 不再遇到官方预检，但到期前无本地请求。
未知屏幕是推测，尚未定位；本轮不增加自动按键、识别标记、状态字段或权限。
task T-093 / attempt a1 / ready_rev 1 / session `67f986cc-92e4-4089-9c22-802a1143b645`。
起点 `16791d6debf730cf9ed56bc77d5f2447bdb3ca88`；未提供新 fence。

唯一脚本变化：脱敏文件的精确授权路径由 terminal-07 改为主控指定的 terminal-09；帮助文字同步。
旧路径和任意相似路径不再通过当前检查。旧报告及文件处理记录保留；不会覆盖已有文件。
脱敏、写盘前凭据/身份扫描、0600、逐级拒绝链接和独占创建规则与 probe-07 一致，识别限制仍见 [PROBE-07.md](PROBE-07.md)。
onboarding 仍只新建一个完成字段，见 [PROBE-08.md](PROBE-08.md)；所有 profile 和交互按键逻辑保持。

在 worktree 根目录运行：

```sh
python3 workbench/tests/probe_t093_normal_login.py --run --prepare-onboarding-state --claude /Users/luckye/.local/share/claude/versions/2.1.302 --output evidence/2026-10-16-batch16/T-093/probe-09.json --terminal-output /private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t093-terminal-09.txt
```

报告是否导出见 `terminal_export.written`，rc 2 可能仍是无本地请求；不要据退出码认定文件没有写出。
主控读后删除该临时文件，只转述屏幕要点，不把正文放进 evidence 或 Git；worker 不读取该文件。
隔离 HOME 和凭据副本仍整个删除，清单差异照实记录；不跑真实模型回合，不申请升级。
主控回复前保持现有按键逻辑，不发送新的自动输入。

`terminal-destination-red-09.json` 保存旧固定路径拒绝新请求的红态；合成复验见 `probe-helper-checks-19.json`。
新路径检查只在自有临时目录中模拟文件系统阶段，未创建指定真实文件、执行真实 CLI 或读取真实 auth。
