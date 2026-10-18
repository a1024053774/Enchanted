STATUS: FAIL
TARGET: 1e556ce716220b6c1ff3200a0a5407166d8938c6
EVIDENCE:
- 已读取 behavioral-acceptance-review 及 Agent 产品参考；仅复核冻结候选。
- 开始、结束均确认 HEAD 未变，相关受控源码无未提交修改；project_map.py status 均为 0 problems、0 stale。
- 字节码检查使用 SourceFileLoader.get_code，拦截全部缓存写入：实际写入 0；缓存缺失时尝试写入 /Users/luckye/Library/Caches/com.apple.python/.../claudeLoginFiles.cpython-39.pyc。
- 对冻结 metadata_service 函数执行纯内存检查，替换路径、信号、进程及删除操作：实际文件操作与信号均为 0。
FINDINGS:
- [P1] workbench/src/claudeLoginSession.py:30–32 — 在 validate_bootstrap 和任何 OS profile 生效前加载 Python 模块。README:375、425 的正式启动及 facts 命令未使用 -B，缓存缺失时会写入真实 HOME；无模型入口使用 -B，因而掩盖此问题。应在任何可缓存导入前禁止字节码写入，并让正式入口统一使用且检查 -I -S -B。
- [P2] workbench/src/claudeLoginSession.py:354–362 — 意外失败时仅向 C 进程组发送 SIGTERM，未确认退出便删除私有根，并可记录 cleanup_failures=[]、isolated_home_removed=true。忽略 SIGTERM 的所属进程仍可能存活。应在意外失败路径确认所属 C 进程组退出后再删除；明确取消时保留报告进程的例外可继续保留。此问题不会产生整体 PASS，但会产生不可靠的清理成功收据。
COUNTEREXAMPLE:
- 冷缓存、普通 Python 正式入口：拦截检查确认会尝试写真实 HOME；当前正式入口没有阻止它。
- 元数据采集抛出 PermissionError，C 进程组忽略 SIGTERM：纯内存执行返回 2，但仍报告清理无失败、私有根已删除，C 仍存活。
- 新增凭据注入、漏记请求、目的地限制及合成 HOME 变异体已做静态检查，本次未执行完整链路，未宣称反例已运行通过。
LIMITATIONS:
- 本次证据限于 L0 静态检查及 L1 受控逻辑检查；没有启动服务、供应商 CLI、模型或 OS 边界探针，没有读取真实凭据或查询 Security 服务。
- 当前候选的新完整链路及真实 OS 边界仍未验收；历史边界证据不能替代。
RULE:
- “确认完成前不得发送完成收据”已由现有提前关闭反例覆盖同类问题。应在 workbench/tests/test_t093_session_cleanup.py 增加元数据失败且 C 组未退出的反例，要求保留主失败并明确报告清理未确认。
