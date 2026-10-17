---
id: T-093
title: 正常登录启动方式落地：隔离 HOME 加登录凭据、本地转发层调用计数、事实核对脚本
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
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

- 来源：T-092 的 build 票，构思主控建票；**未标就绪**，用户尚未说开工。写入范围预期：`workbench/src/`、`workbench/tests/`、本票证据。
