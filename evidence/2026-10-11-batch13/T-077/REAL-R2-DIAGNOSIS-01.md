# T-077 r2 第一次启动：只读诊断

2026-10-12，回应主控 #81。**INCOMPLETE**。候选 `f6bc3ed99c87e6ea20eaf144b6a073266a5decb2` 的真实复验未到冲突阶段。没有准备或启动新会话，没有修改产品、原始运行记录或预算账。

## 已证明的事实

原始证据在 `real-conflict-02/attempt-1/`；结构化摘录和原始 PTY 尾部字节在 `real-r2-diagnosis-01/`。

| 事实 | 原始来源 |
| --- | --- |
| 只有一个原生回合 | `events-after-stop.json` 的 native_record 事件 48 为 task_started，86 为 gpt-6.1-sol / xhigh 的 turn_context；467 为同一 turn 的 task_complete，原始时间 02:07:32.973Z、后台读取时间 02:07:33.122Z |
| 显式交付成功 | 459 登记 key `id:8ee0b73a-c031-46ed-8dd6-5e6490029781:delivery`，460 relay_processed 返回 ok=true；结束后的 SQLite 为 submitted，候选 `2a565adc25a9f86f8ce6a8aa7e8f6de0f3833f8b`，native_session 已持久化为 `01a12ddb-e947-7ce1-941f-ceba0142a500` |
| 回执在编排层已写入终端 | 461 登记 gate 消息，464/465 为 paste_intent/paste_written，469/470 为回执的 turn_submit_intent/turn_submitted；回车写入时间 02:07:33.265～266Z。这些证明终端写入，不证明 CLI 已开始新回合 |
| 周额度接近上限 | native_record 457 的 token_count.rate_limits.primary.used_percent=99，window_minutes=10080；rate_limit_reached_type=null。记录支持近额提醒，不能据此证明已收到硬额度耗尽或 HTTP 429 错误 |
| PTY 有明确的限流提醒弹窗 | `fixture-artifacts.tar.gz` 内 `state/traces/8ee0b73a-c031-46ed-8dd6-5e6490029781/pty.raw` 共 229,163 字节；字节偏移 227,608 出现 `Approaching rate limits`，随后显示 `Switch to gpt-6-luna for lower credit usage?`；默认高亮项为 `1. Switch to gpt-6-luna`，另有保持当前模型的选项 |
| 原生设置确实改变 | native_record 472/473/474 对应原始时间 02:07:33.276/.281/.283Z，均为 thread_settings_applied：model=gpt-6-luna，effort 依次 medium / xhigh / medium，service_tier=default |
| 回执没有开始第二个原生回合 | 原始 rollout 最后为 ordinal 83、02:07:33.283Z；之后没有 task_started、turn_context 或 task_complete。PTY 最后仍显示 `[Pasted Content 3525 chars]`，并显示 Luna medium；后台继续标 busy，最终 run.json 记录总等待期限 900 秒超时 |
| 未进入冲突与集成 | 库中只有 submitted 事件，没有 verified/integrated，verification=null；第一阶段在 wait_receipt 中退出，尚未提交并发 G，也未形成冲突或新 attempt |

PTY 的原始 ANSI 字节已保存为 `real-r2-diagnosis-01/pty-tail.bin`，从原文件偏移 227,408 开始；`pty-tail-repr.txt` 是便于阅读的转义展示。上述弹窗判断来自人工阅读原始终端输出，并与结构化原生设置记录交叉核对；没有用关键词规则生成业务通过结论。

## 原因判断与限度

这次不能只记为“硬额度耗尽导致模型没有回答”。直接证据是**近额限流提醒与回执注入发生了交互冲突**：回执 paste/回车与弹窗相邻，默认换模项随后生效，粘贴内容仍在输入框，没有原生新回合。回执回车被换模弹窗接收，是该时序与终端画面支持的解释；现有证据没有独立记录每个按键当时的焦点，因此不把具体按键归属冒充完全证明。

产品协议存在未决问题：后台把成功写回车标成 busy，却没有新 native turn 的确认；近额弹窗可能消耗输入并把 CLI 设置改到未经本次批准的模型。记录中没有 permission_wait、dispatch_unknown、stop_transfer_failed、queue_stopped、native_final_read_failed 或 terminal_protocol_failed，不代表这种弹窗交互已经受保护。启动 argv 确为 sol/xhigh、无 Fast；实际工作回合也是 sol/xhigh。只有后续设置变为 luna，**没有证据表明 luna 真正开始了模型回合**。

该问题涉及 TUI 放行、输入注入与运行设置漂移，不能在本次只读诊断中修复或用自动补 Enter、换模型、重试来绕过。需要执行主控核对产品的输入就绪/弹窗处理边界。主控 #81 提到“PTY 未找到明确额度提示”，本次在归档尾部找到了上述 **Approaching rate limits** 弹窗；它是近额换模提醒，不是明确宣告额度已耗尽。

## 预算与现场

原轮次已实际使用 4 回合；r2 账本预留 2，观察到 1，未开始的回执仍保守占位，未释放或改写。当前实际观察累计 5，保守占位累计 6；这不构成下一次启动授权。

`run.json` 记录 isolated_home_removed=true、turn_count_complete=true；native_final_read 2797 完整读到 193,303 字节，2798 为 pane_exit。无残留进程由主控 #81 报告。本轮只读取结束后的归档与 immutable SQLite 快照，没有再次操作进程。

诊断重现命令（本 worker worktree；新输出目录不得已存在）：

```sh
python3 -B evidence/2026-10-11-batch13/T-077/diagnose-real-r2.py --output /tmp/t077-r2-diagnosis-replay
```

T-077 真实冲突验收和独立审查仍未完成。保持 **INCOMPLETE**，本轮新增真实回合 0，回复后停止等待。

按 worker 角色卡尝试 issue 上报，命令在既有 inbox 校验处失败：`20261011T184830Z-executor-disposition-001.md` 的 reply_to 指向不存在的 `20261011T184331Z-worker:s13-t076-2-issue-001`。本次 issue 未投递，原错误与命令保存在 `issue-send-error-01.txt`；不修范围外 inbox、不重试，交执行主控核对。
