STATUS: FAIL
TARGET: 7f5d07091ff8c38558812678315774c9f1cc8473
EVIDENCE:
- red-01 原件记录 observer 超时、PID 6599 清理失败、red_observed=false；三个 observer 输出文件均为 0 字节。
- 独立复现纯 Python 检查：父提交因 close RPC 超时及退出未确认仍调用 daemon_stop 被拒；候选通过。Observer 构造未返回的哨兵也未触发后台清理。
- close_red01.py 静态绑定指定 PID、启动时间、完整 argv 和夹具；没有强退入口，复制使用新目录、核对文件数/字节数并保留原件。
- HEAD 未变化；project_map status：0 problems、0 stale。
FINDINGS:
- [P1] evidence/2026-10-16-batch16/T-091/run_red.py:143 — 正常退出未确认时仍关闭 Electron stdout 管道。若随后发出迟到的 ready，red_window.mjs:21 的写入错误可经 fatal() 进入 :17 的 app.exit(2)，形成“正常关闭失败后由断管触发直接退出”的静态可达路径，违反失败即停要求。最小修正：保留原始输出与诊断，使父端结束不会触发应用直接退出；正常退出证据仍须独立确认。
COUNTEREXAMPLE:
- 父提交两个已知坏分支均被拒绝。
- “正常关闭未确认 → 父端关闭管道 → 迟到 ready”未被现有两个 Python 检查覆盖。
LIMITATIONS:
- 上述 P1 是源码可达性结论，未做真实 EPIPE、AppKit 或 Electron 复现。
- 未运行进程检查、关闭、daemon、PTY、GUI、截图、网络或归档；不据此否定或宣称这些外部边界通过。
RULE:
- 在纯编排检查中加入“退出未确认后迟到回复”的反例，核对输出保留、无直接退出、无 daemon_stop、无归档；检查归入 test_red_cleanup.py。
