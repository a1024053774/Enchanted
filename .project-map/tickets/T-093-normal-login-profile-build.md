---
id: T-093
title: 正常登录启动方式落地：隔离 HOME 加登录凭据、本地转发层调用计数、事实核对脚本
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

落实 [T-092](T-092-normal-login-profile.md) 的决定（用户 2026-10-17 作答，逐字见该票）。

1. **小探针先行**（不跑真实模型回合）：确认 Claude Code 登录凭据能否复制进隔离 HOME 后正常使用（macOS 可能存钥匙串）；确认 CLI 能走本地转发层且登录不受影响。探针不通就停下回构思主控，不自行改成可写真实 HOME。
2. "正常登录" profile：仍走同一 `controller_start`、hook、Stop 转交路径；hooks 只经每会话启动参数传入；`workbench/src/claudeLaunch.ts:39,50,51` 目前只支持假 API，按需扩展。
3. 本地转发层：逐条记录请求（含失败与重试）再转真实接口，原始记录可重数。
4. 事实核对脚本：输出调用次数、启动参数与环境里是否有指向真实 HOME 的路径、真实 HOME 前后清单对比是否变化、凭据扫描命中数；不自动放行，不自动拒绝。

## Acceptance

- [ ] 红态：当前 `main` 上没有正常登录入口，现有入口拒绝非假 API 配置。
- [ ] 绿态（无模型）：用假上游跑通整条链，计数与转发层原始记录一致；隔离 HOME 结束后整个删除，真实 HOME 前后清单无差异。
- [ ] 反例：启动参数混入真实 HOME 路径被事实脚本标出；凭据出现在证据里被扫描命中；转发层漏记一条（用丢包模拟）被计数对账抓住。
- [ ] 凭据不进证据或 Git。
- [ ] `project_map.py status` 0 problems。

## 不做

- 不跑真实模型回合：真实运行最多 3 回合，须用户在本票合入后另说开工（T-004 停止条件）。
- 不写用户 `~/.claude` 等全局配置；不做策略引擎。

## 说明

- 来源：T-092 的 build 票，构思主控建票；已标就绪（见下）。写入范围预期：`workbench/src/`、`workbench/tests/`、本票证据。

## 就绪

用户 2026-10-17 说（逐字，会话"a2a-构思主控"）："开1，2， 用fast，快重制了，是我改的"，构思主控据此标就绪（`ready_rev: 1`）。
本票只做落地与无模型验证；真实模型回合（总上限 3）仍须用户在本票合入后另说开工。

## 裁定（2026-10-17）

执行主控 needs-decision：验收"真实 HOME 前后清单无差异"在运行中的机器上做不到稳定满足（差异来自 macOS 钥匙串自己的 WAL 与用户其他 Claude 会话的写入）。该条是构思主控在 T-092 里收缩出来的，用户未逐条确认。用户选"A: OS 沙箱禁写真实 HOME + 禁写反例 (Recommended)"，选项原文："由 OS 沙箱强制禁止写真实 HOME，再加一个试图写真实 HOME 被拒的反例。前后清单照实报告但不作通过条件。证明的是“写不进去”，比“碰巧没写”更强。"

据此 Acceptance 中"真实 HOME 前后清单无差异"改为：OS 沙箱强制禁写真实 HOME，并有一个试图写真实 HOME 被拒的反例；前后清单照实报告，不作通过条件。


## 真实回合授权（2026-10-19）

用户逐字（会话"a2a-构思主控"）："跑 T-093,需要多少回合就跑多少回合,这个你来决定,不能让这个卡住,然后 093 做完就差不多了"。用户把回合数委托给构思主控；构思主控的决定见 inbox 的 assign 条目。本条取代上文"总上限 3、合入后另说开工"。

## Resolution（2026-10-19，执行主控）

PASS。exec/t093 已以 `--no-ff` 合入 main（fb7eb0092），没有 push。

- 独立审查：01 NO_GO、02 INCOMPLETE、03 NO_GO，04 PASS（reviewer s16-t093-r4，审查候选 9373a9d44，报告见 `evidence/2026-10-16-batch16/T-093/independent-review-04.md`）。审查列出的可选 OS 补证 REVIEW-OUTSIDE-05.sh，执行主控已在沙箱外运行，结果 PASS。
- 原生七场（T-096 恢复回归，模型回合 0，假接口请求 0）：
  - r21 在 0be3d3ff2 上：tracer、three、no-argv、version、no-session，五场 PASS。
  - r21 的 isolation、empty-reopen 两场 INCOMPLETE：原因是测试脚本读到了较早的帧，报 KeyError 'launch'。原件保留，isolation 的旧归档不一致也保留。
  - 只修测试脚本的就绪判定（#139，产品没改）后，r22 在 9373a9d44 上重跑这两场，均 PASS。
- 合入后，main 上的 `workbench/tests/test_t096_restore.mjs` 结果 PASS；`project_map.py status` 0 problems。
- 已知限制按报告如实保留：
  - OS 层不按主机限制，只放行 *:443，上游主机由应用层锁定。
  - 正常登录的主控记录不恢复，采用白名单、默认拒绝。
  - 依赖 Claude Code 2.1.302 的内部状态；onboarding 预检直连官方地址；400 之后会重试。
  - r20 helper 输出被截断的根因，以及 r21 旧归档不一致的触发时点，都仍是 unknown。
- 打分：score-5ee1b1bc885e4f7bbda3d56b469e5ffa。
