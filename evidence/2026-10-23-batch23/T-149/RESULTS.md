# T-149-1 / a1 交付记录

2026-10-23；worker `b23-t149`；分支 `exec/t149`。

**已完成主控 #2 确认的变更范围**：删除 0 个、标历史 3 个、待决 10 个。注释保真、索引和 import 检查为 **PASS**；附带复跑的旧 `reviewer-startup` 测试为 **INCOMPLETE**，改前与改后同因失败，不报告整组测试全绿。未改代码、断言或停用待决测试。

## 授权与变更

执行主控 #2 原话：“确认 PLAN 8eda61b96b：删 0、标历史 3、待决 10”；“文件头注明……不改任何代码行”；“10 个待决文件不动”；“Electron 部分不用跑（只改注释）”。调查及完整引用见 [DISPOSITION.md](DISPOSITION.md)，该日期记录保持原样。

- `diagnose_t112_reviewer.py`、`t112_reviewer_record.mjs` 各新增一行文件头注释，指定 `5f19062f52154914123e3796fdff87caaa22fc1f`。
- `controlled_quality_pty.ts` 新增一行文件头注释，指定 `5f7f9816eb9a996377c5b255695244d99c0259e7`。
- 新建 [HISTORICAL.md](../../../workbench/tests/HISTORICAL.md)：列出 3 个历史辅助文件的 revision、用途、调用者及“同取该 revision 的 host/测试/产品”的复跑边界；另列 10 个待决文件的现行有效检查，注明“待用户决定，未停用”。
- 产品、既有 import、函数体、断言、10 个待决文件、历史证据、地图和其他治理文件均未改。

## 验证与证据

基线是 PLAN 提交 `8eda61b96bb01cda338d2bd2cb6927ce4bae5386`。改动前先运行同一组离线检查，改动后再运行，不覆盖旧结果。

| 检查 | 改前 | 改后 | 证据与结论 |
| --- | --- | --- | --- |
| 现有 `test_t112_request_replay.py` | PASS，exit 0，4 项 | PASS，exit 0，4 项 | `before-01/request-replay.json`、`after-01/request-replay.json`。真实捕获请求进入被标记的 Python 模块 handler；覆盖工具声明回放、标题请求、声明改名、缺声明拒绝。 |
| 实际 import `controlled_quality_pty.ts` | PASS，exit 0 | PASS，exit 0 | 各目录 `controlled-pty-import.stdout.txt`；导出 `installControlledPTY` 为 function，没有调用它或启动 PTY。 |
| `node --check t112_reviewer_record.mjs` | PASS，exit 0 | PASS，exit 0 | 各目录 `reviewer-host-parse.*.txt`；只证明语法解析。 |
| 现有 `test_t112_reviewer_startup.mjs`（VM，无 Electron） | INCOMPLETE，exit 1 | INCOMPLETE，exit 1 | 各目录 `reviewer-startup.json`；该旧 VM 夹具只模拟显式 `release()`，未模拟当前 host 等待的 `pane.started`。失败均为 `Startup must release before requiring a session: ["create","identity-before-release"]`；不是 import/语法失败。 |
| 注释及范围保真 | — | PASS | `scope-check-01.json`：逐字节核对 3 个文件均恰好为指定一行注释 + 基线完整原字节；10 个待决文件逐字节等于基线；两份 startup 结果剔除 stack 后完全相同。没有计算指纹。 |
| 项目状态 | Problems 0 / Stale 0 | Problems 0 / Stale 0 | `project-map-final.txt`。 |

两次完整命令和各子命令 exit 保存在 `before-01/summary.json`、`after-01/summary.json`；两份汇总均如实保留 `status: INCOMPLETE`，其中 `import_checks_status: PASS`。已有失败没有被跳过、改绿或改称本次回归。

稀疏 checkout 缺少请求回放需要的两份历史捕获 JSON。复跑脚本只在私有 `/private/tmp` 源码副本中从 Git 读取这两份输入，同时复制未改断言的现有回放测试及其直接依赖；未向历史证据目录补写文件。回放不启动 HTTP server、原生 CLI、后台、Electron 或模型，不复制认证文件。

## 复跑

本轮实际命令（两个输出目录已存在，不可覆盖）：

```sh
python3 -B evidence/2026-10-23-batch23/T-149/RUN-CHECKS-01.py --output evidence/2026-10-23-batch23/T-149/before-01
python3 -B evidence/2026-10-23-batch23/T-149/RUN-CHECKS-01.py --output evidence/2026-10-23-batch23/T-149/after-01
```

复验当前候选时使用新路径，例如 `/private/tmp/t149-import-recheck-01`。脚本要求目录不存在；保留所有 stdout、stderr 和 JSON。若旧 startup 测试仍失败，脚本整体仍退出 1，不吞失败。

保真检查的关键核对方式（以一个文件为例；其余结果见 `scope-check-01.json`）：

```python
from pathlib import Path
import subprocess
base = '8eda61b96bb01cda338d2bd2cb6927ce4bae5386'
path = 'workbench/tests/diagnose_t112_reviewer.py'
header = '# 历史测试：只针对 5f19062f52154914123e3796fdff87caaa22fc1f，当前 main 不跑\n'
assert Path(path).read_bytes() == header.encode('utf-8') + subprocess.check_output(['git', 'show', base + ':' + path])
```

## 限制与待决交接

- 本次不改行为，不新增或修改测试断言，没有产品修复红→绿或变异主张。改前/改后对照只用于核对注释未改变原内容或已知结果。
- 旧 VM 失败已在 DISPOSITION 的 R9 中调查，超出本次仅加注释的范围，保持 **INCOMPLETE**。本次没有修复或重启任何原生会话。
- Electron、真实原生测试、构建和完整回归 06 按主控 #2 的缩小验证范围未运行；没有新增 RUN-OUTSIDE 请求。旧 main 绿态不替本候选背书。
- 10 个待决文件及各自有效检查已写入 HISTORICAL 索引，等待用户决定，未停用。删除数为 0，没有需要修复的被删文件引用。
- 本轮只有新增小文本摘要和命令脚本；没有入库完整 fixture、数据库、二进制或归档包。

提交使用 `git add --sparse` 和普通 `git commit`；不手写 A2A 尾注，不 push、不合并。候选提交号以本报告所在提交及交付消息为准；最终独立审查和集成由执行主控处理。
