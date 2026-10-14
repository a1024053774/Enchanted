## 09A-3R2 block 读回与 cleanup（2026-10-14 UTC 18:2x）

逐屏引导与信任同 clean（目录 /private/tmp/t078-2-p1-09a3r2-block-093154n0/repo）。continue PASS（模型 0）：Esc 后保留恢复的草稿，test-simulated-user 点故意不真实的空框声明；真实 UPS2 的 prompt 同时含 nonce1 与 nonce2，hook 原始 stdout 为 {"decision":"block","reason":"登记注入与实际提交正文不一致；已阻断，请处理草稿后再决定。"}，exit 0；假 API 只有请求 1，无 API2、无 api-error。cleanup 及外置归档见下。用户决定 A 与提交前拦截的正例、反例在真实 CLI（假服务）上均成立。待续：09B/09C 停止链路、真登录 Haiku 2–3 回合（逐次批准）、新候选独立审查、合并。

## 09A-3R2 block 收尾（2026-10-14 UTC 18:4x）

原 cleanup BLOCKED（ps 以中文日期输出，按 5 个 lstart token 切列把解释器路径吃入，误判 identity_changed）；#153 恢复脚本同因在 owns_api 前误判，未发信号。#155 修复：ps 子进程固定 LC_ALL=C/LANG=C，非 C 格式直接拒绝，比对规则不变。运行 cleanup-block-recovery-09a3r2.py --approval-ref "主控 #155"：PASS——仅对 48954（本实例假 API，命令/根/owner/双读 lstart 一致）发一次 SIGTERM 并确认退出；CLI 48987、壳 48986、后台 48977 已退出；根逐成员归档到 /Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block/cleanup-recovery-154/fixture.tar.gz，字节读回 PASS 后删除根。两个 slot 未动。

## 09A-3R2 收尾提交与 09B/09C 计划裁定（2026-10-14 UTC 19:2x）

commit-closeout-09a3r2-09bc-plan → 50ea0f5f（以 s13-t078m 身份）：收尾读回 23 项、cleanup lifetime/ps C locale 修复与测试、PLAN-09BC-01、issue 20261014T191104Z 与 report。
裁定（执行层，属 T-078"紧急停止"验收内的实现缺口，不改设计）：
1. 先把 exec/t078 变基到当前 main（含 T-080：任务卡必填 oracle_paths、打分 schema 2；含 T-083），按双方意图解冲突，T-078 自建任务卡补 oracle_paths。
2. 文件所有权：T-080 已合入、T-081 不改产品、T-082 排在 T-078 之后——前置切片可改 workbench/src/gates/cli.ts（会话命令加 stop 等）、relay.ts、claudeLaunch.ts、panes.ts、daemon.ts、gates/core.ts（仅限转交/调用者身份所需）、store.ts 与测试。不得只删 controller_relay_not_enabled、不得伪造 attempt 或 operator 代写。
3. 顺序按计划：单个真实 Claude 角色转交/工具切片（红绿与边界反例）→ 冻结 09B 材料交审 → 09B 实跑与收尾 → 冻结 09C 交审。
4. 预算：每场景每角色上限 6 根提交、12 主 Messages（合计 ≤24），供应商模型 0；实测后在 manifest 收紧。09C 总观察 ≤150 秒、真实时钟 >120000 ms，不快进。
issue 20261014T191104Z 非 blocking，以本裁定处置（forward 构思主控备案）。
