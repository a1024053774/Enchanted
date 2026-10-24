---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261024T002752Z-ideation-assign-001"
refs: [".project-map/tickets/T-157-stop-hook-user-input-submit.md"]
created_at: "2026-10-24T02:57:39.762589Z"
schema: 1
title: "T-157：Stop 批次期间用户输入后，交付按哪种语义处理"
id: "20261024T025739Z-executor-needs-decision-001"
---

T-157（F01 blocker）修前红态已在真实 Electron 复现（隔离实例，脚本化模型，0 个真实回合）：worker 的 Stop 批次正在异步核对时用户按 Enter，人工介入正确绑定原 attempt，但同一 attempt 的 submit 被门禁拒为 worker_not_active，没有候选；侧栏显示“未知”、窗格头显示“忙”，界面既不说明拒绝原因也没有恢复入口。根因（源码+实测）：人工 Enter 清空并替换当前 prompt 身份，旧 Stop 的 submit 在 await 之后核对身份时已对不上。
任务卡规定交付语义由你定，worker 已停下。两个选项：
1 先处理完 Stop 批次：已匹配的 Stop 批次按原 turn/attempt 先走完门禁；用户的新输入记为人工介入，但发给 worker 的时机排在该批次之后。代价：用户敲的字要等旧批次处理完才送达（通常几秒，门禁慢时更久）。
2（推荐）暂停后由 worker 重新确认：用户输入优先送达；未完成的旧交付暂停，保留旧请求、明确拒绝/未知结果与原 attempt 绑定；界面写明最后确定的事实和原因，给“请 worker 重新交付”的恢复入口——原 worker 在原 attempt 下核对任务卡、代码版本和人工介入后，自己发新的显式 submit（新 request_id，不替它提交，不复用旧请求，不自动重试）。原 attempt 已失效、合同版本变了或结果未知时仍拒绝，走现有中断恢复。理由：不拦用户输入；人工介入后的交付本来就该由 worker 重新确认；与门禁“明确拒绝不改写为成功、未知不重放”一致。
两项都不把已拒绝的旧请求改成成功。