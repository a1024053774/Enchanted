STATUS: FAIL
TARGET: df8144f97a3d70a8ae55c9e6b98584d978e72d63
EVIDENCE:
- 只读审阅冻结源码、测试和文本证据；HEAD 未变，未修改文件。
- 两个归档调用者共用 `archive_fixture()`；使用 `symlinks=True`，比较包含精确 target 字符串的条目，记录两侧词法边界。
- 纯内存执行候选 `Observer.close()` 和收尾 AST：未确认 ready、子进程退出码为 0 时，观察到 `daemon_stop` 和 `archive_fixture`；退出码非 0 时仍观察到 `daemon_stop`。
- 控制器 SIGTERM 被明确记为控制器操作及报告值；close-03 没有退出请求或信号操作。报告未声称外置复制、AppKit、Electron 或 red-02 已通过。
- project-map status：0 problems、0 stale living docs。

FINDINGS:
- [P1] `evidence/2026-10-16-batch16/T-091/run_red.py:476` — 后台清理只检查 `electron_closed`。未确认 ready 就自行退出的 Electron 会进入此分支，退出码为 0 时还会在第 504 行进入归档，违反“无 ready 确认则不停 daemon、不归档”。Electron 已尝试启动但 ready 未确认时，应直接暂缓这两项操作；补充提前退出的边界检查。

COUNTEREXAMPLE:
- `ready_confirmed=False, returncode=None`：正确停等，操作序列为空。
- `ready_confirmed=False, returncode=0`：错误放行，序列为 `daemon_stop → archive_fixture`。
- `ready_confirmed=False, returncode=1`：错误放行 `daemon_stop`。
- 现有测试只覆盖未 ready 且仍活着的情况，未拒绝以上提前退出反例。

LIMITATIONS:
- 未新增文件复制实验或调用真实进程、AppKit、Electron、外置盘；实际归档和 red-02 仍未验收。
- 控制器报告的身份核对、一次 SIGTERM、2 秒退出及无残留未由本审查独立测量。

RULE:
- 在 `test_red_cleanup.py` 覆盖未确认 ready 时的存活、退出 0、退出非 0 三种状态，分别断言不请求正常退出、不停后台、不归档。
