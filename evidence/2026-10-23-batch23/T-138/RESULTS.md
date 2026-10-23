# T-138-1 / a1：复现准备

状态：**INCOMPLETE**。尚未取得缺陷红态；生产代码未改动，修复与验收待真实 Electron 结果。

## 版本与范围

- worker：b23-t138；task：T-138-1；attempt：a1；分支：exec/t138。
- 起点：`b99f4869bbe087946017716a5a8479c0cb47e6c8`；任务卡 ready_rev 1。
- 仅新增 `workbench/tests/test_t138_ime_e2e.py` 和本 ticket 的证据、执行脚本。未修改既有验收文件、地图、ticket、后台或 xterm 源码。

## 复现脚本

真实 Electron、编排后台和 node-pty；PTY 中运行隔离的 Python raw 字节接收器，不调用模型。输入场景只使用 CDP `Input.imeSetComposition`、`Input.insertText` 和方向键/回车；DOM 只用于界面导航、聚焦、事件与选区观察，不赋值 textarea，不调用测试输入桥接。

先输入“前面怪了”，左移两次，在中间提交“打出”，连续三次；再回车、重新输入“前面怪了”、左移两次、提交“打出”。期望字节直接来自任务卡。分别观察设置中的读屏关闭和开启状态，记录可信 composition 事件、textarea 内容/选区、PTY 实际字节及截图。

检查两种设置的原因是依赖源码显示：xterm 在读屏关闭时取消方向键默认动作，在读屏开启时保留浏览器选区移动。此为复现线索，尚非真实缺陷结论。

## 已运行

```sh
python3 workbench/tests/test_t138_ime_e2e.py --revision b99f4869b --summary evidence/2026-10-23-batch23/T-138/sandbox-red-01.json
```

退出码 1；结果 `INCOMPLETE`，`cases=[]`，`defect_reproduced=false`。后台、raw PTY 接收器与构建已成功；等待 Electron 项目界面时 CDP 连接 `127.0.0.1:50648` 返回 `ECONNREFUSED`，未进入任何输入场景。该结果是环境失败，不能当作缺陷红态，也不能判定复现不成立。清理没有报告错误；夹具现场保留在 `/private/tmp/t138-4bsq6y0a`，未归档、未提交。

`python3 -m py_compile` 首次因默认缓存目标位于沙箱外的 `~/Library/Caches/com.apple.python` 失败；后续静态检查改用 `/tmp` 缓存，另存检查输出。

静态检查 PASS：`PYTHONPYCACHEPREFIX=/tmp/t138-pycache python3 -m py_compile workbench/tests/test_t138_ime_e2e.py`、`zsh -n evidence/2026-10-23-batch23/T-138/RUN-OUTSIDE-01.sh`、`git diff --check`。结束时地图检查为 0 problems、0 stale living docs，输出见 `project-map-status-01.txt`。这些检查不替代真实输入场景。

## 下一步与待验收

请执行 `zsh evidence/2026-10-23-batch23/T-138/RUN-OUTSIDE-01.sh`，回传新生成的 `red.json` 路径。脚本每次创建新目录；截图留在目录中，不提交。

- 尚未运行：沙箱外缺陷红态、生产修复、修后绿态、还原修复的变异检查。
- `--mutant` 待确认红态及修复后加入；当前仅交付复现准备，不宣称最终 e2e 已完成。
- 待相关回归：`test_t139_t143_views_perf_e2e.py`、`test_t145_mouse_reports_e2e.py`；`test_t091_pane_ipc.mjs` 需比较基线和候选，不把卡里记载的已知失败算作新通过。
- 如果真实 Electron 没有复现末尾两字错位，应报告实际字节、事件和选区并停下，不按源码推测实施修复。
- 尚未进行完成候选的独立审查；由执行主控在完整交付后安排。
