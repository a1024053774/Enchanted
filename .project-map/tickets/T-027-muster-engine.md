---
id: T-027
title: Muster 引擎以独立命名空间运行
type: build
status: closed
blocked_by: [T-026]
claimed_by: Codex worker wF:pS
supersedes:
---

## What to build

把 Herdr 0.9.3（`c4653a4`）的引擎硬分叉进本仓库，改成 Muster 的命名空间。完成后，用户可以在独立会话中启动 `muster` 后台服务：建项目和任务、分 pane、在 pane 里跑 shell 和 Codex，看到 agent 状态，并通过 `muster` 读写 pane。整个过程中，已安装的 Herdr 照常工作、互不干扰。

引擎不再访问 herdr.dev，保留 Herdr 的许可与来源说明。命名空间、网络和来源要求见 [spec](../specs/workbench-m1-2026-10-06.md) 的"命名空间""网络""代码位置"。

## Acceptance

- [x] 能从源码构建出 `muster`；构建输出和缓存都在外置盘上，外置盘未挂载时构建报错。
- [x] `muster` 能在独立命名会话中启动后台服务，并建出项目、任务和 pane；pane 中的 shell 可读可写；客户端断开后，服务和 pane 仍在。
- [x] 在 muster pane 中启动 Codex，状态识别正确（working、idle），会话 ID 经 Muster 自己的集成 hook 上报。
- [x] 已安装的 Herdr 与 Muster 同时运行，双方的 socket、配置和 hook 互不影响，并留有记录。
- [x] 源码和运行时都不再访问 herdr.dev，网络访问检查留有记录。
- [x] 保留 Herdr 的 LICENSE，并附来源说明（上游地址与 `c4653a4`）；引擎自带测试中与本切片相关的部分通过，失败项逐条记录。

## Resolution

PASS（仅 T-027）。worker 为 Codex `wF:pS`，主控为 Claude Code `wF:pM`。真实运行源码候选为 `3316be04af56ed7b141e659ea26dd7ddc9e90887`；完整报告/证据冻结于 `fd3beb70bcc1add0eb0428e8c062e3d68e694e10`，生产代码及探针相同。重新冻结后的独立只读子审查返回 PASS（固定角色模型 `gpt-5.6-luna`、max），见 [审查原文](../../evidence/2026-10-06-m1-batch2/T-027/review-02-pass.txt)。第一次审查因 worker 更新报告而停止的 INCOMPLETE 原文保留，没有覆盖。

新候选源码构建及实际外置盘 Zig 包布局通过，缺盘反例退出 2；上游来源链接已恢复、项目 repository 指向 a2a、错误引用 git grep 零匹配。3470 项自带测试中 3459 通过、11 为上游已有 ignored 项，50 个进程退出 0。run-04 的真实 shell/endpoint 等 22 项检查通过；先完成这些前置检查，才使用主控最终许可进行唯一一次新 home 的四 hook 复验。run-05 共 35 项通过：真实 Codex working→显式 idle、Muster hook 上报 ID 与原生 session_meta 一致、原生最终 nonce 回复匹配；用户 hooks 字节及默认 Herdr 0.9.1 身份不变；整个私有 CODEX_HOME 删除。复制的 auth/config 没有进入证据或 Git。旧运行不能替新候选背书。

完整命令、原始输出、失败、反事实、权限、清理与独立审查见 [T-027 报告](../../evidence/2026-10-06-m1-batch2/T-027/RESULTS.md) 和 [最终运行索引](../../evidence/2026-10-06-m1-batch2/T-027/final-runtime-evidence.json)。本结论不代表 M1、GUI、coop 接线、多平台或运行时切换通过；供应商实际 tier 与新 hook trust UI 的 blocked 检测未验证。

worker 未修改根治理文件。README 的 stale 按任务书和最终许可由主控收尾；主控获悉审查 PASS 后更新，不由 worker 接管。
