---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-091", "ticket:T-078"]
created_at: "2026-10-17T13:37:56.366110Z"
schema: 1
title: "产品锁定的 Claude CLI 2.1.296 已被自动更新删除，主控窗格在本机起不来"
id: "20261017T133756Z-executor-needs-decision-001"
---

事实：
- workbench/src/claudeLaunch.ts:35 只接受 /Users/luckye/.local/share/claude/versions/2.1.296 这个绝对路径；:60 把 cli_version 固定记为 2.1.296 (Claude Code)。这是 T-078 定下的版本锁定，09B/09C 的证据都是在 2.1.296 上取得的。
- 2026-10-17 机器重启后，Claude Code 的自动更新把 2.1.296 删了。本机现在有 2.1.299、2.1.300、2.1.301、2.1.302（10-17 08:59 装）。
- 后果：在 main 上，工作台的主控窗格启动（controller_start）在本机全部失败，报 controller_launch_config_required。T-091 的三格绿态需要两个真实的主控 CLI（假 API、模型回合 0），所以卡住了。green-01 INCOMPLETE：没开窗口，Claude 启动 0，假 POST 0，已收尾、已归档。
- 以前的 2.1.296 不会再回来。用户的 Claude Code 自动更新会继续删旧版本。

选项：
A（推荐）：改锁定的版本，另开一张缺陷级票，或并入 T-091。锁定值改为当前的 2.1.302，并在 Resolution 写明：T-078 的证据绑定 2.1.296，没有在新版本上重跑。之后再碰到自动更新删版本，同样会坏，所以锁定方式改成从一个配置值读取，并在启动时实际执行 --version 核对版本、记录结果，取代写死的绝对路径。不写用户的全局配置。
B：用户自己装回 2.1.296，并关掉 Claude Code 的自动更新。这会动用户的全局安装和设置，只能由用户来做；执行主控不碰。
C：T-091 绿态先不起真实的主控 CLI，改用受控 receiver 代替主控格。这和 ticket 要求的'三份真实 workbench_snapshot 与进程身份'有出入，需要用户同意改验收条件。

裁定前，T-091 停在绿态之前。不需要 Claude 的回归（core、window、runtime、input-failures、worker-inbox）我先跑。