# T-262 测试夹具与诊断修订

INCOMPLETE：已完成本轮夹具和诊断修订，真实父版红态由主控继续运行。

**Works**：Python 语法与 `--help` 检查通过；`check-diagnostics.py` 使用主动退出的本地 Python 子进程，证明退出码 7、日志尾部、字节数及截断标记在清理前落盘，清理后仍可读。原始结果为 `diagnostics-check-02.json`。
**No regression**：`RecordsPage.tsx` 和 `records.css` 无改动；未运行后台、Electron 或产品回归，没有重试被拒的 `/bin/ps`。project-map 开始检查为 Problems 0、Stale living docs 0。
**Risk / undo**：尚未验证 Electron 能进入页面；若失败，主控应读取新诊断文件，不把启动失败当业务红态。没有提交或 submit，夹具草稿仍待完整验收。

## 用户 #92 的分工与旧现场

主控接手真实入口测试，worker 权限保持原样，不再请求批准 ps。已回读主仓库 `controller/blocked-fixture-cleanup.json`：私有 core 停止返回 `stopped=false`，主控核对无进程残留并删除原夹具，`worker/red-01.json` 保留。`controller/red-outside-01.json` 和 `red-outside-02.json` 均为环境异常，不是业务红态。

## 本轮调整

- worker 仍在 `A2A_REQUEST_DIR` 内建自有临时目录；主控运行时移除该变量，脚本固定使用 `/private/tmp`，不依赖 macOS 的长 TMPDIR。启动前检查 control、core、holder 与 terminal socket 的 UTF-8 字节数，超过 103 直接报错，不改权限或自动换写入边界。
- Electron argv 顺序、`cdp_launch.cjs` 入口、`start_new_session=True` 与纯辅助类 `scripted_claude.Electron` 一致；使用项目现有二进制，明确不传 `ELECTRON_RUN_AS_NODE`，不调用 Claude Fixture，也不触发依赖下载。
- 先创建空项目并打开真实窗口，再向隔离库追加受控输入与回执。源码推断：旧夹具在启动前写入的 worker 记录可能被 `startupView` 选中，但其任务并未派发，导致窗口创建前退出；旧 Electron 日志已丢失，这一解释仍待真实运行核实。
- Electron 启动 argv、cwd、pid、阶段、退出码、HOME/TMPDIR 路径和日志尾部进入报告；提前退出时立即报告。默认每份日志最多保留尾部 16000 字节，带原始字节数与截断标记。
- `--summary` 对应同名 `.diagnostics.jsonl`，在清理前保存第一份诊断，清理后追加第二份；最终 JSON 摘要仍写到 `--summary`。两者已有任一文件即拒绝覆盖。没有传 summary 时，诊断文本保留在自有临时根的旁边，路径写入标准输出摘要。
- 明确业务断言失败为 `FAIL`；后台、Electron、CDP 或清理异常为 `INCOMPLETE`，二者均退出非零。报告保留已观察到的失败断言，即使后续又遇到环境异常。

## 主控下一次运行

完整命令见 `controller-red-03.command`。外层工具 cwd 必须为当前 gate worktree。

```sh
env -u A2A_REQUEST_DIR /usr/bin/python3 workbench/tests/test_t262_records_e2e.py --revision f80d5cdbf0e1b62de864300eff7bb4497f8c4c70 --summary /Users/luckye/Documents/Code/a2a/evidence/2026-11-08-batch34/T-262/controller/red-outside-03.json
```

预期输出文件：主仓库 `controller/red-outside-03.json` 与 `controller/red-outside-03.diagnostics.jsonl`。无需手工设置 TMPDIR。若文件已存在，主控换一个新编号，不覆盖。

若 `FAIL` 的 `failed` 包含双区任务筛选或倒序不符，且真实窗口已进入记录页，即取得本 Tracer bullet 的父版红态；若为 `INCOMPLETE`，按 `diagnostics.before_cleanup.phase`、`returncode`、`electron.log` 定位。此次脚本仍是两个业务断言的草稿，不代表全部 T-262 验收完成。

## 本地检查与清理

命令：`/usr/bin/python3 evidence/2026-11-08-batch34/T-262/worker/check-diagnostics.py`。
本轮自检使用 Node v26.5.0、Python 3.9.6；既有 Electron 包版本 43.4.1（只读取版本，未启动）。socket 字节数分别为 control 61、core 56、holder 72、terminal 81。两次自检的自有准备目录和诊断填充文本均已清理，只保留紧凑 JSON。没有改额外目录；临时操作全部在本 attempt 的请求目录内。
