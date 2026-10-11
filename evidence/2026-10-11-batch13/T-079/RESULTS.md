# T-079-1：启动前等待 shell 就绪

2026-10-11，worker `s13-t079`，T-079 `ready_rev: 1`。**INCOMPLETE：红态探针已准备，待执行主控在沙箱外执行；修复、绿态及提交未完成。**

起点为 `ffe7ecb85e9e224d5917183b48754f15ac0c5ba6`。本轮保留已有主控日志改动，只新增本卡证据及 T-079 的 Resolution；尚未改 `scripts/launch-worker`。

## 已核对的就绪能力

- observed：本机 Herdr CLI 为 `0.9.3`，Codex CLI 为 `0.162.1`。运行中 Herdr server 的版本尚未核对；沙箱外脚本会保存它的状态。
- observed：`pane split --env KEY=VALUE` 支持给新 shell 注入环境。`pane process-info` 提供 shell PID、前台进程组及前台进程列表；`pane get` 没有 shell 就绪字段。
- observed：[官方 CLI 文档](https://raw.githubusercontent.com/herdrdev/herdr/v0.9.3/docs/next/website/src/content/docs/cli-reference.mdx)将可用 shell 定义为 shell 占有前台，且没有其他前台命令、编辑器或 agent。
- observed：上游 `v0.9.3` 的 [macOS 实现](https://github.com/herdrdev/herdr/blob/v0.9.3/src/platform/macos.rs#L416)调用 [available_pane_shell_from_job](https://github.com/herdrdev/herdr/blob/v0.9.3/src/platform/mod.rs#L367)。它要求前台进程组等于 shell PID、前台进程列表仅含该 PID，且进程名属于支持的 shell；[process-info 的实现](https://github.com/herdrdev/herdr/blob/v0.9.3/src/app/api/panes.rs#L519)暴露同一组进程事实。
- inferred：可以按以上结构化字段等待 Herdr 定义的可用 shell，不依赖标题、revision 或读屏。不把进程事实扩大解释成已收到某个 shell prompt 事件；Herdr 没有暴露这样的事件。
- unknown：实际 10 次启动中红态出现次数、实际 server 与文档的版本关系、修复后的稳定性及尾注行为。本轮未启动任何真实 Codex，也未产生模型回合。

能力原始记录：[herdr-capabilities.json](herdr-capabilities.json)，包括本机 help、schema 与上游函数原文。重新生成到新文件，避免覆盖原证据：

```sh
python3 -B evidence/2026-10-11-batch13/T-079/inspect-capabilities.py /tmp/t079-herdr-capabilities-new.json
```

## 红态交接

执行主控从自己的 Herdr pane 运行：

```sh
bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh red
```

脚本固定使用起点提交的 launcher，重复 10 次，未修复也不重试某次启动。它为每次运行新建证据目录；保留完整命令、退出码、stdout/stderr、追加式启动记录、pane/process-info 快照及夹具归档。成功启动只核对 agent 的结构化身份与空闲状态，不发送任务；预期 `agent_pane_busy` 原样保存。其他失败立即停止，交主控判定。只关闭由本次 launcher 记录的新 pane。隔离 `CODEX_HOME` 只复制 `auth.json`，只信任本探针的夹具，只复制 `git add`/`git commit` 两条允许规则；凭据不归档，结束后删除该隔离 home。

本卡要求沙箱外操作统一交执行主控，因此在红态运行前暂停。待返回红态目录后，核对证据再实施最小修复；随后用同样 10 次启动取得绿态，并以不调用模型的夹具 worker 验证 9 项尾注。

## 已执行的检查

- PASS：shell 与内嵌 Python 语法检查。探针准备时修正了仓库根目录的相对定位，并依据 `--help` 修正 `status server --json` 的输出读取方式；这些修正发生在真实探针执行前，没有红态运行被覆盖。
- PASS：本轮地图检查为 0 problems、0 stale living docs，见 [project-map-before-red.txt](project-map-before-red.txt)。
- INCOMPLETE：真实红态 0 次，修复后启动 0 次，夹具尾注检查未运行，没有 a2a 交付提交。

重新生成语法检查与地图检查的命令：

```sh
bash -n evidence/2026-10-11-batch13/T-079/outside-sandbox.sh
python3 -B -c 'import ast; from pathlib import Path; s=Path("evidence/2026-10-11-batch13/T-079/outside-sandbox.sh").read_text(encoding="utf-8"); ast.parse(s.split("<<\x27PY\x27\n",1)[1].rsplit("\nPY",1)[0])'
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
find evidence/2026-10-11-batch13/T-079 -size +5M
```
