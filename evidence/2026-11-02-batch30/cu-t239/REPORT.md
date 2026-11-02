# T-239 Computer Use 复验与三家 CLI 实测

日期：2026-11-02。结论：**INCOMPLETE**。

被测包为 `/private/tmp/a2a-build-t239-20261102/Enchanted.app`，启动参数使用任务书指定的隔离 state 和 user-data。三次启动后均用 `ps` 核对 `daemon.ts` 指向 `/private/tmp/a2a-t239cu/state`；项目列表仅见 `/private/tmp/a2a-t239cu/project`。后台报告的版本为 `635eb1bbc7fbfb68142ea253680047ff73b383d9+dirty`，是未提交工作区的打包版本。截图均在 [shots](shots/) 中。

## A. 历史与非法字节

1. **仅重启后台：通过。** 新建项目终端，执行 `printf 'CU-A1\n\344\270'; sleep 3600`，看到 `CU-A1`（[截图](shots/a1.png)）。从菜单退出应用，只结束隔离后台、保留 core，再以原参数启动；接回终端后 Ctrl-C，执行 `print CU-A2`。期望接续可用；实际显示 `CU-A1` 和 `CU-A2`，后台已连接，无解码错误（[截图](shots/a2.png)）。
2. **后台和 core 均重启：通过。** 从菜单退出，结束隔离后台、core、holder 和其 zsh，再以原参数启动。期望已结束历史正常显示且无“窗格未连接”；实际显示 `CU-A1`、`CU-A2`，顶部显示“终端已结束 · 只读”，后台已连接，没有解码错误或“窗格未连接”（[截图](shots/history.png)）。
3. **非法字节与后续输入：通过。** 新建项目终端，执行 `printf 'CU-B1 \377 CU-B2\n'; print CU-B3`，再执行 `print CU-B4`。实际依次显示 `CU-B1 � CU-B2`、`CU-B3`、`CU-B4`，无错误提示（[截图](shots/invalid.png)）。

以上仅证明本次候选包的指定界面场景；不代替修前红态或代码审查。

## B. 三家 CLI

期望各 CLI 接受“请回复：测试正常。不要操作文件。”并回复。各程序均只启动一次。

- **Claude Code：失败。** 同一项目终端执行 `claude --model claude-haiku-5-5`，约十余秒未出现任何 CLI 画面或信任框，无法提交问题，故无回复时间。运行时 PID 98134；采样中多个 Bun Pool 线程位于 `openat`（[采样](claude-sample.txt)，[截图](shots/claude-start.png)），无法凭此确定打开的路径或根因。随后 Ctrl-C 返回 shell。
- **Codex：失败。** 在同一终端运行 `codex -c check_for_update_on_startup=false`，画面出现 Codex v0.164.0。就绪后粘贴并提交测试句，画面显示 `Queued follow-up inputs`，观察期间未出现回复（[截图](shots/codex-queued.png)）；没有精确计时，无法给出回复时间。运行时 PID 98453；[采样](codex-sample.txt)中一个 tokio 工作线程处于 `read_dir → __opendir2 → open`，不能据此确定路径或因果。Ctrl-C 两次后界面显示 shutting down，进程仍存活，最终按隔离进程清理。
- **agy：失败。** 由于 Codex 未及时退出，另开同一项目的终端，运行 `agy --dangerously-skip-permissions`。出现 `/private/tmp/a2a-t239cu/project` 信任框，按授权选择 Yes（[截图](shots/agy-trust.png)）；CLI 可能因此自行写入信任配置，本人未直接编辑全局配置。登录后提交相同测试句，界面由 `Generating...` 变为 `Working...`，约一分钟仍无回复，无法给出回复时间。运行时 PID 99280；[工作中采样](agy-working-sample.txt)未找到 `openat` 或 `open$NOCANCEL` 字样，不能据此排除其他等待或确定原因。为避免截图包含账号邮箱，未保存工作中全屏截图；[启动阶段采样](agy-sample.txt)另存。

三个未回复场景分别在进程存活时采样；对照命令 `time cat ~/Documents/SKILLS/reality-evidence-engineering/evidence-first-testing/SKILL.md >/dev/null` 分别约 0.003、0.002、0.002 秒成功，不能证明其他路径的读取正常。未遇到 macOS 系统权限框，也未选择更新。未批准角色申请或 Codex 钩子信任框，因未出现这些提示。

## 收尾

从菜单退出测试应用，结束经 PID 与隔离进程树核对的后台、core、holder、zsh 及残留 CLI；随后 `ps` 核对上述 PID 均已消失，按测试包和 state 路径搜索没有匹配的被测进程（仅搜索命令自身）。保留 `/private/tmp/a2a-t239cu/`。结束时 project-map status 为 Problems 0、Stale living docs 0；开始时曾报告 `workbench/README.md` stale，本复验未修改它。没有更改代码、ticket 或地图。

**总评 INCOMPLETE：** T-239 三个指定界面场景通过；三家 CLI 均未取得期望回复，Claude 与 agy 的完整问答分别因启动未就绪、持续运行而未完成，原因尚未确定。未对修复整体验收或发布作通过判断。
